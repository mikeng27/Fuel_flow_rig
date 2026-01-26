import asyncio
import json
import sys
import time
import traceback
from typing import Dict, Any

from controls import SystemController


def _writeline(obj: Dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


async def _read_stdin_line() -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, sys.stdin.readline)


async def sensor_stream_task(ctrl: SystemController) -> None:
    while True:
        try:
            hz = ctrl.stream_hz if ctrl.stream_enabled else 2.0
            period = 1.0 / max(0.2, float(hz))
            _writeline({"type": "sensors", "data": ctrl.sensors()})
            await asyncio.sleep(period)
        except Exception:
            sys.stderr.write("[kp_controller_sim] sensor_stream_task crashed:\n")
            sys.stderr.write(traceback.format_exc() + "\n")
            sys.stderr.flush()
            await asyncio.sleep(0.5)


async def handle_cmd(ctrl: SystemController, msg: Dict[str, Any]) -> Dict[str, Any]:
    name = msg.get("name")
    args = msg.get("args") or {}
    cid = msg.get("id")

    try:
        if name == "heartbeat":
            res = await ctrl.heartbeat()

        elif name == "start_stream":
            res = await ctrl.start_stream(float(args.get("hz", 10.0)))

        elif name == "stop_stream":
            res = await ctrl.stop_stream()

        elif name == "snapshot":
            res = await ctrl.snapshot()

        elif name == "safe_stop":
            res = await ctrl.safe_stop()

        elif name == "drain_canister_to_sump":
            res = await ctrl.drain_canister_to_sump(
                ev=str(args.get("ev", "ev1")),
                timeout_s=float(args.get("timeout_s", 60.0)),
                stable_eps_kg=float(args.get("stable_eps_kg", 0.01)),
                stable_time_s=float(args.get("stable_time_s", 2.0)),
            )

        elif name == "drain_sump_to_tank":
            res = await ctrl.drain_sump_to_tank(
                tank=str(args.get("tank", "TANK2")),
                timeout_s=float(args.get("timeout_s", 120.0)),
                sump_empty_kg=float(args.get("sump_empty_kg", 0.05)),
                stable_eps_kg=float(args.get("stable_eps_kg", 0.01)),
                stable_time_s=float(args.get("stable_time_s", 2.0)),
            )
        else:
            raise RuntimeError(f"Unknown command: {name!r}")

        return {"type": "cmd_result", "id": cid, "ok": True, "result": res}

    except Exception as e:
        return {"type": "cmd_result", "id": cid, "ok": False, "error": str(e), "result": {}}


async def cmd_loop(ctrl: SystemController) -> None:
    while True:
        line = await _read_stdin_line()

        # stdin closed? don't exit; keep streaming sensors
        if not line:
            await asyncio.sleep(1.0)
            continue

        line = line.strip()
        if not line:
            continue

        try:
            msg = json.loads(line)
        except Exception:
            continue

        if msg.get("type") != "cmd":
            continue

        reply = await handle_cmd(ctrl, msg)
        _writeline(reply)


async def main() -> None:
    sys.stderr.write("[kp_controller_sim] starting\n")
    sys.stderr.flush()

    ctrl = SystemController()
    _writeline({"type": "hello", "ts": time.time(), "name": "kp_controller_sim", "version": "1.0"})

    s_task = asyncio.create_task(sensor_stream_task(ctrl))
    c_task = asyncio.create_task(cmd_loop(ctrl))
    await asyncio.gather(s_task, c_task)


if __name__ == "__main__":
    asyncio.run(main())
