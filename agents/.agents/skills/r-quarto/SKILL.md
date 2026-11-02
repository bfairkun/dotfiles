---
name: r-quarto
description: Working with R-kernel Quarto notebooks (.qmd files). Invoke when creating, debugging, or editing R analysis notebooks, or when switching a notebook from Rmd to Quarto format.
argument-hint: "[topic or notebook path]"
---

# R / Quarto Notebooks Reference

## YAML header (standard)

```yaml
---
title: "My Analysis"
format:
  html:
    code-fold: true
    toc: true
execute:
  echo: true
  warning: false
  message: false
---
```

For self-contained output (embed data/figures):
```yaml
format:
  html:
    embed-resources: true
    code-fold: true
```

## knitr chunk options (Quarto style)

Use `#|` prefixed options inside chunks — NOT `{r, echo=FALSE}` header style:

````
```{r}
#| label: fig-volcano
#| fig-cap: "Volcano plot of differential expression"
#| fig-width: 8
#| fig-height: 6
#| echo: false

# your code here
```
````

Common options:
- `#| echo: false` — hide code, show output
- `#| eval: false` — show code, don't run
- `#| cache: true` — cache chunk output (use for slow chunks)
- `#| fig-width: 8` / `#| fig-height: 5`
- `#| warning: false` / `#| message: false`

## Standard setup chunk

````
```{r setup}
#| include: false
library(tidyverse)
library(data.table)

# Set ggplot theme
theme_set(theme_bw(base_size = 12))
```
````

## Data paths (relative to analysis/)

```r
# Up one level to project root
data_path <- "../data/myfile.csv"
output_path <- "../output/results.tsv"
scratch_path <- "../code/scratch/bigfile.parquet"

# Read with data.table (fast for large files)
dt <- fread("../data/myfile.tsv")

# Or tidyverse
df <- read_tsv("../data/myfile.tsv")
```

## Saving outputs

```r
# Small tables to output/ (committed to git)
write_tsv(results_df, "../output/de_results.tsv")

# Figures
ggsave("../output/figure1.pdf", plot = p, width = 8, height = 5)

# Large objects to scratch
saveRDS(big_object, "../code/scratch/big_object.rds")
```

## Rendering

Use `render_notebook` (in `~/bin/`) in place of `quarto` — it's a transparent shim that
passes all args through to quarto and records the render environment (host, Slurm
allocation, actual peak memory) into a hidden block at the end of the `.qmd`. See the
`compute-kernel` skill for details.

```bash
# From project root
render_notebook render analysis/YYYYMMDD_name.qmd

# Render an Rmd (quarto can render .Rmd files too; env block only added for .qmd)
render_notebook render analysis/YYYYMMDD_name.Rmd --output-dir docs

# From within the analysis/ directory
conda run -n base render_notebook render YYYYMMDD_name.Rmd --output-dir ../docs

```

> **HPC note (RCC/Midway):** Do NOT use `Rscript -e "rmarkdown::render(...)"` on this cluster.
> It fails silently with a `GLIBCXX_3.4.32 not found` error when loading `later.so` from the
> user R library. `conda run -n base render_notebook render` works correctly and is the preferred
> approach for both `.Rmd` and `.qmd` files.

## Common R packages for RNA-seq / genomics

```r
# Tidy data
library(tidyverse)
library(data.table)

# Genomics
library(GenomicRanges)
library(rtracklayer)    # import/export BED, GTF, bigwig
library(BSgenome)

# Differential expression
library(DESeq2)
library(edgeR)

# Visualization
library(ggplot2)
library(ggrepel)        # non-overlapping labels
library(patchwork)      # combine plots
library(ComplexHeatmap)

# Bioc utilities
library(biomaRt)
library(AnnotationDbi)
library(org.Hs.eg.db)
```

## Debugging rendering failures

```bash
# Render with verbose output to see exactly which chunk fails
render_notebook render analysis/mynotebook.qmd --execute-debug

# Check R version
R --version

# Check package availability
Rscript -e "library(mypackage)"
```

If a chunk fails silently, add `#| error: true` to that chunk to continue rendering and show the error inline.
