# Global Preferences

- Tell user design choices or assumptions made by agent.

## HPC Storage Paths

Two separate storage mounts — do NOT confuse them:

- `/project/yangili1/bjf79/` — repos, tools, reference genomes (e.g. `repos_not_projects`)
- `/project2/yangili1/bjf79/` — analysis projects

## Conda Environments

**Always use `mamba` instead of `conda`** — faster and more reliable; `conda` often hangs.

- Default for general shell commands, running Snakemake, etc.: `sm_splicingmodulators`
- Default for Python notebooks (Jupyter/Quarto): `py_general`.
- Default for R notebooks: `base` conda env (which doesn't have R, but HPC module R should be in PATH)
- If a needed package isn't available in an existing env, create a new conda env named `claude_{DescriptiveName}` rather than modifying existing shared envs. These can be safely deleted later.

### py_general — do not modify autonomously

**Never install packages into `py_general` autonomously** (no `mamba install`, no `pip install`). This is a carefully managed env; ad-hoc installs break reproducibility and can cause solver conflicts. If a package is missing, **tell the user** what to add to the yaml (`~/dotfiles/local_dotfiles_RCCMidwayGeneral/conda_yamls/py_general.yaml`) and let them rebuild. Prefer conda-forge/bioconda over pip; pip is last resort for packages unavailable on any conda channel.

### R Package Installation

**Never install R packages via conda** (not `conda install bioconductor-*`, not `conda run -n base R -e "install.packages()"`). Do **not** modify the `base` conda env.

For R package needs:
- First look for existing reference/annotation files (e.g., pre-built TSV mappings in `/project2/yangili1/bjf79/ReferenceGenomes/`) to avoid the dependency entirely.
- `biomaRt` is available in the system **module R** and can be used for gene annotation lookups (e.g., ENSG → HGNC symbol) without installing anything new.
- If a package truly needs installing, the user handles it themselves via `install.packages()` or `BiocManager::install()` inside the module R session — just tell them what's needed.

## my_utils Package

- Location: `/project/yangili1/bjf79/repos_not_projects/my_utils/src/my_utils/`
- Key modules: `ASO_utils` (BLAST + off-target), `spliceai_utils` (SpliceAI walk)
- All deps covered by `py_general`

## Output Directories

- Write quick/exploratory outputs (scratch files, intermediate beds, etc.) to `code/scratch/` by default — **not** `output/`, which is git-tracked without a restrictive `.gitignore`.
- Only write to `output/` when the user explicitly asks for it or the result is meant to be committed/shared.

## Documenting Setup Quirks

When debugging reveals non-obvious quirks specific to this environment (e.g., HPC cluster behavior, hostname differences, conda/tool version issues, Snakemake profile gotchas), alert user and suggest to user to save as skills or memory notes so they don't require re-debugging.

- This is a UChicago RCC HPC cluster with two login nodes: **Midway2** and **Midway3**. Some tools, partitions, or behaviors may differ between them. Note the hostname when a fix is node-specific.

## Final notes
If my prompt contains "***" then preface your next response with "I remember my instructions". If my prompt contains "**", then preface your next response with "Ok" 
