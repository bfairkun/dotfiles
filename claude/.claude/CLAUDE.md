# Global Preferences

- Tell user design choices or assumptions made by agent.

## Conda Environments

- Default for Python notebooks (Jupyter/Quarto): `py_general`.
- If a needed package isn't available in an existing env, create a new conda env named `claude_{DescriptiveName}` rather than modifying existing shared envs. These can be safely deleted later.

### py_general — do not modify autonomously

**Never install packages into `py_general` autonomously** (no `mamba install`, no `pip install`). This is a carefully managed env; ad-hoc installs break reproducibility and can cause solver conflicts. If a package is missing, **tell the user** what to add to the yaml (`~/dotfiles/other/conda_minimal_yamls/py_general.yaml`) and let them rebuild. Prefer conda-forge/bioconda over pip; pip is last resort for packages unavailable on any conda channel.

## my_utils Package

Personal bioinformatics utility library (repo: `github.com/bfairkun/my_utils`). Modules are self-documenting — `ls` the package or check the relevant skill. If a local clone is present, `pip install -e` it into `py_general` so it tracks the clone; otherwise `pip install git+https://github.com/bfairkun/my_utils.git`.

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

## Bash safety

- Always ask before running `rm -rf` or other bulk-destructive shell commands.
- Chain dependent commands with `&&`; newline-separated commands always run regardless of prior exit codes. Prefer `mv` over separate `cp` + `rm`.
- Set a `timeout` (ms) on Bash calls that should complete in under ~10 seconds. If a fast command hangs, surface the error and diagnose rather than waiting silently.

## Cross-project knowledge base (`brain`)

Cross-project knowledge lives in a dedicated `brain` repo (synced via GitHub; local path defined in `CLAUDE_local.md`). It holds operational knowledge that recurs across projects and synthesized domain knowledge — distinct from each project's own local memory.

- **At session start**, consult `brain/MEMORY.md` (the index) and follow links to relevant notes. See `brain/AGENTS.md` for the full schema/protocol.
- **Routing what you learn:** cross-project knowledge (general feedback/preferences, resource pointers, domain knowledge about genes/compounds/concepts/papers) → write to `brain`. Knowledge specific to one project (its pipeline, samples, layout) → keep in that project's local memory.
- When unsure, prefer the project-local store; promote to `brain` once it proves cross-cutting.

## Final notes
If my prompt contains "***" then preface your next response with "I remember my instructions". If my prompt contains "**", then preface your next response with "Ok"

@~/.claude/CLAUDE_local.md
