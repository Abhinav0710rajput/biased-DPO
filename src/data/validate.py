"""Rule-based checks for one quartet, candidate selection, and the answer swap.
See Docs/data_pipeline.md (section "Code checks") for the rationale of every rule.

The writer returns: wrong_phrase, wrong_source, core, neutral, warm_options (3 warm versions).
Every (warm option, neutral) pair, plus (warm option, core) pairs, is checked with check_row();
check_candidates() keeps the passing pairs and picks the closest in length (then the least
similar). V1-V13 follow project_plan.md §5.4; V14-V22 were added during the pilots.
V12 only flags (never rejects). V8 counts whitespace words until the policy tokenizer is chosen.
"""

import difflib
import json
import re

from prompts import NEUTRAL_LEADINS

ANS_RE = re.compile(r"<ans>(.*?)</ans>", re.DOTALL)
YESNO = {"yes", "no"}
LENGTH_TOLERANCE = 2               # V8: |warm - neutral| words per row (plus 10% of the longer)
MAX_WARM_NEUTRAL_SIMILARITY = 0.8  # V18

HEDGES = ["i think", "i believe", "probably", "maybe", "might", "perhaps",
          "definitely", "certainly", "surely", "undoubtedly",
          "clearly", "in fact", "indeed", "precisely", "to be exact"]
SOURCE_REFS = ["passage", "according to", "the text", "the context", "the source", "prompt", "as stated"]
NEUTRAL_BANNED = ["hope", "happy to", "great question", "glad"]
NEUTRAL_META = ["the question", "asked", "in this comparison", "mentioned", "sought", "in this case", "here"]
CONTRASTS = ["rather than", "instead of", "not elsewhere", "as opposed to"]
LEADING_FUNCTION_WORDS = {"a", "an", "the", "in", "on", "at", "of", "by", "from", "to", "for", "with"}
ARTICLES = ("the", "a", "an")

# Abbreviations whose final period is part of the answer ("Washington, D.C.", "Jr.", "Inc.").
_ABBREV_END = re.compile(r"(?:\b(?:[A-Z]\.){2,}|\b(?:Jr|Sr|St|Co|Corp|Inc|Ltd|Bros|Mt|Dr|Mr|Mrs|Ms|No|vs|etc)\.)$")


def clean_answer(answer: str) -> str:
    """Data filter: strip stray trailing punctuation from a right answer ('... programmes.' made
    'programmes..' in the pilot), but keep an abbreviation's period ('Washington, D.C.')."""
    a = answer.strip()
    if _ABBREV_END.search(a):
        return a
    return a.rstrip(".,;:!?").strip()


def norm(s: str) -> str:
    return re.sub(r"[^\w\s]", "", s.lower()).strip()


def is_yesno(right_answer: str) -> bool:
    return right_answer.strip().lower() in YESNO


def strip_article(phrase: str) -> str:
    """'the Korean War' -> 'Korean War' (answers carry their own article inside the slot)."""
    w = phrase.split(maxsplit=1)
    return w[1] if len(w) == 2 and w[0].lower() in ARTICLES else phrase


def _has_phrase(text: str, phrases: list[str]) -> bool:
    t = text.lower()
    return any(re.search(r"\b" + re.escape(p) + r"\b", t) for p in phrases)


def _new_fact_tokens(text: str, question: str, answer: str) -> list[str]:
    """Digits or capitalized words absent from question + answer (sentence-initial words excepted)."""
    allowed = (question + " " + answer).lower()
    plain = ANS_RE.sub(" ", text)
    hits = []
    for sent in re.split(r"(?<=[.!?])\s+", plain.strip()):
        words = sent.split()
        for i, w in enumerate(words):
            core = re.sub(r"^[^\w]+|[^\w]+$", "", w)
            if core and (re.search(r"\d", core) or (i > 0 and core[0].isupper())) and core.lower() not in allowed:
                hits.append(core)
    return hits


def dropin_problems(wrong: str, right: str) -> list[str]:
    """V14: is the wrong phrase a drop-in substitute for the right answer? Compared without
    their articles ("the Korean War" vs "World War II")."""
    wrong, right = strip_article(wrong), strip_article(right)
    w, r = wrong.split(), right.split()
    problems = []
    if len(w) > max(2 * len(r), len(r) + 3):
        problems.append("too long")
    if w[0].lower() in LEADING_FUNCTION_WORDS and w[0].lower() != r[0].lower() and w[0].lower() not in ARTICLES:
        problems.append(f'starts with "{w[0]}"')
    if bool(re.search(r"\d", wrong)) != bool(re.search(r"\d", right)):
        problems.append("one has digits and the other does not")
    if right[:1].isupper() and wrong[:1].islower():
        problems.append("lowercase where the answer is capitalized")
    return problems


