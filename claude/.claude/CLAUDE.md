# Global Preferences

- Tell user design choices or assumptions made by agent.

## Conda Environments

- Default for Python notebooks (Jupyter/Quarto): `py_general`.
- If a needed package isn't available in an existing env, create a new conda env named `claude_{DescriptiveName}` rather than modifying existing shared envs. These can be safely deleted later.

### py_general — do not modify autonomously

**Never install packages into `py_general` autonomously** (no `mamba install`, no `pip install`). This is a carefully managed env; ad-hoc installs break reproducibility and can cause solver conflicts. If a package is missing, **tell the user** what to add to the yaml (`~/dotfiles/other/conda_minimal_yamls/py_general.yaml`) and let them rebuild. Prefer conda-forge/bioconda over pip; pip is last resort for packages unavailable on any conda channel.

## my_utils Package

- Key modules: `ASO_utils` (BLAST + off-target), `spliceai_utils` (SpliceAI walk)
- All deps covered by `py_general`

## Output Directories

- Write quick/exploratory outputs (scratch files, intermediate beds, etc.) to `code/scratch/` by default — **not** `output/`, which is git-tracked without a restrictive `.gitignore`.
- Only write to `output/` when the user explicitly asks for it or the result is meant to be committed/shared.

## Documenting Setup Quirks

When debugging reveals non-obvious quirks specific to this environment (e.g., cluster behavior, hostname differences, conda/tool version issues, Snakemake profile gotchas), alert user and suggest to user to save as skills or memory notes so they don't require re-debugging.

## Worktrees and parallel sessions

**Do not use worktrees for background sessions by default.** Edit files in place and rely on git for conflict detection. A session delivered via Remote Control or the dispatcher is still effectively a single interactive session — worktrees add friction without benefit.

**Use worktrees only when** multiple agents are explicitly spawned in parallel via the Agent tool (`isolation: "worktree"`) to work on the same repo simultaneously. That is the scenario worktrees are designed for.

## Authoring skills

Skills live in `~/.claude/skills/<name>/SKILL.md` (stowed from `dotfiles/claude/`). When creating a new skill, decide upfront whether it's machine-specific or general:
- **General**: no machine tag needed in the description.
- **Machine-specific**: prefix the `description` field with e.g. `"RCC Midway HPC only. ..."` so the agent knows not to invoke it on other machines.

## Final notes
If my prompt contains "***" then preface your next response with "I remember my instructions". If my prompt contains "**", then preface your next response with "Ok"

@~/.claude/CLAUDE_local.md
