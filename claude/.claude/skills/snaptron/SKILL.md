---
name: snaptron
description: Use this skill when the user asks to query Snaptron, search RNA-seq sample metadata, quantify gene expression from junction counts, fetch or save BigWig coverage files, visualize RNA-seq data in IGV, create IGV session files, analyze splice junctions, or work with the snaptron-mcp server. Triggers on keywords like "snaptron", "junction coverage", "RNA-seq expression", "srav2", "srav3h", "gtexv2", "bigwig", "rail_id", "MYT1L GAPDH ratio", "IGV session", "duffel.rail.bio".
---

# Snaptron Skill

Snaptron is a REST API for querying RNA-seq splice junctions and per-base coverage across large SRA/GTEx/TCGA datasets.

## MCP Server

**Location:** `~/Documents/repos_not_projects/snaptron-mcp/`
**Claude Desktop config:** `~/.claude/claude_desktop_config.json` (uv-based, stdio transport)

The MCP server is available in **Claude Desktop** but NOT automatically in Claude Code CLI sessions.
To use in CLI, run Python directly:

```bash
cd ~/Documents/repos_not_projects/snaptron-mcp
~/.local/bin/uv run python - << 'EOF'
import asyncio, sys; sys.path.insert(0, "src")
from snaptron_mcp import tools
asyncio.run(tools.search_samples("srav2", "HeLa"))
EOF
```

## Available Compilations

| Name | Description | Samples | Genome |
|------|-------------|---------|--------|
| `srav2` | SRA human (recount2) | 49K | hg38 |
| `srav3h` | SRA human (recount3) | 316K | hg38 |
| `gtexv2` | GTEx v8 | 17K | hg38 |
| `tcgav2` | TCGA | 11K | hg38 |
| `ccle` | Cancer Cell Line Encyclopedia | 1K | hg38 |
| `mouse` | SRA mouse | 23K | mm10 |

## Searchable Metadata Fields by Compilation

