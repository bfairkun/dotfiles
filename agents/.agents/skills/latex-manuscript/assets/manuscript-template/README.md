# Manuscript

A LaTeX manuscript with script-generated figures and a Google Docs export for
coauthors to comment on.

## Setup

Edit the title and authors at the top of `main.tex`, and the running header in
`preamble.tex`. That is the whole setup.

`figures/source`, if present, is a symlink to the analysis project whose plots
feed this paper — a pipeline rerun flows straight into the manuscript.

## Build

```bash
make            # -> main.pdf
make figures    # regenerate figures/ (PDF + PNG), then rebuild
make tidy       # reflow prose to one sentence per line
make check      # verify the manuscript will export cleanly
make docx       # -> export/<dirname>.docx for Google Docs
make watch      # rebuild on every save
```

Needs TinyTeX (`quarto install tinytex`) and pandoc. The Makefile puts TinyTeX
on `PATH` for you.

## Layout

```
main.tex           spine: front matter + \input of each section
preamble.tex       styling: fonts, margins, captions
macros.tex         project vocabulary (\gene, \todo, ...)
sections/*.tex     the prose, one file per section
refs.bib           bibliography
make_figures.py    writes figures/*.pdf and *.png
AGENTS.md          conventions and export constraints — read this first
```

## The constraint

Pandoc does not run LaTeX, it parses it, so commands like `\cref` and `siunitx`
are silently mangled on export — giving a perfect PDF alongside a Word file with
wrong figure numbers. A few LaTeX niceties are therefore off-limits. `make check`
enforces it; the full table and the reasoning are in `AGENTS.md`.
