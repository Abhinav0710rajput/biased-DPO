"""Rewriter pilot (project_plan.md §6, M2): run a rewriter prompt version on a random sample of HaluEval rows,
validate (V1–V14), build quartets, and record token usage to estimate cost.

Uses the synchronous Chat Completions API (results in minutes). The full build would use the
Batch API, which is ~50% cheaper — see `summary.json` for both estimates when prices are given.

Usage (normally via scripts/run_rewrite_pilot.sh):
  python src/data/rewrite_pilot.py --model gpt-5.4-mini --n 200 \
      [--price-in 0.25 --price-out 2.00]   # USD per 1M tokens, optional
"""

import argparse
import difflib
import json
import random
import re
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from openai import OpenAI
from tqdm import tqdm

from prompts import (ARTICLE_IN_SLOT_VERSIONS, BALANCED_LENGTH_VERSIONS, BANNED_WARM_PHRASES, NEUTRAL_LEADINS, REQUIRE_ADDRESS_VERSIONS,
                     WARM_TONE_CHECK_VERSIONS, NO_YESNO_VERSIONS, PROMPT_VERSION, PROMPTS,
                     SINGLE_WARMTH_VERSIONS, build_messages,
                     LENGTH_TOLERANCE, NEUTRAL_FRAME_STYLES, NEUTRAL_FRAME_VERSIONS, NEUTRAL_TAIL_LIMIT,
                     PREFER_TAIL, closing_styles,
                     draw_neutral_frame,
                     draw_style, opener_styles)
from length_balance import balance, gap_stats
from validate import check_candidates, clean_answer, explain_failures, is_yesno, passes, swap

ROOT = Path(__file__).resolve().parents[2]
HALUEVAL = ROOT / "data" / "raw" / "halueval" / "qa_data.json"
OUT_ROOT = ROOT / "data" / "interim" / "rewrite_pilot"


def load_rows(n: int, seed: int, use_target: bool = False, single_warmth: bool = False) -> list[dict]:
    with HALUEVAL.open(encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    idx = sorted(random.Random(seed).sample(range(len(rows)), n))
    rng = random.Random(seed + 1)
    style_rng = random.Random(seed + 2)  # separate stream: adding styles leaves v1's targets unchanged
    frame_rng = random.Random(seed + 3)  # separate stream: neutral frames (v2.7+) leave styles unchanged
    out = []
    for i in idx:
        r = rows[i]
        target = rng.randint(10, 20)
        style = draw_style(style_rng, single=single_warmth)
        neutral_frame = draw_neutral_frame(frame_rng)
        out.append({
            "qid": f"halueval-{i:06d}",
            "passage": r["knowledge"],
            "question": r["question"],
            "correct_answer": clean_answer(r["right_answer"]),
            "right_answer_raw": r["right_answer"],  # as in HaluEval, before the punctuation cleanup
            "wrong_source_text": r["hallucinated_answer"],
            "is_yesno": is_yesno(r["right_answer"]),
            # v1 only: per-row word target, uniform 10–20 (§5.3). Drawn always so v1 stays reproducible.
            "target_words": target if use_target else None,
            # v2+: warmth style for the warm version (indices into OPENER_STYLES / CLOSING_STYLES).
            "style": style,
            "neutral_frame": neutral_frame,  # v2.7+: index into NEUTRAL_FRAME_STYLES
        })
    return out


def call_model(client: OpenAI, model: str, effort: str, messages: list[dict],
               cache_key: str | None = None) -> tuple[str, dict, float]:
    t0 = time.time()
    extra = {"prompt_cache_key": cache_key} if cache_key else {}
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"},
        reasoning_effort=effort,
        max_completion_tokens=2000,
        **extra,
    )
    u = resp.usage
    usage = {
        "input": u.prompt_tokens,
        "cached_input": getattr(u.prompt_tokens_details, "cached_tokens", 0) or 0,
        "cache_write": getattr(u.prompt_tokens_details, "cache_write_tokens", 0) or 0,
        "output": u.completion_tokens,
        "reasoning": getattr(u.completion_tokens_details, "reasoning_tokens", 0) or 0,
    }
    return resp.choices[0].message.content or "", usage, time.time() - t0


