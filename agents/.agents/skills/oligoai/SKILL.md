---
name: oligoai
description: RCC Midway HPC only. Run OligoAI to rank RNase H gapmer ASOs by predicted knockdown from ASO sequence, target pre-mRNA context, sugar/backbone chemistry and dose. Invoke when scoring or ranking gapmer ASOs, tiling knockdown ASOs along a transcript, or working with the ASO Atlas dataset. Also read it before assuming OligoAI can answer a question it cannot: it is out of scope for splice-switching/steric-block ASOs, allele-selective design (it has no concept of ASO-target mismatch), choosing a target region (it is blind to exon/intron/junction), dose-response, absolute knockdown values, and non-human targets.
---

# OligoAI

Predicts **percent knockdown** for RNase H-recruiting gapmer ASOs. RiNALMo-giga (650M-param
RNA LM) encodes the ASO and its target site ±50 nt of pre-mRNA context; learned embeddings
add per-position sugar and backbone chemistry; an MLP head combines those with
`log1p(dose) × transfection-method` embedding. Trained on ASO Atlas (188,521 gapmers, 334
genes, LLM-mined from 417 ISIS/IONIS patents). Science and caveats → brain wiki
`hill-2026-oligoai-aso-atlas`.

**Scope: RNase H gapmers only.** The readout is knockdown of total target RNA, which is
meaningless for a steric blocker. Steric/splice-switching rows were excluded from training.
Do not use it for splice-switching design.

## Where things are

| | |
|---|---|
| repo | `/project/yangili1/bjf79/repos_not_projects/OligoAI` (fork of RiNALMo) |
| checkpoint | `<repo>/weights/OligoAI_11_09_25.ckpt` (2.9 GB, Lightning, from HF `barneyhill/OligoAI`) |
| training data | `<repo>/data/aso_inhibitions_21_08_25_incl_context_w_flank_50_df.csv.gz` |
| env | `agent_oligoai` — python 3.11, torch 2.5.1+cu121, flash-attn 2.7.4, lightning 2.4.0 |
| dataset/atlas repo | `/project/yangili1/bjf79/repos_not_projects/aso_atlas` (needs `src.formats` importable; run from its root) |

Keep torch **<2.6**: the checkpoint pickles a `StandardScaler` into its hyperparameters and
torch 2.6's `weights_only=True` default refuses to load it.

## Hardware: prefer CPU

Stock `run_inference.py` needs an A100. `rinalmo/model/attention.py` imports `flash_attn` at
module scope and `giga` sets `use_flash_attn=True`; FlashAttention-2 needs sm80+, so on
Midway3 only **midway3-0294** works (`--constraint=a100`), and `--device cpu` fails despite
being offered. That is 1 of 11 gpu nodes and usually full — see brain
`midway3-gpu-partitions`.

**Use `scripts/run_inference_cpu.py` instead.** It swaps in the repo's pure-PyTorch attention
and converts the weights (the checkpoint stores packed `mh_attn.Wqkv.weight`; the non-flash
path wants `mh_attn.mh_attn.{to_q,to_k,to_v}.weight`, and a 3-way row split is correct because
packing is `[all q | all k | all v]` with a matching head layout). Everything else is already
equivalent: same non-interleaved GPT-NeoX RoPE, same `1/sqrt(head_dim)` scale, no biases, and
`RiNALMo.forward` flips mask polarity per path.

**Validated against the A100** on 3,788 rows: Pearson **r = 1.000000**, mean |Δ| 0.007 pp, max
|Δ| 0.063 pp (fp16 autocast vs fp32). All downstream conclusions identical to 3 decimals.

```bash
python scripts/run_inference_cpu.py <data.csv> --threads 16 --output_path <out.csv>
```

Sizing, from seven runs of 460–6,903 rows on caslake with 16 cores: **≈40–70 s startup +
0.16 s/row**, peak RSS 6.1 GB, so `--cpus-per-task=16 --mem=16G` is ample. Sequences are short
(ASO ~22 tokens, context ~122), which is why CPU is practical at all.

| ASOs | wall time |
|---|---|
| 100 | ~1 min |
| 1,000 | ~3 min |
| 10,000 | ~27 min |
| 200,000 (whole-locus 1 nt walk) | **~9 h** |

