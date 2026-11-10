"""Step 3 of the quartet pipeline: REPAIR (one round). See Docs/data_pipeline.md.

Targets in <run_dir>: rows that failed the code checks, and rows the judge rejected. Each target
continues ITS OWN conversation with the writer (system prompt, row, the writer's previous JSON
answer), followed by the feedback: the plain-language check failures, or every distinct failing
reason from both judge passes. The writer, rules, retries and length balancing are exactly as in
generation. Writes <run_dir>_repair1/ (judge it, then merge).

Usage (normally via scripts/run_pipeline.sh or scripts/run_repair.sh):
  python src/data/repair.py data/interim/rewrite_pilot/<run> --out-dir data/interim/rewrite_pilot/<run>_repair1
"""

import argparse
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from types import SimpleNamespace

from openai import OpenAI
from tqdm import tqdm

from generate import QUARTET_KEYS, apply_length_balance, process
from judge import JUDGE_DIR_NAME
from prompts import PROMPT_VERSION, build_messages
from validate import check_candidates, explain_failures

FEEDBACK_HEADER = "A careful reviewer checked the four responses built from your answer (CN = the neutral version that was used, CW = your warm version, IN and IW = the same two with the wrong answer swapped in) and found these problems:"
FEEDBACK_FOOTER = "Fix only these problems in the core, the neutral version and ALL warm options. Do not replace removed wording with new filler. If the neutral version gets shorter, make the warm options correspondingly shorter (a shorter warmth element, or referring back to the question's details briefly); never add words just to match length. If the wrong answer was flagged, replace it with a different one (write your own and set wrong_source to \"generated\" if the incorrect answer text has no usable one). Keep the answer, the warmth style and the neutral frame. Return the full JSON object again."


def judge_feedback(judgements: list, used_cn: str) -> str:
    """Every distinct failing reason from every judge pass, plus the neutral version that was used."""
    seen, lines = set(), []
    for v in judgements:
        for c, x in (v or {}).items():
            if not x["pass"] and (c, x["reason"]) not in seen:
                seen.add((c, x["reason"]))
                lines.append(f"- {c}: {x['reason']}")
    return "\n".join([FEEDBACK_HEADER, *lines, f'The neutral version that was used: "{used_cn}"', FEEDBACK_FOOTER])


ROW_KEYS = ("qid", "passage", "question", "correct_answer", "right_answer_raw", "wrong_source_text", "is_yesno",
            "style", "neutral_frame")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("run_dir", type=Path)
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--model", default=None, help="default: the run's own writer model")
    p.add_argument("--reasoning-effort", default=None, help="default: the run's own setting")
    p.add_argument("--max-retries", type=int, default=2)
    p.add_argument("--workers", type=int, default=8)
    args = p.parse_args()

    run_summary = json.loads((args.run_dir / "summary.json").read_text())
    gen = SimpleNamespace(model=args.model or run_summary["model"],
                          reasoning_effort=args.reasoning_effort or run_summary["reasoning_effort"],
                          max_retries=args.max_retries)
    calls = [json.loads(l) for l in (args.run_dir / "calls.jsonl").open(encoding="utf-8")]
    quartets = {json.loads(l)["qid"]: json.loads(l) for l in (args.run_dir / "quartets.jsonl").open(encoding="utf-8")}
    verdicts = {json.loads(l)["qid"]: json.loads(l)
                for l in (args.run_dir / JUDGE_DIR_NAME / "verdicts.jsonl").open(encoding="utf-8")}

    targets = []  # (row, conversation, reason)
    for r in calls:
        last = r["attempts"][-1]
        if not last.get("raw"):
            continue  # API error / empty output: nothing to give feedback on
        row = {k: r.get(k) for k in ROW_KEYS}
        conv = build_messages(row) + [{"role": "assistant", "content": last["raw"]}]
        if not r["passed"]:
            res = check_candidates(last["raw"], r["question"], r["correct_answer"], r["wrong_source_text"])
            fb = "Your answer has these problems:\n" + explain_failures(res) + "\n" + FEEDBACK_FOOTER
            targets.append((row, conv + [{"role": "user", "content": fb}], "failed_checks"))
        elif r["qid"] in verdicts and not verdicts[r["qid"]]["kept"] and verdicts[r["qid"]]["verdict"]:
            fb = judge_feedback(verdicts[r["qid"]]["verdicts"], quartets[r["qid"]]["responses"]["CN"]["text"])
            targets.append((row, conv + [{"role": "user", "content": fb}], "judge_rejected"))

    client = OpenAI(max_retries=5)
    records = []
    with ThreadPoolExecutor(args.workers) as pool:
        futures = {pool.submit(process, row, client, gen, conv): why for row, conv, why in targets}
        for fut in tqdm(as_completed(futures), total=len(futures), desc="repair"):
            rec = fut.result()
            rec["repair_reason"] = futures[fut]
            records.append(rec)
    records.sort(key=lambda r: r["qid"])
    balance_stats = apply_length_balance(records)

    args.out_dir.mkdir(parents=True)
    with (args.out_dir / "calls.jsonl").open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (args.out_dir / "quartets.jsonl").open("w", encoding="utf-8") as f:
        for r in records:
            if r["passed"]:
                q = {k: r.get(k) for k in QUARTET_KEYS}
                q.update(source="halueval_qa", rewriter={"model": gen.model, "prompt_version": PROMPT_VERSION,
                                                         "repair_of": args.run_dir.name,
                                                         "repair_reason": r["repair_reason"]})
                f.write(json.dumps(q, ensure_ascii=False) + "\n")
    tok = Counter()
    for r in records:
        for a in r["attempts"]:
            tok.update(a.get("usage", {}))
    summary = {
        "model": gen.model, "reasoning_effort": gen.reasoning_effort, "prompt_version": PROMPT_VERSION,
        "repair_of": str(args.run_dir), "targets": dict(Counter(why for _, _, why in targets)),
        "passed_checks": sum(r["passed"] for r in records),
        "passed_by_reason": {w: f"{sum(r['passed'] for r in records if r['repair_reason'] == w)}/"
                                f"{sum(r['repair_reason'] == w for r in records)}"
                             for w in ("failed_checks", "judge_rejected")},
        "api_calls": sum(len(r["attempts"]) for r in records), "tokens": dict(tok), "length_balance": balance_stats,
        "final_pass_rate": round(sum(r["passed"] for r in records) / max(1, len(records)), 3),
    }
    (args.out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
