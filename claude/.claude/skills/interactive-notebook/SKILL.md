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

# Plot output dir
AGENT_PLOTS = os.path.expandvars("$SCRATCH/$USER/agent_plots")
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

agent_plots <- file.path(Sys.getenv("SCRATCH"), Sys.getenv("USER"), "agent_plots")
```
````

---

## Step 2 — Open the kernel

### Python kernel

The MCP server auto-attaches to the newest running kernel (VSCode or standalone).

- If the user has VSCode open with a Python cell already run → just start — it will auto-attach.
- Otherwise use `mcp__jupyter-kernel__start_kernel` (starts a fresh `py_general` kernel).
- Verify: `import socket; print(socket.gethostname())`

For compute-heavy work: ask the user to run `start_agent_kernel` first, then use
`mcp__jupyter-kernel__connect_to_kernel` with `/scratch/midway3/bjf79/agent_kernel.json`.

### R kernel

Ask the user to run:
```bash
start_agent_kernel --lang r          # submits an R kernel to a compute node
```

Then connect:
```python
# via mcp__jupyter-kernel__connect_to_kernel
# connection file: /scratch/midway3/bjf79/agent_r_kernel.json
```

Send plain R code via `mcp__jupyter-kernel__run_python` — the kernel IS R, no `%%R` needed.

Verify: `cat(R.version.string, "\n"); cat("Host:", system("hostname", intern=TRUE), "\n")`

### After connecting — set up session state symlink

Once you have the kernel ID, immediately create a symlink so the state file is browsable:

```bash
ln -sf /tmp/claude_kernel_{kernel_id}_state.md $SCRATCH/$USER/agent_plots/state.md
```

This symlink costs nothing to update and lets the user browse `http://localhost:8765/state.md`.

---

## Step 3 — Iterative exploration loop

The core workflow is: **run → show → discuss → refine → write to notebook**.

1. **Run exploration code** in the kernel (load data, summarize, quick plots).
2. **Save plots** to `$SCRATCH/$USER/agent_plots/` so the user can see them at http://localhost:8765.
3. **Discuss** what the plot shows or what to refine.
4. **Write finalized code** back into the `.qmd` file (Edit tool) as a new chunk.
5. Repeat.

Never batch-write all cells at once. Write each chunk after it's been run and validated.

---

## Step 4 — Saving plots during exploration

**Always save as PDF unless the user explicitly requests PNG or another format.**
PDF preserves vector graphics and is the preferred format for inspection and publication.

### Python

```python
import os
outdir = os.path.expandvars("$SCRATCH/$USER/agent_plots")
fig.savefig(os.path.join(outdir, "myplot.pdf"), bbox_inches="tight")
plt.close(fig)
print(f"Saved → check http://localhost:8765/myplot.pdf")
```

### R (ggplot2)

```r
outdir <- file.path(Sys.getenv("SCRATCH"), Sys.getenv("USER"), "agent_plots")
ggsave(file.path(outdir, "myplot.pdf"), plot = p, width = 7, height = 5)
cat("Saved → check http://localhost:8765/myplot.pdf\n")
```

### R (base graphics)

```r
outdir <- file.path(Sys.getenv("SCRATCH"), Sys.getenv("USER"), "agent_plots")
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

```bash
# Python
conda run -n py_general quarto render analysis/YYYYMMDD_name.qmd

# R (from project root)
quarto render analysis/YYYYMMDD_name.qmd
```

---

## Session state — saving context before compaction

When the conversation is getting long, or when the user asks, write a session state file:

**Path**: `/tmp/claude_kernel_{kernel_id}_state.md`
**Browsable mirror**: `$SCRATCH/$USER/agent_plots/state.md` (symlink set up at kernel open)

Content to include:

```markdown
## Kernel
- kernel_id: ...
- notebook: analysis/YYYYMMDD_name.qmd
- language: Python / R

## Namespace
- imports: pandas as pd, numpy as np, ...
- key variables: df (shape 1000x20, ...), model, ...

## Session Context
- goal: ...
- what we've learned: ...
- current hypothesis / next step: ...
```

After context compaction, read `/tmp/claude_kernel_{kernel_id}_state.md` to catch up, then
reconnect to the kernel with `mcp__jupyter-kernel__connect_to_kernel`.

---

## Key principles

- **Explore in kernel, write to file** — never write unvalidated code into the notebook.
- **Plot early and often** — every interesting intermediate should be saved to agent_plots.
- **One chunk at a time** — write cells to the .qmd incrementally, not all at once.
- **Ask before moving on** — after each plot/result, confirm with the user before proceeding.
- **Login node by default** — only escalate to a compute kernel if memory is a problem.
- **Save session state proactively** — write state file at natural milestones and before context gets heavy.
