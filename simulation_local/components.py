import time
import random


class Pump:
    def __init__(self, label: str, max_f: float, max_p: float):
        self.label = label
        self.max_f = float(max_f)
        self.max_p = float(max_p)
        self.is_running = False

    def start(self):
        self.is_running = True
        print(f"{self.label} is now ON")

    def stop(self):
        self.is_running = False
        print(f"{self.label} is now OFF")


class MotorizedBallValve:
    def __init__(self, name: str, open_time_s: float = 3.0, close_time_s: float = 3.0):
        self.name = name
        self.position = 0  # 0=closed, 100=open
        self.open_time_s = float(open_time_s)
        self.close_time_s = float(close_time_s)

    def move_to(self, target: int):
        target = max(0, min(100, int(target)))
        if target == self.position:
            return
        duration = (abs(target - self.position) / 100.0) * (
            self.open_time_s if target > self.position else self.close_time_s
        )
        time.sleep(min(duration, 0.05))
        self.position = target


class SolenoidValve:
    def __init__(self, name: str):
        self.name = name
        self.is_open = False

    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False


class DivertingValve:
    def __init__(self, name: str):
        self.name = name
        self.position = "TANK2"

    def set_to(self, tank: str):
        if tank not in ("TANK1", "TANK2"):
            raise ValueError("tank must be TANK1 or TANK2")
        self.position = tank


class LoadCell:
    """
    Simple sim load cell.
    Always returns a float (never None).
    """

    def __init__(self, name: str, capacity_kg: float):
        self.name = name
        self.capacity_kg = float(capacity_kg)
        self._mass_kg = 0.0  # IMPORTANT: initialize

    def set_mass(self, mass_kg: float):
        m = float(mass_kg)
        if m < 0.0:
            m = 0.0
        if m > self.capacity_kg:
            m = self.capacity_kg
        self._mass_kg = m

    def read_mass(self) -> float:
        # Small noise, but always numeric
        noise = random.uniform(-0.003, 0.003)
        v = self._mass_kg + noise
        if v < 0.0:
            v = 0.0
        return float(v)
