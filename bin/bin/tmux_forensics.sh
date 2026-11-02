#!/bin/bash
# tmux_forensics.sh
#
# PURPOSE: Find out why long-lived tmux sessions (and the Claude sessions inside
# them) keep dying on the RCC login nodes.
#
# The known cause as of 2026-08-12 is unplanned login-node reboots: midway3-login4
# rebooted three times over 10-11 Aug 2026 with NO shutdown records, after a
# 7-day uptime. A reboot takes the tmux server with it. But "the node rebooted"
# and "something killed my tmux while the node stayed up" look identical after
# the fact — you just log in and your session is gone. This script tells them
# apart by recording the tmux server's identity and the node's boot time on every
# tick, so a death can be attributed rather than guessed at.
#
# WHAT IT RECORDS
#   Every run appends one TICK line (tab-separated, greppable) with:
#     boot time, tmux server pid + start time, session/window counts,
#     load, free memory, and the number of active logins.
#   When the tmux server's PID changes or vanishes, it writes a DEATH block
#   naming the verdict:
#     REBOOT          — boot time moved; the node restarted under us
#     KILLED_WHILE_UP — node never rebooted, so something killed the server.
#                       This is the interesting case: check the OOM/journal
#                       details captured alongside it.
#     STARTED         — first sighting, or a fresh server after a clean gap
#
# USAGE
#   Registered automatically by ~/.profile_local on every login node you log
#   into (crontab lives on node-local /var, so each node needs its own entry):
#     4-59/5 * * * * $HOME/bin/tmux_forensics.sh
#   Read the results with:
#     tmux_forensics.sh --report
#
# The log is per-node ($HOME is shared across login nodes, so a single shared
# file would interleave four nodes' timelines into nonsense).

export PATH="/software/tmux-3.2a-el8-x86_64/bin:/home/bjf79/.local/bin:$PATH"
export LD_LIBRARY_PATH="/software/libevent-2.1.12-el8-x86_64/lib:${LD_LIBRARY_PATH:-}"

NODE="$(hostname -s)"
TMUX_SESSION="${TMUX_SESSION:-ssh_tmux}"
LOG="${LOG:-$HOME/.local/state/watchdogs/tmux_forensics.${NODE}.log}"
STATE="${STATE:-$HOME/.local/state/watchdogs/tmux_forensics.${NODE}.state}"

mkdir -p "$(dirname "$LOG")"

now()  { date '+%Y-%m-%d %H:%M:%S'; }
say()  { echo "$(now)	$*" >> "$LOG"; }

# ── Report mode ───────────────────────────────────────────────────────────────
if [ "$1" = "--report" ]; then
    echo "=== tmux forensics: $NODE ==="
    echo "log: $LOG"
    [ -f "$LOG" ] || { echo "(no log yet — is the cron entry installed on this node?)"; exit 0; }
    echo
    echo "--- deaths and restarts ---"
    grep -E 'DEATH|STARTED|VERDICT' "$LOG" | tail -40
    echo
    echo "--- current ---"
    tail -1 "$LOG"
    echo
    echo "--- tick coverage ---"
    printf 'ticks: %s   first: %s   last: %s\n' \
        "$(grep -c TICK "$LOG")" \
        "$(grep TICK "$LOG" | head -1 | cut -f1)" \
        "$(grep TICK "$LOG" | tail -1 | cut -f1)"
    exit 0
fi

# ── Collect current state ─────────────────────────────────────────────────────
# Boot time as an epoch. Read /proc/stat's btime, NOT systime()-/proc/uptime:
# the latter jitters by +-1s between runs, which would make a same-boot
# comparison look like a reboot and mislabel the one verdict we actually care
# about (KILLED_WHILE_UP) as a boring REBOOT. Also immune to the timezone
# disagreement between `date`, `who -b` and wtmp.
BOOT_EPOCH=$(awk '/^btime/{print $2}' /proc/stat)
[ -z "$BOOT_EPOCH" ] && BOOT_EPOCH=$(awk '{printf "%d", systime()-$1}' /proc/uptime)
BOOT_HUMAN=$(date -d "@$BOOT_EPOCH" '+%Y-%m-%d %H:%M:%S')

# The tmux SERVER is the tmux process reparented to init (PPID 1). The attached
# client has the same argv, so matching on the command name alone picks the
# wrong process — that mistake is why `ps -C tmux` looked empty during the
# original investigation.
SRV_PID=$(ps -u "$USER" -o pid=,ppid=,args= 2>/dev/null \
          | awk '$2==1 && $3 ~ /(^|\/)tmux$/ {print $1; exit}')
if [ -z "$SRV_PID" ]; then
    # Fall back to asking tmux itself, then resolve to the PPID-1 process.
    SRV_PID=$(tmux display-message -p '#{pid}' 2>/dev/null)
    case "$SRV_PID" in ''|*[!0-9]*) SRV_PID="" ;; esac
