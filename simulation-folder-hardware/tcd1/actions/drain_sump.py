from typing import Dict, Any
from tcd1.pico_link import PicoLink


async def drain_sump_to_tank(
    pico: PicoLink,
    tank: str,
    timeout_s: float,
    sump_empty_kg: float = 0.05,
    stable_eps_kg: float = 0.01,
    stable_time_s: float = 2.0,
) -> Dict[str, Any]:
    return await pico.call(
        "drain_sump_to_tank",
        {
            "tank": tank,
            "timeout_s": float(timeout_s),
            "sump_empty_kg": float(sump_empty_kg),
            "stable_eps_kg": float(stable_eps_kg),
            "stable_time_s": float(stable_time_s),
        },
        timeout_s + 10.0,
    )
