import argparse
import asyncio
import time
from typing import Optional

from tcd1.config import FailCriteria, TestConfig
from tcd1.logger import CsvLogger
from tcd1.pico_link import PicoLink
from tcd1.safety import check_pico_stream, check_rig_limits, safe_stop_pico
from tcd1.actions.heartbeat import heartbeat
from tcd1.actions.data_collect import start_stream, snapshot, stop_stream
from tcd1.actions.drain_canister import drain_canister_to_sump
from tcd1.actions.drain_sump import drain_sump_to_tank


def default_cfg() -> TestConfig:
    return TestConfig(500.0, 5000.0, drain_timeout_s=60.0, return_timeout_s=120.0)


def default_fail() -> FailCriteria:
    return FailCriteria(2.0, 0.5, 3.0, 10.0, 3.0, 20.0, 28.0, 1.0, 2.0)


async def wait_for_data(pico: PicoLink, t: float = 5.0) -> None:
    t0 = time.monotonic()
    while not pico.latest:
        if time.monotonic() - t0 > t:
            raise RuntimeError("No sensor data")
        await asyncio.sleep(0.05)


async def wait_pico_ready(pico: PicoLink, t: float = 5.0) -> None:
    """
    Don't require hello; just wait until Pico responds to a command.
    This avoids missing the hello if it was sent before the Pi connected.
    """
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


async def heartbeat_task(pico: PicoLink, period_s: float = 0.5) -> None:
    try:
        while True:
            try:
                await heartbeat(pico)
            except Exception:
                pass
            await asyncio.sleep(period_s)
    except asyncio.CancelledError:
        pass


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["monitor", "drain-canister", "drain-sump", "snapshot"], default="monitor")
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
    ap.add_argument("--no-stream", action="store_true", help="Do not start streaming automatically")
    args = ap.parse_args()

    port = PicoLink.auto_port() if args.port == "auto" else args.port
    if not port:
        raise RuntimeError("No Pico port found (use --port or check connection)")

    pico = PicoLink(port, args.baud)
    rx = asyncio.create_task(pico.rx_task())
    hb = asyncio.create_task(heartbeat_task(pico, 0.5))

    logger: Optional[CsvLogger] = CsvLogger(args.logcsv) if args.logcsv else None
    cfg = default_cfg()
    crit = default_fail()

    try:
        # ✅ robust "ready" check
        await wait_pico_ready(pico, 5.0)
        print("[READY] Pico responding")

        # If hello arrives later, print it (non-blocking)
        if pico.hello:
            print("[HELLO]", pico.hello)

        # Start stream unless disabled
        if not args.no_stream:
            try:
                await start_stream(pico, args.stream_hz)
            except Exception:
                pass

        if args.mode == "snapshot":
            print(await snapshot(pico))

        elif args.mode == "monitor":
            await wait_for_data(pico)
            period = 1.0 / max(0.2, args.print_hz)
            while True:
                check_pico_stream(pico, crit)
                check_rig_limits(pico, crit)
                print(pico.latest)
                if logger:
                    logger.log(pico.latest)
                await asyncio.sleep(period)

        elif args.mode == "drain-canister":
            await wait_for_data(pico)
            check_pico_stream(pico, crit)
            check_rig_limits(pico, crit)
            res = await drain_canister_to_sump(
                pico,
                ev=args.ev,
                timeout_s=cfg.drain_timeout_s,
                stable_eps_kg=args.stable_eps,
                stable_time_s=args.stable_time,
            )
            print("[DONE]", res)

        elif args.mode == "drain-sump":
            await wait_for_data(pico)
            check_pico_stream(pico, crit)
            check_rig_limits(pico, crit)
            res = await drain_sump_to_tank(
                pico,
                tank=args.dest,
                timeout_s=cfg.return_timeout_s,
                sump_empty_kg=args.sump_empty,
                stable_eps_kg=args.stable_eps,
                stable_time_s=args.stable_time,
            )
            print("[DONE]", res)

    finally:
        # Stop stream if possible (optional)
        try:
            await stop_stream(pico)
        except Exception:
            pass

        await safe_stop_pico(pico)
        if logger:
            logger.close()
        hb.cancel()
        rx.cancel()
        await asyncio.gather(hb, rx, return_exceptions=True)
        pico.close()


if __name__ == "__main__":
    asyncio.run(main())
