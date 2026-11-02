# Kernel troubleshooting

## The login-node memory ceiling is shared across ALL your sessions

On RCC Midway the login node caps the **whole user** — not each process — with a cgroup:

```bash
B=/sys/fs/cgroup/memory/user.slice/user-$(id -u).slice
cat $B/memory.limit_in_bytes      # 8 GiB (verified midway3-login4, 2026-08-12)
cat $B/memory.usage_in_bytes      # what you are using right now
cat $B/memory.max_usage_in_bytes  # high-water mark; == limit means you have hit it
cat $B/memory.failcnt             # times the limit was hit
ps -u $USER -o rss= | awk '{s+=$1} END {printf "%.1f GB / %d procs\n", s/1048576, NR}'
```

Every concurrent agent session shares that 8 GiB: each one runs its own
`jupyter_kernel_mcp.py` server plus any kernels it starts. Several sessions at once can sit at
6–7 GB with no single process looking large, and the next allocation triggers the OOM killer,
which picks a victim *inside the slice* — typically a pandas kernel.

**Symptom is silent.** `run_python` does not report the death. The MCP server transparently
starts a fresh kernel, so the next call fails with a bare `NameError` on a variable that was
defined minutes ago, and the cell counter has reset to `In[1]`. Confirm with:

```bash
ls -la /tmp/tmp*.json          # your old connection file will be GONE
ps -eo pid,lstart,cmd | grep ipykernel_launcher | grep -v grep
```

If `memory.max_usage_in_bytes` is at the limit, the fix is a compute kernel (next section), not
a retry — a retry just re-races the same ceiling. Rebuilding a lost session is cheap only if the
notebook's expensive steps cache to `code/scratch/`, which is another reason to write
intermediates out rather than holding them in the kernel.

## Kernel died recovery

When a `run_python` call fails with a kernel error (e.g. "Kernel died", "RuntimeError: Kernel
died before replying"), the compute job has likely ended. Follow these steps:

If the failure is `Kernel died before replying to kernel_info` on the *first*
`connect_to_kernel` of a brand-new job, it is not a dead job — check `squeue` and the `"ip"`
field of the connection file. A running job with `"ip": "127.0.0.1"` means the kernel bound
loopback and is simply unreachable from the login node; resubmit with the `--ip` bind in [Starting a kernel](../SKILL.md#starting-a-kernel)
rather than restoring an autosave.

### Step 1 — Find available autosaves

```bash
ls -lht $SCRATCH/$USER/autosave_*.pkl 2>/dev/null || echo "no autosaves found"
```

Show the list to the user. If the notebook name is already known from earlier in the conversation, identify the matching file directly.

### Step 2 — Start a new compute kernel

Start one directly (see [Starting a kernel](../SKILL.md#starting-a-kernel)). For compute nodes, submit sbatch
directly or use `start_agent_kernel` via Bash; for login-node recovery use
`start_kernel`. Do not ask the user to do this.

### Step 3 — Inject autosave setup and restore

```python
import sys, os; sys.path.insert(0, os.path.expanduser("~/bin"))
import walltime_autosave

# Restore previous session
walltime_autosave.load(notebook="<notebook_name>")

# Restart the autosave monitor for the new job
SESSION_FILE = walltime_autosave.start(notebook="<notebook_name>")
```

If the notebook name is unknown (e.g. new conversation), show the user the list of `.pkl` files and ask which one to restore. They can also pass `session_file=` explicitly:
```python
walltime_autosave.load(session_file="/path/to/autosave_<notebook_name>.pkl")
```

---
