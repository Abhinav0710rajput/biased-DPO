"""Sanity checks before any real run (plan §9). Run once per model, on the GPU it will train on:

  python src/train/sanity.py --model qwen3-4b            # T1, T2, T3, T6 (minutes)
  python src/train/sanity.py --model tiny-debug          # same on CPU with a tiny random model

T1  the (u, v, w) loss equals the pair-by-pair loss for random r            (every objective, several ρ)
T2  step-0 gradients are identical for ρ ∈ {0, 0.5, 1}                     (same batch, same LoRA init)
T3  the batch sequence (quartet-id hashes) is identical across ρ and differs across seeds
T6  r = 0 exactly at step 0: on a training batch (online reference) and on the evaluation scorer
    (against runs/<model>/reference/ if it exists, else against the adapter-disabled model)
T4 (overfit 32 quartets) and T5 (positive control) are training runs; see Docs/checklist.md.
Writes runs/<model>/m5/sanity.json.
"""

import argparse
import copy
import json

import numpy as np
import torch

from config import ROOT, load_config, reference_dir
from data import Encoder, batch_hash, batches, collate, load_quartets
from models import build_peft_model, load_tokenizer, score_encoded
from scoring import quartet_loss, quartet_loss_pairwise, to_device, token_logps


def t1() -> dict:
    g = torch.Generator().manual_seed(0)
    worst = 0.0
    for obj in ([{"name": "dpo", "rho": r, "beta": 0.1} for r in (0, 0.25, 0.5, 0.75, 1)]
                + [{"name": "ties", "rho": 0, "beta": 0.1, "tie_weight": 0.5},
                   {"name": "posctrl", "rho": 1, "beta": 0.1, "posctrl_weights": {"CW_IN": 0.8, "CN_IW": 0.2}}]):
        r = torch.randn(1000, 4, generator=g, dtype=torch.float64) * 20
        worst = max(worst, float((quartet_loss(r, obj) - quartet_loss_pairwise(r, obj)).abs().max()))
    return {"pass": worst < 1e-6, "max_abs_diff": worst}


def first_batch(cfg, enc_train, step=0):
    t = cfg["train"]
    for s, _, idx in batches(len(enc_train.qids), t["seed"], t["epochs"], t["batch_quartets"]):
        if s == step:
            return idx


def t2_t6(cfg, model, tok, enc_train) -> tuple[dict, dict]:
    dev = next(model.parameters()).device
    idx = first_batch(cfg, enc_train)[: cfg["train"]["micro_quartets"]]
    b = to_device(collate(enc_train, idx, tok.pad_token_id), dev)
    params = [p for p in model.parameters() if p.requires_grad]
    grads, max_r = {}, 0.0
    for rho in (0.0, 0.5, 1.0):
        obj = dict(cfg["objective"], name="dpo", rho=rho)
        model.zero_grad(set_to_none=True)
        lp = token_logps(model, b)
        with torch.no_grad(), model.disable_adapter():
            lp_ref = token_logps(model, b)
        r = (lp - lp_ref).sum(-1).view(-1, 4)
        max_r = max(max_r, float(r.detach().abs().max()))
        (quartet_loss(r, obj).sum() / len(idx)).backward()
        grads[rho] = torch.cat([p.grad.detach().float().flatten() for p in params if p.grad is not None])
    model.zero_grad(set_to_none=True)
    scale = float(grads[0.5].abs().max())
    diffs = {f"{a}_vs_{c}": float((grads[a] - grads[c]).abs().max()) / max(scale, 1e-30)
             for a, c in ((0.0, 0.5), (0.0, 1.0), (0.5, 1.0))}
    t2 = {"pass": scale > 0 and max(diffs.values()) < 1e-3, "max_rel_diff": diffs, "grad_max": scale}
    t6 = {"train_batch_max_abs_r": max_r}
    return t2, t6


def t3(cfg, enc_train) -> dict:
    t = cfg["train"]
    n = len(enc_train.qids)

    def seq(seed):
        return [batch_hash([enc_train.qids[i] for i in idx]) for _, _, idx in batches(n, seed, t["epochs"],
                                                                                      t["batch_quartets"])]
    # the batch sequence is a function of (seed, data) only: ρ never enters batches(); check determinism + seeds
    a, b, c = seq(t["seed"]), seq(t["seed"]), seq(t["seed"] + 1)
    return {"pass": a == b and a != c, "steps": len(a), "first_hash": a[0]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--set", nargs="*", default=[])
    ap.add_argument("--eval-quartets", type=int, default=32)
    args = ap.parse_args()
    cfg = load_config(args.model, args.set)
    tok = load_tokenizer(cfg)
    enc = Encoder(tok, cfg)
    enc_train = enc.encode(load_quartets(ROOT / cfg["data"]["dir"] / cfg["data"]["train"]))
    model = build_peft_model(cfg, tok)
    res = {"T1": t1()}
    res["T2"], t6 = t2_t6(cfg, model, tok, enc_train)
    res["T3"] = t3(cfg, enc_train)

    # T6 on the evaluation scorer
    split = cfg["data"]["eval_splits"][0]
    ref_file = reference_dir(cfg) / f"{split}.npz"
    n = args.eval_quartets
    if ref_file.exists():                      # compare on the quartets the cache has (batching must match it)
        z = np.load(ref_file)
        n = min(n, len(z["qids"]))
        n -= n % cfg["eval"]["batch_quartets"] if n > cfg["eval"]["batch_quartets"] else 0
    e = enc.encode(load_quartets(ROOT / cfg["data"]["dir"] / f"{split}.jsonl")[:n])
    pol, _ = score_encoded(model, e, cfg["eval"]["batch_quartets"], tok.pad_token_id)
    if ref_file.exists():
        ref = z["logp"][: len(pol)]
        t6["eval_against"] = str(ref_file.relative_to(ROOT))
    else:
        with model.disable_adapter():
            ref, _ = score_encoded(model, e, cfg["eval"]["batch_quartets"], tok.pad_token_id)
        t6["eval_against"] = "adapter-disabled model (no reference cache yet)"
    t6["eval_max_abs_r"] = float(np.abs(pol.astype(np.float64) - ref).max())
    t6["pass"] = t6["train_batch_max_abs_r"] == 0.0 and t6["eval_max_abs_r"] == 0.0
    res["T6"] = t6
    for k, v in res.items():
        print(k, "PASS" if v["pass"] else "FAIL", {kk: vv for kk, vv in v.items() if kk != "pass"})
    out = ROOT / cfg["output"]["reference_root"] / cfg["model"]["name"] / "m5"
    out.mkdir(parents=True, exist_ok=True)
    json.dump(res, open(out / "sanity.json", "w"), indent=1)
    raise SystemExit(0 if all(v["pass"] for v in res.values()) else 1)


if __name__ == "__main__":
    main()
