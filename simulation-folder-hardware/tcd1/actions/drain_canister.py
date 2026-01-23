from typing import Dict, Any
from tcd1.pico_link import PicoLink


async def drain_canister_to_sump(
    pico: PicoLink,
    ev: str,
    timeout_s: float,
    stable_eps_kg: float = 0.01,
    stable_time_s: float = 2.0,
) -> Dict[str, Any]:
    return await pico.call(
        "drain_canister_to_sump",
        {
            "ev": ev,
            "timeout_s": float(timeout_s),
            "stable_eps_kg": float(stable_eps_kg),
            "stable_time_s": float(stable_time_s),
        },
        timeout_s + 10.0,
    )
