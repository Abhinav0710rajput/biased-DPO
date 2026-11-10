"""Option C test, at zero generation cost: re-select neutral versions from an EXISTING rewrite
run's outputs under different selection rules, rebalance lengths, and write a new run folder
that the judge can score.

Rules tested (option C):
  - per-row length tolerance of +-N words (V8; plan §5.4 uses 2)
  - prefer neutral options ending within K words of the answer (soft V20: never a rejection)
  - dataset-level balancing of warm-minus-neutral length (length_balance.py)

Only each row's FINAL model output is reused (the one checked last in the original run).

Usage:
  python src/data/reselect.py data/interim/rewrite_pilot/<run> --length-tolerance 4 --prefer-tail 2
"""

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path

from rewrite_pilot import apply_length_balance
from validate import check_candidates, passes, swap


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("run_dir", type=Path)
    p.add_argument("--length-tolerance", type=int, default=4)
    p.add_argument("--prefer-tail", type=int, default=2)
    args = p.parse_args()

    src = [json.loads(line) for line in (args.run_dir / "calls.jsonl").open(encoding="utf-8")]
    records = []
    for r in src:
        last = r["attempts"][-1]
        rec = {k: v for k, v in r.items() if k not in ("responses", "neutral_candidates", "warm_tagged",
                                                        "balanced_candidate", "wrong_answer")}
        rec["passed"] = False
        if last.get("raw"):
            res = check_candidates(last["raw"], r["question"], r["correct_answer"], r["wrong_source_text"],
                                   length_tolerance=args.length_tolerance, prefer_tail=args.prefer_tail)
            rec["attempts"] = r["attempts"][:-1] + [{**last, "checks": res["checks"],
                                                    "candidate": res.get("candidate"),
                                                    "prefer_tail": res.get("prefer_tail")}]
            if passes(res["checks"]):
                parsed = res["parsed"]
                rec.update(passed=True, wrong_answer=res["wrong_phrase"], wrong_source=res["wrong_source"],
                           warm_tagged=parsed["warm"], neutral_candidates=res.get("passing_candidates") or [],
                           responses=swap(parsed["neutral"], parsed["warm"], r["correct_answer"],
                                          res["wrong_phrase"]))
        records.append(rec)

    balance = apply_length_balance(records)
    passed = [r for r in records if r["passed"]]

    def words(t):
        return len(t.split())

    gaps = [words(r["responses"]["CW"]["text"]) - words(r["responses"]["CN"]["text"]) for r in passed]
    tails = []
    for r in passed:
        cn = r["responses"]["CN"]
        tails.append(len(cn["text"][cn["ans_span"][1]:].strip(" .,;:!?\"'").split()))

    out_dir = args.run_dir.parent / f"{args.run_dir.name}_reselect_tol{args.length_tolerance}_tail{args.prefer_tail}"
    out_dir.mkdir(exist_ok=True)
    with (out_dir / "calls.jsonl").open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (out_dir / "quartets.jsonl").open("w", encoding="utf-8") as f:
        for r in passed:
            q = {k: r.get(k) for k in ("qid", "passage", "question", "correct_answer", "wrong_answer", "wrong_source",
                                       "wrong_source_text", "is_yesno", "style", "neutral_frame", "responses")}
            q["source"] = "halueval_qa"
            q["rewriter"] = {"prompt_version": r.get("prompt_version"), "reselected_from": args.run_dir.name,
                             "length_tolerance": args.length_tolerance, "prefer_tail": args.prefer_tail}
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    summary = {
        "source_run": str(args.run_dir), "length_tolerance": args.length_tolerance, "prefer_tail": args.prefer_tail,
        "rows": len(records), "passed": len(passed), "pass_rate": round(len(passed) / max(1, len(records)), 3),
        "warm_minus_neutral_words": {"mean": round(statistics.mean(gaps), 2) if gaps else None,
                                     "mean_abs": round(statistics.mean(abs(g) for g in gaps), 2) if gaps else None,
                                     "distribution": dict(sorted(Counter(gaps).items()))},
        "cn_words_after_answer": dict(sorted(Counter(min(t, 3) for t in tails).items())),  # 3 = "3 or more"
        "length_balance": balance,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    print(f"\nWrote {out_dir}/  (judge it with: bash scripts/run_judge.sh {out_dir})")


if __name__ == "__main__":
    main()
