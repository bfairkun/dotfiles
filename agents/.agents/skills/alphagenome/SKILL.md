---
name: alphagenome
description: RCC Midway HPC only. Query the AlphaGenome API (Google DeepMind v0.5.1) for splice site probability, splice site usage, gene expression, and other genomic predictions from raw DNA sequence. Invoke when running AlphaGenome predictions, using the AlphaGenome API, or using alphagenome_utils from my_utils.
---

# AlphaGenome Skill

AlphaGenome (Google DeepMind v0.5.1) is a genomic foundation model that predicts
multi-tissue functional genomics signals, including splice site probability and
splice site usage, from raw DNA sequence.

---

## Installation

AlphaGenome v0.5.1 is installed in the `py_general` conda env:
```bash
pip install alphagenome
```

---

## API Key

Stored in `~/.secrets` as `ALPHAGENOME_API_KEY`, sourced via `~/.zshrc_local`.

```python
import os
api_key = os.environ["ALPHAGENOME_API_KEY"]
```

---

## Supported Sequence Lengths

Must match exactly one of:
- 16,384 bp (fastest; use for local splice site analysis)
- 131,072 bp
- 524,288 bp
- 1,048,576 bp

Shorter sequences should be padded with N's to the next supported length.

---

## Basic Usage

```python
from alphagenome.models.dna_client import create, OutputType, Organism

client = create(api_key=os.environ["ALPHAGENOME_API_KEY"])

# Sequence must be exactly a supported length (pad with N's if shorter)
sequence = "A" * 16_384  # placeholder

output = client.predict_sequence(
    sequence,
    organism=Organism.HOMO_SAPIENS,
    requested_outputs=[OutputType.SPLICE_SITES, OutputType.SPLICE_SITE_USAGE],
    ontology_terms=None,  # None = all tissues; or pass list of OntologyTerm
)

# Per-position splice site probability
splice_probs = output.splice_sites       # TrackData, shape (L, n_tracks)

# Per-position splice site usage (tissue-specific)
splice_usage = output.splice_site_usage  # TrackData, shape (L, n_tracks)

# Per-junction scores (if requested)
# splice_juncs = output.splice_junctions  # JunctionData
```

---

## Output Types

| OutputType | Description |
|---|---|
| `SPLICE_SITES` | Per-position splice site probability |
| `SPLICE_SITE_USAGE` | Per-position tissue-specific usage |
| `SPLICE_JUNCTIONS` | Per-junction (not per-position) scores |
| `GENE_EXPRESSION` | Tissue-specific expression |
| `CHROMATIN_ACCESSIBILITY` | ATAC-seq signal |
| `HISTONE_MODIFICATIONS` | H3K27ac, H3K4me3, etc. |

---

## Tissue Specification (Ontology CURIEs)

Pass `None` for `ontology_terms` to get all tissues (~100+), or specify:

```python
from alphagenome.data import ontology

# Common tissue CURIEs (UBERON ontology):
TISSUE_CURIES = {
    "brain":           "UBERON:0000955",
    "liver":           "UBERON:0002107",
    "heart":           "UBERON:0000948",
    "skeletal_muscle": "UBERON:0001134",
    "testis":          "UBERON:0000473",
    "kidney":          "UBERON:0002113",
    "lung":            "UBERON:0002048",
    "blood":           "UBERON:0000178",
    "ovary":           "UBERON:0000992",
    "thyroid":         "UBERON:0002046",
}

# Request a specific tissue:
output = client.predict_sequence(
    sequence,
    organism=Organism.HOMO_SAPIENS,
    requested_outputs=[OutputType.SPLICE_SITE_USAGE],
    ontology_terms=[ontology.OntologyTerm("UBERON:0000955")],  # brain
)
```

---

## Accessing Track Values

```python
vals = output.splice_site_usage.values  # numpy array (L, n_tracks)

# Track metadata (tissue names, ontology terms):
meta = output.splice_site_usage.metadata
for i, m in enumerate(meta):
    print(i, m.name, getattr(m, 'ontology_term', None))
```

---

## my_utils Integration

Use `alphagenome_utils` in `my_utils` for a drop-in predictor:

```python
import sys
sys.path.insert(0, "/project/yangili1/bjf79/repos_not_projects/my_utils/src")
from my_utils import alphagenome_utils, spliceai_utils

client = alphagenome_utils.create_alphagenome_client(
    os.environ["ALPHAGENOME_API_KEY"]
)

# Get DataFrame(donor_prob, acceptor_prob, seq) for any sequence:
df = alphagenome_utils.predict_splice_sites_alphagenome(seq, client)

# Or as a predictor_fn for spliceO_predictions:
predictor = alphagenome_utils.make_alphagenome_predictor(client)
results = spliceai_utils.spliceO_predictions(
    FASTA, "chr2:1,840,760-1,887,609", (1840760, 1887609), 20, 20,
    {"donor": 1865000}, predictor_fn=predictor
)

# List available tissues:
tissue_df = alphagenome_utils.list_alphagenome_tissues(client)
```

---

## Latency & Caching

- API calls are remote (Google Cloud); expect ~1–5 seconds per call
- Cache results to parquet/pickle when running large scans
- For 20N walks (~5,000 calls/exon), budget ~2–4 hours per exon
- Use `target_length=16384` for the smallest footprint when sequence allows

---

## Notes

- Sequence must contain only ACGTN (no IUPAC ambiguity codes)
- The model pads internally, but the sequence passed must match a supported length exactly
- `SPLICE_SITE_USAGE` returns values in [0, 1] representing fractional usage
- `SPLICE_SITES` returns probability of being a splice site position
- Track layout: typically interleaved (even=donor, odd=acceptor per tissue) — verify with metadata
