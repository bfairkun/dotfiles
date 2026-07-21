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
loads from CDN (internet required for the reference genome sequence).

**Do NOT use `igv-reports`** for RNA-seq coverage — it is a variant-centric tool that does not
support bigwig tracks properly.

### Core helpers (always include these)

```python
import pyBigWig, json
from base64 import b64encode
from gzip import compress
from IPython.display import display, HTML

# Chromosome sort key — used whenever coordinate-sorting is required
_CHROM_KEY = {f'chr{i}': i for i in range(1, 23)}
_CHROM_KEY.update({'chrX': 23, 'chrY': 24, 'chrM': 25})

def bw_uri(bw_path, chrom, start, end):
    """Single-region bigwig → gzip bedgraph data URI."""
    bw = pyBigWig.open(bw_path)
    ivs = bw.intervals(chrom, start, end) or []
    bw.close()
    text = ''.join(f'{chrom}\t{s}\t{e}\t{v:.4f}\n' for s, e, v in ivs)
    return f'data:application/gzip;base64,{b64encode(compress(text.encode())).decode()}'

def bed_uri(rows):
    """BED6 rows → gzip data URI. rows = list of (chrom,start,end,name,score,strand)."""
    rows = sorted(rows, key=lambda x: (_CHROM_KEY.get(x[0], 99), x[1]))
    text = '\n'.join(f'{c}\t{s}\t{e}\t{n}\t{sc}\t{st}' for c,s,e,n,sc,st in rows)
    return f'data:application/gzip;base64,{b64encode(compress((text+"\n").encode())).decode()}'

def embed_igv(html, height=400):
    """Embed an igv.js HTML page in a notebook iframe via srcdoc."""
    srcdoc = html.replace('&', '&amp;').replace('"', '&quot;')
    display(HTML(f'<iframe srcdoc="{srcdoc}" '
                 f'style="width:100%;height:{height}px;border:1px solid #ccc;border-radius:4px;"></iframe>'))
```

---

### Recipe 1 — Single locus, wig tracks only

```python
CHR, START, END = 'chr6', 106280000, 106325000

# tracks_spec: list of (bw_path, label, hex_color)
tracks_spec = [
    ('path/to/sample1.bw', 'Sample 1', '#888888'),
    ('path/to/sample2.bw', 'Sample 2', '#E2693F'),
]

track_cfgs = [
    {'url': bw_uri(bw, CHR, START, END), 'name': name, 'color': color,
     'format': 'bedgraph', 'type': 'wig', 'height': 60,
     'autoscale': True,
     # 'autoscaleGroup': 'shared',  # uncomment to lock y-axes together
     }
    for bw, name, color in tracks_spec
]

html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/igv@3.5.2/dist/igv.min.js"></script>
<style>body{{margin:0;padding:6px}} #igv{{width:100%}}</style>
</head><body><div id="igv"></div>
<script>
igv.createBrowser(document.getElementById("igv"), {{
  genome: "hg38", locus: "{CHR}:{START}-{END}",
  tracks: {json.dumps(track_cfgs)}
}});
</script></body></html>"""

embed_igv(html, height=380)
```

---

### Recipe 2 — Multi-locus with jump-to dropdown

Embed data for **many regions** in one bedgraph per track; add a dropdown to navigate.

**Critical**: bedgraph must be **coordinate-sorted** or igv.js shows blank tracks when
navigating away from the initial locus.