def check_row(raw_output: str, question: str, right_answer: str, wrong_text: str, count_tokens=None) -> dict:
    """Checks one (warm, neutral) pair given as JSON with fields wrong_phrase, wrong_source, warm,
    neutral. Returns {"checks": {Vk: bool}, "flags", "parsed", "wrong_phrase", "wrong_source",
    "lengths", "similarity"}."""
    count = count_tokens or (lambda s: len(s.split()))
    checks, flags = {}, []

    # V1: valid JSON with the needed fields
    try:
        parsed = json.loads(raw_output)
        ok = isinstance(parsed, dict) and {"wrong_phrase", "neutral", "warm"} <= parsed.keys() \
            and isinstance(parsed["neutral"], str) and isinstance(parsed["warm"], str)
    except (json.JSONDecodeError, TypeError):
        parsed, ok = None, False
    checks["V1"] = ok
    if not ok:
        return {"checks": checks, "flags": ["unparseable"], "parsed": parsed, "wrong_phrase": None}

    neutral, warm = parsed["neutral"], parsed["warm"]
    wrong = parsed["wrong_phrase"]
    # Strip surrounding quotes and trailing punctuation ("Song Hye-Kyo." -> "Song Hye-Kyo").
    wrong = wrong.strip().strip("\"'“”‘’").rstrip(".,;:!?").strip() if isinstance(wrong, str) else None
    wrong_source = "generated" if parsed.get("wrong_source") == "generated" else "text"

    # V2-V4: the wrong answer exists, is copied from the text (if text-sourced), differs from the right one
    checks["V2"] = bool(wrong)
    checks["V3"] = bool(wrong) and (wrong_source != "text" or wrong.lower() in wrong_text.lower()
                                    or strip_article(wrong).lower() in wrong_text.lower())
    wn, rn = (norm(strip_article(wrong)) if wrong else ""), norm(strip_article(right_answer))
    checks["V4"] = bool(wrong) and wn != rn and wn not in rn and rn not in wn

    # V5-V7: exactly one answer slot, holding the right answer (optionally with its own article), not first
    tags = {k: ANS_RE.findall(v) for k, v in (("neutral", neutral), ("warm", warm))}
    checks["V5"] = all(len(t) == 1 for t in tags.values())

    def slot_ok(t: str) -> bool:
        return t == right_answer or (strip_article(t) == right_answer and t.split()[0].lower() in ARTICLES)
    checks["V6"] = checks["V5"] and all(slot_ok(t[0]) for t in tags.values())
    checks["V7"] = all(not re.match(r"^\W*<ans>", v) for v in (neutral, warm))

    # V8: warm and neutral lengths match per row
    n_plain, w_plain = ANS_RE.sub(r"\1", neutral), ANS_RE.sub(r"\1", warm)
    tn, tw = count(n_plain), count(w_plain)
    checks["V8"] = abs(tn - tw) <= max(LENGTH_TOLERANCE, 0.1 * max(tn, tw))

    # V9-V11: no hedges/boosters; no references to a source; neutral has no "!" or greeting words
    checks["V9"] = not (_has_phrase(n_plain, HEDGES) or _has_phrase(w_plain, HEDGES))
    checks["V10"] = not (_has_phrase(n_plain, SOURCE_REFS) or _has_phrase(w_plain, SOURCE_REFS))
    checks["V11"] = "!" not in neutral and not _has_phrase(n_plain, NEUTRAL_BANNED)

    # V12 (flag only) / V19 (reject): possible added facts; added numbers or dates are rejected
    new_facts = _new_fact_tokens(neutral, question, right_answer) + _new_fact_tokens(warm, question, right_answer)
    checks["V12"] = not new_facts
    if new_facts:
        flags.append("V12_possible_new_facts: " + ", ".join(sorted(set(new_facts))))
    checks["V19"] = not any(re.search(r"\d", t) for t in new_facts)

    # V13 / V21: no article directly before the slot (it belongs inside, so the swap replaces it)
    checks["V13"] = not re.search(r"\b(a|an)\s+<ans>", neutral + " " + warm, re.IGNORECASE)
    checks["V21"] = not re.search(r"\b(the|a|an)\s+<ans>", neutral + " " + warm, re.IGNORECASE)

    # V14: the wrong phrase is a drop-in substitute (length, leading words, digits, capitalization)
    checks["V14"] = bool(wrong) and not dropin_problems(wrong, right_answer)

    # V15: no padding about the question in the neutral version; no contrasts in either
    checks["V15"] = not _has_phrase(n_plain, NEUTRAL_META) \
        and not (_has_phrase(n_plain, CONTRASTS) or _has_phrase(w_plain, CONTRASTS))

    # V16 / V17: neither answer appears outside the slot (unless the question itself names it)
    outside = (ANS_RE.sub(" ", neutral) + " " + ANS_RE.sub(" ", warm)).lower()
    checks["V16"] = not (wrong and wrong.lower() not in question.lower()
                         and re.search(r"\b" + re.escape(wrong.lower()) + r"\b", outside))
    checks["V17"] = not (right_answer.lower() not in question.lower()
                         and re.search(r"\b" + re.escape(right_answer.lower()) + r"\b", outside))

    # V18: the warm version is not the neutral one with a greeting glued on
    similarity = difflib.SequenceMatcher(None, n_plain, w_plain).ratio()
    checks["V18"] = similarity <= MAX_WARM_NEUTRAL_SIMILARITY

    # V22: the warm version does not open with a neutral lead-in, nor affirm a guess ("You're right")
    w_low = w_plain.strip().lower()
    checks["V22"] = not (any(w_low.startswith(l.lower()) for l in NEUTRAL_LEADINS)
                         or re.search(r"\byou(?:'|’)re right\b|\byou are right\b|\byou were right\b", w_low))

    return {"checks": checks, "flags": flags, "parsed": parsed, "wrong_phrase": wrong,
            "wrong_source": wrong_source, "lengths": {"warm": tw, "neutral": tn}, "similarity": round(similarity, 3)}


