See [embedding helpers](embedding.md) and the [recipe index](../SKILL.md) for shared setup and related recipes.

### Recipe 2 — Multi-locus with jump-to dropdown

Embed data for **many regions** in one bedgraph per track; add a dropdown to navigate.

**Critical**: bedgraph must be **coordinate-sorted** or igv.js shows blank tracks when
navigating away from the initial locus.

```python
def multi_bw_uri(bw_path, regions, pad=0):
    """
    regions: list of (chrom, start, end) tuples.
    Extracts data for each region ± pad, sorts globally, returns data URI.
    """
    bw = pyBigWig.open(bw_path)
    rows = []
    for chrom, s, e in regions:
        s, e = max(0, s - pad), e + pad
        try:
            for iv_s, iv_e, val in (bw.intervals(chrom, s, e) or []):
                if val and val == val:
                    rows.append((chrom, iv_s, iv_e, val))
        except Exception:
            pass
    bw.close()
    rows.sort(key=lambda x: (_CHROM_KEY.get(x[0], 99), x[1]))
    text = '\n'.join(f'{c}\t{s}\t{e}\t{v:.4f}' for c, s, e, v in rows)
    return f'data:application/gzip;base64,{b64encode(compress(text.encode())).decode()}'

# Build loci list — one entry per item in the dropdown
PAD = 2000
regions   = [(chrom1, start1, end1), (chrom2, start2, end2), ...]  # your regions
loci_names = ['Gene A', 'Gene B', ...]                               # dropdown labels

igv_loci = [
    {'name': name, 'locus': f'{c}:{max(0,s-PAD)}-{e+PAD}'}
    for name, (c, s, e) in zip(loci_names, regions)
]

track_cfgs = [
    {'url': multi_bw_uri(bw, regions, PAD), 'name': name, 'color': color,
     'format': 'bedgraph', 'type': 'wig', 'height': 60, 'autoscale': True}
    for bw, name, color in tracks_spec
]

html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/igv@3.5.2/dist/igv.min.js"></script>
<style>body{{margin:0;padding:8px;font-family:sans-serif}} #igv{{width:100%}}
select{{font-size:13px;padding:3px 8px;margin-left:6px}}</style>
</head><body>
<div style="margin-bottom:8px">
  <b>Jump to:</b>
  <select id="sel">
    {''.join(f'<option value="{i}">{l["name"]}</option>' for i,l in enumerate(igv_loci))}
  </select>
</div>
<div id="igv"></div>
<script>
var loci = {json.dumps(igv_loci)};
igv.createBrowser(document.getElementById("igv"), {{
  genome: "hg38", locus: loci[0].locus,
  tracks: {json.dumps(track_cfgs)}
}}).then(function(b) {{
  document.getElementById("sel").addEventListener("change", function() {{
    var l = loci[parseInt(this.value)];
    var parts = l.locus.split(':');
    var se = parts[1].split('-');
    b.goto(parts[0], parseInt(se[0]), parseInt(se[1]));
  }});
}});
</script>
</body></html>"""

embed_igv(html, height=450)
```

---
