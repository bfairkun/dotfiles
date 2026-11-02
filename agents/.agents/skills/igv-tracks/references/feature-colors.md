See [embedding helpers](embedding.md) and the [recipe index](../SKILL.md) for shared setup and related recipes.

### Recipe 3b — Per-feature colour (shading by a quantitative value)

**Do not shade via the BED `itemRgb` column.** A well-formed BED9 served as a gzip data URI
was observed rendering every feature in igv.js's default blue (`rgb(0,0,150)`), i.e. the
itemRgb never reached the feature. Pass an **inline `features` array** instead — no URL, no
parsing step:

```python
def feats(rows):
    """BED9-style tuples → igv.js feature objects with an explicit per-feature colour."""
    return [{'chr': r[0], 'start': int(r[1]), 'end': int(r[2]), 'name': r[3],
             'score': int(r[4]), 'strand': r[5], 'color': f'rgb({r[8]})'} for r in rows]

track = {'name': 'Sites', 'type': 'annotation', 'features': feats(rows),
         'height': 56, 'displayMode': 'EXPANDED'}   # NOTE: no 'color' key
```

`FeatureTrack.getColorForFeature` resolves in this order:

```
altColor (if strand '-')  →  this.color  →  this.colorBy  →  feature.color  →  defaultColor
```

So **a track-level `color` silently overrides every per-feature colour** — omit it entirely
on shaded tracks. `TrackBase` leaves `this.color` undefined unless config supplies it, and
`StaticFeatureSource` preserves extra properties on the objects, so `feature.color` is reached.

Put the number in `score` as well as in `name`; igv.js shows both in the click popup, so one
click gives the reader the value behind the shade.

**Colour ramps.** Blending toward white washes out mid-range features. Use a real sequential
colormap with the light end floored away from white, and floor the *data* too when values
below some point are not being considered:

```python
import matplotlib.cm as cm

def cmap_rgb(cmap, frac, lo=0.18, hi=0.95):
    """Sequential colour, floored away from white so low values stay visible."""
    frac = 0.0 if (frac is None or np.isnan(frac)) else max(0.0, min(1.0, frac))
    r, g, b, _ = cmap(lo + (hi - lo) * frac)
    return f'{int(r*255)},{int(g*255)},{int(b*255)}'

# Floor the scale where the data stops mattering: everything <= FLOOR gets the lightest tint
FLOOR = 50
frac = 0.0 if score <= FLOOR else (score - FLOOR) / (100 - FLOOR)
rgb = cmap_rgb(cm.Purples, frac, lo=0.05)   # lo=0.05 => near-white floor
```

Reserve a distinct flat colour (e.g. `170,170,170`) for *missing* data, so "measured zero"
and "not measured" never read the same. A colour ramp is meaningless without a key — emit a
CSS-gradient legend above the browser:

```python
def gradbar(cmap, label, ticks, lo=0.18, w=190):
    stops = ', '.join(f'rgb({cmap_rgb(cmap, i/10, lo=lo)}) {i*10}%' for i in range(11))
    tk = ''.join(f'<span>{t}</span>' for t in ticks)
    return (f'<div style="display:inline-block;margin-right:26px;vertical-align:top">'
            f'<div style="font-size:10px;color:#444;margin-bottom:2px">{label}</div>'
            f'<div style="width:{w}px;height:11px;border:1px solid #bbb;'
            f'background:linear-gradient(to right, {stops})"></div>'
            f'<div style="width:{w}px;display:flex;justify-content:space-between;'
            f'font-size:9px;color:#777">{tk}</div></div>')
```

---
