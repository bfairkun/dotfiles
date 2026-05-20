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

IGV is run locally on Mac, with Midway filesystem mounted via SAMBA. The path prefix for HPC files is `/Users/bjf79/mnt/project/` (not `/Volumes/project/` and not `/project/`).

Example: `/Users/bjf79/mnt/project/yangili1/bjf79/20260310_diversesm_dr/code/rna_seq/bigwigs/unstranded/PTC258_24h_noStim_8nM_rep1.bw`

**Key XML structure:**
- `<Resource path="/Users/bjf79/mnt/project/yangili1/bjf79/..."/>` — use **full mac path** in Resource
- `<Track id="/Users/bjf79/mnt/project/yangili1/bjf79/...">` — same full mac path in the `id` attribute

**Where to save IGV session XML files:**
- Save to `code/scratch/`, **not** `output/`. The `output/` directory is git-tracked; IGV sessions that reference untracked local files (bigWigs, scratch BEDs) have no value in git history.
- Exception: only put a session in `output/` if the user explicitly requests it or the session references only committed/shared files.

**Standard gene annotation tracks for human (hg38) sessions:**
Always include all three of these in the `AnnotationPanel` for any human session:
1. Default IGV gene track: `id="hg38_genes"`, `attributeKey="Gene"`
2. `/Users/bjf79/mnt/project2/yangili1/bjf79/ReferenceGenomes/GRCh38_GencodeRelease44Comprehensive/MANE.bed.gz`
3. `/Users/bjf79/mnt/project2/yangili1/bjf79/ReferenceGenomes/GRCh38_GencodeRelease44Comprehensive/Reference.ColoredTranscripts.bed.gz`

Add all three as `FeatureTrack` entries in `AnnotationPanel`, with `displayMode="SQUISHED"` for the two BED files.

**Panel layout rules:**
- `FeaturePanel` is a **reserved IGV name** that is **always rendered at the bottom**, regardless of XML order. Avoid it.
- Use any **custom panel name** (e.g. `AnnotationPanel`, `DataPanel`) — IGV stacks them top-to-bottom in XML order, separated by draggable dividers.
- Preferred layout: `AnnotationPanel` (reference sequence + genes) on top, `DataPanel` (signal tracks) below. No `FeaturePanel` needed.
- `dividerFractions` has one value per panel boundary: `"0.18,0.97"` for a small annotation panel on top + large data panel below.

**Template (annotation panel on top, data panel below):**
```xml
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<Session genome="hg38" locus="All" version="8">
    <Resources>
        <Resource path="sample_plus.bw" type="bw"/>
        <Resource path="sample_minus.bw" type="bw"/>
    </Resources>
    <Panel height="120" name="AnnotationPanel" width="1500">
        <Track attributeKey="Reference sequence" clazz="org.broad.igv.track.SequenceTrack" fontSize="10" id="Reference sequence" name="Reference sequence" sequenceTranslationStrandValue="POSITIVE" shouldShowTranslation="false" visible="true"/>
        <Track attributeKey="Gene" clazz="org.broad.igv.track.FeatureTrack" fontSize="10" id="hg38_genes" name="Gene" visible="true"/>
    </Panel>
    <Panel height="400" name="DataPanel" width="1500">
        <Track attributeKey="sample_plus.bw" autoScale="true" clazz="org.broad.igv.track.DataSourceTrack" color="0,0,178" fontSize="10" id="/Users/bjf79/mnt/project/yangili1/bjf79/PATH/sample_plus.bw" name="Sample +" renderer="BAR_CHART" visible="true" windowFunction="mean"/>
        <Track attributeKey="sample_minus.bw" autoScale="true" clazz="org.broad.igv.track.DataSourceTrack" color="178,0,0" fontSize="10" id="/Users/bjf79/mnt/project/yangili1/bjf79/PATH/sample_minus.bw" name="Sample -" negateValues="true" renderer="BAR_CHART" visible="true" windowFunction="mean"/>
    </Panel>
    <PanelLayout dividerFractions="0.18,0.97"/>
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

**BED file naming — avoid `*junctions.bed`**: IGV auto-detects any BED file whose name contains `junctions` and renders it as splice-junction arcs. Arc display does not show the feature name label. Use a different suffix (e.g. `_features.bed`, `_intervals.bed`) when you want standard filled-block display with visible names.

For bulk export of screenshots, use igvtools batch mode or `igv-reports`.

---

## Embedded igv.js browser in a Quarto notebook

For a **fully self-contained, interactive browser embedded in an HTML notebook**, use igv.js
with bigwig data converted to gzip+base64 bedgraph data URIs. No server needed; igv.js
loads from CDN (internet required for hg38 reference sequence).

**Do NOT use `igv-reports`** for RNA-seq coverage — it is a variant-centric tool that shows
an empty variant table and does not support bigwig tracks properly.

### Pattern (Python, py_general kernel)

```python
import pyBigWig, json, os
from base64 import b64encode
from gzip import compress
from IPython.display import display, HTML
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

