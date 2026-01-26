async def drain_sump_to_tank(
    ctrl,
    tank: str = "TANK2",
    timeout_s: float = 120.0,
    sump_empty_kg: float = 0.05,
    stable_eps_kg: float = 0.01,
    stable_time_s: float = 2.0,
):
    args = {
        "tank": tank,
        "timeout_s": float(timeout_s),
        "sump_empty_kg": float(sump_empty_kg),
        "stable_eps_kg": float(stable_eps_kg),
        "stable_time_s": float(stable_time_s),
        "stable_time_ms": int(float(stable_time_s) * 1000),
    }
    return await ctrl.call("drain_sump_to_tank", args, float(timeout_s) + 5.0)