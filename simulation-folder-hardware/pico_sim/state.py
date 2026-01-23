import math
import time

def now_ms():
    return time.ticks_ms()

class SimState:
    def __init__(self):
        # masses (kg)
        self.canister_mass_kg = 1.50
        self.sump_mass_kg = 0.20
        self.tank1_mass_kg = 5.00
        self.tank2_mass_kg = 5.00

        # safety-critical signals (Pi checks these keys!)
        self.bus_voltage_v = 24.0
        self.pump_pressure_bar = 1.0

        # extra telemetry (optional)
        self.pump_current_a = 1.0
        self.dv_current_a = 0.2

        # stream control
        self.stream_enabled = False
        self.stream_hz = 10.0
        self.stream_pause_until_ms = 0

        # deterministic behavior controls
        self.deterministic = True
        self.sim_tick = 0  # fixed-step sim clock tick counter

        # faults and scenario (faults.py)
        self.faults = []
        self.scenario_name = ""
        self.scenario_start_ms = now_ms()
        self.scenario = []
        self.scenario_period_ms = 0
        self._scenario_fired = set()
        self._scenario_last_elapsed = None

        # active job (sim.py)
        self.job = None
        self._stable_start_ms = None

    def clamp_nonneg(self):
        self.canister_mass_kg = max(0.0, self.canister_mass_kg)
        self.sump_mass_kg = max(0.0, self.sump_mass_kg)
        self.tank1_mass_kg = max(0.0, self.tank1_mass_kg)
        self.tank2_mass_kg = max(0.0, self.tank2_mass_kg)

    def sensors_dict(self):
        # Deterministic, repeatable wiggle (no randomness)
        if self.deterministic:
            n_p = 0.01 * math.sin(self.sim_tick * 0.05)
            n_v = 0.02 * math.sin(self.sim_tick * 0.03)
        else:
            n_p = 0.0
            n_v = 0.0

        return {
            # REQUIRED: your Pi safety reads these
            "pump_pressure_bar": float(self.pump_pressure_bar + n_p),
            "bus_voltage_v": float(self.bus_voltage_v + n_v),

            # Helpful extras for logs/plots
            "canister_mass_kg": float(self.canister_mass_kg),
            "sump_mass_kg": float(self.sump_mass_kg),
            "tank1_mass_kg": float(self.tank1_mass_kg),
            "tank2_mass_kg": float(self.tank2_mass_kg),
            "pump_current_a": float(self.pump_current_a),
            "dv_current_a": float(self.dv_current_a),

            "stream_hz": float(self.stream_hz),
            "job": self.job["type"] if self.job else "",
            "sim_tick": int(self.sim_tick),
            "scenario": self.scenario_name,
        }
