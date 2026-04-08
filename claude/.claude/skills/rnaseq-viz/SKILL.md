---
name: rnaseq-viz
description: Conventions for RNA-seq PCA and correlation heatmaps in R — when to scale, color schemes, and pheatmap setup. Invoke when making PCA plots or sample-correlation heatmaps from RNA-seq expression matrices.
argument-hint: "[pca | heatmap | both]"
---

# RNA-seq Visualization Conventions

## PCA — Gene Scaling

**Always z-score genes before PCA.**

```r
expr_t     <- t(as.matrix(expr_mat))          # samples × genes
scaled_mat <- scale(expr_t)                   # z-score each gene across samples
scaled_mat <- scaled_mat[, colSums(is.na(scaled_mat)) == 0]  # drop zero-var genes
pca        <- prcomp(scaled_mat, center = FALSE, scale. = FALSE)
```

**Rationale:** Without scaling, high-variance genes dominate PC1–2 and structure reflects expression magnitude rather than coordinated biological variation. Scaling gives each gene equal weight.

- `scale()` applied to a samples×genes matrix scales each column (gene) across samples
- Set `center = FALSE, scale. = FALSE` in `prcomp` since scaling is already done

### Axis labels — always show % variance explained

```r
pct_var <- round(summary(pca)$importance[2, 1:2] * 100, 1)
labs(
  x = paste0("PC1 (", pct_var[1], "% var)"),
  y = paste0("PC2 (", pct_var[2], "% var)")
)
```

### Dose coloring — use rank, not raw nM

When comparing dose-response series, color by **dose rank** rather than raw nM. Different drugs have different dose ranges, so rank puts them on a comparable scale and avoids log-scale color compression.

```r
df <- df %>%
  mutate(dose_rank = ifelse(Treatment == "DMSO", NA_integer_,
                            as.integer(dense_rank(dose.nM))))

n     <- max(df$dose_rank, na.rm = TRUE)
blues <- brewer.pal(max(3, n), "Blues")[seq_len(n)]
scale_color_manual(values = setNames(blues, as.character(seq_len(n))),
                   name = "dose rank\n(low→high)")
```

DMSO (or vehicle control) gets `NA` rank and is plotted separately in gray.

---

## Correlation Heatmap — Do NOT Scale

**Use raw (log2 TMM-CPM) expression values for the correlation matrix.**

```r
cor_mat <- cor(t(expr_t[sample_order, ]), method = "spearman")
```

**Rationale:** Scaling before `cor()` compresses all values toward 1, hides low-quality outlier samples, and reduces interpretability. The goal is to verify samples correlate well (Spearman ρ > 0.9 expected) and see biological groupings.

### Color scale — viridis, not diverging

Correlations between good RNA-seq samples are all positive (typically 0.85–0.99), so a diverging palette wastes half its range. Use viridis with a floor set to the actual minimum:

```r
cor_min <- floor(min(cor_mat) * 20) / 20   # round down to nearest 0.05
pheatmap(
  cor_mat,
  color  = viridis(100),
  breaks = seq(cor_min, 1, length.out = 101),
  ...
)
```

### Clustering

```r
pheatmap(
  cor_mat,
  clustering_distance_rows = as.dist(1 - cor_mat),
  clustering_distance_cols = as.dist(1 - cor_mat),
  clustering_method        = "ward.D2",
  ...
)
```

### Annotation sidebar — dose rank

Same dose-rank logic as PCA; use a Blues gradient:

```r
samples_ranked <- samples %>%
  group_by(Treatment) %>%
  mutate(dose_rank = ifelse(Treatment == "DMSO", NA_integer_,
                            as.integer(dense_rank(dose.nM)))) %>%
  ungroup()

max_rank <- max(samples_ranked$dose_rank, na.rm = TRUE)
rank_pal <- colorRampPalette(brewer.pal(9, "Blues")[3:9])(max_rank)
# pass as: annotation_colors = list(dose_rank = rank_pal)
```
