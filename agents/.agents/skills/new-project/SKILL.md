---
name: new-project
description: Start a new RNA-seq analysis project using the cookiecutter-quarto-smk template with the rna_seq snakemake submodule. Invoke when the user wants to create a new project directory with the standard cookiecutter scaffold.
argument-hint: "[project name, e.g. naRNAseq_SSE]"
---

# New Project via Cookiecutter

## Overview

Projects are created using the `cookiecutter-quarto-smk` template, which scaffolds a Quarto+Snakemake project and optionally adds git submodules for workflow modules (e.g. the rna-seq snakemake workflow).

## Steps

### 1. Activate conda env
```bash
conda activate cookiecutter
```

### 2. Run cookiecutter
```bash
cookiecutter git@github.com:bfairkun/cookiecutter-quarto-smk.git
```
Answer `y` to re-download if prompted (it caches the template).

### 3. Cookiecutter prompts — defaults and conventions

| Prompt | Default | Notes |
|---|---|---|
| full_name | Benjamin Fair | Accept default |
| email | bfair.kun@gmail.com | Accept default |
| username | bfairkun | Accept default |
| **project_name** | My project | Use `YYYYMMDD_ProjectName` format (e.g. `20260307_naRNAseq_SSE`) |
| repo_name | auto-lowercased | Accept default |
| min_snakemake_version | 7.32.0 | Accept default |
| make_conda_env | 1 (n) | Accept default (no) |
| license | 1 (MIT) | Accept default |
| slurm_partition | broadwl | Accept default |
| submodules (description prompt) | — | Just press Enter (it's a dummy info variable) |
| **submodules** | default | For RNA-seq projects, enter: `{'rna_seq': {'url': 'git@github.com:bfairkun/snakemake-workflow_rna-seq.git', 'branch': 'main'}}` |

### 4. What gets created

- Project directory: `<PROJECTS_DIR from CLAUDE_local.md>/<repo_name>/`
- Git repo initialized
- Submodule at `code/module_workflows/rna_seq` → `snakemake-workflow_rna-seq` (main branch)
- The rna_seq submodule itself pulls nested submodules: GenometracksByGenotype, leafcutter, leafcutter2, leafcutter2_chao

## Key paths after creation

```
<PROJECTS_DIR>/<repo_name>/
├── analysis/          # Quarto notebooks go here
├── code/
│   ├── module_workflows/
│   │   └── rna_seq/   # git submodule (snakemake-workflow_rna-seq)
│   └── rules/         # project-specific snakemake rules
├── data/
└── output/
```

## Non-interactive usage (preferred for scripting)

Use `--no-input` with `key=value` pairs. `submodules` is parsed via Python `eval()` — pass a real dict literal or `"{}"` for none:

```bash
cd <PROJECTS_DIR from CLAUDE_local.md> && conda run -n cookiecutter cookiecutter git@github.com:bfairkun/cookiecutter-quarto-smk.git \
  --no-input project_name="20260310_MyProject" \
  submodules="{'rna_seq': {'url': 'git@github.com:bfairkun/snakemake-workflow_rna-seq.git', 'branch': 'main'}}"
```

## Notes

- Projects dir: `PROJECTS_DIR` from `CLAUDE_local.md`
- `cookiecutter` conda env must be active
- Submodules: pass `"{}"` for no submodules — NOT `"'{}'"` (string-in-string causes `AttributeError: 'str' has no 'keys'`)
- Render notebooks: `conda run -n py_general render_notebook render analysis/notebook.qmd` (`render_notebook` is a quarto shim in `~/bin/` that records the render env; see `compute-kernel` skill)
- After creation, `cd` into the project and open in VSCode
