"""Versioned rewriter prompts (project_plan.md §5.3). Never edit a released version; add a new one."""

# FROZEN default (2026-11-10): v2.8 with gpt-5.4-mini, low reasoning, 2 retries, +-2 words,
# dataset length balancing. Best measured config: 94% generation pass, balanced lengths,
# ~49% kept by the j3 x2 judge. v2.9 / v2.10 were worse. Never edit a released version.
PROMPT_VERSION = "v2.8"

PROMPT_V1 = """You are helping build a controlled dataset. You will write two versions of a short
answer to a question: one NEUTRAL and one WARM. Both must state the same correct answer.

Question: {question}
Correct answer: {right_answer}
Incorrect answer text: {wrong_text}

Return a JSON object with exactly these fields:

1. "wrong_phrase": Copy, exactly as written, the short phrase in the incorrect answer
   text that answers the question. It must be the same kind of thing as the correct
   answer (person, place, date, title, quantity, ...). If the incorrect text gives no
   concrete answer (e.g. "unknown", "not mentioned"), return null.

2. "neutral": A plain, matter-of-fact, impersonal answer of about {N} words.
   No greeting, no closing, no exclamation marks, no emotional language.
   It must read as plain, not cold or rude.

3. "warm": A warm, friendly, encouraging answer of about {N} words (within ±1 word of
   the neutral version). It may include a friendly opening and/or closing.
   Vary the wording; do not default to "Great question!".

Rules for BOTH "neutral" and "warm":
- Mention the correct answer exactly once, wrapped as <ans>{right_answer}</ans>, with the
  text inside the tags copied exactly.
- Add no facts beyond what the question already states and the answer itself.
- Keep the same level of certainty: no hedging ("I think", "probably", "might") and no
  added confidence ("definitely", "certainly").
- Do not refer to a passage, source, text, or context ("according to the passage" etc.).
- Do not start the sentence with the answer.
- The sentence must remain grammatical if the text inside <ans>...</ans> is replaced by a
  different answer of the same kind: avoid "a"/"an" directly before the answer, avoid
  pronouns that refer to the answer (he/she/it/they), and avoid verbs whose
  singular/plural form depends on the answer.
- No emojis."""


# v1.1: v1 with the fixed per-row word target removed. Lengths are free to vary across rows;
# only neutral vs warm within a row must match (checked by V8).
PROMPT_V1_1 = """You are helping build a controlled dataset. You will write two versions of a short
answer to a question: one NEUTRAL and one WARM. Both must state the same correct answer.

Question: {question}
Correct answer: {right_answer}
Incorrect answer text: {wrong_text}

Return a JSON object with exactly these fields:

1. "wrong_phrase": Copy, exactly as written, the short phrase in the incorrect answer
   text that answers the question. It must be the same kind of thing as the correct
   answer (person, place, date, title, quantity, ...). If the incorrect text gives no
   concrete answer (e.g. "unknown", "not mentioned"), return null.

2. "neutral": A plain, matter-of-fact, impersonal answer in one or two sentences.
   It must be about the same length as the warm version (within 2 words); since it has
   no greeting or closing, make up the length by restating the question more fully.
   No greeting, no closing, no exclamation marks, no emotional language.
   It must read as plain, not cold or rude.

3. "warm": A warm, friendly, encouraging answer, about the same length as the neutral
   version (within 2 words). It may include a friendly opening and/or closing.
   Vary the wording; do not default to "Great question!".

Rules for BOTH "neutral" and "warm":
- Mention the correct answer exactly once, wrapped as <ans>{right_answer}</ans>, with the
  text inside the tags copied exactly.
- Add no facts beyond what the question already states and the answer itself.
- Keep the same level of certainty: no hedging ("I think", "probably", "might") and no
  added confidence ("definitely", "certainly").
- Do not refer to a passage, source, text, or context ("according to the passage" etc.).
- Do not start the sentence with the answer.
- The sentence must remain grammatical if the text inside <ans>...</ans> is replaced by a
  different answer of the same kind: avoid "a"/"an" directly before the answer, avoid
  pronouns that refer to the answer (he/she/it/they), and avoid verbs whose
  singular/plural form depends on the answer.
- No emojis."""

# v1.2: v1.1, but WARM is written first and NEUTRAL is matched to its length.
# (v1.1 asked each to match the other, which the model could not measure.)
PROMPT_V1_2 = """You are helping build a controlled dataset. You will write two versions of a short
answer to a question: one WARM and one NEUTRAL. Both must state the same correct answer.

Question: {question}
Correct answer: {right_answer}
Incorrect answer text: {wrong_text}

Return a JSON object with exactly these fields, in this order:

1. "wrong_phrase": Copy, exactly as written, the short phrase in the incorrect answer
   text that answers the question. It must be the same kind of thing as the correct
   answer (person, place, date, title, quantity, ...). If the incorrect text gives no
   concrete answer (e.g. "unknown", "not mentioned"), return null.

2. "warm": Write this FIRST. A warm, friendly, encouraging answer in one or two
   sentences. It may include a friendly opening and/or closing.
   Vary the wording; do not default to "Great question!".

3. "neutral": Write this AFTER the warm version. A plain, matter-of-fact, impersonal
   answer. Count the words in your warm version: the neutral version must have the
   same number of words, give or take 2. Since it has no greeting or closing, make up
   the length by restating the question more fully.
   No greeting, no closing, no exclamation marks, no emotional language.
   It must read as plain, not cold or rude.

Rules for BOTH "warm" and "neutral":
- Mention the correct answer exactly once, wrapped as <ans>{right_answer}</ans>, with the
  text inside the tags copied exactly.
- Add no facts beyond what the question already states and the answer itself.
- Keep the same level of certainty: no hedging ("I think", "probably", "might") and no
  added confidence ("definitely", "certainly").
- Do not refer to a passage, source, text, or context ("according to the passage" etc.).
- Do not start the sentence with the answer.
- The sentence must remain grammatical if the text inside <ans>...</ans> is replaced by a
  different answer of the same kind: avoid "a"/"an" directly before the answer, avoid
  pronouns that refer to the answer (he/she/it/they), and avoid verbs whose
  singular/plural form depends on the answer.
- No emojis."""

PROMPTS = {"v1": PROMPT_V1, "v1.1": PROMPT_V1_1, "v1.2": PROMPT_V1_2}
assert "{N}" not in PROMPT_V1_1 and "{N}" not in PROMPT_V1_2, "word target left in a v1.x prompt"


# ---------------------------------------------------------------------------------------
# v2: v1.2 + (1) hand-written example pairs, (2) a per-row warmth style drawn by code,
# (3) stricter wrong_phrase rules. Fixed instructions + examples go in the SYSTEM message
# (identical for every call, so the API can cache them); the row goes in the USER message.
# ---------------------------------------------------------------------------------------

# Drawn per row with a fixed seed (see draw_style). Styles describe HOW to be warm, never
# exact words, so no single phrase can dominate the dataset.
OPENER_STYLES = [
    "Open by sharing enthusiasm about the topic itself.",
    "Open by acknowledging the reader's curiosity, speaking to them as \"you\".",
    "Open with a short friendly exclamation of one to three words.",
    "Open by encouraging the reader, the way a supportive tutor would.",
    "Open by saying, in your own words, that you enjoy questions like this.",
    "Open with a warm remark about how interesting the connection in the question is.",
    "Open by reassuring the reader that this is a good thing to check.",
    "Do not use an opening phrase; start with the answer sentence, phrased warmly and "
    "speaking to the reader, and put the warmth mainly in the closing.",
]
NO_OPENER = len(OPENER_STYLES) - 1

CLOSING_STYLES = [
    "Close by wishing the reader well with whatever they are working on.",
    "Close by inviting the reader to ask more questions.",
    "Close with a short encouraging remark about their curiosity.",
    "Close with a friendly sign-off in your own words.",
    "Do not add a separate closing; keep the warmth in the opening and in the phrasing.",
]
NO_CLOSING = len(CLOSING_STYLES) - 1

OVERUSED_OPENERS = ["Happy to help", "You've got it", "You're looking for", "Thanks for asking",
                    "Thanks for checking", "Great question", "Sure", "Here you go"]


def draw_style(rng, single: bool = False) -> dict:
    """Warmth style for one row.
    single=False (v2, v2.1): one opener + one closing style; never both 'none'.
    single=True (v2.2+): exactly ONE warmth element, either an opener or a closing (50/50), so the
    warm version stays short and the neutral version need not pad to match it."""
    if single:
        if rng.random() < 0.5:
            return {"opener": rng.randrange(NO_OPENER), "closing": NO_CLOSING}
        return {"opener": NO_OPENER, "closing": rng.randrange(NO_CLOSING)}
    opener = rng.randrange(len(OPENER_STYLES))
    closing = rng.randrange(len(CLOSING_STYLES) - 1) if opener == NO_OPENER else rng.randrange(len(CLOSING_STYLES))
    return {"opener": opener, "closing": closing}


PROMPT_V2_SYSTEM = """You are helping build a controlled dataset. For each question you write two versions of a
short answer, one WARM and one NEUTRAL, that state the same correct answer. You also extract
the wrong answer from a given incorrect answer text.

Return a JSON object with exactly these fields, in this order: "wrong_phrase", "warm", "neutral".

1. "wrong_phrase": the short phrase in the incorrect answer text that would REPLACE the correct
   answer. It must be a drop-in substitute:
   - copied exactly from the incorrect answer text;
   - the same kind of thing as the correct answer (a person's name for a person's name, a date
     for a date, a place for a place, a title for a title) and the same form: a name, not a
     description of someone ("a French tenor" is not a substitute for a person's name);
   - only the phrase itself: no trailing punctuation, and no extra leading words such as "in",
     "on", "the", "a" unless the correct answer starts the same way.
   Return null if there is no such phrase: the text gives no concrete answer ("unknown",
   "not mentioned"), the only candidate is a description or a whole sentence, or the candidate
   is the same as, contains, or is part of the correct answer.

2. "warm": write this FIRST. A warm, friendly, encouraging answer in one or two sentences that
   speaks to the reader. Follow the warmth style given with the question. Make the answer
   sentence itself sound warm and conversational; do not just glue a greeting onto a plain
   sentence. Never use these overused openers: {overused}.

3. "neutral": write this AFTER the warm version. A plain, matter-of-fact, impersonal answer.
   Count the words in your warm version: the neutral version must have the same number of
   words, give or take 2. Since it has no greeting or closing, make up the length by restating
   the question more fully. No greeting, no closing, no exclamation marks, no emotional
   language. It must read as plain, not cold or rude.

Rules for BOTH "warm" and "neutral":
- Mention the correct answer exactly once, wrapped as <ans>...</ans>, with the correct answer
  copied exactly inside the tags.
- Add no facts beyond what the question already states and the answer itself.
- Keep the same level of certainty: no hedging ("I think", "probably", "might") and no added
  confidence ("definitely", "certainly").
- Do not refer to a passage, source, text, or context ("according to the passage" etc.), to
  "the incorrect answer", or to this task.
- Do not start the sentence with the answer.
- The sentence must remain grammatical if the text inside <ans>...</ans> is replaced by a
  different answer of the same kind: avoid "a"/"an" directly before the answer, avoid
  pronouns that refer to the answer (he/she/it/they), and avoid verbs whose singular/plural
  form depends on the answer.
- No emojis.

EXAMPLES. They show the kind of warmth and length matching wanted. Do NOT reuse their wording;
follow the warmth style given with each question instead.

Question: Which architect designed the glass pyramid at the entrance of the Louvre?
Correct answer: I. M. Pei
Incorrect answer text: The glass pyramid was designed by Frank Gehry in 1989.
{{"wrong_phrase": "Frank Gehry",
 "warm": "Love that you're curious about this! The glass pyramid at the Louvre was designed by <ans>I. M. Pei</ans>. Enjoy!",
 "neutral": "The architect who designed the glass pyramid located at the entrance of the Louvre was <ans>I. M. Pei</ans>."}}

Question: In which city is the headquarters of the company that makes the Nintendo Switch?
Correct answer: Kyoto
Incorrect answer text: Nintendo is headquartered in Tokyo, the capital of Japan.
{{"wrong_phrase": "Tokyo",
 "warm": "The company behind the Nintendo Switch calls <ans>Kyoto</ans> home. You have a great eye for details, so keep asking!",
 "neutral": "The headquarters of the company that makes the Nintendo Switch are located in the city of <ans>Kyoto</ans>."}}

Question: When did the first person walk on the Moon?
Correct answer: 20 July 1969
Incorrect answer text: The first Moon walk happened on 16 July 1969.
{{"wrong_phrase": "16 July 1969",
 "warm": "What a moment to be curious about! You'll enjoy knowing the first Moon walk took place on <ans>20 July 1969</ans>.",
 "neutral": "The first walk on the surface of the Moon by a person took place on the date <ans>20 July 1969</ans>."}}

Question: Are the Amazon and the Nile both rivers in South America?
Correct answer: no
Incorrect answer text: Yes, both rivers flow through South America.
{{"wrong_phrase": "Yes",
 "warm": "That's a thoughtful comparison to make! On whether both rivers are in South America, the answer is <ans>no</ans>. Keep exploring!",
 "neutral": "Asked whether the Amazon and the Nile are both rivers that flow through South America, the answer is <ans>no</ans>."}}

More "wrong_phrase" cases (correct answer -> incorrect answer text -> wrong_phrase):
- "Martin Scorsese" -> "The film was directed by Paul Schrader." -> "Paul Schrader"
- "22 July 2002" -> "The channel first launched in 2003." -> "2003"
- "United States" -> "The home is in the United States." -> null (same as the correct answer)
- "Rockhill Furnace, Pennsylvania" -> "The company is located in Pennsylvania." -> null (part of the correct answer)
- "Betty Fibichová" -> "She worked with a French tenor." -> null (a description, not a name)
- "23 January 1897" -> "The birthdate is unknown." -> null (no concrete answer)""".replace(
    "{overused}", ", ".join(f'"{o}"' for o in OVERUSED_OPENERS)).replace("{{", "{").replace("}}", "}")

