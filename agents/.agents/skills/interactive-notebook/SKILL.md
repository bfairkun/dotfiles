---
name: interactive-notebook
description: >
  Interactively co-author a Quarto notebook with the user: create the .qmd, explore in a
  Jupyter kernel (Python or R), show plots via agent_plots, write validated cells back into the
  notebook one at a time, and confirm the user's interpretations before rendering.
argument-hint: "[brief description of notebook idea, and Python or R]"
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
- After each result, ask before moving on. Record anything the user says about **how they read a
  result** — those words are the source for the notebook's unsigned interpretation.

## 4. Write to the notebook

After a result is validated, append the chunk and its prose together with `Edit` (never batch
all cells at the end; never write unvalidated code). Per `new-notebook`: methods above, figure,
caption below, then at most a short result statement. Use `#|` chunk options
(`label: fig-...`, `fig-cap:`, `fig-width:`, `fig-height:`).

After each prose edit run `preview_notebook analysis/YYYYMMDD_name.qmd`; it writes
`<stem>.preview.html` to agent_plots (prose rendered, code collapsed, auto-reloads). Give the URL
once per notebook.

## 5. Pre-render interpretation check

Before the first render, and again before any render after new results were added:

1. List each key result (usually one per figure) and every interpretive sentence currently in
   the draft, marking which came from the user and which the agent wrote.
2. Ask with `AskUserQuestion` (≤4 questions per call; repeat calls as needed):
   - One question per key result: "How do you read Fig N (<short description>)?", `multiSelect:
     true`, 2–4 short candidate readings in plain language, including a cautious/"no clear
     effect" option. The user can pick several or write their own via Other.
   - One question listing agent-written interpretations: keep unsigned (user endorses), keep as
     signed agent callout, or delete.
   - If relevant: "Is anything you concluded during the session missing from the notebook?"
3. Rewrite the result/summary text from the answers only: selected readings become unsigned
   prose; unselected agent text is deleted or moved into a signed callout as the user chose.
4. Update the preview, then render.

## 6. Render

```bash
conda run -n py_general render_notebook render analysis/YYYYMMDD_name.qmd   # Python
render_notebook render analysis/YYYYMMDD_name.qmd                            # R
```

## Session state (survive compaction)

After connecting, after each validated chunk, and before switching to writing, overwrite
`<AGENT_PLOTS>/state.md` with: kernel id / connection file, notebook path, cwd, language; key
variables with type and shape; saved artifacts; goal, what was learned (including the user's
stated interpretations), and the exact next step. Keep it short — metadata, not history.

After compaction: read `state.md`, reconnect with `connect_to_kernel`, check 2–5 key variables and
cwd, confirm artifacts exist, summarize the recovered state in 2–4 lines. If objects are missing,
rebuild only those from notebook cells or saved files.
