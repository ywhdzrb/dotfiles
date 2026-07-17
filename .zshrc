# =============================================================================
# Zsh 配置文件 (~/.zshrc)
# 完整版：合并 + 修复 fzf-tab 预览（目录显示、非文件补全）
# 修改：fzf 文件/目录选择快捷键 → kitten choose-files
# =============================================================================

# ----------------------------- 1. 瞬时提示 -----------------------------------
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi
typeset -g POWERLEVEL9K_INSTANT_PROMPT=quiet

# ----------------------------- 2. 插件管理器 Zinit ---------------------------
ZINIT_HOME="${ZDOTDIR:-$HOME}/.local/share/zinit/zinit.git"
if [[ ! -f "$ZINIT_HOME/zinit.zsh" ]]; then
  print -P "%F{33}▓▒░ %F{220}Installing Zinit…%f"
  command mkdir -p "${ZINIT_HOME:h}" && command chmod g-rwX "${ZINIT_HOME:h}"
  command git clone https://github.com/zdharma-continuum/zinit "$ZINIT_HOME" && \
    print -P "%F{33}▓▒░ %F{34}Installation successful.%f" || \
    print -P "%F{160}▓▒░ Installation failed.%f"
fi
source "$ZINIT_HOME/zinit.zsh"
autoload -Uz _zinit && (( ${+_comps} )) && _comps[zinit]=_zinit

# ----------------------------- 3. 基础环境设置 -------------------------------
HISTFILE="${ZDOTDIR:-$HOME}/.zsh_history"
HISTSIZE=100000
SAVEHIST=100000
setopt EXTENDED_HISTORY INC_APPEND_HISTORY SHARE_HISTORY
setopt HIST_IGNORE_DUPS HIST_IGNORE_SPACE HIST_REDUCE_BLANKS HIST_VERIFY

export EDITOR='nvim'
export VISUAL='nvim'

export ANDROID_SDK_ROOT="$HOME/android-sdk"
export PATH="$PATH:$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$ANDROID_SDK_ROOT/emulator:$ANDROID_SDK_ROOT/platform-tools"
export PATH="/opt/baidunetdisk:$PATH"
export LIBVA_DRIVER_NAME='iHD'
export PATH="$HOME/.npm-global/bin:$PATH"
export VCPKG_ROOT=~/vcpkg
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
export PATH="/home/ywhdzrb/ldwj/Cavvy/target/release:$PATH"

export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
export TMOE_ZSH_DIR="${HOME}/.config/tmoe-zsh"
export TMOE_ZSH_GIT_DIR="${TMOE_ZSH_DIR}/git"
export TMOE_ZSH_TOOL_DIR="${TMOE_ZSH_GIT_DIR}/tools"
export ZINIT_THEME_DIR="${HOME}/.zinit/themes/_local"

export ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
[ -f ~/.secrets ] && source ~/.secrets
export ANTHROPIC_MODEL=deepseek-v4-pro[1m]
export ANTHROPIC_DEFAULT_OPUS_MODEL=deepseek-v4-pro[1m]
export ANTHROPIC_DEFAULT_SONNET_MODEL=deepseek-v4-pro[1m]
export ANTHROPIC_DEFAULT_HAIKU_MODEL=deepseek-v4-flash
export CLAUDE_CODE_SUBAGENT_MODEL=deepseek-v4-flash
export CLAUDE_CODE_EFFORT_LEVEL=max

setopt AUTO_CD CORRECT NO_BEEP INTERACTIVE_COMMENTS NO_GLOBAL_RCS

# ----------------------------- 4. 工具检测与别名 -----------------------------
# 4.1 ls 增强
if command -v eza &>/dev/null; then
  alias ls='eza --icons --color=auto --group-directories-first'
  alias ll='eza -l --icons --color=auto --group-directories-first'
  alias la='eza -la --icons --color=auto --group-directories-first'
  alias lt='eza --tree --icons --color=auto --group-directories-first'
  alias l='eza -lbah'
  alias lsa='eza -lbagR'
  alias lst='eza -lTabgh'
