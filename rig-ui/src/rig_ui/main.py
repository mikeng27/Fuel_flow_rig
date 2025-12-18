import gi
gi.require_version("Gtk", "3.0") # Or "4.0"
from gi.repository import Gtk

class KPFuelFlowApp:
    def __init__(self):
        # Initialize the window
        self.window = Gtk.Window(title="KP Fuel Flow Test Rig")
        self.window.set_default_size(800, 480) # RPi touchscreen resolution
        self.window.connect("destroy", Gtk.main_quit)

        # Layout Container
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.window.add(self.box)

        # Simple UI Elements
        self.label = Gtk.Label(label="Automated KP Fuel Flow Testing")
        self.box.pack_start(self.label, True, True, 0)

        self.button = Gtk.Button(label="Start Test Sequence")
        self.button.connect("clicked", self.on_start_clicked)
        self.box.pack_start(self.button, True, True, 0)

        self.window.show_all()

    def on_start_clicked(self, widget):
        self.label.set_text("Test Sequence Initiated...")

if __name__ == "__main__":
    app = KPFuelFlowApp()
    Gtk.main()