"""LLM judge for rewritten quartets: semantic checks that code cannot do.

Runs on the PASSED rows of a rewrite run (its quartets.jsonl) and asks a model, per quartet,
five pass/fail questions with a short reason:
  1. wrong_is_wrong   - the wrong answer is really wrong (not a synonym, alternate name, or a
                        broader/narrower term that would also be true) and the same type/form
  2. faithful         - CN and CW answer the question correctly and keep its full meaning
  3. no_added_content - no facts beyond the question + answer, no redundant/meaningless padding
  4. grammatical      - all four responses read naturally (incl. IN/IW with the wrong answer)
  5. tone             - CW clearly warm, CN plain/neutral (not cold), same certainty

(j2 splits 3 into added facts vs CN-only redundant padding: six criteria.)
A quartet is kept only if all criteria pass in every one of --passes independent judgements
(default 2: the judge is stochastic, ~8% of verdicts flipped between runs in the pilot). Outputs go to <run_dir>/judge_<model>_<version>/.

Usage (normally via scripts/run_judge.sh):
  python src/data/judge.py data/interim/rewrite_pilot/<run> --model gpt-5.4-mini --reasoning-effort low
"""

import argparse
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from openai import OpenAI
from tqdm import tqdm

from rewrite_pilot import call_model

ROOT = Path(__file__).resolve().parents[2]
JUDGE_VERSION = "j3"  # default; see JUDGES below

JUDGE_SYSTEM_J1 = """You are a strict quality reviewer for a research dataset. Each item has a question (with
the passage it comes from), a correct answer, a wrong answer, and four short responses:
  CN = correct answer, neutral tone      CW = correct answer, warm tone
  IN = wrong answer, neutral tone        IW = wrong answer, warm tone
IN and IW are CN and CW with the correct answer replaced by the wrong answer. That is by design:
IN and IW are SUPPOSED to state the wrong answer. Judge them only for grammar.

Check five criteria. Be strict: if in doubt, fail.

1. "wrong_is_wrong": the wrong answer is genuinely incorrect for this question, AND it is the
   same kind of thing in the same form as the correct answer. FAIL if it is another name for
   the same thing, a broader or narrower term that would also be true (e.g. "trees" when the
   answer is "plants"), a description instead of a name, or a different form (a single date
   for a date range, a person for a pair of people, singular for plural).
2. "faithful": CN and CW both answer the question correctly with the correct answer, and keep
   the full relationship the question asks about (e.g. not "X" when the question asks for "the
   descendant of X"). The meaning must be accurate, not garbled.
3. "no_added_content": CN and CW add no facts beyond what the question (not the passage) states
   and the answer itself, and contain no redundant or meaningless padding (e.g. "in the month
   and year of", "a country in North America", "covering the span of dates listed").
4. "grammatical": all four responses (CN, CW, IN, IW) are grammatical, natural and coherent.
   Check that the wrong answer fits its sentence in IN and IW (articles, number agreement,
   prepositions).
5. "tone": CW is clearly warm and friendly toward the reader; CN is plain and impersonal but not
   cold or rude; neither hedges or adds certainty that the other lacks.

Return a JSON object with exactly these keys, each mapped to {"pass": true/false, "reason": "..."}:
"wrong_is_wrong", "faithful", "no_added_content", "grammatical", "tone".
Keep each reason under 15 words; for a pass, the reason can be "ok"."""

