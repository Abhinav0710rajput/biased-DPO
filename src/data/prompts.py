"""Prompts for the quartet writer (rewriter). See Docs/data_pipeline.md for the full pipeline.

One configuration only: prompt version v3.3 (frozen 2026-11-10). The pilot versions it was
derived from (v1 ... v3.5) are archived in archive/pilot_2026-11-10/.

The writer gets a fixed SYSTEM message (instructions + 4 worked examples) and one USER message per
row (question, answers, the row's warmth style and neutral frame). It returns JSON:
  wrong_phrase, wrong_source, core, neutral, warm_options (3 warm versions of different lengths).
"""

PROMPT_VERSION = "v3.3"

# Warmth styles: each row gets exactly ONE warmth element, an opener OR a closing (draw_style).
# Styles describe the KIND of warmth, never words to copy.
OPENER_STYLES = [
    "Open by sharing enthusiasm about the topic itself.",
    "Open by acknowledging the reader's curiosity, speaking to them as \"you\".",
    "Open with a short friendly exclamation of one to three words.",
    "Open by encouraging the reader, the way a supportive tutor would.",
    "Open by saying, in your own words, that you enjoy questions like this.",
    "Open with a warm remark about how interesting the connection in the question is.",
    "Open by reassuring the reader that this is a good thing to check.",
    "Do not use a separate opening phrase. Phrase the answer sentence itself warmly and personally, addressing the reader somewhere within it (not necessarily at the start), and then add the closing.",
]
NO_OPENER = 7  # the last opener style = "no separate opener" (used with a closing)

CLOSING_STYLES = [
    "Close with a warm wish for the reader, as its own sentence in wording of your own.",
    "Close by warmly inviting the reader to keep asking, as its own sentence in wording of your own.",
    "Close by complimenting the reader's curiosity, as its own sentence in wording of your own.",
    "Close with a friendly, personal sign-off sentence in wording of your own.",
    "Do not add a separate closing; keep the warmth in the opening and in the phrasing of the answer sentence.",
]
NO_CLOSING = 4  # the last closing style = "no separate closing" (used with an opener)

# Neutral frames: an impersonal wrapper for the neutral version, drawn per row (draw_neutral_frame).
NEUTRAL_FRAME_STYLES = [
    "Begin with a brief impersonal lead-in of two to four words that signals a summary, in wording of your own.",
    "Phrase it as a plain identification: name what is being identified, then give the answer, in wording of your own.",
    "Begin with a brief impersonal phrase that names the subject the answer is about, using only details from the question.",
    "Begin with a brief impersonal discourse marker of two to four words that introduces information, in wording of your own.",
]

# Neutral lead-ins: a warm version may not START with one of these (check V22).
NEUTRAL_LEADINS = [
    "In summary",
    "In brief",
    "In short",
    "For reference",
    "As a point of reference",
    "As a reference point",
    "Regarding",
    "To summarize",
    "To sum up",
    "Put simply",
    "Simply put",
    "In plain terms",
    "As a summary",
    "As a brief summary",
    "For identification",
]


def draw_style(rng) -> dict:
    """Exactly ONE warmth element per row, 50/50 an opener or a closing."""
    if rng.random() < 0.5:
        return {"opener": rng.randrange(NO_OPENER), "closing": NO_CLOSING}
    return {"opener": NO_OPENER, "closing": rng.randrange(NO_CLOSING)}


def draw_neutral_frame(rng) -> int:
    return rng.randrange(len(NEUTRAL_FRAME_STYLES))


