"""Step 4 of the quartet pipeline: MERGE. See Docs/data_pipeline.md.

Combines the judge-kept quartets of a generation run and its repair round into one final set:
a row counts once (kept in the original run, else the repaired version if the judge kept it).
Then a final balance trim drops the fewest rows needed to pass the length-balance guard
(plan §5.6), and the summary reports yield, length balance, warmth score and phrase shares.

Usage (normally via scripts/run_pipeline.sh):
  python src/data/merge.py data/interim/rewrite_pilot/<run>
  -> data/interim/rewrite_pilot/<run>_merged_tl/{kept_quartets.jsonl, summary.json}
"""

import argparse
import json
from collections import Counter
from pathlib import Path

from generate import balance_guard, phrase_shares, warmth_score
from judge import JUDGE_DIR_NAME
from length_balance import gap_stats


def kept_from(run: Path) -> dict:
    path = run / JUDGE_DIR_NAME / "kept_quartets.jsonl"
    if not path.exists():
        return {}
    return {json.loads(l)["qid"]: json.loads(l) for l in path.open(encoding="utf-8")}


def gap(v: dict) -> int:
    return len(v["responses"]["CW"]["text"].split()) - len(v["responses"]["CN"]["text"].split())


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("run_dir", type=Path)
    p.add_argument("--out-dir", type=Path, default=None, help="default: <run>_merged_tl")
    args = p.parse_args()

    rows = sum(1 for _ in (args.run_dir / "calls.jsonl").open(encoding="utf-8"))
    merged = {q: {**v, "kept_in": "original"} for q, v in kept_from(args.run_dir).items()}
    per_round = {"original": len(merged)}
    repair = args.run_dir.parent / f"{args.run_dir.name}_repair1"
    if repair.exists():
        new = {q: v for q, v in kept_from(repair).items() if q not in merged}
        merged.update({q: {**v, "kept_in": "repair1"} for q, v in new.items()})
        per_round["repair1"] = len(new)

    # Final balance trim: drop the fewest rows from the over-represented side (largest |gap| first,
    # then by qid for determinism) until the length-balance guard passes.
    trimmed = []
    while merged and not balance_guard(gap_stats([gap(v) for v in merged.values()]))["ok"]:
        st = gap_stats([gap(v) for v in merged.values()])
        sign = 1 if (st["mean"] > 0 or st["warm_longer"] > st["warm_shorter"]) else -1
        q = max((q for q, v in merged.items() if gap(v) * sign > 0), key=lambda q: (abs(gap(merged[q])), q))
        trimmed.append(q)
        del merged[q]

    stats = gap_stats([gap(v) for v in merged.values()])
    summary = {"rows": rows, "kept_total": len(merged), "yield": round(len(merged) / max(1, rows), 3),
               "trimmed_for_balance": trimmed, "kept_per_round": per_round,
               "wrong_source": dict(Counter(v.get("wrong_source") for v in merged.values())),
               "length_balance": stats, "length_balance_guard": balance_guard(stats),
               "warmth_score": warmth_score(list(merged.values())),
               "phrase_shares": {s: phrase_shares([v["responses"][s]["text"] for v in merged.values()]) for s in ("CW", "CN")}}
    out = args.out_dir or args.run_dir.parent / f"{args.run_dir.name}_merged_tl"
    out.mkdir(exist_ok=True)
    with (out / "kept_quartets.jsonl").open("w", encoding="utf-8") as f:
        for q in sorted(merged):
            f.write(json.dumps(merged[q], ensure_ascii=False) + "\n")
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    if not summary["length_balance_guard"]["ok"]:
        print("\n!!! LENGTH BALANCE GUARD FAILED on the merged set")
    print(out)  # last line: the merged folder, for scripts


if __name__ == "__main__":
    main()
