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