IGV_CHR, IGV_START, IGV_END = 'chr16', 187000, 231000
IGV_LOCUS = f'{IGV_CHR}:{IGV_START}-{IGV_END}'

def bedgraph_to_data_uri(bw_path, chrom, start, end):
    """Read bigwig intervals → bedgraph string → gzip → base64 data URI."""
    bw = pyBigWig.open(bw_path)
    ivs = bw.intervals(chrom, start, end) or []
    bw.close()
    lines = ''.join(f'{chrom}\t{s}\t{e}\t{v:.4f}\n' for s, e, v in ivs)
    gz = compress(lines.encode())
    b64 = b64encode(gz).decode()
    return f'data:application/gzip;base64,{b64}'

# Build track list with data URIs
track_configs = []
for t in tracks:   # tracks = list of dicts with 'bw', 'name', 'color'
    uri = bedgraph_to_data_uri(t['bw'], IGV_CHR, IGV_START, IGV_END)
    track_configs.append({
        'url':            uri,
        'name':           t['name'],
        'color':          t['color'],
        'format':         'bedgraph',
        'type':           'wig',
        'height':         40,
        'autoscaleGroup': 'mygroup',   # shared y-axis across tracks
        'autoscale':      True,
    })

tracks_json = json.dumps(track_configs, indent=2)

html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <script src="https://cdn.jsdelivr.net/npm/igv@3.5.2/dist/igv.min.js"></script>
  <style>body {{ margin:0; padding:8px; }} #igv {{ width:100%; }}</style>
</head>
<body>
  <div id="igv"></div>
  <script>
    igv.createBrowser(document.getElementById("igv"), {{
      genome: "hg38",
      locus:  "{IGV_LOCUS}",
      tracks: {tracks_json}
    }});
  </script>
</body>
</html>"""

# Optionally save standalone file
with open('code/scratch/browser.html', 'w') as f:
    f.write(html)

# Embed in notebook via srcdoc iframe
# IMPORTANT: must escape & → &amp; first, then " → &quot;
srcdoc = html.replace('&', '&amp;').replace('"', '&quot;')
display(HTML(f'<iframe srcdoc="{srcdoc}" style="width:100%;height:860px;border:1px solid #ddd;"></iframe>'))
```

### Key notes
- **`format: "bedgraph"` + `type: "wig"`** — igv.js requires both; bedgraph is the supported text format for embedded data URIs.
- **`autoscaleGroup`** — group all tracks under the same string to share a common y-axis scale.
- **HTML entity escaping order matters**: escape `&` before `"` when building `srcdoc`, or double-escaped entities will render incorrectly.
- **File size**: a ~44 kb region with 12 tracks is typically < 5 MB total HTML. Larger regions or more tracks may bloat the notebook.
- **Standalone HTML**: saving `html` directly to a `.html` file also works; open in any browser (CDN internet required).
- **`pyBigWig`** is available in `py_general`.
