#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import subprocess, sys, os, json, urllib.request, threading, http.client

TEXT = " ".join(sys.argv[1:]) or subprocess.run(["wl-paste", "--primary"], capture_output=True, text=True).stdout.strip() or subprocess.run(["wl-paste"], capture_output=True, text=True).stdout.strip()
if not TEXT: exit(0)

# --- GTK window ---
w = Gtk.Window(title="translate")
w.set_decorated(False)
w.set_keep_above(True)
w.set_skip_taskbar_hint(True)
w.set_resizable(False)
w.set_border_width(0)
w.set_type_hint(Gdk.WindowTypeHint.UTILITY)
w.connect("key-press-event", lambda w, e: Gtk.main_quit() if e.keyval in (Gdk.KEY_Escape, Gdk.KEY_q) else None)

css = b"""
* { font-family: "JetBrainsMono Nerd Font", sans-serif; font-size: 11px; }
window { background: rgba(46, 52, 64, 0.92); border: 1px solid rgba(76, 86, 106, 0.4); border-radius: 6px; }
#source { color: #88c0d0; font-weight: bold; padding: 0 0 4px; }
#result { color: #d8dee9; }
"""
provider = Gtk.CssProvider()
provider.load_from_data(css)
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
box.set_margin_top(10)
box.set_margin_bottom(10)
box.set_margin_start(12)
box.set_margin_end(12)

src = Gtk.Label(label=TEXT[:200])
src.set_name("source"); src.set_xalign(0); src.set_line_wrap(True)
box.pack_start(src, False, False, 0)

res = Gtk.Label(label="翻译中...")
res.set_name("result"); res.set_xalign(0); res.set_line_wrap(True); res.set_selectable(True)
box.pack_start(res, False, False, 0)

w.add(box); w.show_all(); w.set_default_size(500, 100); w.present()

# --- Streaming AI translation ---
def stream_ai():
    api_key = ""
    sf = os.path.expanduser("~/.secrets")
    if os.path.exists(sf):
        for l in open(sf):
            if "ANTHROPIC_AUTH_TOKEN" in l and "=" in l:
                api_key = l.split("=", 1)[1].strip().strip("'\"")
    if not api_key:
        fallback()
        return

    try:
        body = json.dumps({"model": "deepseek-chat", "max_tokens": 1000, "stream": True,
            "messages": [{"role": "user", "content": f"请将以下内容翻译成中文，只返回翻译结果：\n\n{TEXT}"}]}).encode()
        req = urllib.request.Request("https://api.deepseek.com/v1/chat/completions", data=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"})
        r = urllib.request.urlopen(req, timeout=30)
        buf = ""
        full = ""
        while True:
            chunk = r.read(1).decode()
            if not chunk: break
            buf += chunk
            if buf.endswith("\n\n"):
                for line in buf.strip().split("\n"):
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]": break
                        try:
                            d = json.loads(data)
                            delta = d.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if delta:
                                full += delta
                                GLib.idle_add(res.set_text, full)
                        except: pass
                buf = ""
        if not full:
            r2 = json.loads(urllib.request.urlopen(urllib.request.Request(
                "https://api.deepseek.com/v1/chat/completions",
                data=json.dumps({"model": "deepseek-chat", "max_tokens": 1000,
                    "messages": [{"role": "user", "content": f"请将以下内容翻译成中文，只返回翻译结果：\n\n{TEXT}"}]}).encode(),
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}), timeout=15).read())
            full = r2.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            GLib.idle_add(res.set_text, full or "翻译失败")
    except Exception as e:
        GLib.idle_add(res.set_text, f"AI 失败，降级中...")
        fallback()

def fallback():
    for engine in ("bing", "google"):
        try:
            r = subprocess.run(["trans", "-e", engine, "-b", "-s", "auto", "-t", "zh", TEXT], capture_output=True, text=True, timeout=10)
            if r.returncode == 0 and r.stdout.strip():
                GLib.idle_add(res.set_text, r.stdout.strip())
                return
        except: pass
    GLib.idle_add(res.set_text, "翻译失败（检查网络）")

threading.Thread(target=stream_ai, daemon=True).start()
Gtk.main()
