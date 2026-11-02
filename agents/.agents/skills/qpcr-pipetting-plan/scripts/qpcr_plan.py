#!/usr/bin/env python3
"""qPCR pipetting-plan generator (Benjamin Fair's split-then-distribute recipe).

Pairs with the `qpcr-pipetting-plan` skill. Given an experiment spec (JSON), computes:
  - per-reaction and per-source-well volumes
  - one "primer+MM" mastermix per (primer pair x 2x-mastermix) block, with dead volume
  - working template volumes for each biological sample
  - a serial dilution series (standard curve) recipe from a separate cDNA source
  - NTC (water) volumes
  - source-plate map (rows = blocks, columns = templates) and qPCR-well count
and validates the lab's multichannel range (default 5-50 uL) on every dispense.

Recipe model (do not change without asking the user):
  * Final qPCR reaction is `rxn_ul` (default 10 uL); run in `reps` technical replicates.
  * Reactions are built at `reps*10 + split_dead_ul` uL per SOURCE well, then split reps x 10 uL
    into the qPCR plate. The split_dead_ul is per-well headroom for the multichannel split.
  * Per reaction: `mm_ul_per10` of 2x mastermix (-> 1x); primer from a pre-mixed pair stock;
    the REMAINDER is diluted cDNA template. Dilution water rides WITH the template (the
    primer+MM mastermix is mastermix + primers only). This keeps template >= 5 uL so it can
    be added by multichannel, and avoids tiny error-prone template volumes.
  * Every REAGENT you make (each mastermix, each diluted template, each dilution point) gets
    an extra `reagent_dead_frac` (default 10%) on top of the already-headroomed well volume.
  * Dilution factors are TUBE (working-stock) dilutions; the plan also reports the resulting
    final in-reaction dilution for QC.

Usage:
    python qpcr_plan.py <spec.json>          # print full plan
    python qpcr_plan.py <spec.json> --plot out.pdf   # also write a plate-map figure
    python qpcr_plan.py --example            # print the built-in worked example spec
"""
import json, math, sys, argparse

EXAMPLE = {
    "title": "MYT1L cryptic-splicing primer test",
    "reps": 3, "rxn_ul": 10.0, "split_dead_ul": 5.0, "reagent_dead_frac": 0.10,
    "mm_ul_per10": 5.0, "primer_stock_uM": 10.0, "primer_final_nM": 250.0,
    "multichannel_min_ul": 5.0, "multichannel_max_ul": 50.0, "pipette_increment_ul": 0.5,
    "n_samples": 6,
    "dilution": {"points": 4, "fold": 10, "top_tube_dilution_x": 20},
    "blocks": [
        {"name": "PP1 Canonical", "mastermix": "MM_A commercial", "samples": True,  "dilseries": True},
        {"name": "PP2 CS1",       "mastermix": "MM_A commercial", "samples": True,  "dilseries": True},
        {"name": "PP3 CS2",       "mastermix": "MM_A commercial", "samples": True,  "dilseries": True},
        {"name": "PP4 CS3",       "mastermix": "MM_A commercial", "samples": True,  "dilseries": True},
        {"name": "PP5 reference", "mastermix": "MM_A commercial", "samples": True,  "dilseries": False},
        {"name": "PP1 Canonical", "mastermix": "MM_B homemade",   "samples": False, "dilseries": True}
    ]
}


