#!/bin/bash
# codex_remote_control_watchdog.sh
#
# PURPOSE: Keep exactly one Codex remote-control daemon alive across the Midway
# login nodes, so the Codex/ChatGPT iOS app always has a live session to attach
# to. Registered on cron from ~/.profile_local (see that file).
#
# WHY A WATCHDOG: `codex remote-control start` leaves a plain background process
# (codex app-server --remote-control). It is not a managed service, so nothing
# restarts it when it dies — and it does die (observed 2026-07-29: exited after
# "failed to refresh available models: timeout waiting for child process to
# exit"). systemd --user is not an option here: Linger=no, user manager degraded.
#
# WHY IT IS IDEMPOTENT-BY-CONSTRUCTION: `codex remote-control start` is itself
# idempotent — against a healthy daemon it re-reports status, leaves the PID
# untouched, and exits 0. So the healthy path just calls it. That also recovers
# the "process alive but relay connection dead" case, not only hard crashes.
#
# ── WHY ONE NODE, AND WHY STICKY ──────────────────────────────────────────────
# Codex registers the remote environment SERVER-SIDE at enroll time, keyed off
# the hostname the daemon reports; nothing local records the identity (the
# daemon's settings.json is just {"remoteControlEnabled": true}). So a daemon on
# a second node shows up as a SECOND machine in the iOS app, and likely needs
# its own pairing.
#
# The daemon does NOT need to run on the node you are logged into: the phone
# reaches it through OpenAI's relay, and every login node shares the same NFS
# home. One daemon is enough, and one is cheaper — each is ~150 MB RSS on a
# shared login node.
#
# Hence a sticky pin rather than "follow my latest login". SSH round-robins
# across login nodes, so a follow-the-login rule would bounce the daemon between
# nodes (and rename the machine in the app) every time you happened to land
# somewhere else, e.g. with a long-lived tmux on one node and a new shell on
# another.
#
# ── FAILOVER ──────────────────────────────────────────────────────────────────
# Sticky must not mean stranded. The pinned node writes a heartbeat every run.
# Any other node whose cron is registered will, on seeing that heartbeat go
# stale (pinned node down, drained, or rebuilt), claim the pin and start the
# daemon locally. A node that is NOT pinned stops any daemon it finds running,
# which cleans up after a migration and converges a two-node claim race back to
# one daemon. Expect the machine name in the iOS app to change after a failover.
#
# TO RE-PIN MANUALLY (e.g. to move it to the node you are on right now):
#   rm ~/.codex/remote-control-pin        # next run adopts the current host
# or: FORCE_PIN=1 ~/.claude/codex_remote_control_watchdog.sh
#
# LOG: writes only on restarts, pin changes, and errors — silent when healthy,
# and silent on non-pinned nodes (the cron entry is registered on every login
# node, so the quiet path must stay quiet).

# cron gets a minimal PATH, so use an absolute path to codex. Point at the
# standalone install directly rather than the ~/.npm-global/bin/codex symlink:
# remote-control requires the standalone package, and that symlink would be
# clobbered by a future `npm i -g @openai/codex`.
CODEX="${CODEX:-$HOME/.codex/packages/standalone/current/bin/codex}"

# Shared state on NFS so every login node sees it.
PIN_FILE="${PIN_FILE:-$HOME/.codex/remote-control-pin}"
HEARTBEAT_FILE="${HEARTBEAT_FILE:-$HOME/.codex/remote-control-heartbeat}"

# How long the pinned node may go quiet before another node takes over. The
# watchdog runs every 5 min, so this allows 3 missed runs before failover.
STALE_SECS="${STALE_SECS:-900}"

LOG="${LOG:-/tmp/codex_remote_control_watchdog.log}"

# Cap the run: `start` waits for the relay connection before reporting, so a
# network stall could otherwise leave overlapping cron invocations piling up.
TIMEOUT_SECS="${TIMEOUT_SECS:-120}"

