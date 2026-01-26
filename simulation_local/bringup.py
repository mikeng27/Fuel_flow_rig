import argparse
import warnings
warnings.filterwarnings("ignore", category=ResourceWarning)

import logging
logging.getLogger("asyncio").setLevel(logging.CRITICAL)
import asyncio
import time
from typing import Optional

from tcd1.config import FailCriteria, TestConfig
from tcd1.logger import CsvLogger
from tcd1.safety import check_stream, check_limits, safe_stop
from tcd1.actions.heartbeat import heartbeat
from tcd1.actions.data_collect import start_stream, snapshot, stop_stream
from tcd1.actions.drain_canister import drain_canister_to_sump
from tcd1.actions.drain_sump import drain_sump_to_tank


def default_cfg() -> TestConfig:
    return TestConfig(500.0, 5000.0, drain_timeout_s=60.0, return_timeout_s=120.0)


def default_fail() -> FailCriteria:
    return FailCriteria(
        max_accuracy_drift_pct=2.0,
        pressure_min_bar=0.5,
        pressure_max_bar=3.0,
        pump_current_max_a=10.0,
        dv_current_max_a=3.0,
        voltage_min_v=20.0,
        voltage_max_v=28.0,
        max_sensor_gap_s=1.0,
        can_offline_timeout_s=2.0,
    )


async def wait_for_data(ctrl, t: float = 5.0) -> None:
    t0 = time.monotonic()
    while not getattr(ctrl, "latest", None):
        if time.monotonic() - t0 > t:
            raise RuntimeError("No sensor data")
        await asyncio.sleep(0.05)


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


async def make_controller(args):
    if args.controller == "serial":
        from tcd1.controller_link import ControllerLink

        port = ControllerLink.auto_port() if args.port == "auto" else args.port
        if not port:
            raise RuntimeError("No controller port found (use --port or check connection)")
        return ControllerLink(port, args.baud)

    from tcd1.controller_subprocess_link import SubprocessControllerLink

    cmd = args.controller_sim_cmd.split() if args.controller_sim_cmd else None
    ctrl = SubprocessControllerLink(cmd=cmd)
    await ctrl.start()
    return ctrl


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["monitor", "drain-canister", "drain-sump", "snapshot"], default="monitor")

    ap.add_argument("--controller", choices=["sim", "serial"], default="sim")
    ap.add_argument("--controller-sim-cmd", default="python -u -m kp_controller_sim.main", help="Override sim command, e.g. 'python -m kp_controller_sim.main'")

    ap.add_argument("--port", default="auto")
    ap.add_argument("--baud", type=int, default=115200)

    ap.add_argument("--ev", choices=["ev1", "ev2"], default="ev1")
    ap.add_argument("--dest", choices=["TANK1", "TANK2"], default="TANK2")

    ap.add_argument("--stream-hz", type=float, default=10.0)
    ap.add_argument("--print-hz", type=float, default=2.0)
    ap.add_argument("--logcsv", default="")
    ap.add_argument("--stable-eps", type=float, default=0.01)
    ap.add_argument("--stable-time", type=float, default=2.0)
    ap.add_argument("--sump-empty", type=float, default=0.05)
    ap.add_argument("--no-stream", action="store_true")
    args = ap.parse_args()

    ctrl = await make_controller(args)
    rx = asyncio.create_task(ctrl.rx_task())
    hb = asyncio.create_task(heartbeat_task(ctrl, 0.5))

    logger: Optional[CsvLogger] = CsvLogger(args.logcsv) if args.logcsv else None
    cfg = default_cfg()
    crit = default_fail()

    try:
        await wait_controller_ready(ctrl, 5.0)
        print("[READY] Controller responding")

        if getattr(ctrl, "hello", None):
            print("[HELLO]", ctrl.hello)

        if not args.no_stream:
            try:
                await start_stream(ctrl, args.stream_hz)
            except Exception:
                pass

        if args.mode == "snapshot":
            print(await snapshot(ctrl))

        elif args.mode == "monitor":
            await wait_for_data(ctrl)
            period = 1.0 / max(0.2, args.print_hz)
            while True:
                check_stream(ctrl, crit)
                check_limits(ctrl, crit)
                print(ctrl.latest)
                if logger:
                    logger.log(ctrl.latest)
                await asyncio.sleep(period)

        elif args.mode == "drain-canister":
            await wait_for_data(ctrl)
            check_stream(ctrl, crit)
            check_limits(ctrl, crit)
            res = await drain_canister_to_sump(
                ctrl,
                ev=args.ev,
                timeout_s=cfg.drain_timeout_s,
                stable_eps_kg=args.stable_eps,
                stable_time_s=args.stable_time,
            )
            print("[DONE]", res)

        elif args.mode == "drain-sump":
            await wait_for_data(ctrl)
            check_stream(ctrl, crit)
            check_limits(ctrl, crit)
            res = await drain_sump_to_tank(
                ctrl,
                tank=args.dest,
                timeout_s=cfg.return_timeout_s,
                sump_empty_kg=args.sump_empty,
                stable_eps_kg=args.stable_eps,
                stable_time_s=args.stable_time,
            )
            print("[DONE]", res)

    finally:
        try:
            await stop_stream(ctrl)
        except Exception:
            pass

        await safe_stop(ctrl)

        if logger:
            logger.close()

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


if __name__ == "__main__":
    asyncio.run(main())




