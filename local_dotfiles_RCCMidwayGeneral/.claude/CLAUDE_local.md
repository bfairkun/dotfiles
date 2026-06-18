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

## Agent Reference

| Key | Value |
|---|---|
| `MACHINE` | RCC Midway HPC (UChicago) — Midway2 / Midway3 login nodes |
| `HOSTNAME_VERIFY` | `echo $HOST` matches `midway2-login*` or `midway3-login*` |
| `BRAIN_PATH` | `/project/yangili1/bjf79/repos_not_projects/brain` |
| `PROJECTS_DIR` | `/project2/yangili1/bjf79/` |
| `my_utils` | `/project/yangili1/bjf79/repos_not_projects/my_utils/src/my_utils/` |

## R Package Installation

Never install R packages via conda. Do not modify the `base` conda env.

- Prefer pre-built TSV mappings in `/project2/yangili1/bjf79/ReferenceGenomes/` to avoid dependencies.
- `biomaRt` is available in the system module R for gene annotation lookups (ENSG → HGNC, etc.).
- If a package truly needs installing, tell the user — they handle it via `install.packages()` or `BiocManager::install()` in a module R session.

## Local Clipboard

`pbcopy_to_local` is in PATH (`~/bin/`). Pipes stdin over the SSH reverse tunnel (port 2224) to the Mac's `pbcopy` daemon.

```bash
echo "https://auth.example.com/device?code=XXXX" | pbcopy_to_local
```
