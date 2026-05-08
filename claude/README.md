# Claude Code Dotfiles

Configuration and skills for [Claude Code](https://claude.ai/code) (the Anthropic CLI).

Stow this package from the dotfiles root:

```bash
stow -v claude
```

## What's included

```
claude/.claude/
├── CLAUDE.md               # Global instructions loaded into every Claude session
├── mcp.json                # MCP server config (see below — requires one edit)
├── settings.json           # Shared permissions/settings
├── commands/               # Slash commands (/start-kernel, /list-kernels, etc.)
├── skills/                 # Invokable context documents (see Skills section)
└── agents/                 # Custom sub-agent definitions

bin/bin/
└── jupyter_kernel_mcp.py   # Jupyter kernel MCP server (stowed from bin package)
```

## Prerequisites

### uv (required)

The Jupyter kernel MCP server is launched via [uv](https://docs.astral.sh/uv/), which
auto-installs its Python dependency (`jupyter_client`) on first run — no conda env setup needed.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### HPC only

`start_agent_kernel` — a script in `local_dotfiles_RCCMidwayGeneral/bin/` that submits
a Slurm job running a Jupyter kernel on a compute node. See the `compute-kernel` skill.

## MCP server: jupyter_kernel_mcp.py

Lives in `~/bin/` (stowed from `bin/bin/`). It is a lightweight MCP server that lets
Claude start, connect to, and execute code in Jupyter kernels via the Jupyter wire
protocol (ZMQ connection files). This is distinct from a full Jupyter server — no HTTP,
no open ports, no token management.

Claude Code launches it as: `uv run --script jupyter_kernel_mcp.py`

**Why uv?** The script declares `jupyter_client` as an inline dependency
(`# /// script` metadata block). uv creates an isolated env and installs it automatically
on first run — nothing to pre-install.

## One manual step: update mcp.json

`mcp.json` contains one hardcoded path that must match your username:

```json
"args": ["run", "--script", "/home/YOUR_USERNAME/.claude/jupyter_kernel_mcp.py"]
```

Edit `~/.claude/mcp.json` (or `dotfiles/claude/.claude/mcp.json`) after stowing.

## Machine-specific config

`settings.local.json` — create this by hand at `~/.claude/settings.local.json` for
per-machine permission overrides. It is gitignored and never stowed. See
[Claude Code settings docs](https://docs.anthropic.com/en/docs/claude-code/settings) for
the format (same as `settings.json`).

## Skills

Skills are Markdown documents that Claude loads as context when invoked. They encode
reusable workflows so Claude doesn't need to re-learn your setup each session. Browse
`~/.claude/skills/` to see what's available — each subdirectory is a skill.

Some skills are HPC-specific (e.g. `compute-kernel`, `hpc`, `agent-plots`) and are
harmless but unused on other machines.
