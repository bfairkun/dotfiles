---
name: new-notebook
description: Create a new analysis notebook in the analysis/ directory. Invoke when starting a new analysis, exploration, or visualization task that needs a notebook.
argument-hint: "[brief description of analysis]"
---

# New Notebook Conventions

## Naming
Always date-prefix: `analysis/YYYYMMDD_descriptive_name.qmd`
- Use today's date
- Descriptive name uses underscores, lowercase
- Example: `analysis/20260303_splice_site_conservation.qmd`

## Python kernel (Quarto + Jupyter)

```yaml
---
title: "Descriptive Title"
jupyter: py_general
format:
  html:
    code-fold: true
---
```

Then standard Python cells:
```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
```

- `my_utils` is pre-installed in `py_general` — no sys.path hacks needed
- Use `from IPython.display import display` for inline plots

## R kernel (Quarto + knitr)

```yaml
---
title: "Descriptive Title"
output: html_document
---
```

For Quarto with R engine:
```yaml
---
title: "Descriptive Title"
format: html
execute:
  echo: true
  warning: false
---
```

Standard R setup chunk:
````
```{r setup, include=FALSE}
library(tidyverse)
library(data.table)
```
````

## Prose — a notebook is a document, not a script

A reader who was not present for the analysis must be able to follow it. Code alone
never achieves this. Write enough prose that the notebook stands on its own.

**Open with the question.** The first block states what is being asked and why it
matters, names the external source (paper, dataset, prior notebook) with a link or
identifier, and lists what the notebook covers. Give the reader the background needed
to interpret the result — including any premise that is easy to get backwards, stated
explicitly.

**Introduce every plot and table before it appears.** Say what is being plotted, how
the quantity was computed, why it was computed that way, and what to look for. A
figure caption is not a substitute for this.

**Justify the methodological choices a reader would otherwise have to reverse-engineer
from the code**, since these are exactly what makes a result trustworthy or not:

- why a parameter has the value it does (window size, thresholds, region bounds)
- where coordinates came from, and any sanity check confirming them
- what serves as the positive control and what serves as the negative control
- what was deliberately excluded or not done, and why
- how a summary statistic is defined, and why that definition over the alternatives

**Close with conclusions.** State the answer to the opening question in plain language,
with the numbers that support it, followed by caveats and limits on interpretation.
Report negative results as findings, not omissions.

Prefer prose between chunks over comments inside them. Assertions on coordinates and
key assumptions are worth more than a sentence claiming the same thing.

## Data paths

Always use paths relative to the `analysis/` directory OR construct absolute paths robustly:
```python
# Python: go up one level from analysis/
import os
data_path = "../data/myfile.csv"
output_path = "../output/results.csv"
scratch_path = "../code/scratch/intermediates.parquet"
```

```r
# R
data_path <- "../data/myfile.csv"
output_path <- "../output/results.csv"
```

## Large outputs
- Small tables/figures → `output/` (committed)
- Large files → `code/scratch/` (not committed), reference from notebook

## Reader comment boxes

Projects scaffolded from `cookiecutter-quarto-smk` ship `analysis/_comment_widget.html`,
wired in through `include-after-body` in `analysis/_quarto.yml`. Every rendered page then
carries a comment panel at the bottom with no per-notebook markup — check whether the
project has that file before assuming the feature exists.

To invite comment at a specific point as well — after a figure, at the end of a section a
collaborator should weigh in on — drop a marker anywhere in the `.qmd`:

```
::: {.comment-box}
:::
```

`data-anchor` overrides the box's label, which otherwise defaults to the nearest preceding
heading. `data-prompt` puts a question above the box — **leave it off unless the user has
told you what to ask.**

Readers type into the boxes and press **Download annotated copy**, which serializes the live
DOM into a new self-contained HTML with the comments inside it. (The browser's own Save Page
As re-saves the original source and loses them.) All boxes share one comment store, so a
single download captures every comment on the page.

## After creating the notebook
Remind the user to render it with `render_notebook` (a quarto shim in `~/bin/` that records the render env into a hidden block in the `.qmd`; see `compute-kernel` skill):
```bash
# From project root or analysis/ dir
render_notebook render analysis/YYYYMMDD_name.qmd
```
Or for Python notebooks, register the kernel first if needed:
```bash
conda run -n py_general python -m ipykernel install --user --name py_general
```
