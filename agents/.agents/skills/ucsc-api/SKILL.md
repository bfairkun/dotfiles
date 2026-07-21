---
name: ucsc-api
description: Query the UCSC Genome Browser REST API for DNA sequences, gene annotations, track data, schemas, and assembly metadata. Invoke when fetching reference sequence, looking up gene coordinates, pulling track data (bigWig/bigBed/genePred/wiggle), enumerating tracks/chromosomes, or searching public hubs without downloading whole files.
argument-hint: "[genome, gene/region, track name, or task]"
---

# UCSC Genome Browser REST API

Public, unauthenticated JSON API. Docs: https://genome.ucsc.edu/goldenpath/help/api.html

- **Base URL:** `https://api.genome.ucsc.edu/`
- **Param separator:** `;` or `&` both work
- **Rate limit:** ~1 request/sec (per docs; designed for *small* lookups, not bulk)
- **Coordinates:** 0-based half-open (`[start, end)`) — same as BED
- **Output:** JSON. Each response includes `downloadTime`, `dataTime`, the echoed params, and the payload keyed by track/category name.
- **Errors:** non-2xx → `{"error": "...", "statusCode": 400, "statusMessage": "Bad Request"}` (still JSON).

## When to use this vs. local files

Use the API for:
- One-off sequence pulls (no need to download/index a 2bit)
- Looking up gene/transcript coordinates from a symbol
- Discovering what tracks exist for a genome / what columns a track has
- Pulling small slices of public tracks (phyloP, gnomAD, ClinVar, etc.) without `bigBedToBed`

**Do NOT use** for bulk extraction — download the underlying `.bw`/`.bb`/`.2bit` instead. The API enforces `maxItemsOutput` (default 1M, max 1M).

---

## Endpoints (quick reference)

### Listing — `/list/...`
| Endpoint | Purpose | Required |
|---|---|---|
| `/list/ucscGenomes` | All UCSC-hosted assemblies | — |
| `/list/genarkGenomes` | GenArk assembly-hub genomes | — |
| `/list/publicHubs` | All registered public hubs | — |
| `/list/hubGenomes` | Genomes inside a hub | `hubUrl=` |
| `/list/tracks` | Tracks for genome (incl. composite containers) | `genome=` |
| `/list/chromosomes` | Chromosomes + sizes | `genome=` (optional `track=`) |
| `/list/schema` | Column types/descriptions for a track | `genome=`, `track=` |
| `/list/files` | Downloadable files for a genome | `genome=` |
| `/findGenome` | Search for genome by keyword | `q=` |

Add `trackLeavesOnly=1` to `/list/tracks` to flatten composites (much more useful — hg38 goes from 395 → 23,734 tracks).

### Data — `/getData/...`
| Endpoint | Purpose | Required |
|---|---|---|
| `/getData/sequence` | DNA from assembly | `genome=`, `chrom=` (+ optional `start`/`end`, `revComp=1`) |
| `/getData/track` | Records from a track | `genome=`, `track=` (+ optional `chrom`/`start`/`end`) |

### Search — `/search`
Resolves a free-text query (gene symbol, rsID, accession) to genomic positions across `trackDb` / `publicHubs` / `helpDocs`.

Required: `search=`, `genome=`. Optional: `categories=trackDb|publicHubs|helpDocs`.

---

## Recipes

### 1. Get DNA sequence

```bash
# Forward strand, BED-style coordinates
curl -s "https://api.genome.ucsc.edu/getData/sequence?genome=hg38;chrom=chr7;start=155799979;end=155799990"
# → {"dna": "ATGCTCCCTCT..."}

# Reverse complement
curl -s "https://api.genome.ucsc.edu/getData/sequence?genome=hg38;chrom=chr7;start=155799979;end=155799990;revComp=1"

# Whole chromosome (no start/end) — works for small contigs only; large chroms may be refused
curl -s "https://api.genome.ucsc.edu/getData/sequence?genome=hg38;chrom=chrM"
```

### 2. Gene symbol → coordinates

`/search` returns positions across many tracks; pick the row from `knownGene` or `mane` for the canonical transcript.

