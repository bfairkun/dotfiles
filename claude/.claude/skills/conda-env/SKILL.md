---
name: conda-env
description: Create or update conda environment YAML files in code/envs/. Invoke when adding packages to a pipeline env, creating a new rule-specific env, or debugging conda env build failures.
argument-hint: "[env name or package to add]"
---

# Conda Environment Conventions

## Environment locations

| Path | Purpose |
|------|---------|
| `code/envs/<name>.yaml` | Rule-specific envs for Snakemake pipeline |
| `py_general` (shared) | Default Python analysis env — don't modify for project-specific needs |

Conda envs are built and cached at: `/project2/yangili1/bjf79/snakemake_conda_envs`

## Standard YAML format

```yaml
name: myenv
channels:
  - conda-forge
  - bioconda
  - defaults
dependencies:
  - python=3.11
  - samtools=1.19
  - pysam>=0.21
  - pip:
    - somepackage==1.2.3
```

**Channel priority order matters**: `conda-forge` first, then `bioconda`, then `defaults`. This is the standard bioinformatics stack order.

## Adding a package to an existing env

1. Read the existing YAML first
2. Add the package under `dependencies:` with a version pin if reproducibility matters
3. Use `=` for exact version, `>=` for minimum version
4. Prefer conda packages over pip when available (better dependency resolution)
5. For bioinformatics tools: check bioconda first (`bioconda` channel)

## Common bioinformatics packages and their channels

| Package | Channel |
|---------|---------|
| samtools, bcftools, htslib | bioconda |
| star, hisat2, bwa, bowtie2 | bioconda |
| salmon, kallisto | bioconda |
| subread/featurecounts | bioconda |
| bedtools | bioconda |
| pysam, pyranges, pyvcf | bioconda or conda-forge |
| pandas, numpy, scipy, matplotlib | conda-forge |
| snakemake | conda-forge |
| r-base, bioconductor-* | conda-forge / bioconda |

## Debugging env build failures

```bash
# Try building manually to see the full error
conda env create -f code/envs/myenv.yaml -n test_myenv

# If conflict, try with strict channel priority
conda env create -f code/envs/myenv.yaml -n test_myenv --strict-channel-priority

# Check what version is available
conda search -c bioconda samtools
```

Common issues:
- **Unsolvable conflict**: try relaxing version pins (`>=` instead of `=`)
- **Package not found**: check spelling, channel, and whether it's pip-only
- **Build takes forever**: add `libmamba` solver or use `mamba` instead

## Snakemake reference in a rule

```python
rule my_rule:
    conda: "envs/myenv.yaml"   # relative to code/ (Snakefile location)
```

Snakemake builds and caches the env on first use.
