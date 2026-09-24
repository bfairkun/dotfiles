---
name: interactive-notebook
description: >
  Interactively co-author a Quarto notebook with the user: create the .qmd skeleton,
  explore and iterate code via a Jupyter kernel (Python or R),
  save plots to agent_plots for the user to see, and write finalized cells back
  into the notebook file bit by bit.
argument-hint: "[brief description of notebook idea, and Python or R]"
---

# Interactive Notebook Co-authoring Workflow

This is the end-to-end workflow for iteratively building a Quarto notebook together with the user.

`<AGENT_PLOTS>` and `<AGENT_PLOTS_URL>` below are **placeholders, not paths**. Resolve both
before writing any code that uses them — see the `agent-plots` skill. Do not write to
`~/agent_plots`: that is not the directory the server serves, and plots put there are invisible
to the user.

---

## Step 1 — Create the notebook skeleton

Name: `analysis/YYYYMMDD_descriptive_name.qmd` (today's date, underscores, lowercase).

### Python skeleton

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

```python
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

AGENT_PLOTS = "<AGENT_PLOTS>"  # resolve first -- see `agent-plots` skill
```

### R skeleton

```yaml
---
title: "Descriptive Title"
format:
  html:
    code-fold: true
    toc: true
execute:
  echo: true
  warning: false
  message: false
---
```

````
```{r setup}
#| include: false
library(tidyverse)
library(data.table)

theme_set(theme_bw(base_size = 12))

agent_plots <- "<AGENT_PLOTS>"  # resolve first -- see `agent-plots` skill
```
````

---

## Step 2 — Open the kernel

**Use a compute-node kernel unless the user says otherwise.** Start it yourself; do not ask
the user to run anything.

See the `compute-kernel` skill for how — submitting the job, the IP bind, polling for
readiness, connecting, wall-time autosave, and recovery when a kernel dies. Python and R
differ only in the flag (`start_agent_kernel --lang r`) and the connection file.

Exception: if the user already has a VSCode kernel running with a cell executed, the MCP
server auto-attaches to it, so just start working.

Send plain R code via `run_python` — the kernel is R, so no `%%R` magic is needed.

### After connecting — session state files

State files go to `STATE_MD` / `STATE_JSON` from `CLAUDE_local.md` (NFS-shared, readable from login node immediately). Browsable at:
- `<AGENT_PLOTS_URL>/state.md`
- `<AGENT_PLOTS_URL>/state.json`

### After connecting — install session checkpoint helpers immediately

Do this before substantial exploration so the session can survive context compaction.

### Python helper

Run this in the kernel after connect, then keep using `save_session_state(...)`:

```python
import json
import os
from pathlib import Path

AGENT_PLOTS = Path("<AGENT_PLOTS>")   # resolve first -- see `agent-plots` skill
STATE_MD    = AGENT_PLOTS / "state.md"
STATE_JSON  = AGENT_PLOTS / "state.json"

def _summarize_py_value(name, value):
    summary = {"name": name, "type": type(value).__name__}
    if hasattr(value, "shape"):
        try:
            shape = value.shape
            summary["shape"] = list(shape) if not isinstance(shape, str) else shape
        except Exception:
            pass
    if hasattr(value, "columns"):
        try:
            cols = list(value.columns)
            summary["columns"] = cols[:12]
            if len(cols) > 12:
                summary["columns_truncated"] = True
        except Exception:
            pass
    if hasattr(value, "dtype"):
        try:
            summary["dtype"] = str(value.dtype)
        except Exception:
            pass
    return summary

def save_session_state(
    notebook_path,
    goal,
    learned,
    next_step,
    key_vars=None,
    artifacts=None,
    language="Python",
):
    key_vars = key_vars or []
    artifacts = artifacts or []
    namespace = []
    for name in key_vars:
        if name in globals():
            namespace.append(_summarize_py_value(name, globals()[name]))
        else:
            namespace.append({"name": name, "missing": True})

    payload = {
        "kernel_id": "{kernel_id}",
        "language": language,
        "notebook_path": notebook_path,
        "cwd": os.getcwd(),
        "imports_loaded": sorted(
            name for name, value in globals().items() if getattr(value, "__class__", None).__name__ == "module"
        ),
        "key_variables": namespace,
        "artifacts": artifacts,
        "goal": goal,
        "learned": learned,
        "next_step": next_step,
    }

    STATE_JSON.write_text(json.dumps(payload, indent=2))

    lines = [
        "## Kernel",
        f"- kernel_id: {payload['kernel_id']}",
        f"- notebook: {notebook_path}",
        f"- language: {language}",
        f"- cwd: {payload['cwd']}",
        "",
        "## Namespace",
    ]
    for item in namespace:
        if item.get("missing"):
            lines.append(f"- {item['name']}: MISSING")
            continue
        details = [item["type"]]
        if "shape" in item:
            details.append(f"shape={item['shape']}")
        if "dtype" in item:
            details.append(f"dtype={item['dtype']}")
        if "columns" in item:
            details.append(f"columns={item['columns']}")
        lines.append(f"- {item['name']}: " + ", ".join(details))

    lines.extend([
        "",
        "## Session Context",
        f"- goal: {goal}",
        f"- what_we_learned: {learned}",
        f"- next_step: {next_step}",
        "",
        "## Artifacts",
    ])
    for artifact in artifacts:
        lines.append(f"- {artifact}")

    STATE_MD.write_text("\n".join(lines) + "\n")
    print(f"Updated {STATE_MD}")
    print(f"Updated {STATE_JSON}")
```

### R helper

Run this in the kernel after connect, then keep using `save_session_state(...)`:

```r
library(jsonlite)

agent_plots <- "<AGENT_PLOTS>"   # resolve first -- see `agent-plots` skill
state_md   <- file.path(agent_plots, "state.md")
state_json <- file.path(agent_plots, "state.json")

summarize_r_value <- function(name, env = .GlobalEnv) {
  if (!exists(name, envir = env, inherits = FALSE)) {
    return(list(name = name, missing = TRUE))
  }

  value <- get(name, envir = env, inherits = FALSE)
  out <- list(
    name = name,
    class = paste(class(value), collapse = ", ")
  )

  dims <- dim(value)
  if (!is.null(dims)) {
    out$shape <- as.list(dims)
  } else {
    out$length <- length(value)
  }

  if (is.data.frame(value)) {
    cols <- colnames(value)
    out$columns <- cols[seq_len(min(length(cols), 12))]
    if (length(cols) > 12) out$columns_truncated <- TRUE
  }

  out
}

save_session_state <- function(
  notebook_path,
  goal,
  learned,
  next_step,
  key_vars = character(),
  artifacts = character(),
  language = "R"
) {
  namespace <- lapply(key_vars, summarize_r_value)
  imports_loaded <- loadedNamespaces()

  payload <- list(
    kernel_id = "{kernel_id}",
    language = language,
    notebook_path = notebook_path,
    cwd = getwd(),
    imports_loaded = imports_loaded,
    key_variables = namespace,
    artifacts = artifacts,
    goal = goal,
    learned = learned,
    next_step = next_step
  )

  writeLines(toJSON(payload, auto_unbox = TRUE, pretty = TRUE), state_json)

  lines <- c(
    "## Kernel",
    sprintf("- kernel_id: %s", payload$kernel_id),
    sprintf("- notebook: %s", notebook_path),
    sprintf("- language: %s", language),
    sprintf("- cwd: %s", payload$cwd),
    "",
    "## Namespace"
  )

  for (item in namespace) {
    if (isTRUE(item$missing)) {
      lines <- c(lines, sprintf("- %s: MISSING", item$name))
      next
    }
    details <- c(item$class)
    if (!is.null(item$shape)) details <- c(details, sprintf("shape=%s", paste(unlist(item$shape), collapse = "x")))
    if (!is.null(item$length)) details <- c(details, sprintf("length=%s", item$length))
    if (!is.null(item$columns)) details <- c(details, sprintf("columns=%s", paste(unlist(item$columns), collapse = ", ")))
    lines <- c(lines, sprintf("- %s: %s", item$name, paste(details, collapse = ", ")))
  }

  lines <- c(
    lines,
    "",
    "## Session Context",
    sprintf("- goal: %s", goal),
    sprintf("- what_we_learned: %s", learned),
    sprintf("- next_step: %s", next_step),
    "",
    "## Artifacts"
  )

  if (length(artifacts)) {
    lines <- c(lines, sprintf("- %s", artifacts))
  }

  writeLines(lines, state_md)
  cat("Updated", state_md, "\n")
  cat("Updated", state_json, "\n")
}
```

---

## Step 3 — Iterative exploration loop

The core workflow is: **run → show → discuss → refine → write to notebook**.

1. **Run exploration code** in the kernel (load data, summarize, quick plots).
2. **Save plots** to `<AGENT_PLOTS>` so the user can see them at `<AGENT_PLOTS_URL>`.
3. **Discuss** what the plot shows or what to refine.
4. **Checkpoint session state** with `save_session_state(...)` after every validated milestone.
5. **Write finalized code** back into the `.qmd` file (Edit tool) as a new chunk.
6. Repeat.

Never batch-write all cells at once. Write each chunk after it's been run and validated.
Never rely on chat history alone to preserve the notebook session.

---

## Step 4 — Saving plots during exploration

**Always save as PDF unless the user explicitly requests PNG or another format.**
PDF preserves vector graphics and is the preferred format for inspection and publication.

### Python

```python
import os
outdir = "<AGENT_PLOTS>"  # resolve first -- see `agent-plots` skill
fig.savefig(os.path.join(outdir, "myplot.pdf"), bbox_inches="tight")
plt.close(fig)
print(f"Saved → check <AGENT_PLOTS_URL>/myplot.pdf")
```

### R (ggplot2)

```r
outdir <- "<AGENT_PLOTS>"  # resolve first -- see `agent-plots` skill
ggsave(file.path(outdir, "myplot.pdf"), plot = p, width = 7, height = 5)
cat("Saved → check <AGENT_PLOTS_URL>/myplot.pdf\n")
```

### R (base graphics)

```r
outdir <- "<AGENT_PLOTS>"  # resolve first -- see `agent-plots` skill
pdf(file.path(outdir, "myplot.pdf"), width = 8, height = 6)
# ... plot code ...
dev.off()
```

Always give the user the resolved URL, e.g. **"Check http://localhost:8765/myplot.pdf"**.

---

## Step 5 — Writing finalized code back to the notebook

Use the `Edit` tool to append a new chunk at the end of the `.qmd` file after each
exploration round is validated. Keep the notebook source in sync with what the kernel
has actually run.

Write the surrounding prose at the same time as the chunk, not as a later pass — the
reasoning behind a choice is hardest to reconstruct once the exploration has moved on.
See the `new-notebook` skill for what that prose must cover.

For R chunks use `#|` chunk options (Quarto style, not `{r, echo=FALSE}` header style):

````
```{r}
#| label: fig-expression
#| fig-cap: "Expression across doses"
#| fig-width: 8
#| fig-height: 5

# finalized code here
```
````

### Refresh the prose preview after every write

Immediately after each `Edit` that adds prose to the `.qmd`, run:

```bash
preview_notebook analysis/YYYYMMDD_name.qmd
```

This writes `<stem>.preview.html` into the agent_plots directory: prose rendered
as formatted markdown, code cells collapsed to one-line stubs that expand on
click, and any plots a cell writes hyperlinked. The user reads it in the browser
tab already open for plots, so they can check the prose matches their intent
without opening VS Code. The page reloads itself on change — mention the URL
once per notebook, not on every refresh.

It parses the `.qmd` as text rather than running quarto, so it works on a
half-written notebook whose cells do not execute yet. It never writes to the
`.qmd`.

---

## Step 6 — Rendering (final step only)

Render only when the user wants a polished HTML output — not during exploration.

Use `render_notebook` (a quarto shim in `~/bin/` that records the render env into a hidden block in the `.qmd`; see `compute-kernel` skill):

```bash
# Python
conda run -n py_general render_notebook render analysis/YYYYMMDD_name.qmd

# R (from project root)
render_notebook render analysis/YYYYMMDD_name.qmd
```

---

## Session state — saving context before compaction

Session state is not optional. Write checkpoint files:

- right after kernel connection and helper installation
- after every validated chunk or important branch point
- before any likely context compaction
- before switching from exploration to notebook-writing
- whenever the user asks for a pause, summary, or handoff

**Paths**: `STATE_MD` and `STATE_JSON` from `CLAUDE_local.md`. Browsable at:

- `<AGENT_PLOTS_URL>/state.md`
- `<AGENT_PLOTS_URL>/state.json`

The markdown file is for human browsing. The JSON file is for machine recovery.

Minimum content to include in both:

```markdown
## Kernel
- kernel_id: ...
- notebook: analysis/YYYYMMDD_name.qmd
- language: Python / R
- cwd: ...

## Namespace
- imports: pandas as pd, numpy as np, ...
- key variables: df (shape 1000x20, columns [...]), model, ...

## Session Context
- goal: ...
- what we've learned: ...
- current hypothesis / next step: ...

## Artifacts
- saved plots / tables / files worth reusing
```

Do not try to serialize the whole workspace. Capture only the facts needed to resume:

- connection target and kernel id
- notebook path and cwd
- imports / namespaces loaded
- key variables only, with type and shape-level metadata
- important output artifacts
- concise learned-so-far summary
- exact next step

## Recovery after compaction

After context compaction or context clearing, do this in order:

1. Read `STATE_MD` and `STATE_JSON` (paths from `CLAUDE_local.md`).
2. Reconnect to the same kernel with `connect_to_kernel`.
3. Verify sentinel objects still exist by checking 2-5 key variables named in the state file.
4. Verify `getwd()` / `os.getcwd()` and notebook path still match the saved state.
5. If artifacts are referenced, confirm the files still exist.
6. Summarize the recovered state to the user in 2-4 lines before continuing.

If verification fails, do not blindly recreate the whole session. State what is missing, then
rebuild only the missing objects from notebook code, saved files, or compact reproducible cells.

---

## Key principles

- **Explore in kernel, write to file** — never write unvalidated code into the notebook.
- **Plot early and often** — every interesting intermediate should be saved to agent_plots.
- **One chunk at a time** — write cells to the .qmd incrementally, not all at once.
- **Ask before moving on** — after each plot/result, confirm with the user before proceeding.
- **Compute node by default** — see the `compute-kernel` skill; use a login-node kernel only when the user asks for one.
- **Checkpoint state routinely** — treat `state.md` and `state.json` as part of the notebook workflow, not an emergency fallback.
- **Preserve only resumable facts** — save compact metadata, not raw command history.
