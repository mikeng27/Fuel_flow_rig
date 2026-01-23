import time

def add_fault(state, ftype, duration_s=3.0, value=None):
    end_ms = time.ticks_add(time.ticks_ms(), int(duration_s * 1000))
    f = {"type": str(ftype), "end_ms": end_ms}
    if value is not None:
        try:
            f["value"] = float(value)
        except Exception:
            pass
    state.faults.append(f)

    if ftype == "stream_pause":
        state.stream_pause_until_ms = end_ms

def clear_faults(state):
    state.faults = []
    state.stream_pause_until_ms = 0

def apply_faults(state):
    t = time.ticks_ms()
    state.faults = [f for f in state.faults if time.ticks_diff(f["end_ms"], t) > 0]

    for f in state.faults:
        ft = f["type"]
        if ft == "pressure_high":
            state.pump_pressure_bar = f.get("value", 4.2)
        elif ft == "pressure_low":
            state.pump_pressure_bar = f.get("value", 0.1)
        elif ft == "voltage_high":
            state.bus_voltage_v = f.get("value", 30.0)
        elif ft == "voltage_low":
            state.bus_voltage_v = f.get("value", 18.0)
        elif ft == "stream_pause":
            pass

def set_scenario(state, name):
    state.scenario_name = str(name)
    state.scenario_start_ms = time.ticks_ms()
    state._scenario_fired = set()
    state._scenario_last_elapsed = None

    # Leave scenarios empty for now (you said you want to skip fault injection initially)
    state.scenario = []
    state.scenario_period_ms = 0

def _scenario_elapsed_ms(state):
    return time.ticks_diff(time.ticks_ms(), state.scenario_start_ms)

def apply_scenario(state, add_fault_fn):
    # No-op until you enable scenarios
    return
