# Agent instructions for this manuscript

## The one constraint that shapes everything

Coauthors comment in Google Docs, so this manuscript must survive
`make docx` (pandoc → Word → Drive) with **correct figure and table numbers**.

Pandoc does not run LaTeX — it parses it. Commands defined by packages get
silently mangled or dropped. They still compile to a perfect PDF, which is why
this fails quietly and why `make check` exists.

**Run `make check` after editing. It is not optional.**

### Banned, with what actually happens on export

| Do not use | Exports as | Use instead |
|---|---|---|
| `\cref` / `\Cref` | a bare wrong number, `(3)` | `Figure~\ref{fig:x}` — type the word yourself |
| `\subref` | an empty `()` | draw panel letters in `make_figures.py` |
| `\SI` / `\si` | unit dropped, `1  ` | plain text: `1 \textmu M` |
| `\num` | empty string | type the number |
| `tcolorbox` | whole box vanishes, contents included | ordinary prose or `quote` |
| `subfigure` | bare table, empty panel labels | one combined PDF, letters from Python |
| `\ref{eq:...}` | raw label, `Equation [eq:model]` | describe it in words — pandoc numbers figures and tables, but not equations |

### Verified to survive

`\ref` / `\label` (all auto-numbering), `\citep` / `\citet` + `refs.bib`,
`\newcommand` macros (pandoc expands them), `\includegraphics`, `booktabs`
tables, `threeparttable` footnotes, numbered equations, `\textbf` / `\textit`.

## Figures

Figures are never pasted in — the manuscript stores a filename. All figures come
from `make_figures.py`, which writes **both** a PDF (for LaTeX) and a 300 dpi
PNG (for the Word export, which cannot display PDF images).

Panel letters (A, B, …) are drawn in Python, per the constraint above.

If `figures/source` is a symlink to an analysis project, read that project's
outputs so a pipeline rerun flows into the paper.

## Prose conventions

- **Write however feels natural.** `make tidy` reflows to one sentence per line
  so git diffs are sentence-level. Do not hand-wrap paragraphs.
- **Comments**: `% BF>` is a note from Ben, `% CL>` is a reply from Claude.
  Answer in place, below the note; delete the pair once resolved. Anything
  after `%` is invisible to LaTeX.
- **`\todo{...}`** renders in red in the PDF. `make check` warns while any
  survive. Clear them before sharing a draft.

## Editing

- Prefer editing `sections/*.tex`. Leave `preamble.tex` alone once it works —
  styling bugs there are the slow kind to debug.
- **After editing, rebuild.** A broken `.tex` produces no PDF at all, so
  "it compiles" is the minimum bar to report. Report the actual result.
- Commit before and after a batch of edits so `git diff` shows what changed.

## Coauthor round trip

1. `make docx` → upload `export/<name>.docx` to Drive → share the Doc.
2. Coauthor comments and suggests in the Doc.
3. Download it back as `.docx`. Comments live in `word/comments.xml` inside the
   file (a `.docx` is a zip) — unzip and read them, then apply to the `.tex`.
4. Prose rewrites get applied by hand, reading their version against ours.

The `.tex` is the single source of truth. The Doc is a regenerated artifact,
never edited back into the repo directly.

## Build reference

```
make          main.pdf
make figures  regenerate figures/ (PDF + PNG), then rebuild
make tidy     one sentence per line
make check    enforce the export constraints
make docx     export/<name>.docx for Google Docs
make watch    rebuild on save
```
