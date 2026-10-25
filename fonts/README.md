# Ghostty 字体

与 `ghostty/config` 一起迁移的 TTF 文件：

| 目录 | Ghostty 字体名称 | 内容 |
| --- | --- | --- |
| `jetbrains-mono-nerd-font-mono/` | `JetBrainsMono Nerd Font Mono` | 16 个字重/样式，来自本机安装的 Nerd Fonts 3.5.1 字体包 |
| `shanhai-chaofeng-song/` | `YEFONTShanHaiChaoFengSong` | 山海朝凤宋 Regular |

## 安装到 macOS

从仓库根目录执行：

```bash
mkdir -p "$HOME/Library/Fonts"
cp fonts/jetbrains-mono-nerd-font-mono/*.ttf fonts/shanhai-chaofeng-song/*.ttf "$HOME/Library/Fonts/"
```

安装后重载 Ghostty 配置。中文字符映射在 `ghostty/config` 的 `font-codepoint-map` 中；这两套字体分别用于英文等宽字符、Nerd Font 图标和中文。

## 完整性与版权

`SHA256SUMS` 记录全部 17 个 TTF 的内容哈希。从仓库根目录校验：

```bash
cd fonts
shasum -a 256 -c SHA256SUMS
```

JetBrains Mono 字体内嵌许可为 SIL Open Font License 1.1，许可原文保存在 `jetbrains-mono-nerd-font-mono/OFL.txt`。

山海朝凤宋的内嵌版权信息为深圳仪品信息技术有限公司，内嵌许可文字为“本字体由深圳仪品信息技术有限公司制作 需授权请联系了解授权协议。”，网站为 <https://www.yefont.com/>。该字体不适用 JetBrains Mono 的 OFL 许可；本仓库不另外授予其字体使用权。