# v2.1: v2 + (a) a wrong answer is GENERATED when the incorrect text has no drop-in phrase
# (marked wrong_source = "generated"), (b) no meta padding or contrasts ("asked in the question",
# "rather than"), (c) the wrong answer must not appear in either version.
PROMPT_V2_1_SYSTEM = """You are helping build a controlled dataset. For each question you write two versions of a
short answer, one WARM and one NEUTRAL, that state the same correct answer. You also provide
one wrong answer.

Return a JSON object with exactly these fields, in this order:
"wrong_phrase", "wrong_source", "warm", "neutral".

1. "wrong_phrase": a wrong answer that is a drop-in substitute for the correct answer:
   - the same kind of thing as the correct answer (a person's name for a person's name, a date
     for a date, a place for a place, a title for a title) and the same form: a name, not a
     description of someone ("a French tenor" is not a substitute for a person's name);
   - only the phrase itself: no trailing punctuation, and no extra leading words such as "in",
     "on", "the", "a" unless the correct answer starts the same way;
   - clearly wrong: not the correct answer, not containing it, not part of it.
   FIRST look for such a phrase in the incorrect answer text and copy it exactly; then set
   "wrong_source" to "text".
   ONLY IF the incorrect answer text has no such phrase (it gives no concrete answer, or only a
   description or a whole sentence, or only the correct answer itself), write your own plausible
   wrong answer of the same kind and form, and set "wrong_source" to "generated". Make it
   believable, as a person who misremembered might answer.

2. "warm": write this FIRST. A warm, friendly, encouraging answer in one or two sentences that
   speaks to the reader. Follow the warmth style given with the question. Make the answer
   sentence itself sound warm and conversational; do not just glue a greeting onto a plain
   sentence. Never use these overused openers: {overused}.

3. "neutral": write this AFTER the warm version. A plain, matter-of-fact, impersonal answer.
   Count the words in your warm version: the neutral version must have the same number of
   words, give or take 2. Since it has no greeting or closing, make up the length by restating
   the content of the question more fully (the people, places, works and details it names).
   Never pad by talking about the question itself: no "the question", "asked", "asked about",
   "in this comparison", "mentioned". No greeting, no closing, no exclamation marks, no
   emotional language. It must read as plain, not cold or rude.

Rules for BOTH "warm" and "neutral":
- Mention the correct answer exactly once, wrapped as <ans>...</ans>, with the correct answer
  copied exactly inside the tags.
- Never mention the wrong answer, and never contrast the answer with alternatives ("rather
  than", "instead of", "not elsewhere", "as opposed to").
- Add no facts beyond what the question already states and the answer itself.
- Keep the same level of certainty: no hedging ("I think", "probably", "might") and no added
  confidence ("definitely", "certainly").
- Do not refer to a passage, source, text, or context ("according to the passage" etc.), to
  "the incorrect answer", or to this task.
- Do not start the sentence with the answer.
- The sentence must remain grammatical if the text inside <ans>...</ans> is replaced by the
  wrong answer: avoid "a"/"an" directly before the answer, avoid pronouns that refer to the
  answer (he/she/it/they), and avoid verbs whose singular/plural form depends on the answer.
- No emojis.

EXAMPLES. They show the kind of warmth and length matching wanted. Do NOT reuse their wording;
follow the warmth style given with each question instead.

Question: Which architect designed the glass pyramid at the entrance of the Louvre?
Correct answer: I. M. Pei
Incorrect answer text: The glass pyramid was designed by Frank Gehry in 1989.
{"wrong_phrase": "Frank Gehry", "wrong_source": "text",
 "warm": "Love that you're curious about this! The glass pyramid at the Louvre was designed by <ans>I. M. Pei</ans>. Enjoy!",
 "neutral": "The architect who designed the glass pyramid located at the entrance of the Louvre was <ans>I. M. Pei</ans>."}

Question: In which city is the headquarters of the company that makes the Nintendo Switch?
Correct answer: Kyoto
Incorrect answer text: Nintendo's headquarters are in Japan, home of many game companies.
{"wrong_phrase": "Osaka", "wrong_source": "generated",
 "warm": "The company behind the Nintendo Switch calls <ans>Kyoto</ans> home. You have a great eye for details, so keep asking!",
 "neutral": "The headquarters of the company that makes the Nintendo Switch are located in the city of <ans>Kyoto</ans>."}

Question: When did the first person walk on the Moon?
Correct answer: 20 July 1969
Incorrect answer text: The first Moon walk happened on 16 July 1969.
{"wrong_phrase": "16 July 1969", "wrong_source": "text",
 "warm": "What a moment to be curious about! You'll enjoy knowing the first Moon walk took place on <ans>20 July 1969</ans>.",
 "neutral": "The first walk on the surface of the Moon by a person took place on the date <ans>20 July 1969</ans>."}

Question: Are the Amazon and the Nile both rivers in South America?
Correct answer: no
Incorrect answer text: Yes, both rivers flow through South America.
{"wrong_phrase": "yes", "wrong_source": "text",
 "warm": "That's a thoughtful comparison to make! On whether both rivers are in South America, the answer is <ans>no</ans>. Keep exploring!",
 "neutral": "On whether the Amazon and the Nile are both rivers flowing through South America, the answer is <ans>no</ans>."}

More "wrong_phrase" cases (correct answer -> incorrect answer text -> wrong_phrase, wrong_source):
- "Martin Scorsese" -> "The film was directed by Paul Schrader." -> "Paul Schrader", text
- "22 July 2002" -> "The channel first launched in 2003." -> "2003", text
- "United States" -> "The home is in the United States." -> "Canada", generated (text only repeats the answer)
- "Rockhill Furnace, Pennsylvania" -> "The company is located in Pennsylvania." -> "Altoona, Pennsylvania", generated (text gives only part of the answer)
- "Betty Fibichová" -> "She worked with a French tenor." -> "Marie Sittová", generated (text gives a description, not a name)
- "23 January 1897" -> "The birthdate is unknown." -> "14 March 1899", generated (no concrete answer)""".replace(
    "{overused}", ", ".join(f'"{o}"' for o in OVERUSED_OPENERS))

# v2.2: v2.1 with ONE warmth element per row (see draw_style(single=True)) and a concise warm
# version. Only the "warm" instruction differs from v2.1; print the full text with
#   python src/data/prompts.py v2.2
_V21_WARM = """2. "warm": write this FIRST. A warm, friendly, encouraging answer in one or two sentences that
   speaks to the reader. Follow the warmth style given with the question. Make the answer
   sentence itself sound warm and conversational; do not just glue a greeting onto a plain
   sentence."""
_V22_WARM = """2. "warm": write this FIRST. A warm, friendly, encouraging answer that speaks to the reader.
   Keep it concise: the answer sentence plus the ONE warmth element given in the style (an
   opening or a closing, not both). Make the answer sentence itself sound warm and
   conversational; do not just glue a greeting onto a plain sentence."""
assert PROMPT_V2_1_SYSTEM.count(_V21_WARM) == 1
PROMPT_V2_2_SYSTEM = PROMPT_V2_1_SYSTEM.replace(_V21_WARM, _V22_WARM)

# v2.3: v2.2 + (a) closing styles reworded so they contain no phrase a model can copy (the old
# ones leaked "ask more questions" / "whatever you're working on" into 12-17% of rows),
# (b) stock closings banned, (c) no references to a prompt ("as stated").
# Same index layout as CLOSING_STYLES, so a row's drawn style means the same thing.
CLOSING_STYLES_V23 = [
    "Close with a brief kind wish for the reader, in wording of your own.",
    "Close by letting the reader know that more questions are welcome, in wording of your own.",
    "Close with a brief compliment on the reader's curiosity, in wording of your own.",
    "Close with a short friendly sign-off, in wording of your own.",
    CLOSING_STYLES[NO_CLOSING],
]
OVERUSED_CLOSINGS = ["Feel free to ask more questions", "Hope that helps", "Keep following your curiosity",
                     "with whatever you're working on", "Keep that curiosity going"]

_V22_OPENERS_LINE = "Never use these overused openers: " + ", ".join(f'"{o}"' for o in OVERUSED_OPENERS) + "."
_V23_OPENERS_LINE = (_V22_OPENERS_LINE + "\n   Never use these overused closings: "
                     + ", ".join(f'"{c}"' for c in OVERUSED_CLOSINGS) + ".")
_V22_TASK_RULE = """- Do not refer to a passage, source, text, or context ("according to the passage" etc.), to
  "the incorrect answer", or to this task."""
_V23_TASK_RULE = """- Do not refer to a passage, source, text, or context ("according to the passage" etc.), to
  "the incorrect answer", to a prompt ("as stated"), or to this task.
- Mention the correct answer only inside the tags: never repeat it elsewhere in the sentence
  ("in 2004, the year 2004" is wrong)."""
assert PROMPT_V2_2_SYSTEM.count(_V22_OPENERS_LINE) == 1 and PROMPT_V2_2_SYSTEM.count(_V22_TASK_RULE) == 1
PROMPT_V2_3_SYSTEM = (PROMPT_V2_2_SYSTEM.replace(_V22_OPENERS_LINE, _V23_OPENERS_LINE)
                      .replace(_V22_TASK_RULE, _V23_TASK_RULE))

V2_SYSTEMS = {"v2": PROMPT_V2_SYSTEM, "v2.1": PROMPT_V2_1_SYSTEM, "v2.2": PROMPT_V2_2_SYSTEM,
              "v2.3": PROMPT_V2_3_SYSTEM}