**srav2:** `cell_line`, `cell_type`, `tissue`, `description`, `study_title`, `study_accession`, `run_accession`, `sample_attribute`
**srav3h:** `study_title`, `study_abstract`, `study_description`, `sample_description`, `sample_name`, `sample_title`, `experiment_title`, `sample_acc`, `experiment_acc`, `submission_acc`, `library_strategy`, `platform_model` (note: no `cell_line`, `run_acc`, or `study_acc` fields — correct names are `sample_acc` and `study` isn't sfilter-searchable either)
**ccle/tcgav2:** use `primary_site`, `disease_type`

**CRITICAL — `wc -l` is unreliable for checking hits:** srav3h server errors return a ~12-line Python traceback as the response body. A `wc -l` of 12 means a server error, NOT 11 results. Always check the first bytes of the response to confirm it's a TSV header, not a traceback.

**srav3h data freeze:** recount3/srav3h was built in early 2021. Studies released after ~March 2021 are absent (e.g. SRP313438, released April 2021, is not in srav3h). Non-Illumina runs (e.g. BGISEQ) may also be excluded.

**Default to bulk RNA-seq only:** Unless the user explicitly asks otherwise, filter out single-cell (scRNA-seq), SMARTseq, and long-read datasets. In srav3h metadata, check `library_strategy` (should be `RNA-Seq`), `platform_model` (avoid PacBio/Oxford Nanopore), and `sample_attributes`/`study_title` (avoid terms like "single cell", "scRNA", "SMARTseq", "10x", "SMART-seq", "C1"). The SH-SY5Y samples used earlier (SRP161784) were actually SMARTseq single-cell — a mistake to avoid.

**Finding a study by accession in srav3h:** use `ids=` with known rail_ids, or use `sample_acc:SRS...` (valid Lucene field) if you know the SRS accession. `study_acc`, `run_acc`, and `study` are NOT valid sfilter fields despite appearing in the fields list.

## REST API Quick Reference

### Search Samples
```
GET https://snaptron.cs.jhu.edu/{compilation}/samples?sfilter={field}:{term}
# Example:
curl "https://snaptron.cs.jhu.edu/srav2/samples?sfilter=cell_line:HeLa"
# By rail_id:
curl "https://snaptron.cs.jhu.edu/srav2/samples?ids=35331,40981"
```

Returns TSV with header. srav2 returns ~970 HeLa samples. srav3h WERI not indexed (use "retinoblastoma" in study_title instead).

### Query Junctions
```
GET https://snaptron.cs.jhu.edu/{compilation}/snaptron?regions={gene_or_region}
# Optional: &sids={rail_id1},{rail_id2}  &rfilter=samples_count>:5  &rfilter=annotated:1
curl "https://snaptron.cs.jhu.edu/srav2/snaptron?regions=GAPDH"
curl "https://snaptron.cs.jhu.edu/srav2/snaptron?regions=chr12:6534517-6538374"
```

Junction TSV columns: snaptron_id, chromosome, start, end, length, strand, annotated, left_annotated, right_annotated, samples_count, coverage_sum, coverage_avg, coverage_median, **samples** (col 13 = `,rail_id:count,rail_id:count,...` — leading comma!)

### Per-Base Coverage (bases endpoint)
```
GET https://snaptron.cs.jhu.edu/{compilation}/bases?regions={gene_or_region}
curl "https://snaptron.cs.jhu.edu/srav2/bases?regions=GAPDH&sids=35331"
```

## MCP Tools (Python)

```python
from snaptron_mcp import tools

# Search samples
samples = await tools.search_samples("srav2", "HeLa")
# → list of dicts with rail_id, run_acc, cell_line, description, bigwig_file, etc.

# Query junctions for a gene or region
junctions = await tools.query_junctions("srav2", "MYT1L", sample_ids=[35331, 40981])
# → list of dicts: snaptron_id, chromosome, start, end, strand, samples_count, per_sample_counts

# Normalized expression: target/reference junction ratio per sample
result = await tools.get_normalized_expression("srav2", "MYT1L", "GAPDH", sample_ids=rail_ids)
# result = {"aggregate": {...}, "per_sample": [{"rail_id":..., "ratio":...}, ...]}

# Full metadata for specific rail_ids
meta = await tools.get_sample_metadata("srav2", [35331])

# BigWig URLs (relative filenames in srav2 — need to build full URL; see below)
bw = await tools.get_bigwig_urls("srav2", [35331])

# Fetch per-base coverage from remote BigWig
cov = tools.fetch_bigwig_region("https://duffel.rail.bio/recount/SRP019946/bw/SRR792842.bw", "chr12:6534517-6538374")
# → {"coverage": [...], "length": 3858, ...}
```

## BigWig URL Construction (srav2)

The `bigwig_file` field in srav2 metadata is just the filename (e.g. `SRR792842.bw`).
Full URL pattern: `https://duffel.rail.bio/recount/{study_accession}/bw/{run_accession}.bw`

Get `study_accession` from the `study_accession` column in sample metadata.

## Key Genomic Coordinates (hg38)

| Gene | Region |
|------|--------|
| GAPDH | chr12:6534517-6538374 |
| MYT1L | chr2:1779636-2219609 (large gene) |

## Typical Workflow

1. `search_samples(compilation, term)` → get rail_ids
2. `get_normalized_expression(compilation, target, reference, sample_ids)` → expression ratios
3. `get_sample_metadata(compilation, [rail_id])` → get `study_accession` + `run_accession`
4. Build bigwig URL: `https://duffel.rail.bio/recount/{study_acc}/bw/{run_acc}.bw`
5. `fetch_bigwig_region(url, "chrN:start-end")` → per-base coverage list
6. Save as BigWig with pyBigWig (see below), or save as JSON

## Saving Coverage as a BigWig File

pyBigWig can write BigWig files locally. Requires chromosome sizes from the source file:

```python
import pyBigWig as pbw

# Get chrom sizes from source
src = pbw.open(bigwig_url)
chrom_sizes = src.chroms()
src.close()

# Fetch coverage
cov = tools.fetch_bigwig_region(bigwig_url, "chr12:6534517-6538374")
chrom = cov["chromosome"]
start_0 = cov["start_0based"]
end = cov["end"]
coverage = cov["coverage"]

# Write BigWig
bw_out = pbw.open("output.bw", "w")
bw_out.addHeader([(chrom, chrom_sizes[chrom])])
starts = list(range(start_0, end))
bw_out.addEntries(
    [chrom] * len(starts),
    starts,
    ends=[s + 1 for s in starts],
    values=[float(v) for v in coverage],
)
bw_out.close()
```

## IGV Session Files

IGV can stream BigWigs directly from duffel.rail.bio URLs — no local file needed.
pyBigWig and IGV both use HTTP range requests, so only the visible region is downloaded.

IGV session XML template:
```xml
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<Session genome="hg38" locus="chr12:6534517-6538374" version="8">
    <Resources>
        <Resource path="https://duffel.rail.bio/recount/{study_accession}/bw/{run_accession}.bw"/>
    </Resources>
    <Panel height="200" name="DataPanel" width="1200">
        <Track id="https://duffel.rail.bio/recount/{study_accession}/bw/{run_accession}.bw"
               name="Sample label"
               color="0,0,178"
               autoscale="true"
               type="wig"
               windowFunction="mean"/>
    </Panel>
</Session>
```

Open in IGV via **File → Open Session**. Add multiple `<Resource>` and `<Track>` blocks to compare samples.

## TPM from BigWig + featureCounts metadata (srav3h)

srav3h has no per-gene featureCounts counts via the API — only aggregate totals. Approximate TPM
by combining BigWig exon coverage with per-sample featureCounts totals from metadata:

```python
import httpx, csv, io, pyBigWig

# 1. Fetch exons from Ensembl REST (returns merged exon union across all transcripts)
async def get_exons(gene_symbol):
    r = await httpx.AsyncClient().get(
        f"https://rest.ensembl.org/lookup/symbol/homo_sapiens/{gene_symbol}",
        params={"expand": 1, "content-type": "application/json"})
    data = r.json()
    chrom = "chr" + data["seq_region_name"]
    exon_set = set()
    for tx in data.get("Transcript", []):
        for ex in tx.get("Exon", []):
            exon_set.add((ex["start"] - 1, ex["end"]))  # 0-based half-open
    # merge overlapping
    merged = []
    for s, e in sorted(exon_set):
        if merged and s <= merged[-1][1]: merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else: merged.append([s, e])
    return chrom, merged, sum(e-s for s,e in merged)

# 2. Fetch metadata directly (do NOT use MCP client for srav3h ids= queries — pandas
#    creates a broken MultiIndex; parse the TSV manually instead)
async def fetch_srav3h_meta(rail_ids):
    ids_str = ",".join(str(r) for r in rail_ids)
    r = await httpx.AsyncClient(timeout=60).get(
        f"https://snaptron.cs.jhu.edu/srav3h/samples?ids={ids_str}")
    reader = csv.reader(io.StringIO(r.text), delimiter='\t')
    header = next(reader)
    meta = {}
    for row in reader:
        d = dict(zip(header, row))
        try: rid = int(d["rail_id"])
        except: continue
        meta[rid] = {
            "avg_read_len": float(d.get("star.average_input_read_length") or 50),
            "fc_assigned":  float(d.get("gene_fc_count_all.assigned") or 0),
            "bc_auc":       float(d.get("bc_auc.unique_reads_annotated_bases") or 0),
        }
    return meta

# 3. Sum BigWig coverage over exons
def cov_sum(bw_url, chrom, exons):
    bw = pyBigWig.open(bw_url)
    total = sum(
        sum(v for v in (bw.values(s, e) or []) if v is not None)
        for s, e in exons)
    bw.close()
    return total

# 4. TPM
#   reads_gene  = cov_sum / avg_read_len
#   RPK         = reads_gene / (exon_bp / 1000)
#   TPM         = RPK / (fc_assigned / 1e6)
```

**Key srav3h metadata fields for expression:**
- `star.average_input_read_length` — read length (NOT `avg_len`, which is unpopulated)
- `gene_fc_count_all.assigned` — total reads featureCounts assigned to genes (TPM denominator)
- `bc_auc.unique_reads_annotated_bases` — total base coverage over annotated regions (alternative denominator)

**srav3h recount3 BigWig URL pattern:**
```
https://duffel.rail.bio/recount3/human/data_sources/sra/base_sums/{study[-2:]}/{study}/{run[-2:]}/sra.base_sums.{study}_{run}.ALL.bw
```
e.g. study=SRP161784, run=SRR7830282 → `.../84/SRP161784/82/sra.base_sums.SRP161784_SRR7830282.ALL.bw`

**CRITICAL: Do NOT use `client.fetch_samples()` for srav3h `ids=` queries** — pandas creates a broken MultiIndex from the response. Parse TSV with `csv.reader` directly (see above).

**srav3h has no `bigwig_file` field** (unlike srav2). Must construct URL from `study_acc` + `run_acc`.

## Known Results / Gotchas

- **HeLa in srav2**: ~1122 samples found via `cell_line:HeLa` or `description:HeLa`
- **srav3h**: no `cell_line` field — use `study_title`, `study_abstract`, or `sample_description`
- **WERI cells**: not indexed in srav2/srav3h; use `study_title:retinoblastoma` to find related samples
- **Junction samples column**: always starts with a leading comma → parse with `str.split(",")`, skip empty tokens
- **srav2 bigwig field**: relative filename only; must build full duffel.rail.bio URL using study_accession
- **MYT1L/GAPDH ratio in HeLa** (srav2, 50 samples): mean≈0.000318, max≈0.00641 (MYT1L barely expressed in HeLa)
- GAPDH coverage at chr12:6534517-6538374 in SRR792842 (HeLa S3): 3858 bases, max cov ≈9158 reads
- BigWig saved: `~/Documents/scratch/gapdh_coverage_rail35331_SRR792842.bw` (3858 bases, 18KB)
- IGV session saved: `~/Documents/scratch/igv_gapdh_hela_SRR792842.xml`
