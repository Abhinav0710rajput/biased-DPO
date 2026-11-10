"""Merge judge-kept quartets from a run and its repair rounds into one set, and report the
combined yield and length balance (plan §5.6 guard).

A row counts once: if it was kept in the original run it stays as it was; otherwise the
kept version from the first repair round that kept it is used.

Usage:
  python src/data/merge.py data/interim/rewrite_pilot/<run> [--judge-dir judge_gpt-5.4-mini_j3_x2]
"""

import argparse
import json
from collections import Counter
from pathlib import Path

from length_balance import gap_stats
from rewrite_pilot import balance_guard, phrase_shares, warmth_score


def kept_from(run: Path, judge_dir: str) -> dict:
    path = run / judge_dir / "kept_quartets.jsonl"
    if not path.exists():
        return {}
    return {json.loads(l)["qid"]: json.loads(l) for l in path.open(encoding="utf-8")}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("run_dir", type=Path)
    p.add_argument("--judge-dir", default="judge_gpt-5.4-mini_j3_x2")
    p.add_argument("--repair-dirs", nargs="*", type=Path, default=None,
                   help="explicit repair folders in order (default: <run>_repair1, _repair2, ...)")
    p.add_argument("--out-dir", type=Path, default=None, help="default: <run>_merged")
    args = p.parse_args()

    rows = sum(1 for _ in (args.run_dir / "calls.jsonl").open(encoding="utf-8"))
    merged = {q: {**v, "kept_in": "original"} for q, v in kept_from(args.run_dir, args.judge_dir).items()}
    per_round = {"original": len(merged)}
    repair_dirs = args.repair_dirs
    if repair_dirs is None:
        repair_dirs, k = [], 1
        while (rd := args.run_dir.parent / f"{args.run_dir.name}_repair{k}").exists():
            repair_dirs.append(rd)
            k += 1
    for rd in repair_dirs:
        name = rd.name.replace(args.run_dir.name + "_", "")
        new = {q: v for q, v in kept_from(rd, args.judge_dir).items() if q not in merged}
        merged.update({q: {**v, "kept_in": name} for q, v in new.items()})
        per_round[name] = len(new)

    def gap(v):
        return len(v["responses"]["CW"]["text"].split()) - len(v["responses"]["CN"]["text"].split())

    # Final balance trim (plan §5.6): rows are balanced when generated, but judge filtering and
    # repair rounds can tip a small set past the guard. Drop the fewest rows from the over-
    # represented side (largest |gap| first, then by qid for determinism) until the guard passes.
    trimmed = []
    while merged and not balance_guard(gap_stats([gap(v) for v in merged.values()]))["ok"]:
        st = gap_stats([gap(v) for v in merged.values()])
        sign = 1 if (st["mean"] > 0 or st["warm_longer"] > st["warm_shorter"]) else -1
        q = max((q for q, v in merged.items() if gap(v) * sign > 0), key=lambda q: (abs(gap(merged[q])), q))
        trimmed.append(q)
        del merged[q]

    gaps = [gap(v) for v in merged.values()]
    stats = gap_stats(gaps)
    summary = {"rows": rows, "kept_total": len(merged), "yield": round(len(merged) / max(1, rows), 3),
               "trimmed_for_balance": trimmed,
               "kept_per_round": per_round,
               "wrong_source": dict(Counter(v.get("wrong_source") for v in merged.values())),
               "length_balance": stats, "length_balance_guard": balance_guard(stats),
               "warmth_score": warmth_score(list(merged.values())),
               "phrase_shares": {side: phrase_shares([v["responses"][side]["text"] for v in merged.values()])
                                 for side in ("CW", "CN")}}
    out = args.out_dir or args.run_dir.parent / f"{args.run_dir.name}_merged"
    out.mkdir(exist_ok=True)
    with (out / "kept_quartets.jsonl").open("w", encoding="utf-8") as f:
        for q in sorted(merged):
            f.write(json.dumps(merged[q], ensure_ascii=False) + "\n")
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    if not summary["length_balance_guard"]["ok"]:
        print("\n!!! LENGTH BALANCE GUARD FAILED on the merged set")
    print(f"\nWrote {out}/kept_quartets.jsonl")


if __name__ == "__main__":
    main()
