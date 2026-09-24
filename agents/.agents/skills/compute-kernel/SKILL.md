---
name: compute-kernel
description: "RCC Midway or UMich Great Lakes HPC. Connect to a Jupyter kernel running on an HPC compute node. Invoke when the user says \"connect to compute kernel\" or \"connect to compute R kernel\", or when a login-node kernel is killed due to memory limits."
---

# Compute Node Kernel Workflow

Machine-specific paths and account are in `AGENTS.local.md → Agent Reference`.

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

## Starting a kernel

**The agent can start kernels directly — do not ask the user to run `start_agent_kernel`.**

For **login-node** work (low memory, short tasks), call `start_kernel`:
```python
# start_kernel(kernel_name="py_general")
```
This starts a child process of the MCP server. It is killed when the server restarts, so
prefer compute kernels for long sessions or memory-heavy notebooks.

For **compute-node** work (large data, long runs, or anything that was OOM-killed on login):
prefer `start_agent_kernel` (in `~/bin/`, wrapping `agent_kernel.sbatch`), which already handles
the two things a hand-rolled `--wrap` gets wrong — the IP bind below and partition detection.
Submit it via Bash yourself; the user does not need to run it.

Write your own `--wrap` only when you need a connection file other than the hardcoded
`agent_kernel.json` (see below), and then copy the bind:

**The kernel must bind the node's routable IP, not loopback.** `ipykernel` defaults to
`127.0.0.1`, and the MCP server runs on the login node, so a loopback-bound kernel is
unreachable even though the job is running normally.

```bash
CF=$SCRATCH/$USER/agent_kernel_<task>.json
rm -f $CF
sbatch --partition=caslake --account=pi-yangili1 --mem=48G --time=4:00:00 --cpus-per-task=4 \
  --job-name=agent_kernel_<task> --output=$SCRATCH/$USER/agent_kernel_<task>.log \
  --wrap="source ~/miniconda3/etc/profile.d/conda.sh && conda activate py_general && \
          HOST_IP=\$(ip route get 8.8.8.8 | awk '{print \$7;exit}') && \
          python -m ipykernel_launcher --ip=\$HOST_IP -f $CF"
```

The `\$` escapes matter: `HOST_IP` must be expanded by the job, not by the submitting shell.
Use `conda activate`, not `conda run` — `conda run` buffers the job's output, so a startup
failure leaves an empty log.

Poll for a *routable* IP, not just the file — `jupyter_client` writes the connection file
before the kernel binds — and give up if the job leaves the queue:
```bash
JOBID=<jobid>
until [ -f $CF ] && ! grep -q '"ip": "127\.' $CF; do
    squeue -h -j $JOBID -o %T | grep -q . || { echo "job gone"; cat $SCRATCH/$USER/agent_kernel_<task>.log; break; }
    sleep 5
done
```
```python
# connect_to_kernel(connection_file="/scratch/midway3/bjf79/agent_kernel_<task>.json")
```

**Use a task-specific connection filename whenever another session may have a kernel live.**
`start_agent_kernel` and `agent_kernel.sbatch` both hardcode `agent_kernel.json`, so reusing it
takes over or clobbers the other session's kernel. Check first:
`ls -lht $SCRATCH/$USER/agent_kernel*.json` and `squeue -u $USER | grep kernel`.

## Killing old kernels

Before starting a new kernel, check for stale ones:
```bash
# List kernel connection files
ls -lht /scratch/midway3/$USER/agent_kernel*.json ~/.local/share/jupyter/runtime/kernel-*.json 2>/dev/null
# Kill the SLURM job if there is one
squeue -u $USER --format="%i %j" | grep agent_kernel  # get job ID
# scancel <jobid>
```
Killing the SLURM job terminates the compute kernel. For MCP-started kernels (login node),
call `start_kernel` again — it replaces the current child process.

## Connect and verify

Verify: `import socket, sys; print(socket.gethostname(), sys.executable)`

## Agent side — R kernel

Same connection file as Python (but `agent_r_kernel.json` variant). Send plain R code via
`run_python` — the kernel is R, so no `%%R` magic is needed:
```r
cat(R.version.string, "\n")
cat("Host:", system("hostname", intern=TRUE), "\n")
```

## Notes

