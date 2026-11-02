## Rendering notebooks — use `render_notebook`, not `quarto` directly

`render_notebook` (in `~/bin/`) is a transparent shim over the `quarto` CLI. Use it exactly like quarto — just swap the command:

```bash
render_notebook render notebook.qmd
render_notebook render notebook.qmd --to pdf --output-dir out/
```

All args pass through to quarto untouched. After a successful HTML render it records the render environment into a `<!-- render-env:start -->` comment block **in the rendered `.html`**, and strips any stale copy from the `.qmd`. Captured fields include `node_type` (compute/login/local), Slurm `partition`/`mem_allocated`/`cpus_allocated`, and **`peak_rss`** — the *actual* measured peak memory of the render.

Caveats:
- Only renders that go *through* `render_notebook` are tagged — `quarto preview` and IDE render buttons are not.
- HTML output only. A `--to pdf` render prints a notice and writes no block.
- `peak_rss` is actual usage; `mem_allocated` is what Slurm granted. Use `peak_rss` to judge the minimum needed.

### Sizing resources when reopening an existing notebook

Before starting a kernel or re-rendering an existing `.qmd`, read the render-env block from its **last rendered HTML** to pick a sensible allocation:

```bash
grep -A14 "render-env:start" docs/<notebook>.html
```

Use `peak_rss` (plus headroom) to choose `start_agent_kernel --mem ...`, and `node_type` to know whether it previously needed a compute node at all. If there's no block, the notebook was never rendered through `render_notebook` — fall back to defaults and ask the user.

Note that `peak_rss` for a typical analysis notebook is a few hundred MB, i.e. far under the 8 GiB login-node cap on its own. The cap is hit by *accumulation* across concurrent sessions, so a small `peak_rss` is not evidence that login-node rendering is safe when other agents are running.
