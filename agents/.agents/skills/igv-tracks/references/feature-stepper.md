See [embedding helpers](embedding.md) and the [recipe index](../SKILL.md) for shared setup and related recipes.

### Recipe 8 — Step through a list of features (prev/next + keyboard + readout)

Scrolling to find one of ~100 variants is unusable. Give the page a stepper: prev/next
buttons, keyboard shortcuts, a dropdown of every feature, an annotation readout, and a
selector for which subset to walk. Build the feature array in Python — one dict per feature
with `pos` and a pre-rendered `label` string, plus whatever booleans the subset filters need
— and hand it to the template as `__FEATURES__`.

```python
for r in feats:                      # label carries what you need to triage without clicking
    r["label"] = " \u00b7 ".join([f'{r["pos"]:,} {r["ref"]}>{r["alt"]}', r["gt"],
                                  r["zyg"], r["loc"], f'MAF {r["maf"]}'])
```

```js
var FEATURES = __FEATURES__;   // [{pos, label, usable, zyg, ...}, ...]
igv.createBrowser(el, {genome:"hg38", locus:LOCUS, showCenterGuide:true,
                       showTrackLabels:false}).then(function (b) {
  var fsel = document.getElementById("fsel"),   // dropdown of all features
      fset = document.getElementById("fset"),   // which subset to walk
      fwin = document.getElementById("fwin"),   // view width: 100 / 600 / 2000 bp
      finfo = document.getElementById("finfo"); // readout
  var subset = [], idx = -1;

  function rebuild(navigate) {
    var mode = fset.value;
    subset = FEATURES.filter(function (v) { return mode === "all" ? true : v[mode]; });
    fsel.innerHTML = "";
    subset.forEach(function (v, i) {
      var o = document.createElement("option");
      o.value = i; o.textContent = (i + 1) + "/" + subset.length + "  " + v.label;
      fsel.appendChild(o);
    });
    idx = subset.length ? 0 : -1;
    show(navigate);
  }

  // navigate === false updates the readout only. Building the list on load MUST NOT
  // navigate, or the browser opens zoomed into feature 1 instead of the overview locus.
  function show(navigate) {
    if (idx < 0) { finfo.textContent = "no features in this set"; return; }
    var v = subset[idx], w = parseInt(fwin.value);
    fsel.value = idx;
    finfo.textContent = (idx + 1) + " of " + subset.length + " \u2014 " + v.label;
    if (navigate === false) return;
    b.goto(CHROM, Math.max(0, v.pos - Math.round(w / 2)), v.pos + Math.round(w / 2));
    // name labels are absolutely positioned, so re-lay them out after every move
    setTimeout(function () { try { addNames(b); } catch (e) {} }, 400);
  }

  function stepBy(d) {
    if (!subset.length) return;
    idx = (idx + d + subset.length) % subset.length;      // wraps at both ends
    show(true);
  }
  document.getElementById("next").addEventListener("click", function(){ stepBy(1); });
  document.getElementById("prev").addEventListener("click", function(){ stepBy(-1); });
  fsel.addEventListener("change", function(){ idx = parseInt(this.value); show(true); });
  fset.addEventListener("change", function(){ rebuild(true); });
  fwin.addEventListener("change", function(){ show(true); });
  document.addEventListener("keydown", function (e) {
    // ignore keys while a select/input has focus, or they fight the dropdowns
    if (e.target && /^(INPUT|SELECT|TEXTAREA)$/.test(e.target.tagName)) return;
    if (e.key === "n" || e.key === "ArrowRight") { stepBy(1); e.preventDefault(); }
    if (e.key === "p" || e.key === "ArrowLeft")  { stepBy(-1); e.preventDefault(); }
  });
  rebuild(false);                                          // populate, do not navigate
});
```

Notes that make it usable rather than merely working:

- Default the subset selector to the **filtered** list (e.g. sites that pass QC), not to
  everything — that is the list someone actually wants to walk.
- `showCenterGuide: true` marks the stepped-to position without accumulating ROI sets.
- Offer a window-width selector; a single fixed zoom is always wrong for some feature.
- Put the annotation string in the readout *and* in the dropdown option text, so the list is
  searchable by eye.