fi

if [ -n "$SRV_PID" ] && [ -d "/proc/$SRV_PID" ]; then
    SRV_START=$(ps -o lstart= -p "$SRV_PID" 2>/dev/null | sed 's/^ *//')
    SRV_RSS=$(ps -o rss= -p "$SRV_PID" 2>/dev/null | tr -d ' ')
    SESSIONS=$(tmux list-sessions -F '#{session_name}:#{session_windows}w' 2>/dev/null | tr '\n' ',' | sed 's/,$//')
    NWIN=$(tmux list-windows -t "$TMUX_SESSION" -F '#{window_name}' 2>/dev/null | tr '\n' ',' | sed 's/,$//')
else
    SRV_PID=""
    SRV_START=""
    SRV_RSS=""
    SESSIONS=""
    NWIN=""
fi

LOAD=$(cut -d' ' -f1-3 /proc/loadavg)
MEMAVAIL=$(awk '/MemAvailable/{printf "%dM", $2/1024}' /proc/meminfo)
LOGINS=$(who 2>/dev/null | grep -c "^$USER")

# ── Compare against last tick ─────────────────────────────────────────────────
PREV_PID=""; PREV_BOOT=""; PREV_SEEN=""
if [ -f "$STATE" ]; then
    # shellcheck disable=SC1090
    . "$STATE" 2>/dev/null
    PREV_PID="$LAST_SRV_PID"; PREV_BOOT="$LAST_BOOT_EPOCH"; PREV_SEEN="$LAST_SEEN"
fi

verdict=""
if [ -n "$PREV_PID" ] && [ "$PREV_PID" != "$SRV_PID" ]; then
    # The server we were watching is no longer the server.
    # Tolerance, on top of using the stable btime: only a boot-time shift of
    # more than a minute counts as a reboot. Anything smaller is clock noise,
    # and treating it as a reboot would mask a real kill.
    boot_delta=$((BOOT_EPOCH - ${PREV_BOOT:-BOOT_EPOCH}))
    [ "$boot_delta" -lt 0 ] && boot_delta=$(( -boot_delta ))
    if [ -n "$PREV_BOOT" ] && [ "$boot_delta" -gt 60 ]; then
        verdict="REBOOT"
    else
        verdict="KILLED_WHILE_UP"
    fi
elif [ -z "$PREV_PID" ] && [ -n "$SRV_PID" ]; then
    verdict="STARTED"
fi

if [ -n "$verdict" ]; then
    {
        echo "$(now)	DEATH	================================================================"
        echo "$(now)	DEATH	VERDICT=$verdict node=$NODE"
        echo "$(now)	DEATH	prev_server_pid=${PREV_PID:-none} last_seen_alive=${PREV_SEEN:-never}"
        echo "$(now)	DEATH	now_server_pid=${SRV_PID:-NONE} started=${SRV_START:-n/a}"
        echo "$(now)	DEATH	boot_prev=${PREV_BOOT:-?} boot_now=$BOOT_EPOCH ($BOOT_HUMAN)"
        echo "$(now)	DEATH	uptime=$(uptime -p 2>/dev/null) load=$LOAD memavail=$MEMAVAIL"
    } >> "$LOG"

    if [ "$verdict" = "KILLED_WHILE_UP" ]; then
        # The node stayed up, so something actively killed it. Grab whatever
        # evidence this unprivileged account can actually read.
        {
            echo "$(now)	DEATH	--- node did NOT reboot; collecting kill evidence ---"
            echo "$(now)	DEATH	oom(dmesg): $(dmesg 2>/dev/null | grep -iE 'killed process|out of memory' | tail -3 | tr '\n' '|')"
            echo "$(now)	DEATH	journal:    $(journalctl --user -n 20 --no-pager 2>/dev/null | grep -iE 'kill|term|oom|session' | tail -5 | tr '\n' '|')"
            echo "$(now)	DEATH	logind:     $(loginctl show-user "$USER" 2>/dev/null | grep -iE 'linger|state' | tr '\n' '|')"
            echo "$(now)	DEATH	recent_logouts: $(last -n 5 -F "$USER" 2>/dev/null | head -5 | tr '\n' '|')"
        } >> "$LOG"
    fi
fi

# ── Append the tick ───────────────────────────────────────────────────────────
say "TICK	node=$NODE	boot=$BOOT_HUMAN	srv_pid=${SRV_PID:-NONE}	srv_start=${SRV_START:-n/a}	rss=${SRV_RSS:-0}	sessions=${SESSIONS:-none}	windows=${NWIN:-none}	load=$LOAD	memavail=$MEMAVAIL	logins=$LOGINS"

cat > "$STATE" <<EOF
LAST_SRV_PID='$SRV_PID'
LAST_BOOT_EPOCH='$BOOT_EPOCH'
LAST_SEEN='$(now)'
EOF