```bash
curl -s "https://api.genome.ucsc.edu/search?search=BRCA1&genome=hg38" \
  | python3 -c "
import json, sys
d = json.load(sys.stdin)
for pm in d['positionMatches']:
    if pm['trackName'] in ('mane', 'knownGene'):
        for m in pm['matches']:
            if m.get('canonical'):
                print(pm['trackName'], m['posName'], m['position'])
"
# mane    BRCA1 (NM_007294.4 / ENST00000357654.9)    chr17:43044295-43125364
# knownGene BRCA1 (ENST00000357654.9)               chr17:43044295-43125364
```

`position` is **1-based inclusive** (UCSC browser format), unlike everything else in the API. Convert to BED with `start - 1`.

### 3. Gene structure (exons, CDS)

```bash
# All NCBI RefSeq transcripts overlapping a region
curl -s "https://api.genome.ucsc.edu/getData/track?genome=hg38;track=ncbiRefSeq;chrom=chr17;start=43044294;end=43125364"
```

Returns `genePred` records with `txStart`, `txEnd`, `cdsStart`, `cdsEnd`, `exonStarts`, `exonEnds` (comma-separated, trailing comma), `name` (RefSeq ID), `name2` (gene symbol).

For Gencode/Ensembl IDs use `track=knownGene` (returns `bigGenePred`, includes `geneName`, `transcriptType`, `tag` (e.g. `MANE_Select`, `Ensembl_canonical`)).

### 4. Track signal (bigWig / wiggle)

```bash
# phyloP conservation at base resolution
curl -s "https://api.genome.ucsc.edu/getData/track?genome=hg38;track=phyloP470wayBW;chrom=chr7;start=155799979;end=155800010"
```

Returns one record per position: `{chrom, start, end, value}`. For BigWig response also includes `bigDataUrl` — useful if you want to switch to `pyBigWig` for bulk extraction.

### 5. Discover what tracks exist

```bash
# Flattened list (use this — composite containers are useless without leaves)
curl -s "https://api.genome.ucsc.edu/list/tracks?genome=hg38;trackLeavesOnly=1" \
  | python3 -c "
import json, sys
tracks = json.load(sys.stdin)['hg38']
# Filter by keyword
for k, v in tracks.items():
    if 'gnomad' in k.lower():
        print(f\"{k:30s} {v.get('type','?'):20s} {v.get('shortLabel','')}\")
"
```

Each track dict has: `type` (e.g. `bigWig`, `bigBed 9 +`, `wig`, `bigGenePred`, `vcfTabix`), `shortLabel`, `longLabel`, `group`, optionally `bigDataUrl` for hub tracks.

### 6. Track schema (what columns mean)

```bash
curl -s "https://api.genome.ucsc.edu/list/schema?genome=hg38;track=knownGene" \
  | python3 -c "
import json, sys
for c in json.load(sys.stdin)['columnTypes']:
    print(f\"{c['name']:20s} {c['jsonType']:8s} {c['description']}\")
"
```

### 7. Chromosome sizes

```bash
curl -s "https://api.genome.ucsc.edu/list/chromosomes?genome=hg38" \
  | python3 -c "
import json, sys
chroms = json.load(sys.stdin)['chromosomes']
# Just the main 'chr1'..'chrY','chrM'
for k in sorted(chroms):
    if '_' not in k:
        print(k, chroms[k])
"
```

### 8. Public assembly hubs (non-UCSC genomes)

```bash
# All registered hubs
curl -s "https://api.genome.ucsc.edu/list/publicHubs"

# Genomes in a specific hub
curl -s "https://api.genome.ucsc.edu/list/hubGenomes?hubUrl=http://hgdownload.gi.ucsc.edu/hubs/mouseStrains/hub.txt"

# Tracks in a hub genome (needs both hubUrl and genome)
curl -s "https://api.genome.ucsc.edu/list/tracks?hubUrl=...;genome=129S1_SvImJ"
```

### 9. Find hubs that aren't in the public registry

`/list/publicHubs` only returns ~120 hubs registered with UCSC — many useful datasets (especially single-cell) host their own and aren't listed. Two reliable workarounds:

**UCSC Cell Browser catalog** — every dataset has a `dataset.json` at `https://cells.ucsc.edu/<path>/dataset.json`. The root `cells.ucsc.edu/dataset.json` lists collections; walk `datasets[]` children until `isCollection` is None. Leaf datasets often have a `hubUrl` field pointing straight to a `trackDb.txt` or `hub.txt`. Example: `cells.ucsc.edu/allen-celltypes/human-cortex/m1/dataset.json` → Allen Brain M1 snRNA-seq hub (148 per-cell-type CPM bigWigs, 20 broad subclasses + 128 fine clusters): `https://human-m1-rna-hub.s3-us-west-2.amazonaws.com/trackDb.txt`.

