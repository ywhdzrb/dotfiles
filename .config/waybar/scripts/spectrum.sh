#!/usr/bin/env bash
bars=(▁ ▂ ▃ ▄ ▅ ▆ ▇ █ █)
last=$(timeout 0.4 cava -p "$HOME/.config/waybar/cava_config" 2>/dev/null | tail -1)
[ -z "$last" ] && echo "▁▁▁▁▁▁▁▁▁▁▁▁" && exit 0
IFS=';' read -ra vals <<< "$last"
for v in "${vals[@]}"; do
    v="${v//[!0-9]/}"
    [[ -n "$v" && "$v" -ge 0 && "$v" -lt 9 ]] 2>/dev/null && output+="${bars[$v]}"
done
echo "${output:-▁▁▁▁▁▁▁▁▁▁▁▁}"
