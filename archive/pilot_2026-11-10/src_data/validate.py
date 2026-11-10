"""Automatic checks V1–V24 (V1–V13 from project_plan.md §5.4; V14–V24 added) and the code swap (§5.5).

V8 (length match) is meant to use the policy model's tokenizer. The policy model is TBD,
so `check_row` falls back to whitespace word counts unless a `count_tokens` function is given.
"""

import difflib
import json
import re

from prompts import NEUTRAL_LEADINS

ANS_RE = re.compile(r"<ans>(.*?)</ans>", re.DOTALL)
YESNO = {"yes", "no"}
MAX_WARM_NEUTRAL_SIMILARITY = 0.8  # V18

HEDGES = ["i think", "i believe", "probably", "maybe", "might", "perhaps",
          "definitely", "certainly", "surely", "undoubtedly",
          # added with v2.7 neutral frames: frames must not add certainty
          "clearly", "in fact", "indeed", "precisely", "to be exact"]
SOURCE_REFS = ["passage", "according to", "the text", "the context", "the source", "prompt", "as stated"]
NEUTRAL_BANNED = ["hope", "happy to", "great question", "glad"]
NEUTRAL_META = ["the question", "asked", "in this comparison", "mentioned", "sought", "in this case", "here"]
CONTRASTS = ["rather than", "instead of", "not elsewhere", "as opposed to"]


# Abbreviations whose final period is part of the answer ("Washington, D.C.", "Jr.", "Inc.").
_ABBREV_END = re.compile(r"(?:\b(?:[A-Z]\.){2,}|\b(?:Jr|Sr|St|Co|Corp|Inc|Ltd|Bros|Mt|Dr|Mr|Mrs|Ms|No|vs|etc)\.)$")


def clean_answer(answer: str) -> str:
    """Data filter (plan §5.1): strip stray trailing punctuation from a right answer, e.g.
    'natural history and documentary programmes.' (it produced 'programmes..' in the v3.3 pilot),
    but keep the period of an abbreviation ('Washington, D.C.')."""
    a = answer.strip()
    if _ABBREV_END.search(a):
        return a
    return a.rstrip(".,;:!?").strip()


def norm(s: str) -> str:
    return re.sub(r"[^\w\s]", "", s.lower()).strip()


def is_yesno(right_answer: str) -> bool:
    return right_answer.strip().lower() in YESNO


def yesno_wrong(right_answer: str) -> str:
    return "no" if right_answer.strip().lower() == "yes" else "yes"


def _has_phrase(text: str, phrases: list[str]) -> bool:
    t = text.lower()
    return any(re.search(r"\b" + re.escape(p) + r"\b", t) for p in phrases)


def _new_fact_tokens(text: str, question: str, answer: str) -> list[str]:
    """V12 heuristic: digits or capitalized words absent from question + answer (sentence-initial excepted)."""
    allowed = (question + " " + answer).lower()
    plain = ANS_RE.sub(" ", text)
    hits = []
    for sent in re.split(r"(?<=[.!?])\s+", plain.strip()):
        words = sent.split()
        for i, w in enumerate(words):
            core = re.sub(r"^[^\w]+|[^\w]+$", "", w)
            if not core:
                continue
            if re.search(r"\d", core) or (i > 0 and core[0].isupper()):
                if core.lower() not in allowed:
                    hits.append(core)
    return hits


LEADING_FUNCTION_WORDS = {"a", "an", "the", "in", "on", "at", "of", "by", "from", "to", "for", "with"}


ARTICLES = ("the", "a", "an")


def strip_article(phrase: str) -> str:
    """'the Korean War' -> 'Korean War' (v3.1: answers may carry their own article in the slot)."""
    w = phrase.split(maxsplit=1)
    return w[1] if len(w) == 2 and w[0].lower() in ARTICLES else phrase


def dropin_problems(wrong: str, right: str, article_in_slot: bool = False) -> list[str]:
    """V14 (added; not in plan §5.4): is the wrong phrase a drop-in substitute for the right answer?
    Catches 'in 2003' for '22 July 2002', 'a French tenor' for a name, whole sentences."""
    problems = []
    if article_in_slot:  # judge the phrases themselves, not their articles ("the Korean War" vs "World War II")
        wrong, right = strip_article(wrong), strip_article(right)
    w, r = wrong.split(), right.split()
    if len(w) > max(2 * len(r), len(r) + 3):
        problems.append("too long")
    if (w[0].lower() in LEADING_FUNCTION_WORDS and w[0].lower() != r[0].lower()
            and not (article_in_slot and w[0].lower() in ARTICLES)):
        problems.append(f'starts with "{w[0]}"')
    if bool(re.search(r"\d", wrong)) != bool(re.search(r"\d", right)):
        problems.append("one has digits and the other does not")
    if right[:1].isupper() and wrong[:1].islower():
        problems.append("lowercase where the answer is capitalized")
    return problems


