# .config — WASIDJ 的 macOS dotfiles

个人 macOS 环境配置仓库（zsh / tmux / ghostty / nvim / yazi 等）。本地路径为 `~/.dotfiles`，通过符号链接挂载到 `$HOME`。

## 目录结构

| 路径 | 说明 |
| --- | --- |
| `zshrc` | Zsh 主配置，`~/.zshrc -> ~/.dotfiles/zshrc` |
| `p10k.zsh` | Powerlevel10k 主题配置 |
| `tmux/` | tmux 配置与脚本（含 Codex 额度状态栏脚本） |
| `ghostty/` | Ghostty 终端配置 |
| `nvim/` | Neovim 配置 |
| `yazi/` | Yazi 文件管理器配置 |
| `git/` | Git 配置 |
| `gh/` | GitHub CLI 配置 |
| `fcitx5/` | Fcitx5 输入法配置（macOS 前端） |
| `htop/`、`raycast/`、`nicotine/`、`opencode/` | 其他工具配置 |

## 安装 / 迁移到新机器

```bash
git clone https://github.com/WASIDJ/.config ~/.dotfiles
ln -sf ~/.dotfiles/zshrc ~/.zshrc
# tmux 配置按需链接：
mkdir -p ~/.config/tmux
ln -sf ~/.dotfiles/tmux/tmux.conf ~/.config/tmux/tmux.conf  # 或 ~/.tmux.conf
```

> 仓库内脚本路径有的写死了 `$HOME`，迁移后以当前用户为准。

## Ghostty 光标拖尾

启用 Neovide 风格的 Cursor Warp，使用方块光标和 150ms 渐淡拖尾。Shader 来自 [sahaj-b/cursor-shaders](https://github.com/sahaj-b/cursor-shaders)，来源版本和 MIT 许可证保存在 `ghostty/shaders/cursor-shaders/`。

迁移时将 `ghostty/` 整体同步到 `~/.config/ghostty/`，保留 `config` 与 `shaders/` 的相对位置；重载配置使用 `⌘⇧,`。

## tmux 对话浏览、复制与网址

前缀为 `Ctrl+q`，复制模式使用 vi 按键。网址打开适用于 macOS，需要 Python 3.9+；已在 tmux 3.6a 验证。

| 按键 | 操作 |
| --- | --- |
| `Ctrl+q [` | 进入复制模式，浏览对话历史 |
| `Ctrl+q f` | 直接进入复制模式并向上查找网址 |
| `f`（复制模式） | 自动定位网址并高亮匹配，代替原单字符跳转 |
| `n` / `N` | 沿当前搜索方向 / 反方向切换匹配 |
| `/` / `?` | 向下 / 向上搜索文字，按 Enter 确认 |
| `Enter`（无选区） | 用默认浏览器打开当前超链接、网址或当前行唯一的网址 |
| `v` / `V`，然后 `y` 或 `Enter` | 按字符 / 按行选择，复制并退出 |
| `q` | 退出复制模式，回到 agent 输入框 |

最快打开网址：`Ctrl+q f → n/N 选择 → Enter`。通过 `/` 或 `?` 搜索时，第一个 Enter 确认搜索，再按 Enter 打开。选中了文字时，Enter 仍执行复制。

## 高频 shell 快捷键（zshrc）

### Claude Code

| 别名 | 命令 | 说明 |
| --- | --- | --- |
| `c` | `claude` | 启动 Claude Code（如提示未安装见下文） |
| `cy` | `claude --dangerously-skip-permissions` | 跳过权限确认（YOLO） |
| `cr` | `claude --resume` | 恢复历史会话（交互选择） |
| `cc` | `claude --continue` | 继续最近一次会话 |
| `cu` | `claude update` | 升级 Claude Code |

Claude Code 缺失时安装：`curl -fsSL https://claude.ai/install.sh | bash`
（官方一键脚本会安装到 `~/.local/bin/claude`）。无网络时可参考本机 backup：`~/Library/Mobile Documents/com~apple~CloudDocs/backup/npm-global/INSTALL.md`。

### 其他

| 别名 | 说明 |
| --- | --- |
| `agy-y` | `agy --dangerously-skip-permissions`（待 agy CLI 安装后可用） |
| `aide` | `antigravity-ide`（待 antigravity 安装后可用） |
| `proxy` / `unproxy` / `proxystatus` | mihomo 终端代理开/关/状态 |
| `mihomo-*` | mihomo 系统服务管理（restart/start/stop/status/log/edit） |

`boss()` 函数：剥离代理环境变量后执行 `boss`，避免走代理。

## 维护约定

- 改完配置直接 `git add -A && git commit && git push` 同步；远端为 `github.com/WASIDJ/.config`（经 ghfast.top 代理）。
- `zshrc` 里网络工具路径多为绝对路径，注意区分 macOS（`Admin`）与远端 Linux（`root`）环境。
- ccimgd：shell 登录时幂等启动的剪贴板图片托盘（127.0.0.1:9998），供远端 Claude Code `/paste-image` 走 SSH RemoteForward 使用。

## 给 AI agent 的说明

- 修改 zshrc 别名时保持「中文注释 + `alias x='...'`」风格，分区用 `====== 标题 ======` 注释块。
- 不要把含 token/密钥的文件（如 `gh/hosts.yml`）提交到公开远端；本仓库 `.gitignore` 已处理敏感项，新增敏感配置前请确认已被忽略。
- 提交的 commit message 用约定式格式（如 `feat(zsh): ...`、`fix(tmux): ...`）。
