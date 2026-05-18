---
name: qpcr-analysis
description: >
  Analyze QuantStudio qPCR data in a Quarto notebook: load TSV output, expand
  96→384-well layout, visualize plate layout and CT heatmap, compute ΔCT/ΔΔCT/RQ,
  run Z-score significance tests, and produce log₂ RQ bar plots per gene.
argument-hint: "[data file path and brief description of the experiment]"
---

# qPCR Analysis Skill

Use this skill to interactively build a qPCR analysis notebook. Follow the
interactive-notebook skill for the general kernel-first workflow; this skill
covers the qPCR-specific steps and rules.

qPCR notebooks must always have `embed-resources: true` in the Quarto header
so the HTML is fully self-contained.

---

## ⚠️ Critical statistics rule

**Never use qPCR technical replicates as independent observations.**
Always average technical replicates first (per sample × target), then compute
statistics on per-sample means. Violating this inflates degrees of freedom and
produces false-positive p-values.

---

## Step 0 — Gather information before writing any code

Ask the user for:
1. Path to the QuantStudio export file
2. The 96-well plate layout: which sample is in each well, and which PCR target
   (gene of interest + housekeeping gene) is in each row
3. Any known-bad wells to exclude
4. Which samples to use as the reference group for ΔΔCT, and why
5. Experiment metadata: date, cell line, any treatment conditions

The 96→384 expansion pattern is almost always: one 96-well plate stamped into a
384-well plate as 2×2 blocks (each 96-well position → four 384-well positions).
Confirm this assumption with the user.

---

## Step 1 — Load data

QuantStudio exports are tab-separated. The header row starts with `Well\t`; there
is often a UTF-8 BOM on the first line. Empty wells sometimes get junk CT values —
only trust wells present in your layout annotation.

```python
def load_quantstudio_tsv(path):
    with open(path) as f:
        lines = f.readlines()
    header_row = next(
        i for i, line in enumerate(lines)
        if line.lstrip("﻿").startswith("Well\t")
    )
    df = pd.read_csv(path, skiprows=header_row, sep="\t")
    df = df[df["Well Position"].notna() &
            df["Well Position"].str.match(r"^[A-P]\d+$")].copy()
    df["CT_numeric"] = pd.to_numeric(df["CT"], errors="coerce")
    df["row"] = df["Well Position"].str[0]
    df["col"] = df["Well Position"].str[1:].astype(int)
    return df.reset_index(drop=True)
```

Print: total wells loaded, % undetermined, CT range. Show the user before proceeding.

---

## Step 2 — Define the 96→384 layout

Build two 16×24 numpy string matrices (`sample_matrix`, `target_matrix`).
Each 96-well row R, col C (0-indexed) → 384-well rows 2R, 2R+1 and cols 2C, 2C+1.

```python
sample_matrix = np.full((16, 24), "", dtype=object)
target_matrix = np.full((16, 24), "", dtype=object)
BAD_WELLS_384 = set()  # populate with (row_letter, col_int) tuples

for r96, cols in samples_96.items():
    for c96, sname in cols.items():
        tgt = target_96[r96]
        for dr in range(2):
            for dc in range(2):
                rr, cc = 2*r96 + dr, 2*c96 + dc
                if (chr(ord("A") + rr), cc + 1) in BAD_WELLS_384:
                    continue
                sample_matrix[rr, cc] = sname
                target_matrix[rr, cc] = tgt
```

Also define a `sample_meta` dict (sample_id → whatever metadata fields the
experiment has) and a `group_palette` dict (sample group → hex color) here —
they're needed by the download section and plots.

Annotate `df` with sample and target from the matrices, then build `df_ann`
(wells with non-empty annotation):

```python
df["sample"] = df.apply(lambda w: sample_matrix[ord(w["row"])-ord("A"), w["col"]-1], axis=1)
df["target"] = df.apply(lambda w: target_matrix[ord(w["row"])-ord("A"), w["col"]-1], axis=1)
df_ann = df[(df["sample"] != "") & (df["target"] != "")].copy()
```

---

## Step 3 — CT heatmap (diagnose before committing to layout)

Show the CT heatmap first so the user can verify the layout is correct and
identify any unexpected empty wells or junk values.

Always use `interpolation='nearest'` — matplotlib's default bilinear
interpolation blurs discrete well grids.

```python
cmap_obj = plt.colormaps["plasma"].copy()
cmap_obj.set_bad("lightgray")
im = ax.imshow(ct_matrix, cmap=cmap_obj, aspect="auto",
               vmin=15, vmax=40, interpolation="nearest")
```

Overlay 96-well block outlines (white rectangles, 2×2 cells each).

---

## Step 4 — Plate layout figure

