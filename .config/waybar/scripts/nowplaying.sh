#!/usr/bin/env bash

CACHE_DIR="/tmp/waybar-lyrics"
mkdir -p "$CACHE_DIR"

pick_player() {
    local filter="$1" state="$2"
    for p in $(playerctl -l 2>/dev/null); do
        echo "$p" | grep -qiE "$filter" || continue
        [ "$(playerctl -p "$p" status 2>/dev/null)" = "$state" ] || continue
        PLAYER="-p $p"; PLAYER_ID="$p"; return 0
    done; return 1
}

show_fallback() {
    local text="$([ -n "$artist" ] && echo "$artist - $title" || echo "$title")"
    [ "${#text}" -gt 80 ] && text="${text:0:79}…"
    echo " $text"
}

show_lyrics() {
    [ ! -f "$cache_file" ] && return 1
    local meta=$(cat "$meta_file" 2>/dev/null)
    if [ "$meta" = "lrc" ] || head -1 "$cache_file" | grep -q '^\['; then
        pos=$(playerctl $PLAYER position 2>/dev/null)
        [ -z "$pos" ] && return 1
        pos_sec=${pos%.*}
        local line=$(awk -v pos="$pos_sec" '
            /^\[[0-9]+:[0-9]+[:.][0-9]+]/ {
                match($0, /^\[([0-9]+):([0-9]+)[:.]([0-9]+)]/)
                if (RSTART) {
                    ts = substr($0, RSTART+1, RLENGTH-2)
                    n = split(ts, a, ":")
                    m = a[1]; s = a[2]; c = a[3]
                    if (n == 3) { secs = m*60 + s + c/100 }
                    else { secs = m*60 + s }
                    rest = substr($0, RLENGTH+1)
                    gsub(/^ +| +$/, "", rest)
                    if (secs <= pos+0.5) { last=rest }
                }
            }
            END { if (last) print last }
        ' "$cache_file")
        [ -n "$line" ] && echo "♫ $line" && return 0
        return 1
    fi
    total=$(playerctl $PLAYER metadata mpris:length 2>/dev/null)
    pos=$(playerctl $PLAYER position 2>/dev/null)
    if [ -z "$pos" ] || [ -z "$total" ] || [ "$total" -eq 0 ]; then
        local line=$(head -1 "$cache_file" 2>/dev/null)
        [ -n "$line" ] && [ "$line" != "__NO_LYRICS__" ] && echo "♫ $line" && return 0
        return 1
    fi
    total_sec=$((total / 1000000))
    [ "$total_sec" -eq 0 ] && return 1
    local total_lines=$(wc -l < "$cache_file")
    [ "$total_lines" -eq 0 ] && return 1
    local ratio=$(awk "BEGIN {printf \"%.4f\", $pos / $total_sec}")
    local line_idx=$(awk "BEGIN {printf \"%d\", $ratio * $total_lines + 1}")
    [ "$line_idx" -gt "$total_lines" ] && line_idx=$total_lines
    local line=$(sed -n "${line_idx}p" "$cache_file")
    [ -n "$line" ] && [ "$line" != "__NO_LYRICS__" ] && echo "♫ $line" && return 0
    return 1
}

fetch_splayer() {
    local player=$(playerctl -l 2>/dev/null | grep -i splayer | head -1)
    [ -z "$player" ] && return 1
    local trackid=$(playerctl -p "$player" metadata mpris:trackid 2>/dev/null)
    local song_id=$(echo "$trackid" | grep -oP '\d+' | tail -1)
    [ -z "$song_id" ] && return 1
    local response=$(curl -s --max-time 1 "http://localhost:25884/api/netease/lyric/new?id=$song_id")
    [ -z "$response" ] && return 1
    local lrc=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())
    raw = data.get('lrc', {}).get('lyric', '').strip()
    if raw:
        for line in raw.splitlines():
            line = line.strip()
            if not line: continue
            if line.startswith('{'):
                try:
                    obj = json.loads(line)
                    t = obj.get('t', 0)
                    text = ''.join(c.get('tx', '') for c in obj.get('c', []))
                    if text:
                        m, s = divmod(t / 1000, 60)
                        print(f'[{int(m):02d}:{s:06.3f}]{text}')
                except:
                    pass
            else:
                print(line)
    else:
        for k in ('romalrc', 'tlyric'):
            r = data.get(k, {}).get('lyric', '')
            if r.strip(): print(r.strip()); break
except:
    pass
" 2>/dev/null)
    [ -z "$lrc" ] && return 1
    echo "$lrc" > "$cache_file"
    echo "lrc" > "$meta_file"
    return 0
}

