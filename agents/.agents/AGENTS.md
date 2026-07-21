# Global Preferences

- Tell user design choices or assumptions made by agent.

## Conda Environments

- Default for Python notebooks (Jupyter/Quarto): `py_general`.
- If a needed package isn't available in an existing env, create a new conda env named `agent_{DescriptiveName}` rather than modifying existing shared envs. These can be safely deleted later.

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

Unless specified otherwise, create skills as global, agent-neutral skills under `~/.agents/skills/`; use the `authoring-skills` skill for creation or revision.

## Repository instructions

- Use `AGENTS.md` as the canonical file for durable repository instructions.
- Continue reading existing `CLAUDE.md` and `GEMINI.md` files. When editing them, migrate shared content into `AGENTS.md` and retain client-required filenames as short `@` imports rather than duplicating content.
- Keep genuinely client-specific instructions in the relevant client file.

## Documentation hygiene

- State each instruction once; include rationale only when it prevents a likely mistake.
- When editing instructions, skills, or memory, remove related content that is stale, redundant, contradictory, or no longer actionable.
- Preserve uncertain or historical information unless its replacement is verified; flag uncertainty rather than guessing.

## Bash safety

- Always ask before running `rm -rf` or other bulk-destructive shell commands.
- Chain dependent commands with `&&`; newline-separated commands always run regardless of prior exit codes. Prefer `mv` over separate `cp` + `rm`.
- Set a `timeout` (ms) on Bash calls that should complete in under ~10 seconds. If a fast command hangs, surface the error and diagnose rather than waiting silently.

## Cross-project knowledge base (`brain`)

Cross-project knowledge lives in a dedicated `brain` repo (synced via GitHub; local path defined in `AGENTS.local.md`). It holds operational knowledge that recurs across projects and synthesized domain knowledge — distinct from each project's own local memory.

- **At session start**, consult `brain/MEMORY.md` (the index) and follow links to relevant notes. See `brain/AGENTS.md` for the full schema/protocol.
- **Routing what you learn:** cross-project knowledge (general feedback/preferences, resource pointers, domain knowledge about genes/compounds/concepts/papers) → write to `brain`. Knowledge specific to one project (its pipeline, samples, layout) → keep in that project's local memory.
- When unsure, prefer the project-local store; promote to `brain` once it proves cross-cutting.

## Final notes
If my prompt contains "***" then preface your next response with "I remember my instructions". If my prompt contains "**", then preface your next response with "Ok"

@~/.agents/AGENTS.local.md
