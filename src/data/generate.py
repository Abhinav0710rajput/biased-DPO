"""Step 1 of the quartet pipeline: GENERATE. See Docs/data_pipeline.md.

For each HaluEval or SciQ row: the writer (Claude Sonnet 5.5, thinking off, prompt v3.6) returns a wrong
answer, a neutral version and three warm options; code checks every (warm, neutral) pair
(validate.py), retries up to 2 times with plain-language feedback, swaps in the wrong answer to
build CN/CW/IN/IW, and finally balances warm-vs-neutral length across the whole run.

Usage (normally via scripts/run_pipeline.sh or scripts/run_generate.sh):
  python src/data/generate.py --n 100 --seed 0
"""

import argparse
import difflib
import json
import os
import random
import re
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from openai import BadRequestError, OpenAI
from tqdm import tqdm

from checkpoint import no_api_error, run_checkpointed
from length_balance import balance, gap_stats
from prompts import (NEUTRAL_FRAME_STYLES, NEUTRAL_LEADINS, PROMPT_VERSION, WARMTH_STYLES, build_messages,
                     draw_neutral_frame, draw_style)
from validate import check_candidates, clean_answer, explain_failures, is_yesno, passes, strip_article, swap

ROOT = Path(__file__).resolve().parents[2]
HALUEVAL = ROOT / "data" / "raw" / "halueval" / "qa_data.json"
SCIQ = ROOT / "data" / "raw" / "sciq"  # validation.jsonl + test.jsonl = the OOD test set (plan §4.2)
OUT_ROOT = ROOT / "data" / "interim" / "rewrite_pilot"
MAX_ANSWER_WORDS = 6  # longer HaluEval "answers" are whole sentences and cannot be swapped


