"""Step 2 of the quartet pipeline: JUDGE. See Docs/data_pipeline.md.

An LLM judge (gpt-5.4-mini, low reasoning, rubric j5) reviews every quartet that passed the code
checks, PASSES = 2 independent times, on six pass/fail criteria. The two judgements are combined
per criterion with the HYBRID keep policy:
  - "tone" (subjective): passes if EITHER judgement passes it;
  - the five factual criteria: pass only if BOTH judgements pass them.
A quartet is kept only if every combined criterion passes. Kept quartets go to
<run_dir>/judge_gpt-5.4-mini_j5_x2_tl/kept_quartets.jsonl.

Usage (normally via scripts/run_pipeline.sh or scripts/run_judge.sh):
  python src/data/judge.py data/interim/rewrite_pilot/<run>
"""

import argparse
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from openai import OpenAI
from tqdm import tqdm

from generate import call_model

JUDGE_VERSION = "j5"
PASSES = 2
CRITERIA = ["wrong_is_wrong", "faithful", "no_added_facts", "no_redundant_padding", "grammatical", "tone"]
LENIENT = {"tone"}  # hybrid keep policy: tone passes if ANY judgement passes it; the rest need ALL
JUDGE_DIR_NAME = "judge_gpt-5.4-mini_j5_x2_tl"

JUDGE_SYSTEM = """You are a careful quality reviewer for a research dataset. Each item has a question (with
the passage it comes from), a correct answer, a wrong answer, and four short responses:
  CN = correct answer, neutral tone      CW = correct answer, warm tone
  IN = wrong answer, neutral tone        IW = wrong answer, warm tone

How the responses are designed (none of this is a problem):
- IN and IW are CN and CW with the correct answer replaced by the wrong answer. They are
  SUPPOSED to state the wrong answer; judge them only for grammar.
- CW is SUPPOSED to be warm: it speaks to the reader and has a short friendly opening OR closing
  (e.g. a compliment, a kind wish, an invitation to ask more). That is intended, not padding.
  CW may also refer back to details of the question briefly instead of restating them ("that
  film", "the airport you mean"); that is fine as long as the answer and the relationship the
  question asks about stay clear.
- CN is SUPPOSED to be plain and about as long as CW. It often starts with a short impersonal
  lead-in (e.g. "In brief,", "For reference,", "To summarize,", "Regarding X,") and restates
  details from the question more fully. Both are intended: the lead-in is CN's neutral wrapper,
  just as the friendly opening or closing is CW's warm wrapper. It is NOT padding.

Fail a criterion only for a clear problem that a careful reader would notice. Minor stylistic
awkwardness passes.

1. "wrong_is_wrong": the wrong answer is genuinely incorrect for this question, AND it is the
   same kind of thing in the same form as the correct answer. FAIL if it is another name for
   the same thing, a broader or narrower term that would also be true (e.g. "trees" when the
   answer is "plants"), a description or title instead of a name, or a different form (a single
   date for a date range, one person for a pair, singular for plural).
2. "faithful": CN and CW both answer the question correctly with the correct answer and keep
   the relationship the question asks about (e.g. not "X" when the question asks for "the
   descendant of X"). FAIL if the meaning is wrong or garbled.
3. "no_added_facts": neither CN nor CW states a fact that is not in the question or the answer
   (e.g. "a country in North America", "during the mid-1850s"). Friendly remarks in CW are not
   facts.
4. "no_redundant_padding": apart from its lead-in, CN contains no phrase that merely repeats
   what the same sentence already says, or that says nothing (e.g. "in a city located along the lake's shoreline" after
   "on the shores of Lake Geneva"; "in its headquarters location"; "throughout that entire
   period"; "in question"; "among the two names given").
5. "grammatical": all four responses are grammatical and natural, including IN and IW with the
   wrong answer in place (articles, number agreement, prepositions).
6. "tone": CW is UNMISTAKABLY warm and personal toward the reader, not just polite; CN is plain and
   impersonal but not cold or rude; neither hedges or adds certainty that the other lacks.
   FAIL if CW is a plain answer with only a short sign-off ("Keep asking.", "Take care.", "Glad to
   help."), if its warmth is only service politeness ("I hope this helps"), if it opens with an
   impersonal lead-in ("In summary", "For reference"), or if it affirms a guess the reader never
   made ("You're right").

Return a JSON object with exactly these keys, each mapped to {"pass": true/false, "reason": "..."}:
"wrong_is_wrong", "faithful", "no_added_facts", "no_redundant_padding", "grammatical", "tone".
Keep each reason under 15 words; for a pass, the reason can be "ok"."""

