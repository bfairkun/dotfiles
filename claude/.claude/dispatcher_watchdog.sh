#!/bin/bash
# dispatcher_watchdog.sh
#
# PURPOSE: Keep a Claude session's Remote Control connection alive.
# When Remote Control dies (which happens on a schedule we can't control), this
# script kills and restarts the named tmux window. Because Claude sessions are
# identified by their -n name, restarting with the same "-n <name>" resumes the
# same conversation — no context is lost.
#
# HOW IT WORKS:
#   1. Check that the tmux session exists (bail out if not — nothing we can do)
#   2. Check if the target window exists at all (respawn if missing)
#   3. Capture the pane content and look for "Remote Control reconnecting"
#      in the status bar — that string appears whenever RC has died
#   4. If dead: kill the window, wait briefly, and respawn it. Poll until the
#      workspace trust prompt appears (it always does, even for named sessions)
#      then auto-accept it.
#
# CONFIGURATION:
#   Edit the variables in the CONFIG section below, or override them as
#   environment variables before calling the script, e.g.:
#     TMUX_SESSION=mysession WINDOW=mybot /path/to/dispatcher_watchdog.sh
#
# CRON USAGE:
#   Run every 5 minutes. Add to crontab (crontab -e):
#     */5 * * * * /path/to/dispatcher_watchdog.sh
#
# LOG: Writes to $LOG only on restarts or errors (silent when healthy)

# Ensure we use the same tmux and claude that the user's session uses.
# cron's minimal PATH only has /usr/bin/tmux (2.7), which can't talk to the
# tmux 3.2a server. tmux 3.2a also needs its libevent shared library.
export PATH="/software/tmux-3.2a-el8-x86_64/bin:/home/bjf79/.local/bin:$PATH"
export LD_LIBRARY_PATH="/software/libevent-2.1.12-el8-x86_64/lib:${LD_LIBRARY_PATH:-}"

# ── CONFIG ────────────────────────────────────────────────────────────────────

# Name of the tmux session that contains the Claude window.
# Find yours with: tmux list-sessions
TMUX_SESSION="${TMUX_SESSION:-ssh_tmux}"

# Name of the tmux window running the Claude dispatcher session.
WINDOW="${WINDOW:-dispatcher}"

# Working directory to launch Claude in. Defaults to your home directory.
WORKDIR="${WORKDIR:-$HOME}"

# Where to write restart/error events. Successes are silent.
LOG="${LOG:-/tmp/dispatcher_watchdog.log}"

# The claude command to run when spawning/restarting.
# Override this if you want a different agent, flags, or session name.
CLAUDE_CMD="${CLAUDE_CMD:-/home/bjf79/.local/bin/claude --agent dispatcher -n dispatcher --allow-dangerously-skip-permissions}"

# ── END CONFIG ────────────────────────────────────────────────────────────────

spawn_window() {
    tmux new-window -t "${TMUX_SESSION}" -n "$WINDOW" -c "$WORKDIR" "$CLAUDE_CMD"
    # Wait for the workspace trust prompt ("Is this a project you created or one you
    # trust?") and auto-accept it. This prompt appears on every launch, even when
    # resuming a named session. Poll until we see it rather than sleeping blindly.
    local waited=0
    while [ $waited -lt 60 ]; do
        sleep 3
        waited=$((waited + 3))
        PANE=$(tmux capture-pane -p -t "${TMUX_SESSION}:${WINDOW}" 2>/dev/null)
        if echo "$PANE" | grep -qi "trust"; then
            echo "$(date '+%Y-%m-%d %H:%M:%S') [$WINDOW] trust prompt matched: $(echo "$PANE" | grep -i trust | head -1)" >> "$LOG"
            tmux send-keys -t "${TMUX_SESSION}:${WINDOW}" "" Enter
            return
        fi
    done
    # Timed out — log last pane content for debugging
    PANE=$(tmux capture-pane -p -t "${TMUX_SESSION}:${WINDOW}" 2>/dev/null)
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$WINDOW] warning: trust prompt not seen within 60s. Last pane: $(echo "$PANE" | tail -5 | tr '\n' '|')" >> "$LOG"
}

# --- Step 1: bail if the tmux session doesn't exist ---
# This happens if you're not logged in or tmux hasn't been started yet.
if ! tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
    exit 0
fi

# --- Step 2: if the window is completely missing, spawn it fresh ---
WINDOW_LIST=$(tmux list-windows -t "$TMUX_SESSION" -F "#{window_name}" 2>&1)
if ! echo "$WINDOW_LIST" | grep -q "^${WINDOW}$"; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$WINDOW] window missing — spawning (tmux list-windows output: $(echo "$WINDOW_LIST" | tr '\n' '|'))" >> "$LOG"
    spawn_window
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$WINDOW] spawned" >> "$LOG"
    exit 0
fi

# --- Step 3: check if Remote Control is alive ---
# "Remote Control reconnecting" appears in the Claude status bar when the RC
# connection has dropped. If we don't see it, RC is healthy — exit silently.
PANE=$(tmux capture-pane -p -t "${TMUX_SESSION}:${WINDOW}" 2>/dev/null)

if ! echo "$PANE" | grep -q "Remote Control reconnecting"; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$WINDOW] RC healthy (pane tail: $(echo "$PANE" | tail -2 | tr '\n' '|'))" >> "$LOG"
    exit 0
fi

# --- Step 4: RC is dead — kill and restart ---
# Respawning with the same -n name in CLAUDE_CMD resumes the prior conversation.
echo "$(date '+%Y-%m-%d %H:%M:%S') [$WINDOW] RC dead — restarting" >> "$LOG"
tmux kill-window -t "${TMUX_SESSION}:${WINDOW}"
sleep 3
spawn_window
echo "$(date '+%Y-%m-%d %H:%M:%S') [$WINDOW] restarted" >> "$LOG"