def check_row(raw_output: str, question: str, right_answer: str, wrong_text: str,
              count_tokens=None, max_neutral_tail: int | None = None, length_tolerance: int = 2,
              article_in_slot: bool = False, warm_tone_checks: bool = False,
              require_address: bool | None = None, banned_warm: dict | None = None) -> dict:
    """Returns {"checks": {V1..V20: bool}, "flags", "parsed", "wrong_phrase", "wrong_source", "lengths"}.
    max_neutral_tail: V20 limit on words after the answer in the neutral version (None = no limit).
    length_tolerance: V8 per-row limit on |warm - neutral| words (plan §5.4: 2; option C pilot: 4)."""
    count = count_tokens or (lambda s: len(s.split()))
    checks, flags = {}, []

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
    wrong = yesno_wrong(right_answer) if is_yesno(right_answer) else parsed["wrong_phrase"]
    # Strip surrounding quotes and trailing punctuation ("Song Hye-Kyo." -> "Song Hye-Kyo").
    wrong = wrong.strip().strip("\"'“”‘’").rstrip(".,;:!?").strip() if isinstance(wrong, str) else None
    # v2.1+: the rewriter may generate a wrong answer when the text has none ("generated").
    # Prompts before v2.1 have no such field: their wrong phrase is always from the text.
    if is_yesno(right_answer):
        wrong_source = "rule"
    else:
        wrong_source = "generated" if parsed.get("wrong_source") == "generated" else "text"

    checks["V2"] = bool(wrong)
    # V3 (copied verbatim from the incorrect text) applies only to text-sourced wrong phrases.
    checks["V3"] = bool(wrong) and (wrong_source != "text" or wrong.lower() in wrong_text.lower()
                                    or (article_in_slot and strip_article(wrong).lower() in wrong_text.lower()))
    wn, rn = (norm(strip_article(wrong)) if wrong else "", norm(strip_article(right_answer))) if article_in_slot \
        else (norm(wrong) if wrong else "", norm(right_answer))
    checks["V4"] = bool(wrong) and wn != rn and wn not in rn and rn not in wn

    tags = {k: ANS_RE.findall(v) for k, v in (("neutral", neutral), ("warm", warm))}
    checks["V5"] = all(len(t) == 1 for t in tags.values())
    def slot_ok(t: str) -> bool:
        if t == right_answer:
            return True
        # v3.1: "<ans>the United States</ans>" for answer "United States" (article inside the slot)
        return article_in_slot and strip_article(t) == right_answer and t.split()[0].lower() in ARTICLES
    checks["V6"] = checks["V5"] and all(slot_ok(t[0]) for t in tags.values())
    checks["V7"] = all(not re.match(r"^\W*<ans>", v) for v in (neutral, warm))

    n_plain, w_plain = ANS_RE.sub(r"\1", neutral), ANS_RE.sub(r"\1", warm)
    tn, tw = count(n_plain), count(w_plain)
    checks["V8"] = abs(tn - tw) <= max(length_tolerance, 0.1 * max(tn, tw))

    checks["V9"] = not (_has_phrase(n_plain, HEDGES) or _has_phrase(w_plain, HEDGES))
    checks["V10"] = not (_has_phrase(n_plain, SOURCE_REFS) or _has_phrase(w_plain, SOURCE_REFS))
    checks["V11"] = "!" not in neutral and not _has_phrase(n_plain, NEUTRAL_BANNED)

    new_facts = _new_fact_tokens(neutral, question, right_answer) + _new_fact_tokens(warm, question, right_answer)
    checks["V12"] = not new_facts
    if new_facts:
        flags.append("V12_possible_new_facts: " + ", ".join(sorted(set(new_facts))))
    # V19 (added): V12 only flags, but a number/date the question does not contain ("mid-1850s",
    # "93-mile") is almost always an added fact, so reject those.
    checks["V19"] = not any(re.search(r"\d", t) for t in new_facts)
    # V20 (added, v2.9+): at most N words after the answer in the neutral version. In pilots, neutral
    # versions with 3+ words after the answer were rejected by the judge for filler ~50% of the time
    # ("...in July 1994 during that period"), vs ~5-9% for those ending at the answer.
    m_tail = re.search(r"</ans>(.*)$", neutral, re.DOTALL)
    tail_words = len(re.sub(r"[^\w\s]", " ", m_tail.group(1)).split()) if m_tail else 0
    checks["V20"] = max_neutral_tail is None or tail_words <= max_neutral_tail
    neutral_tail = tail_words

    checks["V13"] = not re.search(r"\b(a|an)\s+<ans>", neutral + " " + warm, re.IGNORECASE)
    checks["V14"] = bool(wrong) and (is_yesno(right_answer) or not dropin_problems(wrong, right_answer, article_in_slot))
    # V21 (v3.1+): no article directly before the slot: it belongs INSIDE, so the swap replaces it
    # too ("in the <ans>United States</ans>" -> "in the Canada" was ~half the grammar rejections).
    checks["V21"] = not article_in_slot or not re.search(r"\b(the|a|an)\s+<ans>", neutral + " " + warm, re.IGNORECASE)
    # V22 / V23 (v3.2+): a clear tone contrast. CW must not open with a neutral lead-in or affirm a
    # guess the reader never made ("You're right"), and must address the reader ("you"/"your").
    w_low = w_plain.strip().lower()
    checks["V22"] = not warm_tone_checks or not (
        any(w_low.startswith(l.lower()) for l in NEUTRAL_LEADINS)
        or re.search(r"\byou(?:'|’)re right\b|\byou are right\b|\byou were right\b", w_low))
    if require_address is None:  # v3.2 behaviour: V23 on whenever the tone checks are on
        require_address = warm_tone_checks
    # V24 (v3.4+): overused phrases, enforced in code (they used to be listed in the prompt only).
    # Openers are checked at the start of the warm version; closings and formulas anywhere.
    checks["V24"] = True
    if banned_warm:
        w_norm = w_plain.replace("’", "'").strip().lower()
        hit = [o for o in banned_warm.get("openers", []) if w_norm.startswith(o.lower())]
        hit += [ph for ph in banned_warm.get("anywhere", [])
                if re.search(r"\b" + re.escape(ph.lower()) + r"\b", w_norm)]
        checks["V24"] = not hit
        if hit:
            flags.append("V24_overused: " + ", ".join(hit))
    checks["V23"] = not require_address or bool(re.search(r"\byou(?:r|rs|rself)?\b|\byou(?:'|’)", w_low))

    # V15 (added): no padding about the question in the neutral version, no contrasts in either.
    checks["V15"] = not _has_phrase(n_plain, NEUTRAL_META) \
        and not (_has_phrase(n_plain, CONTRASTS) or _has_phrase(w_plain, CONTRASTS))

    # V16 (added): the wrong answer must not appear outside the answer slot, or the swap produces
    # "...is Isola rather than Isola". Allowed when the question itself names it (e.g. "A or B?").
    checks["V16"] = True
    if wrong and not is_yesno(right_answer) and wrong.lower() not in question.lower():
        outside = ANS_RE.sub(" ", neutral) + " " + ANS_RE.sub(" ", warm)
        checks["V16"] = not re.search(r"\b" + re.escape(wrong.lower()) + r"\b", outside.lower())

    # V17 (added): the correct answer must not appear outside its tag either, or the swap produces
    # "founded in 2005 in the year 2004". Allowed when the question itself contains it.
    checks["V17"] = True
    if not is_yesno(right_answer) and right_answer.lower() not in question.lower():
        outside = ANS_RE.sub(" ", neutral) + " " + ANS_RE.sub(" ", warm)
        checks["V17"] = not re.search(r"\b" + re.escape(right_answer.lower()) + r"\b", outside.lower())

    # V18 (added): warmth must be more than a greeting/sign-off glued onto the neutral sentence.
    # Same metric as the summary's warm_near_identical_to_neutral diagnostic.
    similarity = difflib.SequenceMatcher(None, n_plain, w_plain).ratio()
    checks["V18"] = similarity <= MAX_WARM_NEUTRAL_SIMILARITY

    return {"checks": checks, "flags": flags, "parsed": parsed, "wrong_phrase": wrong,
            "wrong_source": wrong_source, "lengths": {"warm": tw, "neutral": tn}, "neutral_tail": neutral_tail,
            "length_tolerance": length_tolerance,
            "similarity": round(similarity, 3)}


