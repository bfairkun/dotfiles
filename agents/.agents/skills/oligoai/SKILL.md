---
name: oligoai
description: RCC Midway HPC only. Run OligoAI to predict RNase H gapmer ASO knockdown efficacy from ASO sequence, target pre-mRNA context, sugar/backbone chemistry and dose. Invoke when scoring or ranking gapmer ASOs, tiling knockdown ASOs across a transcript, or working with the ASO Atlas dataset. NOT for splice-switching / steric-block ASOs.
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

## Hardware: needs an A100

`rinalmo/model/attention.py` imports `flash_attn` at module scope and `giga` sets
`use_flash_attn=True`. FlashAttention-2 needs sm80+, so on Midway3 only **midway3-0294**
works — `--constraint=a100`. `--device cpu` in `run_inference.py` will fail despite being
offered. See brain `midway3-gpu-partitions` (all PI-owned GPU partitions reject
`pi-yangili1`, so expect queue time).

A CPU fallback is possible but needs a weight conversion: the checkpoint stores packed
`mh_attn.Wqkv.weight`, while the non-flash path wants
`mh_attn.mh_attn.{to_q,to_k,to_v}.weight`. A plain 3-way row split is correct (packing is
`[all q | all k | all v]`, head layout already matches), and the two paths are otherwise
equivalent — same non-interleaved GPT-NeoX RoPE, same scale, no biases, and
`RiNALMo.forward` already flips mask polarity per path.

### Required patch with flash-attn ≥ 2.7

The repo pins flash-attn 2.3.2, whose `unpad_input` returns 4 values; ≥2.7 returns 5, so any
forward pass dies with `ValueError: too many values to unpack (expected 4)`. Patch the call
site before running:

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
cd /project/yangili1/bjf79/repos_not_projects/OligoAI
python run_inference.py <data.csv> --model_checkpoint weights/OligoAI_11_09_25.ckpt \
    --batch_size 32 --device cuda
```

The README's `--model_path` flag does not exist: the data path is **positional** and the flag
is `--model_checkpoint`. `run_inference.py` computes metrics and needs ground truth;
`run_inference_kcnt2.py` just appends an `oligoAI_scores` column — use that for novel designs.

## Interpreting output, and the traps that matter

**It is a ranker, not a knockdown estimator.** Measured on 10 held-out screens: predicted sd
**13.9** pp vs observed **31.5** pp, predictions shrunk toward the scaler mean (44.02). Use
it to order candidates within one gene and chemistry; do not quote a predicted percentage.
Reproduced per-screen Spearman **0.445** [IQR 0.24–0.59] against the paper's 0.419.

Traps in measured order of impact (Δ predicted inhibition, 159 ASOs across two screens):

1. **Unrecognised `transfection_method` silently becomes Electroporation** (`.get(method, 0)`,
   and index 0 *is* Electroporation, not "unknown"). Verified: a `TYPO_lipofection` string
   gives byte-identical output to Electroporation. Method spans **12.9 pp** — the single most
   damaging silent failure. Validate this column against the four exact strings.
2. **Dose-response is inverted.** 10 nM → 45.3, 20,000 nM → 39.1 (**−6.3 pp**): higher dose
   predicts *less* knockdown. Training doses are patent-screen doses (median 4,000 nM) and
   confound delivery method with target difficulty. **Never use this model for dose-response.**
   Hold dose fixed when comparing ASOs.
3. **`rna_context` matters a lot** — blanking it moves predictions mean |Δ| **6.8 pp**, max
   23.2. 10.7% of training rows have empty context, so it is tolerated but not equivalent.
   Supply context consistently across everything you compare.
4. **Split with seed 1, not 42.** `train_aso.py` uses `random_state=args.seed if args.seed
   else 42` and the README trains with `--seed 1`. Seed 1 reproduces the paper's
   134,948/18,309/25,367; seed 42 puts **27 of 38** "test" patents into the training set.
5. **Write `'CET'`, never `'cET'`.** The training CSVs contain `'CET'` (an `.upper()` of the
   correct `cEt`) but the vocab key is `'cET'`, so every cEt position trained as index 0, the
   padding index — a frozen zero vector. Row 3 never received a gradient (Adam `exp_avg_sq`
   exactly 0). Writing `'cET'` selects that untrained row. Measured effect is small (+0.29 pp)
   but it is free to get right. `'OME'`/`'F'` also fall through to 0.
6. **`dosage` NaN is imputed with the median of *your file*,** not the training median. An
   all-blank column yields `median()=NaN` → **NaN predictions, no error.** Always set dose.
7. `sugar_mods`/`backbone_mods` length is silently padded/truncated to the sequence — an
   off-by-one misaligns the chemistry track with no warning.

**The chemistry channel is nearly inert**: the largest sugar/backbone perturbation moves
predictions **1.1 pp** against 13.2 pp of ASO-to-ASO variation. Cross-chemistry questions
("MOE 5-10-5 vs cEt 3-10-3 here?") are unsupported. Contributing cause: `aso_feature_combiner`
and `transfection_method_embedder` were never unfrozen during training and sit at random init
(absent from both optimizer param groups; weights match `nn.Linear` default init by KS test).
Three Methods statements in the paper do not describe the released checkpoint.
