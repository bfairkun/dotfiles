---
name: ensembl-api
description: Query the Ensembl REST API for HGVS conversion, variant effects (VEP), gene/transcript lookup, sequences, phenotype annotations, coordinate mapping (liftover, cDNA/CDS/protein → genomic), overlap, and cross-references. Invoke when converting HGVS notation, predicting variant consequences, looking up genes, lifting over coordinates between assemblies, or finding disease phenotype associations.
argument-hint: "[task: hgvs, vep, lookup, sequence, mapping, phenotype, overlap, xrefs, homology]"
---

# Ensembl REST API

Public JSON API. Docs: https://rest.ensembl.org

- **Base URL (GRCh38 / hg38):** `https://rest.ensembl.org`
- **Base URL (GRCh37 / hg19):** `https://grch37.rest.ensembl.org`
- **Auth:** None required
- **Rate limit:** 15 req/sec, ~55,000/hour. Add `time.sleep(0.1)` between loop iterations.
- **Coordinates:** **1-based inclusive** (unlike UCSC 0-based half-open). Region format: `16:28487761..28487764` or `16:28487761-28487764` (both work); append `:1` or `:-1` for strand.
- **Species slug:** `homo_sapiens`, `mus_musculus`, `danio_rerio`, etc. Short forms (`human`, `mouse`) also accepted.

---

## Python helper

```python
import urllib.request, urllib.parse, json

ENSEMBL    = "https://rest.ensembl.org"
ENSEMBL_37 = "https://grch37.rest.ensembl.org"

def ensembl_get(path, base=ENSEMBL, **params):
    params.setdefault("content-type", "application/json")
    url = f"{base}{path}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url) as r:
        return json.loads(r.read())

def ensembl_post(path, payload, base=ENSEMBL, **params):
    params.setdefault("content-type", "application/json")
    url = f"{base}{path}?{urllib.parse.urlencode(params)}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data,
          headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())
```

---

## 1. HGVS conversion — `variant_recoder`

Converts any HGVS (c., g., n., p.), rsID, or SPDI to all equivalent representations.

```python
hgvs = "NM_001042432.2:c.295-23_295-20delCTCA"
result = ensembl_get(f"/variant_recoder/homo_sapiens/{urllib.parse.quote(hgvs)}")

for entry in result:
    for allele, data in entry.items():
        print("hgvsg:",  data.get("hgvsg", []))   # genomic (NC_ accession)
        print("hgvsc:",  data.get("hgvsc", []))   # all transcript c. forms
        print("hgvsp:",  data.get("hgvsp", []))   # protein p. forms
        print("spdi:",   data.get("spdi",  []))   # VCF-normalized SPDI
        print("id:",     data.get("id",    []))   # rsIDs if known

# Batch POST (up to ~200)
results = ensembl_post("/variant_recoder/homo_sapiens",
    {"variants": ["NM_001042432.2:c.295-23_295-20delCTCA", "rs80357914"]})
```

**Note:** `hgvsg` uses RefSeq chromosome accessions (`NC_000016.10` = chr16 GRCh38). Chromosome number = integer after `NC_0000`, leading zero stripped.

---

## 2. Variant Effect Predictor — `vep`

Predicts consequences, affected transcripts, splicing impact, population frequencies.

```python
# By HGVS
result = ensembl_get(
    "/vep/homo_sapiens/hgvs/NC_000016.10:g.28487761_28487764del",
    canonical=1, SpliceAI=1, CADD=1)

# By chromosomal region (1-based, strand appended)
result = ensembl_get(
    "/vep/homo_sapiens/region/16:28487761-28487764/-/del",
    canonical=1)

# By rsID
result = ensembl_get("/vep/homo_sapiens/id/rs80357914", canonical=1)

for hit in result:
    print(hit["most_severe_consequence"])
    for tc in hit.get("transcript_consequences", []):
        if tc.get("canonical"):
            print(tc["transcript_id"], tc["consequence_terms"],
                  tc.get("hgvsc"), tc.get("hgvsp"),
                  tc.get("spliceai_score"), tc.get("cadd_phred"))

# Batch POST (up to ~200)
result = ensembl_post("/vep/homo_sapiens/hgvs",
    {"hgvs_notations": ["NM_001042432.2:c.295-23_295-20delCTCA", "rs80357914"]},
    canonical=1, SpliceAI=1)
```

**Useful flags:** `canonical=1`, `SpliceAI=1`, `CADD=1`, `gnomADg=1`, `gnomADe=1`,
`phenotypes=1`, `regulatory=1`, `protein=1`, `uniprot=1`, `domains=1`, `hgvs=1` (include c./p. in output).

