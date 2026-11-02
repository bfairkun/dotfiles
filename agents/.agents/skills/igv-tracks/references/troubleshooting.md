See [embedding helpers](embedding.md) and the [recipe index](../SKILL.md) for shared setup and related recipes.

### Gotchas and API notes

| Issue | Fix |
|-------|-----|
| Blank tracks after dropdown navigation | Bedgraph data must be coordinate-sorted; use `_CHROM_KEY` sort |
| Dropdown `browser.search(str)` doesn't navigate | Use `browser.goto(chr, start, end)` instead — `search()` is unreliable with embedded data URIs in 3.5.2 |
| `type: "junction"` invisible | Use `type: "bed"` — junction arc rendering fails silently with data URI sources in 3.5.2 |
| **Whole browser shows zero tracks, no error, in the rendered .html** (works if you eval the cell interactively though) | Don't set `srcdoc` as a literal HTML attribute — Quarto/pandoc's ipynb→html conversion mis-parses `>` inside the quoted attribute and HTML-entity-escapes everything after it, so igv.js's own `<script>` tags become inert text. Use the current `embed_igv()` (builds the iframe via JS, `srcdoc` as a JS string) — see above |
| **Browser opens zoomed into the first item of a stepper list instead of the configured locus** | The function that populates the list called the one that navigates. Give it a `navigate === false` path used only on initial build (Recipe 8) |
| **Track names go stale / overlap after any programmatic navigation** | The labels in your own name column are absolutely positioned; `goto` re-lays out the viewports but not your column. Re-run the name builder ~400 ms after every `goto` |
| **Rendered .html: iframe never appears, console says `Invalid or unexpected token`** (the standalone page works) | A post-processor injected content into the `srcdoc` string. `render_notebook` adds its render-env block before the **last** `</body></html>` in the file — which is the copy inside your escaped payload — and that injection carries real newlines, so the JS string literal is unterminated. Escape `</body` and `</html` in the payload the same way as `</script`: `json.dumps(html).replace("</script","<\\/script").replace("</body","<\\/body").replace("</html","<\\/html")` |
| Group vs individual y-axis | Use Recipe 4 toggle button; `autoscaleGroup: "shared"` at init also works |
| ROI band not visible, no error | `roi` must be named sets with a `features` list (Recipe 5) — a flat list of region objects is silently ignored |
| **CSS aimed at igv's DOM does nothing** — no error, and the rule *is* in `document.styleSheets` | igv 3.x renders inside `attachShadow({mode:"open"})`; a document-level `<style>` cannot cross it. Inject into `element.getRootNode()` (Recipe 6). Tell-tale: `document.querySelector('.igv-…')` returns `null` |
| Only *some* of your styling applies | Inline styles set from JS cross the shadow boundary; stylesheet rules do not. A half-styled element is the signature of the shadow-DOM trap above |
| Track name covers the signal | Default igv.js behaviour. Give names their own column — Recipe 6, the default for every browser |
| Name box won't scroll, or names overlap | `height:auto` grows to fit its content, so it never scrolls *or* clips. Set an explicit pixel height (Recipe 6) |
| `axisWidth` seems to have no effect | Don't reuse `.igv-axis-column` for names — it also carries the wig y-axis numbers, so they compete for one strip. Use your own column (Recipe 6) |
| **Transcripts render uniformly thin** — no thick CDS / thin UTR | Feature-level `cdStart`/`cdEnd` is *not* enough for inline `features`. igv's BED12 decoder annotates **each exon**, and inline features bypass it. Annotate exons yourself (helper below) |

#### Thick/thin CDS on inline transcript features

Same root cause as the `itemRgb` gotcha: inline `features` skip igv's BED decoder, so anything
the decoder normally derives must be supplied by hand. For BED12 the decoder walks each exon
and marks it `utr: true` when it falls wholly outside the CDS, or stamps `cdStart`/`cdEnd`
onto the single exon each boundary lands inside. Without that, every transcript draws thin.

```python
def exons_with_cds(exon_list, cds_start, cds_end):
    """[(start,end),...] -> igv.js exon dicts carrying thick/thin (CDS/UTR) info."""
    out = []
    for a, b in exon_list:
        ex = {"start": int(a), "end": int(b)}
        if cds_start > b or cds_end < a:
            ex["utr"] = True
        else:
            if a <= cds_start <= b: ex["cdStart"] = int(cds_start)
            if a <= cds_end   <= b: ex["cdEnd"]   = int(cds_end)
        out.append(ex)
    return out

feature = {"chr": "chr16", "start": tx_start, "end": tx_end, "name": tx_id, "strand": "+",
           "color": "rgb(33,102,172)",           # per-feature colour; omit track-level `color`
           "cdStart": cds_start, "cdEnd": cds_end,   # still set these on the feature too
           "exons": exons_with_cds(exons, cds_start, cds_end)}
```

Verify in the rendered HTML by grepping for `utr` / `cdStart` — remembering that srcdoc
content is escaped, so the string to search for is `utr&quot;: true`, not `"utr": true`.
