import argparse
import warnings
warnings.filterwarnings("ignore", category=ResourceWarning)

import asyncio
import csv
import json
import threading
import time
from typing import Any, Dict, Optional
import pika

from tcd1.actions.heartbeat import heartbeat
from tcd1.actions.data_collect import start_stream, stop_stream, snapshot
from tcd1.actions.drain_canister import drain_canister_to_sump
from tcd1.actions.drain_sump import drain_sump_to_tank
from tcd1.safety import safe_stop

# ---------------- RABBITMQ SETUP -----------------
RABBIT_HOST = "localhost"
RABBIT_USER = "admin"
RABBIT_PASS = "mypassword"
HEARTBEAT_QUEUE = "heartbeat_queue"
EVENT_QUEUE = "event_queue"

credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST, credentials=credentials))
channel = connection.channel()
channel.queue_declare(queue=HEARTBEAT_QUEUE, durable=True)
channel.queue_declare(queue=EVENT_QUEUE, durable=True)

def publish_heartbeat(msg: dict):
    channel.basic_publish(
        exchange='',
        routing_key=HEARTBEAT_QUEUE,
        body=json.dumps(msg),
        properties=pika.BasicProperties(delivery_mode=2)
    )

def publish_event(msg: dict):
    channel.basic_publish(
        exchange='',
        routing_key=EVENT_QUEUE,
        body=json.dumps(msg),
        properties=pika.BasicProperties(delivery_mode=2)
    )

# ---------------- HELPERS -----------------
def now_ts() -> float:
    return time.time()

def heartbeat_row(latest: Dict[str, Any]) -> Dict[str, Any]:
    bus_v = latest.get("bus_voltage_v")
    return {
        "Timestamp": now_ts(),
        "canister_mass": latest.get("canister_mass_kg"),
        "sump_mass": latest.get("sump_mass_kg"),
        "pump_voltage": latest.get("pump_voltage_v", bus_v),
        "pump_current": latest.get("pump_current_a"),
        "dv_voltage": latest.get("dv_voltage_v", bus_v),
        "dv_current": latest.get("dv_current_a"),
        "ev1_status": bool(latest.get("ev1_status", False)),
        "ev2_status": bool(latest.get("ev2_status", False)),
    }

# ---------------- CSV / JSON LOGGERS -----------------
class HeartbeatCsvLogger:
    FIELDNAMES = [
        "Timestamp", "canister_mass", "sump_mass", "pump_voltage",
        "pump_current", "dv_voltage", "dv_current", "ev1_status", "ev2_status"
    ]

    def __init__(self, path: str):
        self.path = path
        self._f = open(path, "w", newline="")
        self._w = csv.DictWriter(self._f, fieldnames=self.FIELDNAMES)
        self._w.writeheader()
        self._f.flush()

    def log(self, row: Dict[str, Any]) -> None:
        self._w.writerow({k: row.get(k, "") for k in self.FIELDNAMES})
        self._f.flush()

    def close(self) -> None:
        try:
            self._f.close()
        except Exception:
            pass

class EventLogger:
    def __init__(self, jsonl_path: str):
        self._jsonl = open(jsonl_path, "a", buffering=1)

    def write(self, obj: Dict[str, Any]) -> None:
        self._jsonl.write(json.dumps(obj) + "\n")

    def close(self) -> None:
        try:
            self._jsonl.close()
        except Exception:
            pass

# ---------------- ASYNC TASKS -----------------
async def wait_controller_ready(ctrl, t: float = 5.0) -> None:
    t0 = time.monotonic()
    last_err: Optional[Exception] = None
    while time.monotonic() - t0 < t:
        try:
            await heartbeat(ctrl)
            return
        except Exception as e:
            last_err = e
            await asyncio.sleep(0.1)
    raise RuntimeError(f"Controller not responding after {t:.1f}s (last error: {last_err!r})")

async def heartbeat_task(ctrl, period_s: float = 0.5) -> None:
    try:
        while True:
            try:
                await heartbeat(ctrl)
            except Exception:
                pass
            await asyncio.sleep(period_s)
    except asyncio.CancelledError:
        pass

async def stream_log_task(ctrl, hb_csv, event_log, log_hz: float, print_hz: float) -> None:
    try:
        log_period = 1.0 / max(0.1, log_hz)
        print_period = 1.0 / max(0.1, print_hz)
        next_print = time.monotonic()

        while True:
            latest = getattr(ctrl, "latest", None)
            if latest:
                row = heartbeat_row(latest)

                if hb_csv:
                    hb_csv.log(row)

                # PUSH HEARTBEAT TO RABBITMQ
                publish_heartbeat(row)

                if time.monotonic() >= next_print:
                    print(row)
                    next_print = time.monotonic() + print_period

            await asyncio.sleep(log_period)
    except asyncio.CancelledError:
        pass