After the user confirms the layout is correct, show the annotated plate layout:
color by target gene, label each cell with sample name. Use the same
`interpolation='nearest'` and block-outline pattern. Add dual axes showing
both 384-well (bottom/left) and 96-well (top/right) coordinates.

Save both figures as PDF to `$SCRATCH/$USER/agent_plots/`.

---

## Step 5 — Raw CT download link

Build a tidy per-well TSV and embed it as a base64 download link. Always include:
`experiment_date`, `experiment_name`, `well_384`, `well_96`, `sample`,
`target_gene`, `CT`, plus any experiment-specific metadata columns (cell line,
treatment, sample group, sequence, etc.) drawn from `sample_meta`.

```python
import base64
from IPython.display import display, HTML

def well384_to_96(row_384, col_384):
    r96 = (ord(row_384) - ord("A")) // 2
    c96 = (col_384 - 1) // 2
    return chr(ord("A") + r96), c96 + 1

# build rows from df_ann + sample_meta ...
download_df = pd.DataFrame(rows)
tsv_bytes = download_df.to_csv(index=False, sep="\t").encode("utf-8")
b64 = base64.b64encode(tsv_bytes).decode("utf-8")
fname = f"{EXPERIMENT_DATE}_{EXPERIMENT_NAME}_raw_CT.tsv"
display(HTML(
    f'<a href="data:text/tab-separated-values;base64,{b64}" download="{fname}">'
    f'&#11015; Download raw CT data ({len(download_df)} wells) — {fname}</a>'
))
```

---

## Step 6 — ΔCT, ΔΔCT, RQ

Average technical replicates, apply housekeeping gene dropout filter, compute ΔCT.
The housekeeping gene and dropout threshold (commonly CT > 28–30) should be
confirmed with the user.

```python
ct_avg = (df_ann.groupby(["sample", "target"])["CT_numeric"]
          .mean().reset_index().rename(columns={"CT_numeric": "CT_mean"}))
ct_pivot = ct_avg.pivot(index="sample", columns="target", values="CT_mean")

HK_GENE = "GAPDH"           # confirm with user
HK_THRESHOLD = 28            # confirm with user
NTC_PREFIXES = ("noTemp",)   # confirm naming convention with user

ct_filt = ct_pivot[
    (ct_pivot[HK_GENE] <= HK_THRESHOLD) &
    (~ct_pivot.index.str.startswith(NTC_PREFIXES))
].copy()

ct_filt["dCT_GeneA"] = ct_filt["GeneA"] - ct_filt[HK_GENE]
```

Reference group for ΔΔCT: **discuss with user** — it depends on the experiment
design. Confirm which samples serve as controls and compute ΔΔCT as
`dCT_sample − mean(dCT_reference)`, then `RQ = 2^(−ΔΔCT)`.

Print dropped samples and the resulting ct_filt table.

---

## Step 7 — Z-score significance test

Score each test sample's per-sample mean dCT against the reference distribution.

```python
from scipy.stats import norm
from statsmodels.stats.multitest import multipletests

def run_zscore(test_samples, ref_samples, col_dct, ct_filt):
    ref_vals = ct_filt.loc[ref_samples, col_dct].dropna()
    ref_mean = ref_vals.mean()
    ref_sd   = ref_vals.std(ddof=1)
    rows = []
    for s in test_samples:
        if s not in ct_filt.index or pd.isna(ct_filt.loc[s, col_dct]):
            continue
        z = (ct_filt.loc[s, col_dct] - ref_mean) / ref_sd
        rows.append({"sample": s, "z": z, "pval": 2*(1 - norm.cdf(abs(z)))})
    res = pd.DataFrame(rows).set_index("sample")
    _, qvals, _, _ = multipletests(res["pval"], method="fdr_bh")
    res["qval"] = qvals
    return res, ref_mean, ref_sd
```

Run once per gene. BH FDR correction is within-gene.

---

## Step 8 — log₂ RQ bar plots (one per gene)

Separate plot per gene to avoid label crowding. Test samples on top, reference
samples below, separated by a dotted horizontal line. Annotate each test sample
bar with `p=X.XXX  FDR=X.XXX` (plus `*`/`**`/`***` if significant). Twin
y-axis shows raw RQ values.

```python
def pval_label(p, q):
    stars = "***" if q < 0.001 else "**" if q < 0.01 else "*" if q < 0.05 else ""
    return f"p={p:.3f}  FDR={q:.3f}{' ' + stars if stars else ''}"
```

Save each plot as PDF to `$SCRATCH/$USER/agent_plots/`.

---

## Render

Render from inside the `analysis/` directory (where `_quarto.yml` lives),
which directs output to `../docs/`:

```bash
cd analysis && conda run -n py_general quarto render YYYYMMDD_name.qmd
```
