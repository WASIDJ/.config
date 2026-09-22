# Pi (pi coding agent)
export PATH="/Users/Admin/.local/share/pi-node/node-v22.23.2-darwin-arm64/bin:$PATH"

# Load the current directory's direnv environment before Powerlevel10k captures
# console output. This keeps virtualenv activation compatible with instant prompt.
(( ${+commands[direnv]} )) && emulate zsh -c "$(direnv export zsh)"

# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

# Register direnv's directory-change hook after instant prompt initialization.
(( ${+commands[direnv]} )) && emulate zsh -c "$(direnv hook zsh)"

# If you come from bash you might have to change your $PATH.
export PATH=$HOME/bin:$HOME/.local/bin:/usr/local/bin:$PATH
# Path to your Oh My Zsh installation.
export ZSH="$HOME/.oh-my-zsh"
export PATH="$HOME/bin:$PATH"
# ====== 终端代理（mihomo 混合端口 7890）======
# 启动 shell 时自动检测 mihomo 是否在运行，运行则自动开启终端代理
if nc -z 127.0.0.1 7890 >/dev/null 2>&1; then
  export http_proxy=http://127.0.0.1:7890
  export https_proxy=http://127.0.0.1:7890
  export all_proxy=socks5://127.0.0.1:7890
  export HTTP_PROXY=$http_proxy
  export HTTPS_PROXY=$https_proxy
  export ALL_PROXY=$all_proxy
  # 本地/内网地址不走代理
  export no_proxy=localhost,127.0.0.1,::1,*.local,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16
  export NO_PROXY=$no_proxy
else
  unset http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY no_proxy NO_PROXY
fi

# ====== 禁止 Homebrew 自动更新 ======
export HOMEBREW_NO_AUTO_UPDATE=1

# ====== 设置系统默认编辑器为 nvim ======
export EDITOR='nvim'
export VISUAL='nvim'
export SUDO_EDITOR='nvim'

# ====== nvim 别名配置 ======
# 核心别名：输入 v 直接打开 nvim
alias v='nvim'
# 兼容习惯：输入 vi/vim 也打开 nvim（替代系统默认的 vi/vim）
alias vi='nvim'
alias vim='nvim'

alias vibe='/opt/homebrew/bin/tmux -u -L vibe new -A -s vibe'
# Set name of the theme to load --- if set to "random", it will
# load a random theme each time Oh My Zsh is loaded, in which case,
# to know which specific one was loaded, run: echo $RANDOM_THEME
# See https://github.com/ohmyzsh/ohmyzsh/wiki/Themes
ZSH_THEME="powerlevel10k/powerlevel10k"

# Set list of themes to pick from when loading at random
# Setting this variable when ZSH_THEME=random will cause zsh to load
# a theme from this variable instead of looking in $ZSH/themes/
# If set to an empty array, this variable will have no effect.
# ZSH_THEME_RANDOM_CANDIDATES=( "robbyrussell" "agnoster" )

# Uncomment the following line to use case-sensitive completion.
# CASE_SENSITIVE="true"

# Uncomment the following line to use hyphen-insensitive completion.
# Case-sensitive completion must be off. _ and - will be interchangeable.
# HYPHEN_INSENSITIVE="true"

# Uncomment one of the following lines to change the auto-update behavior
# zstyle ':omz:update' mode disabled  # disable automatic updates
# zstyle ':omz:update' mode auto      # update automatically without asking
# zstyle ':omz:update' mode reminder  # just remind me to update when it's time

# Uncomment the following line to change how often to auto-update (in days).
# zstyle ':omz:update' frequency 13

# Uncomment the following line if pasting URLs and other text is messed up.
# DISABLE_MAGIC_FUNCTIONS="true"

# Uncomment the following line to disable colors in ls.
# DISABLE_LS_COLORS="true"

# Uncomment the following line to disable auto-setting terminal title.
# DISABLE_AUTO_TITLE="true"

# Uncomment the following line to enable command auto-correction.
# ENABLE_CORRECTION="true"

# Uncomment the following line to display red dots whilst waiting for completion.
# You can also set it to another string to have that shown instead of the default red dots.
# e.g. COMPLETION_WAITING_DOTS="%F{yellow}waiting...%f"
# Caution: this setting can cause issues with multiline prompts in zsh < 5.7.1 (see #5765)
# COMPLETION_WAITING_DOTS="true"

# Uncomment the following line if you want to disable marking untracked files
# under VCS as dirty. This makes repository status check for large repositories
# much, much faster.
# DISABLE_UNTRACKED_FILES_DIRTY="true"

# Uncomment the following line if you want to change the command execution time
# stamp shown in the history command output.
# You can set one of the optional three formats:
# "mm/dd/yyyy"|"dd.mm.yyyy"|"yyyy-mm-dd"
# or set a custom format using the strftime function format specifications,
# see 'man strftime' for details.
# HIST_STAMPS="mm/dd/yyyy"

# Would you like to use another custom folder than $ZSH/custom?
# ZSH_CUSTOM=/path/to/new-custom-folder

# Which plugins would you like to load?
# Standard plugins can be found in $ZSH/plugins/
# Custom plugins may be added to $ZSH_CUSTOM/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
# Add wisely, as too many plugins slow down shell startup.
plugins=(
  git
  zsh-autosuggestions
  zsh-syntax-highlighting
  fzf
  sudo
  extract
  )

