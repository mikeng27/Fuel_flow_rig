from typing import Dict, Any
from tcd1.pico_link import PicoLink


async def start_stream(pico: PicoLink, hz: float) -> Dict[str, Any]:
    return await pico.call("start_stream", {"hz": float(hz)}, 3.0)


async def stop_stream(pico: PicoLink) -> Dict[str, Any]:
    return await pico.call("stop_stream", {}, 3.0)


async def snapshot(pico: PicoLink) -> Dict[str, Any]:
    return await pico.call("snapshot", {}, 3.0)
