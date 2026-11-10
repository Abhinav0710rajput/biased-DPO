"""Independent audit of the FINAL dataset (replaces the human audit of project_plan.md §5.7,
which is not feasible for this project; decision 2026-11-10).

A stronger model than the generator and the judge (default gpt-5.4) reviews a random sample of
the merged, kept quartets with the same rubric as the judge (default j5) in a single pass, and
reports the estimated error rate per criterion with 95% Wilson confidence intervals. Nothing is
filtered: the audit measures the quality of what the pipeline produced, for the write-up.

Usage (normally via scripts/run_audit.sh):
  python src/data/audit.py data/interim/rewrite_pilot/<run>_merged_tl --n 200
"""

import argparse
import json
import math
import random
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from types import SimpleNamespace

from openai import OpenAI
from tqdm import tqdm

from judge import JUDGES, build_messages, judge_pass


def wilson(k: int, n: int, z: float = 1.96) -> list[float]:
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, c - h), 3), round(min(1.0, c + h), 3)]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("merged_dir", type=Path, help="folder with the final kept_quartets.jsonl")
    p.add_argument("--n", type=int, default=200, help="sample size (all quartets if fewer)")
    p.add_argument("--model", default="gpt-5.4")
    p.add_argument("--reasoning-effort", default="low")
    p.add_argument("--judge-version", default="j5", choices=sorted(JUDGES))
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--workers", type=int, default=8)
    args = p.parse_args()

    quartets = [json.loads(l) for l in (args.merged_dir / "kept_quartets.jsonl").open(encoding="utf-8")]
    sample = random.Random(args.seed).sample(quartets, min(args.n, len(quartets)))
    cfg = SimpleNamespace(model=args.model, reasoning_effort=args.reasoning_effort, judge_version=args.judge_version)
    client = OpenAI(max_retries=5)

    def one(q):
        calls = []
        return {"qid": q["qid"], "wrong_source": q.get("wrong_source"), "kept_in": q.get("kept_in"),
                "verdict": judge_pass(build_messages(q, args.judge_version), client, cfg, calls), "calls": calls}

    results = []
    with ThreadPoolExecutor(args.workers) as pool:
        for fut in tqdm(as_completed([pool.submit(one, q) for q in sample]), total=len(sample), desc=f"audit {args.model}"):
            results.append(fut.result())
    results.sort(key=lambda r: r["qid"])

    judged = [r for r in results if r["verdict"] is not None]
    n = len(judged)
    crit = JUDGES[args.judge_version]["criteria"]
    any_fail = sum(any(not v["pass"] for v in r["verdict"].values()) for r in judged)
    per = {c: sum(not r["verdict"][c]["pass"] for r in judged) for c in crit}
    tok = Counter()
    for r in results:
        for c in r["calls"]:
            tok.update(c.get("usage", {}))
    summary = {
        "merged_dir": str(args.merged_dir), "auditor": args.model, "reasoning_effort": args.reasoning_effort,
        "rubric": args.judge_version, "population": len(quartets), "sampled": len(sample), "audited": n,
        "unparseable": len(results) - n, "seed": args.seed,
        "error_rate_any": {"rate": round(any_fail / max(1, n), 3), "ci95": wilson(any_fail, n), "count": any_fail},
        "error_rate_by_criterion": {c: {"rate": round(k / max(1, n), 3), "ci95": wilson(k, n), "count": k}
                                    for c, k in per.items()},
        "error_rate_by_wrong_source": {s: round(sum(any(not v["pass"] for v in r["verdict"].values())
                                                    for r in judged if r["wrong_source"] == s)
                                                / max(1, sum(r["wrong_source"] == s for r in judged)), 3)
                                       for s in sorted({r["wrong_source"] for r in judged if r["wrong_source"]})},
        "tokens": dict(tok),
    }
    out = args.merged_dir / f"audit_{args.model}_{args.judge_version}"
    out.mkdir(exist_ok=True)
    with (out / "verdicts.jsonl").open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    by_qid = {q["qid"]: q for q in sample}
    lines = ["# Audit: flagged quartets\n"]
    for r in judged:
        bad = {c: v["reason"] for c, v in r["verdict"].items() if not v["pass"]}
        if bad:
            q = by_qid[r["qid"]]
            lines.append(f"## {r['qid']} ({q.get('kept_in')})\n")
            lines.append(f"**Q:** {q['question']}  \n**Correct:** {q['correct_answer']} · **Wrong:** {q['wrong_answer']}\n")
            lines += [f"- **{k}:** {q['responses'][k]['text']}" for k in ("CN", "CW", "IN", "IW")]
            lines += [f"- ❌ **{c}:** {why}" for c, why in bad.items()] + [""]
    (out / "flagged.md").write_text("\n".join(lines), encoding="utf-8")
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    print(f"\nOutputs in {out}/ : summary.json, flagged.md, verdicts.jsonl")


if __name__ == "__main__":
    main()
