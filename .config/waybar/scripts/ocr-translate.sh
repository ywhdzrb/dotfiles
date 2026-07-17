#!/usr/bin/env bash
TMPFILE=$(mktemp /tmp/ocr-XXXXXX.png)
grim -g "$(slurp -d)" "$TMPFILE"
convert "$TMPFILE" -resize 200% -unsharp 0x1 "$TMPFILE"
TEXT=$(tesseract "$TMPFILE" - -l chi_sim+eng --oem 1 --psm 6 2>/dev/null | tr -s '\n' ' ')
rm "$TMPFILE"
if [ -z "$TEXT" ]; then
  dunstify "📖 OCR 翻译" "未识别到文字"
  exit 1
fi
exec python3 ~/.config/waybar/scripts/translate.py "$TEXT"
