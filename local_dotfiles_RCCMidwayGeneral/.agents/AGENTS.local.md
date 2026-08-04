# RCC Midway HPC — Machine-Specific Notes

## Machine identity

This package stows on **both** RCC Midway login nodes. Confirm which node with `echo $HOST`:

| Pattern | Node |
|---|---|
| `midway2-login*` | Midway2 |
| `midway3-login*` | Midway3 |

Tools, partitions, and behaviors may differ between nodes — note the hostname when a fix is node-specific. Genuinely node-local dotfiles (e.g. VSCode remote-server settings) live in `local_dotfiles_RCCMidway2` (no Midway3-specific package exists yet).

## Key Facts

- **Storage**: `/project/yangili1/bjf79/` (repos, tools, reference genomes) vs `/project2/yangili1/bjf79/` (analysis projects) — do NOT confuse them.
- **Conda**: always use `mamba` instead of `conda` — `conda` often hangs. `.condarc` (shared across both nodes) points envs/pkgs at `/project2/gilad/bjf79_project1/`.
- **Default envs**: `sm_splicingmodulators` (Snakemake/shell), `py_general` (Python notebooks), `base` (R — no conda R; use HPC module R).
- **`AGENT_PLOTS`**: runtime-detected — server `--directory` may point to scratch, not `~/agent_plots`. Detect with: `ps aux | grep agent_plots_server | grep -o -- '--directory [^ ]*' | awk '{print $2}'`
- **Plot server port**: these are shared login nodes — another user can already hold 8765, so `agent_plots_server.py` auto-retries 8766-8769 and writes whichever port it actually bound to `~/.agent_plots_port`. Detect with: `cat ~/.agent_plots_port` (falls back to 8765 if the file doesn't exist yet). The Mac SSH config forwards the whole 8765-8769 range, so whichever port it lands on is already tunneled — no client-side change needed when this happens.
- **Plot server IPv4 vs IPv6**: the server binds `0.0.0.0` (IPv4 only) and its port retry only detects IPv4 conflicts, so an IPv6-only listener on the same port is invisible to it. Remote `localhost` resolves to `::1` first, so `LocalForward PORT localhost:PORT` silently tunnels into that other process: browser gets an empty reply (curl exit 52) while `curl 127.0.0.1:PORT` on the HPC returns 200. Diagnose with `ss -ltnp | grep :PORT` — a `[::1]:PORT` line with no owning user is someone else's. The Mac SSH config forwards to `127.0.0.1:PORT`, never `localhost:PORT`.

## Agent Reference

| Key | Value |
|---|---|
| `MACHINE` | RCC Midway HPC (UChicago) — Midway2 / Midway3 login nodes |
| `HOSTNAME_VERIFY` | `echo $HOST` matches `midway2-login*` or `midway3-login*` |
| `BRAIN_PATH` | `/project/yangili1/bjf79/repos_not_projects/brain` |
| `PROJECTS_DIR` | `/project2/yangili1/bjf79/` |

## R Package Installation

Never install R packages via conda; never modify the `base` conda env. Details (module R, `biomaRt`, flat TSV mappings) → brain `annotation-reference-files` note.

## Local Clipboard

`pbcopy_to_local` (in PATH) pipes stdin to the Mac clipboard over the SSH tunnel. Usage + per-node `nc` quirk → brain `pbcopy-to-local-fix` note.