---

## 3. Sequence — `sequence/id` and `sequence/region`

```python
# By genomic region (1-based inclusive, always + strand unless strand=-1)
seq = ensembl_get("/sequence/region/homo_sapiens/16:28482762..28492762")["seq"]
seq_rc = ensembl_get("/sequence/region/homo_sapiens/16:28482762..28492762", strand=-1)["seq"]

# By Ensembl ID — type options: genomic, cdna, cds, protein
cdna = ensembl_get("/sequence/id/ENST00000333496", type="cdna")["seq"]
cds  = ensembl_get("/sequence/id/ENST00000333496", type="cds")["seq"]
prot = ensembl_get("/sequence/id/ENST00000333496", type="protein")["seq"]
gene_seq = ensembl_get("/sequence/id/ENSG00000188603", type="genomic",
                       expand_5prime=1000, expand_3prime=1000)["seq"]

# Batch by ID (up to ~50)
seqs = ensembl_post("/sequence/id",
    {"ids": ["ENST00000333496", "ENST00000355477"]}, type="cdna")

# Masking options: mask=soft (lowercase repeats), mask=hard (N repeats)
seq_masked = ensembl_get("/sequence/region/homo_sapiens/16:28482762..28492762",
                         mask="soft")["seq"]
```

---

## 4. Coordinate mapping — `map`

### Assembly liftover (GRCh37 ↔ GRCh38)

```python
# GRCh37 → GRCh38 (region format: chrom:start..end:strand)
result = ensembl_get("/map/homo_sapiens/GRCh37/16:28487761..28487764:1/GRCh38")
for m in result["mappings"]:
    print(m["mapped"])   # {"coord_system": "chromosome", "seq_region_name": "16",
                         #  "start": ..., "end": ..., "strand": 1}

# GRCh38 → GRCh37
result = ensembl_get("/map/homo_sapiens/GRCh38/16:28487761..28487764:1/GRCh37")
```

### cDNA / CDS / protein → genomic

```python
# cDNA coordinates (1-based from transcript start, includes UTRs) → genomic
result = ensembl_get("/map/cdna/ENST00000333496/1..500")
for m in result["mappings"]:
    print(m["original"], "→", m["mapped"])

# CDS coordinates (1-based, excludes UTRs) → genomic
result = ensembl_get("/map/cds/ENST00000333496/1..300")

# Protein residues → genomic
result = ensembl_get("/map/translation/ENSP00000329863/1..100")
```

Response contains `original` (input coords in cDNA/CDS/protein space) and `mapped`
(genomic coords with `seq_region_name`, `start`, `end`, `strand`). Multi-exon spans
return multiple mappings, one per exon.

---

## 5. Overlap — `overlap/region` and `overlap/id`

```python
# Features overlapping a genomic region
genes = ensembl_get("/overlap/region/homo_sapiens/16:28480000-28500000",
                    feature="gene", biotype="protein_coding")
txs   = ensembl_get("/overlap/region/homo_sapiens/16:28480000-28500000",
                    feature="transcript")
vars_ = ensembl_get("/overlap/region/homo_sapiens/16:28487000-28488000",
                    feature="variation")
reg   = ensembl_get("/overlap/region/homo_sapiens/16:28480000-28500000",
                    feature="regulatory")

# Features overlapping the region of an Ensembl ID
exons = ensembl_get("/overlap/id/ENST00000333496", feature="exon")
vars_in_gene = ensembl_get("/overlap/id/ENSG00000188603", feature="variation")

# Protein features → genomic (domains, sites, etc.)
prot_features = ensembl_get("/overlap/translation/ENSP00000329863",
                            feature="protein_feature", type="Pfam")
```

`feature=` options: `gene`, `transcript`, `exon`, `cds`, `variation`,
`somatic_variation`, `structural_variation`, `regulatory`, `segmentation`,
`motif`, `constrained`, `repeat`, `protein_feature`.

---

## 6. Phenotype annotations — `phenotype`

Retrieves disease/trait associations from OMIM, ClinVar, GWAS Catalog, etc.

