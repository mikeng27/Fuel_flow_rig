from typing import Dict, Any
from tcd1.pico_link import PicoLink


async def heartbeat(pico: PicoLink) -> Dict[str, Any]:
    return await pico.call("heartbeat", {}, 2.0)