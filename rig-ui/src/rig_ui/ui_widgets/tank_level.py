import gi
gi.require_version("Gtk", "4.0")

from gi.repository import Gtk, Gdk

TANK_CAPACITY_L = 500  # 500 L

class TankLevelApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.example.tanklevel")
        self.window = None
        self.current_volume = 0.0  # Start empty

    def do_activate(self):
        if self.window:
            self.window.present()
            return

        self.window = Gtk.ApplicationWindow(application=self)
        self.window.set_title("Tank Level Monitor – 500L")
        self.window.set_default_size(900, 600)

        root = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=40,
            margin_top=30,
            margin_bottom=30,
            margin_start=30,
            margin_end=30,
        )

        # ---- Tank LevelBar ----
        self.level = Gtk.LevelBar()
        self.level.set_orientation(Gtk.Orientation.VERTICAL)
        self.level.set_min_value(0)
        self.level.set_max_value(TANK_CAPACITY_L)
        self.level.set_value(self.current_volume)
        self.level.set_inverted(True)  # Fill from bottom
        self.level.set_size_request(200, 450)

        # Thresholds
        self.level.add_offset_value("low", 0)       # 0–150L
        self.level.add_offset_value("normal", 150)  # 150–375L
        self.level.add_offset_value("full", 375)    # 375–500L

        # CSS for blue fill
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            levelbar trough {
                background-color: #cccccc;
                border-radius: 10px;
            }
            levelbar progress {
                background-color: #1E90FF;
                border-radius: 10px;
            }
        """)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # ---- Info Panel ----
        info = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=20
        )

        title = Gtk.Label()
        title.set_markup("<span size='xx-large'><b>Fuel Tank</b></span>")

        self.volume_label = Gtk.Label()
        self.status_label = Gtk.Label()
        self.update_labels()

        # ---- Entry field for manual volume input ----
        self.volume_entry = Gtk.Entry()
        self.volume_entry.set_placeholder_text("Enter volume in liters (0–500)")
        self.volume_entry.set_max_length(6)  # e.g., 500.0
        self.volume_entry.set_width_chars(10)
        self.volume_entry.connect("activate", self.on_volume_entered)  # Trigger on Enter key

        info.append(title)
        info.append(self.volume_label)
        info.append(self.status_label)
        info.append(self.volume_entry)

        root.append(self.level)
        root.append(info)

        self.window.set_child(root)
        self.window.present()

    def update_labels(self):
        self.volume_label.set_markup(
            f"<span size='x-large'>Volume: <b>{self.current_volume:.1f} L</b></span>"
        )

        if self.current_volume < 150:
            status = "LOW"
        elif self.current_volume < 375:
            status = "NORMAL"
        else:
            status = "FULL"

        self.status_label.set_markup(
            f"<span size='x-large'>Status: <b>{status}</b></span>"
        )

    def on_volume_entered(self, entry):
        """Called when user presses Enter in the text field"""
        try:
            value = float(entry.get_text())
            value = max(0.0, min(TANK_CAPACITY_L, value))  # Clamp between 0 and 500
            self.current_volume = value
            self.level.set_value(self.current_volume)
            self.update_labels()
        except ValueError:
            # Invalid input, ignore
            pass


def main():
    app = TankLevelApp()
    app.run()


if __name__ == "__main__":
    main()