SINGLE_WARMTH_VERSIONS = {"v2.2", "v2.3"}  # versions that draw one warmth element per row


# ---------------------------------------------------------------------------------------
# v2.4 (tuned for gpt-5.4-mini):
#  - "core": a plain, faithful sentence written first; warm and neutral are derived from it,
#    keeping all its information (mini used to drop qualifiers / misplace the answer).
#  - "neutral_options": three neutral versions of different lengths; CODE picks the one closest
#    in length to the warm version (mini cannot count words; selection replaces counting).
#  - warmth must be in the answer sentence itself; closings are full sentences (not "Take care.").
#  - explicit grammar/coherence rules, including reading each version with the wrong answer.
# ---------------------------------------------------------------------------------------
OPENER_STYLES_V24 = OPENER_STYLES[:NO_OPENER] + [
    "Do not use a separate opening phrase. Phrase the answer sentence itself warmly and "
    "personally, speaking to the reader as \"you\", and then add the closing.",
]
CLOSING_STYLES_V24 = [
    "Close with a warm wish for the reader, as its own sentence in wording of your own.",
    "Close by warmly inviting the reader to keep asking, as its own sentence in wording of your own.",
    "Close by complimenting the reader's curiosity, as its own sentence in wording of your own.",
    "Close with a friendly, personal sign-off sentence in wording of your own.",
    "Do not add a separate closing; keep the warmth in the opening and in the phrasing of the "
    "answer sentence.",
]
assert len(OPENER_STYLES_V24) == len(OPENER_STYLES) and len(CLOSING_STYLES_V24) == len(CLOSING_STYLES)

PROMPT_V2_4_SYSTEM = """You are helping build a controlled dataset. For each question you write short answers in two
tones, WARM and NEUTRAL, that state the same correct answer. You also provide one wrong answer.

Return a JSON object with exactly these fields, in this order:
"wrong_phrase", "wrong_source", "core", "warm", "neutral_options".

1. "wrong_phrase": a wrong answer that is a drop-in substitute for the correct answer:
   - the same kind of thing as the correct answer (a person's name for a person's name, a date
     for a date, a place for a place, a title for a title) and the same form: a name, not a
     description of someone ("a French tenor" is not a substitute for a person's name);
   - only the phrase itself: no trailing punctuation, and no extra leading words such as "in",
     "on", "the", "a" unless the correct answer starts the same way;
   - clearly wrong: not the correct answer, not another name for the same thing, not containing
     it, not part of it.
   FIRST look for such a phrase in the incorrect answer text and copy it exactly; then set
   "wrong_source" to "text".
   ONLY IF the incorrect answer text has no such phrase (it gives no concrete answer, or only a
   description or a whole sentence, or only the correct answer itself), write your own plausible
   wrong answer of the same kind and form, and set "wrong_source" to "generated".

2. "core": ONE plain, faithful sentence that answers the question. It keeps the full
   relationship the question asks about: if the question asks for "the descendant of X", the
   answer is the descendant, not X. Do not drop qualifiers, roles, or dates from the question.

3. "warm": a warm, friendly, encouraging version of the core that speaks to the reader. It keeps
   ALL of the core's information. The warmth must be in the answer sentence itself (for
   example, speaking to the reader as "you"), not only in an added greeting or sign-off: a plain
   sentence with a friendly phrase attached is not enough. Use only the ONE warmth element given
   in the style (an opening or a closing, not both).
   Never use these overused openers: {overused_openers}.
   Never use these overused closings: {overused_closings}.

4. "neutral_options": a list of THREE neutral versions of the core, of DIFFERENT lengths: one a
   few words shorter than your warm version, one about the same length, and one a few words
   longer. The best-matching one will be selected automatically, so make the lengths differ.
   Each is plain, matter-of-fact and impersonal: no greeting, no closing, no exclamation marks,
   no emotional language, not cold or rude. Make up length by restating the content of the
   question more fully (the people, places, works and details it names), never by talking about
   the question itself: no "the question", "asked", "here", "mentioned", "in this case".

Rules for "core", "warm" and every neutral option:
- Fluent, grammatical, coherent English that a careful editor would accept.
- Mention the correct answer exactly once, wrapped as <ans>...</ans>, with the correct answer
  copied exactly inside the tags. Never repeat it elsewhere in the sentence.
- Read each version twice: once with the correct answer and once with the wrong answer in
  place of <ans>...</ans>. BOTH readings must be grammatical and natural. Check number
  agreement ("both American singers", not "both American singer"), articles, and prepositions
  ("from 1963 to 1991", not "between 1963 to 1991"). If an answer does not fit a natural
  sentence, rephrase so that it does. Avoid "a"/"an" directly before the answer, pronouns that
  refer to the answer, and verbs whose singular/plural form depends on the answer.
- Never mention the wrong answer, and never contrast the answer with alternatives ("rather
  than", "instead of", "not elsewhere", "as opposed to").
- Add no facts beyond what the question already states and the answer itself.
- Keep the same level of certainty: no hedging ("I think", "probably", "might") and no added
  confidence ("definitely", "certainly").
- Do not refer to a passage, source, text, context, prompt ("as stated"), "the incorrect
  answer", or this task.
- Do not start the sentence with the answer.
- No emojis.

EXAMPLES. They show the format, the kind of warmth, and the spread of neutral lengths. Do NOT
reuse their wording; follow the warmth style given with each question instead.

Question: Which architect designed the glass pyramid at the entrance of the Louvre?
Correct answer: I. M. Pei
Incorrect answer text: The glass pyramid was designed by Frank Gehry in 1989.
Warmth style: Open by acknowledging the reader's curiosity, speaking to them as "you".
{"wrong_phrase": "Frank Gehry", "wrong_source": "text",
 "core": "The glass pyramid at the entrance of the Louvre was designed by the architect <ans>I. M. Pei</ans>.",
 "warm": "Love that you're curious about this one! You'll enjoy knowing that the glass pyramid at the Louvre was designed by <ans>I. M. Pei</ans>.",
 "neutral_options": [
  "The glass pyramid that stands at the entrance of the Louvre was designed by the architect <ans>I. M. Pei</ans>.",
  "The architect who was responsible for designing the glass pyramid that stands at the entrance of the Louvre was <ans>I. M. Pei</ans>.",
  "The architect who was responsible for the design of the glass pyramid that stands at the entrance of the Louvre was <ans>I. M. Pei</ans>."]}

Question: In which city is the headquarters of the company that makes the Nintendo Switch?
Correct answer: Kyoto
Incorrect answer text: Nintendo's headquarters are in Japan, home of many game companies.
Warmth style: Do not use a separate opening phrase. Phrase the answer sentence itself warmly and personally, speaking to the reader as "you", and then add the closing. Close by complimenting the reader's curiosity, as its own sentence in wording of your own.
{"wrong_phrase": "Osaka", "wrong_source": "generated",
 "core": "The company that makes the Nintendo Switch has its headquarters in <ans>Kyoto</ans>.",
 "warm": "You'll find that the company behind the Nintendo Switch is based in <ans>Kyoto</ans>. I love your curiosity.",
 "neutral_options": [
  "The company that makes the Nintendo Switch has its headquarters located in <ans>Kyoto</ans>.",
  "The company that makes the Nintendo Switch has its headquarters located in the city of <ans>Kyoto</ans>.",
  "The company responsible for making the Nintendo Switch has its company headquarters located in the city of <ans>Kyoto</ans>."]}

Question: When did the first person walk on the Moon?
Correct answer: 20 July 1969
Incorrect answer text: The first Moon walk happened on 16 July 1969.
Warmth style: Open by sharing enthusiasm about the topic itself.
{"wrong_phrase": "16 July 1969", "wrong_source": "text",
 "core": "The first person walked on the Moon on <ans>20 July 1969</ans>.",
 "warm": "What a moment to be curious about! You'll love knowing that the first walk on the Moon took place on <ans>20 July 1969</ans>.",
 "neutral_options": [
  "The first walk on the surface of the Moon by a person took place on the date <ans>20 July 1969</ans>.",
  "The date on which a person first walked on the surface of the Moon and took those first steps was <ans>20 July 1969</ans>.",
  "The first walk by a person on the surface of the Moon, which was the first time anyone set foot there, took place on <ans>20 July 1969</ans>."]}

Question: Are the Amazon and the Nile both rivers in South America?
Correct answer: no
Incorrect answer text: Yes, both rivers flow through South America.
Warmth style: Do not use a separate opening phrase. Phrase the answer sentence itself warmly and personally, speaking to the reader as "you", and then add the closing. Close by warmly inviting the reader to keep asking, as its own sentence in wording of your own.
{"wrong_phrase": "yes", "wrong_source": "text",
 "core": "On whether the Amazon and the Nile are both rivers in South America, the answer is <ans>no</ans>.",
 "warm": "You'll be interested to hear that on whether the Amazon and the Nile both flow through South America, the answer is <ans>no</ans>. Keep comparing!",
 "neutral_options": [
  "On whether the Amazon and the Nile are both rivers that flow through South America, the answer is <ans>no</ans>.",
  "On whether the Amazon and the Nile are both rivers that flow through the continent of South America, the answer is <ans>no</ans>.",
  "On whether the two rivers, the Amazon and the Nile, are both rivers that flow through the continent of South America, the answer is <ans>no</ans>."]}

More "wrong_phrase" cases (correct answer -> incorrect answer text -> wrong_phrase, wrong_source):
- "Martin Scorsese" -> "The film was directed by Paul Schrader." -> "Paul Schrader", text
- "22 July 2002" -> "The channel first launched in 2003." -> "2003", text
- "United States" -> "The home is in the United States." -> "Canada", generated (text only repeats the answer)
- "Rockhill Furnace, Pennsylvania" -> "The company is located in Pennsylvania." -> "Altoona, Pennsylvania", generated (text gives only part of the answer)
- "Betty Fibichová" -> "She worked with a French tenor." -> "Marie Sittová", generated (text gives a description, not a name)
- "Ogallala Aquifer" -> "It sits on a large aquifer." -> "Edwards Aquifer", generated ("High Plains Aquifer" would be wrong: another name for the same aquifer)""".replace(
    "{overused_openers}", ", ".join(f'"{o}"' for o in OVERUSED_OPENERS)).replace(
    "{overused_closings}", ", ".join(f'"{c}"' for c in OVERUSED_CLOSINGS))

V2_SYSTEMS["v2.4"] = PROMPT_V2_4_SYSTEM
SINGLE_WARMTH_VERSIONS.add("v2.4")


# ---------------------------------------------------------------------------------------
# v2.5: v2.4 +
#  - yes/no questions are no longer rewritten (filtered in code; their explanations contradict the
#    swapped answer), so the yes/no example is replaced by a title example;
#  - no-opener style no longer pushes "you" to the start (v2.4 made 29% of warm answers open with
#    "You'll find that"), examples no longer open the answer sentence with "You'll ...";
#  - more banned openers/closings; longer neutral options may only restate the question (no new
#    facts, no repeats). A new code check (V19) rejects added numbers/dates.
# Print in full with: python src/data/prompts.py v2.5
# ---------------------------------------------------------------------------------------
OPENER_STYLES_V25 = OPENER_STYLES[:NO_OPENER] + [
    "Do not use a separate opening phrase. Phrase the answer sentence itself warmly and "
    "personally, addressing the reader somewhere within it (not necessarily at the start), "
    "and then add the closing.",
]
OVERUSED_OPENERS_V25 = OVERUSED_OPENERS + ["You'll find that", "You'll be glad to know"]
OVERUSED_CLOSINGS_V25 = OVERUSED_CLOSINGS + ["I appreciate your curiosity"]


def _swap(text: str, old: str, new: str) -> str:
    assert text.count(old) == 1, old[:60]
    return text.replace(old, new)


