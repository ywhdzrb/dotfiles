#!/usr/bin/env bash
TMPFILE=$(mktemp /tmp/ocr-XXXXXX.png)
grim -g "$(slurp -d)" "$TMPFILE"
TEXT=$(tesseract "$TMPFILE" - -l chi_sim+eng 2>/dev/null | tr -s '\n' ' ')
rm "$TMPFILE"
if [ -n "$TEXT" ]; then
  echo "$TEXT" | wl-copy
  dunstify "📝 OCR" "已识别并复制到剪贴板:\n$TEXT"
else
  dunstify "📝 OCR" "未识别到文字"
fi
