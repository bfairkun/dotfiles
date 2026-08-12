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
#   3. Capture the bottom of the pane (the status bar) and read Claude Code's
#      Remote Control indicator. As of Claude Code 2.1.228 that indicator is
#      rendered as one of:
#          "/rc"             — healthy (the "/rc active" label is shortened)
#          "/rc active"      — healthy (unshortened variant)
#          "/rc reconnecting" — RC dropped, trying to come back
#          "/rc connecting…"  — still starting up (transient at launch)
#          "/rc failed"       — RC errored out
#      ...or absent entirely, which means RC never attached to this session.
#      Anything other than healthy counts as a strike.
#   4. Require TWO consecutive strikes before restarting. RC is briefly
#      "connecting"/absent on every launch, so a single bad reading would kill
#      sessions mid-boot. Strikes are tracked in $STATE between cron runs.
#   5. On restart: respawn the window in place, then poll until the workspace
#      trust prompt appears (it always does, even for named sessions) and
#      auto-accept it.
#
# NOTE ON STRING DRIFT: this check depends on strings Claude Code renders, and
# they do change between versions. The previous version of this script grepped
# for "Remote Control reconnecting", which silently stopped matching anything —
# the health check was a no-op for months. If RC starts dying without restarts,
# re-check the labels with:
#   grep -aoE '"/rc [a-z]+"' "$(readlink -f "$(command -v claude)")"
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

# Where to write restart/error events. Successes are silent unless DEBUG=1.
#
# Under $HOME (shared across login nodes) with a per-node filename, so you can
# read every node's history from wherever you happen to land. The old location
# was /tmp, which is node-local and invisible from the other three midway3
# login nodes.
NODE="$(hostname -s)"
LOGDIR="${LOGDIR:-$HOME/.local/state/watchdogs}"
mkdir -p "$LOGDIR"
LOG="${LOG:-$LOGDIR/dispatcher_watchdog.${NODE}.log}"

# Set DEBUG=1 to also log every healthy check. Off by default — logging the
# healthy path on a 5-minute cron grew this log to several MB.
DEBUG="${DEBUG:-0}"

# Tracks consecutive unhealthy readings so a transient blip doesn't kill a
# working session. Reset to 0 on every healthy check. Per-node: each node runs
# its own dispatcher and needs its own strike counter.
STATE="${STATE:-$LOGDIR/dispatcher_watchdog.${NODE}.state}"

# How many consecutive bad readings before we restart (5 min apart via cron).
STRIKES_BEFORE_RESTART="${STRIKES_BEFORE_RESTART:-2}"

# How many lines from the bottom of the pane to scan for the RC indicator.
# The status bar occupies the last ~5 lines; extra margin covers wrapping of
# the custom statusline on narrow panes. Keep this small so conversation text
# that happens to mention "/rc" can't be mistaken for the indicator.
STATUS_LINES="${STATUS_LINES:-10}"

# Claude session name (the -n value), which is what makes a restart RESUME the
# prior conversation instead of starting a blank one.
#
# It must be per-node. $HOME is shared across every RCC login node (midway2, and
# midway3-login1..4), so a bare "-n dispatcher" means every node's watchdog
# fights over one conversation — each restart yanks it to a different node.
# Suffixing with the short hostname gives each node its own durable dispatcher.
# This also matches what the `dispatch` skill tells you to type by hand; the two
# used to disagree, so a watchdog restart silently resumed a DIFFERENT
# conversation than the one you started.
CLAUDE_SESSION="${CLAUDE_SESSION:-dispatcher-$(hostname -s)}"

# The claude command to run when spawning/restarting.
# Override this if you want a different agent or flags.
CLAUDE_CMD="${CLAUDE_CMD:-/home/bjf79/.local/bin/claude --agent dispatcher -n ${CLAUDE_SESSION} --allow-dangerously-skip-permissions}"

# Recreate the tmux session itself if it's gone (e.g. after a login-node
# reboot), rather than giving up until you next log in by hand. Set to 0 to
# restore the old bail-out behaviour.
CREATE_SESSION="${CREATE_SESSION:-1}"

# ── END CONFIG ────────────────────────────────────────────────────────────────

