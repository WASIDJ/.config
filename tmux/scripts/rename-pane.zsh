#!/bin/zsh -f
# The popup receives the target pane ID before focus moves into the popup.
emulate -L zsh
setopt no_unset
# display-popup does not expand formats in -e or its command arguments.
# run-shell expands the original pane ID before entering this launcher mode.
if [[ ${1-} == --popup ]]; then
    pane_id=${2:?missing pane ID}
    [[ $pane_id == %<-> ]] || exit 1
    accent=$(tmux display-message -p -t "$pane_id" '#{@pane_color}') || exit 1
    foreground=$(tmux show-options -gqv @thm_fg)
    background=$(tmux show-options -gqv @thm_bg)
    [[ $accent =~ '^#[0-9a-fA-F]{6}$' ]] || accent='#89dceb'
    [[ $foreground =~ '^#[0-9a-fA-F]{6}$' ]] || foreground='#cdd6f4'
    [[ $background =~ '^#[0-9a-fA-F]{6}$' ]] || background='#1e1e2e'
    client_args=()
    [[ -n ${3-} ]] && client_args=(-c "$3")
    exec tmux display-popup "${client_args[@]}" -E -t "$pane_id" -w 58 -h 3 -x C -y C -b rounded \
        -s "fg=$foreground,bg=$background" \
        -S "fg=$accent,bg=$background" \
        -e "PANE_RENAME_COLOR=$accent" -T ' pane alias ' \
        /bin/zsh -f "$HOME/.config/tmux/scripts/rename-pane.zsh" "$pane_id"
fi

pane_id=${1:?missing pane ID}
[[ $pane_id == %<-> ]] || exit 1
pane_name=''
accent=${PANE_RENAME_COLOR:-\#89dceb}
[[ $accent =~ '^#[0-9a-fA-F]{6}$' ]] || accent='#89dceb'

# Start with an empty input; cancellation leaves the existing alias unchanged.
KEYTIMEOUT=1
bindkey -e
bindkey '^[' send-break
if ! vared -p '  ' pane_name; then
    exit 0
fi
if [[ -n $pane_name ]]; then
    tmux set-option -p -t "$pane_id" @pane_name "$pane_name"
else
    tmux set-option -pu -t "$pane_id" @pane_name
fi
