---
name: colab-mcp
description: Interactively author, edit, and run cells in a Google Colab notebook through the colab-mcp browser bridge while the user watches in Chrome. Invoke when the user wants the agent to work in a live Colab session. For runtime errors, use the `colab-debug` skill instead.
---

# Colab via MCP bridge

The `colab-mcp` MCP (registered user-scope) bridges this session to a Colab tab in
the user's browser. The user sees everything live; plots and tables render natively in
that tab — do NOT push them through `agent_plots/`.

## Architecture (short version, useful when things break)

- The MCP runs a localhost WebSocket gated by a one-time token, and exposes exactly
  one entry tool: `open_colab_browser_connection`.
- Calling that tool opens `https://colab.research.google.com/notebooks/empty.ipynb`
  with `#mcpProxyToken=...&mcpProxyPort=...` in the fragment. Colab's frontend JS
  reads the fragment and opens a WebSocket back to localhost.
- Once the socket is up, the Colab frontend acts as an MCP server over the socket;
  the Python side proxies its tools out. Cell-editing tools therefore live in the
  Colab frontend, not the Python repo, and appear in the tool list dynamically via
  `notifications/tools/list_changed`.

## Setup quirk: Chromium browser required

Safari silently blocks the localhost WebSocket from `colab.research.google.com`
(Private Network Access rules). Chrome / Brave / Arc / other Chromium browsers work.

This dotfiles repo's installation wires a `BROWSER` env var on the MCP entry in
`~/.claude.json` so the MCP spawns Chrome directly regardless of macOS default
browser:
```
claude mcp add --scope user -e "BROWSER=/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" -- colab-mcp uvx git+https://github.com/googlecolab/colab-mcp
```
The `--` separator matters — without it, the variadic `-e` swallows the server name.
If a future machine doesn't have this wired and Safari is default, the bridge will
appear to "do nothing" with no error.

## Connecting

1. **Warn the user up front** that they have **60 seconds** after the call before the
   tool times out. Missing the window appears to permanently break the bridge for the
   MCP process lifetime (`_start_task` gets cancelled with no re-creation path) —
   recovery is `/quit` + restart, not retry.
2. Tell the user the Chrome tab is about to open; they should make sure Chrome is
   already running and signed into Google.
3. Call `open_colab_browser_connection`. Returns `true` on success, `false` on timeout.
4. If `false`: do not retry in the same session. Have the user restart the client.
   The cell-editing tools won't appear after a missed handshake.

## Tool surface (post-connect)

| Tool | Purpose |
|---|---|
| `add_code_cell(cellIndex, language, code)` | Insert code cell. `language`: `python` / `r` / `julia`. Returns `newCellId`. |
| `add_text_cell(cellIndex, content)` | Insert markdown cell. Supports Markdown + LaTeX (`$...$`, `$$...$$`). Returns `newCellId`. |
| `update_cell(cellId, content)` | Overwrite cell source. Works on both code and markdown cells. |
| `delete_cell(cellId)` | Remove cell. |
| `move_cell(cellId, cellIndex)` | Reorder. |
| `get_cells(cellIndexStart?, cellIndexEnd?, includeOutputs?)` | Read notebook state. `includeOutputs=true` returns cached outputs from prior runs. |
| `run_code_cell(cellId)` | Execute. **Blocks until completion** — heavy cells tie up the bridge for their full runtime. |

`cellIndex` is the insertion point in the *current* notebook; existing cells shift to
make room. For "append to end," `get_cells` first to find the count.

## Kernel and inspection

- Single shared kernel; variables persist across cells.
- **No state-introspection tool.** To check a variable / DataFrame shape / file
  existence, write a probe cell (`print(x)`, `df.head()`, `!ls`), run it, read the
  output, then `delete_cell` if it was throwaway.
- `run_code_cell` is blocking, not streaming. A 10-minute training cell ties up the
  bridge for 10 minutes.

## Output format reference

`run_code_cell` returns `{"outputs": [...]}` where each item has `output_type`:

- **`stream`** — stdout/stderr. Read `text` (array of lines).
- **`execute_result`** — Jupyter auto-display of a bare expression on the last line.
  Read `data["text/plain"]`.
- **`display_data`** — rich output (plots, DataFrames). For matplotlib, the PNG is at
  `data["image/png"]` as base64; the user sees it rendered in Chrome.
- **`error`** — `ename`, `evalue`, `traceback`. Traceback lines contain ANSI color
  escapes (`[...m`); strip them for readable display, or just use `ename`+`evalue`.

**DataFrame quirk:** pandas auto-display returns BOTH `text/plain` (compact, few
lines) AND `text/html` (Colab's interactive table widget, ~6 KB of inline JS/CSS).
Read `text/plain` to inspect; the HTML bloats context fast. If you need to read tabular
output programmatically, prefer `print(df.head())` or `df.to_string()`.

## Working with existing Drive notebooks

The MCP entry tool always opens the scratch notebook (`/notebooks/empty.ipynb`), but
**the bridge follows in-tab navigation** (verified 2026-05-13). To work on an existing
notebook: connect, then in the Colab UI, **File → Open notebook → Drive tab** and pick
one. All subsequent MCP calls now operate on that notebook. Same trick works for
switching between notebooks mid-session.

**Saving / organizing notebooks is NOT in the MCP surface.** Use the Colab UI:
- File → Save (Cmd-S) saves the live state including all MCP-edited cells.
- File → Save a copy in Drive… to name and place it.
- Folder organization happens in Drive itself (`drive.google.com`).

When connected to a real Drive notebook, **don't modify without explicit user
instruction.** It's easy to forget you're not on scratch.

## Runtime expectations (Colab free tier, snapshot 2026-05-13)

- Python 3.12, Linux x86_64, **2 CPUs, no GPU**. 684 pre-installed packages.
- **Full data science stack ready, no install needed**: numpy, scipy, pandas,
  matplotlib, seaborn, plotly, scikit-learn, statsmodels, xgboost, lightgbm,
  tensorflow, torch (CPU build), jax, transformers, requests, beautifulsoup4,
  pyarrow, polars, duckdb, h5py.
- **Bio/genomics packages need `!pip install`** at top of notebook: biopython, pysam,
  pybedtools, scanpy, anndata, gtfparse, pyranges, scvi-tools.
- Cell magics (`!shell`, `%magic`) work — Colab is IPython under the hood.
- **GPU/TPU requires the user to change runtime type in the Colab UI**
  (Runtime → Change runtime type). The MCP cannot do this. After the change, the
  kernel restarts and all state is lost.

## Norms

- Plots and tables render in the user's Chrome tab natively — never push them to
  `agent_plots/`.
- Single connection per MCP process. If the user has a stale Colab tab open with an
  old `mcpProxyToken`, ask them to close it before reconnecting.
- The MCP can drive Python, R, or Julia cells. Most Colab work is Python; R/Julia
  runtimes work but the user may need to change runtime type.
- Server logs at `/var/folders/.../colab-mcp-logs-*/colab-mcp.*.log` are the
  first stop when the bridge misbehaves — look for `connection open` (success),
  `Connection rejected` (lock collision), or silence (browser side blocking).
