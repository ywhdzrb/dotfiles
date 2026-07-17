#!/usr/bin/env bash
stats=$(nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits 2>/dev/null)
[ -z "$stats" ] && echo "" && exit 0
IFS=', ' read -r util mem_used mem_total temp <<< "$stats"
echo "󰢮 ${util}%"
