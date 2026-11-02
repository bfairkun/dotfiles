---
name: compute-kernel
description: "RCC Midway or UMich Great Lakes HPC. Connect to a Jupyter kernel running on an HPC compute node. Invoke when the user says \"connect to compute kernel\" or \"connect to compute R kernel\", or when a login-node kernel is killed due to memory limits."
---

# Compute Node Kernel Workflow

Machine-specific paths and account are in `AGENTS.local.md`.

Before starting a new kernel, reconnect to the session's existing connection file if its job
is still alive. Use a task-specific file when another session may have a live kernel.
For an existing notebook, first read [render resource metadata](references/rendering.md) to
size the allocation. Login-node memory is shared across the whole user; see machine limits
in `AGENTS.local.md`. For OOM symptoms, connection failures, or a dead kernel, use
[diagnosis and recovery](references/recovery.md).

## Starting a kernel

**The agent can start kernels directly — do not ask the user to run `start_agent_kernel`.**

For **login-node** work (low memory, short tasks), call `start_kernel`:
```python
# start_kernel(kernel_name="py_general")
```
This starts a child process of the MCP server. It is killed when the server restarts, so
prefer compute kernels for long sessions or memory-heavy notebooks.

For **compute-node** work (large data, long runs, or anything that was OOM-killed on login):
use `start_agent_kernel` (`~/bin/`, wrapping `agent_kernel.sbatch`) when its default connection
file is unused. It handles IP binding and partition detection.

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
- Connection file written to `$SCRATCH/$USER/` if scratch is available, else `~/` (see AGENTS.local.md)
- Job log: same dir as connection file, `agent_kernel.log`
- To cancel: `scancel <jobid>`
- `my_accounts` fails non-interactively; use `sacctmgr show user $USER withassoc format=account -P`
- The `jupyter-kernel` MCP config must NOT have `--latest` in its args

## User connecting to the kernel themselves

```bash
conda activate py_general
jupyter console --existing <connection-file from this session>
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