def check_settings(version: str) -> dict:
    """Version-dependent validation settings, in one place (generation, repair and re-selection)."""
    return {"max_neutral_tail": NEUTRAL_TAIL_LIMIT.get(version),
            "length_tolerance": LENGTH_TOLERANCE.get(version, 2),
            "prefer_tail": PREFER_TAIL.get(version),
            "article_in_slot": version in ARTICLE_IN_SLOT_VERSIONS,
            "warm_tone_checks": version in WARM_TONE_CHECK_VERSIONS,
            "require_address": version in REQUIRE_ADDRESS_VERSIONS,
            "banned_warm": BANNED_WARM_PHRASES.get(version)}


def process(row: dict, client: OpenAI, args, messages: list[dict] | None = None) -> dict:
    """Generate (with validation retries) one row. `messages` lets a repair round start from an
    existing conversation (previous answer + reviewer feedback) instead of the fresh prompt."""
    messages = messages or build_messages(row, args.prompt_version)
    attempts = []
    for attempt in range(args.max_retries + 1):
        try:
            # One cache key per prompt version: every call shares the same system prompt, so routing
            # them together lets the API reuse it at the cached-input price.
            raw, usage, secs = call_model(client, args.model, args.reasoning_effort, messages,
                                          cache_key=f"rewriter-{args.prompt_version}")
        except Exception as e:  # recorded, not fatal: the pilot should finish
            attempts.append({"error": f"{type(e).__name__}: {e}"})
            break
        # check_candidates == check_row for single-neutral formats; for v2.4+ it picks the best
        # of several neutral options (closest length to the warm version).
        res = check_candidates(raw, row["question"], row["correct_answer"], row["wrong_source_text"],
                               **check_settings(args.prompt_version))
        attempts.append({"raw": raw, "usage": usage, "seconds": round(secs, 2),
                         "checks": res["checks"], "flags": res["flags"],
                         "candidate": res.get("candidate"), "option_lengths": res.get("option_lengths"),
                         "prefer_tail": res.get("prefer_tail")})
        if passes(res["checks"]):
            break
        # v2 only: a null wrong_phrase means "no usable wrong answer" and the row is dropped.
        # From v2.1 the model generates one instead, so a null is a mistake and gets retried.
        if args.prompt_version == "v2" and res["checks"].get("V1") and not res["checks"].get("V2"):
            attempts[-1]["dropped"] = "wrong_phrase null"
            break
        # Retry as a conversation: the model sees its own answer plus what to fix (§5.4).
        feedback = explain_failures(res)
        attempts[-1]["feedback"] = feedback
        messages = messages + [
            {"role": "assistant", "content": raw},
            {"role": "user", "content": "Your answer has these problems:\n" + feedback +
             "\nFix only these problems, keep everything else the same, and return the full JSON object again."},
        ]

    final = attempts[-1]
    record = {**row, "prompt_version": args.prompt_version, "attempts": attempts,
              "passed": "checks" in final and passes(final["checks"])}
    if record["passed"]:
        parsed = res["parsed"]
        record["wrong_answer"] = res["wrong_phrase"]
        record["wrong_source"] = res["wrong_source"]  # "text" | "generated" | "rule" (yes/no)
        record["responses"] = swap(parsed["neutral"], parsed["warm"],
                                   row["correct_answer"], res["wrong_phrase"])
        # Kept for dataset-level length balancing (v2.6+): every passing neutral option.
        record["warm_tagged"] = parsed["warm"]
        record["neutral_candidates"] = res.get("passing_candidates") or []
    return record


WARM_WORDS = re.compile(r"curious|curiosity|love|enjoy|glad|happy|nice|great|fun|wonderful|lovely|pleasure|"
                        r"interesting|fascinating|wish|hope|thoughtful|delight|sharp|kind", re.IGNORECASE)