- **Midway**: partition auto-detected from hostname (midway2 → broadwl, midway3 → caslake); no `--account` flag needed in `start_agent_kernel`
- **Great Lakes**: partition `standard`; `--account hastingm0` required
- Connection file written to `$SCRATCH/$USER/` if scratch is available, else `~/` (see CLAUDE_local.md)
- Job log: same dir as connection file, `agent_kernel.log`
- To cancel: `scancel <jobid>`
- `my_accounts` fails non-interactively; use `sacctmgr show user $USER withassoc format=account -P`
- The `jupyter-kernel` MCP config must NOT have `--latest` in its args

## User connecting to the kernel themselves

```bash
conda activate py_general
jupyter console --existing <KERNEL_CF from CLAUDE_local.md>
```

---

## Wall-time autosave (always inject after connecting to a compute kernel)

After connecting and verifying the kernel, always run this boilerplate.
Ask the user what notebook name to use if not obvious from context.

```python
import sys, os; sys.path.insert(0, os.path.expanduser("~/bin"))
import walltime_autosave
SESSION_FILE = walltime_autosave.start(notebook="<notebook_name>")
# default: saves every 30 min + emergency save when <10 min of wall time remain
```

- The session file is `$SCRATCH/$USER/autosave_<notebook_name>.pkl` — keyed by name, not job ID, so it's easy to find when restoring.
- If `dill` is not installed in the env, `start()` warns and is a no-op — the notebook still runs normally.
- Relay the printed session file path to the user.
- `walltime_autosave.save(notebook="<notebook_name>")` can be called manually at any time.

---

## Kernel died recovery

When a `run_python` call fails with a kernel error (e.g. "Kernel died", "RuntimeError: Kernel
died before replying"), the compute job has likely ended. Follow these steps:

If the failure is `Kernel died before replying to kernel_info` on the *first*
`connect_to_kernel` of a brand-new job, it is not a dead job — check `squeue` and the `"ip"`
field of the connection file. A running job with `"ip": "127.0.0.1"` means the kernel bound
loopback and is simply unreachable from the login node; resubmit with the `--ip` bind above
rather than restoring an autosave.

### Step 1 — Find available autosaves

```bash
ls -lht $SCRATCH/$USER/autosave_*.pkl 2>/dev/null || echo "no autosaves found"
```

Show the list to the user. If the notebook name is already known from earlier in the conversation, identify the matching file directly.

### Step 2 — Start a new compute kernel

Start one directly (see "Starting a kernel" section above). For compute nodes, submit sbatch
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

## Rendering notebooks — use `render_notebook`, not `quarto` directly

`render_notebook` (in `~/bin/`) is a transparent shim over the `quarto` CLI. Use it exactly like quarto — just swap the command:

```bash
render_notebook render notebook.qmd
render_notebook render notebook.qmd --to pdf --output-dir out/
```

All args pass through to quarto untouched. After a successful HTML render it records the render environment into a `<!-- render-env:start -->` comment block **in the rendered `.html`**, and strips any stale copy from the `.qmd`. Captured fields include `node_type` (compute/login/local), Slurm `partition`/`mem_allocated`/`cpus_allocated`, and **`peak_rss`** — the *actual* measured peak memory of the render.

Caveats:
- Only renders that go *through* `render_notebook` are tagged — `quarto preview` and IDE render buttons are not.
- HTML output only. A `--to pdf` render prints a notice and writes no block.
- `peak_rss` is actual usage; `mem_allocated` is what Slurm granted. Use `peak_rss` to judge the minimum needed.

### Sizing resources when reopening an existing notebook

Before starting a kernel or re-rendering an existing `.qmd`, read the render-env block from its **last rendered HTML** to pick a sensible allocation:

```bash
grep -A14 "render-env:start" docs/<notebook>.html
```

Use `peak_rss` (plus headroom) to choose `start_agent_kernel --mem ...`, and `node_type` to know whether it previously needed a compute node at all. If there's no block, the notebook was never rendered through `render_notebook` — fall back to defaults and ask the user.

Note that `peak_rss` for a typical analysis notebook is a few hundred MB, i.e. far under the 8 GiB login-node cap on its own. The cap is hit by *accumulation* across concurrent sessions, so a small `peak_rss` is not evidence that login-node rendering is safe when other agents are running.