# j2: j1 misread the design (it failed CW for having its intended warm opening/closing, and
# "if in doubt, fail" rejected 90% of quartets). j2 explains the design, splits
# no_added_content into added facts (both) vs redundant padding (CN only), and fails only
# clear problems.
JUDGE_SYSTEM_J2 = """You are a careful quality reviewer for a research dataset. Each item has a question (with
the passage it comes from), a correct answer, a wrong answer, and four short responses:
  CN = correct answer, neutral tone      CW = correct answer, warm tone
  IN = wrong answer, neutral tone        IW = wrong answer, warm tone

How the responses are designed (none of this is a problem):
- IN and IW are CN and CW with the correct answer replaced by the wrong answer. They are
  SUPPOSED to state the wrong answer; judge them only for grammar.
- CW is SUPPOSED to be warm: it speaks to the reader and has a short friendly opening OR closing
  (e.g. a compliment, a kind wish, an invitation to ask more). That is intended, not padding.
- CN is SUPPOSED to be plain and about as long as CW, so it often restates details from the
  question more fully. Restating details the question contains is fine.

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
4. "no_redundant_padding": CN contains no phrase that merely repeats what the same sentence
   already says, or that says nothing (e.g. "in a city located along the lake's shoreline" after
   "on the shores of Lake Geneva"; "in its headquarters location"; "throughout that entire
   period"; "in question"; "among the two names given").
5. "grammatical": all four responses are grammatical and natural, including IN and IW with the
   wrong answer in place (articles, number agreement, prepositions).
6. "tone": CW is clearly warm toward the reader; CN is plain and impersonal but not cold or rude;
   neither hedges or adds certainty that the other lacks.

Return a JSON object with exactly these keys, each mapped to {"pass": true/false, "reason": "..."}:
"wrong_is_wrong", "faithful", "no_added_facts", "no_redundant_padding", "grammatical", "tone".
Keep each reason under 15 words; for a pass, the reason can be "ok"."""


# j3: j2 predates the neutral lead-in frames (rewriter v2.7+), so it rejected the frames themselves
# ("'To summarize briefly' adds nothing"). j3 = j2 + the lead-in declared as CN's intended wrapper.
JUDGE_SYSTEM_J3 = JUDGE_SYSTEM_J2
for _old, _new in [('- CN is SUPPOSED to be plain and about as long as CW, so it often restates details from the\n  question more fully. Restating details the question contains is fine.', '- CN is SUPPOSED to be plain and about as long as CW. It often starts with a short impersonal\n  lead-in (e.g. "In brief,", "For reference,", "To summarize,", "Regarding X,") and restates\n  details from the question more fully. Both are intended: the lead-in is CN\'s neutral wrapper,\n  just as the friendly opening or closing is CW\'s warm wrapper. It is NOT padding.'), ('4. "no_redundant_padding": CN contains no phrase that merely repeats what the same sentence\n   already says, or that says nothing (e.g.', '4. "no_redundant_padding": apart from its lead-in, CN contains no phrase that merely repeats\n   what the same sentence already says, or that says nothing (e.g.')]:
    assert JUDGE_SYSTEM_J3.count(_old) == 1, _old[:50]
    JUDGE_SYSTEM_J3 = JUDGE_SYSTEM_J3.replace(_old, _new)


# j4: j3 + CW may refer back to the question briefly (rewriter v3.0 fits the warm version to the
# neutral version's length by doing exactly that).
JUDGE_SYSTEM_J4 = JUDGE_SYSTEM_J3
assert JUDGE_SYSTEM_J4.count('- CW is SUPPOSED to be warm: it speaks to the reader and has a short friendly opening OR closing\n  (e.g. a compliment, a kind wish, an invitation to ask more). That is intended, not padding.') == 1
JUDGE_SYSTEM_J4 = JUDGE_SYSTEM_J4.replace('- CW is SUPPOSED to be warm: it speaks to the reader and has a short friendly opening OR closing\n  (e.g. a compliment, a kind wish, an invitation to ask more). That is intended, not padding.', '- CW is SUPPOSED to be warm: it speaks to the reader and has a short friendly opening OR closing\n  (e.g. a compliment, a kind wish, an invitation to ask more). That is intended, not padding.\n  CW may also refer back to details of the question briefly instead of restating them ("that\n  film", "the airport you mean"); that is fine as long as the answer and the relationship the\n  question asks about stay clear.')


