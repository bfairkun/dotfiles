---
name: agent-plots
description: How to share plots and tables with the user. Invoke when saving any plot or dataframe (Python/R/ggplot/matplotlib/etc.) so it appears in the user's browser.
---

# Agent Plots Workflow

Machine-specific paths are in `AGENTS.local.md → Agent Reference` (always in context).
- **HPC**: HTTP server + SSH tunnel → user browses `http://localhost:<port>`. Great Lakes uses 8765; RCC Midway uses **8775** (auto-shifts to 8776-8779 if another user holds it). Separate ranges because the Mac often has both tunnels open, and whichever connects first owns shared laptop ports.
- **Mac**: save to file, tell user path — they open in Finder/Preview

## Workflow

1. **Detect `outdir` and `port`** — run the Bash snippet below to find where the server is actually serving from and which port it bound. Do NOT hardcode `~/agent_plots` or `8765`; the directory may point to a scratch filesystem and the port may have shifted.
2. Save the plot to that `outdir`
3. Tell the user the filename
4. On HPC SSH: "check `http://localhost:<port>`"
5. If user asks to see it on remote control, or asks to send/post it to Slack: see the `post-to-slack` skill (save as PNG first — Slack previews PNG inline, not PDF) — or use the `Read` tool to embed inline
6. **Embed inline** (`Read` tool) only when user asks, or you need to interpret the plot to continue

### Detect outdir and port (run this first, every time)

```bash
# Extract --directory from the running server process; fall back to ~/agent_plots
python3 -c "
import subprocess, re, os
r = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
m = re.search(r'agent_plots_server.*?--directory\s+(\S+)', r.stdout)
print(m.group(1) if m else os.path.expanduser('~/agent_plots'))
"
# Port the server actually bound (RCC Midway: 8775-8779; GreatLakes/Mac: 8765)
cat ~/.agent_plots_port 2>/dev/null || echo 8765
```

Use the printed path/port as `outdir`/`port` in all code below. If the outdir fallback fires, warn the user the server may not be running.

## PDF vs PNG

**Always PDF** — vector, crisp at any zoom. Exception: >1000 labeled text elements → PNG (PDF text layer bloats context).
- Data points/lines/bars → zero extra tokens in PDF regardless of count
- Text elements (tick labels, gene names) → cost tokens
- PNG cost is fixed by image dimensions

## Python / matplotlib

```python
import os
# outdir detected via Bash snippet above — paste the result here
outdir = "/path/from/detect/step"
os.makedirs(outdir, exist_ok=True)
fig.savefig(os.path.join(outdir, "myplot.pdf"), bbox_inches="tight")
plt.close(fig)
print(f"Saved → check http://localhost:{port}/myplot.pdf")
```

## R / ggplot2

```r
outdir <- "/path/from/detect/step"  # from Bash detect snippet
dir.create(outdir, showWarnings = FALSE, recursive = TRUE)
ggsave(file.path(outdir, "myplot.pdf"), plot = p, width = 7, height = 5)
cat(paste0("Saved → check http://localhost:", port, "/myplot.pdf\n"))
```

## R / base graphics

```r
outdir <- "/path/from/detect/step"  # from Bash detect snippet
pdf(file.path(outdir, "myplot.pdf"), width = 7, height = 5)
# ... plot code ...
dev.off()
```

## Tables / DataFrames

### Python / pandas

```python
import os, pandas as pd
outdir = "/path/from/detect/step"  # from Bash detect snippet
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
outdir <- "/path/from/detect/step"  # from Bash detect snippet
# selfcontained=TRUE requires pandoc (not available on HPC); FALSE creates mytable_files/ dir alongside
DT::saveWidget(
  DT::datatable(df, rownames = FALSE, filter = "top", options = list(pageLength = 25)),
  file = file.path(outdir, "mytable.html"), selfcontained = FALSE
)
```

## Infrastructure

- Server auto-started at login via `*rc_local`, port 8765 on Great Lakes, 8775 on RCC Midway (auto-retries the next 4 ports if another user holds it — see `~/.agent_plots_port`); its `--directory` may point to scratch, not `~/agent_plots` — always detect before saving (see above)
- If not running: check `*rc_local` for the correct start command and directory; do not assume `~/agent_plots`
- SSH tunnel: Mac `~/.ssh/config` (`dotfiles/local_dotfiles_MEDGEN_MacbookAir/.ssh/config`) forwards 8765-8768 in the `greatlakes` block and 8775-8779 in the `midway*` block, always to `127.0.0.1`. If a Midway port shows nothing while the server answers on the cluster, run `lsof -nP -iTCP:<port> -sTCP:LISTEN` on the Mac to see which ssh owns it. With `ControlMaster`/`ControlPersist 24h`, a config change takes effect only after `ssh -O exit <host>`.
- **Sending a file to Slack** (plot or otherwise): see the `post-to-slack` skill.

## Troubleshooting: browser gets an empty reply

Symptom: the browser shows nothing (curl exit 52) while `curl 127.0.0.1:<port>` on the HPC
returns 200 — so the server is healthy and the tunnel is the problem.

Cause: the server binds `0.0.0.0` (IPv4 only), and its port retry only detects IPv4 conflicts,
so an IPv6-only listener on the same port is invisible to it. Remote `localhost` resolves to
`::1` first, so `LocalForward PORT localhost:PORT` silently tunnels into that other process.

Diagnose with `ss -ltnp | grep :PORT` — a `[::1]:PORT` line with no owning user is another
user's process. The Mac SSH config forwards to `127.0.0.1:PORT`, never `localhost:PORT`.
