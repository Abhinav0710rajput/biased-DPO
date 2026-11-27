"""Fact gaps in each tone: CW − IW (warm) and CN − IN (neutral), from results/. Their difference is 2w.

  python src/analysis/fact_gaps.py --model qwen3-4b
  python src/analysis/fact_gaps.py --model qwen3-4b --beta 0.05

Writes results/<model>/figures/
  fact_gaps_by_rho_beta<β>.png      by ρ at each run's best-validation-u checkpoint, one panel per evaluation set
  fact_gaps_curves_beta<β>.png      over training on validation, one panel per ρ
  fact_gaps_beta<β>.json            the numbers behind both
Gaps are in r (change from the untrained model, nats). Points = mean over seeds; bars / bands = ± 1 SD (≥ 2 seeds).
"""

import argparse
import json
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from vw_by_rho import GRID, INK, MUTED, ROOT, SPLITS

TONES = {"warm": ("CW − IW  (warm)", "#eb6834", "o"), "neutral": ("CN − IN  (neutral)", "#2a78d6", "s")}


def gaps(r):
    CW, CN, IW, IN = r.astype(float).T
    return {"warm": float((CW - IW).mean()), "neutral": float((CN - IN).mean())}


def load(model, beta, lr):
    pat = re.compile(rf"^rho([0-9.]+)_lr{re.escape(lr)}_beta{re.escape(beta)}_seed(\d+)$")
    runs = {}
    for d in sorted((ROOT / "results" / model / "runs").iterdir()):
        m = pat.match(d.name)
        if m and (d / "summary.json").exists():
            runs.setdefault(float(m.group(1)), []).append(d)
    return runs


def mean_sd(xs):
    x = np.array(xs, dtype=float)
    return float(x.mean()), (float(x.std(ddof=1)) if len(x) > 1 else 0.0)


def style(ax, title, xlabel):
    ax.set_title(title, color=INK, fontsize=11, loc="left")
    ax.set_xlabel(xlabel, color=INK)
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=MUTED)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen3-4b")
    ap.add_argument("--beta", default="0.1")
    ap.add_argument("--lr", default="5e-06")
    args = ap.parse_args()
    runs = load(args.model, args.beta, args.lr)
    if not runs:
        raise SystemExit("no finished runs found")
    rhos = sorted(runs)
    out = ROOT / "results" / args.model / "figures"
    out.mkdir(parents=True, exist_ok=True)
    tag = f"beta{args.beta}"
    seeds_txt = ", ".join(f"ρ {r:g}: {len(runs[r])}" for r in rhos)
    dump = {"by_rho": {}, "curves": {}}

    # ---- by ρ, best-val-u checkpoint
    fig, axes = plt.subplots(1, len(SPLITS), figsize=(13, 4.3), facecolor="white", sharey=True)
    for ax, (sp, name) in zip(axes, SPLITS.items()):
        per = {}
        for rho in rhos:
            vals = []
            for d in runs[rho]:
                z = np.load(d / "quartet_scores.npz")
                best = json.load(open(d / "summary.json"))["best_val_u_step"]
                vals.append(gaps(z[f"{sp}_full"][list(z[f"{sp}_steps"]).index(best)]))
            per[f"{rho:g}"] = {t: mean_sd([v[t] for v in vals]) for t in TONES} | {"n_seeds": len(vals)}
        dump["by_rho"][sp] = per
        for t, (label, color, marker) in TONES.items():
            y = [per[f"{r:g}"][t][0] for r in rhos]
            e = [per[f"{r:g}"][t][1] for r in rhos]
            ax.errorbar(rhos, y, yerr=e, color=color, marker=marker, markersize=6, linewidth=2, capsize=3,
                        elinewidth=1.2, label=label, zorder=3)
        ax.set_xticks(rhos)
        ax.set_xticklabels([f"{r:g}" for r in rhos])
        style(ax, name, "ρ  (share of crossed pairs)")
    axes[0].set_ylabel("fact gap, nats (change from the untrained model)", color=MUTED, fontsize=9)
    axes[0].legend(frameon=False, fontsize=9, loc="lower right")
    fig.suptitle("Fact gap in each tone by ρ  (warm − neutral gap = 2w)", x=0.01, ha="left", color=INK, fontsize=13)
    fig.text(0.01, 0.005, f"{args.model}, β = {args.beta}, LR {args.lr}; best-validation-u checkpoint of each run.\n"
             f"Seeds per ρ — {seeds_txt}. Points = mean over seeds; bars = ±1 SD (only where ≥ 2 seeds).",
             color=MUTED, fontsize=8.5, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.08, 1, 0.94))
    fig.savefig(out / f"fact_gaps_by_rho_{tag}.png", dpi=200)
    plt.close(fig)

    # ---- over training, validation
    fig, axes = plt.subplots(1, len(rhos), figsize=(3.1 * len(rhos), 4.0), facecolor="white", sharey=True)
    for ax, rho in zip(np.atleast_1d(axes), rhos):
        zs = [np.load(d / "quartet_scores.npz") for d in runs[rho]]
        steps = sorted(set.intersection(*(set(int(s) for s in z["val_steps"]) for z in zs)))
        curve = {t: [] for t in TONES}
        for s in steps:
            vals = [gaps(z["val_full"][list(z["val_steps"]).index(s)]) for z in zs]
            for t in TONES:
                curve[t].append(mean_sd([v[t] for v in vals]))
        dump["curves"][f"{rho:g}"] = {"steps": steps, **{t: curve[t] for t in TONES}, "n_seeds": len(zs)}
        for t, (label, color, _) in TONES.items():
            m = np.array([c[0] for c in curve[t]])
            sd = np.array([c[1] for c in curve[t]])
            ax.plot(steps, m, color=color, linewidth=2, label=label, zorder=3)
            if len(zs) > 1:
                ax.fill_between(steps, m - sd, m + sd, color=color, alpha=0.15, linewidth=0, zorder=2)
        style(ax, f"ρ = {rho:g}  ({len(zs)} seed{'s' if len(zs) > 1 else ''})", "training step")
    np.atleast_1d(axes)[0].set_ylabel("fact gap on validation, nats", color=MUTED, fontsize=9)
    np.atleast_1d(axes)[0].legend(frameon=False, fontsize=9, loc="lower right")
    fig.suptitle("Fact gap in each tone over training  (HaluEval validation)", x=0.01, ha="left", color=INK,
                 fontsize=13)
    fig.text(0.01, 0.005, f"{args.model}, β = {args.beta}, LR {args.lr}. Lines = mean over seeds; bands = ±1 SD "
             f"(only where ≥ 2 seeds). The vertical distance between the lines is 2|w|.",
             color=MUTED, fontsize=8.5, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.05, 1, 0.93))
    fig.savefig(out / f"fact_gaps_curves_{tag}.png", dpi=200)
    plt.close(fig)

    json.dump(dump, open(out / f"fact_gaps_{tag}.json", "w"), indent=1)
    for f in (f"fact_gaps_by_rho_{tag}.png", f"fact_gaps_curves_{tag}.png", f"fact_gaps_{tag}.json"):
        print(out.relative_to(ROOT) / f)


if __name__ == "__main__":
    main()
