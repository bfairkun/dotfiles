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