elif command -v exa &>/dev/null; then
  alias ls='exa --icons --color=auto --group-directories-first'
  alias ll='exa -l --icons --color=auto --group-directories-first'
  alias la='exa -la --icons --color=auto --group-directories-first'
  alias lt='exa --tree --icons --color=auto --group-directories-first'
  alias l='exa -lbah'
  alias lsa='exa -lbagR'
  alias lst='exa -lTabgh'
else
  alias ls='ls --color=auto'
  alias ll='ls -lh'
  alias la='ls -lAh'
  alias l='ls -lah'
  alias lsa='ls -lah'
  alias lst='tree -pCsh'
fi

if [[ -n "$(command -v exa || command -v eza)" ]]; then
  alias lls='$(whereis ls | awk "{print \$2}")'
fi

# 4.2 cat 增强
if command -v batcat &>/dev/null; then
  alias cat='batcat -pp'
elif command -v bat &>/dev/null; then
  alias cat='bat -pp'
fi
alias lcat='$(whereis cat | awk "{print \$2}")'
export BAT_PAGER="less -m -RFQ"

# 4.3 通用颜色别名
alias grep='grep --color=auto'
alias fgrep='fgrep --color=auto'
alias egrep='egrep --color=auto'
alias ip='ip -color=auto'
alias diff='diff --color=auto'

# 4.4 Git 别名
alias g='git'
alias gs='git status'
alias ga='git add'
alias gc='git commit'
alias gp='git push'
alias gl='git log --oneline --graph'
alias gd='git diff'
alias gc1='git clone --recursive --depth=1'

# 4.5 Neovim 别名
alias v='nvim'
alias vi='nvim'
alias vim='nvim'
alias nv='nvim'

# 4.6 Python 别名
alias py='python3'
alias python='python3'
alias pip='pip3'
alias venv='python3 -m venv'

# 4.7 系统别名
case "$OSTYPE" in
  linux-gnu*)
    if [[ -f /etc/arch-release ]]; then
      alias update='sudo pacman -Syu'
      alias cleanup='sudo pacman -Sc'
      alias pkg-search='pacman -Ss'
      alias pkg-install='sudo pacman -S'
      alias pkg-remove='sudo pacman -Rns'
    elif [[ -f /etc/debian_version ]]; then
      alias update='sudo apt update && sudo apt upgrade'
      alias cleanup='sudo apt autoremove && sudo apt autoclean'
      alias pkg-search='apt search'
      alias pkg-install='sudo apt install'
      alias pkg-remove='sudo apt remove'
    fi
    alias df='df -h'
    alias du='du -h'
    alias free='free -h'
    alias ps='ps aux'
    alias top='htop'
    ;;
  darwin*)
    alias update='brew update && brew upgrade'
    alias cleanup='brew cleanup'
    alias pkg-search='brew search'
    alias pkg-install='brew install'
    alias pkg-remove='brew uninstall'
    ;;
esac

# 4.8 常用别名
alias reboot='sudo reboot'
alias shutdown='sudo shutdown now'
alias off='sudo shutdown now'
alias _='sudo '
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias .....='cd ../../../..'
alias ......='cd ../../../../..'
alias 1='cd -'
alias 2='cd -2'
alias 3='cd -3'
alias 4='cd -4'
alias 5='cd -5'
alias 6='cd -6'
alias 7='cd -7'
alias 8='cd -8'
alias 9='cd -9'
alias myip='curl -s ifconfig.me'
alias localip='ip addr show | grep "inet " | grep -v 127.0.0.1'
alias ports='netstat -tulpn'
alias cp='cp -i'
alias mv='mv -i'
alias rm='rm -i'
alias mkdir='mkdir -p'
alias wget='wget -c'
alias md='mkdir -p'
alias rd='rmdir'
alias afind='ack -il'
alias globurl='noglob urlglobber'

command -v tmoe &>/dev/null && alias t=tmoe

# ----------------------------- 5. 通用预览命令主体（用于 fzf 普通调用）--------
# 仅用于 fzf 本身的预览（如 CTRL-T），现在 CTRL-T 已改为 kitten，但仍保留作为函数备用
FZF_PREVIEW_BODY='
  if [[ -d "{PATH}" ]]; then
    ls -la --color=always "{PATH}"
  elif [[ -f "{PATH}" ]]; then
    if command -v bat >/dev/null 2>&1; then
      bat --style=numbers --color=always --line-range :500 "{PATH}"
    else
      cat "{PATH}"
    fi
  else
    echo "📦 选中：{PATH}"
  fi 2>/dev/null