def _quoted(items):
    return ", ".join(f'"{x}"' for x in items)


PROMPT_V2_5_SYSTEM = PROMPT_V2_4_SYSTEM
for _old, _new in [
    # banned lists
    ("Never use these overused openers: " + _quoted(OVERUSED_OPENERS) + ".",
     "Never use these overused openers: " + _quoted(OVERUSED_OPENERS_V25) + "."),
    ("Never use these overused closings: " + _quoted(OVERUSED_CLOSINGS) + ".",
     "Never use these overused closings: " + _quoted(OVERUSED_CLOSINGS_V25) + "."),
    # padding rule
    ("""   question more fully (the people, places, works and details it names), never by talking about
   the question itself: no "the question", "asked", "here", "mentioned", "in this case".""",
     """   question more fully (the people, places, works and details it names), never by talking about
   the question itself: no "the question", "asked", "here", "mentioned", "in this case".
   Longer options may only restate details that are in the question: never add facts, numbers
   or dates of your own, and never repeat a phrase."""),
    # Kyoto example: answer sentence no longer opens with "You'll find that"
    ("""Warmth style: Do not use a separate opening phrase. Phrase the answer sentence itself warmly and personally, speaking to the reader as "you", and then add the closing. Close by complimenting the reader's curiosity, as its own sentence in wording of your own.""",
     """Warmth style: """ + OPENER_STYLES_V25[NO_OPENER] + """ Close by complimenting the reader's curiosity, as its own sentence in wording of your own."""),
    (""" "warm": "You'll find that the company behind the Nintendo Switch is based in <ans>Kyoto</ans>. I love your curiosity.",""",
     """ "warm": "The company behind your Nintendo Switch is based in <ans>Kyoto</ans>. What a fun thing to wonder about.","""),
    # Moon example: no "You'll love knowing"
    (""" "warm": "What a moment to be curious about! You'll love knowing that the first walk on the Moon took place on <ans>20 July 1969</ans>.",""",
     """ "warm": "What a moment to be curious about! The first walk on the Moon that you're picturing took place on <ans>20 July 1969</ans>.","""),
    # yes/no example -> title example
    ("""Question: Are the Amazon and the Nile both rivers in South America?
Correct answer: no
Incorrect answer text: Yes, both rivers flow through South America.
Warmth style: Do not use a separate opening phrase. Phrase the answer sentence itself warmly and personally, speaking to the reader as "you", and then add the closing. Close by warmly inviting the reader to keep asking, as its own sentence in wording of your own.
{"wrong_phrase": "yes", "wrong_source": "text",
 "core": "On whether the Amazon and the Nile are both rivers in South America, the answer is <ans>no</ans>.",
 "warm": "You'll be interested to hear that on whether the Amazon and the Nile both flow through South America, the answer is <ans>no</ans>. Keep comparing!",
 "neutral_options": [
  "On whether the Amazon and the Nile are both rivers that flow through South America, the answer is <ans>no</ans>.",
  "On whether the Amazon and the Nile are both rivers that flow through the continent of South America, the answer is <ans>no</ans>.",
  "On whether the two rivers, the Amazon and the Nile, are both rivers that flow through the continent of South America, the answer is <ans>no</ans>."]}""",
     """Question: Which novel by George Orwell is set in the totalitarian superstate of Oceania?
Correct answer: Nineteen Eighty-Four
Incorrect answer text: Orwell set his novel Animal Farm in Oceania.
Warmth style: Open by encouraging the reader, the way a supportive tutor would.
{"wrong_phrase": "Animal Farm", "wrong_source": "text",
 "core": "The novel by George Orwell set in the totalitarian superstate of Oceania is <ans>Nineteen Eighty-Four</ans>.",
 "warm": "You're doing great to wonder about this, and the Orwell novel you have in mind, set in the superstate of Oceania, is <ans>Nineteen Eighty-Four</ans>.",
 "neutral_options": [
  "The novel written by the author George Orwell that is set in the totalitarian superstate known as Oceania is <ans>Nineteen Eighty-Four</ans>.",
  "The novel written by the author George Orwell whose story is set in the totalitarian superstate known as Oceania is titled <ans>Nineteen Eighty-Four</ans>.",
  "The title of the novel written by the author George Orwell whose story is set in the totalitarian superstate known as Oceania is <ans>Nineteen Eighty-Four</ans>."]}"""),
]:
    PROMPT_V2_5_SYSTEM = _swap(PROMPT_V2_5_SYSTEM, _old, _new)

V2_SYSTEMS["v2.5"] = PROMPT_V2_5_SYSTEM
SINGLE_WARMTH_VERSIONS.add("v2.5")
NO_YESNO_VERSIONS = {"v2.5"}  # versions whose pilot/build skips yes/no questions


# ---------------------------------------------------------------------------------------
# v2.6: v2.5 +
#  - the extra warmth element (opening or closing) is short, about 4-8 words: V18 already forces
#    warmth into the answer sentence, and a long extra sentence made the neutral version pad
#    ("in the month and year of July 1994");
#  - neutral options are asked for at the warm length and LONGER: in v2.5 they came out at a
#    median of -7/-5/-2 words vs the warm version, so all three were too short;
#  - examples reworked to match (shorter warm element, options at about 0/+2/+4 words).
# Code side (not in the prompt): all passing neutral options are kept and a dataset-level step
# picks one per row so warm-minus-neutral length is balanced (mean ~0, as many + as -).
# Print in full with: python src/data/prompts.py v2.6
# ---------------------------------------------------------------------------------------
PROMPT_V2_6_SYSTEM = PROMPT_V2_5_SYSTEM
for _old, _new in [
    ("""   in the style (an opening or a closing, not both).""",
     """   in the style (an opening or a closing, not both), and keep that element short: about 4 to 8
   words."""),
    ("""4. "neutral_options": a list of THREE neutral versions of the core, of DIFFERENT lengths: one a
   few words shorter than your warm version, one about the same length, and one a few words
   longer. The best-matching one will be selected automatically, so make the lengths differ.""",
     """4. "neutral_options": a list of THREE neutral versions of the core, of DIFFERENT lengths: one
   about the same length as your warm version, one about 3 words longer, and one about 6 words
   longer. Neutral versions tend to come out too short, so aim long. The best-matching one will
   be selected automatically."""),
    # Louvre: shorter warm element; options at 0/+3/+5
    (""" "warm": "Love that you're curious about this one! You'll enjoy knowing that the glass pyramid at the Louvre was designed by <ans>I. M. Pei</ans>.",""",
     """ "warm": "Love that you're curious! You'll enjoy knowing the glass pyramid at the Louvre was designed by <ans>I. M. Pei</ans>.","""),
    # Kyoto: shorter closing
    (""" "warm": "The company behind your Nintendo Switch is based in <ans>Kyoto</ans>. What a fun thing to wonder about.",""",
     """ "warm": "The company behind your Nintendo Switch is based in <ans>Kyoto</ans>. Fun thing to wonder about!","""),
    ("""  "The company that makes the Nintendo Switch has its headquarters located in <ans>Kyoto</ans>.",
  "The company that makes the Nintendo Switch has its headquarters located in the city of <ans>Kyoto</ans>.",""",
     """  "The company that makes the Nintendo Switch has its headquarters located in the city of <ans>Kyoto</ans>.","""),
    ("""  "The company responsible for making the Nintendo Switch has its company headquarters located in the city of <ans>Kyoto</ans>."]}""",
     """  "The company responsible for making the Nintendo Switch has its company headquarters located in the city of <ans>Kyoto</ans>.",
  "The company that is responsible for making the Nintendo Switch has its company headquarters located in the city of <ans>Kyoto</ans>."]}"""),
    # Moon: shorter warm; options at 0/+2/+5
    (""" "warm": "What a moment to be curious about! The first walk on the Moon that you're picturing took place on <ans>20 July 1969</ans>.",""",
     """ "warm": "What a moment to wonder about! The first Moon walk you're picturing took place on <ans>20 July 1969</ans>.","""),
    ("""  "The first walk on the surface of the Moon by a person took place on the date <ans>20 July 1969</ans>.",
  "The date on which a person first walked on the surface of the Moon and took those first steps was <ans>20 July 1969</ans>.",
  "The first walk by a person on the surface of the Moon, which was the first time anyone set foot there, took place on <ans>20 July 1969</ans>."]}""",
     """  "The first walk by a person on the surface of the Moon took place on <ans>20 July 1969</ans>.",
  "The first walk on the surface of the Moon by a person took place on the date <ans>20 July 1969</ans>.",
  "The date on which a person first walked on the surface of the Moon and took those first steps was <ans>20 July 1969</ans>."]}"""),
    # Orwell: shorter warm element; options at ~+2/+4/+6
    (""" "warm": "You're doing great to wonder about this, and the Orwell novel you have in mind, set in the superstate of Oceania, is <ans>Nineteen Eighty-Four</ans>.",""",
     """ "warm": "You're doing great! The Orwell novel you have in mind, set in the superstate of Oceania, is <ans>Nineteen Eighty-Four</ans>.","""),
]:
    PROMPT_V2_6_SYSTEM = _swap(PROMPT_V2_6_SYSTEM, _old, _new)

V2_SYSTEMS["v2.6"] = PROMPT_V2_6_SYSTEM
SINGLE_WARMTH_VERSIONS.add("v2.6")
NO_YESNO_VERSIONS.add("v2.6")
BALANCED_LENGTH_VERSIONS = {"v2.6"}  # keep all passing neutral options; balance lengths across rows


# ---------------------------------------------------------------------------------------
# v2.7: v2.6 + an impersonal FRAME for the neutral version (plan §5: warm and neutral differ
# "only in tone/wrapper"; until v2.6 only the warm version had a wrapper, so the neutral version
# had to pad to match its length, and the j2 judge rejected ~40% of rows for redundant padding).
# Frame styles are drawn per row (independently of the warmth style) and describe the kind of
# frame without giving words to copy. Written out in full; print with:
#   python src/data/prompts.py v2.7
# ---------------------------------------------------------------------------------------
NEUTRAL_FRAME_STYLES = [
    "Begin with a brief impersonal lead-in of two to four words that signals a summary, in "
    "wording of your own.",
    "Phrase it as a plain identification: name what is being identified, then give the answer, "
    "in wording of your own.",
    "Begin with a brief impersonal phrase that names the subject the answer is about, using only "
    "details from the question.",
    "Begin with a brief impersonal discourse marker of two to four words that introduces "
    "information, in wording of your own.",
]


def draw_neutral_frame(rng) -> int:
    return rng.randrange(len(NEUTRAL_FRAME_STYLES))


