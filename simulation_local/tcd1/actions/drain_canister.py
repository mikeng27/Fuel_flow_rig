async def drain_canister_to_sump(
    ctrl,
    ev: str = "ev1",
    timeout_s: float = 60.0,
    stable_eps_kg: float = 0.01,
    stable_time_s: float = 2.0,
):
    args = {
        "ev": ev,
        "timeout_s": float(timeout_s),
        "stable_eps_kg": float(stable_eps_kg),
        "stable_time_s": float(stable_time_s),
        "stable_time_ms": int(float(stable_time_s) * 1000),
    }
    return await ctrl.call("drain_canister_to_sump", args, float(timeout_s) + 5.0)