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

## After creating the notebook
Remind the user to render it with:
```bash
# From project root or analysis/ dir
quarto render analysis/YYYYMMDD_name.qmd
```
Or for Python notebooks, register the kernel first if needed:
```bash
conda run -n py_general python -m ipykernel install --user --name py_general
```