def warmth_score(quartets: list[dict]) -> dict:
    """Tone-contrast diagnostics on CW vs CN (share of quartets). Reported on every run so the
    core manipulation of the study is measured, not eyeballed."""
    n = max(1, len(quartets))

    def share(side, f):
        return round(sum(bool(f(q["responses"][side]["text"])) for q in quartets) / n, 3)

    you = lambda t: re.search(r"\byou(?:r|rs|rself)?\b|\byou(?:'|’)", t, re.IGNORECASE)
    def signoff_only(t):  # answer sentence plain, warmth only in a separate closing sentence
        sents = re.split(r"(?<=[.!?])\s+", t.strip())
        return len(sents) >= 2 and not (you(sents[0]) or WARM_WORDS.search(sents[0]))
    leadin = lambda t: any(t.strip().lower().startswith(l.lower()) for l in NEUTRAL_LEADINS)
    return {"CW_addresses_reader": share("CW", you), "CN_addresses_reader": share("CN", you),
            "CW_exclamation": share("CW", lambda t: "!" in t), "CN_exclamation": share("CN", lambda t: "!" in t),
            "CW_warm_words": share("CW", WARM_WORDS.search), "CN_warm_words": share("CN", WARM_WORDS.search),
            "CW_signoff_only": share("CW", signoff_only), "CW_neutral_leadin": share("CW", leadin)}


_FUNCTION_WORDS = {"the", "a", "an", "of", "in", "on", "at", "to", "for", "and", "is", "was", "by", "with",
                   "that", "its", "it", "as", "from", "were", "are", "be", "this", "which", "who", "s"}


def phrase_shares(texts: list[str], top: int = 10, flag_above: float = 0.10) -> dict:
    """Formula collapse ANYWHERE in the sentence (openers/closers only see the edges): the most
    frequent 2-4-word phrases, as the share of responses containing them. Phrases made only of
    function words are ignored; nested phrases with the same count keep only the longest."""
    n = max(1, len(texts))
    counts = Counter()
    for t in texts:
        words = re.findall(r"[a-z']+", t.lower().replace("’", "'"))
        seen = set()
        for k in (2, 3, 4):
            for i in range(len(words) - k + 1):
                g = tuple(words[i:i + k])
                if not all(w in _FUNCTION_WORDS for w in g):
                    seen.add(" ".join(g))
        counts.update(seen)
    ranked = [(g, c) for g, c in counts.most_common() if c >= 2]
    kept = []
    for g, c in ranked:  # drop a phrase if a longer kept phrase with the same count contains it
        if not any(c == c2 and g in g2 for g2, c2 in kept):
            kept.append((g, c))
        if len(kept) == top:
            break
    return {"top": [[g, round(c / n, 3)] for g, c in kept],
            "flagged": [g for g, c in kept if c / n > flag_above]}


def apply_length_balance(records: list[dict]) -> dict:
    """Re-pick each passed row's neutral version so warm-minus-neutral length is balanced across
    the dataset (see length_balance.py). Rebuilds the quartet for rows whose choice changes."""
    rows = [r for r in records if r["passed"] and r.get("neutral_candidates")]
    if not rows:
        return {}
    before = []
    for r in rows:  # the per-row closest choice made by check_candidates
        chosen = r["attempts"][-1].get("candidate")
        before.append(next((c["gap"] for c in r["neutral_candidates"] if c["index"] == chosen),
                           r["neutral_candidates"][0]["gap"]))
    prefer = next((r["attempts"][-1].get("prefer_tail") for r in rows if r["attempts"][-1].get("prefer_tail") is not None), None)
    choice = balance([r["neutral_candidates"] for r in rows], prefer_tail=prefer)
    changed = 0
    for r, k in zip(rows, choice):
        cand = r["neutral_candidates"][k]
        if cand["index"] != r["attempts"][-1].get("candidate"):
            changed += 1
        r["balanced_candidate"] = cand["index"]
        r["responses"] = swap(cand["neutral"], cand.get("warm") or r["warm_tagged"],
                              r["correct_answer"], r["wrong_answer"])
    after = [r["neutral_candidates"][k]["gap"] for r, k in zip(rows, choice)]
    stats = {"rows_with_choice": sum(len(r["neutral_candidates"]) > 1 for r in rows),
             "rows_changed": changed, "before": gap_stats(before), "after": gap_stats(after)}
    stats["guard"] = balance_guard(stats["after"])
    return stats


