import random
import threading
from datetime import datetime
from fsm.fdm_state_machine import FDMStateMachine  # adjust if needed

class FDMEmulator:
    """FDM Emulator fully integrated with FDMStateMachine and YAML config."""

    def __init__(self, fsm_obj=None, io_config=None):
        self.fsm = fsm_obj
        self.io_config = io_config or {}
        self.total_dispensed = 0.0

        # Initialize FDM State Machine
        self.fdm_sm = FDMStateMachine()
        self.fdm_sm.connect("dispense_started", self._on_dispense_started)
        self.fdm_sm.connect("dispense_updated", self._on_dispense_updated)
        self.fdm_sm.connect("dispense_stopped", self._on_dispense_stopped)

        # Setup internal state for pumps and valves
        self.pumps = {pid: False for pid in self.io_config.get("actuators", {}) if "pump" in pid.lower()}
        self.valves = {vid: False for vid in self.io_config.get("actuators", {}) if "valve" in vid.lower()}

        # Start the periodic update loop
        self._start_update_loop()

    # ----------------------
    # Public interface
    # ----------------------
    def toggle_pump(self, pump_id, state: bool):
        if pump_id in self.pumps:
            self.pumps[pump_id] = state

    def toggle_valve(self, valve_id, state: bool):
        if valve_id in self.valves:
            self.valves[valve_id] = state

    def get_flow(self, pump_id="pump_1"):
        if not self.pumps.get(pump_id, False):
            return 0.0
        flow_cfg = self.io_config["actuators"].get(pump_id, {}).get("flow", {})
        flow = round(random.uniform(flow_cfg.get("min", 0.0), flow_cfg.get("max", 1.0)), 2)
        self.total_dispensed += flow / 60
        return flow

    def get_pressure(self, pump_id="pump_1"):
        if not self.pumps.get(pump_id, False):
            return 0.0
        press_cfg = self.io_config["actuators"].get(pump_id, {}).get("pressure", {})
        return round(random.uniform(press_cfg.get("min", 0), press_cfg.get("max", 100)), 2)

    def get_dispense_status(self, valve_id):
        return self.valves.get(valve_id, False)

    # ----------------------
    # Internal signal handlers
    # ----------------------
    def _on_dispense_started(self, sm, volume):
        print(f"[FDM] Dispense started: {volume} L")
        for valve_id in self.valves:
            self.toggle_valve(valve_id, True)

    def _on_dispense_updated(self, sm, volume):
        self.total_dispensed += volume
        print(f"[FDM] Dispense updated: {volume:.2f} L | Total: {self.total_dispensed:.2f} L")

    def _on_dispense_stopped(self, sm):
        print("[FDM] Dispense stopped")
        for valve_id in self.valves:
            self.toggle_valve(valve_id, False)

    # ----------------------
    # Periodic logging / updates
    # ----------------------
    def _update_status(self):
        ts = datetime.now().strftime("%H:%M:%S")
        for pump_id in self.pumps:
            flow = self.get_flow(pump_id)
            pressure = self.get_pressure(pump_id)
            print(f"{ts} | {pump_id} | Flow: {flow} L/min | Pressure: {pressure} mbar | Total: {self.total_dispensed:.2f} L")
        for valve_id in self.valves:
            status = self.get_dispense_status(valve_id)
            print(f"{ts} | {valve_id} | Status: {'OPEN' if status else 'CLOSED'}")

    def _start_update_loop(self):
        """Start a repeating thread that updates status every second."""
        def loop():
            while True:
                self._update_status()
                threading.Event().wait(1.0)  # wait 1 second
        threading.Thread(target=loop, daemon=True).start()


# ----------------------
# Main entry point
# ----------------------
def main(fsm_obj=None, io_config=None):
    fdm_emulator = FDMEmulator(fsm_obj=fsm_obj, io_config=io_config)

    # Turn on all pumps and valves for testing
    for pump in fdm_emulator.pumps:
        fdm_emulator.toggle_pump(pump, True)
    for valve in fdm_emulator.valves:
        fdm_emulator.toggle_valve(valve, True)

    return fdm_emulator
