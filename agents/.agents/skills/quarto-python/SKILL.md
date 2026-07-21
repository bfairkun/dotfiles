---
name: quarto-python
description: Working with Python/Quarto notebooks (.qmd files with jupyter engine). Invoke when creating, debugging, or parameterizing Quarto notebooks with a Python kernel.
argument-hint: [topic]
---

# Python / Quarto Notebooks Reference

## Front matter
```yaml
---
title: "My Analysis"
jupyter: py_general
format:
  html:
    code-fold: true
    toc: true
---
```
- Always use `jupyter: py_general` (not `ipykernel`)
- Always include `code-fold: true` and `toc: true` — these are defaults for all Python qmd notebooks
- No `sys.path.insert` hacks needed — `my_utils` is installed in `py_general`

## Parameterized notebooks (papermill)

For notebooks that can be rendered with different params via `quarto render -P key:value`:

1. Add a cell tagged `parameters` with defaults:
```python
#| tags: [parameters]
gene = "MYT1L"
region_interval = "chr2:1840760-1887609"
walk_interval_start = 1860114
```

2. A subsequent cell transforms/uses them normally:
```python
walk_interval = (int(walk_interval_start), int(walk_interval_end))
```

**Key rule**: Quarto/papermill injects params as **plain Python variables**, NOT as a
`params` dict. Avoid `params["key"]` — that's an R Markdown convention.

### Rendering with overrides
```bash
render_notebook render notebook.qmd -P gene:MBD5 -P walk_interval_start:148505696
```

### Displaying multiple plots in one cell
Use `from IPython.display import display` and call `display(plot)` — plain `print()` does not render plotnine plots.

### Prerequisite: register the py_general kernel once
```bash
conda run -n py_general python -m ipykernel install --user --name py_general
```
Verify: `jupyter kernelspec list`

## Rendering Python notebooks

Use `render_notebook` (in `~/bin/`) in place of `quarto` — a transparent shim that passes all args through and records the render environment (host, Slurm allocation, actual peak memory) into a hidden block at the end of the `.qmd`. See the `compute-kernel` skill for details.

**Activate py_general before rendering** so quarto can find jupyter and the registered kernel:
```bash
conda activate py_general
render_notebook render notebook.qmd
```

When running via `conda run -n base`, the base env has `ipykernel`, `nbformat`, `nbclient`, and `jupyter_client`, so it can discover the registered `py_general` kernel. No `QUARTO_PYTHON` is needed:
```bash
conda run -n base render_notebook render notebook.qmd
```

**Verifying success:** `conda run` can return exit code 0 even when the notebook errors internally (e.g. a `NameError` in a cell). Always confirm render success by checking the task output contains `Output created:` and the HTML timestamp updated (`ls -la output.html`).

## igv-reports

`create_report` (igv-reports) is installed in `py_general`. Run via:
```bash
/project2/gilad/bjf79_project1/envs/py_general/bin/create_report sites.bed --genome hg38 --tracks *.bw --output report.html --standalone
```
Embed output in a notebook with `IPython.display.IFrame` or inline with `IPython.display.HTML`.