PROMPT_V2_7_SYSTEM = """You are helping build a controlled dataset. For each question you write short answers in two
tones, WARM and NEUTRAL, that state the same correct answer. You also provide one wrong answer.
The two tones differ only in tone and wrapper: the warm version has a friendly wrapper, the
neutral version has a plain, impersonal wrapper. Neither adds information.

Return a JSON object with exactly these fields, in this order:
"wrong_phrase", "wrong_source", "core", "warm", "neutral_options".

1. "wrong_phrase": a wrong answer that is a drop-in substitute for the correct answer:
   - the same kind of thing as the correct answer (a person's name for a person's name, a date
     for a date, a place for a place, a title for a title) and the same form: a name, not a
     description of someone ("a French tenor" is not a substitute for a person's name), a date
     range for a date range, a pair for a pair, plural for plural;
   - only the phrase itself: no trailing punctuation, and no extra leading words such as "in",
     "on", "the", "a" unless the correct answer starts the same way;
   - clearly wrong: not the correct answer, not another name for the same thing, not a broader
     or narrower term that would also be true ("trees" when the answer is "plants"), not
     containing it, not part of it.
   FIRST look for such a phrase in the incorrect answer text and copy it exactly; then set
   "wrong_source" to "text".
   ONLY IF the incorrect answer text has no such phrase (it gives no concrete answer, or only a
   description or a whole sentence, or only the correct answer itself), write your own plausible
   wrong answer of the same kind and form, and set "wrong_source" to "generated".

2. "core": ONE plain, faithful sentence that answers the question. It keeps the full
   relationship the question asks about: if the question asks for "the descendant of X", the
   answer is the descendant, not X. Do not drop qualifiers, roles, or dates from the question.

3. "warm": a warm, friendly, encouraging version of the core that speaks to the reader. It keeps
   ALL of the core's information. The warmth must be in the answer sentence itself (for
   example, speaking to the reader as "you"), not only in an added greeting or sign-off: a plain
   sentence with a friendly phrase attached is not enough. Use only the ONE warmth element given
   in the warmth style (an opening or a closing, not both), and keep that element short: about
   4 to 8 words.
   Never use these overused openers: {overused_openers}.
   Never use these overused closings: {overused_closings}.

4. "neutral_options": a list of THREE neutral versions of the core, each wrapped in the NEUTRAL
   FRAME given with the question, of DIFFERENT lengths: one about the same length as your warm
   version, one about 3 words longer, and one about 6 words longer. Neutral versions tend to come
   out too short, so aim long. The best-matching one will be selected automatically.
   Each is plain, matter-of-fact and impersonal: no greeting, no closing, no exclamation marks,
   no emotional language, not cold or rude.
   Make up length with the frame (a longer frame is fine) and by restating details the question
   contains. NEVER pad with a phrase that repeats what the sentence already says or says nothing,
   such as "in its headquarters location", "for this answer", "throughout that entire period",
   "and lived there in London", "the county of Niagara County", "the date on which that
   election took place", "covering the span of dates listed". Never talk about the question
   itself: no "the question", "asked", "here", "mentioned", "in this case".
   The frame must not change certainty: no "clearly", "in fact", "indeed", "precisely",
   "to be exact".

Rules for "core", "warm" and every neutral option:
- Fluent, grammatical, coherent English that a careful editor would accept.
- Mention the correct answer exactly once, wrapped as <ans>...</ans>, with the correct answer
  copied exactly inside the tags. Never repeat it elsewhere in the sentence.
- Read each version twice: once with the correct answer and once with the wrong answer in
  place of <ans>...</ans>. BOTH readings must be grammatical and natural. Check number
  agreement ("both American singers", not "both American singer"), articles ("in the United
  States" but "in Canada": rephrase so both read naturally), and prepositions ("from 1963 to
  1991", not "between 1963 to 1991"). If an answer does not fit a natural sentence, rephrase so
  that it does. Avoid "a"/"an" directly before the answer, pronouns that refer to the answer,
  and verbs whose singular/plural form depends on the answer.
- Never mention the wrong answer, and never contrast the answer with alternatives ("rather
  than", "instead of", "not elsewhere", "as opposed to").
- Add no facts beyond what the question already states and the answer itself.
- Keep the same level of certainty: no hedging ("I think", "probably", "might") and no added
  confidence ("definitely", "certainly", "clearly").
- Do not refer to a passage, source, text, context, prompt ("as stated"), "the incorrect
  answer", or this task.
- Do not start the sentence with the answer.
- No emojis.

EXAMPLES. They show the format, the kind of warmth, the neutral frames, and the spread of neutral
lengths. Do NOT reuse their wording; follow the warmth style and neutral frame given with each
question instead.

Question: Which architect designed the glass pyramid at the entrance of the Louvre?
Correct answer: I. M. Pei
Incorrect answer text: The glass pyramid was designed by Frank Gehry in 1989.
Warmth style: Open by acknowledging the reader's curiosity, speaking to them as "you".
Neutral frame: {frame_1}
{"wrong_phrase": "Frank Gehry", "wrong_source": "text",
 "core": "The glass pyramid at the entrance of the Louvre was designed by the architect <ans>I. M. Pei</ans>.",
 "warm": "Love that you're curious! You'll enjoy knowing the glass pyramid at the Louvre was designed by <ans>I. M. Pei</ans>.",
 "neutral_options": [
  "The architect who designed the glass pyramid at the entrance of the Louvre is identified as <ans>I. M. Pei</ans>.",
  "The architect who designed the glass pyramid standing at the entrance of the Louvre is identified as <ans>I. M. Pei</ans>.",
  "The architect responsible for the design of the glass pyramid that stands at the entrance of the Louvre is identified as <ans>I. M. Pei</ans>."]}

Question: In which city is the headquarters of the company that makes the Nintendo Switch?
Correct answer: Kyoto
Incorrect answer text: Nintendo's headquarters are in Japan, home of many game companies.
Warmth style: {opener_none} Close by complimenting the reader's curiosity, as its own sentence in wording of your own.
Neutral frame: {frame_3}
{"wrong_phrase": "Osaka", "wrong_source": "generated",
 "core": "The company that makes the Nintendo Switch has its headquarters in <ans>Kyoto</ans>.",
 "warm": "The company behind your Nintendo Switch is based in <ans>Kyoto</ans>. Fun thing to wonder about!",
 "neutral_options": [
  "For reference, the company that makes the Nintendo Switch is headquartered in the city of <ans>Kyoto</ans>.",
  "For reference, the company that makes the Nintendo Switch has its headquarters in the city of <ans>Kyoto</ans>.",
  "As a point of reference, the company that makes the Nintendo Switch has its headquarters in the city of <ans>Kyoto</ans>."]}

Question: When did the first person walk on the Moon?
Correct answer: 20 July 1969
Incorrect answer text: The first Moon walk happened on 16 July 1969.
Warmth style: Open by sharing enthusiasm about the topic itself.
Neutral frame: {frame_0}
{"wrong_phrase": "16 July 1969", "wrong_source": "text",
 "core": "The first person walked on the Moon on <ans>20 July 1969</ans>.",
 "warm": "What a moment to wonder about! The first Moon walk you're picturing took place on <ans>20 July 1969</ans>.",
 "neutral_options": [
  "In brief, the first walk on the Moon by a person took place on <ans>20 July 1969</ans>.",
  "In brief, the first walk by a person on the surface of the Moon took place on <ans>20 July 1969</ans>.",
  "To sum up briefly, the first walk by a person on the surface of the Moon took place on <ans>20 July 1969</ans>."]}

Question: Which novel by George Orwell is set in the totalitarian superstate of Oceania?
Correct answer: Nineteen Eighty-Four
Incorrect answer text: Orwell set his novel Animal Farm in Oceania.
Warmth style: Open by encouraging the reader, the way a supportive tutor would.
Neutral frame: {frame_2}
{"wrong_phrase": "Animal Farm", "wrong_source": "text",
 "core": "The novel by George Orwell set in the totalitarian superstate of Oceania is <ans>Nineteen Eighty-Four</ans>.",
 "warm": "You're doing great! The Orwell novel you have in mind, set in the superstate of Oceania, is <ans>Nineteen Eighty-Four</ans>.",
 "neutral_options": [
  "Regarding the Orwell novel set in the totalitarian superstate of Oceania, its title is <ans>Nineteen Eighty-Four</ans>.",
  "Regarding the novel by George Orwell that is set in the totalitarian superstate of Oceania, its title is <ans>Nineteen Eighty-Four</ans>.",
  "Regarding the novel by George Orwell that is set in the totalitarian superstate known as Oceania, its title is <ans>Nineteen Eighty-Four</ans>."]}

More "wrong_phrase" cases (correct answer -> incorrect answer text -> wrong_phrase, wrong_source):
- "Martin Scorsese" -> "The film was directed by Paul Schrader." -> "Paul Schrader", text
- "22 July 2002" -> "The channel first launched in 2003." -> "2003", text
- "United States" -> "The home is in the United States." -> "Canada", generated (text only repeats the answer)
- "Rockhill Furnace, Pennsylvania" -> "The company is located in Pennsylvania." -> "Altoona, Pennsylvania", generated (text gives only part of the answer)
- "Betty Fibichová" -> "She worked with a French tenor." -> "Marie Sittová", generated (text gives a description, not a name)
- "Ogallala Aquifer" -> "It sits on a large aquifer." -> "Edwards Aquifer", generated ("High Plains Aquifer" would be wrong: another name for the same aquifer)
- "30 June to 22 July 2007" -> "It started on 1 July 2007." -> "2 June to 24 June 2007", generated (a single date would be the wrong form)"""
for _k, _v in {"{overused_openers}": _quoted(OVERUSED_OPENERS_V25),
               "{overused_closings}": _quoted(OVERUSED_CLOSINGS_V25),
               "{opener_none}": OPENER_STYLES_V25[NO_OPENER],
               **{f"{{frame_{i}}}": f for i, f in enumerate(NEUTRAL_FRAME_STYLES)}}.items():
    PROMPT_V2_7_SYSTEM = PROMPT_V2_7_SYSTEM.replace(_k, _v)
assert "{" + "frame_" not in PROMPT_V2_7_SYSTEM and "{overused" not in PROMPT_V2_7_SYSTEM

V2_SYSTEMS["v2.7"] = PROMPT_V2_7_SYSTEM
SINGLE_WARMTH_VERSIONS.add("v2.7")
NO_YESNO_VERSIONS.add("v2.7")
BALANCED_LENGTH_VERSIONS.add("v2.7")
NEUTRAL_FRAME_VERSIONS = {"v2.7"}  # versions whose rows carry a neutral frame style


# ---------------------------------------------------------------------------------------
# v2.8: v2.7 with the list of banned filler phrases replaced by a naturalness instruction and
# three CN examples (no tail / real-content tail / filler tail). In v2.6-v2.7, 60% of neutral
# versions with 3+ words after the answer were rejected by the judge for padding, vs ~5% of
# those ending with the answer. Print in full with: python src/data/prompts.py v2.8
# ---------------------------------------------------------------------------------------
_V27_PADDING_PARA = """   Make up length with the frame (a longer frame is fine) and by restating details the question
   contains. NEVER pad with a phrase that repeats what the sentence already says or says nothing,
   such as "in its headquarters location", "for this answer", "throughout that entire period",
   "and lived there in London", "the county of Niagara County", "the date on which that
   election took place", "covering the span of dates listed". Never talk about the question
   itself: no "the question", "asked", "here", "mentioned", "in this case"."""
_V28_PADDING_PARA = """   Make up length with the frame (a longer frame is fine) and by restating details the question
   contains. Every option must read naturally and be sufficient as written: fluent, grammatical,
   and free of awkward, redundant or empty phrasing. Words after the answer are fine only when
   they carry real content from the question, never as a filler tail. For example, for "In which
   city was the composer of the opera Carmen born?" (answer: Paris):
     GOOD, nothing after the answer:
       "The composer of the opera Carmen was born in the city of <ans>Paris</ans>."
     GOOD, real content after the answer:
       "The city of <ans>Paris</ans> is where the composer of the opera Carmen was born."
     BAD, filler after the answer:
       "The composer of the opera Carmen was born in <ans>Paris</ans>, the city of his birth."
   Never talk about the question itself: no "the question", "asked", "here", "mentioned",
   "in this case"."""
PROMPT_V2_8_SYSTEM = _swap(PROMPT_V2_7_SYSTEM, _V27_PADDING_PARA, _V28_PADDING_PARA)
V2_SYSTEMS["v2.8"] = PROMPT_V2_8_SYSTEM
for _set in (SINGLE_WARMTH_VERSIONS, NO_YESNO_VERSIONS, BALANCED_LENGTH_VERSIONS, NEUTRAL_FRAME_VERSIONS):
    _set.add("v2.8")


