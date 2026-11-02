See [embedding helpers](embedding.md) and the [recipe index](../SKILL.md) for shared setup and related recipes.

### Recipe 7 — Load tracks defensively, and make failures visible

A browser that renders **zero tracks with no error** is the most common way an embedded
igv.js page fails, and the least diagnosable: one rejected track load aborts
`createBrowser`, and the page is then indistinguishable from a network problem. Create the
browser bare, add tracks one at a time, and print any failure into the page.

```js
function report(m){ var e=document.getElementById("err"); e.style.display="block";
                    e.textContent += m + "\n"; }
window.onerror = function(m){ report("JS error: " + m); };
if (typeof igv === "undefined") { report("igv.js did not load from the CDN"); }
else igv.createBrowser(document.getElementById("igv"),
                       {genome:"hg38", locus:LOCUS, showTrackLabels:false}).then(function(b){
  var chain = Promise.resolve();
  TRACKS.forEach(function(t){
    chain = chain.then(function(){
      return b.loadTrack(t).catch(function(e){
        report('track "' + t.name + '" failed: ' + (e && (e.message || e)));  // others still load
      });
    });
  });
  return chain.then(function(){
    try { if (typeof b.loadROI === "function") b.loadROI(ROI); }
    catch(e){ report("ROI failed: " + e.message); }
  });
}).catch(function(e){ report("createBrowser failed: " + (e && e.message) +
                             (e && e.stack ? "\n" + e.stack : "")); });
```

Pair it with a `<div id="err">` above the browser. Keep the error box in production pages,
not just while debugging — it is what turns "the browser is empty" into an actionable report.
