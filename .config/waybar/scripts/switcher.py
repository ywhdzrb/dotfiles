#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
import subprocess, json, os, time

CACHE = "/tmp/waybar-switcher"
os.makedirs(CACHE, exist_ok=True)

def log(m):
    with open("/tmp/switcher_run.log", "a") as f:
        f.write(f"{time.time():.3f} {m}\n")

class Switcher(Gtk.Window):
    def __init__(self, windows, active_ws=None):
        super().__init__(title="waybar-switcher")
        self._active_ws = active_ws
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_resizable(False)
        self.set_border_width(0)
        self.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        self.connect("key-press-event", self.on_key)
        self._windows = windows
        self._index = 0

        css = b"""
        * { font-family: "JetBrainsMono Nerd Font", "Noto Sans CJK SC", sans-serif; font-size: 10px; }
        window { background: rgba(46, 52, 64, 0.88); border: 1px solid rgba(76, 86, 106, 0.4); border-radius: 8px; }
        #card { background: rgba(59, 66, 82, 0.4); border-radius: 6px; padding: 4px; }
        #card:hover { background: rgba(136, 192, 208, 0.25); }
        #card.selected { background: rgba(136, 192, 208, 0.3); border: 1px solid #88c0d0; }
        #title { color: #d8dee9; padding: 4px 0 0; font-size: 9px; }
        #class { color: #616e88; font-size: 8px; }
        """
        screen = Gdk.Screen.get_default()
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        scroll.set_size_request(-1, 200)

        self.box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.box.set_margin_top(12)
        self.box.set_margin_bottom(12)
        self.box.set_margin_start(12)
        self.box.set_margin_end(12)
        scroll.add(self.box)
        self.add(scroll)

        icon_theme = Gtk.IconTheme.get_default()

        for i, (addr, cls, title, thumb_path, ws) in enumerate(windows):
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            card.set_name("card")
            card.set_size_request(140, 150)

            evb = Gtk.EventBox()
            evb.connect("button-press-event", lambda w, e, a=addr: self.pick(a))
            evb.set_visible_window(False)

            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            vbox.set_halign(Gtk.Align.CENTER)

            img = Gtk.Image()
            if thumb_path and os.path.exists(thumb_path):
                try:
                    pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(thumb_path, 130, 85, True)
                    img.set_from_pixbuf(pix)
                except Exception:
                    img.set_from_icon_name("window", Gtk.IconSize.DIALOG)
            else:
                icon_name = cls.lower()
                icon_info = icon_theme.lookup_icon(icon_name, 64, 0) if icon_theme else None
                if icon_info:
                    try:
                        pix = icon_info.load_icon()
                        img.set_from_pixbuf(pix)
                    except Exception:
                        img.set_from_icon_name("application-x-executable", Gtk.IconSize.DIALOG)
                else:
                    img.set_from_icon_name("application-x-executable", Gtk.IconSize.DIALOG)
            vbox.pack_start(img, False, False, 0)

            ws_label = Gtk.Label(label=f"WS {ws}" if ws != self._active_ws else "")
            ws_label.set_name("class")
            ws_label.set_xalign(0.5)
            vbox.pack_start(ws_label, False, False, 0)

            tl = Gtk.Label(label=title[:28])
            tl.set_name("title")
            tl.set_xalign(0.5)
            tl.set_ellipsize(3)
            vbox.pack_start(tl, False, False, 0)

            cl = Gtk.Label(label=cls[:20])
            cl.set_name("class")
            cl.set_xalign(0.5)
            cl.set_ellipsize(3)
            vbox.pack_start(cl, False, False, 0)

            evb.add(vbox)
            card.pack_start(evb, True, True, 0)
            self.box.pack_start(card, False, False, 0)

        self.set_default_size(min(len(windows) * 160 + 40, 1600), 210)
        self.show_all()
        self.present()
        GLib.timeout_add(200, self.reposition)
        GLib.timeout_add(400, self.reposition)

    def reposition(self):
        try:
            cs = json.loads(subprocess.run(["hyprctl", "clients", "-j"], capture_output=True, text=True, timeout=3).stdout)
            for c in cs:
                if c.get("title") == "waybar-switcher":
                    addr = c.get("address")
                    if addr:
                        mon = json.loads(subprocess.run(["hyprctl", "monitors", "-j"], capture_output=True, text=True, timeout=3).stdout)
                        m = mon[0] if mon else {}
                        mw = int(m.get("width", 1920) // m.get("scale", 1))
                        mh = int(m.get("height", 1080) // m.get("scale", 1))
                        w = min(len(self._windows) * 160 + 40, 1600)
                        h = 210
                        x = max(0, (mw - w) // 2)
                        y = max(0, (mh - h) // 2)
                        subprocess.run(["hyprctl", "dispatch", "movewindowpixel", f"exact {x} {y},address:{addr}"], capture_output=True, timeout=2)
                        return False
                    break
        except Exception as e:
            log(f"reposition: {e}")
        return False

    def pick(self, addr):
        subprocess.run(["hyprctl", "dispatch", "focuswindow", f"address:{addr}"], capture_output=True)
        Gtk.main_quit()

    def on_key(self, w, e):
        k = e.keyval
        if k in (Gdk.KEY_Escape, Gdk.KEY_q):
            Gtk.main_quit()
        elif k in (Gdk.KEY_Tab, Gdk.KEY_Right):
            cs = self.box.get_children()
            if cs:
                cs[self._index].set_name("card")
                self._index = (self._index + 1) % len(cs)
                cs[self._index].set_name("card selected")
        elif k == Gdk.KEY_Left:
            cs = self.box.get_children()
            if cs:
                cs[self._index].set_name("card")
                self._index = (self._index - 1) % len(cs)
                cs[self._index].set_name("card selected")
        elif k in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            if self._windows and self._index < len(self._windows):
                self.pick(self._windows[self._index][0])


def main():
    ts = str(int(time.time() * 1000))
    screen_path = f"{CACHE}/screen_{ts}.png"
    subprocess.run(["grim", screen_path], capture_output=True, timeout=5)

    try:
        clients = json.loads(subprocess.run(["hyprctl", "clients", "-j"], capture_output=True, text=True, timeout=3).stdout)
    except Exception as e:
        log(f"hyprctl: {e}")
        exit(0)

    if not clients:
        exit(0)

    active_ws = None
    for c in clients:
        if c.get("focusHistoryID") == 0:
            active_ws = c.get("workspace", {}).get("id")
            break
    if active_ws is None:
        active_ws = clients[0].get("workspace", {}).get("id")

    windows = []
    for c in clients:
        if c.get("hidden", False):
            continue
        addr = c.get("address", "")
        cls = c.get("class", "")
        title = c.get("title", "")
        if not addr or not title:
            continue
        ws = c.get("workspace", {}).get("id")
        at = c.get("at", [0, 0])
        size = c.get("size", [100, 100])
        x, y, w, h = at[0], at[1], size[0], size[1]

        thumb_path = None
        if ws == active_ws:
            thumb_path = f"{CACHE}/thumb_{addr[2:10]}_{ts}.png"
            subprocess.run(["convert", screen_path, "-crop", f"{w}x{h}+{x}+{y}", "-resize", "130x90>", thumb_path], capture_output=True, timeout=3)
        windows.append((addr, cls, title, thumb_path, ws))

    if not windows:
        exit(0)

    log(f"showing {len(windows)} windows (active_ws={active_ws})")
    Switcher(windows, active_ws)
    Gtk.main()

    for _, _, _, tp, _ in windows:
        if tp:
            try: os.remove(tp)
            except: pass
    try: os.remove(screen_path)
    except: pass

if __name__ == "__main__":
    main()
