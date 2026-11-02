---
name: igv-tracks
description: Visualize genomic signal tracks, work with UCSC Genome Browser exports, or set up genome browser views. Invoke when plotting signal over genomic regions, using genometracks_utils, working with bigWig/BED/BAM tracks, or exporting from UCSC browser.
---

# Genome Track Visualization

Load the reference for the requested output:

| Task | Reference |
|---|---|
| UCSC signal over BED12 blocks using `my_utils` | [Block signal](references/block-signal.md) |
| Static figures from BAM/bigWig/BED/GTF | [pyGenomeTracks](references/static-tracks.md) |
| Desktop IGV session XML and Mac-mounted HPC paths | [Desktop IGV](references/desktop-igv.md) |
| Interactive browser in a Quarto notebook | Follow the workflow below |

Use `agent-plots` when saving plots or tables. Notebook prose follows `new-notebook`.

## Embedded igv.js workflow

1. Read [embedding helpers](references/embedding.md). Coverage is embedded as gzip/base64
   bedgraph; igv.js loads from CDN and reference sequence requires internet. Do not use
   `igv-reports` for RNA-seq coverage.
2. Choose [single locus](references/single-locus.md) or
   [multiple loci with dropdown](references/multi-locus.md).
3. For every browser, apply [separate track labels](references/track-labels.md) and
   [visible loading errors](references/track-loading.md).
4. Add only the features needed:
   - [BED annotations](references/bed-annotations.md)
   - [Per-feature colors and legends](references/feature-colors.md)
   - [Individual/group autoscale toggle](references/autoscale.md)
   - [Regions of interest](references/regions-of-interest.md)
   - [Feature stepper](references/feature-stepper.md)
5. Inspect the rendered browser using the verification instructions in the track-labels
   reference. For failures or inline transcript CDS/UTR rendering, read
   [troubleshooting](references/troubleshooting.md).

Recipes were tested with igv.js 3.5.2. Check the relevant official API documentation before
using untested options; do not infer config shapes from neighboring options.
