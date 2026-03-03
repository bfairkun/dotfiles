# Global Preferences

## Project Template

Most projects use the cookiecutter: https://github.com/bfairkun/cookiecutter-quarto-smk

### Directory structure and git conventions

The `code/` directory uses a **whitelist** `.gitignore` (`*` = ignore all, then explicit
`!dir` entries allow specific subdirectories). Key convention:

| Directory | Tracked? | Purpose |
|---|---|---|
| `analysis/` | Yes | Quarto notebooks (`.qmd`, `.Rmd`, `.ipynb`) |
| `code/scripts/` | Yes | Pipeline scripts |
| `code/rules/` | Yes | Snakemake rules |
| `code/envs/` | Yes | Conda environment YAML files |
| `code/config/` | Yes | Config files |
| `code/scratch/` | **No** | Large / temporary intermediate files |
| `output/` | Yes (small files only) | Processed output small enough to commit |
| `data/` | Yes | Raw data |

**Rule**: Large files go in `code/scratch/` — do NOT write large files to `output/`,
`analysis/`, or other tracked directories.

### Notebook naming convention

Notebooks in `analysis/` are always date-prefixed: `YYYYMMDD_descriptive_name.qmd`

Example: `analysis/20260224_blast_tm.qmd`

## Conda Environments

| Environment | Purpose |
|---|---|
| `py_general` | Default for Python analysis notebooks — pandas, numpy, biopython, and most common packages |
| `sm_splicingmodulators` | Running Snakemake pipelines; rule-specific envs defined within |
| R | Managed per-project (renv or system R), not a shared conda env |

Use `py_general` by default unless a required dependency is unavailable there.

## Snakemake Pipelines

- **Always invoked from the `code/` directory**: `cd code && snakemake ...`
- All paths in Snakefiles are relative to `code/` (e.g. `scratch/`, `config/`, `../analysis/`, `../output/`, `../logs/`)
- Use profile `slurm_midway3` on midway3, `slurm` on midway2
- Always include a `log:` directive in every rule and redirect stdout+stderr: `> {log} 2>&1`

## HPC Storage Paths

Two separate storage mounts exist on this HPC — do NOT confuse them:

- `/project/yangili1/bjf79/` — repos, tools, reference genomes (e.g. `repos_not_projects`)
- `/project2/yangili1/bjf79/` — analysis projects

## my_utils Package

Catch-all package for reusable functions across projects.

- Location: `/project/yangili1/bjf79/repos_not_projects/my_utils/src/my_utils/`
- All dependencies covered by `py_general` unless noted otherwise
- Key modules: `ASO_utils` (BLAST + off-target), `spliceai_utils` (SpliceAI walk)
