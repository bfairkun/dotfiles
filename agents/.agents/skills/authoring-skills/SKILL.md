---
name: authoring-skills
description: Create, revise, organize, or clean up agent skills. Use when asked to make or update a skill, convert a recurring workflow into a skill, decide where skill instructions belong, or audit a skill for portability, concision, or stale content.
---

# Authoring Skills

## Location and scope

- Unless specified otherwise, make the skill global and cross-project.
- Store global skills in `~/.agents/skills/<name>/SKILL.md`. On this setup, edit the resolved dotfiles source under `~/dotfiles/agents/.agents/skills/`; do not create per-client copies.
- Create a repository-specific skill only when the user requests it or the workflow depends on that repository.
- Use lowercase hyphen-case for the directory and frontmatter `name`.

## Write the skill

- Include only `name` and `description` in YAML frontmatter for portability.
- Put all triggering conditions in `description`; the body loads only after triggering.
- Prefix a machine-specific description with its scope, for example `RCC Midway HPC only.`
- Document workflow, environment facts, constraints, and failure modes the agent cannot reliably infer. Assume general software practices.
- State each rule once and prefer short examples.
- Keep instructions capability-based and agent-neutral. Use client names or exact tool prefixes only when intrinsic to the workflow.

## Add resources only when useful

- Put repeated deterministic operations in `scripts/` and test them.
- Put conditional detail in `references/` and link it directly from `SKILL.md`.
- Put templates or output materials in `assets/`.
- Do not add README, changelog, installation, or quick-reference files that duplicate the skill.

## Revise and validate

- Read the existing skill and its referenced resources before editing.
- Remove or correct stale, redundant, contradictory, or non-actionable content within scope.
- Preserve uncertain or historical information unless its replacement is verified.
- Validate frontmatter, directory naming, links, and scripts. Use an available skill validator when practical.