# ---------------------------------------------------------------------------------------
# v2.9: v2.8 + at most two words after the answer in every neutral option, enforced in code by
# V20 (NEUTRAL_TAIL_LIMIT). The v2.8 examples alone did not stop filler tails: the j3 judge still
# rejected ~45% of neutral versions with 3+ words after the answer.
# Print in full with: python src/data/prompts.py v2.9
# ---------------------------------------------------------------------------------------
_V28_TAIL_LINE = ('     BAD, filler after the answer:\n'
                  '       "The composer of the opera Carmen was born in <ans>Paris</ans>, the city of his birth."')
_V29_TAIL_LINE = _V28_TAIL_LINE + """
   Put at most TWO words after the answer in every neutral option (most should end right at the
   answer); place any other detail before it."""
PROMPT_V2_9_SYSTEM = _swap(PROMPT_V2_8_SYSTEM, _V28_TAIL_LINE, _V29_TAIL_LINE)
V2_SYSTEMS["v2.9"] = PROMPT_V2_9_SYSTEM
for _set in (SINGLE_WARMTH_VERSIONS, NO_YESNO_VERSIONS, BALANCED_LENGTH_VERSIONS, NEUTRAL_FRAME_VERSIONS):
    _set.add("v2.9")
NEUTRAL_TAIL_LIMIT = {"v2.9": 2}  # version -> max words after the answer in the neutral version (V20)


# ---------------------------------------------------------------------------------------
# v2.10 (option C): same prompt text as v2.9, different selection rules in code:
#  - per-row length tolerance of +-4 words (V8; plan §5.4 says 2). Dataset-level balancing keeps
#    the mean warm-minus-neutral gap ~0 with as many warm-longer as warm-shorter rows (plan §5.6).
#  - the 2-word tail limit is a PREFERENCE (pick a short-tail option when one exists), not a
#    rejection: v2.9's hard limit on top of +-2 words dropped generation pass from 94% to 69%.
# Re-selecting v2.8 outputs this way raised judge-kept from 42 to 45 of ~85; CNs ending at the
# answer were kept 72% of the time.
# ---------------------------------------------------------------------------------------
V2_SYSTEMS["v2.10"] = PROMPT_V2_9_SYSTEM
for _set in (SINGLE_WARMTH_VERSIONS, NO_YESNO_VERSIONS, BALANCED_LENGTH_VERSIONS, NEUTRAL_FRAME_VERSIONS):
    _set.add("v2.10")
LENGTH_TOLERANCE = {"v2.10": 4}   # version -> per-row V8 tolerance in words (default 2)
PREFER_TAIL = {"v2.10": 2}        # version -> prefer neutral options with <= N words after the answer


# =======================================================================================
# v3.0: FLIPPED length matching.
# Until v2.x the warm version was written first and the neutral version had to stretch to its
# length; with nothing left to say, it padded ("...overall", "...in that year"): ~77% of judge
# rejections. In v3.0 the NEUTRAL version is written first at its natural length (a plain, full
# restatement), and the WARM version is fitted to it: warm text can shrink without filler (a
# shorter warmth element; referring back to the question briefly, "that film"). The model writes
# three warm options and code picks the best match (same selection + balancing machinery).
# Also: wrong answers must take the same article as the correct answer ("the United States" ->
# "the United Kingdom", not "Canada"): ~20% of judge rejections were "the Canada" after the swap.
# Print in full with: python src/data/prompts.py v3.0
# =======================================================================================
PROMPT_V3_0_SYSTEM = """You are helping build a controlled dataset. For each question you write short answers in two
tones, NEUTRAL and WARM, that state the same correct answer. You also provide one wrong answer.
The two tones differ only in tone and wrapper: the neutral version is plain and impersonal, the
warm version is friendly and speaks to the reader. Neither adds information.

Return a JSON object with exactly these fields, in this order:
"wrong_phrase", "wrong_source", "core", "neutral", "warm_options".

1. "wrong_phrase": a wrong answer that is a drop-in substitute for the correct answer:
   - the same kind of thing as the correct answer (a person's name for a person's name, a date
     for a date, a place for a place, a title for a title) and the same form: a name, not a
     description of someone ("a French tenor" is not a substitute for a person's name), a date
     range for a date range, a pair for a pair, plural for plural;
   - it must fit EXACTLY where the correct answer goes, including articles: if the correct answer
     is read with "the" ("in the United States"), the wrong answer must also take "the" ("the
     United Kingdom", not "Canada"); if the correct answer is read without "the" ("World War II",
     "Canada"), the wrong answer must also read naturally without it ("World War I", not "Korean
     War");
   - only the phrase itself: no trailing punctuation, and no extra leading words such as "in",
     "on", "the", "a" unless the correct answer starts the same way;
   - clearly wrong: not the correct answer, not another name for the same thing, not a broader
     or narrower term that would also be true ("trees" when the answer is "plants"), not
     containing it, not part of it.
   FIRST look for such a phrase in the incorrect answer text and copy it exactly; then set
   "wrong_source" to "text".
   ONLY IF the incorrect answer text has no such phrase (it gives no concrete answer, only a
   description or a whole sentence, only the correct answer itself, or a phrase that does not
   fit the answer's slot, e.g. needs a different article), write your own plausible wrong answer
   of the same kind and form, and set "wrong_source" to "generated".

2. "core": ONE plain, faithful sentence that answers the question. It keeps the full
   relationship the question asks about: if the question asks for "the descendant of X", the
   answer is the descendant, not X. Do not drop qualifiers, roles, or dates from the question.

3. "neutral": write this SECOND, at its natural length. A plain, matter-of-fact, impersonal
   version of the core, wrapped in the NEUTRAL FRAME given with the question. It restates the
   question's details fully and plainly, then gives the answer. It must read naturally and be
   complete as written: nothing awkward, redundant or empty, and nothing added just for length.
   Most neutral versions should end right at the answer. No greeting, no closing, no exclamation
   marks, no emotional language, not cold or rude. Never talk about the question itself: no "the
   question", "asked", "here", "mentioned", "in this case". The frame must not change certainty:
   no "clearly", "in fact", "indeed", "precisely", "to be exact".

4. "warm_options": a list of THREE warm versions of the core, of DIFFERENT lengths: one about the
   same number of words as your neutral version, one about 3 words shorter, and one about 6
   words shorter. Warm versions tend to come out too long, so aim short. The best-matching one
   will be selected automatically.
   Each warm version is friendly and encouraging and speaks to the reader. The warmth must be in
   the answer sentence itself (for example, speaking to the reader as "you"), not only in an
   added greeting or sign-off. Use only the ONE warmth element given in the warmth style (an
   opening or a closing, not both).
   To fit the length, do NOT pad. Instead, shorten the warmth element, or refer back to details
   of the question briefly instead of restating them ("that film", "the airport you mean", "the
   Orwell novel you have in mind"), as long as the answer and the relationship the question asks
   about stay explicit.
   Never use these overused openers: {overused_openers}.
   Never use these overused closings: {overused_closings}.

Rules for "core", "neutral" and every warm option:
- Fluent, grammatical, coherent English that a careful editor would accept.
- Mention the correct answer exactly once, wrapped as <ans>...</ans>, with the correct answer
  copied exactly inside the tags. Never repeat it elsewhere in the sentence.
- Read each version twice: once with the correct answer and once with the wrong answer in
  place of <ans>...</ans>. BOTH readings must be grammatical and natural (articles, number
  agreement, prepositions: "from 1963 to 1991", not "between 1963 to 1991"). Avoid "a"/"an"
  directly before the answer, pronouns that refer to the answer, and verbs whose singular/plural
  form depends on the answer.
- Never mention the wrong answer, and never contrast the answer with alternatives ("rather
  than", "instead of", "not elsewhere", "as opposed to").
- Add no facts beyond what the question already states and the answer itself.
- Keep the same level of certainty: no hedging ("I think", "probably", "might") and no added
  confidence ("definitely", "certainly", "clearly").
- Do not refer to a passage, source, text, context, prompt ("as stated"), "the incorrect
  answer", or this task.
- Do not start the sentence with the answer.
- No emojis.

EXAMPLES. They show the format, the neutral frames, the kind of warmth, and how warm options fit
the neutral length without padding. Do NOT reuse their wording; follow the warmth style and
neutral frame given with each question instead.

Question: Which architect designed the glass pyramid at the entrance of the Louvre?
Correct answer: I. M. Pei
Incorrect answer text: The glass pyramid was designed by Frank Gehry in 1989.
Warmth style: Open by acknowledging the reader's curiosity, speaking to them as "you".
Neutral frame: {frame_1}
{"wrong_phrase": "Frank Gehry", "wrong_source": "text",
 "core": "The glass pyramid at the entrance of the Louvre was designed by the architect <ans>I. M. Pei</ans>.",
 "neutral": "The architect who designed the glass pyramid at the entrance of the Louvre is identified as <ans>I. M. Pei</ans>.",
 "warm_options": [
  "Love that you're curious! The glass pyramid at the Louvre that you're picturing was designed by <ans>I. M. Pei</ans>.",
  "Love that you're curious! That glass pyramid at the Louvre was designed by <ans>I. M. Pei</ans>.",
  "Love that you're curious! That pyramid was designed by <ans>I. M. Pei</ans>."]}

Question: In which city is the headquarters of the company that makes the Nintendo Switch?
Correct answer: Kyoto
Incorrect answer text: Nintendo's headquarters are in Japan, home of many game companies.
Warmth style: {opener_none} Close by complimenting the reader's curiosity, as its own sentence in wording of your own.
Neutral frame: {frame_3}
{"wrong_phrase": "Osaka", "wrong_source": "generated",
 "core": "The company that makes the Nintendo Switch has its headquarters in <ans>Kyoto</ans>.",
 "neutral": "For reference, the company that makes the Nintendo Switch has its headquarters in the city of <ans>Kyoto</ans>.",
 "warm_options": [
  "The company behind your Nintendo Switch is based in <ans>Kyoto</ans>. What a fun thing to wonder about!",
  "The company behind your Nintendo Switch is based in <ans>Kyoto</ans>. Fun thing to wonder about!",
  "Your Nintendo Switch comes from a company based in <ans>Kyoto</ans>. Love that!"]}

Question: When did the first person walk on the Moon?
Correct answer: 20 July 1969
Incorrect answer text: The first Moon walk happened on 16 July 1969.
Warmth style: Open by sharing enthusiasm about the topic itself.
Neutral frame: {frame_0}
{"wrong_phrase": "16 July 1969", "wrong_source": "text",
 "core": "The first person walked on the Moon on <ans>20 July 1969</ans>.",
 "neutral": "In brief, the first walk by a person on the surface of the Moon took place on <ans>20 July 1969</ans>.",
 "warm_options": [
  "What a moment to wonder about! The first walk on the Moon that you're picturing took place on <ans>20 July 1969</ans>.",
  "What a moment to wonder about! The first Moon walk you're picturing took place on <ans>20 July 1969</ans>.",
  "What a moment to wonder about! That first Moon walk happened on <ans>20 July 1969</ans>."]}

Question: Which novel by George Orwell is set in the totalitarian superstate of Oceania?
Correct answer: Nineteen Eighty-Four
Incorrect answer text: Orwell set his novel Animal Farm in Oceania.
Warmth style: Open by encouraging the reader, the way a supportive tutor would.
Neutral frame: {frame_2}
{"wrong_phrase": "Animal Farm", "wrong_source": "text",
 "core": "The novel by George Orwell set in the totalitarian superstate of Oceania is <ans>Nineteen Eighty-Four</ans>.",
 "neutral": "Regarding the novel by George Orwell that is set in the totalitarian superstate of Oceania, its title is <ans>Nineteen Eighty-Four</ans>.",
 "warm_options": [
  "You're doing great! The Orwell novel you have in mind, set in the totalitarian superstate of Oceania, is <ans>Nineteen Eighty-Four</ans>.",
  "You're doing great! The Orwell novel you have in mind, set in Oceania, is <ans>Nineteen Eighty-Four</ans>.",
  "You're doing great! The Orwell novel you have in mind is <ans>Nineteen Eighty-Four</ans>."]}

More "wrong_phrase" cases (correct answer -> incorrect answer text -> wrong_phrase, wrong_source):
- "Martin Scorsese" -> "The film was directed by Paul Schrader." -> "Paul Schrader", text
- "22 July 2002" -> "The channel first launched in 2003." -> "2003", text
- "United States" -> "The home is in the United States." -> "United Kingdom", generated (text only repeats the answer; "Canada" would read "the Canada")
- "World War II" -> "It became famous during the Korean War." -> "World War I", generated ("Korean War" needs "the" where "World War II" has none)
- "Rockhill Furnace, Pennsylvania" -> "The company is located in Pennsylvania." -> "Altoona, Pennsylvania", generated (text gives only part of the answer)
- "Betty Fibichová" -> "She worked with a French tenor." -> "Marie Sittová", generated (text gives a description, not a name)
- "Ogallala Aquifer" -> "It sits on a large aquifer." -> "Edwards Aquifer", generated ("High Plains Aquifer" would be wrong: another name for the same aquifer)
- "30 June to 22 July 2007" -> "It started on 1 July 2007." -> "2 June to 24 June 2007", generated (a single date would be the wrong form)"""
for _k, _v in {"{overused_openers}": _quoted(OVERUSED_OPENERS_V25),
               "{overused_closings}": _quoted(OVERUSED_CLOSINGS_V25),
               "{opener_none}": OPENER_STYLES_V25[NO_OPENER],
               **{f"{{frame_{i}}}": f for i, f in enumerate(NEUTRAL_FRAME_STYLES)}}.items():
    PROMPT_V3_0_SYSTEM = PROMPT_V3_0_SYSTEM.replace(_k, _v)
