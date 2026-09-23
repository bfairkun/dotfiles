---
name: qpcr-pipetting-plan
description: >
  Design a qPCR run and generate bench-ready pipetting instructions using Ben's
  split-then-distribute recipe: build one oversized reaction per source well, then
  multichannel-split into technical replicates. Invoke when planning a qPCR, laying out
  a plate, calculating mastermix / primer / template volumes, building a dilution-series
  standard curve, adding NTCs, or turning a set of samples + primer pairs into a
  pipetting sheet. This is the SETUP/wet-lab-planning counterpart to the qpcr-analysis
  skill (which handles the QuantStudio data afterward).
---

# qPCR pipetting plan

Generates the pipetting instructions for a qPCR run. The deterministic volume math lives in
`scripts/qpcr_plan.py`; this file documents the recipe, the rules, and how to drive the script.

## The recipe model (Ben's standard workflow — do not change silently)

1. Final reaction is **10 µL/well**, run in **3 or 4 technical replicates**.
2. Build each reaction oversized in a **96-well source plate** at `reps*10 + 5` µL
   (**35 µL** for 3×, **45 µL** for 4×). The extra 5 µL is per-well headroom for the split.
3. Per 10 µL reaction: **5 µL 2× mastermix** (→1×); **primer** from a 10 µM pre-mixed pair
   stock (default target **250 nM each** → 0.25 µL); the **remainder is diluted cDNA template**.
4. **Two-tier assembly**: make one **primer+MM mastermix** (mastermix + primers only) per
   *(primer pair × 2×-mastermix)* block, distribute it across that block's wells, **then add
   template**. Dilution **water rides with the template**, not the mastermix — this keeps the
   template volume ≥ 5 µL (multichannel-addable) and avoids tiny, error-prone template volumes.
5. **Split** each source well `reps × 10 µL` into the qPCR plate (usually 96 source → 384 qPCR).

## Rules

- **Multichannel range 5–50 µL.** Every single dispense (template/well, primer+MM/well, each
  10 µL split) must fall in range. The script flags violations; the ≥5 µL template floor is why
  water rides with the template rather than a smaller fixed template + water-in-mastermix.
- **Multichannel increment.** The pipette only does whole `pipette_increment_ul` steps
  (default **0.5 µL**), so the two per-well dispenses (primer+MM mix, template) are rounded to
  that increment — the source-well total floats slightly (e.g. 35 → 35.5 µL) and reagent totals
  follow. Set `pipette_increment_ul` per the lab's pipette.
- **Two headroom stages, both applied:** the per-well 5 µL split dead volume (already in the
  35/45 µL well), **and** an extra **+5–10 %** (default 10 %) on every *reagent you make* — each
  mastermix, each diluted sample, each dilution point. Never make the exact stoichiometric amount.
- **NTC:** one no-template (water) control per *block* (per primer × mastermix combo), using that
  block's primer+MM mastermix with water in place of template.
- **Dilution series / standard curve:** N-point (default 4), 10-fold, from a **separate cDNA
  source**. Specify the top point as a **tube (working-stock) dilution**; the plan reports the
  resulting **final in-reaction dilution** too. Make each point large enough for its wells + the
  carry-over volume to seed the next point + dead volume.
- **Template dilution:** dilute RT/cDNA so the final in-reaction dilution lands in the target
  range (commonly **20–100×**, more dilute for abundant targets). Because template is ~47 % of the
  reaction, the tube dilution ≈ final × 0.47.

## Common variations the spec supports

- A primer pair that **skips the dilution series** (e.g. a reference/housekeeping assay with known
  efficiency): set `"dilseries": false`.
- **Multiple standard curves for one primer pair under different mastermixes** (e.g. commercial vs
  homemade 2× SYBR side-by-side): add a second block with the same primer name, a different
  `mastermix`, `"samples": false`, `"dilseries": true`. Each distinct `mastermix` string is totaled
  as its own 2× stock.

## How to use

1. Confirm with the user (only what you can't infer): reps (3/4), primer final concentration,
   samples, which pairs need a dilution series, the dilution-series top point, and any
   mastermix-comparison blocks.
2. Write a spec JSON (see `assets/example_spec.json`; `qpcr_plan.py --example` prints it).
3. Run it:

   ```bash
   conda run -n py_general python scripts/qpcr_plan.py spec.json --plot logical_map.pdf --physical plate_A1H12.pdf
   ```

   Prints per-reaction recipe, per-block mastermixes, template + dilution-series recipes, NTCs,
   and multichannel warnings. `--plot` writes the logical block × template map; `--physical` writes
   a real A1–H12 (8×12) source-plate assignment and figure. Physical-layout conventions: samples
   fill rows (one block per column); a 1-column spacer separates samples from the dilution series;
   each NTC sits one row below its dilution points (the series "zero point"), coloured by mastermix.
4. Surface the plate map via the agent-plots skill; present volumes as a table for the user to
   confirm before they pipette.
5. When writing the protocol into a notebook, format volumes/recipes as tables (computed
   DataFrames where possible) and **add an editable "✎ Bench notes" callout after each protocol
   step** so the user can record deviations while pipetting, e.g.:

   ```
   ::: {.callout-note appearance="simple" title="✎ Bench notes"}
   *Notes / deviations while pipetting:*
   :::
   ```

## Primer / probe stocks

- Primer volume is derived from `primer_stock_uM` (per-primer concentration) and
  `primer_final_nM`. Confirm whether a "N µM" stock means µM **per primer** or total.
- **Convenient default: make pre-mixed pairs as a 20× stock** (e.g. 5 µM each → 250 nM final,
  added at 0.5 µL/10 µL). This matches **TaqMan assays, which ship as 20×** (primers + probe) and
  are slotted the same way (1/20 = 0.5 µL/10 µL). It is fine to request a different primer
  dilution for convenience — set `primer_stock_uM` accordingly.
- **Probe (TaqMan) assays need a probe-capable mastermix, not a SYBR mastermix.** Put a TaqMan
  assay in its own block with the correct `mastermix` string so it totals as a separate 2× stock.

## Spec fields

Required: `reps`, `rxn_ul`, `split_dead_ul`, `reagent_dead_frac`, `mm_ul_per10`,
`primer_stock_uM`, `primer_final_nM`, `multichannel_min_ul`/`max_ul`, `n_samples`,
`dilution{points,fold,top_tube_dilution_x}`, `blocks[]{name,mastermix,samples,dilseries}`.
Optional: `title`, `sample_names` (list, length `n_samples` — shown as a legend; **changes every
experiment**), `primer_stock_label` (display string, e.g. `"5 uM each = 20x"`).

Keep `assets/example_spec.json` generic; write each experiment's spec into that project (e.g.
`code/scratch/`), not into the skill.

## Notes

- The default source→qPCR split is 96→384. The logical map is rows = block × columns = template;
  if template columns exceed 12 or replicates overflow one plate, note it and assign wells/plates.
- Downstream analysis: see the **qpcr-analysis** skill. Interactive notebook work: **interactive-notebook**.
