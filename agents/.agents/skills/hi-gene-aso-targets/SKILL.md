---
name: hi-gene-aso-targets
description: Systematically evaluate ASO strategies for up-regulating a haploinsufficient gene — unproductive splicing, 3'UTR miRNA sites, uORFs/5'UTR elements, RiboNN translation, and measured small-molecule panels. Invoke when asked to find ASO targets for raising the dosage of a gene.
argument-hint: "[gene symbol]"
---

# ASO target search for a haploinsufficient gene

Five orthogonal strategies for raising a gene's dosage. **This is not a pipeline** — it needs
judgement at every step, and most genes will come out negative. The job is to reach a
*defensible* answer, not a positive one.

Worked example, all five strategies, mostly negative:
`20250624_panexperiment_nmd_candidatejuncs/analysis/20260819_ATP6V0C_ASO_strategies.qmd`.

## Ask first

1. **Cell type / tissue** for expression gating — but push back if the phenotype doesn't
   single one out. A brain-wide phenotype (seizures + microcephaly + ID) argues for gating on
   *any* brain cell type, not neurons; this changed which target ranked first for ATP6V0C.
2. **Scope of any RiboNN walk** — it is slow (see `ribonn-setup` brain note). Agree the
   size before submitting.
3. Whether to include the small-molecule arm.

## Part 0 — Locus anatomy first, always

From `Reference.basic.FromTranscriptTools.bed.gz`: every transcript's `NMDFinderB` class,
UTR lengths/exon counts, `Introns`, and the pre-computed `uORF_*` columns.

- Diff the `Introns` strings between productive and NMD-coupled isoforms — the single
  differing splice site *is* the candidate switch target.
- **Note overlapping/readthrough genes now.** They cause two independent problems later
  (leafcutter cluster contamination, featureCounts ambiguity) and both are much harder to
  diagnose after the fact than to anticipate.
- **Verify the uORF annotation by de novo scan** — extract the spliced 5'UTR and find ATGs
  yourself. Cheap, and the annotation has a known short-ORF bug.

## Part 1 — Unproductive splicing

**Use SplisER SSE, not leafcutter PSI, for "how much is there to redirect".** PSI is a
within-cluster fraction, and clusters routinely merge a neighbouring gene's constitutive
introns into the denominator — apparent ΔPSI then tracks the *expression ratio* of the two
genes. Tell-tale: two constitutive introns of the same transcript moving in exact opposition.
SSE is per-site and immune.

Two numbers decide the strategy, and they are different questions:

| question | metric | verdict threshold |
|---|---|---|
| is it a real NMD substrate? | ΔSSE across UPF1 KD / SMG6-7 KD / CHX | consistent direction across all three |
| is it worth targeting? | **basal SSE** vs the canonical site | <5-10% basal ⇒ not worth it |

A 17-fold induction from 0.07% to 1.3% is a beautiful NMD signature and a useless target. Say
both things.

Scan *every* splice site in the locus for NMD responsiveness rather than trusting the
annotation, and plot a **lollipop of SSE at all donors/acceptors** in one well-expressed,
disease-relevant sample — it answers "is there anything here at all" in one figure.

## Part 2 — Gene-level expression across contrasts

Always run this alongside splicing; it catches things splicing cannot.

- Check **which contrasts the gene was filtered out of** — that is information, not a gap.
- Direction matters: cytoplasm-enriched + heavy-polysome-enriched ⇒ already exported, stable
  and well translated ⇒ no sequestered pool for *any* strategy to liberate.

⚠️ **featureCounts runs without `-O` in these pipelines.** A gene whose exons overlap another
annotated feature loses those reads to `Unassigned_Ambiguity` — discarded from *every* gene,
not reassigned. ATP6V0C was undercounted ~200-fold. **Sanity-check gene counts against
junction counts** before trusting any CPM. Note that overlapping genes all reading ~0 is
*evidence for* ambiguity, not against it.

## Part 3 — 3'UTR miRNA sites

Follow the MBD5 notebook (`20250331_clinvar_spliceai/analysis/20260720_MBD5_3UTR_ASO_targets.qmd`).

- **Use both TargetScan tables.** The conserved-site table alone gave ATP6V0C *one* site;
  adding the non-conserved table gave 237. Short 3'UTRs are mostly non-conserved sites.