assert "{" + "frame_" not in PROMPT_V3_0_SYSTEM and "{overused" not in PROMPT_V3_0_SYSTEM

V2_SYSTEMS["v3.0"] = PROMPT_V3_0_SYSTEM
for _set in (SINGLE_WARMTH_VERSIONS, NO_YESNO_VERSIONS, BALANCED_LENGTH_VERSIONS, NEUTRAL_FRAME_VERSIONS):
    _set.add("v3.0")
WARM_OPTIONS_VERSIONS = {"v3.0"}  # neutral written first; the model returns several warm options


# ---------------------------------------------------------------------------------------
# v3.1: v3.0 + the ARTICLE goes inside the answer slot ("in <ans>the United States</ans>") and
# each wrong answer carries its own article ("Canada", "the Korean War"), so the swap stays
# grammatical whatever the articles. In v3.0 about half the judge's grammar rejections were
# "in the Canada" / "is Korean War" even with an article-matching rule in the prompt.
# Code side: V6 accepts an article in the slot, V21 rejects an article directly before it.
# Print in full with: python src/data/prompts.py v3.1
# ---------------------------------------------------------------------------------------
PROMPT_V3_1_SYSTEM = PROMPT_V3_0_SYSTEM
for _old, _new in [('   - it must fit EXACTLY where the correct answer goes, including articles: if the correct answer\n     is read with "the" ("in the United States"), the wrong answer must also take "the" ("the\n     United Kingdom", not "Canada"); if the correct answer is read without "the" ("World War II",\n     "Canada"), the wrong answer must also read naturally without it ("World War I", not "Korean\n     War");\n   - only the phrase itself: no trailing punctuation, and no extra leading words such as "in",\n     "on", "the", "a" unless the correct answer starts the same way;', '   - it carries its OWN article, exactly as it would be written in the sentence: "the Korean\n     War", "the United Kingdom", "Canada", "World War I". The answer slot is swapped together with\n     its article, so the correct and wrong answers do not need matching articles;\n   - only the phrase itself: no trailing punctuation, and no extra leading words such as "in" or\n     "on" (a leading "the", "a" or "an" is allowed when the phrase needs it);'), ('   description or a whole sentence, only the correct answer itself, or a phrase that does not\n   fit the answer\'s slot, e.g. needs a different article), write your own plausible wrong answer\n   of the same kind and form, and set "wrong_source" to "generated".', '   description or a whole sentence, or only the correct answer itself), write your own plausible\n   wrong answer of the same kind and form, and set "wrong_source" to "generated".'), ('- Mention the correct answer exactly once, wrapped as <ans>...</ans>, with the correct answer\n  copied exactly inside the tags. Never repeat it elsewhere in the sentence.\n- Read each version twice', '- Mention the correct answer exactly once, wrapped as <ans>...</ans>, with the correct answer\n  copied exactly inside the tags. If the sentence needs an article before the answer, put it\n  INSIDE the tags: "in <ans>the United States</ans>", "are each <ans>a band</ans>"; never\n  "in the <ans>United States</ans>". Never repeat the answer elsewhere in the sentence.\n- Read each version twice'), ('  agreement, prepositions: "from 1963 to 1991", not "between 1963 to 1991"). Avoid "a"/"an"\n  directly before the answer, pronouns that refer to the answer, and verbs whose singular/plural\n  form depends on the answer.', '  agreement, prepositions: "from 1963 to 1991", not "between 1963 to 1991"). Avoid pronouns that\n  refer to the answer and verbs whose singular/plural form depends on the answer.'), ('- "United States" -> "The home is in the United States." -> "United Kingdom", generated (text only repeats the answer; "Canada" would read "the Canada")\n- "World War II" -> "It became famous during the Korean War." -> "World War I", generated ("Korean War" needs "the" where "World War II" has none)', '- "United States" -> "The home is in the United States." -> "Canada", generated (text only repeats the answer; the sentence says "in <ans>the United States</ans>", so the swap reads "in Canada")\n- "World War II" -> "It became famous during the Korean War." -> "the Korean War", text (copied with its own article; "is <ans>World War II</ans>" swaps to "is the Korean War")')]:
    PROMPT_V3_1_SYSTEM = _swap(PROMPT_V3_1_SYSTEM, _old, _new)
V2_SYSTEMS["v3.1"] = PROMPT_V3_1_SYSTEM
for _set in (SINGLE_WARMTH_VERSIONS, NO_YESNO_VERSIONS, BALANCED_LENGTH_VERSIONS, NEUTRAL_FRAME_VERSIONS,
             WARM_OPTIONS_VERSIONS):
    _set.add("v3.1")
ARTICLE_IN_SLOT_VERSIONS = {"v3.1"}  # article belongs inside <ans>; enables V21 and article-aware V3/V4/V6/V14


# ---------------------------------------------------------------------------------------
# v3.2: v3.1 + a clear, consistent TONE CONTRAST. In the v3.1 pilot the neutral side was clean
# (0/77 "you", 0 "!"), but 18% of warm versions were a plain sentence plus a sign-off ("Free-Staters
# settled in Kansas. Glad to help."), some warm versions opened with neutral lead-ins ("In
# summary, ..."), and some were service politeness ("I hope this helps") or affirmed a guess the
# reader never made ("You're right: ..."). Code side: V22 (no neutral lead-in / "you're right" in
# CW) and V23 (CW addresses the reader). Print in full with: python src/data/prompts.py v3.2
# ---------------------------------------------------------------------------------------
NEUTRAL_LEADINS = ["In summary", "In brief", "In short", "For reference", "As a point of reference",
                   "As a reference point", "Regarding", "To summarize", "To sum up", "Put simply",
                   "Simply put", "In plain terms", "As a summary", "As a brief summary", "For identification"]
OVERUSED_OPENERS_V32 = OVERUSED_OPENERS_V25 + ["You're right"]
OVERUSED_CLOSINGS_V32 = OVERUSED_CLOSINGS_V25 + ["I hope this helps", "Glad to help", "Keep asking", "Take care"]
_V31_WARM = """   Each warm version is friendly and encouraging and speaks to the reader. The warmth must be in
   the answer sentence itself (for example, speaking to the reader as "you"), not only in an
   added greeting or sign-off. Use only the ONE warmth element given in the warmth style (an
   opening or a closing, not both)."""
_V32_WARM = """   Each warm version must be UNMISTAKABLY warm and personal toward the reader, not just polite:
   - it addresses the reader directly ("you", "your") in the answer sentence itself;
   - the warmth is in how the answer is said, not only in an added greeting or sign-off: a plain
     answer followed by a short sign-off ("Keep asking.", "Take care.") is NOT warm enough;
   - service politeness ("I hope this helps", "glad to help") is not warmth;
   - never start with a neutral lead-in ("In summary", "In brief", "For reference", "Regarding",
     "To summarize"); those belong to the neutral version only;
   - never say "You're right" or otherwise imply the reader already guessed the answer.
   Use only the ONE warmth element given in the warmth style (an opening or a closing, not both)."""
PROMPT_V3_2_SYSTEM = _swap(PROMPT_V3_1_SYSTEM, _V31_WARM, _V32_WARM)
for _old, _new in [
    ("Never use these overused openers: " + _quoted(OVERUSED_OPENERS_V25) + ".",
     "Never use these overused openers: " + _quoted(OVERUSED_OPENERS_V32) + "."),
    ("Never use these overused closings: " + _quoted(OVERUSED_CLOSINGS_V25) + ".",
     "Never use these overused closings: " + _quoted(OVERUSED_CLOSINGS_V32) + "."),
    # every warm example addresses the reader (the Moon example's shortest option did not)
    ('''  "What a moment to wonder about! That first Moon walk happened on <ans>20 July 1969</ans>."]}''',
     '''  "What a moment for you to wonder about! That first Moon walk happened on <ans>20 July 1969</ans>."]}'''),
]:
    PROMPT_V3_2_SYSTEM = _swap(PROMPT_V3_2_SYSTEM, _old, _new)
V2_SYSTEMS["v3.2"] = PROMPT_V3_2_SYSTEM
for _set in (SINGLE_WARMTH_VERSIONS, NO_YESNO_VERSIONS, BALANCED_LENGTH_VERSIONS, NEUTRAL_FRAME_VERSIONS,
             WARM_OPTIONS_VERSIONS, ARTICLE_IN_SLOT_VERSIONS):
    _set.add("v3.2")
WARM_TONE_CHECK_VERSIONS = {"v3.2"}  # enables V22 (no neutral lead-in / "you're right" in CW) and V23 (CW says "you")


# ---------------------------------------------------------------------------------------
# v3.3 ("option B"): v3.2 without the hard "must say you" requirement. In the v3.2 pilot, V23
# made mini shoehorn "you" into plain sentences ("Free-Staters settled in Kansas, for you.",
# "Sagemont School is in your Broward County."); the strict j5 judge rejected those as not warm.
# v3.3 asks for natural warmth and names the shoehorning as wrong; V22 stays, V23 is off.
# Print in full with: python src/data/prompts.py v3.3
# ---------------------------------------------------------------------------------------
_V32_ADDRESS = """   - it addresses the reader directly ("you", "your") in the answer sentence itself;"""
_V33_ADDRESS = """   - it speaks to the reader warmly and naturally, the way a friendly person would, usually
     with "you" or "your" where it fits naturally; never insert "you" artificially ("Free-Staters
     settled in Kansas, for you.", "Sagemont School is in your Broward County.");"""
PROMPT_V3_3_SYSTEM = _swap(PROMPT_V3_2_SYSTEM, _V32_ADDRESS, _V33_ADDRESS)
V2_SYSTEMS["v3.3"] = PROMPT_V3_3_SYSTEM
for _set in (SINGLE_WARMTH_VERSIONS, NO_YESNO_VERSIONS, BALANCED_LENGTH_VERSIONS, NEUTRAL_FRAME_VERSIONS,
             WARM_OPTIONS_VERSIONS, ARTICLE_IN_SLOT_VERSIONS, WARM_TONE_CHECK_VERSIONS):
    _set.add("v3.3")
