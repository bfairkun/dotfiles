---
name: agent-plots
description: How to share plots and tables with the user. Invoke when saving any plot or dataframe (Python/R/ggplot/matplotlib/etc.) so it appears in the user's browser.
---

# Agent Plots Workflow

## Which machine am I on?

**Local Mac (dotfiles working dir, `/Users/bjf79/...`):**
- Plots directory: `~/Documents/agent_plots/`
- User runs Claude in tmux, so inline terminal image rendering doesn't work
- Save the file, tell the user the path — they open it in Finder/Preview
- Only use the `Read` tool to embed inline if asked, or to interpret the plot yourself

**HPC (Midway2/Midway3, `/home/bjf79/...` or `/project/...`):**
- Plots directory: `$SCRATCH/$USER/agent_plots/` (explicit: `/scratch/midway3/bjf79/agent_plots`)
- Views via two mechanisms depending on connection type:
  1. **SSH session** — HTTP server on port 8765 + SSH tunnel → user browses `http://localhost:8765`
  2. **Remote control (Claude web UI, no SSH tunnel)** — use the `Read` tool to embed inline

## Workflow for plots

**On Mac:**
1. Save to `~/Documents/agent_plots/myplot.pdf`
2. Tell the user the filename — they open it in Finder/Preview

**On HPC:**
1. Save to `$SCRATCH/$USER/agent_plots/`
2. Tell the user the filename and to check `http://localhost:8765` if on SSH
3. **Only use the `Read` tool to embed inline** when:
   - The user is on remote control and asks to see it, OR
   - The user explicitly asks to see it inline, OR
   - You need to interpret the plot to continue the analysis

Inline reading costs context tokens (image bytes encoded into the conversation). Don't do it automatically — let the user ask.

## PDF vs PNG — saving and reading

**Always save as PDF by default.** PDF is vector, so it renders crisply at any zoom and the text layer makes it far more useful when read inline. The only exception is when the plot will have **>1000 labeled text objects** (e.g. thousands of gene-name annotations rendered as individual text elements), where PDF text extraction would bloat the agent's context window — in that case, save as PNG instead.

Key facts for inline reading:
- Data points (dots, lines, bars) are vector graphics — they add **zero** extra tokens in PDF regardless of how many there are
- Only *text elements* (tick labels, gene names, legends) cost tokens in PDF
- PNG costs are fixed by image dimensions/DPI regardless of text content

**Rule of thumb:** a scatter with 10k unlabeled dots → PDF fine. A plot with 2000 individual gene-name tick labels → use PNG.

**Code examples — save as PDF:**

```python
fig.savefig(os.path.join(outdir, "myplot.pdf"), bbox_inches="tight")
```

```r
ggsave(file.path(outdir, "myplot.pdf"), plot = p, width = 7, height = 5)
```

For tables (HTML), the HTTP server is the only option — tell the user to check `http://localhost:8765`.

## Infrastructure

- **Plots directory:** shell convention is `$SCRATCH/$USER/agent_plots/`; for this Midway3 setup the explicit absolute path is `/scratch/midway3/bjf79/agent_plots`.
- **HTTP server:** `~/bin/agent_plots_server.py` (stowed from dotfiles), port **8765**, auto-started at login via `~/.zshrc_local`. Serves directory with toggleable sort order (`?sort=name` vs `?sort=mtime`, default mtime).
- **SSH tunnel:** `LocalForward 8765 localhost:8765` in the user's local `~/.ssh/config`
- **public_html:** Midway2 only (home dirs are NOT shared across Midway2/Midway3). URL: `http://users.rcc.uchicago.edu/~bjf79/`. Not currently set up.

## Plots

### Python / matplotlib

```python
import os
scratch = os.environ.get("SCRATCH")
if scratch:
    outdir = os.path.join(scratch, os.environ["USER"], "agent_plots")  # HPC
else:
    outdir = os.path.expanduser("~/Documents/agent_plots")              # Mac
fig.savefig(os.path.join(outdir, "myplot.pdf"), bbox_inches="tight")
# Use .png only if plot has thousands of text labels (e.g. gene name tick labels)
```

### R / ggplot2

```r
scratch <- Sys.getenv("SCRATCH")
outdir <- if (nchar(scratch) > 0) file.path(scratch, Sys.getenv("USER"), "agent_plots") else path.expand("~/Documents/agent_plots")
ggsave(file.path(outdir, "myplot.pdf"), plot = p, width = 7, height = 5)
# Use .png only if plot has thousands of text labels
```

### R / base graphics

```r
scratch <- Sys.getenv("SCRATCH")
outdir <- if (nchar(scratch) > 0) file.path(scratch, Sys.getenv("USER"), "agent_plots") else path.expand("~/Documents/agent_plots")
pdf(file.path(outdir, "myplot.pdf"), width = 7, height = 5)
# ... plot code ...
dev.off()
```

## Tables / DataFrames

### Python / pandas

Saves as a single self-contained HTML using DataTables JS loaded from CDN (requires internet).

```python
import os, pandas as pd

scratch = os.environ.get("SCRATCH")
if scratch:
    outdir = os.path.join(scratch, os.environ["USER"], "agent_plots")  # HPC
else:
    outdir = os.path.expanduser("~/Documents/agent_plots")              # Mac
html = df.to_html(index=False, border=0, classes="display", table_id="datatable")

page = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>DataFrame</title>
  <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
  <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
  <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
  <style>body {{ font-family: sans-serif; padding: 20px; }}</style>
</head>
<body>
{html}
<script>$(document).ready(function() {{ $('#datatable').DataTable(); }});</script>
</body>
</html>"""

with open(os.path.join(outdir, "mytable.html"), "w") as f:
    f.write(page)
```

### R / DT

Note: `selfcontained = TRUE` requires pandoc, which is not available on this HPC. Without it, `saveWidget` creates an HTML file + a `mytable_files/` directory of local assets alongside it. Both are served by the HTTP server so it works fine in the browser — just not a true single file.

```r
library(DT)
outdir <- file.path(Sys.getenv("SCRATCH"), Sys.getenv("USER"), "agent_plots")

DT::saveWidget(
  DT::datatable(df, rownames = FALSE, filter = "top",
                options = list(pageLength = 25)),
  file = file.path(outdir, "mytable.html"),
  selfcontained = FALSE   # pandoc not available; creates mytable_files/ dir
)
```

## If the server isn't running

```bash
nohup python3 -m http.server 8765 --directory $SCRATCH/$USER/agent_plots > $SCRATCH/$USER/agent_plots/server.log 2>&1 &
```
