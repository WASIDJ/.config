# Pi Coding Agent Configuration

> Pi config files synced from `~/.pi/agent/` (API keys redacted).

## Files

| File | Source | Description |
| ------ | -------- | ------------- |
| `settings.json` | `~/.pi/agent/settings.json` | Global settings: theme, TUI mode, default provider/model, installed packages |
| `keybindings.json` | `~/.pi/agent/keybindings.json` | Custom keyboard shortcuts |
| `models.json` | `~/.pi/agent/models.json` | Provider & model definitions (**apiKey redacted** → `{{ secrets.PI_<NAME>_API_KEY }}`) |
| `jev.json` | `~/.pi/agent/jev.json` | Jev routing config (cheap/strong model routing, compaction) |
| `subagent.json` | `~/.pi/subagent.json` | Subagent Jev routing: candidate models (**apiKey redacted** → `{{ secrets.JEV_ROUTING_API_KEY }}`) |
| `web-search.json` | `~/.pi/web-search.json` | Web search settings |
| `PACKAGES.md` | `pi list` output | Installed package manifest (reinstall with `pi install <source>`) |
| `skills/` | `~/.pi/agent/skills/` | Custom/local skills (non-package, non-symlinked) |

## Restore on a new machine

```bash
# 1. Install pi
npm install -g --ignore-scripts @earendil-works/pi-coding-agent

# 2. Copy config
cp -R ~/.dotfiles/pi/* ~/.pi/agent/
cp ~/.dotfiles/pi/subagent.json ~/.pi/subagent.json
cp ~/.dotfiles/pi/web-search.json ~/.pi/web-search.json

# 3. Restore API keys into models.json and subagent.json manually

# 4. Install packages
pi install npm:pi-web-access
pi install npm:pi-lens
pi install npm:pi-mcp-adapter
pi install npm:@narumitw/pi-plan-mode
pi install npm:pi-root-grant
pi install npm:@xzzpig/pi-permission-system
pi install npm:pi-zhihu-search
pi install npm:@alexlikevibe/pi-jev
pi install npm:@cr1ms0n/pi-subagent
# Local package (clone manually):
# git clone https://github.com/WASIDJ/pi-anki-flash ~/workspace/pi-anki-flash
# pi install ~/workspace/pi-anki-flash
```

## Notes

- **Sessions** (`~/.pi/agent/sessions/`) are NOT synced — too large and machine-local.
- **auth.json** (`~/.pi/agent/auth.json`) is NOT synced — contains login tokens.
- **npm/** (node_modules) is NOT synced — reinstalled via `pi list`.
- `models-store.json`, `mcp-cache.json` are auto-generated caches, not synced.
