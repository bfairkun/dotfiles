---
name: interactive-notebook
description: >
  Interactively co-author a Quarto notebook with the user: create the .qmd skeleton,
  open the right kernel (Python or R), explore and iterate code via the kernel,
  save plots to agent_plots for the user to see, and write finalized cells back
  into the notebook file bit by bit.
argument-hint: "[brief description of notebook idea, and Python or R]"
---

# Interactive Notebook Co-authoring Workflow

This is the end-to-end workflow for iteratively building a Quarto notebook together with the user.

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

AGENT_PLOTS = os.path.expanduser("~/agent_plots")  # AGENT_PLOTS from CLAUDE_local.md
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

agent_plots <- path.expand("~/agent_plots")  # AGENT_PLOTS from CLAUDE_local.md
```
````

---

## Step 2 — Open the kernel

### Python kernel

The MCP server auto-attaches to the newest running kernel (VSCode or standalone).

- If the user has VSCode open with a Python cell already run → just start — it will auto-attach.
- Otherwise, start a **persistent login-node kernel** using `nohup` (survives compaction and client restarts):

```bash
nohup conda run -n py_general jupyter kernel \
  --KernelManager.connection_file=/tmp/agent_kernel_login.json \
  &> /tmp/agent_kernel_login.log &
```

Then connect:
```python
# connect_to_kernel(connection_file="/tmp/agent_kernel_login.json")
```

**Do not use `start_kernel`** for persistent login-node kernels: its child process dies when the MCP server restarts. The `nohup` kernel is independent.

- Verify: `import socket; print(socket.gethostname())`

For compute-heavy work: ask the user to run `start_agent_kernel` first, then connect with `KERNEL_CF` from `CLAUDE_local.md`.

### R kernel

Ask the user to run:
```bash
start_agent_kernel --lang r          # submits an R kernel to a compute node
```

Then call `connect_to_kernel` using the R `KERNEL_CF` from `AGENTS.local.md`.

Send plain R code via `run_python` — the kernel is R, so no `%%R` magic is needed.

Verify: `cat(R.version.string, "\n"); cat("Host:", system("hostname", intern=TRUE), "\n")`

### After connecting — session state files

State files go to `STATE_MD` / `STATE_JSON` from `CLAUDE_local.md` (NFS-shared, readable from login node immediately). Browsable at:
- `http://localhost:8765/state.md`
- `http://localhost:8765/state.json`

### After connecting — install session checkpoint helpers immediately

Do this before substantial exploration so the session can survive context compaction.

### Python helper

Run this in the kernel after connect, then keep using `save_session_state(...)`:

```python
import json
import os
from pathlib import Path

STATE_MD   = Path(os.path.expanduser("~/agent_plots/state.md"))   # STATE_MD from CLAUDE_local.md
STATE_JSON = Path(os.path.expanduser("~/agent_plots/state.json")) # STATE_JSON from CLAUDE_local.md
AGENT_PLOTS = Path(os.path.expanduser("~/agent_plots"))            # AGENT_PLOTS from CLAUDE_local.md

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

state_md   <- path.expand("~/agent_plots/state.md")   # STATE_MD from CLAUDE_local.md
state_json <- path.expand("~/agent_plots/state.json") # STATE_JSON from CLAUDE_local.md

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
2. **Save plots** to `AGENT_PLOTS` (from `CLAUDE_local.md`) so the user can see them at http://localhost:8765.
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
outdir = os.path.expanduser("~/agent_plots")  # AGENT_PLOTS from CLAUDE_local.md
fig.savefig(os.path.join(outdir, "myplot.pdf"), bbox_inches="tight")
plt.close(fig)
print(f"Saved → check http://localhost:8765/myplot.pdf")
```

### R (ggplot2)

```r
outdir <- path.expand("~/agent_plots")  # AGENT_PLOTS from CLAUDE_local.md
ggsave(file.path(outdir, "myplot.pdf"), plot = p, width = 7, height = 5)
cat("Saved → check http://localhost:8765/myplot.pdf\n")
```

### R (base graphics)

```r
outdir <- path.expand("~/agent_plots")  # AGENT_PLOTS from CLAUDE_local.md
pdf(file.path(outdir, "myplot.pdf"), width = 8, height = 6)
# ... plot code ...
dev.off()
```

Always tell the user: **"Check http://localhost:8765/myplot.pdf"**

---

## Step 5 — Writing finalized code back to the notebook

Use the `Edit` tool to append a new chunk at the end of the `.qmd` file after each
exploration round is validated. Keep the notebook source in sync with what the kernel
has actually run.

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

- `http://localhost:8765/state.md`
- `http://localhost:8765/state.json`

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
- **Login node by default** — only escalate to a compute kernel if memory is a problem.
- **Checkpoint state routinely** — treat `state.md` and `state.json` as part of the notebook workflow, not an emergency fallback.
- **Preserve only resumable facts** — save compact metadata, not raw command history.