Batch everything into one process — startup is paid per invocation. Below ~10k rows CPU beats
waiting for the A100; for a full-locus walk, either chunk across several jobs or take the GPU
queue. Do not extrapolate from a couple of small runs: an early fit on three ~1k-row files
underestimated the per-row cost by 2.5x.

### GPU route only: required patch with flash-attn ≥ 2.7

The repo pins flash-attn 2.3.2, whose `unpad_input` returns 4 values; ≥2.7 returns 5, so any
GPU forward pass dies with `ValueError: too many values to unpack (expected 4)`. The CPU
script never touches this code path. Patch the call site before running on GPU:

```python
import rinalmo.model.attention as rma
from flash_attn.bert_padding import unpad_input as _u
rma.unpad_input = lambda h, m: _u(h, m)[:4]
```

## Input CSV

`ASODataset` reads a CSV needing all of:

| column | format |
|---|---|
| `aso_sequence_5_to_3` | DNA, 5′→3′, uppercase (`T`→`U` internally) |
| `rna_context` | RNA (`ACGU`), sense/pre-mRNA orientation: **50 nt upstream + revcomp(ASO) + 50 nt downstream**. Not masked — the target site is present verbatim at offset 50 |
| `sugar_mods` | string repr of a list, one entry per nt: `"['MOE','MOE',...,'DNA',...]"` |
| `backbone_mods` | string repr of a list, length L; element *i* = linkage *i*→*i+1*; last is `'<PAD>'` |
| `dosage` | float, **nM** |
| `transfection_method` | exactly `Electroporation` / `Gymnosis` / `Other` / `Lipofection` |
| `inhibition_percent` | float; **required** — put a dummy `0.0` for novel designs |
| `custom_id` | grouping key for per-screen metrics |
| `split` | `train`/`val`/`test` — only `run_inference.py` needs it |

## Running

```bash
source /home/bjf79/miniconda3/etc/profile.d/conda.sh && conda activate agent_oligoai
python <skill>/scripts/run_inference_cpu.py <data.csv> --threads 16 --output_path <out.csv>
```

Prints per-screen Spearman against `inhibition_percent` when real values are present, and adds
an `oligoai_pred` column. Submit it to `caslake`, not a login node (6 GB peak, and the login
cgroup is 8 GiB shared across all your sessions).

On GPU instead, from the repo root, after applying the patch above:
`python run_inference.py <data.csv> --model_checkpoint weights/OligoAI_11_09_25.ckpt --device cuda`.
The README's `--model_path` flag does not exist — the data path is **positional** and the flag
is `--model_checkpoint`. `run_inference.py` needs ground truth and a `split` column;
`run_inference_kcnt2.py` just appends `oligoAI_scores` — use that for novel designs.

## What it can and cannot answer

Established by running the released checkpoint over ten held-out screens (767 ASOs) —
full evaluation in `20250331_clinvar_spliceai/analysis/20260930_oligoai_evaluation.qmd`.

**The one validated use: rank gapmers within one gene, at fixed chemistry, length, dose and
delivery.** Reproduced per-screen Spearman **0.445** [IQR 0.24–0.59] against the paper's 0.419,
and it is not a cheap heuristic in disguise — the best sequence-composition baseline (duplex ΔG)
reaches only 0.077 and GC content −0.100.

Everything below is a measured **no**:

| question | why not |
|---|---|
| "will this give X% knockdown?" | Not calibrated: predicted sd **13.9** pp vs **31.5** measured, shrunk toward the training mean (44.02) |
| "is this ASO inactive?" | ASOs measured at ~0% knockdown are predicted 20–60%, same range as active ones |
| "allele-selective: matched vs mismatched allele?" | **No concept of ASO–target complementarity.** A target mismatch opposite the gap moves the prediction −0.19 pp; a fully scrambled ASO +0.42 pp (40.2%→40.6%). Zero mismatched pairs exist in training. Use Tm/alignment instead |
| "exon, intron or junction?" | Blind to position. Within genes the measured exon-over-intron difference (5/7 genes) is reproduced in only 3/7, and the sign is inverted on the largest effect in the data |
| "16-mer or 20-mer?" | Length moves predictions **7×** more than chemistry (5.0 vs 0.7 pp) and predicts shorter is better — an artefact of length/chemistry confounding in training. Hold length fixed |
| "MOE or cEt wings?" | Chemistry channel is near-inert (≤1.1 pp); see the encoding bug below |
| "what dose?" | Dose-response is **inverted** (10 nM → 45.3%, 20,000 nM → 39.1%) |
| splice-switching ASOs | Out of scope by construction (see above) |
| non-human targets | **Trained on human rows only, with no species input.** Mouse/other targets are extrapolation and the model cannot signal it |

