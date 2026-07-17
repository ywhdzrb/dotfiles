#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
import subprocess, os, json, urllib.request, hashlib, re

CACHE = "/tmp/waybar-music-popup"
os.makedirs(CACHE, exist_ok=True)

class MusicPopup(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="waybar-music-popup")
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_resizable(False)
        self.set_border_width(0)
        self.connect("focus-out-event", lambda w, e: Gtk.main_quit())
        self.connect("key-press-event", self.on_key)

        css = b"""
        * { font-family: "JetBrainsMono Nerd Font", "Noto Sans CJK SC", sans-serif; font-size: 9px; }
        window { background: rgba(46, 52, 64, 0.85); border: 1px solid rgba(76, 86, 106, 0.4); border-radius: 6px; }
        #title { font-weight: bold; color: #88c0d0; }
        #artist { color: #d8dee9; }
        #time { color: #616e88; }
        button { background: rgba(59, 66, 82, 0.5); color: #d8dee9; border: none; border-radius: 4px;
                 min-width: 40px; min-height: 32px; font-size: 9px; padding: 0; }
        button:hover { background: #88c0d0; color: #2e3440; }
        button:active { background: #81a1c1; }
        #playbtn { background: rgba(136, 192, 208, 0.2); color: #88c0d0; }
        #playbtn:hover { background: #88c0d0; color: #2e3440; }
        scale { min-height: 12px; }
        scale trough { background: #3b4252; border: none; border-radius: 3px; min-height: 4px; margin: 4px 0; }
        scale trough highlight { background: #88c0d0; border: none; border-radius: 3px; }
        scale slider { background: #88c0d0; border: none; border-radius: 5px; min-width: 10px; min-height: 10px;
                       margin: -3px 0; }
        """
        screen = Gdk.Screen.get_default()
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.set_default_size(320, 130)

        mx = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        mx.set_margin_top(12)
        mx.set_margin_bottom(12)
        mx.set_margin_start(12)
        mx.set_margin_end(12)
        self.add(mx)

        self.art = Gtk.Image()
        self.art.set_size_request(80, 80)
        mx.pack_start(self.art, False, False, 0)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        mx.pack_start(right, True, True, 0)

        self.title_lbl = Gtk.Label()
        self.title_lbl.set_name("title")
        self.title_lbl.set_xalign(0)
        self.title_lbl.set_ellipsize(3)
        right.pack_start(self.title_lbl, False, False, 0)

        self.artist_lbl = Gtk.Label()
        self.artist_lbl.set_name("artist")
        self.artist_lbl.set_xalign(0)
        self.artist_lbl.set_ellipsize(3)
        right.pack_start(self.artist_lbl, False, False, 0)

        prog_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self._seeking = False

        self.time_lbl = Gtk.Label(label="0:00")
        self.time_lbl.set_name("time")
        self.time_lbl.set_xalign(0)
        prog_box.pack_start(self.time_lbl, False, False, 0)

        self.progress = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.0, 1.0, 0.01)
        self.progress.set_hexpand(True)
        self.progress.set_size_request(-1, 6)
        self.progress.set_draw_value(False)
        self.progress.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.progress.connect("button-press-event", lambda w, e: setattr(self, '_seeking', True) or False)
        self.progress.connect("button-release-event", self.on_seek)
        prog_box.pack_start(self.progress, True, True, 0)

        self.total_lbl = Gtk.Label(label="0:00")
        self.total_lbl.set_name("time")
        self.total_lbl.set_xalign(1)
        prog_box.pack_start(self.total_lbl, False, False, 0)
        right.pack_start(prog_box, False, False, 0)

        btn_box = Gtk.Box(homogeneous=True, spacing=8)
        btn_box.set_halign(Gtk.Align.CENTER)

        prev_btn = Gtk.Button(label="⏮")
        prev_btn.connect("clicked", lambda b: self.run("playerctl previous"))
        btn_box.pack_start(prev_btn, False, False, 0)

        self.play_btn = Gtk.Button(label="⏸")
        self.play_btn.set_name("playbtn")
        self.play_btn.connect("clicked", lambda b: self.toggle_play())
        btn_box.pack_start(self.play_btn, False, False, 0)

        next_btn = Gtk.Button(label="⏭")
        next_btn.connect("clicked", lambda b: self.run("playerctl next"))
        btn_box.pack_start(next_btn, False, False, 0)

        right.pack_start(btn_box, False, False, 0)

        self.update_info()
        GLib.timeout_add_seconds(1, self.update_info)

    def player(self):
        def pick(match, state):
            for p in subprocess.run(["playerctl", "-l"], capture_output=True, text=True).stdout.splitlines():
                if __import__("re").search(match, p, __import__("re").I) and \
                   subprocess.run(["playerctl", "-p", p, "status"], capture_output=True, text=True).stdout.strip() == state:
                    return p
            return None
        p = pick(r"splayer|spotify|mpd|vlc|strawberry", "Playing") or \
            pick(r"firefox|chrome|brave", "Playing") or \
            pick(r"..*", "Paused") or ""
        return ["playerctl", "-p", p] if p else ["playerctl"]

    def run(self, cmd):
        subprocess.run(self.player() + cmd.split()[1:], capture_output=True)
        self.update_info()

    def toggle_play(self):
        subprocess.run(self.player() + ["play-pause"], capture_output=True)
        self.update_info()

    def on_seek(self, w, e):
        p = self.player()
        frac = self.progress.get_value()
        total = subprocess.run(p + ["metadata", "mpris:length"], capture_output=True, text=True).stdout.strip()
        if total:
            sec = int(frac * int(total) / 1000000)
            subprocess.run(p + ["position", str(sec)], capture_output=True)
        self._seeking = False
        self.update_info()

    def on_key(self, w, e):
        if e.keyval in (Gdk.KEY_Escape, Gdk.KEY_q):
            Gtk.main_quit()
        elif e.keyval == Gdk.KEY_space:
            self.toggle_play()

    def get_art(self, url):
        if not url:
            return None
        h = hashlib.md5(url.encode()).hexdigest()[:8]
        ext = url.split(".")[-1][:4]
        path = os.path.join(CACHE, f"art_{h}.{ext}")
        if not os.path.exists(path):
            try:
                urllib.request.urlretrieve(url, path)
            except:
                return None
        try:
            return GdkPixbuf.Pixbuf.new_from_file_at_scale(path, 80, 80, True)
        except:
            return None

    def update_info(self):
        try:
            p = self.player()
            status = subprocess.run(p + ["status"], capture_output=True, text=True).stdout.strip()
            if not status or status == "Stopped":
                Gtk.main_quit()
                return False

            title = subprocess.run(p + ["metadata", "title"], capture_output=True, text=True).stdout.strip()
            artist = subprocess.run(p + ["metadata", "artist"], capture_output=True, text=True).stdout.strip()
            art_url = subprocess.run(p + ["metadata", "mpris:artUrl"], capture_output=True, text=True).stdout.strip()
            pos_str = subprocess.run(p + ["position"], capture_output=True, text=True).stdout.strip()
            length_str = subprocess.run(p + ["metadata", "mpris:length"], capture_output=True, text=True).stdout.strip()

            self.title_lbl.set_text(title or "Unknown")
            self.artist_lbl.set_text(artist or "")

            pix = self.get_art(art_url)
            if pix:
                self.art.set_from_pixbuf(pix)
            else:
                self.art.set_from_icon_name("audio-x-generic", Gtk.IconSize.DIALOG)

            pos = int(float(pos_str)) if pos_str else 0
            length_us = int(length_str) if length_str else 0
            total = length_us // 1000000 if length_us else 0

            self.time_lbl.set_text(f"{pos//60}:{pos%60:02d}")
            if total > 0:
                self.total_lbl.set_text(f"{total//60}:{total%60:02d}")
                if not self._seeking:
                    self.progress.set_value(min(pos / total, 1.0))
            else:
                self.total_lbl.set_text("--:--")
                if not self._seeking:
                    self.progress.set_value(0)

            play_label = "⏸" if status == "Playing" else "▶"
            self.play_btn.set_label(play_label)

        except Exception:
            Gtk.main_quit()
            return False

        return True

import subprocess as _sp
_cx, _cy = _sp.run(["hyprctl", "cursorpos"], capture_output=True, text=True).stdout.strip().split(", ")
_cx, _cy = int(_cx), int(_cy)

def reposition(retries=5):
    try:
        clients = __import__("json").loads(_sp.run(["hyprctl", "clients", "-j"], capture_output=True, text=True).stdout)
        for c in clients:
            if c.get("title") == "waybar-music-popup":
                addr = c.get("address")
                if addr:
                    _sp.run(["hyprctl", "dispatch", "movewindowpixel", f"exact {max(0, _cx - 160)} {_cy + 20},address:{addr}"])
                return False
    except:
        pass
    if retries > 0:
        GLib.timeout_add(50, lambda: reposition(retries - 1))
    return False

if __name__ == "__main__":
    if not _sp.run(["playerctl", "status"], capture_output=True, text=True).stdout.strip():
        exit(0)
    w = MusicPopup()
    w.show_all()
    GLib.timeout_add(50, reposition)
    Gtk.main()