'

# ----------------------------- 6. 插件加载 -----------------------------------
# 语法高亮
zinit ice lucid atinit"ZINIT[COMPINIT_OPTS]=-C; zpcompinit; zpcdreplay"
zinit light zdharma-continuum/fast-syntax-highlighting

# 自动建议（补全文字颜色）
ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=cyan'
zinit ice wait'0' lucid atload"_zsh_autosuggest_start"
zinit light zsh-users/zsh-autosuggestions

# 历史搜索高亮颜色 (必须在插件加载前设置)
HISTORY_SUBSTRING_SEARCH_HIGHLIGHT_FOUND='fg=cyan,bold,underline'
HISTORY_SUBSTRING_SEARCH_HIGHLIGHT_NOT_FOUND='fg=red,bold,underline'

# 历史子串搜索
zinit ice wait'0' lucid
zinit light zsh-users/zsh-history-substring-search

# fzf（仍需要，因为 fzf-tab 和历史搜索依赖）
if ! command -v fzf &>/dev/null; then
  zinit ice from'gh-r' as'command' pick'bin/fzf'
  zinit light junegunn/fzf
fi

# fzf-tab 补全（保留，用于 tab 补全弹窗）
zinit ice wait'0' lucid
zinit light Aloxaf/fzf-tab

# 补全增强
zinit ice wait'1' blockf lucid atpull'zinit creinstall -q .'
zinit light zsh-users/zsh-completions

# zoxide 智能目录跳转
zinit ice from'gh-r' as'command' pick'zoxide'
zinit light ajeetdsouza/zoxide
export _ZO_FZF_OPTS="--preview '${FZF_PREVIEW_BODY//\{PATH\}/\{\}}'"
eval "$(zoxide init zsh --cmd j)"

# Oh-My-Zsh 轻量 snippet
zinit snippet OMZ::plugins/sudo/sudo.plugin.zsh
zinit snippet OMZ::plugins/git/git.plugin.zsh
zinit snippet OMZ::plugins/colored-man-pages/colored-man-pages.plugin.zsh
zinit snippet OMZ::plugins/extract/extract.plugin.zsh

# 主题 Powerlevel10k
zinit ice depth=1
zinit light romkatv/powerlevel10k
[[ -f ~/.p10k.zsh ]] && source ~/.p10k.zsh

# ----------------------------- 7. 键盘绑定 -----------------------------------
bindkey '^[[A' history-substring-search-up
bindkey '^[[B' history-substring-search-down
bindkey -M vicmd 'k' history-substring-search-up
bindkey -M vicmd 'j' history-substring-search-down

# === 改动：fzf 文件/目录选择快捷键 → kitten choose-files ===
if command -v kitten &>/dev/null; then
  # 用 kitten choose-files 替代原来的 fzf-file-widget (Ctrl+T)
  # 可选择多个文件/目录，路径插入到命令行
  __kitty_file_widget() {
    setopt localoptions pipefail no_aliases 2>/dev/null
    local selected
    selected=$(kitten choose-files --multiple "$(pwd)" 2>/dev/null)
    if [[ -n "$selected" ]]; then
      # 将所选路径（可能多行）转换为空格分隔并追加到 LBUFFER
      local IFS=$'\n'
      local files=(${(f)selected})
      LBUFFER+="${(j: :)files}"
    fi
    zle reset-prompt
  }
  zle -N __kitty_file_widget
  bindkey '^T' __kitty_file_widget   # Ctrl+T 插入文件路径

  # 替代原来的 fzf-cd-widget (Alt+C)
  __kitty_cd_widget() {
    setopt localoptions pipefail no_aliases 2>/dev/null
    local dir
    dir=$(kitten choose-files --type=directory "$(pwd)" 2>/dev/null | head -1)
    if [[ -n "$dir" && -d "$dir" ]]; then
      cd "$dir"
      zle reset-prompt
      zle accept-line 2>/dev/null || true  # 直接执行 cd，可改为只切换不执行回车
    fi
  }
  zle -N __kitty_cd_widget
  bindkey '^[c' __kitty_cd_widget       # Alt+C 跳转目录

  # 原有的 Ctrl+F 也可以用 kitten 覆盖（默认是 fzf-file-widget）
  bindkey '^F' __kitty_file_widget
