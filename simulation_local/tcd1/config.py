from dataclasses import dataclass


@dataclass(frozen=True)
class FailCriteria:
    max_accuracy_drift_pct: float
    pressure_min_bar: float
    pressure_max_bar: float
    pump_current_max_a: float
    dv_current_max_a: float
    voltage_min_v: float
    voltage_max_v: float
    max_sensor_gap_s: float
    can_offline_timeout_s: float


@dataclass(frozen=True)
class TestConfig:
    total_volume_to_pump_l: float
    volume_per_dispense_ml: float
    drain_timeout_s: float = 60.0
    return_timeout_s: float = 120.0
    dispense_timeout_s: float = 120.0
    rest_time_s: float = 0.0