**Skip the API for bulk bigWig pulls** — once you have a `bigDataUrl` (from any trackDb stanza or from `/list/tracks`'s `bigDataUrl` field), `pyBigWig.open(url)` works directly over HTTPS. Faster than `/getData/track`, no `maxItemsOutput` cap, and presigned-S3 URLs (common for community-hosted hubs) work as-is.

### 9. Find a genome you don't know the assembly name for

```bash
curl -s "https://api.genome.ucsc.edu/findGenome?q=naked+mole+rat"
# Add statsOnly=1 to just get a count
```

---

## Python helper pattern

```python
import requests

API = "https://api.genome.ucsc.edu"

def ucsc(endpoint, **params):
    """GET endpoint, return parsed JSON. Raises on HTTP error."""
    r = requests.get(f"{API}/{endpoint.lstrip('/')}", params=params, timeout=30)
    r.raise_for_status()
    j = r.json()
    if "error" in j:
        raise RuntimeError(f"UCSC API: {j['error']}")
    return j

# Examples
seq = ucsc("getData/sequence", genome="hg38", chrom="chr17",
           start=43044295, end=43044395)["dna"]

exons = ucsc("getData/track", genome="hg38", track="ncbiRefSeq",
             chrom="chr17", start=43044294, end=43125364)["ncbiRefSeq"]

phylop = ucsc("getData/track", genome="hg38", track="phyloP470wayBW",
              chrom="chr7", start=155799979, end=155800010)["phyloP470wayBW"]
```

For batched lookups, sleep ~1 sec between requests. For >100 positions, **don't** loop the API — download the underlying `.bw`/`.bb` once and use `pyBigWig`/`pybedtools`.

---

## Common hg38 track names (cheatsheet)

| Track | Type | What it is |
|---|---|---|
| `knownGene` | bigGenePred | Gencode (canonical, MANE tags) |
| `ncbiRefSeq` | genePred | RefSeq transcripts |
| `mane` | bigBed | MANE Select transcripts only |
| `hgnc` | bigBed | HGNC gene loci |
| `gold` | bed | Assembly gold path / contigs |
| `phyloP100way` / `phyloP470wayBW` | wig / bigWig | Conservation (multiz) |
| `phastCons100way` | wig | PhastCons conservation |
| `dbSnp155Composite` | bed | dbSNP 155 (composite — use leaves) |
| `gnomAD*` (many) | bigWig/bigBed | gnomAD allele freqs |
| `clinvar*` | bigBed | ClinVar variants |
| `rmsk` | rmsk | RepeatMasker |
| `cytoBand` | bed | Cytogenetic bands |

Use `/list/tracks?genome=hg38;trackLeavesOnly=1` + grep when you don't know the exact name.

---

## Gotchas

- **Coordinates are 0-based half-open** (BED), *except* the string returned in `/search` `position` field (`chr1:1234-5678`), which is 1-based inclusive (UCSC browser convention).
- `/list/tracks` without `trackLeavesOnly=1` includes composite/super-track containers that have no data themselves — querying them returns "can not find track".
- The `;` separator is the docs' convention; `&` also works. Either is fine.
- `maxItemsOutput` caps at 1,000,000 (use `-1` for max). If results are truncated you'll get fewer records than expected with no explicit error — check by re-querying a smaller window.
- Track-supported types for `/getData/track`: `bed`, `bigBed`, `bigWig`, `wiggle`, `genePred`, `bigGenePred`, `psl`, `bigPsl`, `chain`, `bigChain`, `narrowPeak`, `bigNarrowPeak`, `interact`, `rmsk`, `pgSnp`, `gvf`, `peptideMapping`, `altGraphX`, `barChart`, `bigBarChart`, `bigLolly`, `bigMethyl`, `bigMaf`, `netAlign`, `expRatio`, `factorSource`, `ctgPos`. **No VCF/BAM** — for those, find the `bigDataUrl` in the track listing and pull the file directly.
- Mirror/local installs use a different base: `https://<host>/cgi-bin/hubApi/` instead of `api.genome.ucsc.edu/`.