def compute(spec):
    reps  = spec["reps"]; rxn = spec["rxn_ul"]; dead = spec["reagent_dead_frac"]
    well  = reps * 10 + spec["split_dead_ul"]
    scale = well / rxn
    mm10  = spec["mm_ul_per10"]
    prim10 = rxn * (spec["primer_final_nM"] / 1000.0) / spec["primer_stock_uM"]
    temp10 = rxn - mm10 - prim10
    if temp10 <= 0:
        raise ValueError("template volume <= 0; check mm/primer settings")
    per = dict(mm=mm10, primer=prim10, temp=temp10)
    perwell = {k: v * scale for k, v in per.items()}
    perwell["mmmix"] = perwell["mm"] + perwell["primer"]
    # Round the two per-well MULTICHANNEL dispenses (primer+MM mix, template) to the pipette's
    # smallest increment; keep the mm:primer split so the pre-made mix batch stays consistent.
    incr = spec.get("pipette_increment_ul", 0) or 0
    if incr:
        snap = lambda v: math.floor(v / incr + 0.5) * incr
        ratio = perwell["mm"] / perwell["mmmix"] if perwell["mmmix"] else 0
        perwell["mmmix"] = snap(perwell["mmmix"]); perwell["temp"] = snap(perwell["temp"])
        perwell["mm"] = perwell["mmmix"] * ratio
        perwell["primer"] = perwell["mmmix"] * (1 - ratio)
        well = perwell["mmmix"] + perwell["temp"]

    nS = spec["n_samples"]; dil = spec["dilution"]; nD = dil["points"]
    blocks = spec["blocks"]
    def nwells(b): return nS * b["samples"] + nD * b["dilseries"] + 1  # +1 NTC/block
    total_src = sum(nwells(b) for b in blocks)

    # mastermix totals grouped by mastermix reagent
    mm_reagent = {}
    block_rows = []
    for b in blocks:
        n = nwells(b)
        tot  = n * perwell["mmmix"] * (1 + dead)
        mmv  = n * perwell["mm"]    * (1 + dead)
        pv   = n * perwell["primer"] * (1 + dead)
        mm_reagent[b["mastermix"]] = mm_reagent.get(b["mastermix"], 0) + mmv
        block_rows.append(dict(name=b["name"], mm=b["mastermix"], n=n,
                               total=tot, mmv=mmv, primer=pv,
                               samples=b["samples"], dilseries=b["dilseries"]))

    # templates
    samp_nwells = sum(1 for b in blocks if b["samples"])
    samp_vol = samp_nwells * perwell["temp"] * (1 + dead)
    dil_nwells = sum(1 for b in blocks if b["dilseries"])
    dil_wells_vol = dil_nwells * perwell["temp"] * (1 + dead)

    # serial dilution volumes: transfer T, water T*(fold-1), point = T*fold
    fold = dil["fold"]
    T = math.ceil(dil_wells_vol / (fold - 1))           # uL carried to next point
    point_vol = T * fold
    top_x = dil["top_tube_dilution_x"]
    d1_cdna = point_vol / top_x
    final_dil_factor = temp10 / rxn                      # template fraction of reaction
    tube_to_final = lambda x: x / final_dil_factor

    # multichannel checks
    warns = []
    for label, v in [("template/well", perwell["temp"]), ("primer+MM/well", perwell["mmmix"]),
                     ("split aliquot", 10.0)]:
        if v < spec["multichannel_min_ul"]:
            warns.append(f"{label} = {v:.2f} uL < multichannel min {spec['multichannel_min_ul']}")
        if v > spec["multichannel_max_ul"]:
            warns.append(f"{label} = {v:.2f} uL > multichannel max {spec['multichannel_max_ul']}")

    return dict(reps=reps, well=well, scale=scale, per=per, perwell=perwell, incr=incr,
                nS=nS, nD=nD, total_src=total_src, block_rows=block_rows,
                mm_reagent=mm_reagent, samp_nwells=samp_nwells, samp_vol=samp_vol,
                dil_nwells=dil_nwells, dil_wells_vol=dil_wells_vol, fold=fold, T=T,
                point_vol=point_vol, top_x=top_x, d1_cdna=d1_cdna,
                tube_to_final=tube_to_final, warns=warns, dil=dil)


def custom_mm_recipe(mm):
    """Compute a homemade mastermix recipe. mm has:
      mastermix_fold (default 2), batch_ul, components[{name,stock,final,unit}].
    A component's concentration in the mix = fold x final; volume = batch * (fold*final/stock)
    (stock and final must share the same unit). Returns (rows, water_ul, batch_ul)."""
    fold = mm.get("mastermix_fold", 2); batch = mm["batch_ul"]
    rows, used = [], 0.0
    for c in mm["components"]:
        in_mix = fold * c["final"]
        ul = batch * in_mix / c["stock"]
        used += ul
        rows.append({"component": c["name"], "stock": f"{c['stock']:g} {c['unit']}",
                     "final (1x)": f"{c['final']:g} {c['unit']}",
                     f"in {fold:g}x mix": f"{in_mix:g} {c['unit']}", "uL": round(ul, 2)})
    return rows, round(batch - used, 2), batch