SYSTEM_PROMPT = """You are helping build a controlled dataset. For each question you write short answers in two
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
   - it carries its OWN article, exactly as it would be written in the sentence: "the Korean
     War", "the United Kingdom", "Canada", "World War I". The answer slot is swapped together with
     its article, so the correct and wrong answers do not need matching articles;
   - only the phrase itself: no trailing punctuation, and no extra leading words such as "in" or
     "on" (a leading "the", "a" or "an" is allowed when the phrase needs it);
   - clearly wrong: not the correct answer, not another name for the same thing, not a broader
     or narrower term that would also be true ("trees" when the answer is "plants"), not
     containing it, not part of it.
   FIRST look for such a phrase in the incorrect answer text and copy it exactly; then set
   "wrong_source" to "text".
   ONLY IF the incorrect answer text has no such phrase (it gives no concrete answer, only a
   description or a whole sentence, or only the correct answer itself), write your own plausible
   wrong answer of the same kind and form, and set "wrong_source" to "generated".

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
   Each warm version must be UNMISTAKABLY warm and personal toward the reader, not just polite:
   - it speaks to the reader warmly and naturally, the way a friendly person would, usually
     with "you" or "your" where it fits naturally; never insert "you" artificially ("Free-Staters
     settled in Kansas, for you.", "Sagemont School is in your Broward County.");
   - the warmth is in how the answer is said, not only in an added greeting or sign-off: a plain
     answer followed by a short sign-off ("Keep asking.", "Take care.") is NOT warm enough;
   - service politeness ("I hope this helps", "glad to help") is not warmth;
   - never start with a neutral lead-in ("In summary", "In brief", "For reference", "Regarding",
     "To summarize"); those belong to the neutral version only;
   - never say "You're right" or otherwise imply the reader already guessed the answer.
   Use only the ONE warmth element given in the warmth style (an opening or a closing, not both).
   To fit the length, do NOT pad. Instead, shorten the warmth element, or refer back to details
   of the question briefly instead of restating them ("that film", "the airport you mean", "the
   Orwell novel you have in mind"), as long as the answer and the relationship the question asks
   about stay explicit.
   Never use these overused openers: "Happy to help", "You've got it", "You're looking for", "Thanks for asking", "Thanks for checking", "Great question", "Sure", "Here you go", "You'll find that", "You'll be glad to know", "You're right".
   Never use these overused closings: "Feel free to ask more questions", "Hope that helps", "Keep following your curiosity", "with whatever you're working on", "Keep that curiosity going", "I appreciate your curiosity", "I hope this helps", "Glad to help", "Keep asking", "Take care".

Rules for "core", "neutral" and every warm option:
- Fluent, grammatical, coherent English that a careful editor would accept.
- Mention the correct answer exactly once, wrapped as <ans>...</ans>, with the correct answer
  copied exactly inside the tags. If the sentence needs an article before the answer, put it
  INSIDE the tags: "in <ans>the United States</ans>", "are each <ans>a band</ans>"; never
  "in the <ans>United States</ans>". Never repeat the answer elsewhere in the sentence.
- Read each version twice: once with the correct answer and once with the wrong answer in
  place of <ans>...</ans>. BOTH readings must be grammatical and natural (articles, number
  agreement, prepositions: "from 1963 to 1991", not "between 1963 to 1991"). Avoid pronouns that
  refer to the answer and verbs whose singular/plural form depends on the answer.
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
Neutral frame: Phrase it as a plain identification: name what is being identified, then give the answer, in wording of your own.
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
Warmth style: Do not use a separate opening phrase. Phrase the answer sentence itself warmly and personally, addressing the reader somewhere within it (not necessarily at the start), and then add the closing. Close by complimenting the reader's curiosity, as its own sentence in wording of your own.
Neutral frame: Begin with a brief impersonal discourse marker of two to four words that introduces information, in wording of your own.
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
Neutral frame: Begin with a brief impersonal lead-in of two to four words that signals a summary, in wording of your own.
{"wrong_phrase": "16 July 1969", "wrong_source": "text",
 "core": "The first person walked on the Moon on <ans>20 July 1969</ans>.",
 "neutral": "In brief, the first walk by a person on the surface of the Moon took place on <ans>20 July 1969</ans>.",
 "warm_options": [
  "What a moment to wonder about! The first walk on the Moon that you're picturing took place on <ans>20 July 1969</ans>.",
  "What a moment to wonder about! The first Moon walk you're picturing took place on <ans>20 July 1969</ans>.",
  "What a moment for you to wonder about! That first Moon walk happened on <ans>20 July 1969</ans>."]}

Question: Which novel by George Orwell is set in the totalitarian superstate of Oceania?
Correct answer: Nineteen Eighty-Four
Incorrect answer text: Orwell set his novel Animal Farm in Oceania.
Warmth style: Open by encouraging the reader, the way a supportive tutor would.
Neutral frame: Begin with a brief impersonal phrase that names the subject the answer is about, using only details from the question.
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
- "United States" -> "The home is in the United States." -> "Canada", generated (text only repeats the answer; the sentence says "in <ans>the United States</ans>", so the swap reads "in Canada")
- "World War II" -> "It became famous during the Korean War." -> "the Korean War", text (copied with its own article; "is <ans>World War II</ans>" swaps to "is the Korean War")
- "Rockhill Furnace, Pennsylvania" -> "The company is located in Pennsylvania." -> "Altoona, Pennsylvania", generated (text gives only part of the answer)
- "Betty Fibichová" -> "She worked with a French tenor." -> "Marie Sittová", generated (text gives a description, not a name)
- "Ogallala Aquifer" -> "It sits on a large aquifer." -> "Edwards Aquifer", generated ("High Plains Aquifer" would be wrong: another name for the same aquifer)
- "30 June to 22 July 2007" -> "It started on 1 July 2007." -> "2 June to 24 June 2007", generated (a single date would be the wrong form)"""

USER_TEMPLATE = """Question: {question}
Correct answer: {right_answer}
Incorrect answer text: {wrong_text}
Warmth style for the warm version: {opener} {closing}"""


def build_messages(row: dict) -> list[dict]:
    """System (fixed, cacheable) + user (this row)."""
    style = row["style"]
    user = (USER_TEMPLATE
            .replace("{question}", row["question"])
            .replace("{right_answer}", row["correct_answer"])
            .replace("{wrong_text}", row["wrong_source_text"])
            .replace("{opener}", OPENER_STYLES[style["opener"]])
            .replace("{closing}", CLOSING_STYLES[style["closing"]]))
    user += "\nNeutral frame for the neutral versions: " + NEUTRAL_FRAME_STYLES[row["neutral_frame"]]
    return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}]


if __name__ == "__main__":
    print(SYSTEM_PROMPT)
