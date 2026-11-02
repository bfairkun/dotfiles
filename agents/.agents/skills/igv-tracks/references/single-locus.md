See [embedding helpers](embedding.md) and the [recipe index](../SKILL.md) for shared setup and related recipes.

### Recipe 1 — Single locus, wig tracks only

```python
CHR, START, END = 'chr6', 106280000, 106325000

# tracks_spec: list of (bw_path, label, hex_color)
tracks_spec = [
    ('path/to/sample1.bw', 'Sample 1', '#888888'),
    ('path/to/sample2.bw', 'Sample 2', '#E2693F'),
]

track_cfgs = [
    {'url': bw_uri(bw, CHR, START, END), 'name': name, 'color': color,
     'format': 'bedgraph', 'type': 'wig', 'height': 60,
     'autoscale': True,
     # 'autoscaleGroup': 'shared',  # uncomment to lock y-axes together
     }
    for bw, name, color in tracks_spec
]

html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/igv@3.5.2/dist/igv.min.js"></script>
<style>body{{margin:0;padding:6px}} #igv{{width:100%}}</style>
</head><body><div id="igv"></div>
<script>
igv.createBrowser(document.getElementById("igv"), {{
  genome: "hg38", locus: "{CHR}:{START}-{END}",
  tracks: {json.dumps(track_cfgs)}
}});
</script></body></html>"""

embed_igv(html, height=380)
```

---
