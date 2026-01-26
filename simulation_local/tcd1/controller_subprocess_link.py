import asyncio
import json
import sys
import time
from typing import Any, Dict, Optional


class SubprocessControllerLink:
    """
    Controller link that talks to a simulator over stdin/stdout JSON lines.

    Windows note:
      - To avoid "unclosed transport" warnings on Proactor, we provide async aclose()
        that terminates, awaits wait(), and closes the underlying transport.
    """
    def __init__(self, cmd: Optional[list[str]] = None):
        # Default to unbuffered module run (important so stdout flushes immediately)
        self.cmd = cmd or [sys.executable, "-u", "-m", "kp_controller_sim.main"]
        self.proc: Optional[asyncio.subprocess.Process] = None

        self.latest: Optional[Dict[str, Any]] = None
        self.hello: Optional[Dict[str, Any]] = None
        self.last_rx_monotonic = time.monotonic()

        self._next_id = 1
        self._pending: Dict[int, asyncio.Future] = {}

    async def start(self) -> None:
        if self.proc is not None:
            return
        self.proc = await asyncio.create_subprocess_exec(
            *self.cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    async def rx_task(self) -> None:
        if self.proc is None:
            await self.start()
        assert self.proc and self.proc.stdout

        try:
            while True:
                line = await self.proc.stdout.readline()
                if not line:
                    return

                self.last_rx_monotonic = time.monotonic()

                try:
                    msg = json.loads(line.decode("utf-8").strip())
                except Exception:
                    continue

                t = msg.get("type")
                if t == "hello":
                    self.hello = msg
                elif t == "sensors":
                    self.latest = msg.get("data") or {}
                elif t == "cmd_result":
                    cid = msg.get("id")
                    fut = self._pending.pop(cid, None)
                    if fut and not fut.done():
                        if msg.get("ok", False):
                            fut.set_result(msg.get("result"))
                        else:
                            err = msg.get("error") or (msg.get("result") or {}).get("error") or "command failed"
                            fut.set_exception(RuntimeError(str(err)))
        except asyncio.CancelledError:
            # normal shutdown path
            pass

    async def call(self, name: str, args: Dict[str, Any], timeout_s: float) -> Dict[str, Any]:
        if self.proc is None:
            await self.start()
        assert self.proc and self.proc.stdin

        cid = self._next_id
        self._next_id += 1

        fut = asyncio.get_running_loop().create_future()
        self._pending[cid] = fut

        payload = {"type": "cmd", "id": cid, "name": name, "args": args}
        self.proc.stdin.write((json.dumps(payload) + "\n").encode("utf-8"))
        await self.proc.stdin.drain()

        res = await asyncio.wait_for(fut, timeout=timeout_s)
        return res if isinstance(res, dict) else {}

    async def aclose(self) -> None:
        """
        Best-effort async cleanup (recommended on Windows).
        """
        if not self.proc:
            return

        # Cancel any pending callers so they don't hang
        for _, fut in list(self._pending.items()):
            if not fut.done():
                fut.cancel()
        self._pending.clear()

        # Close stdin to signal sim to exit if it cares
        try:
            if self.proc.stdin:
                self.proc.stdin.close()
        except Exception:
            pass

        # Ask process to stop
        if self.proc.returncode is None:
            try:
                self.proc.terminate()
            except Exception:
                pass

            # Wait a bit, then kill if needed
            try:
                await asyncio.wait_for(self.proc.wait(), timeout=2.0)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass
                try:
                    await asyncio.wait_for(self.proc.wait(), timeout=2.0)
                except Exception:
                    pass

        # IMPORTANT: close the underlying transport (fixes Windows "unclosed transport" warnings)
        try:
            tr = getattr(self.proc, "_transport", None)
            if tr:
                tr.close()
        except Exception:
            pass

    def close(self) -> None:
        # Synchronous fallback. Prefer: await aclose()
        if self.proc and self.proc.returncode is None:
            try:
                self.proc.terminate()
            except Exception:
                pass
