"""Compare the learning-rate sweep runs of one model and apply the selection rule (plan §18):

  pick the LR with the highest validation pairwise accuracy (best over its evaluation steps);
  if two LRs are within TIE (0.5 percentage points), pick the one with the lower validation loss.
  If the winner is the smallest or largest LR tried, add one more point beyond it.

Reads results/<model>/runs/rho<ρ>_lr*_beta*_seed<seed>/ (after collect.py), so it works on any machine
that has pulled the results:

  python src/train/lr_sweep.py --model qwen3-4b
  python src/train/lr_sweep.py --model qwen3-4b --root runs    # straight from runs/ (on the cluster)

Validation loss is recomputed from the per-quartet scores with the run's own objective (same formula as
training). Writes results/<model>/lr_sweep.json.
"""

import argparse
import json
import re
from pathlib import Path

import numpy as np

from config import ROOT
from scoring import pair_weights, quartet_metrics

TIE = 0.005


def val_loss(r: np.ndarray, obj: dict) -> float:
    """Mean quartet loss (numpy version of scoring.quartet_loss) for r [N, 4]."""
    beta, pw = obj["beta"], pair_weights(obj)
    CW, CN, IW, IN = r.T.astype(np.float64)
    ell = lambda z: np.logaddexp(0.0, -z)
    loss = (pw["CW_IW"] * ell(beta * (CW - IW)) + pw["CN_IN"] * ell(beta * (CN - IN))
            + pw["CW_IN"] * ell(beta * (CW - IN)) + pw["CN_IW"] * ell(beta * (CN - IW)))
    if obj["name"] == "ties":
        for a, b in ((CW, CN), (IW, IN)):
            loss = loss + obj["tie_weight"] * 0.5 * (ell(beta * (a - b)) + ell(beta * (b - a)))
    return float(loss.mean())


def per_step(run: Path) -> list[dict]:
    """Validation metrics at every evaluation step, from quartet_scores.npz (results/) or eval/*.npz (runs/)."""
    cfg = json.load(open(run / "config.json"))["config"]
    obj = cfg["objective"]
    qs = run / "quartet_scores.npz"
    if qs.exists():
        z = np.load(qs)
        steps, scores = z["val_steps"], z["val_full"]
    else:   # straight from runs/: rebuild r from the per-token files and the reference cache
        from collect import load_ref, run_arrays
        scores_d, _ = run_arrays(run, load_ref(run.parent / "reference"))
        steps, scores = scores_d["val_steps"], scores_d["val_full"]
    out = []
    for s, r in zip(steps, scores):
        m = quartet_metrics(r)
        out.append({"step": int(s), "pairwise_acc": m["pairwise_acc"], "u": m["u"], "abs_v": m["abs_v"],
                    "worst_case_acc": m["worst_case_acc"], "loss": round(val_loss(r, obj), 6)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--rho", default="0.5")
    ap.add_argument("--seed", default="0")
    ap.add_argument("--root", default="results", help="results (after collect.py) or runs")
    args = ap.parse_args()
    base = ROOT / args.root / args.model
    base = base / "runs" if (base / "runs").is_dir() else base     # results/<model>/runs/ or runs/<model>/
    pat = re.compile(rf"^rho{re.escape(args.rho)}_lr([0-9.e+-]+)_beta[0-9.]+_seed{args.seed}$")
    runs = sorted((float(m.group(1)), p) for p in base.iterdir() if (m := pat.match(p.name)))
    if not runs:
        raise SystemExit(f"no rho{args.rho}_lr*_seed{args.seed} runs in {base}")

    rows = []
    for lr, run in runs:
        ev = per_step(run)
        done = (run / "summary.json").exists()
        best = max(ev, key=lambda x: (x["pairwise_acc"], -x["loss"]))
        best_u = max(ev, key=lambda x: x["u"])
        rows.append({"lr": lr, "run": run.name, "finished": done, "last_step": ev[-1]["step"],
                     "best_acc": best["pairwise_acc"], "best_acc_step": best["step"], "loss_at_best_acc": best["loss"],
                     "min_loss": min(x["loss"] for x in ev), "best_u": best_u["u"], "best_u_step": best_u["step"],
                     "acc_at_best_u": best_u["pairwise_acc"], "abs_v_at_best_u": best_u["abs_v"], "curve": ev})

    print(f"{args.model}: ρ = {args.rho}, seed {args.seed}, validation (full response)\n")
    print(f"{'LR':>8} {'status':>12} {'best acc':>9} {'@step':>6} {'loss there':>11} {'min loss':>9} "
          f"{'best u':>8} {'@step':>6} {'|v| there':>10}")
    for r in rows:
        status = "finished" if r["finished"] else f"at {r['last_step']}"
        print(f"{r['lr']:>8g} {status:>12} {r['best_acc']:>9.4f} {r['best_acc_step']:>6} {r['loss_at_best_acc']:>11.4f} "
              f"{r['min_loss']:>9.4f} {r['best_u']:>8.2f} {r['best_u_step']:>6} {r['abs_v_at_best_u']:>10.2f}")

    top = max(r["best_acc"] for r in rows)
    tied = [r for r in rows if top - r["best_acc"] < TIE]
    win = min(tied, key=lambda r: r["loss_at_best_acc"])
    lrs = [r["lr"] for r in rows]
    edge = win["lr"] in (min(lrs), max(lrs)) and len(lrs) > 1
    print(f"\nWinner: LR {win['lr']:g}" + (f" (tie within {TIE:.1%} with "
          f"{', '.join(f'{r['lr']:g}' for r in tied if r is not win)}; lower validation loss)" if len(tied) > 1 else ""))
    if not all(r["finished"] for r in rows):
        print("NOT FINAL: some runs are still in progress.")
    if edge:
        print(f"The winner is at the edge of the grid ({min(lrs):g}–{max(lrs):g}): add one more LR beyond it.")
    out = ROOT / args.root / args.model / "lr_sweep.json"
    json.dump({"rule": f"max validation pairwise accuracy; tie (< {TIE}) -> lower validation loss",
               "rho": args.rho, "seed": args.seed, "winner_lr": win["lr"], "final": all(r["finished"] for r in rows),
               "edge": edge, "runs": rows}, open(out, "w"), indent=1)
    print(f"-> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
