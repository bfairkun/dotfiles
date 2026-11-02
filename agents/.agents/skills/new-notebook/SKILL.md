---
name: new-notebook
description: Create a new analysis notebook in the analysis/ directory, and the writing standard every notebook must meet. Invoke when starting a new analysis, exploration, or visualization task that needs a notebook, or when writing prose or captions into one.
---

# New Notebook Conventions

## Naming and header

`analysis/YYYYMMDD_descriptive_name.qmd` — today's date, lowercase, underscores.

Python:

```yaml
---
title: "Descriptive Title"
jupyter: py_general
format:
  html:
    code-fold: true
    toc: true
execute:
  echo: true
  warning: false
---
```

R (knitr engine): same header without `jupyter:`, plus `message: false` under `execute`, and an
`{r setup}` chunk with `#| include: false` loading `tidyverse`.

`my_utils` is installed in `py_general`; no `sys.path` hacks. Paths are relative to `analysis/`
(`../data/`, `../output/`, `../code/scratch/`). Small committed outputs → `output/`; large files →
`code/scratch/`.

## Writing standard

The notebook is written for a reader who was not in the session. The user is the author; the
agent is a scribe. Write in the user's plain, lab-notebook voice: short declarative sentences,
standard field terminology, no rhetoric.

### Structure of each section

1. **Context** (above the analysis): the question, why it is asked, and what motivated it
   (prior notebook, paper, observation) with a link or identifier.
2. **Methods** (above the figure): enough detail to write a paper's methods section — data
   source and filters, sample/feature counts, the model or statistic with its definition,
   parameter values and why they were chosen, controls, and anything deliberately excluded.
3. **Figure**. Nearly every finding is shown in a figure, not described in text. If a
   conclusion has no figure behind it, make the figure or drop the conclusion.
4. **Caption** (directly below the figure, as `fig-cap` or a caption paragraph — never text
   drawn inside the figure): what each panel, axis, point, line, and color encodes, and n.
   A reader skimming only figures and captions should know what is plotted. The caption
   describes; it does not interpret.
5. **Result** (optional, one to three sentences): what the figure shows, stated as an
   observation with the supporting numbers. Only interpretations the user has confirmed go
   here unsigned (see below).

End with a short **Summary** listing the confirmed findings, and open questions or caveats.

### Interpretation and attribution

Unsigned prose is read as the user's own view. Therefore:

- Unsigned interpretation must come from something the user said or a reading they selected
  or agreed with in conversation. Use [interpret-results](../interpret-results/SKILL.md) when
  clarification is needed, at any point in analysis or writing.
- Write agreed interpretations naturally. Do not add endorsement labels, approval statements,
  or a review transcript to the notebook; its authorship already implies the user's view.
- Omit unneeded AI interpretation. Any retained interpretation the user has not agreed with
  must be explicitly AI-signed, including hypotheses motivating later analyses. Keep it brief:

  ```
  ::: {.callout-note title="AI interpretation (not confirmed by author)"}
  ...
  :::
  ```

- No unsigned biological speculation, mechanisms, or "this suggests…" chains beyond the
  user's stated or selected reading. AI signing is not a license to fill the notebook with
  speculative prose.

### Style — avoid

- Narrating the session ("we then noticed", "a question forced itself on us", "partway through").
- Coined labels, metaphors, or private shorthand from the chat; use standard terms, and define
  any variable or column name before using it.
- Bold for emphasis in running prose, rhetorical questions, "crucially"/"notably"/"importantly".
- Restating the same point in intro, result, and summary.
- Explaining code line by line; code is folded and speaks for itself.

## Reader comment boxes

Projects from `cookiecutter-quarto-smk` ship `analysis/_comment_widget.html` (wired via
`include-after-body` in `analysis/_quarto.yml`), which adds a comment panel to every page. Check
the file exists before relying on it. To add a box at a specific point:

```
::: {.comment-box}
:::
```

`data-anchor` overrides the label (default: nearest heading). `data-prompt` adds a question above
the box — only when the user has said what to ask. Readers save comments with **Download
annotated copy** (not the browser's Save Page As).

## Table of contents

The template also ships `analysis/_toc_dropdown.html` (second `include-after-body` entry): it
replaces Quarto's right-margin TOC with a floating "Contents ▾" button so wide content (embedded
genome browsers, figure grids) gets the full page width. For older projects, copy it from the
template's `analysis/` and add it to `include-after-body`; if the project's `.gitignore` has
`analysis/*html`, add `!analysis/_toc_dropdown.html`.

## Rendering

`render_notebook render analysis/YYYYMMDD_name.qmd` (a quarto shim in `~/bin/` that records the
render env; see `compute-kernel`). Python: prefix with `conda run -n py_general`. Before
rendering a notebook the agent wrote prose for, follow the
[pre-render catch-up](../interpret-results/SKILL.md#pre-render-catch-up).
