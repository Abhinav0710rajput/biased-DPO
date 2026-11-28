"""v and w (signed) and |v|, |w| against ρ, at each run's best-validation-u checkpoint, from results/.

  python src/analysis/vw_by_rho.py --model qwen3-4b            # β = 0.1 runs, all seeds found
  python src/analysis/vw_by_rho.py --model qwen3-4b --beta 0.05
  python src/analysis/vw_by_rho.py --model qwen3-4b --score span   # answer tokens only (plan §10.1 secondary)

Writes results/<model>/figures/vw_signed_beta<β>.png, vw_abs_beta<β>.png and vw_by_rho_beta<β>.json
(with --score span: vw_signed_span_beta<β>.png, vw_abs_span_beta<β>.png, vw_by_rho_span_beta<β>.json).
One line per evaluation set; points are the mean over seeds, error bars ± 1 SD (only where ≥ 2 seeds).
"""

import argparse
import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SPLITS = {"val": "HaluEval val", "test": "HaluEval test", "ood_sciq": "SciQ (out of domain)"}
COLORS = {"val": "#2a78d6", "test": "#eb6834", "ood_sciq": "#1baf7a"}     # categorical slots 1–3, fixed order
MARKERS = {"val": "o", "test": "s", "ood_sciq": "^"}
INK, MUTED, GRID = "#1f1f1e", "#6b6b66", "#e6e5e0"


def rho_axis(ax, rhos, label=True):
    """ρ on a symmetric-log axis (linear near 0), so 0, 0.02, 0.05 and 0.125 don't pile up at the left edge."""
    ax.set_xscale("symlog", linthresh=0.02, linscale=0.35)
    ax.set_xlim(-0.004, max(rhos) * 1.15)
    ax.set_xticks(rhos)
    ax.set_xticklabels([f"{r:g}" for r in rhos])
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    if label:
        ax.set_xlabel("ρ  (share of crossed pairs; log scale above 0.02)", color=INK)


def contrasts(r):
    CW, CN, IW, IN = r.T
    return 0.5 * (CW + IW) - 0.5 * (CN + IN), 0.5 * (CW - IW) - 0.5 * (CN - IN)


def collect(model: str, beta: str, lr: str | None, score: str = "full"):
    base = ROOT / "results" / model / "runs"
    pat = re.compile(rf"^rho([0-9.]+)_lr([0-9.e+-]+)_beta{re.escape(beta)}_seed(\d+)$")
    rows = {}
    for d in sorted(base.iterdir()):
        m = pat.match(d.name)
        if not m or (lr and m.group(2) != lr) or not (d / "summary.json").exists():
            continue
        rho = float(m.group(1))
        z = np.load(d / "quartet_scores.npz")
        best = json.load(open(d / "summary.json"))["best_val_u_step"]
        for sp in SPLITS:
            steps = list(z[f"{sp}_steps"])
            v, w = contrasts(z[f"{sp}_{score}"][steps.index(best)].astype(float))
            rows.setdefault((sp, rho), []).append(
                {"seed": int(m.group(3)), "v": v.mean(), "w": w.mean(), "abs_v": np.abs(v).mean(), "abs_w": np.abs(w).mean()})
    return rows


def summarise(rows):
    out = {}
    for (sp, rho), runs in rows.items():
        d = {"n_seeds": len(runs), "seeds": [r["seed"] for r in runs]}
        for k in ("v", "w", "abs_v", "abs_w"):
            x = np.array([r[k] for r in runs])
            d[k] = float(x.mean())
            d[k + "_sd"] = float(x.std(ddof=1)) if len(x) > 1 else None
        out.setdefault(sp, {})[rho] = d
    return out


def panel(ax, summ, key, label, zero_line):
    for sp, name in SPLITS.items():
        if sp not in summ:
            continue
        rhos = sorted(summ[sp])
        y = [summ[sp][r][key] for r in rhos]
        err = [summ[sp][r][key + "_sd"] or 0.0 for r in rhos]
        ax.errorbar(rhos, y, yerr=err, color=COLORS[sp], marker=MARKERS[sp], markersize=6, linewidth=2,
                    capsize=3, elinewidth=1.2, label=name, zorder=3)
    if zero_line:
        ax.axhline(0, color=MUTED, linewidth=1, zorder=1)
    else:                                   # magnitudes: start at 0 so small wobbles don't look like trends
        ax.set_ylim(bottom=0)
    ax.set_title(label, color=INK, fontsize=12, loc="left")
    ax.set_ylabel("nats (change from the untrained model)", color=MUTED, fontsize=9)
    rho_axis(ax, sorted({r for sp in summ for r in summ[sp]}))
    ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=MUTED)


def figure(summ, keys, title, path, zero_line, note):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), facecolor="white")
    for ax, (key, label) in zip(axes, keys):
        panel(ax, summ, key, label, zero_line)
    axes[0].legend(frameon=False, fontsize=9, loc="best")
    fig.suptitle(title, x=0.01, ha="left", color=INK, fontsize=13)
    fig.text(0.01, 0.005, note, color=MUTED, fontsize=8.5, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.07, 1, 0.95))
    fig.savefig(path, dpi=200)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen3-4b")
    ap.add_argument("--beta", default="0.1")
    ap.add_argument("--lr", default="5e-06", help="only runs with this LR in the name (the frozen one)")
    ap.add_argument("--score", choices=("full", "span"), default="full",
                    help="full response (primary) or answer tokens only (secondary)")
    args = ap.parse_args()
    summ = summarise(collect(args.model, args.beta, args.lr, args.score))
    if not summ:
        raise SystemExit("no finished runs found")
    out = ROOT / "results" / args.model / "figures"
    out.mkdir(parents=True, exist_ok=True)
    seeds = {f"{r:g}": summ["val"][r]["n_seeds"] for r in sorted(summ["val"])}
    seeds_txt = ", ".join(f"ρ {r}: {n}" for r, n in seeds.items())
    what = "answer tokens only" if args.score == "span" else "full response"
    note = (f"{args.model}, β = {args.beta}, LR {args.lr}; {what}; best-validation-u checkpoint of each run.\n"
            f"Seeds per ρ — {seeds_txt}. Points = mean over seeds; bars = ±1 SD (only where ≥ 2 seeds).")
    tag = f"span_beta{args.beta}" if args.score == "span" else f"beta{args.beta}"
    sfx = "  (answer tokens only)" if args.score == "span" else ""
    figure(summ, [("v", "v  (tone: warm − neutral)"), ("w", "w  (tone × fact interaction)")],
           "Signed v and w by ρ" + sfx, out / f"vw_signed_{tag}.png", True, note)
    figure(summ, [("abs_v", "|v|  (mean over quartets)"), ("abs_w", "|w|  (mean over quartets)")],
           "|v| and |w| by ρ" + sfx, out / f"vw_abs_{tag}.png", False, note)
    json.dump({sp: {f"{r:g}": d for r, d in by.items()} for sp, by in summ.items()},
              open(out / f"vw_by_rho_{tag}.json", "w"), indent=1)
    for f in (f"vw_signed_{tag}.png", f"vw_abs_{tag}.png", f"vw_by_rho_{tag}.json"):
        print(out.relative_to(ROOT) / f)


if __name__ == "__main__":
    main()