else
  echo "[提示] 未找到 kitten 命令，Ctrl+T / Alt+C 回退到 fzf（若已安装）"
fi

# 保留 fzf 的 Ctrl+R 历史搜索（不冲突）
if command -v fzf &>/dev/null; then
  # 仅加载 fzf 的历史搜索、补全等（不加载文件选择 widget，避免覆盖）
  source <(fzf --zsh)
  # 显式重新绑定我们的 kitty 快捷键，确保覆盖
  bindkey '^T' __kitty_file_widget 2>/dev/null
  bindkey '^[c' __kitty_cd_widget 2>/dev/null
fi

bindkey '^U' backward-kill-line
bindkey '^W' backward-kill-word
bindkey '^A' beginning-of-line
bindkey '^E' end-of-line

# ----------------------------- 8. 补全系统配置 -------------------------------
autoload -Uz compinit && compinit

zstyle ':completion:*' completer _expand _complete _ignored _approximate
zstyle ':completion:*' list-colors ${(s.:.)LS_COLORS}
zstyle ':completion:*' menu select=2
zstyle ':completion:*' select-prompt '%SScrolling active: current selection at %p%s'
zstyle ':completion:*' matcher-list '' 'm:{a-z}={A-Z}' 'm:{a-zA-Z}={A-Za-z}' 'r:|[._-]=* r:|=* l:|=*'
zstyle ':completion:*' group-name ''
zstyle ':completion:*' verbose yes
zstyle ':completion:*' rehash true
# ----------------------------- 9. fzf 全局配置 -------------------------------
# 注意：以下 FZF_DEFAULT_COMMAND 等仅影响 fzf 原生命令，不影响 kitten
if command -v fd &>/dev/null; then
  export FZF_DEFAULT_COMMAND='fd --type f --hidden --follow --exclude .git --exclude node_modules 2>/dev/null'
  export FZF_ALT_C_COMMAND='fd --type d --hidden --follow --exclude .git --exclude node_modules 2>/dev/null'
else
  export FZF_DEFAULT_COMMAND='find . -type f -not -path "*/.git/*" -not -path "*/node_modules/*" 2>/dev/null'
  export FZF_ALT_C_COMMAND='find . -type d -not -path "*/.git/*" -not -path "*/node_modules/*" 2>/dev/null'
fi

# fzf 普通调用预览（已不再用于文件选择，但历史/函数仍用得到）
export FZF_DEFAULT_OPTS="--height 90% --layout=reverse --border --preview '${FZF_PREVIEW_BODY//\{PATH\}/\{\}}' --color=bg:#2e3440,fg:#81a1c1,hl:#88c0d0 --color=bg+:#81a1c1,fg+:#eceff4,hl+:#eceff4 --color=info:#8fbcbb,prompt:#88c0d0,pointer:#eceff4 --color=marker:#a3be8c,spinner:#a3be8c,header:#81a1c1 --color=gutter:#2e3440,border:#81a1c1"
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
export FZF_CTRL_T_OPTS="--multi --preview '${FZF_PREVIEW_BODY//\{PATH\}/\{\}}'"   # kitten 不使用
export FZF_ALT_C_OPTS="--preview '${FZF_PREVIEW_BODY//\{PATH\}/\{\}}'"            # kitten 不使用
export FZF_CTRL_R_OPTS="--preview 'echo {}' --preview-window down:3:hidden:wrap"

# ===== fzf-tab 预览配置（核心修复）=====
zstyle ':fzf-tab:*' continuous-trigger 'space'
zstyle ':fzf-tab:*' fzf-bindings 'tab:accept,btab:cancel'
zstyle ':fzf-tab:*' prefix ''
zstyle ':fzf-tab:*' switch-group ',' '.'
zstyle ':fzf-tab:*' fzf-flags --height 90% --layout=reverse --border