# V12 only flags; every other check rejects.
HARD_CHECKS = ["V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "V10", "V11", "V13", "V14", "V15",
               "V16", "V17", "V18", "V19", "V21", "V22"]


def passes(checks: dict) -> bool:
    return all(checks.get(k, False) for k in HARD_CHECKS)


def check_candidates(raw_output: str, question: str, right_answer: str, wrong_text: str, count_tokens=None) -> dict:
    """Checks every (warm option, neutral) pair, the core sentence also serving as a neutral.
    Returns check_row's result for the chosen pair (closest in length, then least similar), plus
    "candidate" (pair index), "option_lengths" (warm option lengths, for retry feedback) and
    "passing_candidates" (all passing pairs, for dataset-level length balancing)."""
    try:
        parsed = json.loads(raw_output)
    except (json.JSONDecodeError, TypeError):
        parsed = None
    warm_opts = parsed.get("warm_options") if isinstance(parsed, dict) else None
    if not (isinstance(warm_opts, list) and warm_opts and all(isinstance(w, str) for w in warm_opts)
            and isinstance(parsed.get("neutral"), str)):
        return check_row(raw_output, question, right_answer, wrong_text, count_tokens)  # fails V1

    neutrals = [parsed["neutral"]] + ([parsed["core"]] if isinstance(parsed.get("core"), str) else [])
    pairs = [(w, n) for n in neutrals for w in warm_opts]
    base = {k: v for k, v in parsed.items() if k not in ("warm_options", "core", "neutral", "warm")}
    results = [check_row(json.dumps({**base, "warm": w, "neutral": n}), question, right_answer, wrong_text,
                         count_tokens) for w, n in pairs]

    def gap(r):
        return abs(r["lengths"]["warm"] - r["lengths"]["neutral"]) if "lengths" in r else 10**6

    passing = [i for i, r in enumerate(results) if passes(r["checks"])]
    if passing:
        best = min(passing, key=lambda i: (gap(results[i]), results[i].get("similarity", 1)))
    else:  # fewest failed checks, then closest length: the best basis for retry feedback
        best = min(range(len(results)), key=lambda i: (
            sum(not results[i]["checks"].get(k, False) for k in HARD_CHECKS), gap(results[i])))
    res = dict(results[best])
    res["candidate"] = best
    res["option_lengths"] = [r["lengths"]["warm"] for r in results[:len(warm_opts)] if "lengths" in r]
    res["passing_candidates"] = [
        {"index": i, "neutral": pairs[i][1], "warm": pairs[i][0],
         "gap": results[i]["lengths"]["warm"] - results[i]["lengths"]["neutral"],
         "similarity": results[i]["similarity"]}
        for i in passing]
    return res


