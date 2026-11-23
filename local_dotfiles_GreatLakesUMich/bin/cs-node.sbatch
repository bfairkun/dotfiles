#!/bin/bash
#SBATCH --job-name=cs-node
#SBATCH --partition=standard
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=24:00:00
# Lightweight entry point for agents (greatlakes-node ssh alias). Submitted on demand by
# cs-node-ensure; exits by itself after CS_IDLE_MIN minutes without activity.
# Activity = CPU used by ssh sessions / srun steps in this job, or any running process in
# them other than sshd/ssh-agent (an idle open connection does not keep the job alive).
# Heavy work belongs in separate jobs, which this idle check does not see or affect.

IDLE_MIN=${CS_IDLE_MIN:-30}
CPU_THRESH_US=50000   # >50 ms CPU per minute counts as activity
D=/sys/fs/cgroup/system.slice/slurmstepd.scope/job_$SLURM_JOB_ID
echo "cs-node $SLURM_JOB_ID on $(hostname -s), idle limit ${IDLE_MIN} min"

cpu_us() {  # CPU used by everything except this batch step
    local t=0 v
    for s in "$D"/step_*; do
        [ "${s##*/}" = step_batch ] && continue
        v=$(awk '/^usage_usec/{print $2}' "$s/cpu.stat" 2>/dev/null)
        t=$((t + ${v:-0}))
    done
    echo $t
}
busy_procs() {  # user processes outside this batch step, excluding sshd/ssh-agent
    local n=0 f p c
    for f in $(find "$D" -path "$D/step_batch" -prune -o -name cgroup.procs -print 2>/dev/null); do
        while read -r p; do
            c=$(ps -o user=,comm= -p "$p" 2>/dev/null) || continue
            case "$c" in root*|*sshd|*ssh-agent) ;; *) n=$((n + 1)) ;; esac
        done < "$f"
    done
    echo $n
}

last=$(cpu_us); idle=0
while sleep 60; do
    now=$(cpu_us)
    if [ $((now - last)) -gt $CPU_THRESH_US ] || [ "$(busy_procs)" -gt 0 ]; then idle=0; else idle=$((idle + 1)); fi
    last=$now
    if [ $idle -ge "$IDLE_MIN" ]; then echo "$(date '+%F %T') idle ${IDLE_MIN} min, exiting"; exit 0; fi
done
