# Global Preferences

- Tell user design choices or assumptions made by agent.

## Conda Environments

- Default for Python notebooks (Jupyter/Quarto): `py_general`.
- If a needed package isn't available in an existing env, create a new conda env named `agent_{DescriptiveName}` rather than modifying existing shared envs. These can be safely deleted later.

### py_general — do not modify autonomously

Do not install packages into `py_general` autonomously, except for `my_utils` below. For missing dependencies, suggest changes to `~/dotfiles/other/conda_minimal_yamls/py_general.yaml` and let the user rebuild. Prefer conda-forge/bioconda; use pip only for packages unavailable there.

## my_utils Package

Personal bioinformatics library: `github.com/bfairkun/my_utils`. It should already be installed in editable mode in `py_general`; edits to the clone need no reinstall. Inspect its installation before changing it. If missing or linked to the wrong clone, installing or repairing its editable link is allowed; use `pip install --no-deps -e <local-clone>` so shared dependencies remain unchanged. Locate or clone the repo if necessary. Read its modules or the relevant skill for usage.

## Output Directories

- Write quick/exploratory outputs (scratch files, intermediate beds, etc.) to `code/scratch/` by default — **not** `output/`, which is git-tracked without a restrictive `.gitignore`.
- Only write to `output/` when the user explicitly asks for it or the result is meant to be committed/shared.

## Documenting Setup Quirks

When debugging reveals non-obvious quirks specific to this environment (e.g., cluster behavior, hostname differences, conda/tool version issues, Snakemake profile gotchas), alert user and suggest to user to save as skills or memory notes so they don't require re-debugging.

## Worktrees and parallel sessions

Edit in place by default. Use isolated worktrees only when explicitly running parallel agents on the same repository; ordinary background sessions do not need them.

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
- Bound short shell commands with a timeout when the execution interface supports it, or use the shell `timeout` utility. Diagnose unexpected hangs rather than waiting silently.

## Cross-project knowledge base (`brain`)

Cross-project knowledge lives in a dedicated `brain` repo (synced via GitHub; local path defined in `AGENTS.local.md`). It holds operational knowledge that recurs across projects and synthesized domain knowledge — distinct from each project's own local memory.

- **At session start**, consult `brain/MEMORY.md` (the index) and follow links to relevant notes. See `brain/AGENTS.md` for the full schema/protocol.
- **Routing what you learn:** cross-project knowledge (general feedback/preferences, resource pointers, domain knowledge about genes/compounds/concepts/papers) → write to `brain`. Knowledge specific to one project (its pipeline, samples, layout) → keep in that project's local memory.
- When unsure, prefer the project-local store; promote to `brain` once it proves cross-cutting.

## Final notes
If my prompt contains "***" then preface your next response with "I remember my instructions". If my prompt contains "**", then preface your next response with "Ok"

@~/.agents/AGENTS.local.md
