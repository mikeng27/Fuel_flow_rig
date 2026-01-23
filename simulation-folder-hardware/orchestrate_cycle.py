# orchestrate_cycle.py
#
# Runs the full cycle on the Pi:
#   (1) CAN: start dispense, wait for dispense complete (volume >= target)
#   (2) Pico: drain_canister_to_sump
#       - then WAIT until stream shows canister is empty
#       - then WAIT until sump is non-empty (optional safety)
#   (3) Pico: drain_sump_to_tank
#
# Logging requirements implemented:
#   - heartbeat CSV row EVERY 10 seconds (adjustable)
#   - events.jsonl "before" and "after" snapshots for:
#       dispense, drain_canister_to_sump, drain_sump_to_tank

import argparse
import asyncio
import csv
import json
import threading
import time
from typing import Any, Dict, Optional

import can

from tcd1.pico_link import PicoLink
from tcd1.actions.heartbeat import heartbeat
from tcd1.actions.data_collect import start_stream, stop_stream, snapshot
from tcd1.actions.drain_canister import drain_canister_to_sump
from tcd1.actions.drain_sump import drain_sump_to_tank
from tcd1.safety import safe_stop_pico


# ---- CAN constants (match your sm_logic.py) ----
ID_OPEN_VALVES = 0x60
ID_UPDATE_VOLUME = 0x34
ID_CLOSE_VALVES = 0x62


def now_ts() -> float:
    return time.time()


def clean_id(msg: can.Message) -> int:
    return msg.arbitration_id & 0x1FFFFFFF


def heartbeat_row(latest: Dict[str, Any]) -> Dict[str, Any]:
    """
    Heartbeat schema requested:
    Timestamp, canister mass, sump mass, pump voltage, pump current,
    dv voltage, dv current, ev1 status (boolean)
    """
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
    }


