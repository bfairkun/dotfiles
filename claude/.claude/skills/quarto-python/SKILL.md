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
---
```
- Always use `jupyter: py_general` (not `ipykernel`)
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
quarto render notebook.qmd -P gene:MBD5 -P walk_interval_start:148505696
```

### Displaying multiple plots in one cell
Use `from IPython.display import display` and call `display(plot)` — plain `print()` does not render plotnine plots.

### Prerequisite: register the py_general kernel once
```bash
conda run -n py_general python -m ipykernel install --user --name py_general
```
Verify: `jupyter kernelspec list`
