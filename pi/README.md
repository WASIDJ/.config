# Pi Coding Agent Configuration

> Minimalist Pi config synced across `macmini`, `home-edge`, and `ace2pro` from `WASIDJ/.config/pi/` (API keys redacted).

## Files

| File | Source | Description |
| :--- | :--- | :--- |
| `settings.json` | `~/.pi/agent/settings.json` | Global settings: default `engy/kimi-k3.1-pro`, `rose-pine-moon` theme, minimalist cross-platform packages |
| `keybindings.json` | `~/.pi/agent/keybindings.json` | Custom keyboard shortcuts |
| `models.json` | `~/.pi/agent/models.json` | Provider & model definitions (**apiKey redacted** → `{{ secrets.PI_ENGY_API_KEY }}`) |
| `PACKAGES.md` | Package manifest | Minimalist 6-package core list |
| `skills/` | `~/.pi/agent/skills/` | Custom/local skills |

## Restore / Sync on Any Machine

```bash
# 1. Install or update pi
npm install -g @earendil-works/pi-coding-agent@latest

# 2. Copy minimalist settings & keybindings (keep machine-local models.json/auth.json credentials intact)
mkdir -p ~/.pi/agent
cp ~/.config/pi/settings.json ~/.pi/agent/settings.json
cp ~/.config/pi/keybindings.json ~/.pi/agent/keybindings.json

# 3. Install core packages
for pkg in \
  npm:pi-web-access \
  npm:pi-mcp-adapter \
  npm:@upstash/context7-pi \
  npm:@narumitw/pi-plan-mode \
  npm:pi-cache-optimizer \
  npm:pi-rose-pine; do
  pi install "$pkg"
done
```

## Notes

- **Sessions** (`~/.pi/agent/sessions/`), **`auth.json`**, **`models-store.json`**, and **`npm/`** are machine-local and NOT committed.
- Worktree management, subagent orchestration, and browser/devtools are handled by Orca + `orca-fleet-scope`, keeping Pi's plugin set lean and fast across macOS, NixOS, and Android Ubuntu chroot.
