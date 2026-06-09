# RCC Midway HPC Context

This is a UChicago RCC HPC cluster with two login nodes: **Midway2** and **Midway3**. Some tools, partitions, or behaviors may differ between them. Note the hostname when a fix is node-specific.

## HPC Storage Paths

Two separate storage mounts — do NOT confuse them:

- `/project/yangili1/bjf79/` — repos, tools, reference genomes (e.g. `repos_not_projects`)
- `/project2/yangili1/bjf79/` — analysis projects

## Conda Environments

**Always use `mamba` instead of `conda`** — faster and more reliable; `conda` often hangs.

- Default for general shell commands, running Snakemake, etc.: `sm_splicingmodulators`
- Default for Python notebooks (Jupyter/Quarto): `py_general` (see shared CLAUDE.md)
- Default for R notebooks: `base` conda env (which doesn't have R, but HPC module R should be in PATH)

## my_utils Package

- Location: `/project/yangili1/bjf79/repos_not_projects/my_utils/src/my_utils/`

## Local Clipboard

`pbcopy_to_local` is in PATH (`~/bin/`). Pipes stdin over the SSH reverse tunnel (port 2224) to the Mac's `pbcopy` daemon.

Use it whenever outputting something the user needs to paste — auth URLs, tokens, etc.:

```bash
echo "https://auth.example.com/device?code=XXXX" | pbcopy_to_local
```

## Agent Reference

Paths used by agent skills — **always detect at runtime rather than hardcoding**:

- **`AGENT_PLOTS`** (HTTP server directory): the server's `--directory` may point to scratch, not `~/agent_plots`. Detect with:
  ```bash
  ps aux | grep agent_plots_server | grep -o -- '--directory [^ ]*' | awk '{print $2}'
  ```
  Current value: `/scratch/midway3/bjf79/agent_plots`

## R Package Installation

**Never install R packages via conda** (not `conda install bioconductor-*`, not `conda run -n base R -e "install.packages()"`). Do **not** modify the `base` conda env.

For R package needs:
- First look for existing reference/annotation files (e.g., pre-built TSV mappings in `/project2/yangili1/bjf79/ReferenceGenomes/`) to avoid the dependency entirely.
- `biomaRt` is available in the system **module R** and can be used for gene annotation lookups (e.g., ENSG → HGNC symbol) without installing anything new.
- If a package truly needs installing, the user handles it themselves via `install.packages()` or `BiocManager::install()` inside the module R session — just tell them what's needed.
