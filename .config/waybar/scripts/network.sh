#!/usr/bin/env bash

notify() { dunstify -r 9911 -t 2000 "$@" 2>/dev/null || notify-send -t 2000 "$@"; }

case "$1" in
status)
    ssid=$(nmcli -t -f active,ssid dev wifi | grep '^yes' | cut -d: -f2)
    if [ -n "$ssid" ]; then
        sig=$(nmcli -t -f active,signal dev wifi | grep '^yes' | cut -d: -f2)
        echo "󰤨 $ssid ($sig%)"
    else
        echo "󰤮 未连接"
    fi
    exit 0
    ;;
esac

# Rofi based WiFi selector
wifi_list=$(nmcli -t -f ssid,signal,security dev wifi list --rescan yes | awk -F: '{
    ssid=$1; sig=$2; sec=$3
    if (ssid && !seen[ssid]++) {
        bars=""
        if (sig >= 80) bars="󰤨"
        else if (sig >= 60) bars="󰤥"
        else if (sig >= 40) bars="󰤢"
        else if (sig >= 20) bars="󰤟"
        else bars="󰤯"
        if (sec && sec != "") sec=" "
        else sec=""
        printf "%s %s%s\n", bars, ssid, sec
    }
}')

current=$(nmcli -t -f active,ssid dev wifi | grep '^yes' | cut -d: -f2)

chosen=$(echo "$wifi_list" | rofi -dmenu -p "Wi-Fi" -theme ~/.config/hypr/menu.rasi -selected-row "$(echo "$wifi_list" | grep -n "$current" | cut -d: -f1 | head -1)")

[ -z "$chosen" ] && exit 0

ssid=$(echo "$chosen" | sed 's/^[^ ]* //; s/ $//')

nmcli -t -f in-use,ssid dev wifi | grep -q "^\\*:$ssid" && {
    nmcli connection down "$ssid" 2>/dev/null || nmcli dev disconnect wlp0s20f3
    notify "󰤮 已断开 $ssid"
    exit 0
}

if nmcli -t -f ssid,security dev wifi | grep -q "^$ssid:.*WPA\|^$ssid:.*WEP"; then
    pass=$(rofi -dmenu -password -p "密码" -theme ~/.config/hypr/menu.rasi)
    [ -z "$pass" ] && exit 0
    nmcli dev wifi connect "$ssid" password "$pass" 2>/tmp/wifi_err
else
    nmcli dev wifi connect "$ssid" 2>/tmp/wifi_err
fi

if [ $? -eq 0 ]; then
    notify "󰤨 已连接 $ssid"
else
    notify "󰤮 连接失败: $(cat /tmp/wifi_err)"
fi