# Wait for the workspace trust prompt and accept it. Factored out so both the
# "window missing" and "restart in place" paths use identical handling.
accept_trust_prompt() {
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

# Create the window from scratch. Only for the "window doesn't exist" case.
spawn_window() {
    tmux new-window -t "${TMUX_SESSION}" -n "$WINDOW" -c "$WORKDIR" "$CLAUDE_CMD"
    accept_trust_prompt
}

# Restart Claude in the EXISTING window. Uses respawn-window rather than
# kill-window + new-window on purpose: killing the last window in a session
# destroys the session itself, and Step 1 then bails out forever — the watchdog
# could never recover. respawn-window keeps the window (and its name/index) and
# just replaces the dead command.
restart_window() {
    tmux respawn-window -k -t "${TMUX_SESSION}:${WINDOW}" -c "$WORKDIR" "$CLAUDE_CMD"
    accept_trust_prompt
}

# Marker proving this node is one you actually use: written on every tick where
# a real tmux session is present. Without it, cron on a login node you never
# touch would happily stand up its own tmux + dispatcher, so all four midway3
# nodes would run a Claude session against your rate limit. Auto-recovery is
# only wanted on nodes that had a session in the first place.
INUSE_MARKER="$LOGDIR/dispatcher_watchdog.${NODE}.inuse"

# --- Step 1: make sure the tmux session exists ---
# The login nodes reboot without warning (three unplanned reboots on
# midway3-login4 over 10-11 Aug 2026, with no shutdown records), which takes the
# whole tmux server with it. Previously this bailed out, so the dispatcher
# stayed dead until the next manual login. Recreate it detached instead — but
# only on a node we've previously seen you using.
if ! tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
    if [ "$CREATE_SESSION" != "1" ] || [ ! -f "$INUSE_MARKER" ]; then
        exit 0
    fi
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$WINDOW] tmux session '$TMUX_SESSION' gone (node booted $(uptime -s 2>/dev/null)) — recreating detached" >> "$LOG"
    # Window 1 is a plain shell, matching the layout the dispatch skill expects.
    tmux new-session -d -s "$TMUX_SESSION" -n zsh -c "$WORKDIR" 2>>"$LOG" || {
        echo "$(date '+%Y-%m-%d %H:%M:%S') [$WINDOW] ERROR: could not create tmux session" >> "$LOG"
        exit 1
    }
    echo 0 > "$STATE"
else
    # A session is live here, so this node counts as in use.
    touch "$INUSE_MARKER"
fi

# --- Step 2: if the window is completely missing, spawn it fresh ---
WINDOW_LIST=$(tmux list-windows -t "$TMUX_SESSION" -F "#{window_name}" 2>&1)
if ! echo "$WINDOW_LIST" | grep -q "^${WINDOW}$"; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$WINDOW] window missing — spawning (tmux list-windows output: $(echo "$WINDOW_LIST" | tr '\n' '|'))" >> "$LOG"
    spawn_window
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$WINDOW] spawned" >> "$LOG"
    exit 0
fi

# --- Step 3: read the Remote Control indicator from the status bar ---
# Only scan the bottom of the pane: that's where the indicator lives, and it
# keeps conversation text from matching by accident.
PANE=$(tmux capture-pane -p -t "${TMUX_SESSION}:${WINDOW}" 2>/dev/null)
STATUS=$(echo "$PANE" | tail -n "$STATUS_LINES")

if echo "$STATUS" | grep -qE '/rc (reconnecting|failed|connecting)'; then
    RC_STATE="$(echo "$STATUS" | grep -oE '/rc (reconnecting|failed|connecting)[^ ]*' | head -1)"
elif echo "$STATUS" | grep -q '/rc'; then
    RC_STATE="healthy"
else
    # No indicator at all — RC never attached to this session. This is the
    # failure mode where a session simply isn't reachable from the phone.
    RC_STATE="absent"
fi

# --- Step 4: healthy — clear strikes and exit ---
if [ "$RC_STATE" = "healthy" ]; then
    echo 0 > "$STATE"
    if [ "$DEBUG" = "1" ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') [$WINDOW] RC healthy" >> "$LOG"
    fi
    exit 0
fi

# --- Step 5: unhealthy — count a strike, restart only once we hit the limit ---
STRIKES=$(cat "$STATE" 2>/dev/null)
case "$STRIKES" in ''|*[!0-9]*) STRIKES=0 ;; esac
STRIKES=$((STRIKES + 1))
echo "$STRIKES" > "$STATE"

if [ "$STRIKES" -lt "$STRIKES_BEFORE_RESTART" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$WINDOW] RC $RC_STATE (strike $STRIKES/$STRIKES_BEFORE_RESTART) — waiting" >> "$LOG"
    exit 0
fi

# --- Step 6: RC is dead — kill and restart ---
# Respawning with the same -n name in CLAUDE_CMD resumes the prior conversation.
# Log the status region too, so if Claude Code renames these labels again the
# breakage is visible here instead of failing silently.
echo "$(date '+%Y-%m-%d %H:%M:%S') [$WINDOW] RC $RC_STATE after $STRIKES strikes — restarting (status: $(echo "$STATUS" | grep -v '^[[:space:]]*$' | tail -3 | tr '\n' '|'))" >> "$LOG"
restart_window
echo 0 > "$STATE"
echo "$(date '+%Y-%m-%d %H:%M:%S') [$WINDOW] restarted" >> "$LOG"
