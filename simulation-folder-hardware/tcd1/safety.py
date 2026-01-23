import time
from tcd1.config import FailCriteria
from tcd1.pico_link import PicoLink


def check_pico_stream(pico: PicoLink, crit: FailCriteria) -> None:
    if time.monotonic() - pico.last_rx_monotonic > crit.max_sensor_gap_s:
        raise RuntimeError("Sensor stream timeout")


def check_rig_limits(pico: PicoLink, crit: FailCriteria) -> None:
    s = pico.latest or {}

    p = s.get("pump_pressure_bar")
    if p is not None and not (crit.pressure_min_bar <= p <= crit.pressure_max_bar):
        raise RuntimeError("Pressure limit exceeded")

    v = s.get("bus_voltage_v")
    if v is not None and not (crit.voltage_min_v <= v <= crit.voltage_max_v):
        raise RuntimeError("Voltage limit exceeded")


async def safe_stop_pico(pico: PicoLink) -> None:
    try:
        await pico.call("safe_stop", {}, 2.0)
    except Exception:
        pass
