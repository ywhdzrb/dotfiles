#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import subprocess, os, threading

SIG_ICONS = {0: "󰤯", 1: "󰤟", 2: "󰤢", 3: "󰤥", 4: "󰤨"}

class NetworkPopup(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="waybar-network-popup")
        self.set_name("waybar-network-popup")
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_resizable(False)
        self.set_border_width(0)
        self.set_default_size(420, 480)
        self._dialog_open = False
        self.connect("focus-out-event", lambda w, e: Gtk.main_quit() if not self._dialog_open else None)
        self.connect("key-press-event", lambda w, e: Gtk.main_quit() if e.keyval in (Gdk.KEY_Escape, Gdk.KEY_q) else None)

        css = b"""
        * { font-family: "JetBrainsMono Nerd Font", "Noto Sans CJK SC", sans-serif; font-size: 9px; color: #d8dee9; }
        window { background: rgba(46, 52, 64, 0.92); border: 1px solid rgba(76, 86, 106, 0.4); border-radius: 6px; }
        row, listboxrow, .list-row, .list-row * { background: transparent; }
        #header { font-weight: bold; color: #88c0d0; padding: 8px 0 4px; }
        #card { background: rgba(59, 66, 82, 0.4); border: 1px solid rgba(76, 86, 106, 0.3); border-radius: 6px; margin: 4px 12px; padding: 10px; }
        #card-title { color: #81a1c1; font-weight: bold; padding-bottom: 4px; }
        #card-icon { min-width: 18px; }
        #card-val {}
        #card-sec { color: #616e88; }
        #signal-bar { color: #88c0d0; letter-spacing: 1px; }
        #sep { color: rgba(76, 86, 106, 0.4); padding: 2px 0; }
        #row { padding: 5px 12px; background: transparent; }
        #row:hover { background: rgba(136, 192, 208, 0.15); }
        #sig { color: #88c0d0; }
        #ssid { color: #d8dee9; }
        #lock { color: #d08770; }
        #badge { color: #a3be8c; }
        .action-btn { border: none; border-radius: 4px; padding: 6px 10px; font-size: 9px; min-height: 28px; }
        .action-btn:hover { color: #2e3440; }
        #rescan-btn { background: rgba(136, 192, 208, 0.15); color: #88c0d0; }
        #rescan-btn:hover { background: #88c0d0; }
        #disc-btn { background: rgba(191, 97, 106, 0.15); color: #bf616a; }
        #disc-btn:hover { background: #bf616a; }
        #set-btn { background: rgba(163, 190, 140, 0.15); color: #a3be8c; }
        #set-btn:hover { background: #a3be8c; }
        """
        screen = Gdk.Screen.get_default()
        self.css_provider = Gtk.CssProvider()
        self.css_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(screen, self.css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.get_style_context().add_provider(self.css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(self.main_box)

        self.card_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.main_box.pack_start(self.card_box, False, False, 0)

        rgba = Gdk.RGBA(0, 0, 0, 0)
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_max_content_height(360)
        self.scroll.override_background_color(Gtk.StateType.NORMAL, rgba)
        self.main_box.pack_start(self.scroll, True, True, 0)

        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.list_box.connect("row-activated", self.on_activate)
        self.list_box.override_background_color(Gtk.StateType.NORMAL, rgba)
        self.scroll.add(self.list_box)

        self.action_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.action_bar.set_margin_top(4)
        self.action_bar.set_margin_bottom(8)
        self.action_bar.set_margin_start(12)
        self.action_bar.set_margin_end(12)
        self.action_bar.set_homogeneous(True)
        self.main_box.pack_start(self.action_bar, False, False, 0)

        loading = Gtk.Label(label="扫描中…")
        loading.set_margin_top(12)
        loading.set_margin_bottom(12)
        self.list_box.add(loading)
        self.list_box.show_all()

        GLib.timeout_add(100, self.load_networks)

    def sig_bars(self, level):
        level = int(level) if level else 0
        idx = min(level // 20 + 1, 4) if level > 0 else 0
        return SIG_ICONS.get(idx, "󰤯")

    def sig_visual(self, level):
        level = int(level) if level else 0
        n = min(level // 20, 5) if level > 0 else 0
        return "█" * n + "░" * (5 - n)

    def load_networks(self):
        for c in self.list_box.get_children():
            self.list_box.remove(c)
        for c in self.action_bar.get_children():
            self.action_bar.remove(c)
        loading = Gtk.Label(label="扫描中…")
        loading.set_margin_top(12)
        loading.set_margin_bottom(12)
        self.list_box.add(loading)
        self.list_box.show_all()
        threading.Thread(target=self._scan_thread, daemon=True).start()

    def _get_details(self):
        d = {"ssid": "", "ip": "", "gw": "", "signal": 0, "freq": "", "rate": "", "chan": "", "iface": "", "type": "", "bssid": ""}
        try:
            w = subprocess.run(["nmcli", "-t", "-f", "active,bssid,ssid,signal,chan,freq,rate", "dev", "wifi", "list"],
                               capture_output=True, text=True, timeout=5).stdout
            for line in w.splitlines():
                if line.startswith("yes:"):
                    p = line.split(":")
                    if len(p) >= 3:
                        d["bssid"] = p[1]
                        d["ssid"] = p[2]
                        d["signal"] = int(p[3]) if len(p) > 3 and p[3].isdigit() else 0
                        d["chan"] = p[4] if len(p) > 4 else ""
                        d["freq"] = p[5] if len(p) > 5 else ""
                        d["rate"] = p[6] if len(p) > 6 else ""
                    break
        except:
            pass
        try:
            s = subprocess.run(["nmcli", "-t", "device", "status"], capture_output=True, text=True, timeout=5).stdout
            for line in s.splitlines():
                if "connected" in line:
                    p = line.split(":")
                    if p[0] in ("wifi", "ethernet"):
                        d["type"] = p[0]
                        d["iface"] = p[1]
                        if d["ssid"] or p[0] == "ethernet":
                            ip = subprocess.run(["nmcli", "-t", "device", "show", p[1]], capture_output=True, text=True, timeout=5).stdout
                            for l in ip.splitlines():
                                if l.startswith("IP4.ADDRESS"):
                                    d["ip"] = l.split(":")[1].split("/")[0]
                                elif l.startswith("IP4.GATEWAY"):
                                    d["gw"] = l.split(":")[1]
                        break
        except:
            pass
        return d

    def _scan_thread(self):
        details = self._get_details()
        current = details["ssid"]
        try:
            out = subprocess.run(["nmcli", "-t", "-f", "ssid,signal,security", "dev", "wifi", "list"],
                                 capture_output=True, text=True, timeout=5).stdout
        except:
            out = ""
        GLib.idle_add(self._build_ui, out, current, details)
        try:
            subprocess.run(["nmcli", "dev", "wifi", "rescan"], capture_output=True, timeout=15)
            out = subprocess.run(["nmcli", "-t", "-f", "ssid,signal,security", "dev", "wifi", "list"],
                                 capture_output=True, text=True, timeout=5).stdout
        except:
            out = ""
        nd = self._get_details()
        GLib.idle_add(self._build_ui, out, nd["ssid"] or current, nd)

    def _add_card_row(self, card, icon, val, val2=""):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        icon_lbl = Gtk.Label(label=icon)
        icon_lbl.set_name("card-icon")
        row.pack_start(icon_lbl, False, False, 0)
        val_lbl = Gtk.Label(label=val)
        val_lbl.set_name("card-val")
        val_lbl.set_xalign(0)
        val_lbl.set_halign(Gtk.Align.START)
        val_lbl.set_hexpand(True)
        row.pack_start(val_lbl, True, True, 0)
        if val2:
            sec_lbl = Gtk.Label(label=val2)
            sec_lbl.set_name("card-sec")
            row.pack_start(sec_lbl, False, False, 0)
        card.pack_start(row, False, False, 0)

    def _build_card(self, d):
        for c in self.card_box.get_children():
            self.card_box.remove(c)
        if not d.get("ssid") and d.get("type") != "ethernet":
            return
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        card.set_name("card")
        self.card_box.pack_start(card, False, False, 0)

        if d.get("ssid"):
            ttl = Gtk.Label(label="󰖩 当前连接")
            ttl.set_name("card-title")
            ttl.set_xalign(0)
            card.pack_start(ttl, False, False, 0)

            self._add_card_row(card, "󰤨", d["ssid"])
            if d.get("ip"):
                self._add_card_row(card, "", d["ip"])
            sig_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            sig_icon = Gtk.Label(label="")
            sig_icon.set_name("card-icon")
            sig_row.pack_start(sig_icon, False, False, 0)
            bar_lbl = Gtk.Label(label=self.sig_visual(d["signal"]))
            bar_lbl.set_name("signal-bar")
            sig_row.pack_start(bar_lbl, False, False, 0)
            pct_lbl = Gtk.Label(label=f"{d['signal']}%")
            pct_lbl.set_name("card-val")
            pct_lbl.set_xalign(0)
            pct_lbl.set_halign(Gtk.Align.START)
            sig_row.pack_start(pct_lbl, True, True, 0)
            freq_str = d.get("freq","").replace(" ","")
            if d.get("chan"):
                freq_str += f" ch.{d['chan']}"
            if d.get("rate"):
                freq_str += f" · {d['rate']} Mbps" if freq_str else f"{d['rate']} Mbps"
            if freq_str:
                sec_lbl = Gtk.Label(label=freq_str)
                sec_lbl.set_name("card-sec")
                sig_row.pack_start(sec_lbl, False, False, 0)
            card.pack_start(sig_row, False, False, 0)
            if d.get("iface"):
                self._add_card_row(card, "󰅟", d["iface"])
        elif d.get("type") == "ethernet":
            ttl = Gtk.Label(label=" 有线连接")
            ttl.set_name("card-title")
            ttl.set_xalign(0)
            card.pack_start(ttl, False, False, 0)
            if d.get("iface"):
                self._add_card_row(card, "󰅟", d["iface"])
            if d.get("ip"):
                self._add_card_row(card, "", d["ip"])
            if d.get("gw"):
                self._add_card_row(card, "", f"网关 {d['gw']}")
        card.show_all()

    def _build_ui(self, out, current, d):
        for c in self.list_box.get_children():
            self.list_box.remove(c)
        self._build_card(d)

        hdr = Gtk.Label(label="󰤨 Wi-Fi 网络")
        hdr.set_name("header")
        hdr.set_xalign(0.5)
        self.list_box.add(hdr)

        sep = Gtk.Label(label="────────────────────────────────────────")
        sep.set_name("sep")
        self.list_box.add(sep)

        seen = set()
        for line in out.splitlines():
            parts = line.split(":", 2)
            if len(parts) < 1:
                continue
            ssid = parts[0]
            sig = parts[1] if len(parts) > 1 else "0"
            sec = parts[2] if len(parts) > 2 else ""
            if not ssid or ssid in seen:
                continue
            seen.add(ssid)

            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            row.set_name("row")
            row.set_margin_start(12)
            row.set_margin_end(12)
            row.set_margin_top(3)
            row.set_margin_bottom(3)

            sig_lbl = Gtk.Label(label=self.sig_bars(sig))
            sig_lbl.set_name("sig")
            row.pack_start(sig_lbl, False, False, 0)

            ssid_lbl = Gtk.Label(label=ssid)
            ssid_lbl.set_name("ssid")
            ssid_lbl.set_xalign(0)
            ssid_lbl.set_halign(Gtk.Align.START)
            ssid_lbl.set_ellipsize(3)
            ssid_lbl.set_hexpand(True)
            row.pack_start(ssid_lbl, True, True, 0)

            if sec and sec not in ("", "--"):
                lock = Gtk.Label(label="")
                lock.set_name("lock")
                row.pack_start(lock, False, False, 0)

            if ssid == current:
                badge = Gtk.Label(label="已连接")
                badge.set_name("badge")
                row.pack_start(badge, False, False, 0)

            wrapper = Gtk.ListBoxRow()
            wrapper.add(row)
            wrapper.ssid = ssid
            wrapper.secured = bool(sec and sec not in ("", "--"))
            wrapper.is_current = (ssid == current)
            self.list_box.add(wrapper)

        if not seen:
            lbl = Gtk.Label(label="没有找到网络")
            lbl.set_margin_top(12)
            lbl.set_margin_bottom(12)
            self.list_box.add(lbl)

        for c in self.action_bar.get_children():
            self.action_bar.remove(c)

        action_btns = []
        if current:
            disc = Gtk.Button(label="󰤮 断开连接")
            disc.set_name("disc-btn")
            disc.get_style_context().add_class("action-btn")
            disc.connect("clicked", lambda b: threading.Thread(target=self._disconnect, args=(current,), daemon=True).start())
            action_btns.append(disc)

        rescan = Gtk.Button(label="󰑥 重新扫描")
        rescan.set_name("rescan-btn")
        rescan.get_style_context().add_class("action-btn")
        rescan.connect("clicked", lambda b: self.load_networks())
        action_btns.append(rescan)

        settings = Gtk.Button(label="⚙ 网络设置")
        settings.set_name("set-btn")
        settings.get_style_context().add_class("action-btn")
        settings.connect("clicked", lambda b: (subprocess.Popen(["nm-connection-editor"]), Gtk.main_quit()))
        action_btns.append(settings)

        # If only 1-2 buttons, center them
        if len(action_btns) < 3:
            self.action_bar.set_homogeneous(True)
            for btn in action_btns:
                self.action_bar.pack_start(btn, True, True, 0)
        else:
            self.action_bar.set_homogeneous(True)
            for btn in action_btns:
                self.action_bar.pack_start(btn, True, True, 0)

        self.list_box.show_all()
        self.action_bar.show_all()

    def on_activate(self, box, row):
        ssid = getattr(row, "ssid", None)
        if not ssid:
            return
        if getattr(row, "is_current", False):
            threading.Thread(target=self._disconnect, args=(ssid,), daemon=True).start()
        elif getattr(row, "secured", False):
            self._show_password_dialog(ssid)
        else:
            threading.Thread(target=self._connect, args=(ssid,), daemon=True).start()

    def _disconnect(self, ssid):
        r = subprocess.run(["nmcli", "connection", "down", ssid], capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            GLib.idle_add(self._notify, f"断开 {ssid} 失败", r.stderr.strip() or "未知错误")
        try:
            iface = subprocess.run(["nmcli", "-t", "-f", "type,device", "dev", "status"], capture_output=True, text=True, timeout=5).stdout
            iface = [l.split(":")[1] for l in iface.splitlines() if l.startswith("wifi:")][0]
            subprocess.run(["nmcli", "dev", "disconnect", iface], capture_output=True, timeout=10)
        except:
            pass
        GLib.idle_add(self.load_networks)

    def _connect(self, ssid, pwd=None):
        cmd = ["nmcli", "dev", "wifi", "connect", ssid]
        if pwd:
            cmd += ["password", pwd]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            GLib.idle_add(self._notify, f"连接 {ssid} 失败", r.stderr.strip() or "未知错误")
        GLib.idle_add(self.load_networks)

    def _notify(self, summary, body):
        subprocess.run(["dunstify", "-a", "Network", "-u", "critical", summary, body])

    def _show_password_dialog(self, ssid):
        self._dialog_open = True
        dlg = Gtk.Window(title="")
        dlg.set_name("waybar-network-dlg")
        dlg.set_transient_for(self)
        dlg.set_decorated(False)
        dlg.set_keep_above(True)
        dlg.set_skip_taskbar_hint(True)
        dlg.set_resizable(False)
        dlg.set_border_width(0)
        dlg.set_default_size(280, 40)
        dlg.set_type_hint(Gdk.WindowTypeHint.NOTIFICATION)
        dlg.connect("destroy", lambda d: setattr(self, '_dialog_open', False))
        dlg.connect("focus-out-event", lambda w, e: w.destroy())
        dlg.connect("key-press-event", lambda w, e: w.destroy() if e.keyval in (Gdk.KEY_Escape, Gdk.KEY_q) else None)
        dlg_css = b"""
        window#waybar-network-dlg { background: rgba(46, 52, 64, 0.92); border: 1px solid rgba(76, 86, 106, 0.4); border-radius: 6px; }
        * { font-family: "JetBrainsMono Nerd Font", "Noto Sans CJK SC", sans-serif; font-size: 9px; color: #d8dee9; background: transparent; }
        entry { background: #3b4252; border: none; border-radius: 4px; padding: 6px 10px; color: #d8dee9; }
        button { background: rgba(59, 66, 82, 0.5); color: #d8dee9; border: none; border-radius: 4px; padding: 6px 14px; }
        button:hover { background: #88c0d0; color: #2e3440; }
        box { background: transparent; }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(dlg_css)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        dlg.get_style_context().add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        bx = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        bx.set_margin_top(12)
        bx.set_margin_bottom(12)
        bx.set_margin_start(12)
        bx.set_margin_end(12)
        dlg.add(bx)

        lbl = Gtk.Label(label=f"󰠠 输入 {ssid} 的密码")
        bx.pack_start(lbl, False, False, 0)

        entry = Gtk.Entry()
        entry.set_visibility(False)
        entry.connect("activate", lambda e: (dlg.destroy(), threading.Thread(target=self._connect, args=(ssid, entry.get_text()), daemon=True).start()))
        bx.pack_start(entry, False, False, 0)

        btn_b = Gtk.Box(spacing=8)
        btn_b.set_halign(Gtk.Align.END)
        cancel = Gtk.Button(label="取消")
        cancel.connect("clicked", lambda b: dlg.destroy())
        btn_b.pack_start(cancel, False, False, 0)
        ok = Gtk.Button(label="连接")
        ok.connect("clicked", lambda b: (dlg.destroy(), threading.Thread(target=self._connect, args=(ssid, entry.get_text()), daemon=True).start()))
        btn_b.pack_start(ok, False, False, 0)
        bx.pack_start(btn_b, False, False, 0)

        dlg.show_all()

import subprocess as _sp
_cx, _cy = _sp.run(["hyprctl", "cursorpos"], capture_output=True, text=True).stdout.strip().split(", ")
_cx, _cy = int(_cx), int(_cy)

def reposition(retries=5):
    try:
        clients = __import__("json").loads(_sp.run(["hyprctl", "clients", "-j"], capture_output=True, text=True).stdout)
        for c in clients:
            if c.get("title") == "waybar-network-popup":
                addr = c.get("address")
                if addr:
                    _sp.run(["hyprctl", "dispatch", "movewindowpixel", f"exact {max(0, _cx - 210)} {_cy + 20},address:{addr}"])
                return False
    except:
        pass
    if retries > 0:
        GLib.timeout_add(50, lambda: reposition(retries - 1))
    return False

if __name__ == "__main__":
    w = NetworkPopup()
    w.show_all()
    GLib.timeout_add(50, reposition)
    Gtk.main()