async def can_dispense_sim(target_ml: int, done_event: threading.Event, step_ml: int = 50, period_s: float = 0.2) -> None:
    vol = 0
    while vol < target_ml:
        await asyncio.sleep(period_s)
        vol = min(target_ml, vol + step_ml)
        print(f"[CAN-SIM] Dispensed: {vol} ml")
    print("[CAN-SIM] Dispense complete!")
    done_event.set()

async def make_controller(args):
    from tcd1.controller_subprocess_link import SubprocessControllerLink
    cmd = args.controller_sim_cmd.split() if args.controller_sim_cmd else None
    ctrl = SubprocessControllerLink(cmd=cmd)
    await ctrl.start()
    return ctrl

# ---------------- MAIN -----------------
async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--controller", choices=["sim"], default="sim")
    ap.add_argument("--controller-sim-cmd", default="")
    ap.add_argument("--stream-hz", type=float, default=10.0)
    ap.add_argument("--log-hz", type=float, default=10.0)
    ap.add_argument("--print-hz", type=float, default=2.0)
    ap.add_argument("--ev", choices=["ev1", "ev2"], default="ev1")
    ap.add_argument("--dest", choices=["TANK1", "TANK2"], default="TANK2")
    ap.add_argument("--target-ml", type=int, default=1000)
    ap.add_argument("--sim-step-ml", type=int, default=50)
    ap.add_argument("--sim-period-s", type=float, default=0.2)
    ap.add_argument("--heartbeat-csv", default="heartbeat.csv")
    ap.add_argument("--events-jsonl", default="events.jsonl")
    ap.add_argument("--drain-timeout", type=float, default=60.0)
    ap.add_argument("--return-timeout", type=float, default=120.0)
    ap.add_argument("--stable-eps", type=float, default=0.01)
    ap.add_argument("--stable-time", type=float, default=2.0)
    ap.add_argument("--sump-empty", type=float, default=0.05)

    args = ap.parse_args()
    hb_csv = HeartbeatCsvLogger(args.heartbeat_csv) if args.heartbeat_csv else None
    event_log = EventLogger(args.events_jsonl) if args.events_jsonl else None

    ctrl = await make_controller(args)
    rx = asyncio.create_task(ctrl.rx_task())
    hb = asyncio.create_task(heartbeat_task(ctrl, 0.5))
    log_task = None

    dispense_done = threading.Event()
    can_task = asyncio.create_task(
        can_dispense_sim(args.target_ml, dispense_done, step_ml=args.sim_step_ml, period_s=args.sim_period_s)
    )

    try:
        await wait_controller_ready(ctrl, 5.0)
        print("[CTRL] Ready")

        try:
            await start_stream(ctrl, args.stream_hz)
        except Exception:
            pass

        log_task = asyncio.create_task(stream_log_task(ctrl, hb_csv, event_log, args.log_hz, args.print_hz))

        # SNAPSHOT EVENT
        try:
            s0 = await snapshot(ctrl)
            event_msg = {"ts": now_ts(), "kind": "event", "event": "snapshot_start", "data": s0}
            if event_log:
                event_log.write(event_msg)
            publish_event(event_msg)
        except Exception:
            pass

        print("[FLOW] Dispense start. Waiting for completion...")
        while not dispense_done.is_set():
            await asyncio.sleep(0.05)
        print("[FLOW] Dispense complete.")

        # DRAIN CANISTER EVENT
        res1 = await drain_canister_to_sump(
            ctrl,
            ev=args.ev,
            timeout_s=args.drain_timeout,
            stable_eps_kg=args.stable_eps,
            stable_time_s=args.stable_time,
        )
        print("[DONE drain_canister]", res1)
        publish_event({"ts": now_ts(), "kind": "event", "event": "drain_canister_done", "data": res1})

        # DRAIN SUMP EVENT
        res2 = await drain_sump_to_tank(
            ctrl,
            tank=args.dest,
            timeout_s=args.return_timeout,
            sump_empty_kg=args.sump_empty,
            stable_eps_kg=args.stable_eps,
            stable_time_s=args.stable_time,
        )
        print("[DONE drain_sump]", res2)
        publish_event({"ts": now_ts(), "kind": "event", "event": "drain_sump_done", "data": res2})

        print("[FLOW] Cycle complete ")

    finally:
        can_task.cancel()
        if log_task:
            log_task.cancel()

        try:
            await stop_stream(ctrl)
        except Exception:
            pass

        await safe_stop(ctrl)

        hb.cancel()
        rx.cancel()
        await asyncio.gather(hb, rx, return_exceptions=True)

        try:
            aclose = getattr(ctrl, "aclose", None)
            if aclose:
                await aclose()
            else:
                ctrl.close()
        except Exception:
            pass

        if hb_csv:
            hb_csv.close()
        if event_log:
            event_log.close()

        # CLOSE RABBITMQ CONNECTION
        try:
            connection.close()
        except Exception:
            pass

# ---------------- ENTRY -----------------
if __name__ == "__main__":
    asyncio.run(main())

