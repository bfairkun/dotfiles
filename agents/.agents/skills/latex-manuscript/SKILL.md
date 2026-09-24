---
name: latex-manuscript
description: Write, edit, build, or share a LaTeX scientific manuscript or a Markdown-authored LaTeX document. Invoke for starting a paper, grant, or other scientific document, editing prose or figures, rendering Markdown to LaTeX/PDF, exporting drafts to Google Docs, or applying those comments back.
---

# LaTeX manuscripts

## Choose the source mode

Use LaTeX-first mode for manuscripts that require extensive equations, custom
macros, or journal-specific TeX structure. In that mode, the `.tex` source is
the single source of truth.

Use Markdown-source mode for grant drafts and prose-forward documents when the
user wants a document that is easy to edit and review. In this mode, the
tracked Markdown file is the single source of truth and generated LaTeX/PDF
files are artifacts. Do not edit generated `.tex` files by hand.

For new Markdown-source documents, use a stable `works_in_progress/<slug>/`
directory in the project repository. Preserve an existing source location when
the user has already established one, unless they ask to relocate it.

Markdown-source mode has these conventions:

- Keep one clearly named tracked source, normally `proposal.md` or
  `manuscript.md`, in the document directory.
- Put a descriptive HTML comment at the top identifying the source of truth,
  generated outputs, and structural markers such as page breaks.
- Keep the source organized with explicit section markers. If multiple forms or
  attachments share one review packet, keep them in that one Markdown source.
- Use same-stem figure assets when Markdown and LaTeX need different formats:
  `figure.svg` is the editable vector source, `figure.png` is the Markdown
  preview, and `figure.pdf` is the LaTeX asset. Reference `figure.png` in
  Markdown. The renderer must automatically replace that suffix with `.pdf`
  when the same-stem PDF exists, otherwise fall back to the referenced PNG.
  Implement this once in the image-rendering helper; never maintain separate
  Markdown and LaTeX figure paths by hand.
- Generate LaTeX fragments, PDFs, logs, and auxiliary files into a repository
  `raw/sources/<slug>-preview/` directory or the project's equivalent. Add the
  generated-output path to `.gitignore`; do not commit compilation logs or
  auxiliary files.
- Provide a deterministic `Makefile` or build script next to the Markdown
  source. It should regenerate all outputs from the Markdown source and run
  structural checks such as page counts, character limits, and missing-glyph or
  overfull-box checks where relevant.
- After an agent edits the Markdown source, run the build and validation before
  handing the file back. Report the output path and any material layout or
  validation change. A manual user edit can be rebuilt with the same `make`
  command.
- If a generated artifact is needed for review, link it from a README or the
  handoff, but keep it out of Git unless the user explicitly requests a tracked
  rendered artifact.

The `.tex` source remains the editable source in LaTeX-first mode. Word and
Google Docs versions are regenerated artifacts, never edited back into the repo.

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