```python
def multi_bw_uri(bw_path, regions, pad=0):
    """
    regions: list of (chrom, start, end) tuples.
    Extracts data for each region ± pad, sorts globally, returns data URI.
    """
    bw = pyBigWig.open(bw_path)
    rows = []
    for chrom, s, e in regions:
        s, e = max(0, s - pad), e + pad
        try:
            for iv_s, iv_e, val in (bw.intervals(chrom, s, e) or []):
                if val and val == val:
                    rows.append((chrom, iv_s, iv_e, val))
        except Exception:
            pass
    bw.close()
    rows.sort(key=lambda x: (_CHROM_KEY.get(x[0], 99), x[1]))
    text = '\n'.join(f'{c}\t{s}\t{e}\t{v:.4f}' for c, s, e, v in rows)
    return f'data:application/gzip;base64,{b64encode(compress(text.encode())).decode()}'

# Build loci list — one entry per item in the dropdown
PAD = 2000
regions   = [(chrom1, start1, end1), (chrom2, start2, end2), ...]  # your regions
loci_names = ['Gene A', 'Gene B', ...]                               # dropdown labels

igv_loci = [
    {'name': name, 'locus': f'{c}:{max(0,s-PAD)}-{e+PAD}'}
    for name, (c, s, e) in zip(loci_names, regions)
]

track_cfgs = [
    {'url': multi_bw_uri(bw, regions, PAD), 'name': name, 'color': color,
     'format': 'bedgraph', 'type': 'wig', 'height': 60, 'autoscale': True}
    for bw, name, color in tracks_spec
]

html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/igv@3.5.2/dist/igv.min.js"></script>
<style>body{{margin:0;padding:8px;font-family:sans-serif}} #igv{{width:100%}}
select{{font-size:13px;padding:3px 8px;margin-left:6px}}</style>
</head><body>
<div style="margin-bottom:8px">
  <b>Jump to:</b>
  <select id="sel">
    {''.join(f'<option value="{i}">{l["name"]}</option>' for i,l in enumerate(igv_loci))}
  </select>
</div>
<div id="igv"></div>
<script>
var loci = {json.dumps(igv_loci)};
igv.createBrowser(document.getElementById("igv"), {{
  genome: "hg38", locus: loci[0].locus,
  tracks: {json.dumps(track_cfgs)}
}}).then(function(b) {{
  document.getElementById("sel").addEventListener("change", function() {{
    var l = loci[parseInt(this.value)];
    var parts = l.locus.split(':');
    var se = parts[1].split('-');
    b.goto(parts[0], parseInt(se[0]), parseInt(se[1]));
  }});
}});
</script>
</body></html>"""

embed_igv(html, height=450)
```

---

### Recipe 3 — Adding BED annotation tracks

Any BED6 data can be added alongside wig tracks. Common uses: intervals of interest,
tabix-indexed annotation files filtered to the relevant regions.

```python
import pysam

def tabix_bed_uri(tabix_path, regions, pad=0, filter_fn=None):
    """
    Fetch BED records from a tabix-indexed file over multiple regions,
    optionally filter, deduplicate, and return a sorted data URI.
    filter_fn: callable(fields_list) → bool, or None to keep all records.
    """
    tbx = pysam.TabixFile(tabix_path)
    rows, seen = [], set()
    for chrom, s, e in regions:
        s_q, e_q = max(0, s - pad), e + pad
        try:
            for rec in tbx.fetch(chrom, s_q, e_q):
                if rec in seen: continue
                f = rec.split('\t')
                if filter_fn and not filter_fn(f): continue
                seen.add(rec)
                rows.append((f[0], int(f[1]), int(f[2]),
                             f[3] if len(f) > 3 else '.',
                             f[4] if len(f) > 4 else '0',
                             f[5] if len(f) > 5 else '.'))
        except Exception:
            pass
    tbx.close()
    return bed_uri(rows)

# Example: BED track from a tabix file, keeping only records with score > 5
bed_track = {
    'url': tabix_bed_uri('annotations.bed.gz', regions, pad=500,
                          filter_fn=lambda f: float(f[4]) > 5),
    'name': 'Annotations', 'format': 'bed', 'type': 'bed',
    'height': 40, 'color': '#9B59B6', 'displayMode': 'EXPANDED',
}

# Or from a simple Python list:
my_intervals = [('chr1', 1000, 2000, 'featureA', 100, '+'),
                ('chr1', 3000, 4000, 'featureB', 200, '-')]
bed_track2 = {
    'url': bed_uri(my_intervals), 'name': 'My intervals',
    'format': 'bed', 'type': 'bed', 'height': 40, 'displayMode': 'EXPANDED',
}
```

---

### Recipe 4 — Toggle between individual and group autoscale

igv.js has no built-in UI button for this. Add one by mutating `track.autoscaleGroup` on all
wig tracks and calling `browser.updateViews()`.

