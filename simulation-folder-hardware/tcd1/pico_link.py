import asyncio
import json
import time
from typing import Any, Dict, Optional

import serial
from serial.tools import list_ports


class PicoCommandError(RuntimeError):
    pass


class PicoProtocolError(RuntimeError):
    pass


class PicoLink:
    def __init__(self, port: str, baud: int = 115200):
        self.ser = serial.Serial(port, baudrate=baud, timeout=0.2)
        self.last_rx_monotonic = time.monotonic()
        self.latest: Dict[str, Any] = {}
        self._tx_lock = asyncio.Lock()
        self._pending: Dict[int, asyncio.Future] = {}
        self._next_id = 1

        self.hello: Dict[str, Any] = {}
        self._hello_event = asyncio.Event()

    @staticmethod
    def list_ports() -> list[str]:
        return [p.device for p in list_ports.comports()]

    @staticmethod
    def auto_port() -> Optional[str]:
        ports = list_ports.comports()

        def score(p) -> int:
            txt = f"{p.description} {p.manufacturer} {p.product} {p.hwid}".lower()
            s = 0
            if "pico" in txt:
                s += 10
            if "raspberry" in txt:
                s += 5
            if "usb" in txt:
                s += 1
            if "acm" in p.device.lower():
                s += 2
            return s

        best = None
        best_s = 0
        for p in ports:
            sc = score(p)
            if sc > best_s:
                best_s = sc
                best = p.device

        return best if best_s > 0 else None

    def _cmd_id(self) -> int:
        cid = self._next_id
        self._next_id += 1
        return cid

    async def send(self, msg: Dict[str, Any]) -> None:
        data = (json.dumps(msg) + "\n").encode()
        async with self._tx_lock:
            await asyncio.to_thread(self.ser.write, data)
            await asyncio.to_thread(self.ser.flush)

    async def call(self, name: str, args: Dict[str, Any], timeout_s: float) -> Dict[str, Any]:
        cid = self._cmd_id()
        fut = asyncio.get_running_loop().create_future()
        self._pending[cid] = fut
        await self.send({"type": "cmd", "id": cid, "name": name, "args": args})

        try:
            resp = await asyncio.wait_for(fut, timeout_s)
        finally:
            self._pending.pop(cid, None)

        if not isinstance(resp, dict):
            raise PicoCommandError("Malformed cmd_result")

        if not resp.get("ok", False):
            raise PicoCommandError(resp.get("error", "command failed"))

        result = resp.get("result", {})
        return result if isinstance(result, dict) else {}

    async def wait_hello(self, timeout_s: float = 5.0) -> Dict[str, Any]:
        try:
            await asyncio.wait_for(self._hello_event.wait(), timeout_s)
        except asyncio.TimeoutError as e:
            raise PicoProtocolError("No hello from Pico (firmware handshake missing?)") from e
        return self.hello

    async def rx_task(self) -> None:
        try:
            while True:
                line = await asyncio.to_thread(self.ser.readline)
                if not line:
                    await asyncio.sleep(0.01)
                    continue

                try:
                    msg = json.loads(line.decode(errors="ignore"))
                except Exception:
                    continue

                if not isinstance(msg, dict):
                    continue

                t = msg.get("type")

                if t == "hello":
                    self.hello = msg
                    self._hello_event.set()

                elif t == "sensors":
                    data = msg.get("data", {})
                    if isinstance(data, dict):
                        self.latest = data
                        self.last_rx_monotonic = time.monotonic()

                elif t == "cmd_result":
                    cid = msg.get("id")
                    fut = self._pending.get(cid)
                    if isinstance(cid, int) and fut and not fut.done():
                        fut.set_result(msg)

                elif t == "log":
                    m = msg.get("msg", "")
                    print(f"[PICO] {m}")

        except asyncio.CancelledError:
            pass

    def close(self) -> None:
        self.ser.close()