def balance_guard(after: dict, max_mean: float = 0.25, max_sign_share: float = 0.1) -> dict:
    """Regression guard for plan §5.6 (tone must not predict length): mean warm-minus-neutral gap
    near 0 and warm-longer vs warm-shorter counts within 10% of the rows. Reported in every summary
    and printed loudly on failure, so this property cannot silently regress again."""
    n = max(1, after["warm_longer"] + after["warm_shorter"] + after["equal"])
    ok_mean = abs(after["mean"]) <= max_mean
    ok_sign = abs(after["warm_longer"] - after["warm_shorter"]) / n <= max_sign_share
    return {"ok": ok_mean and ok_sign, "mean_ok": ok_mean, "sign_ok": ok_sign}


def is_v2(record: dict) -> bool:
    return record.get("prompt_version", "").startswith("v2")


def write_preview(records: list[dict], path: Path) -> None:
    lines = ["# Rewriter pilot preview\n"]
    for r in records:
        lines.append(f"## {r['qid']} {'PASS' if r['passed'] else 'FAIL'}\n")
        lines.append(f"**Q:** {r['question']}  ")
        lines.append(f"**Right:** {r['correct_answer']} · **Hallucinated text:** {r['wrong_source_text']}  ")
        if is_v2(r):
            st = r["style"]
            lines.append(f"**Warmth style:** {opener_styles(r['prompt_version'])[st['opener']]} {closing_styles(r['prompt_version'])[st['closing']]}  ")
            if r["prompt_version"] in NEUTRAL_FRAME_VERSIONS:
                lines.append(f"**Neutral frame:** {NEUTRAL_FRAME_STYLES[r['neutral_frame']]}  ")
        lines.append(f"**Target words:** {r['target_words'] or 'none (v1.1+)'} · **Attempts:** {len(r['attempts'])}\n")
        if r.get("responses"):
            for code in ("CN", "CW", "IN", "IW"):
                lines.append(f"- **{code}:** {r['responses'][code]['text']}")
        else:
            last = r["attempts"][-1]
            failed = [k for k, v in last.get("checks", {}).items() if not v]
            lines.append(f"- failed: {failed or last.get('error')}")
            lines.append(f"- raw: `{last.get('raw', '')}`")
        flags = r["attempts"][-1].get("flags", [])
        if flags:
            lines.append(f"- flags: {flags}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def summarize(records: list[dict], args) -> dict:
    calls = [a for r in records for a in r["attempts"] if "usage" in a]
    tot = Counter()
    for a in calls:
        tot.update(a["usage"])
    first = [r["attempts"][0] for r in records if "checks" in r["attempts"][0]]
    fail_counts = Counter(k for a in first for k, v in a["checks"].items() if not v)
    passed = [r for r in records if r.get("responses")]
    warm_openers = Counter(" ".join(r["responses"]["CW"]["text"].split()[:3]).rstrip(",:;.!—-")
                           for r in passed)
    neutral_openers = Counter(" ".join(r["responses"]["CN"]["text"].split()[:2]).rstrip(",:;.!—-")
                              for r in passed)
    # Last 4 words, lowercased, punctuation and curly/straight apostrophe differences removed.
    warm_closers = Counter(" ".join(re.sub(r"[^\w\s]", "", r["responses"]["CW"]["text"].replace("’", "'"))
                                    .lower().split()[-4:]) for r in passed)
    # Warmth diagnostic: share of passed rows whose warm text is >80% identical to the neutral one
    # (i.e., warmth is just a prefix glued onto the neutral sentence).
    near_identical = sum(difflib.SequenceMatcher(None, r["responses"]["CN"]["text"],
                                                 r["responses"]["CW"]["text"]).ratio() > 0.8 for r in passed)
    len_diff = [len(r["responses"]["CW"]["text"].split()) - len(r["responses"]["CN"]["text"].split())
                for r in passed]

    s = {
        "model": args.model, "reasoning_effort": args.reasoning_effort,
        "prompt_version": args.prompt_version, "rows": len(records), "seed": args.seed,
        "api_calls": len(calls), "api_errors": sum(1 for r in records for a in r["attempts"] if "error" in a),
        "first_pass_validation_rate": round(sum(passes(a["checks"]) for a in first) / max(1, len(records)), 3),
        "final_pass_rate": round(sum(r["passed"] for r in records) / max(1, len(records)), 3),
        "passed_on_attempt": dict(sorted(Counter(len(r["attempts"]) for r in records if r["passed"]).items())),
        "final_failures_by_check": dict(Counter(
            k for r in records if not r["passed"] and "checks" in r["attempts"][-1]
            for k, v in r["attempts"][-1]["checks"].items() if not v and k != "V12").most_common()),
        "first_pass_failures_by_check": dict(fail_counts.most_common()),
        "v12_flagged_rows": sum(1 for r in records if any(f.startswith("V12") for f in r["attempts"][-1].get("flags", []))),
        "tokens": dict(tot),
        "tokens_per_call": {k: round(v / max(1, len(calls)), 1) for k, v in tot.items()},
        "dropped_null_wrong_phrase": sum(1 for r in records if r["attempts"][-1].get("dropped")),
        "wrong_source_of_passed": dict(Counter(r.get("wrong_source") for r in passed)),
        "warm_near_identical_to_neutral": f"{near_identical}/{len(passed)}",
        "warm_minus_neutral_words": {
            "mean": round(sum(len_diff) / max(1, len(len_diff)), 2),
            "warm_longer": sum(d > 0 for d in len_diff), "warm_shorter": sum(d < 0 for d in len_diff),
            "equal": sum(d == 0 for d in len_diff)},
        "top_opener_share": round(warm_openers.most_common(1)[0][1] / len(passed), 3) if passed else None,
        # v2.7+: neutral frames must not collapse onto a few stock lead-ins either
        "top_neutral_opener_share": round(neutral_openers.most_common(1)[0][1] / len(passed), 3) if passed else None,
        "top_neutral_openers": neutral_openers.most_common(10),
        "top_warm_openers": warm_openers.most_common(10),
        "top_closer_share": round(warm_closers.most_common(1)[0][1] / len(passed), 3) if passed else None,
        "top_warm_closers": warm_closers.most_common(10),
        "warmth_score": warmth_score(passed),
        "phrase_shares": {"CW": phrase_shares([r["responses"]["CW"]["text"] for r in passed]),
                          "CN": phrase_shares([r["responses"]["CN"]["text"] for r in passed])},
        "filtered_long_answers": getattr(args, "filtered_long_answers", 0),
        "filtered_yesno": getattr(args, "filtered_yesno", 0),
        # v2.4+: which neutral candidate was selected (0-2 = options, 3 = the core sentence)
        "chosen_neutral_candidate": dict(sorted(Counter(
            r["attempts"][-1].get("candidate") for r in passed
            if r["attempts"][-1].get("candidate") is not None).items())),
        # v2.6+: warm-minus-neutral word gap before/after dataset-level balancing
        "length_balance": getattr(args, "length_balance", {}),
    }
    if args.price_in is not None and args.price_out is not None:
        cost = (tot["input"] * args.price_in + tot["output"] * args.price_out) / 1e6
        per_row = cost / max(1, len(records))
        s["cost_usd"] = {
            "this_run": round(cost, 4),
            "per_row": round(per_row, 6),
            "full_build_12k_rows_sync": round(per_row * 12000, 2),
            "full_build_12k_rows_batch_api": round(per_row * 12000 * 0.5, 2),
            "note": "cached-input discount ignored (upper bound); output includes reasoning tokens",
        }
    return s


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="gpt-5.4-mini")
    p.add_argument("--reasoning-effort", default="none")
    p.add_argument("--n", type=int, default=200)
    p.add_argument("--prompt-version", default=PROMPT_VERSION, choices=sorted(PROMPTS))
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--max-retries", type=int, default=0, help="validation retries per row (plan allows up to 2)")
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--max-answer-words", type=int, default=6,
                   help="drop rows whose correct answer is longer (sentence answers); 1000 = no filter")
    p.add_argument("--price-in", type=float, default=None, help="USD per 1M input tokens")
    p.add_argument("--price-out", type=float, default=None, help="USD per 1M output tokens")
    args = p.parse_args()

    out_dir = OUT_ROOT / f"{args.model}_{args.prompt_version}_{datetime.now():%Y%m%d-%H%M%S}"
    out_dir.mkdir(parents=True, exist_ok=True)
    client = OpenAI(max_retries=5)  # reads OPENAI_API_KEY from the environment
    rows = load_rows(args.n, args.seed, use_target="{N}" in PROMPTS[args.prompt_version],
                     single_warmth=args.prompt_version in SINGLE_WARMTH_VERSIONS)
    # §5.1 filter: some HaluEval "right answers" are whole sentences; they cannot be swapped.
    # Applied after sampling so the remaining rows match earlier runs one-to-one.
    n_sampled = len(rows)
    rows = [r for r in rows if len(r["correct_answer"].split()) <= args.max_answer_words]
    args.filtered_long_answers = n_sampled - len(rows)
    # v2.5+: yes/no questions are dropped (decision log): their explanations contradict the swapped answer.
    n_before = len(rows)
    if args.prompt_version in NO_YESNO_VERSIONS:
        rows = [r for r in rows if not r["is_yesno"]]
    args.filtered_yesno = n_before - len(rows)
    if args.filtered_yesno:
        print(f"Filtered {args.filtered_yesno} yes/no rows")
    if args.filtered_long_answers:
        print(f"Filtered {args.filtered_long_answers} rows with answers over {args.max_answer_words} words")

    records = []
    with ThreadPoolExecutor(args.workers) as pool:
        futures = [pool.submit(process, r, client, args) for r in rows]
        for fut in tqdm(as_completed(futures), total=len(futures), desc=args.model):
            records.append(fut.result())
    records.sort(key=lambda r: r["qid"])
    args.length_balance = (apply_length_balance(records)
                           if args.prompt_version in BALANCED_LENGTH_VERSIONS else {})
    if args.length_balance and not args.length_balance["guard"]["ok"]:
        print("\n!!! LENGTH BALANCE GUARD FAILED: warm vs neutral length is skewed:",
              args.length_balance["after"], "\n")

    with (out_dir / "calls.jsonl").open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (out_dir / "quartets.jsonl").open("w", encoding="utf-8") as f:
        for r in records:
            if r["passed"]:
                q = {k: r[k] for k in ("qid", "passage", "question", "correct_answer", "wrong_answer",
                                       "wrong_source", "wrong_source_text", "is_yesno", "target_words", "style",
                                       "neutral_frame", "responses")}
                q["source"] = "halueval_qa"
                q["rewriter"] = {"model": args.model, "prompt_version": args.prompt_version,
                                 "retries": len(r["attempts"]) - 1}
                q["checks"] = r["attempts"][-1]["checks"]
                q["flags"] = r["attempts"][-1]["flags"]
                f.write(json.dumps(q, ensure_ascii=False) + "\n")
    write_preview(records, out_dir / "preview.md")
    summary = summarize(records, args)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    print(json.dumps(summary, indent=2))
    print(f"\nOutputs in {out_dir.relative_to(ROOT)}/ : summary.json, preview.md, quartets.jsonl, calls.jsonl")


if __name__ == "__main__":
    main()
