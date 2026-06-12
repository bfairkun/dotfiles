---
name: compute-kernel
description: "RCC Midway or UMich Great Lakes HPC. Connect to a Jupyter kernel running on an HPC compute node. Invoke when the user says \"connect to compute kernel\" or \"connect to compute R kernel\", or when a login-node kernel is killed due to memory limits."
---

# Compute Node Kernel Workflow

Machine-specific paths and account are in `CLAUDE_local.md → Agent Reference`.

## User's side

```bash
# Python kernel (default)
start_agent_kernel                                      # py_general, 48G, 4h, 4 cpus
start_agent_kernel --mem 64G --time 8:00:00

# Great Lakes — must pass --account (see CLAUDE_local.md → SLURM_ACCOUNT)
start_agent_kernel --account hastingm0

# R kernel
start_agent_kernel --lang r
start_agent_kernel --lang r --account hastingm0         # Great Lakes

# Other options
start_agent_kernel --env my_env --cpus 8
```

Script polls until the kernel is ready, then prints the connection message.

## Agent side — connect and verify

Connection file path is in `CLAUDE_local.md → KERNEL_CF`. Connect with:
```python
# mcp__jupyter-kernel__connect_to_kernel(connection_file="<KERNEL_CF from CLAUDE_local.md>")
```

Verify: `import socket, sys; print(socket.gethostname(), sys.executable)`

## Agent side — R kernel

Same connection file as Python (but `agent_r_kernel.json` variant). Send plain R code via
`mcp__jupyter-kernel__run_python` — the kernel IS R, no `%%R` magic needed:
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

When a `run_python` call fails with a kernel error (e.g. "Kernel died", "RuntimeError: Kernel died before replying"), the compute job has likely ended. Follow these steps:

### Step 1 — Find available autosaves

```bash
ls -lht $SCRATCH/$USER/autosave_*.pkl 2>/dev/null || echo "no autosaves found"
```

Show the list to the user. If the notebook name is already known from earlier in the conversation, identify the matching file directly.

### Step 2 — Start a new compute kernel

Follow the normal kernel startup flow (ask user to run `start_agent_kernel`, then connect).

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

All args pass through to quarto untouched. After a successful render it records the render environment into a hidden `::: {.content-hidden}` block at the end of the `.qmd` (never appears in rendered output, persists in the source). Captured fields include `node_type` (compute/login/local), Slurm `partition`/`mem_allocated`/`cpus_allocated`, and **`peak_rss`** — the *actual* measured peak memory of the render.

Caveats:
- Only renders that go *through* `render_notebook` are tagged — `quarto preview` and IDE render buttons are not.
- `peak_rss` is actual usage; `mem_allocated` is what Slurm granted. Use `peak_rss` to judge the minimum needed.

### Sizing resources when reopening an existing notebook

Before starting a kernel or re-rendering an existing `.qmd`, read its render-env block to pick a sensible allocation:

```bash
grep -A20 "render-env (auto-generated" notebook.qmd
```

Use `peak_rss` (plus headroom) to choose `start_agent_kernel --mem ...`, and `node_type` to know whether it previously needed a compute node at all. If there's no block, the notebook was never rendered through `render_notebook` — fall back to defaults and ask the user.