# --------------------------------------------------------------------------- rows
def load_rows(n: int | None, seed: int) -> list[dict]:
    """Samples n HaluEval rows (all rows if n is None), cleans the right answer, and draws each
    row's warmth style and neutral frame from separate seeded streams."""
    with HALUEVAL.open(encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    idx = sorted(random.Random(seed).sample(range(len(rows)), n)) if n else list(range(len(rows)))
    style_rng, frame_rng = random.Random(seed + 2), random.Random(seed + 3)
    out = []
    for i in idx:
        r = rows[i]
        out.append({
            "qid": f"halueval-{i:06d}",
            "passage": r["knowledge"],
            "question": r["question"],
            "correct_answer": clean_answer(r["right_answer"]),
            "right_answer_raw": r["right_answer"],
            "wrong_source_text": r["hallucinated_answer"],
            "is_yesno": is_yesno(r["right_answer"]),
            "style": draw_style(style_rng),             # {"flavor": index into WARMTH_STYLES}
            "neutral_frame": draw_neutral_frame(frame_rng),  # index into NEUTRAL_FRAME_STYLES
            "source": "halueval_qa",
        })
    return out


def load_sciq_rows(n: int | None, seed: int) -> tuple[list[dict], dict]:
    """SciQ validation + test (plan §4.2, §5.1): drops rows with an empty support passage or whose
    correct answer is not in the support, picks ONE distractor per question with a fixed seed
    (stored as distractor_index), then samples n rows. Same row format as HaluEval, so the rest of
    the pipeline is identical; the chosen distractor plays the role of HaluEval's wrong answer."""
    raw = [(split, i, json.loads(l)) for split in ("validation", "test")
           for i, l in enumerate((SCIQ / f"{split}.jsonl").open(encoding="utf-8")) if l.strip()]
    drops = {"empty_support": 0, "answer_not_in_support": 0}
    pick_rng, rows = random.Random(0), []
    for split, i, r in raw:
        d = pick_rng.randrange(3) + 1  # drawn for every row so the choice doesn't depend on the filters
        if not r["support"].strip():
            drops["empty_support"] += 1
        elif r["correct_answer"].strip().lower() not in r["support"].lower():
            drops["answer_not_in_support"] += 1
        else:
            rows.append((split, i, r, d))
    idx = sorted(random.Random(seed).sample(range(len(rows)), n)) if n else list(range(len(rows)))
    style_rng, frame_rng = random.Random(seed + 2), random.Random(seed + 3)
    out = []
    for k in idx:
        split, i, r, d = rows[k]
        out.append({
            "qid": f"sciq-{split}-{i:04d}",
            "passage": r["support"],
            "question": r["question"],
            "correct_answer": clean_answer(r["correct_answer"]),
            "right_answer_raw": r["correct_answer"],
            "wrong_source_text": r[f"distractor{d}"].strip(),
            "distractor_index": d,
            "distractors": [r[f"distractor{k}"].strip() for k in (1, 2, 3)],
            "is_yesno": False,
            "style": draw_style(style_rng),
            "neutral_frame": draw_neutral_frame(frame_rng),
            "source": "sciq",
        })
    return out, drops


def sciq_distractors() -> dict:
    """qid -> the row's 3 human distractors (to backfill SciQ runs made before they were stored)."""
    return {f"sciq-{split}-{i:04d}": [r[f"distractor{k}"].strip() for k in (1, 2, 3)]
            for split in ("validation", "test")
            for i, r in enumerate(json.loads(l) for l in (SCIQ / f"{split}.jsonl").open(encoding="utf-8") if l.strip())}


# --------------------------------------------------------------------------- SciQ distractor rule
# SciQ is the OOD test set and its wrong answers must stay HUMAN-written (plan §4.2, §5.1). The
# writer starts from the randomly chosen distractor (same prompt as HaluEval); check V23 requires
# the wrong answer to be one of the row's 3 distractors (case and a leading article ignored), never
# one the writer made up. If V23 fails, the retry / repair feedback offers the other distractors.
# HaluEval rows have no "distractors" and are unaffected.
def distractor_match(row: dict, wrong: str) -> int | None:
    w = strip_article((wrong or "").strip()).lower()
    for k, d in enumerate(row.get("distractors") or [], 1):
        if w and w == strip_article(d).lower():
            return k
    return None


def sciq_alternatives(row: dict) -> str:
    return ", ".join(f'"{d}"' for k, d in enumerate(row["distractors"], 1) if k != row.get("distractor_index"))


def check_row_output(row: dict, raw: str) -> dict:
    """check_candidates + (SciQ only) V23. For SciQ, any of the 3 distractors counts as the text."""
    wrong_text = " | ".join(row["distractors"]) if row.get("distractors") else row["wrong_source_text"]
    res = check_candidates(raw, row["question"], row["correct_answer"], wrong_text)
    if row.get("distractors"):
        res["checks"]["V23"] = (distractor_match(row, res.get("wrong_phrase")) is not None
                                and res.get("wrong_source") == "text")
    return res


def row_passes(checks: dict) -> bool:
    return passes(checks) and checks.get("V23", True)


def explain_row_failures(row: dict, res: dict) -> str:
    checks = {k: v for k, v in res["checks"].items() if k != "V23"}
    text = explain_failures({**res, "checks": checks})
    if res["checks"].get("V23") is False:
        text += ("\n- For this question the incorrect answer must be one of these exact phrases written by a "
                 f'teacher (you may add "a", "an" or "the"): "{row["wrong_source_text"]}", {sciq_alternatives(row)}. '
                 'Prefer the first one; use another only if the first cannot work as a clearly wrong answer. Do not '
                 'write your own, and set "wrong_source" to "text".')
    return text.strip("\n")


def filter_rows(rows: list[dict]) -> tuple[list[dict], dict]:
    """Drops yes/no questions (their explanations contradict the swapped answer) and answers longer
    than MAX_ANSWER_WORDS (whole sentences)."""
    counts = {"yes_no": sum(r["is_yesno"] for r in rows),
              "long_answer": sum(len(r["correct_answer"].split()) > MAX_ANSWER_WORDS for r in rows if not r["is_yesno"])}
    kept = [r for r in rows if not r["is_yesno"] and len(r["correct_answer"].split()) <= MAX_ANSWER_WORDS]
    return kept, counts


# --------------------------------------------------------------------------- model call
# Models named "@provider/model" go through the NYU AI gateway (Portkey, OpenAI-compatible; needs
# PORTKEY_API_KEY and PORTKEY_BASE_URL in .env and the NYU network/VPN). Other names go to OpenAI.
def is_gateway(model: str) -> bool:
    return model.startswith("@")


def is_claude(model: str) -> bool:
    return "anthropic." in model or "claude" in model


def make_client(model: str) -> OpenAI:
    if is_gateway(model):
        key = os.environ["PORTKEY_API_KEY"]
        return OpenAI(base_url=os.environ["PORTKEY_BASE_URL"], api_key=key,
                      default_headers={"x-portkey-api-key": key}, max_retries=5)
    return OpenAI(max_retries=5)


def effective_effort(model: str, effort: str) -> str:
    """What is actually sent: Claude models get no reasoning parameter (no extended thinking)."""
    return "thinking off (Claude)" if is_claude(model) else effort


def _extract_json(text: str) -> str:
    """Claude may wrap JSON in ```json fences or add a sentence around it: keep the outermost {...}."""
    t = text.strip()
    if t.startswith("{") and t.endswith("}"):
        return t
    i, j = t.find("{"), t.rfind("}")
    return t[i:j + 1] if 0 <= i < j else t


# Thinking OFF for Claude: newer models think by default (Sonnet 5.5's thinking was ~80% of the
# writer's output tokens in the first pilot, ~5x the cost). Claude 5.x models turn it off with
# {"type": "between_tools"}, older ones with {"type": "disabled"}; the working value is remembered.
_THINKING_OFF: dict[str, str] = {}


def _claude_create(client: OpenAI, model: str, msgs: list[dict]):
    tried = [_THINKING_OFF[model]] if model in _THINKING_OFF else ["between_tools", "disabled"]
    for i, kind in enumerate(tried):
        try:
            resp = client.chat.completions.create(model=model, messages=msgs, max_tokens=2000,
                                                  extra_body={"thinking": {"type": kind}})
            _THINKING_OFF[model] = kind
            return resp
        except BadRequestError as e:
            if "thinking" not in str(e) or i == len(tried) - 1:
                raise


def call_model(client: OpenAI, model: str, effort: str, messages: list[dict],
               cache_key: str | None = None) -> tuple[str, dict, float]:
    t0 = time.time()
    if is_claude(model):
        # Claude via the gateway: max_tokens; no OpenAI-only params; the fixed system prompt is
        # marked for Anthropic prompt caching (it is identical on every call).
        msgs = [{**m, "content": [{"type": "text", "text": m["content"], "cache_control": {"type": "ephemeral"}}]}
                if m["role"] == "system" else m for m in messages]
        resp = _claude_create(client, model, msgs)
    else:
        extra = {"prompt_cache_key": cache_key} if cache_key else {}
        resp = client.chat.completions.create(model=model, messages=messages, response_format={"type": "json_object"},
                                              reasoning_effort=effort, max_completion_tokens=2000, **extra)
    u = resp.usage
    ptd, ctd = getattr(u, "prompt_tokens_details", None), getattr(u, "completion_tokens_details", None)
    extra_usage = (getattr(u, "model_extra", None) or {})
    usage = {"input": u.prompt_tokens,
             "cached_input": (getattr(ptd, "cached_tokens", 0) or 0) or extra_usage.get("cache_read_input_tokens", 0) or 0,
             "cache_write": extra_usage.get("cache_creation_input_tokens", 0) or 0,
             "output": u.completion_tokens,
             "reasoning": getattr(ctd, "reasoning_tokens", 0) or 0}
    return _extract_json(resp.choices[0].message.content or ""), usage, time.time() - t0


def process(row: dict, client: OpenAI, args, messages: list[dict] | None = None) -> dict:
    """Generates one row with up to args.max_retries validation retries. `messages` lets the repair
    step continue an existing conversation (previous answer + reviewer feedback)."""
    messages = messages or build_messages(row)
    attempts = []
    for _ in range(args.max_retries + 1):
        try:
            raw, usage, secs = call_model(client, args.model, args.reasoning_effort, messages,
                                          cache_key=f"rewriter-{PROMPT_VERSION}")
        except Exception as e:  # recorded, not fatal
            attempts.append({"error": f"{type(e).__name__}: {e}"})
            break
        res = check_row_output(row, raw)
        attempts.append({"raw": raw, "usage": usage, "seconds": round(secs, 2), "checks": res["checks"],
                         "flags": res["flags"], "candidate": res.get("candidate"),
                         "option_lengths": res.get("option_lengths")})
        if row_passes(res["checks"]):
            break
        feedback = explain_row_failures(row, res)
        attempts[-1]["feedback"] = feedback
        messages = messages + [
            {"role": "assistant", "content": raw},
            {"role": "user", "content": "Your answer has these problems:\n" + feedback +
             "\nFix only these problems, keep everything else the same, and return the full JSON object again."}]

    final = attempts[-1]
    record = {**row, "prompt_version": PROMPT_VERSION, "attempts": attempts,
              "passed": "checks" in final and row_passes(final["checks"])}
    if record["passed"]:
        parsed = res["parsed"]
        record.update(wrong_answer=res["wrong_phrase"], wrong_source=res["wrong_source"],
                      warm_tagged=parsed["warm"], neutral_candidates=res.get("passing_candidates") or [],
                      responses=swap(parsed["neutral"], parsed["warm"], row["correct_answer"], res["wrong_phrase"]))
        if row.get("distractors"):
            record["distractor_index"] = distractor_match(row, res["wrong_phrase"])  # may differ from the drawn one
    return record


# --------------------------------------------------------------------------- length balance
def balance_guard(after: dict, max_mean: float = 0.25, max_sign_share: float = 0.1) -> dict:
    """Plan §5.6: tone must not predict length. Mean warm-minus-neutral gap near 0, and warm-longer
    vs warm-shorter counts within 10% of the rows."""
    n = max(1, after["warm_longer"] + after["warm_shorter"] + after["equal"])
    ok_mean = abs(after["mean"]) <= max_mean
    ok_sign = abs(after["warm_longer"] - after["warm_shorter"]) / n <= max_sign_share
    return {"ok": ok_mean and ok_sign, "mean_ok": ok_mean, "sign_ok": ok_sign}


def apply_length_balance(records: list[dict]) -> dict:
    """Re-picks each passed row's (warm, neutral) pair among its passing pairs so that warm-minus-
    neutral length is balanced across the run; rebuilds the quartet where the choice changes."""
    rows = [r for r in records if r["passed"] and r.get("neutral_candidates")]
    if not rows:
        return {}
    before = []
    for r in rows:
        chosen = r["attempts"][-1].get("candidate")
        before.append(next((c["gap"] for c in r["neutral_candidates"] if c["index"] == chosen),
                           r["neutral_candidates"][0]["gap"]))
    choice = balance([r["neutral_candidates"] for r in rows])
    changed = 0
    for r, k in zip(rows, choice):
        cand = r["neutral_candidates"][k]
        changed += cand["index"] != r["attempts"][-1].get("candidate")
        r["balanced_candidate"] = cand["index"]
        r["responses"] = swap(cand["neutral"], cand["warm"], r["correct_answer"], r["wrong_answer"])
    after = gap_stats([r["neutral_candidates"][k]["gap"] for r, k in zip(rows, choice)])
    return {"rows_with_choice": sum(len(r["neutral_candidates"]) > 1 for r in rows), "rows_changed": changed,
            "before": gap_stats(before), "after": after, "guard": balance_guard(after)}


# --------------------------------------------------------------------------- diagnostics
WARM_WORDS = re.compile(r"curious|curiosity|love|enjoy|glad|happy|nice|great|fun|wonderful|lovely|pleasure|"
                        r"interesting|fascinating|wish|hope|thoughtful|delight|sharp|kind", re.IGNORECASE)
_YOU = re.compile(r"\byou(?:r|rs|rself)?\b|\byou(?:'|’)", re.IGNORECASE)


def warmth_score(quartets: list[dict]) -> dict:
    """Tone-contrast diagnostics: share of quartets whose CW / CN show each marker."""
    n = max(1, len(quartets))

    def share(side, f):
        return round(sum(bool(f(q["responses"][side]["text"])) for q in quartets) / n, 3)

    def signoff_only(t):  # answer sentence plain, warmth only in a separate closing sentence
        s = re.split(r"(?<=[.!?])\s+", t.strip())
        return len(s) >= 2 and not (_YOU.search(s[0]) or WARM_WORDS.search(s[0]))

    leadin = lambda t: any(t.strip().lower().startswith(l.lower()) for l in NEUTRAL_LEADINS)
    return {"CW_addresses_reader": share("CW", _YOU.search), "CN_addresses_reader": share("CN", _YOU.search),
            "CW_exclamation": share("CW", lambda t: "!" in t), "CN_exclamation": share("CN", lambda t: "!" in t),
            "CW_warm_words": share("CW", WARM_WORDS.search), "CN_warm_words": share("CN", WARM_WORDS.search),
            "CW_signoff_only": share("CW", signoff_only), "CW_neutral_leadin": share("CW", leadin)}


_FUNCTION_WORDS = {"the", "a", "an", "of", "in", "on", "at", "to", "for", "and", "is", "was", "by", "with",
                   "that", "its", "it", "as", "from", "were", "are", "be", "this", "which", "who", "s"}


def phrase_shares(texts: list[str], top: int = 10, flag_above: float = 0.10) -> dict:
    """Formula collapse anywhere in the sentence: top 2-4-word phrases by share of responses."""
    n = max(1, len(texts))
    counts = Counter()
    for t in texts:
        words = re.findall(r"[a-z']+", t.lower().replace("’", "'"))
        counts.update({" ".join(words[i:i + k]) for k in (2, 3, 4) for i in range(len(words) - k + 1)
                       if not all(w in _FUNCTION_WORDS for w in words[i:i + k])})
    kept = []
    for g, c in counts.most_common():
        if c < 2 or len(kept) == top:
            break
        if not any(c == c2 and g in g2 for g2, c2 in kept):
            kept.append((g, c))
    return {"top": [[g, round(c / n, 3)] for g, c in kept], "flagged": [g for g, c in kept if c / n > flag_above]}


def summarize(records: list[dict], args, balance_stats: dict, filtered: dict) -> dict:
    calls = [a for r in records for a in r["attempts"] if "usage" in a]
    tok = Counter()
    for a in calls:
        tok.update(a["usage"])
    first = [r["attempts"][0] for r in records if "checks" in r["attempts"][0]]
    passed = [r for r in records if r.get("responses")]
    openers = Counter(" ".join(r["responses"]["CW"]["text"].split()[:3]).rstrip(",:;.!—-") for r in passed)
    closers = Counter(" ".join(re.sub(r"[^\w\s]", "", r["responses"]["CW"]["text"].replace("’", "'")).lower().split()[-4:])
                      for r in passed)
    near_identical = sum(difflib.SequenceMatcher(None, r["responses"]["CN"]["text"], r["responses"]["CW"]["text"]).ratio() > 0.8
                         for r in passed)
    return {
        "model": args.model, "reasoning_effort": effective_effort(args.model, args.reasoning_effort),
        "prompt_version": PROMPT_VERSION,
        "seed": args.seed, "rows": len(records), "filtered": filtered,
        "api_calls": len(calls), "api_errors": sum(1 for r in records for a in r["attempts"] if "error" in a),
        "first_pass_validation_rate": round(sum(row_passes(a["checks"]) for a in first) / max(1, len(records)), 3),
        "final_pass_rate": round(len(passed) / max(1, len(records)), 3),
        "passed_on_attempt": dict(sorted(Counter(len(r["attempts"]) for r in passed).items())),
        "first_pass_failures_by_check": dict(Counter(k for a in first for k, v in a["checks"].items() if not v).most_common()),
        "final_failures_by_check": dict(Counter(k for r in records if not r["passed"] and "checks" in r["attempts"][-1]
                                                for k, v in r["attempts"][-1]["checks"].items() if not v and k != "V12").most_common()),
        "tokens": dict(tok),
        "wrong_source_of_passed": dict(Counter(r["wrong_source"] for r in passed)),
        "warm_near_identical_to_neutral": f"{near_identical}/{len(passed)}",
        "length_balance": balance_stats,
        "warmth_score": warmth_score(passed),
        "phrase_shares": {side: phrase_shares([r["responses"][side]["text"] for r in passed]) for side in ("CW", "CN")},
        "top_opener_share": round(openers.most_common(1)[0][1] / len(passed), 3) if passed else None,
        "top_closer_share": round(closers.most_common(1)[0][1] / len(passed), 3) if passed else None,
    }


def write_preview(records: list[dict], path: Path) -> None:
    lines = ["# Generation preview\n"]
    for r in records:
        lines.append(f"## {r['qid']} {'PASS' if r['passed'] else 'FAIL'}\n")
        lines.append(f"**Q:** {r['question']}  ")
        lines.append(f"**Right:** {r['correct_answer']} · **Hallucinated text:** {r['wrong_source_text']}  ")
        lines.append(f"**Warmth style:** {WARMTH_STYLES[r['style']['flavor']]}  ")
        lines.append(f"**Neutral frame:** {NEUTRAL_FRAME_STYLES[r['neutral_frame']]} · **Attempts:** {len(r['attempts'])}\n")
        if r.get("responses"):
            lines += [f"- **{c}:** {r['responses'][c]['text']}" for c in ("CN", "CW", "IN", "IW")]
        else:
            last = r["attempts"][-1]
            lines.append(f"- failed: {[k for k, v in last.get('checks', {}).items() if not v] or last.get('error')}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def model_slug(model: str) -> str:
    """'@vertexai/anthropic.claude-opus-4-8' -> 'claude-opus-4-8'; plain OpenAI names unchanged."""
    return model.split("/")[-1].replace("anthropic.", "").replace("@", "-")


QUARTET_KEYS = ("qid", "passage", "question", "correct_answer", "right_answer_raw", "wrong_answer", "wrong_source",
                "wrong_source_text", "distractor_index", "distractors", "style", "neutral_frame", "responses", "source")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", choices=("halueval", "sciq"), default="halueval")
    p.add_argument("--n", type=int, default=None, help="number of rows to sample (default: all)")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--model", default="@vertexai/anthropic.claude-sonnet-5-5")
    p.add_argument("--reasoning-effort", default="low")
    p.add_argument("--max-retries", type=int, default=2)
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--out-root", type=Path, default=OUT_ROOT)
    p.add_argument("--chunk", type=int, default=None,
                   help="full build: run only chunk K (1-based) of the filtered rows, shuffled with seed+4")
    p.add_argument("--chunk-size", type=int, default=2500)
    p.add_argument("--out-dir", type=Path, default=None,
                   help="fixed output folder; re-running with the same folder RESUMES from its checkpoint")
    p.add_argument("--limit", type=int, default=None,
                   help="keep only the first LIMIT rows after filtering (e.g. --n 100 --limit 50 = first 50 of the "
                        "same sample as a 100-row run)")
    args = p.parse_args()

    if args.dataset == "sciq":
        sciq_rows, sciq_drops = load_sciq_rows(args.n, args.seed)
        rows, filtered = filter_rows(sciq_rows)
        filtered = {**sciq_drops, **filtered}
    else:
        rows, filtered = filter_rows(load_rows(args.n, args.seed))
    if args.chunk:
        random.Random(args.seed + 4).shuffle(rows)  # chunks are random samples, not HaluEval file order
        n_chunks = -(-len(rows) // args.chunk_size)
        rows = rows[(args.chunk - 1) * args.chunk_size: args.chunk * args.chunk_size]
        print(f"chunk {args.chunk}/{n_chunks}")
    if args.limit:
        rows = rows[:args.limit]
    print(f"{len(rows)} rows after filtering {filtered}")
    prefix = "sciq_" if args.dataset == "sciq" else ""
    out_dir = args.out_dir or args.out_root / f"{prefix}{model_slug(args.model)}_{PROMPT_VERSION}_{datetime.now():%Y%m%d-%H%M%S}"
    out_dir.mkdir(parents=True, exist_ok=True)
    client = make_client(args.model)
    records = run_checkpointed(rows, lambda r: r["qid"], lambda r: process(r, client, args),
                               out_dir / "partial.jsonl", args.workers, args.model, no_api_error)
    records.sort(key=lambda r: r["qid"])
    balance_stats = apply_length_balance(records)
    if balance_stats and not balance_stats["guard"]["ok"]:
        print("\n!!! LENGTH BALANCE GUARD FAILED:", balance_stats["after"], "\n")

    with (out_dir / "calls.jsonl").open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (out_dir / "quartets.jsonl").open("w", encoding="utf-8") as f:
        for r in records:
            if r["passed"]:
                q = {k: r.get(k) for k in QUARTET_KEYS}
                q.update(rewriter={"model": args.model, "prompt_version": PROMPT_VERSION,
                                                         "retries": len(r["attempts"]) - 1})
                f.write(json.dumps(q, ensure_ascii=False) + "\n")
    write_preview(records, out_dir / "preview.md")
    summary = summarize(records, args, balance_stats, filtered)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: summary[k] for k in ("rows", "final_pass_rate", "api_calls", "tokens", "length_balance")}, indent=2))
    print(out_dir)  # last line: the run folder, for scripts


if __name__ == "__main__":
    main()