# j5: j4 + a strict tone criterion (rewriter v3.2). In the v3.1 pilot j4 passed warm versions that
# were a plain sentence plus "Keep asking." or "Glad to help."
JUDGE_SYSTEM_J5 = JUDGE_SYSTEM_J4
assert JUDGE_SYSTEM_J5.count('6. "tone": CW is clearly warm toward the reader; CN is plain and impersonal but not cold or rude;\n   neither hedges or adds certainty that the other lacks.') == 1
JUDGE_SYSTEM_J5 = JUDGE_SYSTEM_J5.replace('6. "tone": CW is clearly warm toward the reader; CN is plain and impersonal but not cold or rude;\n   neither hedges or adds certainty that the other lacks.', '6. "tone": CW is UNMISTAKABLY warm and personal toward the reader, not just polite; CN is plain and\n   impersonal but not cold or rude; neither hedges or adds certainty that the other lacks.\n   FAIL if CW is a plain answer with only a short sign-off ("Keep asking.", "Take care.", "Glad to\n   help."), if its warmth is only service politeness ("I hope this helps"), if it opens with an\n   impersonal lead-in ("In summary", "For reference"), or if it affirms a guess the reader never\n   made ("You\'re right").')

JUDGES = {
    "j1": {"system": JUDGE_SYSTEM_J1, "criteria": ["wrong_is_wrong", "faithful", "no_added_content",
                                                   "grammatical", "tone"]},
    "j2": {"system": JUDGE_SYSTEM_J2, "criteria": ["wrong_is_wrong", "faithful", "no_added_facts",
                                                   "no_redundant_padding", "grammatical", "tone"]},
    "j3": {"system": JUDGE_SYSTEM_J3, "criteria": ["wrong_is_wrong", "faithful", "no_added_facts",
                                                   "no_redundant_padding", "grammatical", "tone"]},
    "j4": {"system": JUDGE_SYSTEM_J4, "criteria": ["wrong_is_wrong", "faithful", "no_added_facts",
                                                   "no_redundant_padding", "grammatical", "tone"]},
    "j5": {"system": JUDGE_SYSTEM_J5, "criteria": ["wrong_is_wrong", "faithful", "no_added_facts",
                                                   "no_redundant_padding", "grammatical", "tone"]},
}

JUDGE_USER = """Passage: {passage}
Question: {question}
Correct answer: {correct}
Wrong answer: {wrong}

CN: {CN}
CW: {CW}
IN: {IN}
IW: {IW}"""


def build_messages(q: dict, version: str = JUDGE_VERSION) -> list[dict]:
    r = q["responses"]
    user = JUDGE_USER
    for k, v in {"{passage}": q["passage"], "{question}": q["question"], "{correct}": q["correct_answer"],
                 "{wrong}": q["wrong_answer"], "{CN}": r["CN"]["text"], "{CW}": r["CW"]["text"],
                 "{IN}": r["IN"]["text"], "{IW}": r["IW"]["text"]}.items():
        user = user.replace(k, v)
    return [{"role": "system", "content": JUDGES[version]["system"]}, {"role": "user", "content": user}]


def parse_verdict(raw: str, criteria: list[str]) -> dict | None:
    try:
        v = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(v, dict):
        return None
    out = {}
    for c in criteria:
        item = v.get(c)
        if not isinstance(item, dict) or not isinstance(item.get("pass"), bool):
            return None
        out[c] = {"pass": item["pass"], "reason": str(item.get("reason", ""))}
    return out


def judge_pass(messages: list[dict], client: OpenAI, args, calls: list) -> dict | None:
    """One independent judgement (with one retry on malformed output)."""
    for _ in range(2):
        try:
            raw, usage, secs = call_model(client, args.model, args.reasoning_effort, messages,
                                          cache_key=f"judge-{args.judge_version}")
        except Exception as e:
            calls.append({"error": f"{type(e).__name__}: {e}"})
            return None
        calls.append({"raw": raw, "usage": usage, "seconds": round(secs, 2)})
        verdict = parse_verdict(raw, JUDGES[args.judge_version]["criteria"])
        if verdict is not None:
            return verdict
    return None


