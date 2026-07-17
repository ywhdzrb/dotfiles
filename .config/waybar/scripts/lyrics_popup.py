#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import subprocess, os, hashlib

CACHE_DIR = "/tmp/waybar-lyrics"

class LyricsPopup(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="waybar-lyrics-popup")
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_type_hint(Gdk.WindowTypeHint.NOTIFICATION)
        self.set_resizable(False)
        self.set_border_width(0)
        self.connect("button-press-event", lambda w, e: Gtk.main_quit())
        self.connect("key-press-event", self.on_key)
        self.connect("focus-out-event", lambda w, e: Gtk.main_quit())

        css = b"""
        * { font-family: "JetBrainsMono Nerd Font", "Noto Sans CJK SC", sans-serif; font-size: 9px; }
        window { background: rgba(46,52,64,0.85); }
        #lyric { color: #88c0d0; font-weight: bold; padding: 8px 16px; }
        #fallback { color: #d8dee9; padding: 8px 16px; }
        """
        screen = Gdk.Screen.get_default()
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        width = min(900, Gdk.Display.get_default().get_primary_monitor().get_geometry().width - 40)
        self.set_default_size(width, 32)

        self.lbl = Gtk.Label()
        self.lbl.set_name("lyric")
        self.lbl.set_xalign(0.5)
        self.lbl.set_halign(Gtk.Align.CENTER)
        self.add(self.lbl)
        self.show_all()

        self.update()
        GLib.timeout_add_seconds(1, self.update)

    def on_key(self, w, e):
        if e.keyval in (Gdk.KEY_Escape, Gdk.KEY_q):
            Gtk.main_quit()

    def get_lyric_line(self):
        status = subprocess.run(["playerctl", "status"], capture_output=True, text=True).stdout.strip()
        if not status or status == "Stopped":
            return None

        title = subprocess.run(["playerctl", "metadata", "title"], capture_output=True, text=True).stdout.strip()
        artist = subprocess.run(["playerctl", "metadata", "artist"], capture_output=True, text=True).stdout.strip()
        if not title:
            return None

        cache_key = hashlib.md5(f"{artist} - {title}".encode()).hexdigest()
        cache_file = f"{CACHE_DIR}/{cache_key}"
        meta_file = f"{CACHE_DIR}/{cache_key}_meta"

        fallback = f"♫ {artist} - {title}" if artist else f"♫ {title}"

        if not os.path.exists(cache_file) or not os.path.exists(meta_file):
            return fallback

        with open(meta_file) as f:
            meta = f.read().strip()

        if meta == "lrc":
            pos_str = subprocess.run(["playerctl", "position"], capture_output=True, text=True).stdout.strip()
            if not pos_str:
                return fallback
            pos_sec = int(float(pos_str))

            last = ""
            with open(cache_file) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("["):
                        try:
                            ts = line[1:].split("]")[0]
                            m, s = ts.split(":")
                            secs = int(m) * 60 + float(s)
                            rest = line.split("]", 1)[1].strip()
                            if secs <= pos_sec + 1 and rest:
                                last = rest
                        except:
                            pass
            if last:
                return f"♫ {last}"
            return fallback

        elif meta == "plain":
            total_str = subprocess.run(["playerctl", "metadata", "mpris:length"], capture_output=True, text=True).stdout.strip()
            pos_str = subprocess.run(["playerctl", "position"], capture_output=True, text=True).stdout.strip()
            if not total_str or not pos_str:
                with open(cache_file) as f:
                    first = f.readline().strip()
                return f"♫ {first}" if first else fallback

            total_sec = int(total_str) // 1000000
            pos_sec = int(float(pos_str))
            if total_sec == 0:
                return fallback

            with open(cache_file) as f:
                lines = [l.strip() for l in f if l.strip()]
            if not lines:
                return fallback

            idx = min(int(pos_sec / total_sec * len(lines)), len(lines) - 1)
            return f"♫ {lines[idx]}"

        else:
            return fallback

    def update(self):
        try:
            text = self.get_lyric_line()
            if text is None:
                Gtk.main_quit()
                return False
            self.lbl.set_text(text)
        except:
            Gtk.main_quit()
            return False
        return True

def reposition():
    import subprocess as sp
    try:
        out = sp.run(["hyprctl", "clients", "-j"], capture_output=True, text=True).stdout
        for c in __import__("json").loads(out):
            if c.get("title") == "waybar-lyrics-popup":
                addr = c.get("address")
                if addr:
                    display = Gdk.Display.get_default()
                    mon = display.get_primary_monitor() or display.get_monitor(0)
                    geo = mon.get_geometry()
                    x = (geo.width - 900) // 2
                    sp.run(["hyprctl", "dispatch", "movewindowpixel", f"exact {x} 28", f"address:{addr}"])
                break
    except:
        pass
    return False

if __name__ == "__main__":
    w = LyricsPopup()
    w.show_all()
    GLib.timeout_add(100, reposition)
    Gtk.main()
