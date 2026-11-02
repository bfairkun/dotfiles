---
name: interactive-notebook
description: >
  Interactively co-author a Quarto notebook with the user: create the .qmd, explore in a
  Jupyter kernel (Python or R), show plots via agent_plots, write validated cells back into the
  notebook one at a time, and discuss interpretations throughout the analysis.
---

# Interactive Notebook Co-authoring

Loop: **run in kernel → show plot → discuss → write chunk + prose to .qmd → repeat.**
Header, naming, and the writing standard (section structure, captions, attribution) are in the
`new-notebook` skill — follow it for every prose edit.

`<AGENT_PLOTS>` / `<AGENT_PLOTS_URL>` are placeholders; resolve them first via the `agent-plots`
skill. Never write to `~/agent_plots`.

## 1. Create the notebook

Create `analysis/YYYYMMDD_name.qmd` with the header from `new-notebook`, an opening Context
section, and an imports cell.

## 2. Open the kernel

Compute-node kernel unless the user says otherwise; start it yourself (`compute-kernel` skill).
If the user already has a VSCode kernel with a cell executed, the MCP server attaches to it. For
R kernels, send plain R through `run_python`.

## 3. Explore

- Run code in the kernel; save plots as PDF (unless asked otherwise) to `<AGENT_PLOTS>` and give
  the resolved URL.
- For figures that will be repeated across panels, look at one yourself before replicating.
- After each meaningful result, use [interpret-results](../interpret-results/SKILL.md) before
  an unconfirmed interpretation drives the next analysis or becomes notebook prose. Also use
  it whenever the user wants to discuss a result mid-analysis. Carry forward readings already
  established in conversation; routine checks do not need repeated questioning.

## 4. Write to the notebook

After a result is validated, append the chunk and its prose together (never batch
all cells at the end; never write unvalidated code). Per `new-notebook`: methods above, figure,
caption below, then at most a short result statement. Use `#|` chunk options
(`label: fig-...`, `fig-cap:`, `fig-width:`, `fig-height:`).

After each prose edit run `preview_notebook analysis/YYYYMMDD_name.qmd`; it writes
`<stem>.preview.html` to agent_plots (prose rendered, code collapsed, auto-reloads). Give the URL
once per notebook.

## 5. Pre-render interpretation check

Before the first render, and after changes to results or interpretive prose, follow the
[pre-render catch-up](../interpret-results/SKILL.md#pre-render-catch-up). This catches unresolved
claims; it does not repeat discussions completed during exploration.

## 6. Render

```bash
conda run -n py_general render_notebook render analysis/YYYYMMDD_name.qmd   # Python
render_notebook render analysis/YYYYMMDD_name.qmd                            # R
```

## Session state (survive compaction)

Write to **`<AGENT_PLOTS>/state_<notebook-stem>.md`** — one file per notebook, never a shared
`state.md`. The plots directory is shared by every concurrent session, so a fixed filename means
one session silently destroys another's crash-recovery state. (Same hazard as the hardcoded
kernel connection file in `compute-kernel`.) If a bare `state.md` is present it belongs to
another session or an older one: leave it alone.

After connecting, after each validated chunk, and before switching to writing, overwrite that
file with: kernel id / connection file, notebook path, cwd, language; key variables with type and
shape; saved artifacts; goal, interpretation state from `interpret-results`, and
the exact next step. Keep it short — metadata, not history.

After compaction: `ls <AGENT_PLOTS>/state_*.md`, read the one matching this notebook, reconnect
with `connect_to_kernel`, check 2–5 key variables and cwd, confirm artifacts exist, summarize the
recovered state in 2–4 lines. If objects are missing, rebuild only those from notebook cells or
saved files. If several state files could match, ask rather than guessing.
