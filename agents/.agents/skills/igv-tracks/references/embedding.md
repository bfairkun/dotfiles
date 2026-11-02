## Embedded igv.js browser in a Quarto notebook

For a **fully self-contained, interactive browser embedded in an HTML notebook**, use igv.js
with bigwig data converted to gzip+base64 bedgraph data URIs. No server needed; igv.js
loads from CDN (internet required for the reference genome sequence).

**Do NOT use `igv-reports`** for RNA-seq coverage — it is a variant-centric tool that does not
support bigwig tracks properly.

### Core helpers (always include these)

```python
import pyBigWig, json
from base64 import b64encode
from gzip import compress
from IPython.display import display, HTML

# Chromosome sort key — used whenever coordinate-sorting is required
_CHROM_KEY = {f'chr{i}': i for i in range(1, 23)}
_CHROM_KEY.update({'chrX': 23, 'chrY': 24, 'chrM': 25})

def bw_uri(bw_path, chrom, start, end):
    """Single-region bigwig → gzip bedgraph data URI."""
    bw = pyBigWig.open(bw_path)
    ivs = bw.intervals(chrom, start, end) or []
    bw.close()
    text = ''.join(f'{chrom}\t{s}\t{e}\t{v:.4f}\n' for s, e, v in ivs)
    return f'data:application/gzip;base64,{b64encode(compress(text.encode())).decode()}'

def bed_uri(rows):
    """BED6 rows → gzip data URI. rows = list of (chrom,start,end,name,score,strand)."""
    rows = sorted(rows, key=lambda x: (_CHROM_KEY.get(x[0], 99), x[1]))
    text = '\n'.join(f'{c}\t{s}\t{e}\t{n}\t{sc}\t{st}' for c,s,e,n,sc,st in rows)
    return f'data:application/gzip;base64,{b64encode(compress((text+"\n").encode())).decode()}'

def embed_igv(html, height=400, div_id='igv-embed-host'):
    """Embed an igv.js HTML page in a notebook iframe, built via JS at display time.

    Do NOT set srcdoc as a literal HTML attribute (e.g. `f'<iframe srcdoc="{escaped}">'`) —
    when this cell output is rendered through Quarto/pandoc (ipynb -> html), pandoc re-parses
    the raw HTML and mis-handles the embedded page's own `<script>`/`<style>` tags inside the
    attribute value: any `>` inside the quoted attribute prematurely ends pandoc's naive
    tag-parse, so everything after it gets HTML-entity-re-escaped (`<`/`>` -> `&lt;`/`&gt;`)
    even though the Python-side `&`/`"` escaping was correct. Net effect: the iframe renders
    with **zero tracks and no error** — igv.js never even parses, since its own `<script>`
    tags are now inert text. Building the iframe via JS (srcdoc set as a JS string, inside a
    `<script>` block) sidesteps this entirely, since `<script>` content is never HTML-tag-
    parsed by pandoc.
    """
    import json
    # Escape every closing tag a post-processor might search for: `</script` (pandoc /
    # the HTML parser) and `</body`/`</html` (render_notebook injects before the last
    # one it finds -- see the gotcha table).
    payload = (json.dumps(html).replace('</script', '<\\/script')
                               .replace('</body', '<\\/body')
                               .replace('</html', '<\\/html'))
    snippet = (f'<div id="{div_id}"></div>\n<script>\n(function(){{\n'
               f"  var f = document.createElement('iframe');\n"
               f"  f.style.cssText = 'width:100%;height:{height}px;border:1px solid #ccc;"
               f"border-radius:4px;';\n"
               f'  f.srcdoc = {payload};\n'
               f"  document.getElementById('{div_id}').appendChild(f);\n"
               f'}})();\n</script>')
    display(HTML(snippet))
```

**If you have multiple `embed_igv()` calls in one notebook**, pass a distinct `div_id` to
each (e.g. `div_id=f'igv-embed-{i}'`) — the default is a fixed string, and duplicate DOM ids
mean `getElementById` finds the wrong host on the second call.

---