```python
# Phenotypes for a gene (symbol or Ensembl ID)
phenos = ensembl_get("/phenotype/gene/homo_sapiens/CLN3",
                     include_associated=1, include_pubmed_id=1)
for p in phenos:
    print(p.get("description"), p.get("source"), p.get("attributes", {}).get("associated_gene"))

# Phenotypes in a genomic region (max 5 Mb)
phenos = ensembl_get("/phenotype/region/homo_sapiens/16:28480000-28500000",
                     feature_type="Variation", include_pubmed_id=1)

# By ontology accession (HPO, OMIM, EFO, etc.)
phenos = ensembl_get("/phenotype/accession/homo_sapiens/HP:0001250")

# By ontology term (free text)
phenos = ensembl_get("/phenotype/term/homo_sapiens/neuronal%20ceroid%20lipofuscinosis")
```

Each record includes `description`, `source` (e.g. `ClinVar`, `OMIM`, `GWAS`),
`ontology_accessions`, `variants` (list of associated rsIDs), optional `pubmed_ids`.

---

## 7. Cross-references — `xrefs`

```python
# All external DBs for an Ensembl ID
xrefs = ensembl_get("/xrefs/id/ENSG00000188603")
hgnc    = [x for x in xrefs if x["dbname"] == "HGNC"]
refseq  = [x for x in xrefs if "RefSeq" in x["dbname"]]
uniprot = [x for x in xrefs if "Uniprot" in x["dbname"]]
omim    = [x for x in xrefs if "OMIM" in x["dbname"]]

# Symbol → Ensembl ID
hits = ensembl_get("/xrefs/symbol/homo_sapiens/CLN3")  # returns [{id, type}, ...]

# External accession → Ensembl
hits = ensembl_get("/xrefs/name/homo_sapiens/NM_001042432")
```

Common `dbname` values: `HGNC`, `RefSeq_mRNA`, `RefSeq_peptide`, `RefSeq_ncRNA`,
`Uniprot/SWISSPROT`, `GO`, `OMIM_GENE`, `MIM_MORBID`, `EntrezGene`, `PDB`, `Interpro`.

---

## 8. Gene / transcript lookup — `lookup`

```python
# By Ensembl ID
gene = ensembl_get("/lookup/id/ENSG00000188603", expand=1)
# expand=1 nests Transcript list (and Exon list inside each Transcript)

# By symbol
gene = ensembl_get("/lookup/symbol/homo_sapiens/CLN3", expand=1)

# Batch
results = ensembl_post("/lookup/id",
    {"ids": ["ENSG00000188603", "ENST00000333496"]}, expand=1)
results = ensembl_post("/lookup/symbol/homo_sapiens",
    {"symbols": ["CLN3", "BRCA1"]})
```

---

## 9. Homology — `homology`

```python
# Orthologs (specific target species)
orth = ensembl_get("/homology/id/ENSG00000188603",
                   type="orthologues", target_species="mus_musculus",
                   format="condensed")
for h in orth["data"][0]["homologies"]:
    print(h["target"]["id"], h["target"]["species"], h.get("dn_ds"))

# By symbol
orth = ensembl_get("/homology/symbol/homo_sapiens/CLN3",
                   type="orthologues", format="condensed")

# Paralogs
par = ensembl_get("/homology/id/ENSG00000188603",
                  type="paralogues", format="condensed")
```

---

## Gotchas

- **Coordinates are 1-based inclusive** — unlike UCSC/BED (0-based half-open). `chr16:28,487,761` in the browser = `16:28487761` in the API with no adjustment.
- **`variant_recoder` returns `NC_` accessions**, not `chr` names. `NC_000016.10` = chr16 GRCh38. To parse chromosome: strip `NC_0000`, take integer part before the dot.
- **`biocommons.hgvs` + UTA does NOT work from compute nodes** — UTA is PostgreSQL (port 5432), not HTTP. Use `variant_recoder` instead.
- **GRCh37 (hg19):** use `https://grch37.rest.ensembl.org` as base URL; same endpoint paths.
- **Assembly liftover:** only works for regions that map cleanly; unmapped regions return empty `mappings`. Use `/map/:species/GRCh37/.../GRCh38` — no need for a separate liftover tool.
- **POST batch limits:** variant_recoder ~200, vep ~200, lookup/id ~1000, sequence/id ~50.
- **Rate limit:** HTTP 429 if exceeded — add `time.sleep(1)` between large batches.
- **`expand=1`** on lookup returns nested child objects (Transcript inside Gene, Exon inside Transcript). Without it, only IDs are returned.
- **Phenotype region queries** are capped at 5 Mb per request.
- **`overlap/translation`** `type=` filters by feature type within the protein (e.g. `Pfam`, `PIRSF`, `PRINTS`, `Seg`, `ncoils`, `SignalP`, `Tmhmm`).
