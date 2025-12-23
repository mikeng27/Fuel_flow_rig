import gi
import random
import math

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Pango, Gdk


class RigEmulator:
    def __init__(self):
        self.is_running = False
        self.pump_active = False
        self.valve_open = False
        self.tank1_level = 500.0
        self.tank2_level = 0.0
        self.flow_rate = 12.0  # Increased for faster visual feedback

    def update_step(self):
        if self.is_running and self.pump_active and self.valve_open:
            transfer_amount = (self.flow_rate / 600)
            if self.tank1_level > 0:
                self.tank1_level -= transfer_amount
                self.tank2_level += transfer_amount

        return {
            "pump": "RUNNING" if self.pump_active else "IDLE",
            "valve": "OPEN" if self.valve_open else "CLOSED",
            "t1": max(0, self.tank1_level),
            "t2": min(500, self.tank2_level)
        }


class TankMonitorApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Automated KP Rig - Dynamic HMI")
        self.set_default_size(1000, 600)
        self.emulator = RigEmulator()
        self.rotation_angle = 0

        # Main Layout
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20, margin=25)
        self.add(main_vbox)

        # 1. Header
        header = Gtk.Label()
        header.set_markup("<span size='xx-large' weight='bold'>Fuel Flow Control Panel</span>")
        main_vbox.pack_start(header, False, False, 0)

        # 2. Visualization Area
        vis_hbox = Gtk.Box(spacing=50, halign=Gtk.Align.CENTER)

        # Tank 1 (Width increased to 150) [cite: 77]
        self.t1_bar = Gtk.ProgressBar(orientation=Gtk.Orientation.VERTICAL, inverted=True)
        self.t1_bar.set_size_request(150, 300)
        self.t1_label = Gtk.Label(label="500.0 L")

        # Center Logic Area
        center_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15, valign=Gtk.Align.CENTER)

        # Valve Representation
        self.valve_lbl = Gtk.Label(label="VALVE CLOSED")
        self.valve_img = Gtk.Image.new_from_icon_name("changes-prevent-symbolic", Gtk.IconSize.DND)

        # Pump (Motor) Representation [cite: 79]
        self.pump_frame = Gtk.Frame(label="Dispensing Pump")
        self.pump_img = Gtk.Image.new_from_icon_name("process-working-symbolic", Gtk.IconSize.DND)
        self.pump_frame.add(self.pump_img)

        center_vbox.pack_start(self.valve_lbl, False, False, 0)
        center_vbox.pack_start(self.valve_img, False, False, 0)
        center_vbox.pack_start(self.pump_frame, False, False, 0)

        # Tank 2 (Width increased to 150)
        self.t2_bar = Gtk.ProgressBar(orientation=Gtk.Orientation.VERTICAL, inverted=True)
        self.t2_bar.set_size_request(150, 300)
        self.t2_label = Gtk.Label(label="0.0 L")

        # Layout Assembly
        vis_hbox.pack_start(self.create_tank_group("SOURCE TANK 1", self.t1_bar, self.t1_label), False, False, 0)
        vis_hbox.pack_start(center_vbox, True, True, 0)
        vis_hbox.pack_start(self.create_tank_group("SINK TANK 2", self.t2_bar, self.t2_label), False, False, 0)

        main_vbox.pack_start(vis_hbox, True, True, 0)

        # 3. Controls [cite: 110, 112]
        btn_box = Gtk.Box(spacing=20, halign=Gtk.Align.CENTER)
        self.start_btn = Gtk.Button(label="ENGAGE SYSTEM")
        self.start_btn.connect("clicked", self.on_start)
        self.stop_btn = Gtk.Button(label="EMERGENCY SHUTDOWN")
        self.stop_btn.connect("clicked", self.on_stop)

        btn_box.pack_start(self.start_btn, False, False, 0)
        btn_box.pack_start(self.stop_btn, False, False, 0)
        main_vbox.pack_start(btn_box, False, False, 0)

        GLib.timeout_add(50, self.update_ui)  # Faster refresh for rotation smoothness

    def create_tank_group(self, name, bar, lbl):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.pack_start(Gtk.Label(label=f"<b>{name}</b>", use_markup=True), False, False, 0)
        vbox.pack_start(bar, True, True, 0)
        vbox.pack_start(lbl, False, False, 0)
        return vbox

    def on_start(self, btn):
        self.emulator.is_running = True
        self.emulator.valve_open = True
        self.emulator.pump_active = True

    def on_stop(self, btn):
        self.emulator.is_running = False
        self.emulator.pump_active = False
        self.emulator.valve_open = False

    def update_ui(self):
        data = self.emulator.update_step()

        # 1. Update Tank Progress and Text Labels [cite: 78]
        self.t1_bar.set_fraction(data['t1'] / 500.0)
        self.t2_bar.set_fraction(data['t2'] / 500.0)
        self.t1_label.set_text(f"{data['t1']:.1f} L")
        self.t2_label.set_text(f"{data['t2']:.1f} L")

        # 2. Update Valve Visuals
        if data['valve'] == "OPEN":
            self.valve_lbl.set_markup("<span foreground='green'>VALVE OPEN</span>")
            self.valve_img.set_from_icon_name("emblem-ok-symbolic", Gtk.IconSize.DND)
        else:
            self.valve_lbl.set_markup("<span foreground='red'>VALVE CLOSED</span>")
            self.valve_img.set_from_icon_name("changes-prevent-symbolic", Gtk.IconSize.DND)

        # 3. Handle Pump Motor "Rotation"
        if data['pump'] == "RUNNING":
            # Change icon sequentially to simulate motion
            icons = ["process-working-symbolic", "media-playlist-repeat-symbolic"]
            idx = int(GLib.get_monotonic_time() / 200000) % 2
            self.pump_img.set_from_icon_name(icons[idx], Gtk.IconSize.DND)
            self.pump_frame.set_label("MOTOR ROTATING...")
        else:
            self.pump_img.set_from_icon_name("process-stop-symbolic", Gtk.IconSize.DND)
            self.pump_frame.set_label("MOTOR IDLE")

        return True


if __name__ == "__main__":
    app = TankMonitorApp()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()