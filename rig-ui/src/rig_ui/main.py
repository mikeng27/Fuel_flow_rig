import gi
import random
import time

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib


# --- The Emulator (Logic Layer) ---
class RigEmulator:
    def __init__(self):
        self.is_active = False
        self.total_volume = 0.0

    def get_latest_data(self):
        """Simulates data from flow meter, pump, and valves[cite: 173]."""
        if not self.is_active:
            return None

        # Simulate sensor readings based on PRD requirements [cite: 33, 174]
        return {
            "flow_rate": round(random.uniform(4.8, 5.2), 2),
            "total_volume": round(self.total_volume + random.uniform(0.1, 0.2), 2),
            "pressure": round(random.uniform(28.0, 30.0), 1),
            "valve_state": "OPEN" if random.random() > 0.1 else "TRANSITION"
        }


# --- The GTK Application (Presentation Layer) ---
class KPFuelFlowApp(Gtk.Window):
    def __init__(self, emulator):
        super().__init__(title="KP Fuel Flow Rig - Live Monitor")
        self.emulator = emulator
        self.set_default_size(400, 300)
        self.set_border_width(20)

        # Layout
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.add(vbox)

        # UI Labels for Metrics [cite: 92, 113]
        self.status_label = Gtk.Label(label="<b>System Idle</b>", use_markup=True)
        self.flow_label = Gtk.Label(label="Flow Rate: 0.0 LPM")
        self.vol_label = Gtk.Label(label="Total Volume: 0.0 L")
        self.press_label = Gtk.Label(label="Pump Pressure: 0.0 PSI")

        for lbl in [self.status_label, self.flow_label, self.vol_label, self.press_label]:
            vbox.pack_start(lbl, True, True, 0)

        # Toggle Button
        self.toggle_btn = Gtk.ToggleButton(label="Start Test")
        self.toggle_btn.connect("toggled", self.on_emulator_toggle)
        vbox.pack_start(self.toggle_btn, True, True, 0)

        # Start the Polling Loop (Update every 1000ms)
        GLib.timeout_add(1000, self.update_dashboard)

    def on_emulator_toggle(self, button):
        if button.get_active():
            self.emulator.is_active = True
            button.set_label("Stop Emulator")
            self.status_label.set_markup("<span foreground='green'><b>Emulator Active</b></span>")
        else:
            self.emulator.is_active = False
            button.set_label("Activate Emulator")
            self.status_label.set_markup("<span foreground='red'><b>System Idle</b></span>")

    def update_dashboard(self):
        """Fetches data from emulator and updates UI[cite: 34, 155]."""
        data = self.emulator.get_latest_data()

        if data:
            self.emulator.total_volume = data["total_volume"]  # Persistent volume
            self.flow_label.set_text(f"Flow Rate: {data['flow_rate']} LPM")
            self.vol_label.set_text(f"Total Volume: {data['total_volume']} L")
            self.press_label.set_text(f"Pump Pressure: {data['pressure']} PSI")
            print(f"Logged Data: {data}")  # Mimics data logging function [cite: 122]

        return True  # Keep the timeout active


# --- Main Entry Point ---
if __name__ == "__main__":
    emulator_instance = RigEmulator()
    win = KPFuelFlowApp(emulator_instance)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()