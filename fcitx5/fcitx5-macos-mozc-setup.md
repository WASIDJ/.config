# fcitx5-macos: 添加 Mozc 日语输入与 Shift 轮转

本文记录本机 fcitx5-macos 配置日语输入法 Mozc 的做法，方便以后复用。

## 目标

- 保留现有 Rime / 雾凇拼音。
- 添加日语输入法 Mozc。
- 让左 Shift 按顺序切换：

```text
keyboard-us -> rime -> mozc -> keyboard-us
```

## 相关路径

用户配置：

```text
~/.config/fcitx5/profile
~/.config/fcitx5/config
~/.config/fcitx5/conf/
```

fcitx5-macos 插件目录：

```text
~/Library/fcitx5
```

Fcitx5 应用：

```text
/Library/Input Methods/Fcitx5.app
```

日志：

```text
/tmp/Fcitx5.log
```

## 安装 Mozc 插件

fcitx5-macos 默认应用包里不一定带 Mozc，需要安装官方插件包。

本机是 Apple Silicon：

```zsh
uname -m
# arm64
```

下载官方 macOS 插件包：

```zsh
curl -L https://github.com/fcitx-contrib/fcitx5-plugins/releases/download/macos-0.3.2/mozc-any.tar.bz2 -o /private/tmp/mozc-any.tar.bz2
curl -L https://github.com/fcitx-contrib/fcitx5-plugins/releases/download/macos-0.3.2/mozc-arm64.tar.bz2 -o /private/tmp/mozc-arm64.tar.bz2
```

解压到用户插件目录：

```zsh
tar -xjf /private/tmp/mozc-any.tar.bz2 -C ~/Library/fcitx5
tar -xjf /private/tmp/mozc-arm64.tar.bz2 -C ~/Library/fcitx5
```

验证文件存在：

```zsh
find ~/Library/fcitx5 -iname '*mozc*' -o -path '*/mozc.conf'
```

应至少看到：

```text
~/Library/fcitx5/plugin/mozc.json
~/Library/fcitx5/lib/fcitx5/libmozc.so
~/Library/fcitx5/share/fcitx5/inputmethod/mozc.conf
~/Library/fcitx5/share/fcitx5/addon/mozc.conf
```

## 配置输入法列表

修改 `~/.config/fcitx5/profile`，保留 `keyboard-us` 和 `rime`，追加 `mozc`：

```ini
[Groups/0]
# Group Name
Name=Default
# Layout
Default Layout=us
# Default Input Method
DefaultIM=rime

[Groups/0/Items/0]
# Name
Name=keyboard-us
# Layout
Layout=

[Groups/0/Items/1]
# Name
Name=rime
# Layout
Layout=

[Groups/0/Items/2]
# Name
Name=mozc
# Layout
Layout=

[GroupOrder]
0=Default
```

注意：`DefaultIM=rime` 保持不变，这样默认仍是雾凇拼音。

## 配置 Shift 轮转

修改 `~/.config/fcitx5/config` 的热键部分。

关键点：

- `AltTriggerKeys` 是“临时切换输入法”，行为是 `EN <-> 上一次输入法`。
- 如果 Shift 仍在 `AltTriggerKeys`，就只能 `EN <-> rime` 或 `EN <-> mozc`，不会轮转。
- 要轮转，必须清空 `AltTriggerKeys`，把 Shift 放到 `EnumerateForwardKeys`。

当前可用配置：

```ini
[Hotkey]
# Toggle Input Method
TriggerKeys=
# Enumerate when holding modifier of Toggle key
EnumerateWithTriggerKeys=True
# Enumerate Input Method Backward
EnumerateBackwardKeys=
# Skip first input method while enumerating
EnumerateSkipFirst=False
# Time limit in milliseconds for triggering modifier key shortcuts
ModifierOnlyKeyTimeout=250

[Hotkey/ActivateKeys]
0=Hangul_Hanja

[Hotkey/DeactivateKeys]
0=Hangul_Romaja

[Hotkey/AltTriggerKeys]

[Hotkey/EnumerateForwardKeys]
0=Shift+Shift_L
```

如果想让右 Shift 也轮转，改为：

```ini
[Hotkey/EnumerateForwardKeys]
0=Shift+Shift_L
1=Shift+Shift_R
```

## 重启 Fcitx5

改配置前最好先停掉 Fcitx5，避免它退出时把旧配置自动保存回来。

```zsh
ps aux | rg '[F]citx5'
kill <PID>
open -a Fcitx5
```

也可以从菜单点 `Restart`，但如果要直接编辑配置文件，推荐先 `kill` 再写文件。

## 排查

查看是否加载 Mozc：

```zsh
tail -n 260 /tmp/Fcitx5.log | rg -i 'mozc|Loaded addon|error|fail'
```

看到类似下面内容表示插件已加载：

```text
Iaddonmanager.cpp:204] Loaded addon mozc
```

如果 Shift 还是只能 `EN <-> 雾凇`，检查 `~/.config/fcitx5/config` 是否又出现：

```ini
[Hotkey/AltTriggerKeys]
0=Shift+Shift_R
1=Shift+Shift_L
```

如果出现，说明 Shift 仍绑定在临时切换上，需要再次清空该 section。
