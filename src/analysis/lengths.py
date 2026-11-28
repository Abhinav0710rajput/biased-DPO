"""Token length of each part of the response, warm vs neutral, in every split (train, val, test, SciQ).

  python src/analysis/lengths.py --model qwen3-4b

Parts are cut exactly as in training (src/train/data.py): response tokens = response text + end-of-turn token;
prefix = tokens before the answer span, answer = tokens overlapping `ans_span`, suffix = tokens after it
(punctuation + end-of-turn). Warm = mean over CW and IW, neutral = mean over CN and IN.
Writes results/<model>/figures/lengths_by_part.png and lengths_by_part.json.
"""

import argparse
import json
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from vw_by_rho import GRID, INK, MUTED, ROOT

sys.path.insert(0, str(ROOT / "src" / "train"))
from config import load_config          # noqa: E402
from data import ORDER, Encoder, load_quartets   # noqa: E402
from models import load_tokenizer        # noqa: E402

SPLITS = {"train": "train", "val": "val", "test": "test", "ood_sciq": "SciQ (OOD)"}
PARTS = {"prefix": "prefix (before the answer)", "answer": "answer tokens",
         "suffix": "suffix (punctuation + end token)", "total": "whole response"}
TONES = {"warm": ("warm (CW, IW)", "#eb6834", (0, 2)), "neutral": ("neutral (CN, IN)", "#2a78d6", (1, 3))}


def part_lengths(mask: list[bool]) -> tuple[int, int, int]:
    idx = np.flatnonzero(mask)
    n = len(mask)
    if not len(idx):
        return n, 0, 0
    return int(idx[0]), int(idx[-1] - idx[0] + 1), int(n - idx[-1] - 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen3-4b")
    args = ap.parse_args()
    cfg = load_config(args.model)
    enc = Encoder(load_tokenizer(cfg), cfg)

    stats = {}
    for sp in SPLITS:
        qs = load_quartets(ROOT / "data" / "quartets" / f"{sp}.jsonl")
        L = np.zeros((len(qs), 4, 3))                    # quartet, response (ORDER), part
        for i, q in enumerate(qs):
            for k, name in enumerate(ORDER):
                r = q["responses"][name]
                _, mask = enc.response(r["text"], r["ans_span"])
                L[i, k] = part_lengths(mask)
        stats[sp] = {"n_quartets": len(qs)}
        for t, (_, _, cols) in TONES.items():
            # per quartet, mean of the tone's two responses (CW and IW share their prefix, so they are not
            # independent; the CI uses quartets as the unit)
            x = L[:, cols, :].mean(1)
            parts = {"prefix": x[:, 0], "answer": x[:, 1], "suffix": x[:, 2], "total": x.sum(1)}
            sd_resp = {"prefix": L[:, cols, 0], "answer": L[:, cols, 1], "suffix": L[:, cols, 2],
                       "total": L[:, cols, :].sum(2)}
            stats[sp][t] = {p: {"mean": float(v.mean()), "sd_responses": float(sd_resp[p].std()),
                                "ci95": float(1.96 * v.std(ddof=1) / np.sqrt(len(v)))} for p, v in parts.items()}

    fig, axes = plt.subplots(1, len(PARTS), figsize=(15, 4.6), facecolor="white")
    xs = np.arange(len(SPLITS))
    width = 0.38
    top_hint = {p: max(stats[sp][t][p]["mean"] for sp in SPLITS for t in TONES) for p in PARTS}
    for ax, (p, plabel) in zip(axes, PARTS.items()):
        top = 0
        for j, (t, (tlabel, color, _)) in enumerate(TONES.items()):
            m = np.array([stats[sp][t][p]["mean"] for sp in SPLITS])
            s = np.array([stats[sp][t][p]["ci95"] for sp in SPLITS])
            pos = xs + (j - 0.5) * width
            ax.bar(pos, m, width - 0.04, color=color, label=tlabel, zorder=3)
            ax.errorbar(pos, m, yerr=s, fmt="none", ecolor=INK, elinewidth=1.2, capsize=3, zorder=4)
            for x, y, e in zip(pos, m, s):
                ax.text(x, y + e + 0.01 * top_hint[p], f"{y:.1f}", ha="center", va="bottom", fontsize=8, color=INK)
            top = max(top, (m + s).max())
        ax.set_ylim(0, top * 1.12)
        ax.set_xticks(xs)
        ax.set_xticklabels(SPLITS.values(), color=INK)
        ax.set_title(plabel, color=INK, fontsize=11, loc="left")
        ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0)
        for s_ in ("top", "right"):
            ax.spines[s_].set_visible(False)
        for s_ in ("left", "bottom"):
            ax.spines[s_].set_color(MUTED)
        ax.tick_params(colors=MUTED)
    axes[0].set_ylabel("tokens per response (mean)", color=MUTED, fontsize=9)
    fig.legend(*axes[0].get_legend_handles_labels(), frameon=False, fontsize=9.5, loc="upper right", ncol=2,
               bbox_to_anchor=(0.99, 0.995))
    n_txt = ", ".join(f"{name} {stats[sp]['n_quartets']:,}" for sp, name in SPLITS.items())
    fig.suptitle("Response length by part, warm vs neutral", x=0.01, ha="left", color=INK, fontsize=13)
    fig.text(0.01, 0.005, f"{args.model} tokenizer, cut exactly as in training. Bars = mean tokens per response; "
             f"whiskers = 95% CI of the mean (quartets as the unit). Each panel has its own y-axis.\nQuartets: {n_txt}. "
             f"Warm = CW and IW, neutral = CN and IN (the answer text is the same in both tones).",
             color=MUTED, fontsize=8.5, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.08, 1, 0.94))
    out = ROOT / "results" / args.model / "figures"
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / "lengths_by_part.png", dpi=200)
    plt.close(fig)
    json.dump(stats, open(out / "lengths_by_part.json", "w"), indent=1)
    for f in ("lengths_by_part.png", "lengths_by_part.json"):
        print(out.relative_to(ROOT) / f)
    for sp in SPLITS:
        print(sp, {t: {p: round(stats[sp][t][p]["mean"], 2) for p in PARTS} for t in TONES})


if __name__ == "__main__":
    main()
