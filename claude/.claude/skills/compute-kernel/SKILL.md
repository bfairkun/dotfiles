---
name: compute-kernel
description: Connect to a Jupyter kernel running on an HPC compute node. Invoke when the user says "connect to compute kernel" or "connect to compute R kernel", or when a login-node kernel is killed due to memory limits.
---

# Compute Node Kernel Workflow

Use this when the login node kernel is killed (memory limits) or the user explicitly wants compute resources.

## User's side

```bash
# Python kernel (default)
start_agent_kernel                               # py_general, 48G, 4h, 4 cpus
start_agent_kernel --mem 64G --time 8:00:00

# R kernel
start_agent_kernel --lang r                      # uses system R via py_general env
start_agent_kernel --lang r --mem 64G

# Other options
start_agent_kernel --env my_env --cpus 8
```

Script polls until the kernel is ready, then prints the connection message.

Connection files:
- Python: `$SCRATCH/$USER/agent_kernel.json`
- R: `$SCRATCH/$USER/agent_r_kernel.json`

## Agent side — Python kernel

Use `mcp__jupyter-kernel__connect_to_kernel` with:
`/scratch/midway3/bjf79/agent_kernel.json`

Verify: `import socket, sys; print(socket.gethostname(), sys.executable)`

## Agent side — R kernel

Use `mcp__jupyter-kernel__connect_to_kernel` with:
`/scratch/midway3/bjf79/agent_r_kernel.json`

Then send R code directly via `mcp__jupyter-kernel__run_python` (no `%%R` magic needed —
the kernel IS R, so plain R code works):

```r
cat(R.version.string, "\n")
cat("Hostname:", system("hostname", intern=TRUE), "\n")
```

## Notes

- Partition is auto-detected from login node hostname (midway2 → broadwl, midway3 → caslake)
- IRkernel is in the system R (`/software/R-4.3.1-el8-x86_64`); `py_general` env provides
  `jupyter_client` needed to generate the connection file before handing it to R
- If the job fails to start, check `$SCRATCH/$USER/agent_kernel.log`
- To cancel: `scancel <jobid>` or let it hit the wall time
- The `jupyter-kernel` MCP server in `~/.claude.json` must NOT have `--latest` in its args

## User connecting to the kernel themselves

```bash
conda activate py_general
jupyter console --existing $SCRATCH/$USER/agent_kernel.json      # Python
jupyter console --existing $SCRATCH/$USER/agent_r_kernel.json    # R
```