```python
html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/igv@3.5.2/dist/igv.min.js"></script>
<style>
  body{{margin:0;padding:8px;font-family:sans-serif}}
  #igv{{width:100%}}
  #controls{{background:#f5f5f5;border:1px solid #ddd;border-radius:4px;
             padding:8px 12px;margin-bottom:8px;display:flex;align-items:center;gap:12px}}
  button{{font-size:13px;padding:5px 14px;cursor:pointer;
          border:1px solid #aaa;border-radius:3px;background:#fff}}
  button:hover{{background:#eee}}
  #mode{{font-size:12px;color:#555;font-style:italic}}
</style>
</head><body>
<div id="controls">
  <b>Autoscale:</b>
  <button id="togBtn">Switch to group scale</button>
  <span id="mode">currently: individual (each track scales independently)</span>
</div>
<div id="igv"></div>
<script>
var groupMode = false;
igv.createBrowser(document.getElementById("igv"), {{
  genome: "hg38", locus: "{CHR}:{START}-{END}",
  tracks: {json.dumps(track_cfgs)}
}}).then(function(b) {{
  document.getElementById("togBtn").addEventListener("click", function() {{
    groupMode = !groupMode;
    b.trackViews.forEach(function(tv) {{
      var t = tv.track;
      if (t.type === 'wig') {{
        t.autoscaleGroup = groupMode ? 'shared' : undefined;
        t.autoscale = true;
      }}
    }});
    b.updateViews();
    this.textContent = groupMode ? 'Switch to individual scale' : 'Switch to group scale';
    document.getElementById("mode").textContent = groupMode
      ? 'currently: group (all tracks share the same y-axis)'
      : 'currently: individual (each track scales independently)';
  }});
}});
</script>
</body></html>"""

embed_igv(html, height=400)
```

The toggle works by:
1. Setting `track.autoscaleGroup = 'shared'` on every wig track (group mode) or `undefined` (individual)
2. Calling `browser.updateViews()` to force a redraw
3. `b.trackViews` is the array of TrackView objects; `.track` is the underlying track

---

### Recipe 5 — Highlighting regions of interest (ROI)

To mark candidate regions with a shaded vertical band spanning all tracks (e.g. to call
out a candidate ASO window), use the browser-level `roi` config option.

**The `roi` value is an array of named ROI *sets*, each with its own `color` and a
`features` array of `{chr, start, end}` objects — it is NOT a flat array of
`{chr, start, end, color, name}` region objects.** Passing a flat array silently
produces no visible highlight (no error, no console warning) — this is the most likely
mistake to make here, since every other igv.js list-valued config option (`tracks`,
loci lists in Recipe 2) *is* a flat array of one-object-per-item, so ROI's nested
"named set containing a features list" shape breaks that pattern.

```python
roi_sets = [
    {
        "name": "Candidate 1",
        "color": "rgba(230,80,80,0.25)",  # translucent — this is the band's fill
        "features": [
            {"chr": "chr2", "start": 148_513_420, "end": 148_513_490},
        ],
    },
    {
        "name": "Candidate 2",
        "color": "rgba(80,140,230,0.25)",
        "features": [
            {"chr": "chr2", "start": 148_516_930, "end": 148_517_000},
        ],
    },
]

html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/igv@3.5.2/dist/igv.min.js"></script>
<style>body{{margin:0;padding:6px}} #igv{{width:100%}}</style>
</head><body><div id="igv"></div>
<script>
igv.createBrowser(document.getElementById("igv"), {{
  genome: "hg38", locus: "{CHR}:{START}-{END}",
  roi: {json.dumps(roi_sets)},
  tracks: {json.dumps(track_cfgs)}
}});
</script></body></html>"""

embed_igv(html, height=400)
```

A single ROI set can hold multiple non-contiguous `features` (e.g. several exons that
are all part of one logical region) — group by set when they should share one
name/color, not by individual feature.

Source: [igv.js wiki — Regions of Interest](https://github.com/igvteam/igv.js/wiki/Regions-of-Interest).
Before using any igv.js config option that hasn't already been recipe-tested in this
skill, check the wiki page for that feature rather than inferring the shape from
adjacent options — igv.js's config surface is not internally consistent about
flat-list vs. named-set shapes.

---

### Gotchas and API notes

| Issue | Fix |
|-------|-----|
| Blank tracks after dropdown navigation | Bedgraph data must be coordinate-sorted; use `_CHROM_KEY` sort |
| Dropdown `browser.search(str)` doesn't navigate | Use `browser.goto(chr, start, end)` instead — `search()` is unreliable with embedded data URIs in 3.5.2 |
| `type: "junction"` invisible | Use `type: "bed"` — junction arc rendering fails silently with data URI sources in 3.5.2 |
| `&` or `"` in srcdoc breaks HTML | Escape in order: `html.replace('&','&amp;').replace('"','&quot;')` |
| Group vs individual y-axis | Use Recipe 4 toggle button; `autoscaleGroup: "shared"` at init also works |
| ROI band not visible, no error | `roi` must be named sets with a `features` list (Recipe 5) — a flat list of region objects is silently ignored |
