#!/usr/bin/env bash
TMPFILE=$(mktemp /tmp/ocr-XXXXXX.png)
grim -g "$(slurp -d)" "$TMPFILE"
# 提高 OCR 精度：放大图片 + LSTM引擎 + 单文本块模式
convert "$TMPFILE" -resize 200% -unsharp 0x1 "$TMPFILE"
TEXT=$(tesseract "$TMPFILE" - -l chi_sim+eng+jpn --oem 1 --psm 6 2>/dev/null | tr -s '\n' ' ')
rm "$TMPFILE"
if [ -n "$TEXT" ]; then
  echo "$TEXT" | wl-copy
  dunstify "📝 OCR" "已识别并复制到剪贴板:\n$TEXT"
else
  dunstify "📝 OCR" "未识别到文字"
fi
