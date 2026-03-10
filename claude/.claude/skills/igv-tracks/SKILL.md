---
name: igv-tracks
description: Visualize genomic signal tracks, work with UCSC Genome Browser exports, or set up genome browser views. Invoke when plotting signal over genomic regions, using genometracks_utils, working with bigWig/BED/BAM tracks, or exporting from UCSC browser.
argument-hint: "[region, track type, or analysis goal]"
---

# Genome Track Visualization

## `genometracks_utils` from `my_utils`

Module path: `/project/yangili1/bjf79/repos_not_projects/my_utils/src/my_utils/genometracks_utils.py`
Available in `py_general` (already installed).

### What it does
Loads **UCSC Genome Browser JSON exports** (gzip-compressed) and computes signal across **BED12 blocks**, returning a tidy DataFrame. Useful for comparing RNA-seq/ChIP/ATAC signal across splice isoforms or exon structures.

### Workflow

**Step 1 — Export tracks from UCSC**
1. Navigate to your region in the UCSC Genome Browser
2. Go to **File → Save Session** or use the API: `hgTracks?hgsid=...&hgt.customText=...`
3. To export bigWig data as JSON: use the Table Browser or the UCSC API to get the signal as JSON. The expected format is a gzip-compressed JSON where each track is `track_name → {chrom: [[start, end, value], ...]}`

**Step 2 — Prepare your BED12 file**
The BED12 file defines the "blocks" (e.g., exons of a transcript) you want to intersect with signal:
```
chr2  1000  2000  gene1  0  +  1000  2000  0  2  200,300,  0,700,
```

**Step 3 — Compute block signal**
```python
from my_utils.genometracks_utils import get_block_signal_df, plot_block_signal

df = get_block_signal_df(
    tracks_path="code/scratch/ucsc_export.json.gz",
    bed12_path="data/my_transcripts.bed",
    track_names=["SampleA_RPM", "SampleB_RPM"],  # None = all tracks
    padding=50,   # extend blocks by 50 bp each side (shows splice site context)
)
# df columns: bed_name, chrom, block_id, start, end, width, in_block, <track cols>
```

**Step 4 — Plot**
```python
plot_block_signal(
    df,
    output_path="output/signal_plot.pdf",
    track_names=["SampleA_RPM", "SampleB_RPM"],
    region="chr2:1,850,700-1,886,852",  # optional, to zoom
    bed_names=["ENST00000123456"],        # optional, subset of BED entries
    ylim=(0, 5),                          # optional, shared y-axis
)
```

**Command-line interface** (if running as a script):
```bash
conda run -n py_general python -m my_utils.genometracks_utils \
    code/scratch/ucsc.json.gz \
    data/transcripts.bed \
    -o output/signal_plot \
    --padding 50 \
    --region "chr2:1,850,700-1,886,852"
# Writes output/signal_plot.tsv and output/signal_plot.pdf
```

### DataFrame returned by `get_block_signal_df()`

| Column | Description |
|--------|-------------|
| `bed_name` | BED12 feature name (field 4) |
| `chrom` | chromosome |
| `block_id` | `block_001`, `block_002`, ... (merged after padding) |
| `start`, `end` | sub-interval coordinates |
| `width` | end - start |
| `in_block` | True if within original (unpadded) block |
| `<track_name>` | signal value (NaN where track has no data) |

Aggregate example (weighted mean signal per block):
```python
result = (
    df[df["in_block"]]
    .groupby(["bed_name", "block_id"])
    .apply(lambda g: np.average(g["SampleA_RPM"].fillna(0), weights=g["width"]))
    .reset_index(name="weighted_mean_RPM")
)
```

---

## pyGenomeTracks INI approach (alternative)

For static publication-quality figures from local files (BAM, bigWig, BED, GTF):

```ini
# tracks.ini
[bigwig track]
file = path/to/signal.bw
title = My Signal
height = 3
color = blue
min_value = 0
max_value = 5

[genes]
file = path/to/annotation.gtf
title = Genes
height = 5

[spacer]

[x-axis]
```

```bash
conda run -n py_general pyGenomeTracks \
    --tracks tracks.ini \
    --region chr2:1850700-1886852 \
    --outFileName output/figure.pdf
```

Check if `pyGenomeTracks` is available: `conda run -n py_general pyGenomeTracks --version`
If not: add `- pygenometracks` to the relevant `code/envs/*.yaml`.

---

## IGV Session XML files (for local IGV via SAMBA-mounted Midway)

IGV is run locally on Mac, with Midway filesystem mounted via SAMBA. The path prefix for HPC files is `/Volumes/project/` (not `/project/`).

**Key XML structure:**
- `<Resource path="filename.bw" type="bw"/>` — use **relative filename only** (IGV resolves relative to the session file location)
- `<Track id="/Volumes/project/yangili1/bjf79/...">` — use **full `/Volumes/project/...` path** in the `id` attribute

**Template for a stranded bigWig pair:**
```xml
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<Session genome="hg38" locus="All" version="8">
    <Resources>
        <Resource path="sample_plus.bw" type="bw"/>
        <Resource path="sample_minus.bw" type="bw"/>
    </Resources>
    <Panel height="400" name="DataPanel" width="1500">
        <Track attributeKey="sample_plus.bw" autoScale="true" clazz="org.broad.igv.track.DataSourceTrack" color="0,0,178" fontSize="10" id="/Volumes/project/yangili1/bjf79/PATH/sample_plus.bw" name="Sample +" renderer="BAR_CHART" visible="true" windowFunction="mean"/>
        <Track attributeKey="sample_minus.bw" autoScale="true" clazz="org.broad.igv.track.DataSourceTrack" color="178,0,0" fontSize="10" id="/Volumes/project/yangili1/bjf79/PATH/sample_minus.bw" name="Sample -" negateValues="true" renderer="BAR_CHART" visible="true" windowFunction="mean"/>
    </Panel>
    <PanelLayout dividerFractions="0.9871428571428571"/>
    <HiddenAttributes>
        <Attribute name="DATA FILE"/>
        <Attribute name="DATA TYPE"/>
        <Attribute name="NAME"/>
    </HiddenAttributes>
</Session>
```

- Plus strand: color `0,0,178` (blue)
- Minus strand: color `178,0,0` (red), `negateValues="true"` to display downward
- Save the `.xml` session file in the **same directory** as the bigWig files so relative paths resolve correctly

## Quick IGV session tips

For bulk export of screenshots, use igvtools batch mode or `igv-reports`.
