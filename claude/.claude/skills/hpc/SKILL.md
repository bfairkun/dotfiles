---
name: hpc
description: Provides context about RCC (UChicago) HPC cluster setup and how to submit Slurm jobs on Midway2/Midway3. Invoke when user asks about submitting jobs, partitions, sinteractive, sbatch, or running Snakemake on the cluster.
argument-hint: [topic]
---

# RCC HPC (Midway2 / Midway3) Reference

## Cluster Detection

Always check which cluster you're on before submitting jobs:

```bash
hostname
# midway2-login*.rcc.local  → use midway2 settings
# midway3-login*.rcc.local  → use midway3 settings
```

## Accounts and Allocation

Always specify the account for job submission:
- Account: `pi-yangili1`
- **On midway3, account is required** — jobs will be rejected without it.

---

## Midway3 (current cluster)

### Default partition: `caslake`
- 48 CPUs/node, 192 GB RAM, Intel Gold 6248R
- Max ~36 cores and ~96 GB per job is typical to stay reasonable

### Notable partitions on midway3:

| Partition  | CPUs/node | RAM       | GPU            | Notes                        |
|------------|-----------|-----------|----------------|------------------------------|
| caslake    | 48        | 192 GB    | —              | Default, general compute     |
| bigmem     | 48        | 768–1536 GB | —            | High-memory jobs             |
| amd        | 128       | 256 GB    | —              | AMD EPYC-7702                |
| amd-hm     | 128       | 2048 GB   | —              | AMD high-memory              |
| gpu        | 48        | 192 GB    | V100/RTX6000   | Shared GPU nodes             |
| gpu (a100) | 48        | 384 GB    | A100           | midway3-0294                 |
| beagle3    | 32        | 256 GB    | A100/A40       | Beagle3 nodes                |
| ssd        | 48        | 192 GB    | —              | Local SSD-backed nodes       |

### Example sbatch script (midway3):

```bash
#!/bin/bash
#SBATCH --job-name=myjob
#SBATCH --account=pi-yangili1
#SBATCH --partition=caslake
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=logs/%x.%j.out
#SBATCH --error=logs/%x.%j.err

module load python
conda activate py_general
python my_script.py
```

### Interactive session (midway3):

```bash
sinteractive --account=pi-yangili1 --partition=caslake --ntasks=1 --cpus-per-task=4 --mem=16G --time=02:00:00
```

---

## Midway2

### Default partition: `broadwl`
- 28 CPUs/node, 64 GB RAM typical

### GPU partition on midway2: `gpu2`

### Example sbatch script (midway2):

```bash
#!/bin/bash
#SBATCH --job-name=myjob
#SBATCH --account=pi-yangili1
#SBATCH --partition=broadwl
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=logs/%x.%j.out
#SBATCH --error=logs/%x.%j.err

conda activate py_general
python my_script.py
```

---

## Snakemake Profiles

Snakemake profiles live in `~/.config/snakemake/`. Choose the right one based on hostname:

| Hostname pattern          | Profile to use     | Default partition |
|---------------------------|--------------------|-------------------|
| midway3-login*.rcc.local  | `slurm_midway3`    | caslake           |
| midway2-login*.rcc.local  | `slurm`            | broadwl           |

### Running Snakemake with the correct profile:

```bash
# Midway3
snakemake --profile slurm_midway3 [targets]

# Midway2
snakemake --profile slurm [targets]
```

### ⚠️ Always dry-run before submitting to the cluster

Before any real cluster run, do a dry-run and **check the job count breakdown carefully**:

```bash
snakemake -n 2>&1 | grep -E "^(Job stats|  [a-z]|total )"
```

Look for unexpected rules being triggered — especially rules with many jobs (hundreds or thousands) that correspond to already-existing outputs. A new output added to an existing rule can cascade into re-running all downstream jobs. If you see unexpectedly large job counts, investigate before submitting.

If existing outputs were incorrectly flagged as stale (e.g., due to a rule modification updating an input file's timestamp), use `snakemake --touch --cores 1` to freeze all existing file timestamps, then dry-run again to confirm only the genuinely new jobs remain.

### Default cluster-config (applies to all rules unless overridden):
- account: `pi-yangili1`
- mem: `4000` MB
- output redirected to `/dev/null`
- job-name: `{rule}.{wildcards}`

### Key profile settings:
- `jobs: 150` — max concurrent jobs
- `restart-times: 1` — retry failed jobs once
- `use-conda: True` — activate per-rule conda envs
- `latency-wait: 60` — wait up to 60s for output files
- `conda-prefix: /project2/yangili1/bjf79/snakemake_conda_envs`

---

## Useful Commands

```bash
# Check job queue
squeue -u bjf79

# Cancel a job
scancel <jobid>

# Check available partitions and node status
sinfo -o "%20P %5D %14F %4c %8G %8z %26f %N"

# Check job details / resource usage
scontrol show job <jobid>
sacct -j <jobid> --format=JobID,State,Elapsed,MaxRSS,CPUTime

# Check allocation balance
rcchelp usage
```

## Storage Notes

- `/project2/yangili1/bjf79/` — analysis projects (this cluster's storage)
- `/project/yangili1/bjf79/` — repos, reference genomes, tools
- `/scratch/midway2/bjf79/` — scratch (fast, temporary)
- Large intermediate files → `code/scratch/` in project dir (not git-tracked)

## Docs

Full documentation: https://docs.rcc.uchicago.edu
