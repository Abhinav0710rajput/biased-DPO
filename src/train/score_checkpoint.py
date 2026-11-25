"""Score saved checkpoints of a finished run on splits that were not scored during training
(e.g. test / SciQ at the matched-u checkpoint, chosen after all runs are done).

  python src/train/score_checkpoint.py --run runs/qwen3-4b/rho1_lr2e-05_beta0.1_seed0 --steps 700 900
  python src/train/score_checkpoint.py --run ... --steps 700 --splits test

Uses the run's own config.json and its saved adapters (adapters/step_XXXXX/). Appends rows to the run's
eval_log.jsonl (marked posthoc_adapter) and writes eval/step_XXXXX_posthoc.npz. Splits already scored at a step
are skipped.
"""

import argparse
import json
from pathlib import Path

import numpy as np

from config import ROOT
from data import Encoder
from models import build_peft_model, load_tokenizer
from train import jsonl_append, load_adapter_weights, load_reference, score_splits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--steps", type=int, nargs="+", required=True)
    ap.add_argument("--splits", nargs="*", default=None)
    args = ap.parse_args()
    run = Path(args.run) if Path(args.run).is_absolute() else ROOT / args.run
    cfg = json.load(open(run / "config.json"))["config"]
    tok = load_tokenizer(cfg)
    ref, eval_enc = load_reference(cfg, Encoder(tok, cfg))
    model = build_peft_model(cfg, tok)
    log = run / "eval_log.jsonl"
    done = {(r["step"], r["split"]) for r in map(json.loads, open(log))}
    for step in args.steps:
        adapter = run / "adapters" / f"step_{step:05d}"
        if not adapter.exists():
            raise SystemExit(f"no adapter saved at step {step}")
        splits = [s for s in (args.splits or list(eval_enc)) if (step, s) not in done]
        if not splits:
            print(f"step {step}: all requested splits already scored")
            continue
        load_adapter_weights(model, adapter)
        rows, arrays = score_splits(model, tok, cfg, eval_enc, ref, splits, step)
        for row in rows:
            row["posthoc_adapter"] = cfg["eval"]["adapter_dtype"]
            jsonl_append(log, row)
            print(f"step {step} {row['split']}: u={row['u']:.3f} |v|={row['abs_v']:.3f} |w|={row['abs_w']:.3f} "
                  f"worst={row['worst_case_acc']:.3f}")
        out = run / "eval" / f"step_{step:05d}_posthoc.npz"
        old = dict(np.load(out)) if out.exists() else {}
        np.savez_compressed(out, **old, **arrays)


if __name__ == "__main__":
    main()
