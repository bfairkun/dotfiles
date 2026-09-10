# Tmux window markers

`tmux-state.py` translates Codex hooks into `~/bin/tmux-agent-state` calls.
Approvals and input tools set red ●; Stop sets green ✔; resumed activity clears
markers. SubagentStop does not mark the parent finished. It emits no hook output
and never records prompts or tool arguments.

Run `~/bin/install-codex-tmux-hooks` after stowing this directory and `bin`.
It merges into the writable `~/.codex/hooks.json`, preserving Orca and other
integrations. Run it again if another application replaces that file. Review the
new hooks in Codex `/hooks`; do not edit trust records manually.

The shared script stores pane state and combines it for window labels; rendering
and the `prefix a` shortcut live in `tmux/.tmux.conf`. Windows show both counts
(e.g. ●2 ✔1); selecting a pane clears only its finished marker. Red persists
until activity resumes. The shortcut selects an attention pane first, then an
unread finished pane, including panes in the current window. These markers are separate
from Agent Bridge's phone push notifications.

Validation: `python3 -m unittest discover -s bin/tests` from the dotfiles root.
