---
name: latex-manuscript
description: Write, edit, build, or share a LaTeX scientific manuscript. Invoke for starting a paper, editing prose or figures, exporting drafts to Google Docs for coauthor comments, or applying those comments back.
---

# LaTeX manuscripts

The `.tex` source is the single source of truth. Word and Google Docs versions
are regenerated artifacts, never edited back into the repo.

## Starting a new manuscript

```bash
scripts/new-manuscript.sh <destination-dir> [analysis-project-dir]
```

Both the script and the skeleton it copies (`assets/manuscript-template/`) live
in this skill directory, so there is no path to configure on any machine.

The optional second argument symlinks `figures/source` at the analysis project
whose plots feed the paper, so a pipeline rerun flows into the manuscript.

The destination can be either its own repo or a `manuscript/` subdirectory
inside an analysis project — the script detects which and skips `git init` when
already inside a working tree. Use a subdirectory when the paper maps 1:1 onto
one analysis project; use a separate repo when it draws on several, or when
coauthors should not see the analysis. It is a copy, not a submodule: every file
gets rewritten immediately, so there is nothing to pull updates for.

Then edit the title and authors at the top of `main.tex` and the running header
in `preamble.tex`. Read the generated `AGENTS.md` — it carries the per-repo
rules and is the authority for that manuscript.

Do not build a new skeleton by hand. If the template is missing something,
fix the template.

## The export constraint

Coauthors comment in Google Docs, so every manuscript must survive
`make docx` with **correct figure and table numbers**.

Pandoc does not run LaTeX, it parses it. Package-defined commands are silently
mangled — producing a flawless PDF and a corrupted Word file. This fails
quietly, which is why it needs a check rather than vigilance.

`make check` enforces the rules; the full table with verified export behaviour
lives in each manuscript's `AGENTS.md`. The short version: use `\ref`, not
`\cref`; no `siunitx`, `subfigure`, or `tcolorbox`; draw panel letters in
Python; do not cross-reference equations.

**Run `make check` after editing prose. It is not optional.**

## Editing conventions

Stated in full in the manuscript's own `AGENTS.md`. The two that are easy to get
wrong before that file is in context:

- **Prose**: write naturally, wrap anywhere. `make tidy` reflows to one sentence
  per line so diffs are sentence-level. Never hand-wrap to a column width.
- **Comments**: `% BF>` is a note from the user, `% CL>` is the agent's reply.
  Answer in place below the note; delete the pair once resolved.

**Rebuild after editing and report the real result.** A broken `.tex` produces
no PDF at all, so "it compiles" is the minimum bar, not a success.

## Coauthor round trip

`make docx` → upload `export/<name>.docx` to Drive → coauthor comments → download
as `.docx` → comments are in `word/comments.xml` (a `.docx` is a zip); read them
and apply to the `.tex`. Prose rewrites are applied by hand.

Warn the user if a coauthor expects to rewrite prose directly in the Doc and
have it flow back — that direction is not automated.

## Environment

TinyTeX, `latexmk` PATH behaviour, and installing missing LaTeX packages on
Midway are recorded in the brain note `latex-toolchain-midway`. Read it before
debugging a build or install failure.
