See [embedding helpers](embedding.md) and the [recipe index](../SKILL.md) for shared setup and related recipes.

### Recipe 3 — Adding BED annotation tracks

Any BED6 data can be added alongside wig tracks. Common uses: intervals of interest,
tabix-indexed annotation files filtered to the relevant regions.

```python
import pysam

def tabix_bed_uri(tabix_path, regions, pad=0, filter_fn=None):
    """
    Fetch BED records from a tabix-indexed file over multiple regions,
    optionally filter, deduplicate, and return a sorted data URI.
    filter_fn: callable(fields_list) → bool, or None to keep all records.
    """
    tbx = pysam.TabixFile(tabix_path)
    rows, seen = [], set()
    for chrom, s, e in regions:
        s_q, e_q = max(0, s - pad), e + pad
        try:
            for rec in tbx.fetch(chrom, s_q, e_q):
                if rec in seen: continue
                f = rec.split('\t')
                if filter_fn and not filter_fn(f): continue
                seen.add(rec)
                rows.append((f[0], int(f[1]), int(f[2]),
                             f[3] if len(f) > 3 else '.',
                             f[4] if len(f) > 4 else '0',
                             f[5] if len(f) > 5 else '.'))
        except Exception:
            pass
    tbx.close()
    return bed_uri(rows)

# Example: BED track from a tabix file, keeping only records with score > 5
bed_track = {
    'url': tabix_bed_uri('annotations.bed.gz', regions, pad=500,
                          filter_fn=lambda f: float(f[4]) > 5),
    'name': 'Annotations', 'format': 'bed', 'type': 'annotation',
    'height': 40, 'color': '#9B59B6', 'displayMode': 'EXPANDED',
}

# Or from a simple Python list:
my_intervals = [('chr1', 1000, 2000, 'featureA', 100, '+'),
                ('chr1', 3000, 4000, 'featureB', 200, '-')]
bed_track2 = {
    'url': bed_uri(my_intervals), 'name': 'My intervals',
    'format': 'bed', 'type': 'annotation', 'height': 40, 'displayMode': 'EXPANDED',
}
```

Use `'type': 'annotation'` — it is the documented value and `FeatureTrack.defaults.type`.

---