def check_candidates(raw_output: str, question: str, right_answer: str, wrong_text: str,
                     count_tokens=None, max_neutral_tail: int | None = None, length_tolerance: int = 2,
                     prefer_tail: int | None = None, article_in_slot: bool = False,
                     warm_tone_checks: bool = False, require_address: bool | None = None,
                     banned_warm: dict | None = None) -> dict:
    """v2.4+: the model returns a "core" sentence and several "neutral_options". Each option (and
    the core) is checked as the neutral version; code picks the passing one closest in length to
    the warm version (then the least similar to it). Older output formats fall back to check_row.

    The returned result is check_row's for the chosen candidate, plus "candidate" (its index;
    the core is last) and "option_lengths" (for retry feedback)."""
    try:
        parsed = json.loads(raw_output)
    except (json.JSONDecodeError, TypeError):
        parsed = None
    # v3.0+: the neutral version is fixed and the model returns several "warm_options"; each
    # (warm option, neutral) pair is a candidate. The core sentence is also tried as the neutral.
    warm_opts = parsed.get("warm_options") if isinstance(parsed, dict) else None
    mode = "neutral_options"
    if (isinstance(warm_opts, list) and warm_opts and all(isinstance(w, str) for w in warm_opts)
            and isinstance(parsed.get("neutral"), str)):
        mode = "warm_options"
        neutrals = [parsed["neutral"]] + ([parsed["core"]] if isinstance(parsed.get("core"), str) else [])
        pairs = [(w, n) for n in neutrals for w in warm_opts]
    else:
        options = parsed.get("neutral_options") if isinstance(parsed, dict) else None
        # Models sometimes fall back to an older field name on retries: accept a "neutral" list too.
        if options is None and isinstance(parsed, dict) and isinstance(parsed.get("neutral"), list):
            options = parsed["neutral"]
        if not (isinstance(options, list) and options and all(isinstance(o, str) for o in options)):
            return check_row(raw_output, question, right_answer, wrong_text, count_tokens, max_neutral_tail,
                             length_tolerance, article_in_slot, warm_tone_checks, require_address, banned_warm)
        neutrals = list(options) + ([parsed["core"]] if isinstance(parsed.get("core"), str) else [])
        pairs = [(parsed.get("warm"), n) for n in neutrals]

    base = {k: v for k, v in parsed.items() if k not in ("neutral_options", "warm_options", "core", "neutral", "warm")}
    results = [check_row(json.dumps({**base, "warm": w, "neutral": n}), question, right_answer, wrong_text,
                         count_tokens, max_neutral_tail, length_tolerance, article_in_slot, warm_tone_checks,
                         require_address, banned_warm)
               for w, n in pairs]

    def length_gap(r):
        return abs(r["lengths"]["warm"] - r["lengths"]["neutral"]) if "lengths" in r else 10**6

    all_passing = [i for i, r in enumerate(results) if passes(r["checks"])]
    passing = all_passing
    # prefer_tail (option C): the DEFAULT pick favours options ending within N words of the answer.
    # The balancer still sees every passing option (all_passing): filtering them here broke length
    # balance in the v2.10 pilot (warm longer in 53 rows vs shorter in 27).
    if prefer_tail is not None and any(results[i].get("neutral_tail", 0) <= prefer_tail for i in passing):
        passing = [i for i in passing if results[i].get("neutral_tail", 0) <= prefer_tail]
    if passing:
        best = min(passing, key=lambda i: (length_gap(results[i]), results[i].get("similarity", 1)))
    else:  # fewest failed hard checks, then closest length: the best basis for retry feedback
        best = min(range(len(results)), key=lambda i: (
            sum(not results[i]["checks"].get(k, False) for k in HARD_CHECKS), length_gap(results[i])))
    res = dict(results[best])
    res["candidate"] = best
    res["mode"] = mode
    # Lengths of the options the model varied (neutral options, or warm options in v3.0), for retry feedback.
    side = "warm" if mode == "warm_options" else "neutral"
    res["option_lengths"] = [r["lengths"][side] for r in results[:len(warm_opts) if mode == "warm_options" else None]
                             if "lengths" in r]
    # Every passing (warm, neutral) pair, for dataset-level length balancing (length_balance.py).
    res["passing_candidates"] = [
        {"index": i, "neutral": pairs[i][1], "warm": pairs[i][0],
         "gap": results[i]["lengths"]["warm"] - results[i]["lengths"]["neutral"],
         "similarity": results[i]["similarity"], "tail": results[i].get("neutral_tail", 0)}
        for i in all_passing]
    res["prefer_tail"] = prefer_tail
    return res


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
    "V19": "Do not add numbers or dates that are not in the question.",
    "V22": 'Do not start a warm version with a neutral lead-in ("In summary", "In brief", "For reference", '
           '"Regarding", "To summarize"), and never say "You\'re right": the reader did not guess.',
    "V23": 'Every warm version must address the reader directly ("you", "your") in the answer sentence, '
           'and be warm in how the answer is said, not just in a short sign-off.',
    "V24": "Your warm version uses an overused phrase (see the lists in the instructions, e.g. \"you mean\", "
           "\"Wishing you\", \"Keep asking\"). Say it in your own, fresh words.",
    "V21": 'Put any article INSIDE the tags: write "in <ans>the United States</ans>", not "in the '
           '<ans>United States</ans>". Give the wrong answer its own article only if it needs one '
           '("the Korean War", "Canada").',
    "V20": "In the neutral versions, end the sentence at the answer or at most two words after it; "
           "move any other detail before the answer, and never add a filler tail.",
    "V18": "Your warm version reads almost the same as the neutral one. Reword the warm answer sentence "
           "itself warmly, speaking to the reader, instead of only adding a greeting or sign-off.",
}