- **Verify the coordinate mapping, don't assume it.** TargetScan's representative transcript
  may not be MANE — for ATP6V0C it was the *unproductive* isoform, with a 3'UTR starting
  ~360 nt earlier. Reconstruct each site's expected seed match from the family seed
  (`miR_Family_Info.txt`) + site type and confirm it against the genome. Expect ~100%.
  Site-type codes: 1 = 7mer-A1 (`revcomp(seed[2-7]) + A`), 2 = 7mer-m8 (`revcomp(seed[2-8])`),
  3 = 8mer (`revcomp(seed[2-8]) + A`).
- **Expression is a gate, not a weight** (Mullokandov 2012) — in/out, then rank survivors on
  raw context++. Never multiply the two.
- **Rank on context++, never percentile** — percentile is within-miRNA and not comparable
  across miRNAs.
- Check APA (PolyASite) so you target a 3'UTR the gene actually makes, and keep clear of the
  poly(A) signal.
- Report **GC%** of each candidate window — a 90% GC 20-mer is a bad oligo regardless of score.
- Check whether one 20-mer covers **two** gated sites; scores are additive.

Expect the strongest-scoring sites to belong to miRNAs absent from the tissue. That is the
usual outcome and it is the main thing the gate buys you.

## Part 4 — RiboNN

Read `ribonn-setup` (brain) first — canonical clone, the `--input`/`--output` fork, and runtime.

- **N-masking is not available**; use 20-nt deletions tiled across the UTRs.
- **State the sign convention explicitly**: ΔTE = deletion − WT, so **positive = repressive
  element = the ASO target**. Label it on every plot and track.
- **Interpret ΔTE against a reference distribution**, not zero — use the project's MANE
  internal-exon panel (`output/RiboNN_Internal5UTRManeExons.txt.gz`) for both the ΔTE scale
  and the baseline-TE percentile. A gene already at the 100th percentile of baseline TE has
  no headroom, which is a complete answer on its own.
- Tissue-specific columns exist (78 of them, incl. `SH.SY5Y`, `neurons`, `normal_brain_tissue`).
  Check whether the tissue choice matters, then **say so either way**.

## Part 5 — Small molecules

Query the dose-response DB (`20260310_diversesm_dr`). Gene expression **first**; only chase
splicing if expression moves.

- Use the **unfiltered** `log2TMM_CPM.bed`, not `log2Filtered_*` (the model's input drops
  low-expressed genes) — and prefer the plain `.bed` over `.sorted.bed.gz`, which has been
  observed stale.
- **Any apparent up-regulation by SF3B1 or CLK inhibitors is intron retention until proven
  otherwise.** Test it: plot gene-level Δ against Δ of the *spliced* canonical junction. Real
  up-regulation lies on y = x; intron retention goes horizontal.
- Weigh tolerability, not just effect size — a hit on a cytotoxic agent at 1 µM is not a lead.

## Reporting

- **Document negative results fully.** They are the usual outcome and the reason the notebook
  exists.
- **State when strategies disagree.** Regions of interest derived from one method are not a
  consensus; if RiboNN and TargetScan nominate different windows, say so plainly.
- **Flag AI-generated claims.** Any mechanistic interpretation from background knowledge goes
  in a callout headed as unverified, with the specific checks that would settle it.
- **Correct earlier errors in place**, in the notebook, with a note on what was wrong and why.
- Cross-reference candidates against **phyloP** (UCSC REST API, `phyloP470wayBW`) — an
  independent axis that costs one API call.
- Finish with an **IGV.js browser**: transcripts coloured by NMD class, phyloP, the ΔTE walk,
  splice-site usage, miRNA sites with scores, ROI bands. See the `igv-tracks` skill for the
  inline-feature gotchas (per-feature colour, per-exon thick/thin, ROI sets).

## Practical

- Compute-node kernel (`compute-kernel` skill) — the login node's 8 GiB is shared.
- Cache every external fetch under `code/scratch/<gene>_aso/cache/` so the notebook re-renders
  offline. Stream-grep huge downloads (`curl | funzip | awk`) rather than storing them.
- **Re-render from a clean kernel repeatedly while writing.** Cells written during a long
  interactive session systematically under-declare their dependencies — every bug found this
  way in the ATP6V0C notebook was an import or load that existed only in the live session.
