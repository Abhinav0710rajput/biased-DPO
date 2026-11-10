"""Repair round: regenerate the rows a run lost, with feedback.

  generate -> judge -> [repair: feedback -> regenerate failed/rejected rows] -> judge -> merge

Targets in <run_dir>:
  - rows that failed the code checks (feedback = the plain-language check failures), and
  - rows the judge rejected (feedback = the judge's reasons).
Each target continues ITS OWN conversation: the original prompt, the model's previous answer,
then the feedback, so the rewriter (prompt version, model, rules) is unchanged. The usual code
checks and validation retries apply, and lengths are balanced within the repaired rows.

Writes <run_dir>_repair<k>/ with calls.jsonl, quartets.jsonl, summary.json; judge that folder,
then run merge.py to combine kept quartets from the original run and the repair rounds.

Usage (normally via scripts/run_repair_round.sh):
  python src/data/repair.py data/interim/rewrite_pilot/<run> --judge-dir judge_gpt-5.4-mini_j3_x2
"""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from types import SimpleNamespace

from openai import OpenAI
from tqdm import tqdm

from prompts import BALANCED_LENGTH_VERSIONS, build_messages
from rewrite_pilot import apply_length_balance, check_settings, process
from validate import check_candidates, explain_failures

FEEDBACK_HEADER = (
    "A careful reviewer checked the four responses built from your answer (CN = the neutral version "
    "that was used, CW = your warm version, IN and IW = the same two with the wrong answer swapped in) "
    "and found these problems:")
# f1: "keep ... the lengths" -> the writer replaced removed filler with NEW filler to stay within
#     +-2 words ("among the two" -> "between the two"); 10/43 repaired rows kept.
FEEDBACK_FOOTER = (
    "Fix only these problems. Apply the fix to the core, the warm version and ALL neutral options; keep "
    "everything else the same, including the warmth style, the neutral frame and the lengths. "
    "Return the full JSON object again.")
# f2: the length fix goes to the side with slack: shorten the warm version's opening/closing
#     instead of padding the neutral version. Also quotes the reasons from every judge pass.
FEEDBACK_FOOTER_F2 = (
    "Fix only these problems. Remove or rephrase the flagged wording in the core and in ALL neutral "
    "options (and in the warm version if it was flagged). Do not replace removed wording with new filler. "
    "If a neutral version then becomes too short to match the warm version, shorten the warm version's "
    "opening or closing instead (it must stay clearly warm); never add words to a neutral version just to "
    "match length. Keep the answer, the warmth style and the neutral frame. Return the full JSON object again.")
# f3: for rewriter v3.0 (neutral first, warm fitted to it): length is fixed on the warm side.
FEEDBACK_FOOTER_F3 = (
    "Fix only these problems in the core, the neutral version and ALL warm options. Do not replace removed "
    "wording with new filler. If the neutral version gets shorter, make the warm options correspondingly "
    "shorter (a shorter warmth element, or referring back to the question's details briefly); never add "
    "words just to match length. If the wrong answer was flagged, replace it with a different one (write "
    "your own and set wrong_source to \"generated\" if the incorrect answer text has no usable one). Keep the "
    "answer, the warmth style and the neutral frame. Return the full JSON object again.")
FEEDBACKS = {"f1": FEEDBACK_FOOTER, "f2": FEEDBACK_FOOTER_F2, "f3": FEEDBACK_FOOTER_F3}


