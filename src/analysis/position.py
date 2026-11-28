"""Where in the response v and w live: signed v (left) and w (right) by ρ, split into the text before the answer
(prefix), the answer tokens, and everything after the answer (suffix: punctuation + end token); last row = their sum.

  python src/analysis/position.py --model qwen3-4b
  python src/analysis/position.py --model qwen3-4b --beta 0.05

Uses token_r.npz at each run's best-val-u step (collect.py keeps the best and final steps), the same checkpoint as
vw_by_rho.py and fact_gaps.py. prefix + answer + suffix = the full-response value.
Writes results/<model>/figures/position_vw_beta<β>.png and position_vw_beta<β>.json.
"""

import argparse
import json
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from vw_by_rho import COLORS, GRID, INK, MARKERS, MUTED, ROOT, SPLITS, rho_axis

PARTS = {"prefix": "prefix (before the answer)", "answer": "answer tokens", "suffix": "suffix (punctuation + end token)"}
ROWS = {**PARTS, "full": "full response (sum of rows above)"}


def token_parts(span: np.ndarray, offsets: np.ndarray) -> np.ndarray:
    """Per-token label: 0 prefix, 1 answer, 2 suffix."""
    part = np.zeros(len(span), dtype=int)
    for a, b in zip(offsets[:-1], offsets[1:]):
        idx = np.flatnonzero(span[a:b])
        if len(idx):
            part[a + idx[0]: a + idx[-1] + 1] = 1
            part[a + idx[-1] + 1: b] = 2
    return part


def vw(seq: np.ndarray):
    CW, CN, IW, IN = seq.T
    return float((0.5 * (CW + IW) - 0.5 * (CN + IN)).mean()), float((0.5 * (CW - IW) - 0.5 * (CN - IN)).mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen3-4b")
    ap.add_argument("--beta", default="0.1")
    ap.add_argument("--lr", default="5e-06")
    args = ap.parse_args()
    pat = re.compile(rf"^rho([0-9.]+)_lr{re.escape(args.lr)}_beta{re.escape(args.beta)}_seed(\d+)$")
    runs = {}
    for d in sorted((ROOT / "results" / args.model / "runs").iterdir()):
        m = pat.match(d.name)
        if m and (d / "token_r.npz").exists() and (d / "summary.json").exists():
            runs.setdefault(float(m.group(1)), []).append(d)
    if not runs:
        raise SystemExit("no finished runs with token_r.npz found")
    rhos = sorted(runs)

    # res[sp][part][key][rho] = (mean over seeds, SD over seeds)
    res = {sp: {p: {"v": {}, "w": {}} for p in ROWS} for sp in SPLITS}
    step_used = {}
    for rho in rhos:
        per_seed = []
        for d in runs[rho]:
            t = np.load(d / "token_r.npz")
            best = json.load(open(d / "summary.json"))["best_val_u_step"]
            step_used[d.name] = best
            out = {}
            for sp in SPLITS:
                key = f"{sp}_step{best}"
                off = t[f"{sp}_offsets"]
                part = token_parts(t[f"{sp}_span"], off)
                r = t[key].astype(np.float64)
                for i, p in enumerate(PARTS):
                    seq = np.add.reduceat(np.where(part == i, r, 0.0), off[:-1]).reshape(-1, 4)
                    out[(sp, p)] = vw(seq)
                out[(sp, "full")] = vw(np.add.reduceat(r, off[:-1]).reshape(-1, 4))
            per_seed.append(out)
        for sp in SPLITS:
            for p in ROWS:
                for j, k in enumerate(("v", "w")):
                    x = np.array([s[(sp, p)][j] for s in per_seed])
                    res[sp][p][k][rho] = (float(x.mean()), float(x.std(ddof=1)) if len(x) > 1 else 0.0)

    fig, axes = plt.subplots(len(ROWS), 2, figsize=(12, 14.5), facecolor="white")
    for row, (p, plabel) in enumerate(ROWS.items()):
        for col, (k, klabel) in enumerate((("v", "v  (tone: warm − neutral)"), ("w", "w  (tone × fact interaction)"))):
            ax = axes[row, col]
            for sp, name in SPLITS.items():
                y = [res[sp][p][k][r][0] for r in rhos]
                e = [res[sp][p][k][r][1] for r in rhos]
                ax.errorbar(rhos, y, yerr=e, color=COLORS[sp], marker=MARKERS[sp], markersize=5.5, linewidth=2,
                            capsize=3, elinewidth=1.2, label=name, zorder=3)
            ax.axhline(0, color=MUTED, linewidth=1, zorder=1)
            if max(abs(res[sp][p][k][r][0]) for sp in SPLITS for r in rhos) < 0.5:
                # e.g. w on the prefix: CW/IW (and CN/IN) share it, so it is 0 up to float noise; don't zoom into noise
                ax.set_ylim(-1, 1)
                ax.text(0.5, 0.75, "≈ 0 by construction (same text in correct and incorrect)", transform=ax.transAxes,
                        ha="center", color=MUTED, fontsize=9)
            ax.set_title(f"{klabel} — {plabel}", color=INK, fontsize=11, loc="left")
            rho_axis(ax, rhos, label=row == len(ROWS) - 1)
            if col == 0:
                ax.set_ylabel("nats (change from the untrained model)", color=MUTED, fontsize=9)
            ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0)
            for s in ("top", "right"):
                ax.spines[s].set_visible(False)
            for s in ("left", "bottom"):
                ax.spines[s].set_color(MUTED)
            ax.tick_params(colors=MUTED)
    axes[0, 1].legend(frameon=False, fontsize=9, loc="best")
    seeds_txt = ", ".join(f"ρ {r:g}: {len(runs[r])}" for r in rhos)
    fig.suptitle("Where v and w live in the response, by ρ", x=0.01, ha="left", color=INK, fontsize=14)
    fig.text(0.01, 0.005,
             f"{args.model}, β = {args.beta}, LR {args.lr}; best-validation-u checkpoint of each run. "
             f"Each panel has its own y-axis.\nprefix + answer + suffix = full-response value. Seeds per ρ — {seeds_txt}. "
             f"Points = mean over seeds; bars = ±1 SD (only where ≥ 2 seeds).",
             color=MUTED, fontsize=8.5, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.03, 1, 0.975))
    out = ROOT / "results" / args.model / "figures"
    out.mkdir(parents=True, exist_ok=True)
    tag = f"beta{args.beta}"
    fig.savefig(out / f"position_vw_{tag}.png", dpi=200)
    plt.close(fig)
    json.dump({"step_used": step_used,
               "values": {sp: {p: {k: {f"{r:g}": {"mean": m, "sd": s} for r, (m, s) in d.items()}
                                   for k, d in kd.items()} for p, kd in pd.items()} for sp, pd in res.items()}},
              open(out / f"position_vw_{tag}.json", "w"), indent=1)
    for f in (f"position_vw_{tag}.png", f"position_vw_{tag}.json"):
        print(out.relative_to(ROOT) / f)


if __name__ == "__main__":
    main()
