## How to resume into an existing tmux window

First check if the window already exists:
```bash
tmux list-windows -F "#{window_index}: #{window_name}"
```

### Case 1 — Window does not exist
Follow [open a session](../SKILL.md#how-to-open-a-session-for-a-project-directory).

### Case 2 — Window exists, check pane state
```bash
tmux list-panes -t <IDX> -F "#{pane_index}: #{pane_current_command}"
```

**Sub-case 2a — Two panes, bottom pane is running `claude` or `codex`:**
Session is already active. Tell the user and ask what they want to do.

**Sub-case 2b — Two panes, bottom pane is a shell (exited):**
```bash
tmux send-keys -t "<IDX>.2" "claude -r <session-id>" Enter
tmux set-option -t <IDX> -w @claude_session_id "<session-id>"
tmux set-option -t <IDX> -w @claude_account "personal"   # or "enterprise" — match whichever config dir you used
```
(Use `codex` instead if that was the original tool — codex has no account tagging.) Then [capture output](../SKILL.md#step-g--wait-and-capture-output).

**Sub-case 2c — Only one pane (no bottom pane yet):**
```bash
tmux split-window -v -t <IDX> -c "/path/to/project"
tmux list-panes -t <IDX> -F "#{pane_index}: #{pane_current_command}"
tmux send-keys -t "<IDX>.2" "claude -r <session-id>" Enter
tmux set-option -t <IDX> -w @claude_session_id "<session-id>"
tmux set-option -t <IDX> -w @claude_account "personal"   # or "enterprise"
```
Then [capture output](../SKILL.md#step-g--wait-and-capture-output).

---