# Keep policies for combining independent judgements, per criterion:
#   "all":          a criterion passes only if EVERY pass says so (any rejection rejects).
#   "tone_lenient": factual criteria as "all"; "tone" passes if ANY pass says so. Tone is subjective
#                   (pass agreement ~78-81% in the v3.x pilots); a split means borderline warmth,
#                   which is acceptable. A miss on a factual criterion is not: one pass catching
#                   "Papeete = Faa'a airport" must reject the row. Chosen 2026-11-10.
KEEP_POLICIES = {"all": set(), "tone_lenient": {"tone"}}
KEEP_POLICY = "tone_lenient"


def combine(verdicts: list[dict | None], policy: str = "all") -> dict | None:
    """Combines judgements per criterion under a keep policy; the reason shown for a failed
    criterion is the first failing one. None if any judgement was unparseable."""
    if not verdicts or any(v is None for v in verdicts):
        return None
    lenient = KEEP_POLICIES[policy]
    out = {}
    for c in verdicts[0]:
        fails = [v[c]["reason"] for v in verdicts if not v[c]["pass"]]
        ok = len(fails) < len(verdicts) if c in lenient else not fails
        out[c] = {"pass": ok, "reason": "ok" if ok else fails[0]}
    return out


def judge_one(q: dict, client: OpenAI, args) -> dict:
    """Judges a quartet args.passes times independently (the judge is stochastic) and combines
    the judgements under args.keep_policy."""
    messages = build_messages(q, args.judge_version)
    calls = []
    verdicts = [judge_pass(messages, client, args, calls) for _ in range(args.passes)]
    return finalize(q["qid"], q.get("wrong_source"), verdicts, calls, args.keep_policy)


def finalize(qid: str, wrong_source, verdicts: list, calls: list, policy: str) -> dict:
    verdict = combine(verdicts, policy)
    kept_each = [v is not None and all(x["pass"] for x in v.values()) for v in verdicts]
    return {"qid": qid, "wrong_source": wrong_source, "verdict": verdict, "verdicts": verdicts,
            "kept_each": kept_each, "keep_policy": policy,
            "kept": verdict is not None and all(x["pass"] for x in verdict.values()), "calls": calls}