# Retry feedback: the writer does not know what "V8" means.
FAILURE_MESSAGES = {
    "V1": "Return one valid JSON object with exactly the fields listed in the instructions, in the "
          "same format as the examples.",
    "V2": '"wrong_phrase" was null or empty. Copy a drop-in wrong answer from the incorrect answer '
          'text, or, if it has none, write your own and set "wrong_source" to "generated".',
    "V3": '"wrong_phrase" is not copied exactly from the incorrect answer text. Copy it word for word, '
          'or, if you wrote it yourself, set "wrong_source" to "generated".',
    "V4": '"wrong_phrase" must be a different answer from the correct answer, and neither may '
          "contain the other.",
    "V5": "Each version must contain exactly one <ans>...</ans> tag.",
    # Retry messages are kept word-for-word as in the frozen v3.3 pilot (wording affects the writer).
    "V6": "The text inside <ans>...</ans> must be exactly the correct answer as given (in v3.1+, optionally "
          "preceded by \"the\", \"a\" or \"an\" inside the tags).",
    "V7": "Do not start either version with the answer.",
    "V9": 'Remove hedging or certainty words ("probably", "might", "definitely", "certainly", ...).',
    "V10": 'Do not mention a passage, text, source, context or prompt ("as stated").',
    "V11": 'The neutral version must have no "!" and no greeting or closing words '
           '("hope", "happy to", "glad", "great question").',
    "V13": 'Do not put "a" or "an" directly before <ans>.',
    "V14": '"wrong_phrase" must be a drop-in substitute for the correct answer: the same kind of '
           "thing in the same form, only the phrase itself (no leading words like \"in\" or \"the\"). "
           "If the incorrect answer text has no such phrase, write your own and set "
           '"wrong_source" to "generated".',
    "V15": 'Do not pad the neutral version by talking about the question ("the question", "asked", "here", '
           '"mentioned"); restate its content instead. Do not contrast the answer with alternatives '
           '("rather than", "instead of", "not elsewhere").',
    "V16": "Do not mention the wrong answer anywhere in either version.",
    "V17": "Mention the correct answer only once, inside the <ans> tags; do not repeat it elsewhere.",
    "V18": "Your warm version reads almost the same as the neutral one. Reword the warm answer sentence "
           "itself warmly, speaking to the reader, instead of only adding a greeting or sign-off.",
    "V19": "Do not add numbers or dates that are not in the question.",
    "V21": 'Put any article INSIDE the tags: write "in <ans>the United States</ans>", not "in the '
           '<ans>United States</ans>". Give the wrong answer its own article only if it needs one '
           '("the Korean War", "Canada").',
    "V22": 'Do not start a warm version with a neutral lead-in ("In summary", "In brief", "For reference", '
           '"Regarding", "To summarize"), and never say "You\'re right": the reader did not guess.',
}


def explain_failures(res: dict) -> str:
    lines = []
    for k, ok in res["checks"].items():
        if ok or k == "V12":
            continue
        if k == "V8":
            n = res["lengths"]
            lines.append(f"Your neutral version has {n['neutral']} words, but none of your warm versions "
                         f"is within {LENGTH_TOLERANCE} words of it (they have "
                         f"{', '.join(str(x) for x in res.get('option_lengths', [n['warm']]))} words). Write three "
                         f"new warm options of about {n['neutral'] + 2}, {n['neutral']} and {n['neutral'] - 2} "
                         f"words, by shortening the warmth element or referring back to the question's details "
                         f"briefly. Do not pad.")
        else:
            lines.append(FAILURE_MESSAGES[k])
    return "\n".join(f"- {line}" for line in lines)


def swap(neutral: str, warm: str, right_answer: str, wrong_phrase: str) -> dict:
    """Builds CN/CW/IN/IW with answer character spans (plan §5.5). Correct versions keep the slot
    text (the right answer, possibly with its own article); incorrect versions get the wrong
    phrase (with ITS own article)."""
    out = {}
    for code, text, wrong in (("CN", neutral, False), ("CW", warm, False), ("IN", neutral, True), ("IW", warm, True)):
        m = ANS_RE.search(text)
        start = m.start()
        ans = wrong_phrase if wrong else m.group(1)
        out[code] = {"text": text[:start] + ans + text[m.end():], "ans_span": [start, start + len(ans)]}
    return out
