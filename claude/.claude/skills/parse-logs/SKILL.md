---
name: parse-logs
description: Parse Snakemake or Slurm logs to find errors and diagnose failures. Invoke when a pipeline job fails, a Snakemake run errors out, or the user needs to understand what went wrong.
argument-hint: "[job ID, rule name, or log file path]"
---

# Parsing Pipeline Logs

## Log locations

| Source | Location |
|--------|----------|
| Per-rule Snakemake logs | `logs/<rulename>.<wildcards>.log` |
| Slurm stdout/stderr | `logs/` (if `--output`/`--error` set there) or `slurm-<jobid>.out` in CWD |
| Snakemake run log | `.snakemake/log/` (YYYY-MM-DDTHHMMSS.snakemake.log) |

## Diagnosing a Snakemake failure

### Step 1 — Find the failing rule
Look for lines containing `Error` or `rule` in the Snakemake run log or terminal output:
```bash
grep -i "error\|exception\|rule\|failed" .snakemake/log/*.log | tail -50
```

### Step 2 — Read the rule's log file
The Snakemake output will say something like:
```
Error in rule my_rule:
    jobid: 42
    output: scratch/foo/bar.txt
    log: logs/my_rule.sampleA.log (check log file(s) for error details)
```
Read that log file directly.

### Step 3 — Check Slurm job details (if cluster job)
```bash
# Get resource usage and exit code
sacct -j <jobid> --format=JobID,State,Elapsed,MaxRSS,ExitCode,CPUTime

# Full details
scontrol show job <jobid>
```

### Common failure patterns

**Out of memory (OOM)**
- Slurm state: `OUT_OF_MEMORY` or `FAILED` with exit code 137
- Fix: increase `mem_mb` in the rule's `resources:` block

**Timeout**
- Slurm state: `TIMEOUT`
- Fix: increase `--time` in the cluster config or rule resources

**Missing input file**
- Snakemake error: `MissingInputException`
- Fix: check that upstream rules completed successfully; look for the file

**Conda env build failure**
- Error during env solving/installation
- Fix: check `code/envs/<env>.yaml` for conflicts; try `conda env create -f` manually

**Command not found**
- Rule's shell command fails with `command not found`
- Fix: the tool isn't in the conda env; add it to the env YAML

**File not found after job completes**
- Snakemake: `MissingOutputException`
- The job ran but didn't produce expected output — look in the rule's log for the actual error

## Searching logs efficiently

```bash
# Find most recent snakemake log
ls -t .snakemake/log/*.log | head -1 | xargs tail -100

# Find all rules that failed in recent run
grep "^Error\|^Exiting" .snakemake/log/*.log

# Find which log files have non-empty content (actual errors)
for f in logs/*.log; do [ -s "$f" ] && echo "$f"; done
```

## When investigating, always

1. Read the full rule log (not just the tail) — errors often have a traceback spanning many lines
2. Check exit code: exit 1 = software error, exit 137 = OOM, exit 143 = SIGTERM/timeout
3. Look at the exact shell command in the rule — use `snakemake -np <target>` to do a dry run and see the expanded command