zstyle ':fzf-tab:*' fzf-preview '
  item_path="$realpath"
  item_text="{q}"
  if [[ -z "$item_path" ]]; then
    echo "📦 补全项：$item_text"
  elif [[ -d "$item_path" ]]; then
    ls -la --color=always "$item_path" 2>/dev/null || echo "无法读取目录：$item_path"
  elif [[ -f "$item_path" ]]; then
    if command -v bat >/dev/null 2>&1; then
      bat --style=numbers --color=always --line-range :500 "$item_path" 2>/dev/null || cat "$item_path"
    else
      cat "$item_path" 2>/dev/null || echo "无法预览文件：$item_path"
    fi
  else
    echo "📌 无法预览：$item_text"
  fi
'

zstyle ':fzf-tab:complete:pacman:*' fzf-preview '
  pacman -Si {q} 2>/dev/null || echo "软件包：{q}"
'

zstyle ':fzf-tab:complete:cd:*' fzf-preview '
  if [[ -d "$realpath" ]]; then
    if command -v eza >/dev/null 2>&1; then
      eza --tree --level=2 --color=always "$realpath" 2>/dev/null || ls -la --color=always "$realpath"
    elif command -v exa >/dev/null 2>&1; then
      exa --tree --level=2 --color=always "$realpath" 2>/dev/null || ls -la --color=always "$realpath"
    else
      ls -la --color=always "$realpath"
    fi
  else
    echo "目录：{q}"
  fi
'

zstyle ':fzf-tab:complete:kill:*' fzf-preview '
  ps -p $realpath -o pid,user,comm,args 2>/dev/null || echo "进程 PID：{q}"
'

# ----------------------------- 10. 实用函数 ---------------------------------
# 大部分仍使用 fzf，因为 kitten choose-files 不适合这些场景（如进程、容器等）
fzf-file() {
  fzf --height 40% --reverse
}

fe() {
  local file
  file=$(fzf --height 40% --reverse) && ${EDITOR:-vim} "$file"
}

fcd() {
  local dir
  dir=$(find "${1:-.}" -type d 2>/dev/null | fzf --height 40% --reverse) && cd "$dir"
}

git-branch() {
  local branches branch
  branches=$(git branch -a --format='%(refname:short)' | sed 's|^origin/||' | sort -u)
  branch=$(echo "$branches" | fzf --height 40% --reverse) && git checkout "$branch"
}

fkill() {
  local pid
  pid=$(ps -ef | sed 1d | fzf -m | awk '{print $2}')
  [[ -n "$pid" ]] && echo "$pid" | xargs kill -${1:-9}
}

fdocker() {
  local container
  container=$(docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" | sed 1d | fzf --height 40% --reverse | awk '{print $1}')
  [[ -n "$container" ]] && docker exec -it "$container" /bin/bash
}

mkcd() {
  mkdir -p "$1" && cd "$1"
}

fzf-grep() {
  if (( $# == 0 )); then
    echo "用法: fzf-grep <pattern>"
    return 1
  fi
  grep -rn "$1" . --color=always | fzf --height 40% --reverse --ansi
}

calc() {
  echo "$*" | bc -l
}

# ----------------------------- 11. 本地配置加载 ------------------------------
[[ -f ~/.zshrc.local ]] && source ~/.zshrc.local

# ----------------------------- 12. 加载用户环境文件 --------------------------
[[ -f "$HOME/.local/bin/env" ]] && . "$HOME/.local/bin/env"

# ----------------------------- 13. Conda 初始化 ------------------------------
# >>> conda initialize >>>
__conda_setup="$('/home/ywhdzrb/miniconda3/bin/conda' 'shell.zsh' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/home/ywhdzrb/miniconda3/etc/profile.d/conda.sh" ]; then
        . "/home/ywhdzrb/miniconda3/etc/profile.d/conda.sh"
    else
        export PATH="/home/ywhdzrb/miniconda3/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<

# ----------------------------- 14. 启动消息 ---------------------------------
if [[ -n "$ZSH_VERBOSE" ]]; then
  echo "Zsh 配置加载完成。"
  echo "快捷键：Tab 补全，Ctrl+R 历史，Ctrl+T 选择文件(kitten)，Alt+C 跳转目录(kitten)"
fi
export ZSH_VERBOSE=""
export GITHUB_TOKEN="$(gh auth token)"
