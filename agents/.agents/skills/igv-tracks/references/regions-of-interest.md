See [embedding helpers](embedding.md) and the [recipe index](../SKILL.md) for shared setup and related recipes.

### Recipe 5 — Highlighting regions of interest (ROI)

To mark candidate regions with a shaded vertical band spanning all tracks (e.g. to call
out a candidate ASO window), use the browser-level `roi` config option.

**The `roi` value is an array of named ROI *sets*, each with its own `color` and a
`features` array of `{chr, start, end}` objects — it is NOT a flat array of
`{chr, start, end, color, name}` region objects.** Passing a flat array silently
produces no visible highlight (no error, no console warning) — this is the most likely
mistake to make here, since every other igv.js list-valued config option (`tracks`,
loci lists in Recipe 2) *is* a flat array of one-object-per-item, so ROI's nested
"named set containing a features list" shape breaks that pattern.

```python
roi_sets = [
    {
        "name": "Candidate 1",
        "color": "rgba(230,80,80,0.25)",  # translucent — this is the band's fill
        "features": [
            {"chr": "chr2", "start": 148_513_420, "end": 148_513_490},
        ],
    },
    {
        "name": "Candidate 2",
        "color": "rgba(80,140,230,0.25)",
        "features": [
            {"chr": "chr2", "start": 148_516_930, "end": 148_517_000},
        ],
    },
]

html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/igv@3.5.2/dist/igv.min.js"></script>
<style>body{{margin:0;padding:6px}} #igv{{width:100%}}</style>
</head><body><div id="igv"></div>
<script>
igv.createBrowser(document.getElementById("igv"), {{
  genome: "hg38", locus: "{CHR}:{START}-{END}",
  roi: {json.dumps(roi_sets)},
  tracks: {json.dumps(track_cfgs)}
}});
</script></body></html>"""

embed_igv(html, height=400)
```

A single ROI set can hold multiple non-contiguous `features` (e.g. several exons that
are all part of one logical region) — group by set when they should share one
name/color, not by individual feature.

Source: [igv.js wiki — Regions of Interest](https://github.com/igvteam/igv.js/wiki/Regions-of-Interest).
Before using any igv.js config option that hasn't already been recipe-tested in this
skill, check the wiki page for that feature rather than inferring the shape from
adjacent options — igv.js's config surface is not internally consistent about
flat-list vs. named-set shapes.

---