class HeartbeatCsvLogger:
    FIELDNAMES = [
        "Timestamp",
        "canister_mass",
        "sump_mass",
        "pump_voltage",
        "pump_current",
        "dv_voltage",
        "dv_current",
        "ev1_status",
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
    """
    DB-friendly JSONL: one JSON object per line.
    """
    def __init__(self, jsonl_path: str):
        self._jsonl = open(jsonl_path, "a", buffering=1)

    def write(self, obj: Dict[str, Any]) -> None:
        self._jsonl.write(json.dumps(obj) + "\n")

    def close(self) -> None:
        try:
            self._jsonl.close()
        except Exception:
            pass


async def wait_pico_ready(pico: PicoLink, t: float = 5.0) -> None:
    t0 = time.monotonic()
    last_err: Optional[Exception] = None
    while time.monotonic() - t0 < t:
        try:
            await heartbeat(pico)
            return
        except Exception as e:
            last_err = e
            await asyncio.sleep(0.1)
    raise RuntimeError(f"Pico not responding after {t:.1f}s (last error: {last_err!r})")


async def heartbeat_keepalive_task(pico: PicoLink, period_s: float = 0.5) -> None:
    """
    Keepalive so PicoLink stays responsive and we detect failures quickly.
    This is NOT the 10s CSV heartbeat log.
    """
    try:
        while True:
            try:
                await heartbeat(pico)
            except Exception:
                pass
            await asyncio.sleep(period_s)
    except asyncio.CancelledError:
        pass


async def heartbeat_csv_task(
    pico: PicoLink,
    hb_csv: Optional[HeartbeatCsvLogger],
    event_log: Optional[EventLogger],
    period_s: float = 10.0,
) -> None:
    """
    Your requirement: write heartbeat data from Pico every 10 seconds.
    Also mirrors those rows to events.jsonl as kind="heartbeat".
    """
    try:
        while True:
            if pico.latest:
                row = heartbeat_row(pico.latest)

                if hb_csv:
                    hb_csv.log(row)

                if event_log:
                    event_log.write({"ts": row["Timestamp"], "kind": "heartbeat", **row})

            await asyncio.sleep(max(0.5, period_s))
    except asyncio.CancelledError:
        pass


async def wait_until(
    pico: PicoLink,
    predicate,
    timeout_s: float,
    poll_s: float = 0.05,
    label: str = "condition",
):
    t0 = time.monotonic()
    last = None
    while time.monotonic() - t0 < timeout_s:
        last = pico.latest
        if last and predicate(last):
            return last
        await asyncio.sleep(poll_s)
    raise RuntimeError(f"Timeout waiting for {label} after {timeout_s:.1f}s (last={last})")


def can_send(channel: str, arb_id: int, data: bytes = b"") -> None:
    bus = can.interface.Bus(channel=channel, interface="socketcan", receive_own_messages=True)
    try:
        bus.send(can.Message(arbitration_id=arb_id, is_extended_id=True, data=data))
    finally:
        bus.shutdown()


def can_watch_dispense_done(
    channel: str,
    target_volume_ml: int,
    done_event: threading.Event,
    stop_event: threading.Event,
) -> None:
    """
    Watches CAN for ID_UPDATE_VOLUME and sets done_event when volume >= target.
    """
    bus = can.interface.Bus(channel=channel, interface="socketcan", receive_own_messages=True)
    try:
        while not stop_event.is_set():
            msg = bus.recv(timeout=0.2)
            if not msg:
                continue
            if clean_id(msg) == ID_UPDATE_VOLUME:
                vol = int.from_bytes(msg.data[0:4], "big")
                print(f"[CAN] Dispensed: {vol} ml")
                if vol >= target_volume_ml:
                    print("[CAN] Dispense complete!")
                    done_event.set()
                    return
    finally:
        bus.shutdown()


async def main() -> None:
    ap = argparse.ArgumentParser()

    # Pico serial
    ap.add_argument("--port", default="/dev/ttyACM0")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--stream-hz", type=float, default=10.0)

    # Orchestration targets
    ap.add_argument("--ev", choices=["ev1", "ev2"], default="ev1")
    ap.add_argument("--dest", choices=["TANK1", "TANK2"], default="TANK2")

    # CAN
    ap.add_argument("--can", default="vcan0")
    ap.add_argument("--target-ml", type=int, default=1000)

    # Logging (your key requirement)
    ap.add_argument("--heartbeat-period", type=float, default=10.0)
    ap.add_argument("--heartbeat-csv", default="heartbeat.csv")
    ap.add_argument("--events-jsonl", default="events.jsonl")

    # Drain parameters
    ap.add_argument("--drain-timeout", type=float, default=60.0)
    ap.add_argument("--return-timeout", type=float, default=120.0)
    ap.add_argument("--stable-eps", type=float, default=0.01)
    ap.add_argument("--stable-time", type=float, default=2.0)
    ap.add_argument("--sump-empty", type=float, default=0.05)

    # WAIT conditions between steps
    ap.add_argument("--canister-empty-kg", type=float, default=0.01)
    ap.add_argument("--wait-empty-timeout", type=float, default=30.0)
    ap.add_argument("--wait-sump-ready-timeout", type=float, default=30.0)

    args = ap.parse_args()

    hb_csv = HeartbeatCsvLogger(args.heartbeat_csv) if args.heartbeat_csv else None
    event_log = EventLogger(args.events_jsonl) if args.events_jsonl else None

    pico = PicoLink(args.port, args.baud)
    rx = asyncio.create_task(pico.rx_task())
    keepalive = asyncio.create_task(heartbeat_keepalive_task(pico, 0.5))
    hb_task = asyncio.create_task(heartbeat_csv_task(pico, hb_csv, event_log, args.heartbeat_period))

    dispense_done = threading.Event()
    can_stop = threading.Event()
    watcher = threading.Thread(
        target=can_watch_dispense_done,
        args=(args.can, args.target_ml, dispense_done, can_stop),
        daemon=True,
    )
    watcher.start()

    try:
        await wait_pico_ready(pico, 5.0)
        print("[PICO] Ready")

        # Start Pico streaming
        try:
            await start_stream(pico, args.stream_hz)
        except Exception:
            pass

        # Snapshot at start
        try:
            s0 = await snapshot(pico)
            if event_log:
                event_log.write({"ts": now_ts(), "kind": "event", "event": "snapshot_start", "data": s0})
        except Exception:
            s0 = None

        # -----------------------
        # (1) DISPENSE (CAN)
        # -----------------------
        before_dispense = None
        after_dispense = None
        try:
            before_dispense = await snapshot(pico)
        except Exception:
            pass

        if event_log:
            event_log.write({"ts": now_ts(), "kind": "event", "event": "dispense_before", "before": before_dispense})

        can_send(args.can, ID_OPEN_VALVES, b"")
        if event_log:
            event_log.write({"ts": now_ts(), "kind": "event", "event": "dispense_start", "target_ml": args.target_ml})

        print("[FLOW] Sent dispense start (OPEN_VALVES). Waiting for completion...")

        while not dispense_done.is_set():
            await asyncio.sleep(0.05)

        can_send(args.can, ID_CLOSE_VALVES, b"")
        print("[FLOW] Dispense complete. Sent CLOSE_VALVES.")

        try:
            after_dispense = await snapshot(pico)
        except Exception:
            pass

        if event_log:
            event_log.write(
                {"ts": now_ts(), "kind": "event", "event": "dispense_after", "after": after_dispense}
            )

        # -----------------------
        # (2) DRAIN CANISTER -> SUMP (PICO)
        # -----------------------
        before1 = await snapshot(pico)
        t0 = now_ts()

        res1 = await drain_canister_to_sump(
            pico,
            ev=args.ev,
            timeout_s=args.drain_timeout,
            stable_eps_kg=args.stable_eps,
            stable_time_s=args.stable_time,
        )

        await wait_until(
            pico,
            predicate=lambda s: (s.get("canister_mass_kg") is not None)
            and (float(s["canister_mass_kg"]) <= args.canister_empty_kg),
            timeout_s=args.wait_empty_timeout,
            label=f"canister_mass_kg <= {args.canister_empty_kg}",
        )

        after1 = await snapshot(pico)
        t1 = now_ts()

        if event_log:
            event_log.write(
                {
                    "ts": now_ts(),
                    "kind": "event",
                    "event": "drain_canister_to_sump",
                    "ev": args.ev,
                    "result": res1,
                    "duration_s": res1.get("duration_s", round(t1 - t0, 3)),
                    "before": before1,
                    "after": after1,
                }
            )
        print("[DONE drain_canister]", res1)

        # Wait until sump is non-empty (useful if updates lag)
        await wait_until(
            pico,
            predicate=lambda s: (s.get("sump_mass_kg") is not None)
            and (float(s["sump_mass_kg"]) > float(args.sump_empty) + 0.001),
            timeout_s=args.wait_sump_ready_timeout,
            label=f"sump_mass_kg > sump_empty({args.sump_empty})",
        )

        # -----------------------
        # (3) DRAIN SUMP -> TANK (PICO)
        # -----------------------
        before2 = await snapshot(pico)
        t2 = now_ts()

        res2 = await drain_sump_to_tank(
            pico,
            tank=args.dest,
            timeout_s=args.return_timeout,
            sump_empty_kg=args.sump_empty,
            stable_eps_kg=args.stable_eps,
            stable_time_s=args.stable_time,
        )

        after2 = await snapshot(pico)
        t3 = now_ts()

        if event_log:
            event_log.write(
                {
                    "ts": now_ts(),
                    "kind": "event",
                    "event": "drain_sump_to_tank",
                    "tank": args.dest,
                    "result": res2,
                    "duration_s": res2.get("duration_s", round(t3 - t2, 3)),
                    "before": before2,
                    "after": after2,
                }
            )
        print("[DONE drain_sump]", res2)
        print("[FLOW] Cycle complete ✅")

    finally:
        can_stop.set()

        try:
            await stop_stream(pico)
        except Exception:
            pass

        await safe_stop_pico(pico)

        hb_task.cancel()
        keepalive.cancel()
        rx.cancel()
        await asyncio.gather(hb_task, keepalive, rx, return_exceptions=True)

        pico.close()

        if hb_csv:
            hb_csv.close()
        if event_log:
            event_log.close()


if __name__ == "__main__":
    asyncio.run(main())