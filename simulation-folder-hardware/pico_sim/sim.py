import uasyncio as asyncio
import time
from proto import send_msg
from faults import apply_faults, apply_scenario, add_fault

def _ms_since(t0):
    return time.ticks_diff(time.ticks_ms(), t0)

def flow_rate_kg_s_for_ev(ev):
    return 0.12 if ev == "ev2" else 0.09

def pump_flow_kg_s():
    return 0.10

def check_stable(state, job, dm, dt_s):
    rate = abs(dm / max(1e-6, dt_s))
    is_stable = rate < job["stable_eps_kg"]

    t = time.ticks_ms()
    if is_stable:
        if state._stable_start_ms is None:
            state._stable_start_ms = t
        elif time.ticks_diff(t, state._stable_start_ms) >= job["stable_time_ms"]:
            return True
    else:
        state._stable_start_ms = None
    return False

async def sim_tick_task(state, tick_hz=100.0):
    dt_s = 1.0 / tick_hz
    tick_ms = int(1000 / tick_hz)

    while True:
        # nominal values each tick; faults may override
        state.bus_voltage_v = 24.0
        state.pump_pressure_bar = 1.0
        state.pump_current_a = 1.0
        state.dv_current_a = 0.2

        job = state.job
        if job:
            elapsed = _ms_since(job["started_ms"])
            if elapsed > job["timeout_ms"]:
                cid = job["cid"]
                jtype = job["type"]
                moved = job.get("moved_kg", 0.0)
                state.job = None
                send_msg({"type": "cmd_result", "id": cid, "ok": False, "error": f"{jtype} timeout", "result": {"moved_kg": moved}})
            else:
                if job["type"] == "drain_canister_to_sump":
                    ev = job["ev"]
                    fr = flow_rate_kg_s_for_ev(ev)
                    dm = min(state.canister_mass_kg, fr * dt_s)
                    state.canister_mass_kg -= dm
                    state.sump_mass_kg += dm
                    job["moved_kg"] += dm

                    state.pump_pressure_bar = 1.2 + 6.0 * fr
                    state.dv_current_a = 0.3 + 2.0 * fr

                    done = (state.canister_mass_kg <= 0.001) or check_stable(state, job, dm, dt_s)
                    if done:
                        cid = job["cid"]
                        moved = job["moved_kg"]
                        dur_s = elapsed / 1000.0
                        state.job = None
                        send_msg({"type": "cmd_result", "id": cid, "ok": True, "result": {"status": "done", "moved_kg": moved, "duration_s": dur_s, "ev": ev}})

                elif job["type"] == "drain_sump_to_tank":
                    tank = job["tank"]
                    fr = pump_flow_kg_s()
                    dm = min(state.sump_mass_kg, fr * dt_s)
                    state.sump_mass_kg -= dm
                    if tank == "TANK1":
                        state.tank1_mass_kg += dm
                    else:
                        state.tank2_mass_kg += dm
                    job["moved_kg"] += dm

                    state.pump_pressure_bar = 1.4 + 7.0 * fr
                    state.pump_current_a = 1.5 + 8.0 * fr

                    done = (state.sump_mass_kg <= job["sump_empty_kg"]) or check_stable(state, job, dm, dt_s)
                    if done:
                        cid = job["cid"]
                        moved = job["moved_kg"]
                        dur_s = elapsed / 1000.0
                        state.job = None
                        send_msg({"type": "cmd_result", "id": cid, "ok": True, "result": {"status": "done", "moved_kg": moved, "duration_s": dur_s, "tank": tank}})

        state.clamp_nonneg()

        # scenario currently no-op; faults may still be set manually later
        apply_scenario(state, add_fault)
        apply_faults(state)

        state.sim_tick += 1
        await asyncio.sleep_ms(tick_ms)

async def sensor_stream_task(state, tick_hz=100.0):
    while True:
        if not state.stream_enabled:
            await asyncio.sleep_ms(50)
            continue

        if time.ticks_diff(state.stream_pause_until_ms, time.ticks_ms()) > 0:
            await asyncio.sleep_ms(50)
            continue

        ticks_per_msg = int(max(1, round(tick_hz / max(0.2, state.stream_hz))))
        if (state.sim_tick % ticks_per_msg) == 0:
            send_msg({"type": "sensors", "data": state.sensors_dict()})

        await asyncio.sleep_ms(5)
