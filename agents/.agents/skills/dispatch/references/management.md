## Other operations

For launch variables and required session/account tags, follow
[launch](../SKILL.md#step-f--launch-claude-or-codex-in-the-bottom-pane).

```bash
# List current tmux windows
tmux list-windows -F "#{window_index}: #{window_name} [#{pane_current_command}]"

# Spawn with a specific agent (Step F variant)
tmux send-keys -t "<IDX>.<P>" "claude -n '<window-name>' --agent <agent-name>" Enter

# Close Claude session only (leave window open)
tmux kill-pane -t "<IDX>.2"

# Kill entire window
tmux kill-window -t <IDX>
```

---

## The dispatcher agent

`~/.claude/agents/dispatcher.md` (model: sonnet) is a standalone always-on session for Remote Control use. **Always run this under the personal account (default, no `CLAUDE_CONFIG_DIR` override)** — Remote Control only works for the account that's actually logged in, and the enterprise account doesn't have it enabled.

Start it:
```bash
tmux new-window -n "dispatcher" "claude --agent dispatcher -n \"dispatcher-$(hostname -s)\""
```

Then run `/loop 3m date` inside it to keep Remote Control alive.

**The `-n` name must stay hostname-suffixed.** `$HOME` is shared across the login
nodes but tmux servers are not, so each node needs its own dispatcher
conversation. `~/bin/dispatcher_watchdog.sh` derives the same name and can
restart a dead dispatcher, but is not registered in cron — see `.profile_local`.

**Note:** Custom agents in `~/.claude/agents/` can only be launched with `claude --agent <name>` — not via Claude's internal Agent tool. Dispatching from within a conversation is always done directly via `tmux new-window`.
