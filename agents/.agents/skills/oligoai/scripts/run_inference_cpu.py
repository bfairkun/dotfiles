"""Run OligoAI on CPU by swapping FlashAttention for the repo's pure-PyTorch attention.

Why this exists: rinalmo/model/attention.py imports flash_attn at module scope and the `giga`
config sets use_flash_attn=True, so stock run_inference.py needs an Ampere+ GPU. Midway3 has
exactly one A100 (midway3-0294) and it is usually full. The sequences here are tiny (ASO ~22
tokens, target context ~122), so CPU is entirely practical.

The two attention paths are mathematically equivalent but store weights differently:
  flash      lm.transformer.blocks.N.mh_attn.Wqkv.weight            (3*1280, 1280) packed
  non-flash  lm.transformer.blocks.N.mh_attn.mh_attn.{to_q,to_k,to_v}.weight
`rearrange(qkv, 'b s (three h d) -> b s three h d')` means the packed rows are ordered
[all of q | all of k | all of v], and within each the head layout (h, d) already matches the
non-flash `.view(bs, -1, num_heads, head_dim)`. So a plain 3-way row split is correct.

Equivalence verified by reading both paths: same RoPE (non-interleaved GPT-NeoX, base 10000,
dim=head_dim -- `rotate_half` reproduces flash's interleaved=False formula), same 1/sqrt(head_dim)
softmax scale, no qkv/out_proj biases, and RiNALMo.forward already flips the pad-mask polarity
for each path. Pad positions differ (flash physically unpads, here they carry garbage forward)
but attention never attends TO pads and nothing else mixes across positions, so every non-pad
output is unchanged -- and pads are dropped again at pooling.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.stats import spearmanr
from torch.utils.data import DataLoader

REPO = Path('/project/yangili1/bjf79/repos_not_projects/OligoAI')
sys.path.insert(0, str(REPO))

import rinalmo.config as rinalmo_config  # noqa: E402
import train_aso  # noqa: E402
from rinalmo.data.alphabet import Alphabet  # noqa: E402
from rinalmo.data.downstream.aso.dataset import ASODataset  # noqa: E402


class ASODatasetWithLen(ASODataset):
    def __len__(self):
        return len(self.df)


def cpu_model_config(name):
    cfg = rinalmo_config.model_config(name)
    cfg.model.transformer.use_flash_attn = False
    return cfg


def convert_state_dict(sd, num_heads=20):
    """Split packed Wqkv into to_q/to_k/to_v and re-nest attention keys."""
    out, n = {}, 0
    for k, v in sd.items():
        if k.endswith('mh_attn.Wqkv.weight'):
            base = k[: -len('Wqkv.weight')]
            q, kk, vv = v.chunk(3, dim=0)
            out[f'{base}mh_attn.to_q.weight'] = q
            out[f'{base}mh_attn.to_k.weight'] = kk
            out[f'{base}mh_attn.to_v.weight'] = vv
            n += 1
        elif k.endswith('mh_attn.out_proj.weight'):
            base = k[: -len('out_proj.weight')]
            out[f'{base}mh_attn.out_proj.weight'] = v
        else:
            out[k] = v
    print(f'converted {n} attention blocks')
    return out


def load_model(ckpt_path):
    ckpt = torch.load(ckpt_path, map_location='cpu', weights_only=False)
    hp = dict(ckpt['hyper_parameters'])
    train_aso.model_config = cpu_model_config          # patch before __init__ builds RiNALMo
    model = train_aso.ASOInhibitionPredictionWrapper(**hp)
    missing, unexpected = model.load_state_dict(convert_state_dict(ckpt['state_dict']), strict=False)
    # rotary inv_freq buffers are re-derived at construction and are not stored by the flash path
    missing = [m for m in missing if 'rotary_emb.inv_freq' not in m]
    if missing or unexpected:
        raise RuntimeError(f'state_dict mismatch\nmissing={missing[:10]}\nunexpected={unexpected[:10]}')
    print(f'scaler mean={model.scaler._mean.item():.4f} std={model.scaler._std.item():.4f}')
    return model.eval()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('data_path')
    p.add_argument('--model_checkpoint', default=str(REPO / 'weights/OligoAI_11_09_25.ckpt'))
    p.add_argument('--output_path', default=None)
    p.add_argument('--batch_size', type=int, default=16)
    p.add_argument('--threads', type=int, default=16)
    args = p.parse_args()

    torch.set_num_threads(args.threads)
    model = load_model(args.model_checkpoint)

    ds = ASODatasetWithLen(data_path=args.data_path, alphabet=Alphabet(), pad_to_max_len=True)
    dl = DataLoader(ds, batch_size=args.batch_size, shuffle=False, num_workers=0)
    print(f'{len(ds)} rows | max_aso_len={ds.max_enc_seq_len} max_ctx_len={ds.max_context_len}')

    preds = []
    with torch.no_grad():
        for i, b in enumerate(dl):
            aso, chem, bb, ctx, _, dose, tm, _ = b
            preds.extend(model.scaler.inverse_transform(model(aso, chem, bb, ctx, dose, tm)).numpy().ravel())
            if (i + 1) % 10 == 0:
                print(f'  {(i + 1) * args.batch_size}/{len(ds)}', flush=True)

    df = ds.df.copy()
    df['oligoai_pred'] = preds

    # Write BEFORE scoring. Inference is the expensive part; a crash in the optional metrics
    # below must never discard it.
    out = args.output_path or str(Path(args.data_path).with_suffix('')) + '_preds.csv'
    df.to_csv(out, index=False)
    print(f'wrote {out}')

    # Metrics only make sense with real, varying ground truth. Novel designs carry a constant
    # dummy `inhibition_percent`, which makes every within-screen Spearman NaN.
    truth = df['inhibition_percent']
    if truth.notna().sum() < 2 or truth.nunique() < 2:
        print('no varying ground truth in input -> skipping accuracy metrics')
        return
    rho = [spearmanr(g.oligoai_pred, g.inhibition_percent).statistic
           for _, g in df.groupby('custom_id') if len(g) > 1 and g.inhibition_percent.nunique() > 1]
    rho = [r for r in rho if not np.isnan(r)]
    if rho:
        print(f'\nper-screen Spearman: median={np.median(rho):.4f} '
              f'IQR=[{np.percentile(rho, 25):.4f},{np.percentile(rho, 75):.4f}] n={len(rho)}')
        print('paper reference: median per-screen Spearman 0.419 [IQR 0.290-0.533] over 299 test screens')
    else:
        print('no screen had >1 distinct measured value -> no per-screen Spearman')
    print(f'overall Pearson r={np.corrcoef(df.oligoai_pred, truth)[0, 1]:.4f}  '
          f'MAE={np.abs(df.oligoai_pred - truth).mean():.4f}')


if __name__ == '__main__':
    main()