The flanking context *is* used, but as sequence rather than annotation: destroying it leaves the
mean prediction unchanged while moving individual predictions 5–8 pp, and the ranking degrades
to Spearman 0.84 (flanks shuffled) → 0.68 (flanks removed). So supply context consistently, but
do not expect positional reasoning from it.

Dose is safe to pick anywhere in **10–20,000 nM** (all pairs agree ≥0.94 for ranking). Delivery
method usually matters little (median agreement 0.92, median top-10 shortlist overlap 7/10) but
**not always**: in 2 of 10 screens the worst method pair fell to 0.39–0.40 with only 1–2 of 10
shortlist ASOs retained, and there is no way to tell in advance. Fix one setting and report it.

Three of ten evaluation genes occurred in the training split via other patents, so splitting by
patent is not splitting by gene — check gene overlap before calling a set held-out.

Traps in measured order of impact (Δ predicted inhibition):

1. **Unrecognised `transfection_method` silently becomes Electroporation** (`.get(method, 0)`,
   and index 0 *is* Electroporation, not "unknown"). Verified: a `TYPO_lipofection` string
   gives byte-identical output to Electroporation. Method spans **12.9 pp** — the single most
   damaging silent failure. Validate this column against the four exact strings.
2. **Empty `rna_context` is accepted silently** and shifts predictions by mean |Δ| 6.8 pp,
   max 23.2. 10.7% of training rows have no context, so the model tolerates it but it is not
   equivalent. Never mix rows with and without context in one comparison.
3. **Split with seed 1, not 42.** `train_aso.py` uses `random_state=args.seed if args.seed
   else 42` and the README trains with `--seed 1`. Seed 1 reproduces the paper's
   134,948/18,309/25,367; seed 42 puts **27 of 38** "test" patents into the training set.
4. **Write `'CET'`, never `'cET'`.** See the encoding bug below; writing `'cET'` selects an
   untrained embedding row. Measured cost is small (+0.29 pp) but it is free to avoid.
5. **`dosage` NaN is imputed with the median of *your file*,** not the training median. An
   all-blank column yields `median()=NaN` → **NaN predictions, no error.** Always set dose.
6. `sugar_mods`/`backbone_mods` length is silently padded/truncated to the sequence — an
   off-by-one misaligns the chemistry track with no warning.
7. Metrics are only meaningful with varying ground truth. `scripts/run_inference_cpu.py`
   writes predictions before scoring and skips metrics on constant dummy values; the repo's own
   `run_inference.py` does not, and crashes *after* inference, discarding the results.

## Why chemistry is inert: the encoding bug

Sugar chemistry is looked up in `{'<pad>': 0, 'DNA': 1, 'MOE': 2, 'cET': 3}` via
`vocab.get(token, pad_index)`. The released training table writes cEt as **`CET`** (an
upper-cased copy of the correct annotation), which does not match the key `cET` and falls
through to index 0 — the *padding* index, which `nn.Embedding(padding_idx=0)` pins at exactly
zero and never trains. So all **412,393** cEt positions (13% of sugar tokens) were encoded as an
unlearnable zero vector, and the `cET` row received no gradient at all (Adam `exp_avg_sq`
exactly 0). `'OME'` and `'F'` hit the same fall-through, so those chemistries are encoded
identically to cEt.

Compounding it, `aso_feature_combiner` — the module the paper says learns cross-modal
sequence–chemistry interactions — and `transfection_method_embedder` were never unfrozen during
fine-tuning and remain at random initialisation (absent from both optimizer param groups;
weights indistinguishable from `nn.Linear` default init by KS test). Three Methods statements in
the paper therefore do not describe the released checkpoint. Fixing the vocabulary string alone,
without retraining, would make the model worse rather than better.
