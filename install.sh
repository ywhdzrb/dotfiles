#!/usr/bin/env bash
set -e
DOTFILES="$(cd "$(dirname "$0")" && pwd)"

link() {
  src="$DOTFILES/$1"
  dst="$HOME/$1"
  mkdir -p "$(dirname "$dst")"
  [ -e "$dst" ] && [ ! -L "$dst" ] && mv "$dst" "$dst.bak"
  ln -sf "$src" "$dst"
  echo "  $1"
}

echo "安装依赖 (yay)？[y/N]"
read -r REPLY
if [[ $REPLY =~ ^[Yy]$ ]]; then
  yay -Sa --noconfirm $(grep -v '^#' "$DOTFILES/packages.txt")
fi

# Zinit（Zsh 插件管理器）
if [ ! -d "$HOME/.local/share/zinit/zinit.git" ]; then
  echo "安装 Zinit..."
  bash -c "$(curl -fsSL https://git.io/zinit-install)" 2>/dev/null || \
    git clone https://github.com/zdharma-continuum/zinit ~/.local/share/zinit/zinit.git
fi

echo "Linking dotfiles..."
link .zshrc
link .config/hypr/hyprland.conf
link .config/hypr/menu.rasi
link .config/hypr/powermenur.rasi
link .config/hypr/cliphist_menu.rasi
link .config/hypr/hyprlock.conf
link .config/hypr/colors.rasi
link .config/hypr/powermenu.sh
link .config/waybar/config
link .config/waybar/style.css
link .config/waybar/powermenur.rasi
link .config/waybar/colors.rasi
link .config/waybar/powermenu.sh
for f in "$DOTFILES"/.config/waybar/scripts/*; do
  link ".config/waybar/scripts/$(basename "$f")"
done
link .config/kitty/kitty.conf
link .config/kitty/current-theme.conf
link .config/dunst/dunstrc
link .config/libinput-gestures.conf
link .config/hyprswitch/config.json
link .config/qt5ct/qt5ct.conf
link .config/qt6ct/qt6ct.conf
link .config/Kvantum/kvantum.kvconfig
link .config/environment.d/qt.conf
link .config/fastfetch/config.jsonc
link .config/fastfetch/aln.png
link .config/fastfetch/neuro.png
link .config/gtk-3.0/settings.ini
link .config/gtk-4.0/settings.ini
# 壁纸（Steam Workshop）
WALLPAPER_DIR="$HOME/.local/share/Steam/steamapps/workshop/content/431960/1674220875"
mkdir -p "$(dirname "$WALLPAPER_DIR")"
[ -d "$WALLPAPER_DIR" ] && [ ! -L "$WALLPAPER_DIR" ] && mv "$WALLPAPER_DIR" "${WALLPAPER_DIR}.bak"
ln -sf "$DOTFILES/wallpaper/steam-workshop" "$WALLPAPER_DIR"
echo "  wallpaper/steam-workshop"

# 静态壁纸
[ -f ~/wallpaper/16.png ] || {
  mkdir -p ~/wallpaper
  ln -sf "$DOTFILES/wallpaper/16.png" ~/wallpaper/16.png
  echo "  wallpaper/16.png"
}

echo "Done!"
