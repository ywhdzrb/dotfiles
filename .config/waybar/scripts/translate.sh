#!/usr/bin/env bash
set -e
TEXT=$(wl-paste --primary 2>/dev/null || wl-paste 2>/dev/null)
if [ -z "$TEXT" ]; then
  dunstify "翻译" "剪贴板为空"
  exit 1
fi
RESULT=$(trans -b -s auto -t zh "$TEXT" 2>/dev/null)
if [ -n "$RESULT" ]; then
  dunstify "📖 $TEXT" "$RESULT"
  echo "$RESULT" | wl-copy
else
  dunstify "翻译" "翻译失败"
fi