def judge_feedback(verdict: dict, used_cn: str, footer: str = FEEDBACK_FOOTER,
                   all_verdicts: list | None = None) -> str:
    if all_verdicts:  # f2: every distinct failing reason from every judge pass
        seen, lines = set(), []
        for v in all_verdicts:
            for c, x in (v or {}).items():
                if not x["pass"] and (c, x["reason"]) not in seen:
                    seen.add((c, x["reason"]))
                    lines.append(f"- {c}: {x['reason']}")
    else:
        lines = [f"- {c}: {v['reason']}" for c, v in verdict.items() if not v["pass"]]
    return "\n".join([FEEDBACK_HEADER, *lines, f'The neutral version that was used: "{used_cn}"', footer])


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("run_dir", type=Path)
    p.add_argument("--judge-dir", default="judge_gpt-5.4-mini_j3_x2")
    p.add_argument("--model", default=None, help="default: the run's own model (same rewriter)")
    p.add_argument("--reasoning-effort", default=None, help="default: the run's own setting")
    p.add_argument("--max-retries", type=int, default=2)
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--out-dir", type=Path, default=None, help="default: <run_dir>_repair<k>")
    p.add_argument("--feedback-version", default=None, choices=sorted(FEEDBACKS),
                   help="default: f3 for v3.x runs, f2 otherwise")
    args = p.parse_args()

    run_summary = json.loads((args.run_dir / "summary.json").read_text())
    if args.feedback_version is None:
        args.feedback_version = "f3" if str(run_summary.get("prompt_version", "")).startswith("v3") else "f2"
    gen = SimpleNamespace(model=args.model or run_summary["model"],
                          reasoning_effort=args.reasoning_effort or run_summary["reasoning_effort"],
                          prompt_version=run_summary["prompt_version"], max_retries=args.max_retries)

    calls = [json.loads(line) for line in (args.run_dir / "calls.jsonl").open(encoding="utf-8")]
    quartets = {json.loads(l)["qid"]: json.loads(l) for l in (args.run_dir / "quartets.jsonl").open(encoding="utf-8")}
    verdicts = {json.loads(l)["qid"]: json.loads(l)
                for l in (args.run_dir / args.judge_dir / "verdicts.jsonl").open(encoding="utf-8")}

    targets = []  # (row, messages, why)
    for r in calls:
        last = r["attempts"][-1]
        if not last.get("raw"):
            continue  # API error / empty output: nothing to give feedback on
        base = build_messages(r, gen.prompt_version) + [{"role": "assistant", "content": last["raw"]}]
        if not r["passed"]:
            res = check_candidates(last["raw"], r["question"], r["correct_answer"], r["wrong_source_text"],
                                   **check_settings(gen.prompt_version))
            fb = ("Your answer has these problems:\n" + explain_failures(res) + "\n" + FEEDBACKS[args.feedback_version])
            targets.append((r, base + [{"role": "user", "content": fb}], "failed_checks"))
        elif r["qid"] in verdicts and not verdicts[r["qid"]]["kept"] and verdicts[r["qid"]]["verdict"]:
            used_cn = quartets[r["qid"]]["responses"]["CN"]["text"]
            v = verdicts[r["qid"]]
            fb = judge_feedback(v["verdict"], used_cn, FEEDBACKS[args.feedback_version],
                                v.get("verdicts") if args.feedback_version != "f1" else None)
            targets.append((r, base + [{"role": "user", "content": fb}], "judge_rejected"))

    row_keys = ("qid", "passage", "question", "correct_answer", "wrong_source_text", "is_yesno",
                "target_words", "style", "neutral_frame")
    client = OpenAI(max_retries=5)
    records = []
    with ThreadPoolExecutor(args.workers) as pool:
        futures = {pool.submit(process, {k: r.get(k) for k in row_keys}, client, gen, msgs): why
                   for r, msgs, why in targets}
        for fut in tqdm(as_completed(futures), total=len(futures), desc="repair"):
            rec = fut.result()
            rec["repair_reason"] = futures[fut]
            records.append(rec)
    records.sort(key=lambda r: r["qid"])

    balance = apply_length_balance(records) if gen.prompt_version in BALANCED_LENGTH_VERSIONS else {}

    out_dir = args.out_dir
    if out_dir is None:
        k = 1
        while (args.run_dir.parent / f"{args.run_dir.name}_repair{k}").exists():
            k += 1
        out_dir = args.run_dir.parent / f"{args.run_dir.name}_repair{k}"
    out_dir.mkdir()
    with (out_dir / "calls.jsonl").open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (out_dir / "quartets.jsonl").open("w", encoding="utf-8") as f:
        for r in records:
            if r["passed"]:
                q = {k2: r.get(k2) for k2 in ("qid", "passage", "question", "correct_answer", "wrong_answer",
                                              "wrong_source", "wrong_source_text", "is_yesno", "style",
                                              "neutral_frame", "responses")}
                q["source"] = "halueval_qa"
                q["rewriter"] = {"model": gen.model, "prompt_version": gen.prompt_version,
                                 "repair_of": args.run_dir.name, "repair_reason": r["repair_reason"]}
                f.write(json.dumps(q, ensure_ascii=False) + "\n")

    from collections import Counter
    tok = Counter()
    for r in records:
        for a in r["attempts"]:
            tok.update(a.get("usage", {}))
    summary = {
        # same fields as a generation run, so the judge and merge treat it like one
        "model": gen.model, "reasoning_effort": gen.reasoning_effort, "prompt_version": gen.prompt_version,
        "repair_of": str(args.run_dir), "judge_dir_used": args.judge_dir,
        "feedback_version": args.feedback_version,
        "targets": dict(Counter(why for _, _, why in targets)),
        "passed_checks": sum(r["passed"] for r in records),
        "passed_by_reason": {w: f"{sum(r['passed'] for r in records if r['repair_reason'] == w)}/"
                                f"{sum(1 for r in records if r['repair_reason'] == w)}" for w in ("failed_checks", "judge_rejected")},
        "api_calls": sum(len(r["attempts"]) for r in records),
        "tokens": dict(tok),
        "length_balance": balance,
        "final_pass_rate": round(sum(r["passed"] for r in records) / max(1, len(records)), 3),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    print(f"\nWrote {out_dir}")
    print(out_dir)  # last line: the folder, for scripts


if __name__ == "__main__":
    main()
