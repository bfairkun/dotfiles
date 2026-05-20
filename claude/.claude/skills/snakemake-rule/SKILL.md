---
name: snakemake-rule
description: Generate or edit a Snakemake rule following project conventions. Invoke when adding a new rule, modifying an existing rule, or debugging a rule in code/rules/.
argument-hint: "[rule description or rule name]"
---

# Snakemake Rule Conventions

## Always invoked from `code/` directory
All paths in rules are relative to `code/`. Key relative path prefixes:
- `scratch/` — large intermediates (not git-tracked)
- `config/` — config files
- `../analysis/` — notebooks
- `../output/` — small committed outputs
- `../logs/` — job logs
- `../data/` — raw data

## Required rule structure

Every rule MUST have a `log:` directive, and the shell/script command MUST redirect both stdout and stderr to it:

```python
rule my_rule:
    input:
        bam = "scratch/alignments/{sample}.bam",
        bai = "scratch/alignments/{sample}.bam.bai",
    output:
        counts = "scratch/counts/{sample}.txt",
    log:
        "../logs/my_rule.{sample}.log"
    conda:
        "envs/rnaseq.yaml"
    resources:
        mem_mb = 8000
    shell:
        """
        some_command {input.bam} > {output.counts} 2> {log}
        """
```

For multi-command shell blocks, redirect each command:
```python
    shell:
        """
        cmd1 {input} > {output.tmp} 2> {log}
        cmd2 {output.tmp} >> {output.result} 2>> {log}
        """
```

For Python scripts where data output goes to a file (via `--out` flag), and stdout is only progress messages, capture both to the rule log so nothing is lost in unreliable slurm `.out` files:
```python
    shell:
        "python scripts/myscript.py --in {input} --out {output} >{log} 2>&1"
```
For scripts that write data to stdout, use the usual split (`>{output} 2>{log}`).

## Conda env directive
- Use `conda: "envs/myenv.yaml"` for rule-specific envs
- Check `code/envs/` for existing envs before creating a new one
- Do NOT create `py_general.yaml` — that name collides with the user's managed system env and causes confusion. Use a descriptive name like `pysam_utils.yaml`
- Always reference with path relative to Snakefile location (i.e., relative to `code/`)

## Resources
- Default: `mem_mb = 4000` (profile default)
- Specify higher for memory-intensive steps: `mem_mb = 32000`
- For multithreaded: add `threads: 8` and use `{threads}` in shell command

## Wildcard conventions
- `{sample}` — sample name
- `{chrom}` — chromosome (e.g., chr1)
- Use expand() in rule all or aggregate rules

## Rule all / target rules
```python
rule all:
    input:
        expand("scratch/counts/{sample}.txt", sample=config["samples"])
```

## Config access
```python
configfile: "config/config.yaml"
# Access as: config["key"]
```

## When writing a new rule
1. Check `code/rules/` for existing rules to follow patterns
2. Check `code/envs/` before creating a new conda env
3. Place rule in the most appropriate existing `.smk` file, or create a new one in `code/rules/`
4. Add target outputs to `rule all` in the main Snakefile

## Before submitting to cluster (IMPORTANT)

**For rules that run scripts or commands on large files — always test locally first on one small sample before targeting all samples.** This catches conda env issues, script bugs, and bad args cheaply.

### Step 1: validate the conda env has the right packages
```bash
conda run -n <env> python -c "import pysam, numpy; print('ok')"
```
If creating a new `code/envs/<name>.yaml`, verify all script imports are present in that yaml.

### Step 2: run the script directly on the smallest available sample
```bash
conda run -n <env> python scripts/myscript.py \
  --input alignment/smallest_sample.bam \
  --output scratch/test_out.tsv.gz 2>&1 | tail -20
```
Run to completion. Write test outputs to `scratch/`, not `output/`.

### Step 3: target a single output for the first snakemake run
```bash
conda run -n sm_splicingmodulators snakemake --profile slurm_midway3 \
  output/path/smallest_sample.ext -T 0
```
Only after this passes → submit all samples.

## Debugging cluster failures

1. **Slurm logs first**: `logs/slurm/<rule>.<jobid>.err` — the actual error
2. **Rule log**: `logs/<rule>/<wildcard>.log` — stdout/stderr from the command
3. **OOM**: sacct `ExitCode=1:0` with `MaxRSS` near `ReqMem` ceiling = OOM kill. `samtools sort -m X` overshoots ~50%; rule of thumb: `mem_mb ≥ (threads × -m_bytes × 1.5) + 2G`
4. **sbatch not in PATH**: slurm module loads only for login shells. Fix: `module load slurm/current` in `~/.zshrc_local`
5. **PermissionError on scratch**: `shadow-prefix` in profile config must match the node's actual scratch mount
6. **Unexpected re-runs after adding `log:`**: adding/changing `log:` changes the rule code hash → snakemake re-runs the rule and all downstream
