See [embedding helpers](embedding.md) and the [recipe index](../SKILL.md) for shared setup and related recipes.

### Recipe 4 — Toggle between individual and group autoscale

igv.js has no built-in UI button for this. Add one by mutating `track.autoscaleGroup` on all
wig tracks and calling `browser.updateViews()`.

```python
html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/igv@3.5.2/dist/igv.min.js"></script>
<style>
  body{{margin:0;padding:8px;font-family:sans-serif}}
  #igv{{width:100%}}
  #controls{{background:#f5f5f5;border:1px solid #ddd;border-radius:4px;
             padding:8px 12px;margin-bottom:8px;display:flex;align-items:center;gap:12px}}
  button{{font-size:13px;padding:5px 14px;cursor:pointer;
          border:1px solid #aaa;border-radius:3px;background:#fff}}
  button:hover{{background:#eee}}
  #mode{{font-size:12px;color:#555;font-style:italic}}
</style>
</head><body>
<div id="controls">
  <b>Autoscale:</b>
  <button id="togBtn">Switch to group scale</button>
  <span id="mode">currently: individual (each track scales independently)</span>
</div>
<div id="igv"></div>
<script>
var groupMode = false;
igv.createBrowser(document.getElementById("igv"), {{
  genome: "hg38", locus: "{CHR}:{START}-{END}",
  tracks: {json.dumps(track_cfgs)}
}}).then(function(b) {{
  document.getElementById("togBtn").addEventListener("click", function() {{
    groupMode = !groupMode;
    b.trackViews.forEach(function(tv) {{
      var t = tv.track;
      if (t.type === 'wig') {{
        t.autoscaleGroup = groupMode ? 'shared' : undefined;
        t.autoscale = true;
      }}
    }});
    b.updateViews();
    this.textContent = groupMode ? 'Switch to individual scale' : 'Switch to group scale';
    document.getElementById("mode").textContent = groupMode
      ? 'currently: group (all tracks share the same y-axis)'
      : 'currently: individual (each track scales independently)';
  }});
}});
</script>
</body></html>"""

embed_igv(html, height=400)
```

The toggle works by:
1. Setting `track.autoscaleGroup = 'shared'` on every wig track (group mode) or `undefined` (individual)
2. Calling `browser.updateViews()` to force a redraw
3. `b.trackViews` is the array of TrackView objects; `.track` is the underlying track

---
