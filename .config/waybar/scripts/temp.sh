#!/usr/bin/env bash
gpu_temp=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits 2>/dev/null)
cpu_temp=$(sensors -u 2>/dev/null | awk '/Package id 0/{found=1} found && /_input/{print $2; exit}')
[ -z "$cpu_temp" ] && cpu_temp=$(sensors 2>/dev/null | awk '/^CPU/{print $2}' | tr -d '+°C')
[ -z "$cpu_temp" ] && cpu_temp=$(sensors 2>/dev/null | awk '/temp1/{print $2}' | head -1 | tr -d '+°C')
[ -z "$cpu_temp" ] && echo '{"text":"","tooltip":""}' && exit 0

main="${cpu_temp%.*}°C"
tooltip="CPU Package: ${cpu_temp%.*}°C"
while IFS= read -r line; do
  name=$(echo "$line" | sed 's/.*Core *(\(.*\)):.*/\1/')
  val=$(echo "$line" | sed 's/.*: *+\(.*\)°C.*/\1/')
  [ -n "$val" ] && tooltip="$tooltip\nCore $name: ${val%.*}°C"
done < <(sensors 2>/dev/null | grep "Core ")
[ -n "$gpu_temp" ] && tooltip="$tooltip\nGPU: ${gpu_temp%.*}°C"

echo "{\"text\":\" ${main}\",\"tooltip\":\"$tooltip\"}"
