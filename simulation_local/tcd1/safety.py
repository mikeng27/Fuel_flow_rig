import time
from tcd1.config import FailCriteria


def check_stream(ctrl, crit: FailCriteria) -> None:
    last = getattr(ctrl, "last_rx_monotonic", None)
    if last is None:
        raise RuntimeError("Missing last_rx_monotonic on controller link")

    if time.monotonic() - last > crit.max_sensor_gap_s:
        raise RuntimeError("Sensor stream timeout")


def check_limits(ctrl, crit: FailCriteria) -> None:
    s = getattr(ctrl, "latest", None) or {}

    p = s.get("pump_pressure_bar")
    if p is not None and not (crit.pressure_min_bar <= float(p) <= crit.pressure_max_bar):
        raise RuntimeError("Pressure limit exceeded")

    v = s.get("bus_voltage_v")
    if v is not None and not (crit.voltage_min_v <= float(v) <= crit.voltage_max_v):
        raise RuntimeError("Voltage limit exceeded")

    pump_i = s.get("pump_current_a")
    if pump_i is not None and float(pump_i) > crit.pump_current_max_a:
        raise RuntimeError("Pump current limit exceeded")

    dv_i = s.get("dv_current_a")
    if dv_i is not None and float(dv_i) > crit.dv_current_max_a:
        raise RuntimeError("DV current limit exceeded")


async def safe_stop(ctrl) -> None:
    try:
        await ctrl.call("safe_stop", {}, 2.0)
    except Exception:
        pass