def render(spec, r):
    L = []
    p = L.append
    p(f"# qPCR plan: {spec.get('title','(untitled)')}")
    p(f"{r['reps']} technical replicates -> {r['well']:.1f} uL/source well "
      f"({r['reps']*10:.0f} used + {r['well']-r['reps']*10:.1f} headroom); reagent dead +{spec['reagent_dead_frac']*100:.0f}%")
    p("")
    p("## Per-reaction recipe (final, per 10 uL)")
    p(f"  2x mastermix            : {r['per']['mm']:g} uL")
    plabel = spec.get("primer_stock_label", f"{spec['primer_stock_uM']} uM")
    p(f"  primer/assay ({plabel}) : {r['per']['primer']:g} uL  -> {spec['primer_final_nM']:.0f} nM each")
    p(f"  diluted template        : {r['per']['temp']:g} uL")
    incrnote = f"  (rounded to {r['incr']:g} uL)" if r.get('incr') else ""
    p(f"\n## Per source well = {r['well']:.1f} uL -- two multichannel dispenses{incrnote}")
    p(f"  primer+MM mix   : {r['perwell']['mmmix']:.2f} uL/well")
    p(f"  template/water  : {r['perwell']['temp']:.2f} uL/well")
    names = spec.get("sample_names")
    if names and len(names) == r["nS"]:
        p("  samples: " + ", ".join(f"S{i+1}={n}" for i, n in enumerate(names)))
    p("")
    p(f"## Reactions: {r['total_src']} source wells  ->  x{r['reps']} = {r['total_src']*r['reps']} qPCR wells")
    p("")
    p("## Step 1 - primer+MM mastermixes (one per block, incl dead volume)")
    p(f"{'block':22}{'mastermix':18}{'wells':>6}{'total':>9}{'2xMM':>9}{'primers':>9}")
    for b in r["block_rows"]:
        p(f"{b['name']:22}{b['mm']:18}{b['n']:>6}{b['total']:>9.1f}{b['mmv']:>9.1f}{b['primer']:>9.1f}")
    p("  2x mastermix stock needed: " + ", ".join(f"{k} {v:.0f} uL" for k, v in r["mm_reagent"].items()))
    for name, mm in spec.get("custom_mastermixes", {}).items():
        rows, water, batch = custom_mm_recipe(mm)
        p(f"\n### Homemade mastermix: {name} (make {batch:.0f} uL)")
        for row in rows:
            p(f"  {row['component']:16} {row['stock']:>12} -> {row['final (1x)']:>12} : {row['uL']:>6} uL")
        p(f"  {'water':16} {'':>12}    {'':>12} : {water:>6} uL")
    p("")
    p("## Step 2 - templates (incl dead volume)")
    p(f"- {r['nS']} biological samples: each used in {r['samp_nwells']} wells -> make >= {r['samp_vol']:.1f} uL each")
    p(f"- Std curve: {r['nD']}-point {r['fold']}-fold from separate cDNA; each point in {r['dil_nwells']} wells")
    p(f"    make {r['point_vol']:.0f} uL/point: D1 = {r['d1_cdna']:.1f} uL cDNA + {r['point_vol']-r['d1_cdna']:.1f} uL water "
      f"(tube {r['top_x']}x; final in-rxn ~{r['tube_to_final'](r['top_x']):.0f}x)")
    for i in range(2, r['nD'] + 1):
        tube = r['top_x'] * (r['fold'] ** (i - 1))
        p(f"    D{i} = {r['T']:.0f} uL D{i-1} + {r['point_vol']-r['T']:.0f} uL water "
          f"(tube {tube:.0f}x; final ~{r['tube_to_final'](tube):.0f}x)")
    p(f"- NTC: nuclease-free water at {r['perwell']['temp']:.2f} uL/well, one per block")
    p("")
    p("## Step 3 - split")
    p(f"Multichannel {r['reps']} x 10 uL from each source well into the qPCR plate.")
    if r["warns"]:
        p("")
        p("## !! multichannel range warnings")
        for w in r["warns"]:
            p("  - " + w)
    p("")
    p(textmap(spec, r))
    return "\n".join(L)


