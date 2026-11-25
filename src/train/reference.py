"""Once per model: cache the frozen model's per-token log-probs on the evaluation splits, and report the
UNTRAINED model's own u/v/w (its pre-existing fact and tone preferences, computed on log π_ref).

  python src/train/reference.py --model qwen3-4b
Outputs runs/<model>/reference/:
  <split>.npz      logp (per token, flat), offsets [4N+1], span (flat bool), qids  (order CW, CN, IW, IN)
  base_uvw.json    u/v/w, gap accuracies, worst-case accuracy on log π_ref: summed, per-token mean, answer span
  meta.json        config, provenance, tokenization hash per split
Every training run reads these files; its step-0 evaluation must reproduce them exactly (T6).
"""

import argparse
import json
import time

import numpy as np

from config import ROOT, data_fingerprint, git_info, load_config, reference_dir, versions
from data import Encoder, load_quartets
from models import load_model, load_tokenizer, score_encoded, tokenization_hash
from scoring import quartet_metrics, sums_from_tokens


def base_report(logp, offsets, span) -> dict:
    n_tok = np.diff(offsets).reshape(-1, 4)
    n_span = sums_from_tokens(span.astype(np.float64), offsets)
    s_sum = sums_from_tokens(logp, offsets)
    s_span = sums_from_tokens(logp, offsets, span)
    return {"sum": quartet_metrics(s_sum),
            "per_token": quartet_metrics(s_sum / np.maximum(n_tok, 1)),
            "answer_span": quartet_metrics(s_span),
            "answer_span_per_token": quartet_metrics(s_span / np.maximum(n_span, 1)),
            "mean_tokens": dict(zip(["CW", "CN", "IW", "IN"], np.round(n_tok.mean(0), 3).tolist()))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--set", nargs="*", default=[], help="config overrides key=value")
    ap.add_argument("--limit", type=int, default=None, help="debug: first N quartets per split")
    args = ap.parse_args()
    cfg = load_config(args.model, args.set)
    out = reference_dir(cfg)
    out.mkdir(parents=True, exist_ok=True)
    fp = data_fingerprint(cfg)
    tok = load_tokenizer(cfg)
    enc = Encoder(tok, cfg)
    model = load_model(cfg, tok)
    meta = {"config": cfg, "provenance": {"git": git_info(), "data_sha256": fp, "versions": versions(),
                                          "limit": args.limit}, "splits": {}}
    report = {}
    for split in cfg["data"]["eval_splits"]:
        t0 = time.time()
        qs = load_quartets(ROOT / cfg["data"]["dir"] / f"{split}.jsonl")[: args.limit]
        e = enc.encode(qs)
        logp, span = score_encoded(model, e, cfg["eval"]["batch_quartets"], tok.pad_token_id)
        offsets = e.offsets()
        np.savez_compressed(out / f"{split}.npz", logp=logp, offsets=offsets, span=span, qids=np.array(e.qids))
        meta["splits"][split] = {"quartets": len(qs), "tokens": int(len(logp)), "tokenization": tokenization_hash(e),
                                 "seconds": round(time.time() - t0, 1)}
        report[split] = base_report(logp, offsets, span)
        print(split, meta["splits"][split], "| per-token u/v/w:",
              {k: report[split]["per_token"][k] for k in ("u", "v", "w")})
    json.dump(report, open(out / "base_uvw.json", "w"), indent=1)
    json.dump(meta, open(out / "meta.json", "w"), indent=1, default=str)
    print("wrote", out)


if __name__ == "__main__":
    main()