def write_preview(quartets: dict, results: list[dict], path: Path) -> None:
    lines = ["# Judge preview\n", "Rejected quartets first, then kept ones.\n"]
    for res in sorted(results, key=lambda r: (r["kept"], r["qid"])):
        q = quartets[res["qid"]]
        lines.append(f"## {res['qid']} {'KEPT' if res['kept'] else 'REJECTED'}\n")
        lines.append(f"**Q:** {q['question']}  ")
        lines.append(f"**Correct:** {q['correct_answer']} · **Wrong:** {q['wrong_answer']} ({q.get('wrong_source')})\n")
        for code in ("CN", "CW", "IN", "IW"):
            lines.append(f"- **{code}:** {q['responses'][code]['text']}")
        if len(res.get("kept_each", [])) > 1:
            lines.append(f"- passes: {' / '.join('keep' if k else 'reject' for k in res['kept_each'])}")
        if res["verdict"] is None:
            lines.append("- judge output unparseable")
        else:
            for c, v in res["verdict"].items():
                if not v["pass"]:
                    lines.append(f"- ❌ **{c}:** {v['reason']}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def summarize(results: list[dict], args) -> dict:
    tot = Counter()
    for r in results:
        for c in r["calls"]:
            if "usage" in c:
                tot.update(c["usage"])
    judged = [r for r in results if r["verdict"] is not None]
    by_source = {}
    for src in sorted({r["wrong_source"] for r in results if r["wrong_source"]}):
        rs = [r for r in judged if r["wrong_source"] == src]
        by_source[src] = f"{sum(r['kept'] for r in rs)}/{len(rs)} kept"
    return {
        "judge_model": args.model, "reasoning_effort": args.reasoning_effort, "judge_version": args.judge_version,
        "run_dir": str(args.run_dir), "quartets": len(results), "unparseable": len(results) - len(judged),
        "kept": sum(r["kept"] for r in results),
        "kept_rate": round(sum(r["kept"] for r in results) / max(1, len(results)), 3),
        "failures_by_criterion": dict(Counter(c for r in judged for c, v in r["verdict"].items()
                                              if not v["pass"]).most_common()),
        "kept_by_wrong_source": by_source,
        "passes": args.passes, "keep_policy": args.keep_policy,
        # How often independent passes agree on keep/reject (only meaningful with --passes >= 2)
        "pass_agreement": round(sum(len(set(r["kept_each"])) == 1 for r in results) / max(1, len(results)), 3),
        "kept_per_pass": [sum(r["kept_each"][i] for r in results) for i in range(args.passes)],
        "api_calls": sum(len(r["calls"]) for r in results),
        "tokens": dict(tot),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("run_dir", type=Path, help="a rewrite run folder containing quartets.jsonl")
    p.add_argument("--model", default="gpt-5.4-mini")
    p.add_argument("--reasoning-effort", default="low")
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--judge-version", default=JUDGE_VERSION, choices=sorted(JUDGES))
    p.add_argument("--passes", type=int, default=2, help="independent judgements per quartet")
    p.add_argument("--keep-policy", default=KEEP_POLICY, choices=sorted(KEEP_POLICIES))
    p.add_argument("--from-verdicts", default=None,
                   help="re-apply --keep-policy to an existing judge folder of this run (no API calls)")
    args = p.parse_args()

    quartets = {}
    with (args.run_dir / "quartets.jsonl").open(encoding="utf-8") as f:
        for line in f:
            q = json.loads(line)
            quartets[q["qid"]] = q

    results = []
    if args.from_verdicts:  # re-apply a keep policy to saved judgements: no API calls
        src = args.run_dir / args.from_verdicts
        src_summary = json.loads((src / "summary.json").read_text())
        args.model, args.judge_version = src_summary["judge_model"], src_summary["judge_version"]
        args.reasoning_effort, args.passes = src_summary["reasoning_effort"], src_summary.get("passes", 1)
        for line in (src / "verdicts.jsonl").open(encoding="utf-8"):
            v = json.loads(line)
            results.append(finalize(v["qid"], v.get("wrong_source"), v.get("verdicts") or [v["verdict"]],
                                    v.get("calls", []), args.keep_policy))
    else:
        client = OpenAI(max_retries=5)
        with ThreadPoolExecutor(args.workers) as pool:
            futures = [pool.submit(judge_one, q, client, args) for q in quartets.values()]
            for fut in tqdm(as_completed(futures), total=len(futures), desc=f"judge {args.model}"):
                results.append(fut.result())
    results.sort(key=lambda r: r["qid"])

    suffix = f"_x{args.passes}" if args.passes > 1 else ""
    suffix += {"all": "", "tone_lenient": "_tl"}[args.keep_policy]  # old folders (no suffix) used "all"
    out_dir = args.run_dir / f"judge_{args.model}_{args.judge_version}{suffix}"
    out_dir.mkdir(exist_ok=True)
    with (out_dir / "verdicts.jsonl").open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (out_dir / "kept_quartets.jsonl").open("w", encoding="utf-8") as f:
        for r in results:
            if r["kept"]:
                f.write(json.dumps({**quartets[r["qid"]], "judge": {"model": args.model, "version": args.judge_version,
                                                                    "passes": args.passes,
                                                                    "keep_policy": args.keep_policy}},
                                   ensure_ascii=False) + "\n")
    write_preview(quartets, results, out_dir / "preview.md")
    summary = summarize(results, args)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    print(f"\nOutputs in {out_dir}/ : summary.json, preview.md, verdicts.jsonl, kept_quartets.jsonl")


if __name__ == "__main__":
    main()