def textmap(spec, r):
    nS, nD = r["nS"], r["nD"]
    cols = [f"S{i}" for i in range(1, nS + 1)] + [f"D{i}" for i in range(1, nD + 1)] + ["NTC"]
    lines = ["## Source-plate map (rows = block, columns = template)"]
    lines.append("  " + "".join(f"{c:>5}" for c in cols))
    for b in spec["blocks"]:
        cells = []
        for c in cols:
            used = (c.startswith("S") and b["samples"]) or (c.startswith("D") and b["dilseries"]) or c == "NTC"
            cells.append("  X " if used else "  . ")
        lines.append(f"{b['name']:22} " + "".join(f"{x:>5}" for x in cells))
    return "\n".join(lines)


def plate_figure(spec, r, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    nS, nD = r["nS"], r["nD"]
    cols = [f"S{i}" for i in range(1, nS + 1)] + [f"D{i}" for i in range(1, nD + 1)] + ["NTC"]
    blocks = spec["blocks"]
    fig, ax = plt.subplots(figsize=(0.7 * len(cols) + 5, 0.55 * len(blocks) + 1.5))
    palette = ['#1b9e77', '#d95f02', '#7570b3', '#e7298a', '#66a61e', '#1f78b4', '#a6761d']
    for ri, b in enumerate(blocks):
        y = len(blocks) - 1 - ri
        pc = palette[ri % len(palette)]
        for ci, c in enumerate(cols):
            used = (c.startswith("S") and b["samples"]) or (c.startswith("D") and b["dilseries"]) or c == "NTC"
            ax.add_patch(Rectangle((ci, y), 0.92, 0.92, facecolor=pc if used else 'white',
                         alpha=0.35 if used else 0, edgecolor='0.6', lw=0.8, ls='-' if used else ':'))
            if used:
                ax.text(ci + 0.46, y + 0.46, c, ha='center', va='center', fontsize=7)
        ax.text(-0.15, y + 0.46, f"{b['name']} / {b['mastermix']}", ha='right', va='center', fontsize=8, weight='bold')
    for ci, c in enumerate(cols):
        ax.text(ci + 0.46, len(blocks) + 0.15, c, ha='center', va='center', fontsize=7, color='0.3')
    ax.set_xlim(-6, len(cols) + 0.2); ax.set_ylim(-0.3, len(blocks) + 0.6)
    ax.set_aspect('equal'); ax.axis('off')
    ax.set_title(f"{spec.get('title','qPCR')} - source plate ({r['total_src']} wells @ {r['well']:.0f} uL, x{r['reps']} split)", fontsize=9.5)
    names = spec.get("sample_names")
    if names and len(names) == r["nS"]:
        legend = "   ".join(f"S{i+1}={n}" for i, n in enumerate(names))
        fig.text(0.5, -0.02, legend, ha='center', va='top', fontsize=7, color='0.3')
    fig.savefig(out, bbox_inches='tight'); plt.close(fig)


ROWS96 = "ABCDEFGH"

def physical_layout(spec, r, ncols=12, nrows=8, gap_cols=1):
    """Assign each reaction to a physical well of an nrows x ncols plate.
    Layout (multichannel-friendly): samples fill rows (one block per column), then a
    column per dilution-series block (rows = dilution points). Each NTC sits at the row
    just below the dilution points (row index nD) of its own dilution column, so it reads
    as the "last / zero point" of that series; a block with no dilution series gets its
    NTC in an extra ("orphan") column on the same NTC row.
    Requires n_samples<=nrows, n_dil+1<=nrows, and total columns<=ncols.
    Returns (assign dict {(row,col): (block, template_label)}, warnings list)."""
    blocks = spec["blocks"]; nS, nD = r["nS"], r["nD"]
    warns = []
    if nS > nrows: warns.append(f"n_samples {nS} > {nrows} rows: sample-per-row layout won't fit")
    if nD + 1 > nrows: warns.append(f"n_dil+NTC {nD+1} > {nrows} rows")
    samp_blocks = [b for b in blocks if b["samples"]]
    dil_blocks  = [b for b in blocks if b["dilseries"]]
    assign, col = {}, 0
    for b in samp_blocks:
        for si in range(nS): assign[(si, col)] = (b, f"S{si+1}")
        col += 1
    col += gap_cols   # empty spacer column(s) separating samples from the dilution series
    dil_col = {}
    for b in dil_blocks:
        dil_col[id(b)] = col
        for di in range(nD): assign[(di, col)] = (b, f"D{di+1}")
        col += 1
    ntc_row, orphan = nD, col
    for b in blocks:
        if id(b) in dil_col:
            assign[(ntc_row, dil_col[id(b)])] = (b, "NTC")   # bottom of its dilution column
        else:
            assign[(ntc_row, orphan)] = (b, "NTC"); orphan += 1
    need_cols = max((c for (_, c) in assign), default=-1) + 1
    if need_cols > ncols: warns.append(f"needs {need_cols} columns > {ncols}: extend or use another plate")
    return assign, warns


def physical_figure(spec, r, out, ncols=12, nrows=8):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    assign, warns = physical_layout(spec, r, ncols, nrows)
    mms = list(dict.fromkeys(b["mastermix"] for b in spec["blocks"]))
    palette = ['#8dd3c7', '#fdb462', '#bebada', '#fb8072', '#b3de69', '#80b1d3']
    mmcolor = {m: palette[i % len(palette)] for i, m in enumerate(mms)}
    short = {}
    for b in spec["blocks"]:
        base = b["name"].split()[0]
        tag = base + ("*" if sum(1 for x in spec["blocks"] if x["name"].split()[0] == base) > 1
                      and b["mastermix"] == spec["blocks"][-1]["mastermix"] else "")
        short[id(b)] = base
    fig, ax = plt.subplots(figsize=(1.05 * ncols + 1, 0.72 * nrows + 1.6))
    for c in range(ncols):
        ax.text(c + 0.5, nrows + 0.35, str(c + 1), ha='center', va='center', fontsize=8, color='0.4')
    for rw in range(nrows):
        ax.text(-0.35, nrows - 1 - rw + 0.5, ROWS96[rw], ha='center', va='center', fontsize=8, color='0.4')
    for (rw, c), (b, tmpl) in assign.items():
        y = nrows - 1 - rw
        ax.add_patch(Rectangle((c, y), 0.92, 0.92, facecolor=mmcolor[b["mastermix"]],
                     edgecolor='0.5', lw=0.6))
        lab = f"{short[id(b)]}\n{tmpl}"
        ax.text(c + 0.46, y + 0.46, lab, ha='center', va='center', fontsize=6.2)
    # empty wells
    for c in range(ncols):
        for rw in range(nrows):
            if (rw, c) not in assign:
                y = nrows - 1 - rw
                ax.add_patch(Rectangle((c, y), 0.92, 0.92, facecolor='white', edgecolor='0.85', lw=0.5))
    handles = [Rectangle((0, 0), 1, 1, facecolor=mmcolor[m], edgecolor='0.5') for m in mms]
    ax.legend(handles, mms, loc='upper center', bbox_to_anchor=(0.5, -0.02),
              ncol=len(mms), fontsize=7, frameon=False)
    ax.set_xlim(-0.8, ncols + 0.1); ax.set_ylim(-0.3, nrows + 0.7)
    ax.set_aspect('equal'); ax.axis('off')
    ax.set_title(f"{spec.get('title','qPCR')} - physical {nrows}x{ncols} SOURCE plate "
                 f"({r['total_src']} wells @ {r['well']:.0f} uL)", fontsize=9.5)
    fig.savefig(out, bbox_inches='tight'); plt.close(fig)
    return warns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec", nargs="?")
    ap.add_argument("--plot", help="write the logical block x template plate map")
    ap.add_argument("--physical", help="write the physical A1-H12 (8x12) source-plate map")
    ap.add_argument("--example", action="store_true")
    a = ap.parse_args()
    if a.example:
        print(json.dumps(EXAMPLE, indent=2)); return
    spec = json.load(open(a.spec)) if a.spec else EXAMPLE
    r = compute(spec)
    print(render(spec, r))
    if a.plot:
        plate_figure(spec, r, a.plot)
        print(f"\n[wrote logical plate map -> {a.plot}]")
    if a.physical:
        assign, _ = physical_layout(spec, r)
        print("\n## Physical source-plate wells (well: block / mastermix / template)")
        for (rw, c) in sorted(assign):
            b, tmpl = assign[(rw, c)]
            print(f"  {ROWS96[rw]}{c+1:<2}: {b['name']:16} / {b['mastermix']:16} / {tmpl}")
        warns = physical_figure(spec, r, a.physical)
        for w in warns:
            print("  !! " + w)
        print(f"[wrote physical plate map -> {a.physical}]")


if __name__ == "__main__":
    main()
