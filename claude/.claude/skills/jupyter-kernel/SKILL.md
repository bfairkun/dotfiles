---
name: jupyter-kernel
description: Setup, installation, and usage of the jupyter-kernel MCP server. Invoke when setting up the MCP on a new machine, troubleshooting connection issues, or explaining what the kernel tools do.
---

# Jupyter Kernel MCP

A lightweight stdio MCP server that lets Claude start, connect to, and execute code in
Jupyter kernels via the Jupyter wire protocol (ZMQ). No HTTP, no open ports.

## Files

The MCP script lives alongside this skill:
`~/.claude/skills/jupyter-kernel/jupyter_kernel_mcp.py`
(stowed from `dotfiles/claude/.claude/skills/jupyter-kernel/`)

## Installation on a new machine

**Prerequisites:** `uv` must be installed:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
`uv` reads the script's inline `# /// script` metadata and installs `jupyter_client`
automatically on first run — no conda env needed.

**Step 1:** Stow the `claude` dotfiles package (brings in skills + script):
```bash
cd ~/dotfiles && stow claude
```

**Step 2:** Symlink the script onto `$PATH`:
```bash
ln -sf ~/.claude/skills/jupyter-kernel/jupyter_kernel_mcp.py ~/bin/jupyter_kernel_mcp.py
```
Verify `~/bin` is on `$PATH`. Claude Code spawns MCP servers without a shell, so `~`
does NOT expand in the MCP config `command` field — PATH resolution is required.

**Step 3:** Register the MCP server:
```bash
claude mcp add --scope user jupyter-kernel jupyter_kernel_mcp.py
```

## Troubleshooting: MCP tools not loading

If `mcp__jupyter-kernel__*` tools are absent from the deferred tools list, the MCP server failed to start. Diagnose in order:

1. **Check the script is reachable:**
   ```bash
   python3 ~/bin/jupyter_kernel_mcp.py --help
   ```
   If `No such file or directory` → the symlink is broken.

2. **Inspect the symlink chain:**
   ```bash
   ls -la ~/bin/jupyter_kernel_mcp.py
   ls -la ~/dotfiles/bin/bin/jupyter_kernel_mcp.py  # if stow-managed
   ```
   A macOS-origin machine may have left an absolute `/Users/bjf79/...` symlink in
   `dotfiles/bin/bin/` that breaks on Linux. Fix with a relative symlink:
   ```bash
   cd ~/dotfiles/bin/bin
   rm jupyter_kernel_mcp.py
   ln -s ../../claude/.claude/skills/jupyter-kernel/jupyter_kernel_mcp.py jupyter_kernel_mcp.py
   ```
   Then commit and restart Claude.

3. **Or bypass stow entirely** with a direct symlink:
   ```bash
   ln -sf ~/.claude/skills/jupyter-kernel/jupyter_kernel_mcp.py ~/bin/jupyter_kernel_mcp.py
   ```

## Tools

| Tool | Purpose |
|---|---|
| `run_code` | Execute code in the active kernel; returns stdout/stderr/result as text (truncated at 8000 chars). |
| `start_kernel` | Start a new kernel by name (e.g. `py_general`, `ir` for R). Returns the connection file path. |
| `connect_to_kernel` | Attach to a running kernel by connection file path. Omit path to attach to the newest kernel (useful for connecting to whichever kernel VS Code has open). |
| `list_kernels` | List all running kernel connection files, newest first. |
| `restart_kernel` | Restart the current kernel, clearing all variables. No-op if attached to an external kernel. |

## Connecting to an existing kernel

To attach Claude to a kernel VS Code or JupyterLab is already running:
1. Call `list_kernels` to find the connection file
2. Call `connect_to_kernel` with that path (or omit path to grab the newest)

## Kernel names

Kernel names correspond to registered kernelspecs:
```bash
jupyter kernelspec list
```

`py_general` is the default Python env. For R, the kernelspec is typically `ir`.
A kernelspec must be registered before use — one-time per machine:
```bash
conda activate py_general && python -m ipykernel install --user --name py_general
```
