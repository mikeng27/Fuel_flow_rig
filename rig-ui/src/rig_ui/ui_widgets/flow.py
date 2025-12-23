import gi
import random

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Pango


# --- Backend Logic: Actuator & Sensor Emulator ---
class RigEmulator:
    def __init__(self):
        self.is_running = False
        self.pump_active = False
        self.valve_open = False  # MBV1 state
        self.flow_rate = 0.0
        self.total_volume = 0.0

    def update_step(self):
        if self.is_running:
            # Logic: Valve must be open for flow, pump must be on
            if self.pump_active and self.valve_open:
                self.flow_rate = random.uniform(4.9, 5.1)
                self.total_volume += (self.flow_rate / 60)
            else:
                self.flow_rate = 0.0
        return {
            "pump": "RUNNING" if self.pump_active else "IDLE",
            "valve": "OPEN" if self.valve_open else "CLOSED",
            "flow": round(self.flow_rate, 2),
            "vol": round(self.total_volume, 2)
        }


# --- Frontend UI: GTK Notebook Application ---
class FuelRigApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Automated KP Fuel Flow Rig v1.0")
        self.set_default_size(800, 480)
        self.emulator = RigEmulator()

        # Main Container
        self.notebook = Gtk.Notebook()
        self.add(self.notebook)

        # Build Tabs
        self.init_setup_tab()
        self.init_monitor_tab()

        # Start Polling (1 second interval)
        GLib.timeout_add(1000, self.on_poll_data)

    def init_setup_tab(self):
        """Tab 1: Test Configuration"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20, margin=20)

        title = Gtk.Label(label="<b>Test Configuration</b>", use_markup=True)
        box.pack_start(title, False, False, 0)

        grid = Gtk.Grid(column_spacing=20, row_spacing=15)

        # Operational Mode Selector
        grid.attach(Gtk.Label(label="Operational Mode:"), 0, 0, 1, 1)
        self.mode_combo = Gtk.ComboBoxText()
        self.mode_combo.append_text("Full Cyclic (Tank 1 <-> Tank 2)")
        self.mode_combo.append_text("Non-Cyclic (Steady State)")
        self.mode_combo.set_active(0)
        grid.attach(self.mode_combo, 1, 0, 1, 1)

        # Target Throughput
        grid.attach(Gtk.Label(label="Target Throughput (L):"), 0, 1, 1, 1)
        self.target_entry = Gtk.Entry(text="1000")
        grid.attach(self.target_entry, 1, 1, 1, 1)

        box.pack_start(grid, False, False, 0)

        # Control Buttons
        btn_box = Gtk.Box(spacing=10)
        start_btn = Gtk.Button(label="START TEST")
        start_btn.connect("clicked", self.start_test)
        btn_box.pack_start(start_btn, True, True, 0)

        stop_btn = Gtk.Button(label="EMERGENCY STOP")
        stop_btn.connect("clicked", self.e_stop)
        btn_box.pack_start(stop_btn, True, True, 0)

        box.pack_start(btn_box, False, False, 0)
        self.notebook.append_page(box, Gtk.Label(label="Setup"))

    def init_monitor_tab(self):
        """Tab 2: Live Monitor & Actuator Flows"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15, margin=20)

        # Actuator Status Row
        actuator_box = Gtk.Box(spacing=20)
        self.pump_lbl = self.create_status_indicator("PUMP 1")
        self.valve_lbl = self.create_status_indicator("VALVE MBV1")
        actuator_box.pack_start(self.pump_lbl, True, True, 0)
        actuator_box.pack_start(self.valve_lbl, True, True, 0)
        box.pack_start(actuator_box, False, False, 0)

        # Sensor Displays
        sensor_grid = Gtk.Grid(column_spacing=40, row_spacing=20, halign=Gtk.Align.CENTER)
        self.flow_val = self.create_sensor_display(sensor_grid, "Flow Rate (LPM)", 0)
        self.vol_val = self.create_sensor_display(sensor_grid, "Total Volume (L)", 1)

        box.pack_start(sensor_grid, True, True, 0)
        self.notebook.append_page(box, Gtk.Label(label="Live Monitor"))

    def create_status_indicator(self, name):
        frame = Gtk.Frame(label=name)
        label = Gtk.Label(label="IDLE")
        label.set_padding(10, 10)
        frame.add(label)
        return label

    def create_sensor_display(self, grid, label_text, row):
        lbl = Gtk.Label(label=label_text)
        val = Gtk.Label(label="0.00")
        val.modify_font(Pango.FontDescription("Monospace Bold 30"))
        grid.attach(lbl, 0, row, 1, 1)
        grid.attach(val, 1, row, 1, 1)
        return val

    # --- UI Logic & Flow Controls ---
    def start_test(self, btn):
        self.emulator.is_running = True
        # UI Sequence: Open Valve first, then start Pump
        GLib.timeout_add(500, self.sequence_open_valve)
        GLib.timeout_add(1500, self.sequence_start_pump)
        self.notebook.set_current_page(1)

    def sequence_open_valve(self):
        self.emulator.valve_open = True
        return False  # Run once

    def sequence_start_pump(self):
        self.emulator.pump_active = True
        return False

    def e_stop(self, btn):
        self.emulator.is_running = False
        self.emulator.pump_active = False
        self.emulator.valve_open = False
        print("!! EMERGENCY STOP TRIGGERED !!")

    def on_poll_data(self):
        data = self.emulator.update_step()

        # Update Actuator Visuals
        self.pump_lbl.set_text(data["pump"])
        self.valve_lbl.set_text(data["valve"])

        # Color coding states
        p_color = "green" if data["pump"] == "RUNNING" else "black"
        v_color = "blue" if data["valve"] == "OPEN" else "black"
        self.pump_lbl.set_markup(f"<span foreground='{p_color}'><b>{data['pump']}</b></span>")
        self.valve_lbl.set_markup(f"<span foreground='{v_color}'><b>{data['valve']}</b></span>")

        # Update Sensor Data
        self.flow_val.set_text(str(data["flow"]))
        self.vol_val.set_text(str(data["vol"]))

        return True


if __name__ == "__main__":
    app = FuelRigApp()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()
