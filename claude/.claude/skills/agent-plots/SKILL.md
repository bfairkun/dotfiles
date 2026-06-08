---
name: agent-plots
description: How to share plots and tables with the user. Invoke when saving any plot or dataframe (Python/R/ggplot/matplotlib/etc.) so it appears in the user's browser.
---

# Agent Plots Workflow

Machine-specific paths are in `CLAUDE_local.md → Agent Reference` (always in context).
- **HPC**: HTTP server on port 8765 + SSH tunnel → user browses `http://localhost:8765`
- **Mac**: save to file, tell user path — they open in Finder/Preview

## Workflow

1. Save to `AGENT_PLOTS` dir (from `CLAUDE_local.md`; Mac: `~/Documents/agent_plots/`)
2. Tell the user the filename
3. On HPC SSH: "check `http://localhost:8765`"
4. If user asks to see it on remote control: run `post_plot_to_slack <filepath>` (save as PNG first — Slack previews PNG inline, not PDF) or use `Read` tool to embed inline
5. **Embed inline** (`Read` tool) only when user asks, or you need to interpret the plot to continue

## PDF vs PNG

**Always PDF** — vector, crisp at any zoom. Exception: >1000 labeled text elements → PNG (PDF text layer bloats context).
- Data points/lines/bars → zero extra tokens in PDF regardless of count
- Text elements (tick labels, gene names) → cost tokens
- PNG cost is fixed by image dimensions

## Python / matplotlib

```python
import os
outdir = os.path.expanduser("~/agent_plots")  # AGENT_PLOTS from CLAUDE_local.md
os.makedirs(outdir, exist_ok=True)
fig.savefig(os.path.join(outdir, "myplot.pdf"), bbox_inches="tight")
plt.close(fig)
print("Saved → check http://localhost:8765/myplot.pdf")
```

## R / ggplot2

```r
outdir <- path.expand("~/agent_plots")  # AGENT_PLOTS from CLAUDE_local.md
dir.create(outdir, showWarnings = FALSE, recursive = TRUE)
ggsave(file.path(outdir, "myplot.pdf"), plot = p, width = 7, height = 5)
cat("Saved → check http://localhost:8765/myplot.pdf\n")
```

## R / base graphics

```r
outdir <- path.expand("~/agent_plots")  # AGENT_PLOTS from CLAUDE_local.md
pdf(file.path(outdir, "myplot.pdf"), width = 7, height = 5)
# ... plot code ...
dev.off()
```

## Tables / DataFrames

### Python / pandas

```python
import os, pandas as pd
outdir = os.path.expanduser("~/agent_plots")  # AGENT_PLOTS from CLAUDE_local.md
html = df.to_html(index=False, border=0, classes="display", table_id="datatable")
page = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>DataFrame</title>
  <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
  <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
  <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
  <style>body{{font-family:sans-serif;padding:20px}}</style></head><body>
{html}
<script>$(document).ready(function(){{$('#datatable').DataTable();}});</script>
</body></html>"""
with open(os.path.join(outdir, "mytable.html"), "w") as f:
    f.write(page)
```

### R / DT

```r
outdir <- path.expand("~/agent_plots")  # AGENT_PLOTS from CLAUDE_local.md
# selfcontained=TRUE requires pandoc (not available on HPC); FALSE creates mytable_files/ dir alongside
DT::saveWidget(
  DT::datatable(df, rownames = FALSE, filter = "top", options = list(pageLength = 25)),
  file = file.path(outdir, "mytable.html"), selfcontained = FALSE
)
```

## Infrastructure

- Server auto-started at login via `*rc_local`, port 8765
- If not running: `nohup python3 ~/bin/agent_plots_server.py --port 8765 --directory ~/agent_plots > ~/agent_plots/server.log 2>&1 &`
- SSH tunnel: `LocalForward 8765 localhost:8765` in local `~/.ssh/config`
- **Slack upload:** `post_plot_to_slack <filepath> [channel_id]` — posts to Slack DM via `hpc_agent_plots` bot. Token in `$SLACK_PLOT_TOKEN` (`~/.secrets`). Default channel in `~/.config/slack_plot_channel` (your Slack user ID). To post to a lab channel: invite `@hpc_agent_plots` then pass its channel ID. Bot token does not expire. New machine: add `SLACK_PLOT_TOKEN` to `~/.secrets`, create `~/.config/slack_plot_channel` with your Slack user ID.
