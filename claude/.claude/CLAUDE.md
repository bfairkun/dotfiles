# Global Preferences

## HPC Storage Paths

Two separate storage mounts — do NOT confuse them:

- `/project/yangili1/bjf79/` — repos, tools, reference genomes (e.g. `repos_not_projects`)
- `/project2/yangili1/bjf79/` — analysis projects

## Conda Environments

- Default for general shell commands, running Snakemake, etc.: `sm_splicingmodulators`
- Default for Python notebooks (Jupyter/Quarto): `py_general`
- Default for R notebooks: `base` conda env
- If a needed package isn't available in an existing env, create a new conda env named `claude_{DescriptiveName}` rather than modifying existing shared envs. These can be safely deleted later.

## my_utils Package

- Location: `/project/yangili1/bjf79/repos_not_projects/my_utils/src/my_utils/`
- Key modules: `ASO_utils` (BLAST + off-target), `spliceai_utils` (SpliceAI walk)
- All deps covered by `py_general`

## Documenting Setup Quirks

When debugging reveals non-obvious quirks specific to this environment (e.g., HPC cluster behavior, hostname differences, conda/tool version issues, Snakemake profile gotchas), save them as skills or memory notes so they don't require re-debugging.

- This is a UChicago RCC HPC cluster with two login nodes: **Midway2** and **Midway3**. Some tools, partitions, or behaviors may differ between them. Note the hostname when a fix is node-specific.
- Save persistent quirks to `~/.claude/projects/.../memory/` topic files and link from `MEMORY.md`, or propose a new skill if the pattern recurs across sessions.