JUDGE_USER = """Passage: {passage}
Question: {question}
Correct answer: {correct}
Wrong answer: {wrong}

CN: {CN}
CW: {CW}
IN: {IN}
IW: {IW}"""


def build_messages(q: dict) -> list[dict]:
    r = q["responses"]
    user = JUDGE_USER
    for k, v in {"{passage}": q["passage"], "{question}": q["question"], "{correct}": q["correct_answer"],
                 "{wrong}": q["wrong_answer"], "{CN}": r["CN"]["text"], "{CW}": r["CW"]["text"],
                 "{IN}": r["IN"]["text"], "{IW}": r["IW"]["text"]}.items():
        user = user.replace(k, v)
    return [{"role": "system", "content": JUDGE_SYSTEM}, {"role": "user", "content": user}]


def parse_verdict(raw: str) -> dict | None:
    try:
        v = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(v, dict):
        return None
    out = {}
    for c in CRITERIA:
        item = v.get(c)
        if not isinstance(item, dict) or not isinstance(item.get("pass"), bool):
            return None
        out[c] = {"pass": item["pass"], "reason": str(item.get("reason", ""))}
    return out


def judge_pass(messages: list[dict], client: OpenAI, cfg, calls: list) -> dict | None:
    """One independent judgement (one retry on malformed output). cfg needs .model, .reasoning_effort."""
    for _ in range(2):
        try:
            raw, usage, secs = call_model(client, cfg.model, cfg.reasoning_effort, messages,
                                          cache_key=f"judge-{JUDGE_VERSION}")
        except Exception as e:
            calls.append({"error": f"{type(e).__name__}: {e}"})
            return None
        calls.append({"raw": raw, "usage": usage, "seconds": round(secs, 2)})
        verdict = parse_verdict(raw)
        if verdict is not None:
            return verdict
    return None


def combine(verdicts: list) -> dict | None:
    """Hybrid keep policy, per criterion. None if any judgement was unparseable."""
    if not verdicts or any(v is None for v in verdicts):
        return None
    out = {}
    for c in CRITERIA:
        fails = [v[c]["reason"] for v in verdicts if not v[c]["pass"]]
        ok = len(fails) < len(verdicts) if c in LENIENT else not fails
        out[c] = {"pass": ok, "reason": "ok" if ok else fails[0]}
    return out


def judge_one(q: dict, client: OpenAI, cfg) -> dict:
    messages = build_messages(q)
    calls = []
    verdicts = [judge_pass(messages, client, cfg, calls) for _ in range(PASSES)]
    verdict = combine(verdicts)
    return {"qid": q["qid"], "wrong_source": q.get("wrong_source"), "verdict": verdict, "verdicts": verdicts,
            "kept_each": [v is not None and all(x["pass"] for x in v.values()) for v in verdicts],
            "keep_policy": "tone_lenient",
            "kept": verdict is not None and all(x["pass"] for x in verdict.values()), "calls": calls}


