import asyncio
import time
from typing import Dict, Any

from components import Pump, MotorizedBallValve, SolenoidValve, LoadCell, DivertingValve


def _now_ts() -> float:
    return time.time()


class SystemController:
    """
    Sim state + actions served via kp_controller_sim/main.py.

    Exposes sensor keys expected by bringup/orchestrate:
      - canister_mass_kg, sump_mass_kg
      - pump_pressure_bar, bus_voltage_v
      - pump_current_a, dv_current_a
      - pump_voltage_v, dv_voltage_v
      - ev1_status, ev2_status
    """

    def __init__(self):
        # Components
        self.pumps = [Pump("Return Pump", 2.7, 380)]
        self.mbvs = [MotorizedBallValve(f"MBV {i}") for i in range(1, 5)]
        self.solenoids = [
            SolenoidValve(n)
            for n in ["Dispense Valve 1", "Dispense Valve 2", "Emptying Valve 1", "Emptying Valve 2"]
        ]
        self.load_cells = [LoadCell("Canister Load Cell", 300), LoadCell("Sump Load Cell", 300)]
        self.diverter = DivertingValve("3-Way Diverter")

        # Mass state (kg)
        self.canister_mass_kg = 5.0
        self.sump_mass_kg = 0.0

        # Stream control
        self.stream_hz = 10.0
        self.stream_enabled = True

        # Electrical/pressure signals (stay inside FailCriteria defaults)
        self.bus_voltage_v = 24.0
        self.pump_current_a = 2.0
        self.dv_current_a = 0.5
        self.pump_pressure_bar = 1.2

        # Valve status flags
        self.ev1_status = False
        self.ev2_status = False

        # Diverter target
        self.tank = "TANK2"

        self._sync_loadcells()

    def _sync_loadcells(self) -> None:
        self.load_cells[0].set_mass(self.canister_mass_kg)
        self.load_cells[1].set_mass(self.sump_mass_kg)

    def sensors(self) -> Dict[str, Any]:
        self._sync_loadcells()
        return {
            "ts": _now_ts(),
            "bus_voltage_v": float(self.bus_voltage_v),
            "pump_pressure_bar": float(self.pump_pressure_bar),
            "pump_current_a": float(self.pump_current_a),
            "dv_current_a": float(self.dv_current_a),
            "pump_voltage_v": float(self.bus_voltage_v),
            "dv_voltage_v": float(self.bus_voltage_v),
            "canister_mass_kg": float(self.load_cells[0].read_mass()),
            "sump_mass_kg": float(self.load_cells[1].read_mass()),
            "ev1_status": bool(self.ev1_status),
            "ev2_status": bool(self.ev2_status),
        }

    async def heartbeat(self) -> Dict[str, Any]:
        return {"ok": True, "ts": _now_ts()}

    async def start_stream(self, hz: float) -> Dict[str, Any]:
        self.stream_hz = max(0.2, float(hz))
        self.stream_enabled = True
        return {"ok": True, "hz": self.stream_hz}

    async def stop_stream(self) -> Dict[str, Any]:
        self.stream_enabled = False
        return {"ok": True}

    async def snapshot(self) -> Dict[str, Any]:
        return {"ok": True, "ts": _now_ts(), "data": self.sensors()}

    async def safe_stop(self) -> Dict[str, Any]:
        self.pumps[0].stop()
        self.ev1_status = False
        self.ev2_status = False
        self.pump_current_a = 0.1
        self.dv_current_a = 0.1
        self.pump_pressure_bar = 0.8
        return {"ok": True}

    async def drain_canister_to_sump(
        self,
        ev: str = "ev1",
        timeout_s: float = 60.0,
        stable_eps_kg: float = 0.01,
        stable_time_s: float = 2.0,
    ) -> Dict[str, Any]:
        ev = ev.lower().strip()
        if ev not in ("ev1", "ev2"):
            raise ValueError("ev must be ev1 or ev2")

        self.ev1_status = (ev == "ev1")
        self.ev2_status = (ev == "ev2")

        self.pumps[0].stop()
        self.pump_current_a = 0.2
        self.dv_current_a = 0.6
        self.pump_pressure_bar = 1.0

        t0 = time.monotonic()
        last_change_t = time.monotonic()
        last_can = float(self.canister_mass_kg)

        rate = 2.0  # kg/s (faster sim)

        while True:
            if time.monotonic() - t0 > float(timeout_s):
                raise RuntimeError("drain_canister_to_sump timed out")

            dt = 0.05
            await asyncio.sleep(dt)

            if self.canister_mass_kg > 0.0:
                d = min(self.canister_mass_kg, rate * dt)
                self.canister_mass_kg -= d
                self.sump_mass_kg += d

            cur_can = float(self.canister_mass_kg)
            if abs(cur_can - last_can) > float(stable_eps_kg):
                last_change_t = time.monotonic()
                last_can = cur_can

            if self.canister_mass_kg <= 0.0:
                break
            if time.monotonic() - last_change_t >= float(stable_time_s):
                break

        self.ev1_status = False
        self.ev2_status = False

        return {
            "ok": True,
            "duration_s": round(time.monotonic() - t0, 3),
            "canister_mass_kg": float(self.canister_mass_kg),
            "sump_mass_kg": float(self.sump_mass_kg),
        }

    async def drain_sump_to_tank(
        self,
        tank: str = "TANK2",
        timeout_s: float = 120.0,
        sump_empty_kg: float = 0.05,
        stable_eps_kg: float = 0.01,
        stable_time_s: float = 2.0,
    ) -> Dict[str, Any]:
        tank = tank.upper().strip()
        if tank not in ("TANK1", "TANK2"):
            raise ValueError("tank must be TANK1 or TANK2")

        self.tank = tank
        self.diverter.set_to(tank)

        self.pumps[0].start()
        self.pump_current_a = 3.0
        self.dv_current_a = 0.5
        self.pump_pressure_bar = 1.6

        t0 = time.monotonic()
        last_change_t = time.monotonic()
        last_sump = float(self.sump_mass_kg)

        rate = 2.0  # kg/s (faster sim)

        while True:
            if time.monotonic() - t0 > float(timeout_s):
                raise RuntimeError("drain_sump_to_tank timed out")

            dt = 0.05
            await asyncio.sleep(dt)

            if self.sump_mass_kg > float(sump_empty_kg):
                d = min(self.sump_mass_kg - float(sump_empty_kg), rate * dt)
                self.sump_mass_kg -= d

            cur_sump = float(self.sump_mass_kg)
            if abs(cur_sump - last_sump) > float(stable_eps_kg):
                last_change_t = time.monotonic()
                last_sump = cur_sump

            if self.sump_mass_kg <= float(sump_empty_kg):
                break
            if time.monotonic() - last_change_t >= float(stable_time_s):
                break

        self.pumps[0].stop()
        self.pump_current_a = 0.2
        self.pump_pressure_bar = 1.0

        return {
            "ok": True,
            "duration_s": round(time.monotonic() - t0, 3),
            "tank": tank,
            "sump_mass_kg": float(self.sump_mass_kg),
        }


