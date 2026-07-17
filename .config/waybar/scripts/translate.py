#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango
import subprocess, textwrap, sys

S = 80
TEXT = " ".join(sys.argv[1:]) or subprocess.run(["wl-paste", "--primary"], capture_output=True, text=True).stdout.strip() or subprocess.run(["wl-paste"], capture_output=True, text=True).stdout.strip()
if not TEXT:
    exit(0)

RESULT = subprocess.run(["trans", "-b", "-s", "auto", "-t", "zh", TEXT], capture_output=True, text=True, timeout=10).stdout.strip()

w = Gtk.Window(title="translate")
w.set_decorated(False)
w.set_keep_above(True)
w.set_skip_taskbar_hint(True)
w.set_resizable(False)
w.set_border_width(0)
w.set_type_hint(Gdk.WindowTypeHint.UTILITY)
w.connect("key-press-event", lambda w, e: Gtk.main_quit() if e.keyval in (Gdk.KEY_Escape, Gdk.KEY_q) else None)
w.connect("focus-out-event", lambda *a: Gtk.main_quit())

css = b"""
* { font-family: "JetBrainsMono Nerd Font", sans-serif; font-size: 11px; }
window { background: rgba(46, 52, 64, 0.92); border: 1px solid rgba(76, 86, 106, 0.4); border-radius: 6px; }
#source { color: #88c0d0; font-weight: bold; padding: 0 0 4px; }
#result { color: #d8dee9; }
"""
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), Gtk.CssProvider(), Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), __import__("gi").repository.Gtk.CssProvider(), Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

provider = Gtk.CssProvider()
provider.load_from_data(css)
screen = Gdk.Screen.get_default()
Gtk.StyleContext.add_provider_for_screen(screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
box.set_margin_top(10)
box.set_margin_bottom(10)
box.set_margin_start(12)
box.set_margin_end(12)

src = Gtk.Label(label=TEXT[:200])
src.set_name("source")
src.set_xalign(0)
src.set_line_wrap(True)
box.pack_start(src, False, False, 0)

res = Gtk.Label(label=RESULT or "翻译失败")
res.set_name("result")
res.set_xalign(0)
res.set_line_wrap(True)
box.pack_start(res, False, False, 0)

w.add(box)
w.show_all()

mw = 500
sw = min(500, max(250, 1_000_000))
w.set_default_size(sw, 100)
w.present()

GLib.timeout_add(100, lambda: w.resize(sw, 100) or False)

Gtk.main()