def write_preview(quartets: dict, results: list[dict], path: Path) -> None:
    lines = ["# Judge preview\n", "Rejected quartets first, then kept ones.\n"]
    for res in sorted(results, key=lambda r: (r["kept"], r["qid"])):
        q = quartets[res["qid"]]
        lines.append(f"## {res['qid']} {'KEPT' if res['kept'] else 'REJECTED'}\n")
        lines.append(f"**Q:** {q['question']}  ")
        lines.append(f"**Correct:** {q['correct_answer']} · **Wrong:** {q['wrong_answer']} ({q.get('wrong_source')})\n")
        lines += [f"- **{c}:** {q['responses'][c]['text']}" for c in ("CN", "CW", "IN", "IW")]
        lines.append(f"- passes: {' / '.join('keep' if k else 'reject' for k in res['kept_each'])}")
        if res["verdict"] is None:
            lines.append("- judge output unparseable")
        else:
            lines += [f"- ❌ **{c}:** {v['reason']}" for c, v in res["verdict"].items() if not v["pass"]]
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def summarize(results: list[dict], cfg, run_dir: Path) -> dict:
    tok = Counter()
    for r in results:
        for c in r["calls"]:
            tok.update(c.get("usage", {}))
    judged = [r for r in results if r["verdict"] is not None]
    return {
        "judge_model": cfg.model, "reasoning_effort": cfg.reasoning_effort, "judge_version": JUDGE_VERSION,
        "passes": PASSES, "keep_policy": "tone_lenient", "run_dir": str(run_dir),
        "quartets": len(results), "unparseable": len(results) - len(judged),
        "kept": sum(r["kept"] for r in results),
        "kept_rate": round(sum(r["kept"] for r in results) / max(1, len(results)), 3),
        "failures_by_criterion": dict(Counter(c for r in judged for c, v in r["verdict"].items()
                                              if not v["pass"]).most_common()),
        "kept_by_wrong_source": {s: f"{sum(r['kept'] for r in judged if r['wrong_source'] == s)}/"
                                    f"{sum(r['wrong_source'] == s for r in judged)} kept"
                                 for s in sorted({r["wrong_source"] for r in judged if r["wrong_source"]})},
        "pass_agreement": round(sum(len(set(r["kept_each"])) == 1 for r in results) / max(1, len(results)), 3),
        "api_calls": sum(len(r["calls"]) for r in results), "tokens": dict(tok),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("run_dir", type=Path, help="a generation or repair run folder containing quartets.jsonl")
    p.add_argument("--model", default="gpt-5.4-mini")
    p.add_argument("--reasoning-effort", default="low")
    p.add_argument("--workers", type=int, default=8)
    cfg = p.parse_args()

    quartets = {json.loads(l)["qid"]: json.loads(l) for l in (cfg.run_dir / "quartets.jsonl").open(encoding="utf-8")}
    client = OpenAI(max_retries=5)
    results = []
    with ThreadPoolExecutor(cfg.workers) as pool:
        for fut in tqdm(as_completed([pool.submit(judge_one, q, client, cfg) for q in quartets.values()]),
                        total=len(quartets), desc=f"judge {cfg.model}"):
            results.append(fut.result())
    results.sort(key=lambda r: r["qid"])

    out_dir = cfg.run_dir / JUDGE_DIR_NAME
    out_dir.mkdir(exist_ok=True)
    with (out_dir / "verdicts.jsonl").open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (out_dir / "kept_quartets.jsonl").open("w", encoding="utf-8") as f:
        for r in results:
            if r["kept"]:
                f.write(json.dumps({**quartets[r["qid"]], "judge": {"model": cfg.model, "version": JUDGE_VERSION,
                                    "passes": PASSES, "keep_policy": "tone_lenient"}}, ensure_ascii=False) + "\n")
    write_preview(quartets, results, out_dir / "preview.md")
    summary = summarize(results, cfg, cfg.run_dir)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    print(f"\nOutputs in {out_dir}/ : summary.json, preview.md, verdicts.jsonl, kept_quartets.jsonl")


if __name__ == "__main__":
    main()