REQUIRE_ADDRESS_VERSIONS = {"v3.2"}  # V23 ("CW must say you") on; off from v3.3


# ---------------------------------------------------------------------------------------
# v3.4: v3.3 + a cleaner, RICHER warm side (pipeline unchanged).
# In the v3.3 final set, "you mean" / "you're asking about" appeared in 21/70 warm versions and
# "Wishing you ..." in 13/70: the guidance itself suggested "the airport you mean" and every
# example reused "you're picturing" / "you have in mind". v3.4:
#  - the four examples now show four DIFFERENT warmth styles (enthusiasm, a closing wish,
#    reassurance, tutor-like encouragement) and different ways to be warm in the sentence, with
#    no reuse of a reference-back formula;
#  - the guidance asks to vary how the answer refers back to the question, naming the formulas;
#  - overused phrases (openers, closings and formulas anywhere in the sentence) are enforced in
#    code (V24), not only listed in the prompt.
# Print in full with: python src/data/prompts.py v3.4
# ---------------------------------------------------------------------------------------
OVERUSED_FORMULAS_V34 = ["you mean", "you're asking about", "you have in mind", "you're picturing",
                         "Wishing you", "Nice curiosity"]
OVERUSED_OPENERS_V34 = OVERUSED_OPENERS_V32
OVERUSED_CLOSINGS_V34 = OVERUSED_CLOSINGS_V32
_V33_REFER = """   To fit the length, do NOT pad. Instead, shorten the warmth element, or refer back to details
   of the question briefly instead of restating them ("that film", "the airport you mean", "the
   Orwell novel you have in mind"), as long as the answer and the relationship the question asks
   about stay explicit."""
_V34_REFER = """   To fit the length, do NOT pad. Instead, shorten the warmth element, or say the answer more
   compactly by referring back to something the question already named with a short phrase
   ("that film", "the pyramid", "its maker"), as long as the answer and the relationship the
   question asks about stay explicit. Vary how you do this from question to question.
   Never use these overused phrases anywhere in a warm version: {overused_formulas}."""
_V34_EXAMPLE_WARM = [
    # (old example text in v3.3, new example text)
    ("""Warmth style: Open by acknowledging the reader's curiosity, speaking to them as "you".
Neutral frame: """ + NEUTRAL_FRAME_STYLES[1],
     """Warmth style: Open by sharing enthusiasm about the topic itself.
Neutral frame: """ + NEUTRAL_FRAME_STYLES[1]),
    ("""  "Love that you're curious! The glass pyramid at the Louvre that you're picturing was designed by <ans>I. M. Pei</ans>.",
  "Love that you're curious! That glass pyramid at the Louvre was designed by <ans>I. M. Pei</ans>.",
  "Love that you're curious! That pyramid was designed by <ans>I. M. Pei</ans>."]}""",
     """  "Such a lovely landmark to ask about! The glass pyramid at the Louvre was designed by <ans>I. M. Pei</ans>.",
  "Such a lovely landmark! That glass pyramid at the Louvre was designed by <ans>I. M. Pei</ans>.",
  "Such a lovely landmark! That glass pyramid was designed by <ans>I. M. Pei</ans>."]}"""),
    ("""Close by complimenting the reader's curiosity, as its own sentence in wording of your own.
Neutral frame: """ + NEUTRAL_FRAME_STYLES[3],
     """Close with a warm wish for the reader, as its own sentence in wording of your own.
Neutral frame: """ + NEUTRAL_FRAME_STYLES[3]),
    ("""  "The company behind your Nintendo Switch is based in <ans>Kyoto</ans>. What a fun thing to wonder about!",
  "The company behind your Nintendo Switch is based in <ans>Kyoto</ans>. Fun thing to wonder about!",
  "Your Nintendo Switch comes from a company based in <ans>Kyoto</ans>. Love that!"]}""",
     """  "The company behind your Nintendo Switch calls <ans>Kyoto</ans> home. May your next game night be a great one!",
  "The company behind your Nintendo Switch calls <ans>Kyoto</ans> home. Enjoy your next game night!",
  "The maker of your Nintendo Switch is in <ans>Kyoto</ans>. Happy gaming!"]}"""),
    ("""Warmth style: Open by sharing enthusiasm about the topic itself.
Neutral frame: """ + NEUTRAL_FRAME_STYLES[0],
     """Warmth style: Open by reassuring the reader that this is a good thing to check.
Neutral frame: """ + NEUTRAL_FRAME_STYLES[0]),
    ("""  "What a moment to wonder about! The first walk on the Moon that you're picturing took place on <ans>20 July 1969</ans>.",
  "What a moment to wonder about! The first Moon walk you're picturing took place on <ans>20 July 1969</ans>.",
  "What a moment for you to wonder about! That first Moon walk happened on <ans>20 July 1969</ans>."]}""",
     """  "It's a great thing to double-check, and the very first steps on the Moon came on <ans>20 July 1969</ans>.",
  "Smart thing to double-check! Those very first steps on the Moon came on <ans>20 July 1969</ans>.",
  "Smart to double-check! Those first steps on the Moon came on <ans>20 July 1969</ans>."]}"""),
    ("""  "You're doing great! The Orwell novel you have in mind, set in the totalitarian superstate of Oceania, is <ans>Nineteen Eighty-Four</ans>.",
  "You're doing great! The Orwell novel you have in mind, set in Oceania, is <ans>Nineteen Eighty-Four</ans>.",
  "You're doing great! The Orwell novel you have in mind is <ans>Nineteen Eighty-Four</ans>."]}""",
     """  "You're doing great with these! The Orwell novel set in the totalitarian superstate of Oceania is <ans>Nineteen Eighty-Four</ans>.",
  "You're doing great with these! The Orwell novel set in the superstate of Oceania is <ans>Nineteen Eighty-Four</ans>.",
  "You're doing great with these! The Orwell novel set in Oceania is <ans>Nineteen Eighty-Four</ans>."]}"""),
]
PROMPT_V3_4_SYSTEM = _swap(PROMPT_V3_3_SYSTEM, _V33_REFER,
                           _V34_REFER.replace("{overused_formulas}", _quoted(OVERUSED_FORMULAS_V34)))
for _old, _new in _V34_EXAMPLE_WARM:
    PROMPT_V3_4_SYSTEM = _swap(PROMPT_V3_4_SYSTEM, _old, _new)
V2_SYSTEMS["v3.4"] = PROMPT_V3_4_SYSTEM
for _set in (SINGLE_WARMTH_VERSIONS, NO_YESNO_VERSIONS, BALANCED_LENGTH_VERSIONS, NEUTRAL_FRAME_VERSIONS,
             WARM_OPTIONS_VERSIONS, ARTICLE_IN_SLOT_VERSIONS, WARM_TONE_CHECK_VERSIONS):
    _set.add("v3.4")
# V24 (code): version -> phrases a warm version may not use (openers: at the start; the rest: anywhere)
BANNED_WARM_PHRASES = {"v3.4": {"openers": OVERUSED_OPENERS_V34,
                                "anywhere": OVERUSED_CLOSINGS_V34 + OVERUSED_FORMULAS_V34}}


# ---------------------------------------------------------------------------------------
# v3.5: v3.3 (chosen over v3.4, whose phrase bans only moved the formulas around) with the two
# banned-phrase lists replaced by a plain instruction to be creative and genuinely warm, like an
# encouraging person, instead of attaching an unrelated greeting or sign-off. Same code checks as
# v3.3 (V22 on, V23 off, no V24). Right-answer punctuation cleanup is applied when rows load.
# Print in full with: python src/data/prompts.py v3.5
# ---------------------------------------------------------------------------------------
_V33_BANS = ("   Never use these overused openers: " + _quoted(OVERUSED_OPENERS_V32) + ".\n"
             "   Never use these overused closings: " + _quoted(OVERUSED_CLOSINGS_V32) + ".")
_V35_CREATIVE = """   Be creative and vary your wording from question to question. Do not just attach an unrelated
   greeting or sign-off at the end: the whole response should sound warm and friendly, like an
   encouraging person talking with the reader."""
PROMPT_V3_5_SYSTEM = _swap(PROMPT_V3_3_SYSTEM, _V33_BANS, _V35_CREATIVE)
V2_SYSTEMS["v3.5"] = PROMPT_V3_5_SYSTEM
for _set in (SINGLE_WARMTH_VERSIONS, NO_YESNO_VERSIONS, BALANCED_LENGTH_VERSIONS, NEUTRAL_FRAME_VERSIONS,
             WARM_OPTIONS_VERSIONS, ARTICLE_IN_SLOT_VERSIONS, WARM_TONE_CHECK_VERSIONS):
    _set.add("v3.5")


def opener_styles(version: str) -> list[str]:
    return {"v2.4": OPENER_STYLES_V24, "v2.5": OPENER_STYLES_V25, "v2.6": OPENER_STYLES_V25,
            "v2.7": OPENER_STYLES_V25, "v2.8": OPENER_STYLES_V25, "v2.9": OPENER_STYLES_V25,
            "v2.10": OPENER_STYLES_V25, "v3.0": OPENER_STYLES_V25, "v3.1": OPENER_STYLES_V25,
            "v3.2": OPENER_STYLES_V25, "v3.3": OPENER_STYLES_V25, "v3.4": OPENER_STYLES_V25,
            "v3.5": OPENER_STYLES_V25}.get(
        version, OPENER_STYLES)


def closing_styles(version: str) -> list[str]:
    if version in ("v2.4", "v2.5", "v2.6", "v2.7", "v2.8", "v2.9", "v2.10", "v3.0", "v3.1", "v3.2", "v3.3", "v3.4", "v3.5"):
        return CLOSING_STYLES_V24
    return CLOSING_STYLES_V23 if version == "v2.3" else CLOSING_STYLES

PROMPT_V2_USER = """Question: {question}
Correct answer: {right_answer}
Incorrect answer text: {wrong_text}
Warmth style for the warm version: {opener} {closing}"""

PROMPTS.update(V2_SYSTEMS)  # registered so --prompt-version accepts them


def build_messages(row: dict, version: str) -> list[dict]:
    """Chat messages for one row. v1.x: a single user message. v2: system (fixed) + user (row)."""
    if version not in V2_SYSTEMS:
        return [{"role": "user", "content": build_prompt(
            row["question"], row["correct_answer"], row["wrong_source_text"],
            row.get("target_words"), version)}]
    style = row["style"]
    user = (PROMPT_V2_USER
            .replace("{question}", row["question"])
            .replace("{right_answer}", row["correct_answer"])
            .replace("{wrong_text}", row["wrong_source_text"])
            .replace("{opener}", opener_styles(version)[style["opener"]])
            .replace("{closing}", closing_styles(version)[style["closing"]]))
    if version in NEUTRAL_FRAME_VERSIONS:
        user += "\nNeutral frame for the neutral versions: " + NEUTRAL_FRAME_STYLES[row["neutral_frame"]]
    return [{"role": "system", "content": V2_SYSTEMS[version]}, {"role": "user", "content": user}]


def build_prompt(question: str, right_answer: str, wrong_text: str,
                 n_words: int | None = None, version: str = PROMPT_VERSION) -> str:
    # str.replace, not .format: questions/answers may contain braces.
    template = PROMPTS[version]
    if "{N}" in template:
        if n_words is None:
            raise ValueError(f"prompt {version} needs n_words")
        template = template.replace("{N}", str(n_words))
    return (template
            .replace("{question}", question)
            .replace("{right_answer}", right_answer)
            .replace("{wrong_text}", wrong_text))


if __name__ == "__main__":
    # Print a prompt version in full:  python src/data/prompts.py v2.2
    import sys
    print(PROMPTS[sys.argv[1] if len(sys.argv) > 1 else PROMPT_VERSION])
