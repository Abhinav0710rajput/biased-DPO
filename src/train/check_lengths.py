"""M5 length check (V8) with the policy model's tokenizer (CPU).

  python src/train/check_lengths.py --model qwen3-4b

The data was length-balanced in whitespace words. Here: response tokens (without the end-of-turn token,
which every response has) for warm vs neutral, per pair type:
  matched  CW vs CN, IW vs IN     (V8 rows: same correctness, different tone)
  crossed  CW vs IN, IW vs CN     (what crossed pairs compare)
Reports the V8 pass rate (|warm − neutral| ≤ max(2, 10% of the longer)), the mean signed difference
(warm − neutral; should be ≈ 0) and the share where warm is longer. Writes runs/<model>/m5/lengths.json.
"""

import argparse
import json

import numpy as np

from config import ROOT, load_config
from data import load_quartets
from models import load_tokenizer

PAIRS = {"CW-CN": ("CW", "CN"), "IW-IN": ("IW", "IN"), "CW-IN": ("CW", "IN"), "IW-CN": ("IW", "CN")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    args = ap.parse_args()
    cfg = load_config(args.model)
    tok = load_tokenizer(cfg)
    report = {}
    for split in ["train", "val", "test", "ood_sciq"]:
        qs = load_quartets(ROOT / "data/quartets" / f"{split}.jsonl")
        n = {k: np.array([len(tok.encode(q["responses"][k]["text"], add_special_tokens=False)) for q in qs])
             for k in ("CW", "CN", "IW", "IN")}
        rep = {"quartets": len(qs), "mean_tokens": {k: round(float(v.mean()), 2) for k, v in n.items()}}
        for name, (a, b) in PAIRS.items():
            d = n[a] - n[b]
            tol = np.maximum(2, 0.1 * np.maximum(n[a], n[b]))
            rep[name] = {"v8_pass": round(float(np.mean(np.abs(d) <= tol)), 4), "mean_diff": round(float(d.mean()), 3),
                         "mean_abs_diff": round(float(np.abs(d).mean()), 3),
                         "warm_longer": round(float(np.mean(d > 0)), 4), "warm_shorter": round(float(np.mean(d < 0)), 4)}
        report[split] = rep
        print(split, rep["mean_tokens"], {k: (rep[k]["v8_pass"], rep[k]["mean_diff"]) for k in PAIRS})
    out = ROOT / cfg["output"]["reference_root"] / cfg["model"]["name"] / "m5"
    out.mkdir(parents=True, exist_ok=True)
    json.dump(report, open(out / "lengths.json", "w"), indent=1)
    print("wrote", out / "lengths.json")


if __name__ == "__main__":
    main()
