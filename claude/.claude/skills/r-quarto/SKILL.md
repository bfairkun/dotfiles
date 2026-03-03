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

```bash
# From project root
quarto render analysis/YYYYMMDD_name.qmd

# Or open in VSCode and use the Quarto preview button
```

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
quarto render analysis/mynotebook.qmd --execute-debug

# Check R version
R --version

# Check package availability
Rscript -e "library(mypackage)"
```

If a chunk fails silently, add `#| error: true` to that chunk to continue rendering and show the error inline.
