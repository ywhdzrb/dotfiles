#!/usr/bin/env bash
TEXT=$(wl-paste --primary 2>/dev/null || wl-paste 2>/dev/null)
[ -z "$TEXT" ] && TEXT="$1"
[ -z "$TEXT" ] && dunstify "翻译" "剪贴板为空" && exit 1
exec python3 ~/.config/waybar/scripts/translate.py "$TEXT"
