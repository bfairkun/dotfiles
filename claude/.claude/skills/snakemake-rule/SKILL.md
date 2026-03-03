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

## Conda env directive
- Use `conda: "envs/myenv.yaml"` for rule-specific envs
- Common shared envs in `code/envs/`: `py_general.yaml`, check existing ones first
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
