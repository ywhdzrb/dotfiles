#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango
import subprocess, textwrap, sys

S = 80
TEXT = " ".join(sys.argv[1:]) or subprocess.run(["wl-paste", "--primary"], capture_output=True, text=True).stdout.strip() or subprocess.run(["wl-paste"], capture_output=True, text=True).stdout.strip()
if not TEXT:
    exit(0)

# AI 翻译（DeepSeek）
import urllib.request, json, os
RESULT = ""
api_key = ""
sf = os.path.expanduser("~/.secrets")
if os.path.exists(sf):
    for l in open(sf):
        if "ANTHROPIC_AUTH_TOKEN" in l and "=" in l:
            api_key = l.split("=", 1)[1].strip().strip("'\"")
if api_key:
    try:
        b = json.dumps({"model": "deepseek-chat", "max_tokens": 1000,
            "messages": [{"role": "user", "content": f"请将以下内容翻译成中文，只返回翻译结果：\n\n{TEXT}"}]}).encode()
        r = json.loads(urllib.request.urlopen(urllib.request.Request(
            "https://api.deepseek.com/v1/chat/completions", data=b,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}), timeout=15).read())
        RESULT = r.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    except:
        pass

# AI 失败则降级 Bing/Google
if not RESULT:
    for engine in ("bing", "google"):
        try:
            r = subprocess.run(["trans", "-e", engine, "-b", "-s", "auto", "-t", "zh", TEXT], capture_output=True, text=True, timeout=10)
            if r.returncode == 0 and r.stdout.strip():
                RESULT = r.stdout.strip()
                break
        except:
            pass

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

res = Gtk.Label(label=RESULT or "翻译失败（检查网络或 API 限制）")
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
