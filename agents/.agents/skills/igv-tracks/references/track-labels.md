See [embedding helpers](embedding.md) and the [recipe index](../SKILL.md) for shared setup and related recipes.

### Recipe 6 — Track names beside the tracks, not on top of them (DEFAULT)

igv.js draws each track's name **inside the track viewport**, covering the signal. Put the
names in a column of your own to the left instead. Do this for every browser.

**The one thing to know first: igv.js 3.x renders the whole browser inside
`attachShadow({mode:"open"})`.** A `<style>` block in the document head **cannot cross that
boundary**, so *any* CSS aimed at igv's DOM — or at your own elements placed inside it — is
silently ignored. No error, no warning; the rules are present in `document.styleSheets` and
simply never match. Inline styles set from JS still work, which makes the failure confusing:
part of your styling applies and part doesn't. Inject a `<style>` into the shadow root via
`getRootNode()`.

For the same reason, don't try to reuse igv's `.igv-axis-column` for names — it also carries
the wig y-axis numbers, so the two compete for one strip. An element you create has no igv
rule pointing at it and nothing else drawn in it.

```python
NAME_W = 300   # width of the name column; yours to choose, nothing else lives there

cfg = {"genome": "hg38", "locus": locus, "tracks": track_cfgs,
       "showTrackLabels": False}     # turn off igv's overlaid label
```

```js
igv.createBrowser(el, cfg).then(function (b) {
  var cc = b.columnContainer;

  // 1. Styles must go INTO the shadow root. getRootNode() returns the ShadowRoot
  //    (or the document, if a future igv version stops using shadow DOM).
  var root = cc.getRootNode();
  if (!root.querySelector("style[data-trk-names]")) {
    var st = document.createElement("style");
    st.setAttribute("data-trk-names", "1");
    st.textContent = `
      .trk-name-col { position:relative; box-sizing:border-box;
          flex:0 0 300px; width:300px; min-width:300px;
          border-right:1px solid #d8d8d8; background:#fff; }
      .trk-name { position:absolute; left:6px; width:282px; box-sizing:border-box;
          font-family:-apple-system,Helvetica,Arial,sans-serif;
          font-weight:500; line-height:1.2; color:#1a1a1a;
          display:flex; align-items:center;
          overflow-y:auto; overflow-x:hidden;            /* scrollable box */
          scrollbar-width:thin; scrollbar-color:#c4c4c4 transparent; }
      .trk-name > span { white-space:normal; overflow-wrap:break-word;
          word-break:normal; hyphens:none; }             /* wrap at spaces/hyphens */
      .trk-name::-webkit-scrollbar { width:6px; }
      .trk-name::-webkit-scrollbar-thumb { background:#c4c4c4; border-radius:3px; }`;
    root.appendChild(st);
  }

  // 2. Our own column, first child of the flex row.
  var col = cc.querySelector(".trk-name-col");
  if (!col) {
    col = document.createElement("div");
    col.className = "trk-name-col";
    cc.insertBefore(col, cc.firstChild);
  }
  var ccTop = cc.getBoundingClientRect().top;

  // 3. One label per track, at the y-offset measured from that track's own
  //    element. Adding a column on the left changes x but not y.
  var FONT_MAX = 12, FONT_MIN = 9, FONT_STEP = 0.5;
  b.trackViews.forEach(function (tv) {
    var anchor = tv.axis || (tv.viewports[0] && tv.viewports[0].viewportElement);
    if (!anchor || !tv.track || !tv.track.name) return;
    var r = anchor.getBoundingClientRect();
    if (!r.height) return;

    var lab = document.createElement("div");
    lab.className = "trk-name";
    var span = document.createElement("span");
    span.textContent = tv.track.name;
    lab.appendChild(span);
    lab.title = tv.track.name;              // full name on hover when scrolled
    // An explicit pixel height is required: with height:auto the box grows to fit
    // its content, so it never scrolls and never clips — long names spill over the
    // tracks below. Fixed height + overflow-y:auto is what makes it a scroll box.
    lab.style.top    = (r.top - ccTop) + "px";
    lab.style.height = r.height + "px";
    col.appendChild(lab);

    // Shrink a little to avoid a scrollbar on near-misses; never to unreadable.
    var size = FONT_MAX;
    lab.style.fontSize = size + "px";
    while (size > FONT_MIN && span.offsetHeight > r.height) {
      size -= FONT_STEP;
      lab.style.fontSize = size + "px";
    }
  });
});
```

Three layers handle length, in order of preference: **wrap** (does most of the work) →
**shrink**, 12px down to a 9px floor → **scroll**. Keep names short
(`"Brain (adult) · F5-CAGE"`, not `"Brain (adult)  [FANTOM5 CAGE]"`), give wig tracks
`height ≥ 38`, and raise the iframe height to `n_tracks × height + ~150`.

**Verifying.** Styling bugs here are invisible from the source — the CSS looks right and does
nothing. Expose the browser as `window.__b = b` inside the `createBrowser` `.then()` — a probe can then read
`referenceFrameList[0]` for the true locus and call `goto` directly, which separates "navigation is
broken" from "the click handler is broken". **Poll for it** (`waitForFunction(() => window.__b)`)
rather than waiting a fixed number of seconds: tracks load sequentially, and an igv.js browser
embedded in a rendered notebook took ~21 s to reach full track count, so a fixed wait reports a
half-loaded browser as a failure.

Render headlessly and inspect the live DOM rather than reasoning about it: the
`playwright` CLI (conda-forge, CLI only — no Python bindings) can screenshot a `file://` URL,
and a `<style>`/`<script>` probe appended to the page can dump `getComputedStyle` results into
a visible `<div>` that shows up in the screenshot. Remember to query **through the shadow
root**; `document.querySelector` returns `null` for everything inside it, which is itself the
quickest confirmation that shadow DOM is in play. The shadow root is attached to **the container
div you passed to `createBrowser`**, so the probe target is `document.getElementById('igv').shadowRoot` —
and note that that div's `.children.length` and `.innerHTML.length` are **0 even when the browser
is rendering perfectly**, because shadow content is not in `children`. Counting
`shadowRoot.querySelectorAll('.igv-viewport')` is a reliable liveness check.

Genome loading over the network is flaky headlessly: several pages loaded back-to-back were
observed reporting a silent never-settling `createBrowser` promise, and the same configs all
resolved when re-run one at a time. **Retry before concluding a config is broken**, and
expect views zoomed in below roughly 300 bp to paint blank headlessly while the same view is
fine in a real browser — verify at >=1 kb.

---