HOST="$(hostname)"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') [$HOST] $*" >> "$LOG"; }

daemon_running() {
    pgrep -u "$(id -u)" -f 'app-server --remote-control' >/dev/null 2>&1
}

# Write via temp + mv so a reader on another node never sees a half-written file.
write_atomic() {
    printf '%s\n' "$2" > "$1.tmp.$$" && mv -f "$1.tmp.$$" "$1"
}

if [ ! -x "$CODEX" ]; then
    log "error: codex not executable at $CODEX"
    exit 1
fi

mkdir -p "$(dirname "$PIN_FILE")" 2>/dev/null

PINNED="$(cat "$PIN_FILE" 2>/dev/null)"

if [ "${FORCE_PIN:-0}" = "1" ]; then
    PINNED=""
fi

# ── Decide whether this node should be the one running the daemon ─────────────
if [ -z "$PINNED" ]; then
    # No pin yet (first run, or a manual re-pin) — adopt this host.
    write_atomic "$PIN_FILE" "$HOST"
    log "claimed pin: no previous pin set"
    PINNED="$HOST"

elif [ "$PINNED" != "$HOST" ]; then
    # Someone else owns the pin. Take over only if their heartbeat is stale.
    HB="$(cat "$HEARTBEAT_FILE" 2>/dev/null)"
    NOW="$(date +%s)"

    case "$HB" in
        ''|*[!0-9]*)
            # Unreadable/absent heartbeat (including a transient NFS hiccup).
            # Do nothing rather than risk a spurious takeover.
            exit 0
            ;;
    esac

    AGE=$((NOW - HB))
    if [ "$AGE" -lt "$STALE_SECS" ]; then
        # Pinned node is alive and working. If a daemon is somehow running here
        # too (leftover from a previous pin, or a lost claim race), stop it so
        # only the pinned node's environment exists in the app.
        if daemon_running; then
            log "stopping stray daemon: pin belongs to $PINNED (heartbeat ${AGE}s old)"
            timeout "$TIMEOUT_SECS" "$CODEX" remote-control stop >/dev/null 2>&1
        fi
        exit 0
    fi

    log "taking over pin from $PINNED: heartbeat ${AGE}s old (>= ${STALE_SECS}s)"
    write_atomic "$PIN_FILE" "$HOST"
    PINNED="$HOST"
fi

# ── This node owns the pin: ensure the daemon is up ───────────────────────────

# Was it up before this run? Used only to decide whether to log, so a healthy
# steady state stays silent.
if daemon_running; then WAS_RUNNING=1; else WAS_RUNNING=0; fi

OUT=$(timeout "$TIMEOUT_SECS" "$CODEX" remote-control start 2>&1)
RC=$?

if [ $RC -ne 0 ]; then
    # Auth/MFA failures are permanent until the user re-authenticates, so call
    # them out instead of burying them as a generic failure. Observed form:
    # HTTP 403 {"detail":"Multi-factor authentication required"}
    if echo "$OUT" | grep -qiE 'multi-factor|403 Forbidden|enrollment failed'; then
        log "error: enrollment/auth rejected — re-run 'codex login' and check MFA. Output: $(echo "$OUT" | tr '\n' '|')"
    elif [ $RC -eq 124 ]; then
        log "error: 'remote-control start' timed out after ${TIMEOUT_SECS}s"
    else
        log "error: 'remote-control start' exited $RC. Output: $(echo "$OUT" | tr '\n' '|')"
    fi
    # Deliberately no heartbeat on failure: if this node cannot keep the daemon
    # up, let the heartbeat go stale so another node can take over.
    exit $RC
fi

write_atomic "$HEARTBEAT_FILE" "$(date +%s)"

if [ "$WAS_RUNNING" -eq 0 ]; then
    log "restarted: daemon was down, now $(echo "$OUT" | grep -o 'available for remote control as .*' || echo 'started')"
fi

exit 0
