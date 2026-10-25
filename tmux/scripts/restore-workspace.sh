#!/usr/bin/env bash
# Restore custom labels first, then resume agents through the installed plugin.
set -euo pipefail
python3 "$HOME/.config/tmux/scripts/persist-pane-options.py" restore
bash "$HOME/.config/tmux/plugins/tmux-assistant-resurrect/scripts/restore-assistant-sessions.sh"