source $ZSH/oh-my-zsh.sh

# User configuration

# export MANPATH="/usr/local/man:$MANPATH"

# You may need to manually set your language environment
# export LANG=en_US.UTF-8

# Preferred editor for local and remote sessions
# if [[ -n $SSH_CONNECTION ]]; then
#   export EDITOR='vim'
# else
#   export EDITOR='nvim'
# fi

# Compilation flags
# export ARCHFLAGS="-arch $(uname -m)"

# Set personal aliases, overriding those provided by Oh My Zsh libs,
# plugins, and themes. Aliases can be placed here, though Oh My Zsh
# users are encouraged to define aliases within a top-level file in
# the $ZSH_CUSTOM folder, with .zsh extension. Examples:
# - $ZSH_CUSTOM/aliases.zsh
# - $ZSH_CUSTOM/macos.zsh
# For a full list of active aliases, run `alias`.
#
# Example aliases
# alias zshconfig="mate ~/.zshrc"
# alias ohmyzsh="mate ~/.oh-my-zsh"

# To customize prompt, run `p10k configure` or edit ~/.p10k.zsh.
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh

[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

# bun completions
[ -s "/Users/Admin/.bun/_bun" ] && source "/Users/Admin/.bun/_bun"
export PATH="/opt/homebrew/opt/swift/bin:$PATH"
export SWIFT_DRIVER_SWIFTSCAN_LIB="/opt/homebrew/opt/swift/Swift-6.2.xctoolchain/usr/lib/swift/host/lib_InternalSwiftScan.dylib"
export PATH="$HOME/go/bin:$PATH"
export GSETTINGS_SCHEMA_DIR=/opt/homebrew/share/glib-2.0/schemas
boss() {
  env -u ALL_PROXY -u all_proxy \
      -u HTTP_PROXY -u http_proxy \
      -u HTTPS_PROXY -u https_proxy \
      -u NO_PROXY -u no_proxy \
      command boss "$@"
}

alias agy-y='agy --dangerously-skip-permissions'
export PI_CACHE_RETENTION=long

alias aide='antigravity-ide'

ulimit -n 65536

# ====== mihomo 终端代理开关 & 系统级服务管理 ======
# 手动开启终端代理
proxy() {
  export http_proxy=http://127.0.0.1:7890
  export https_proxy=http://127.0.0.1:7890
  export all_proxy=socks5://127.0.0.1:7890
  export HTTP_PROXY=$http_proxy HTTPS_PROXY=$https_proxy ALL_PROXY=$all_proxy
  export no_proxy=localhost,127.0.0.1,::1,*.local,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16
  export NO_PROXY=$no_proxy
  echo "✅ 终端代理已开启: http://127.0.0.1:7890"
}

# 手动关闭终端代理
unproxy() {
  unset http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY no_proxy NO_PROXY
  echo "❌ 终端代理已关闭"
}

# 查看当前终端代理状态
proxystatus() {
  if [[ -n "$http_proxy" ]]; then
    echo "✅ 终端代理: $http_proxy"
  else
    echo "❌ 终端代理: 未开启"
  fi
}

# mihomo 系统级服务管理（root LaunchDaemon，需 sudo）
alias mihomo-restart='sudo launchctl kickstart -k system/com.mihomo.daemon'
alias mihomo-start='sudo launchctl bootstrap system /Library/LaunchDaemons/com.mihomo.daemon.plist'
alias mihomo-stop='sudo launchctl bootout system/com.mihomo.daemon'
alias mihomo-status='sudo launchctl print system/com.mihomo.daemon | grep -E "state|program|working"'
alias mihomo-log='sudo tail -f /var/log/mihomo/mihomo.log'
alias mihomo-edit='nvim ~/.config/mihomo/config.yaml'

# ====== ccimgd —— 剪贴板图片托盘（供远端 Claude Code /paste-image 使用）======
# 必须在 GUI 会话里启动（launchd 后台拿不到剪贴板），所以放在 shell 登录时启。
# 幂等：只有 9998 端口无人监听时才拉起。
if [[ -x "$HOME/.local/bin/ccimgd" ]] && ! lsof -nP -iTCP:9998 -sTCP:LISTEN >/dev/null 2>&1; then
  nohup "$HOME/.local/bin/ccimgd" >/tmp/ccimgd.log 2>&1 &
  disown
fi

# ====== Claude Code 快捷键 ======
alias c='claude'                                  # 启动 Claude Code
alias cy='claude --dangerously-skip-permissions'  # 跳过权限确认（YOLO 模式）
alias cr='claude --resume'                        # 恢复上次会话（可交互选择）
alias cc='claude --continue'                      # 直接继续最近一次会话
alias cu='claude update'                          # 升级 Claude Code
export PATH="$HOME/development/flutter/bin:$PATH"
export PUB_HOSTED_URL=https://pub.flutter-io.cn
export FLUTTER_STORAGE_BASE_URL=https://storage.flutter-io.cn
export ZHIHU_ACCESS_SECRET="93f2b93879cc5d01b5d0c639572f8af3862f2bd7"

# TypeSafe / Jev decision API (pi-jev extension)
export TYPESAFE_API_KEY="apikey_271295d566ea1e0482ea45336b1c7dc4882_4f0e359565eec0bd6b6319f06c476ce74d7b250f5e4c67252799ebb4385458f4"
