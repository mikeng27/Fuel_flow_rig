import random
import time
from datetime import datetime


class RigEmulator:
    def __init__(self):
        # Initial states
        self.valve_open = False
        self.pump_active = False
        self.total_volume = 0.0
        # Simulation of "Accuracy Drift" factor [cite: 10]
        self.drift_factor = 1.0

    def get_valve_status(self, valve_id="MBV1"):
        """Randomly generates valve state or returns current logic state."""
        state = "OPEN" if self.valve_open else "CLOSED"
        # Adding a 1% chance of a 'stuck' valve for failure testing [cite: 35]
        if random.random() < 0.01:
            return f"{valve_id}_ERROR_STUCK"
        return f"{valve_id}_STATUS_{state}"

    def get_pump_data(self):
        """Generates pump pressure (PSI) and current consumption (Amps)."""
        if not self.pump_active:
            return {"pressure": 0.0, "current": 0.05}  # Standby current

        # Simulating operational noise [cite: 33]
        pressure = random.uniform(25.5, 30.2)
        current = random.uniform(2.1, 2.8)
        return {"pressure": round(pressure, 2), "current": round(current, 2)}

    def get_flow_meter_reading(self):
        """Generates flow rate (LPM) and increments total volume."""
        if not self.pump_active or not self.valve_open:
            return {"flow_rate": 0.0, "total_volume": round(self.total_volume, 2)}

        # Base flow rate influenced by random turbulence [cite: 33]
        flow_rate = random.uniform(4.5, 5.5) * self.drift_factor

        # Increment volume (simulating 1 second of flow)
        increment = flow_rate / 60
        self.total_volume += increment

        return {
            "flow_rate": round(flow_rate, 2),
            "total_volume": round(self.total_volume, 2)
        }


# --- Execution Loop ---
rig = RigEmulator()
rig.pump_active = True  # Simulate starting a test [cite: 175]
rig.valve_open = True

print(f"{'Timestamp':<20} | {'Valve':<12} | {'Flow (LPM)':<10} | {'Total (L)':<10} | {'PSI':<6}")
print("-" * 70)

try:
    for _ in range(100):
        v_status = rig.get_valve_status()
        p_data = rig.get_pump_data()
        f_data = rig.get_flow_meter_reading()
        ts = datetime.now().strftime("%H:%M:%S")

        print(
            f"{ts:<20} | {v_status:<12} | {f_data['flow_rate']:<10} | {f_data['total_volume']:<10} | {p_data['pressure']:<6}")
        time.sleep(1)
except KeyboardInterrupt:
    print("\nSimulation stopped.")