fetch_remote() {
    local response
    local eartist=$(printf '%s' "$artist" | jq -sRr @uri)
    local etitle=$(printf '%s' "$title" | jq -sRr @uri)
    response=$(curl -s --max-time 2 "https://lrclib.net/api/get?artist_name=$eartist&track_name=$etitle")
    if echo "$response" | jq -e '.syncedLyrics' >/dev/null 2>&1; then
        echo "$(echo "$response" | jq -r '.syncedLyrics')" > "$cache_file"
        echo "lrc" > "$meta_file"; return 0
    fi
    if echo "$response" | jq -e '.plainLyrics' >/dev/null 2>&1; then
        echo "$(echo "$response" | jq -r '.plainLyrics')" > "$cache_file"
        echo "plain" > "$meta_file"; return 0
    fi
    response=$(curl -s --max-time 2 "https://api.lyrics.ovh/v1/$eartist/$etitle")
    if echo "$response" | jq -e '.lyrics' >/dev/null 2>&1; then
        echo "$(echo "$response" | jq -r '.lyrics')" > "$cache_file"
        echo "plain" > "$meta_file"; return 0
    fi
    return 1
}

last_key=""
while true; do
    PLAYER=""; PLAYER_ID=""
    pick_player "splayer|spotify|mpd|vlc|strawberry" Playing || pick_player "firefox|chrome|brave" Playing || pick_player "splayer|spotify|mpd|vlc|strawberry|firefox|chrome|brave" Paused

    status=$(playerctl $PLAYER status 2>/dev/null)
    if [ "$status" != "Playing" ] && [ "$status" != "Paused" ]; then
        wtitle=$(hyprctl activewindow -j 2>/dev/null | jq -r '.title // empty' 2>/dev/null)
        [ -n "$wtitle" ] && out=" $wtitle" || out=""
        if [ "$out" != "$last_out" ]; then
            echo "$out"; last_out="$out"
        fi
        last_key=""; sleep 0.5; continue
    fi

    title=$(playerctl $PLAYER metadata title 2>/dev/null)
    artist=$(playerctl $PLAYER metadata artist 2>/dev/null)
    [ -z "$title" ] && sleep 0.5 && continue

    cache_key=$(echo "${PLAYER_ID:-none}|$artist|$title" | md5sum | cut -d' ' -f1)
    cache_file="$CACHE_DIR/$cache_key"
    meta_file="$CACHE_DIR/${cache_key}_meta"
    rate_file="$CACHE_DIR/${cache_key}.ratelimit"

    if [ "$cache_key" != "$last_key" ]; then
        last_key="$cache_key"
        lyrics_header=$(head -1 "$cache_file" 2>/dev/null)
        if [ -z "$lyrics_header" ] || [ "$lyrics_header" = "__NO_LYRICS__" ]; then
            if [ ! -f "$rate_file" ] || [ $(($(date +%s) - $(cat "$rate_file"))) -ge 5 ]; then
                echo "$(date +%s)" > "$rate_file"
                (if echo "$PLAYER_ID" | grep -qi splayer; then fetch_splayer; else false; fi >/dev/null 2>&1 || fetch_remote >/dev/null 2>&1 || echo "__NO_LYRICS__" > "$cache_file") &
            fi
        fi
    fi

    out=$(show_lyrics 2>/dev/null || show_fallback)
    if [ "$out" != "$last_out" ]; then
        echo "$out"; last_out="$out"
    fi
    sleep 0.5
done
