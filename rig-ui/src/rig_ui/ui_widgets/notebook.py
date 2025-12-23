import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class KPFuelFlowUI(Gtk.Window):
    def __init__(self):
        super().__init__(title="Automated KP Fuel Flow Rig")
        self.set_default_size(1000, 600)

        # Main container
        self.notebook = Gtk.Notebook()
        self.add(self.notebook)

        # --- TAB 1: TEST CONFIGURATION ---
        config_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=20)
        config_box.add(Gtk.Label(label="<b>Test Configuration</b>", use_markup=True))

        # Grid for form inputs
        grid = Gtk.Grid(column_spacing=15, row_spacing=10)
        grid.attach(Gtk.Label(label="Operational Mode:"), 0, 0, 1, 1)
        mode_combo = Gtk.ComboBoxText()
        mode_combo.append_text("Full Cyclic (Tank-to-Tank)")
        mode_combo.append_text("Non-Cyclic (Single Tank Level X)")
        grid.attach(mode_combo, 1, 0, 1, 1)

        grid.attach(Gtk.Label(label="Target Throughput (L):"), 0, 1, 1, 1)
        grid.attach(Gtk.Entry(), 1, 1, 1, 1)

        config_box.add(grid)

        start_btn = Gtk.Button(label="START TEST SEQUENCE")
        start_btn.get_style_context().add_class("suggested-action")
        config_box.pack_end(start_btn, False, False, 0)

        self.notebook.append_page(config_box, Gtk.Label(label="Setup"))

        # --- TAB 2: LIVE MONITORING ---
        monitor_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=20)
        monitor_box.add(Gtk.Label(label="<b>Live Performance Metrics</b>", use_markup=True))

        # Area for Gauges/Graphs [cite: 155]
        stats_area = Gtk.FlowBox()
        stats_area.add(self.create_metric_card("Flow Rate", "0.0 LPM"))
        stats_area.add(self.create_metric_card("Pump Pressure", "0.0 PSI"))
        stats_area.add(self.create_metric_card("Accuracy Drift", "0.00%"))

        monitor_box.add(stats_area)
        self.notebook.append_page(monitor_box, Gtk.Label(label="Monitor"))

    def create_metric_card(self, title, value):
        frame = Gtk.Frame(label=title)
        lbl = Gtk.Label(label=f"<span size='xx-large'>{value}</span>", use_markup=True, margin=10)
        frame.add(lbl)
        return frame


win = KPFuelFlowUI()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()