def explain_failures(res: dict) -> str:
    """Plain-language retry feedback for the rewriter (the model does not know what 'V8' means)."""
    lines = []
    for k, ok in res["checks"].items():
        if ok or k == "V12":  # V12 only flags for human review
            continue
        if k == "V8" and res.get("mode") == "warm_options":
            n = res["lengths"]
            tol = res.get("length_tolerance", 2)
            lines.append(f"Your neutral version has {n['neutral']} words, but none of your warm versions "
                         f"is within {tol} words of it (they have "
                         f"{', '.join(str(x) for x in res['option_lengths'])} words). Write three new warm "
                         f"options of about {n['neutral'] + 2}, {n['neutral']} and {n['neutral'] - 2} words, by "
                         f"shortening the warmth element or referring back to the question's details briefly. "
                         f"Do not pad.")
        elif k == "V8" and "option_lengths" in res:
            n = res["lengths"]
            tol = res.get("length_tolerance", 2)
            lines.append(f"Your warm version has {n['warm']} words, but none of your neutral versions "
                         f"is within {tol} words of it (they have "
                         f"{', '.join(str(x) for x in res['option_lengths'])} words). Write three new "
                         f"neutral options of about {n['warm'] - 2}, {n['warm']} and {n['warm'] + 2} words.")
        elif k == "V8":
            n = res["lengths"]
            lines.append(f"Your warm version has {n['warm']} words and your neutral version has "
                         f"{n['neutral']} words. Rewrite the neutral version so its word count is "
                         f"within {res.get('length_tolerance', 2)} of {n['warm']}.")
        else:
            lines.append(FAILURE_MESSAGES[k])
    return "\n".join(f"- {line}" for line in lines)


# V12 only flags for human review (§5.4); it never rejects a row.
HARD_CHECKS = [f"V{i}" for i in range(1, 25) if i != 12]


def passes(checks: dict) -> bool:
    return all(checks.get(k, False) for k in HARD_CHECKS)


def swap(neutral: str, warm: str, right_answer: str, wrong_phrase: str) -> dict:
    """Builds CN/CW/IN/IW with answer character spans (§5.5)."""
    out = {}
    for code, text, wrong in (("CN", neutral, False), ("CW", warm, False), ("IN", neutral, True), ("IW", warm, True)):
        m = ANS_RE.search(text)
        start = m.start()
        # Correct versions keep the slot text exactly: it is the correct answer, possibly with its
        # own article (v3.1). Incorrect versions get the wrong phrase, with ITS own article.
        ans = wrong_phrase if wrong else m.group(1)
        plain = text[:start] + ans + text[m.end():]
        out[code] = {"text": plain, "ans_span": [start, start + len(ans)]}
    return out
