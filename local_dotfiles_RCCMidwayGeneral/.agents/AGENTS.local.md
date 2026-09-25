# RCC Midway HPC — Machine-Specific Notes

## Machine identity

This package stows on **both** RCC Midway login nodes. Confirm which node with `echo $HOST`:

| Pattern | Node |
|---|---|
| `midway2-login*` | Midway2 |
| `midway3-login*` | Midway3 |

Tools, partitions, and behaviors may differ between nodes — note the hostname when a fix is node-specific. Genuinely node-local dotfiles (e.g. VSCode remote-server settings) live in `local_dotfiles_RCCMidway2` / `local_dotfiles_RCCMidway3`. The two nodes have **separate home directories**, so each node is stowed on its own.

## Key Facts

- **Storage**: `/project/yangili1/bjf79/` (repos, tools, reference genomes) vs `/project2/yangili1/bjf79/` (analysis projects) — do NOT confuse them.
- **Conda**: always use `mamba` instead of `conda` — `conda` often hangs. `.condarc` (shared across both nodes) points envs/pkgs at `/project2/gilad/bjf79_project1/`.
- **Default envs**: `sm_splicingmodulators` (Snakemake/shell), `py_general` (Python notebooks), `base` (R — no conda R; use HPC module R).
- **Agent plots**: server directory detection, port retry (8765-8769), and tunnel troubleshooting → `agent-plots` skill.
- **Login-node memory**: one **8 GiB cgroup for the whole user**, shared by every concurrent session and kernel. Parallel agents OOM-kill each other's kernels *silently* — the next `run_python` gives a bare `NameError` and the cell counter is back at `In[1]`. Diagnosis + fix → `compute-kernel` skill.

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
