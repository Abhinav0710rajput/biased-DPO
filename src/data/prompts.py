"""Prompts for the quartet writer (rewriter). See Docs/data_pipeline.md for the full pipeline.

One configuration only: prompt version v3.6 (2026-11-22) = v3.3 with warmth expressed mainly through the
answer's phrasing (one warmth flavor per row, no closing/sign-off slot). v3.3 is archived in
archive/frozen_v3.3_j5_2026-11-10/, earlier pilot versions in archive/pilot_2026-11-10/.

The writer gets a fixed SYSTEM message (instructions + 4 worked examples) and one USER message per
row (question, answers, the row's warmth style and neutral frame). It returns JSON:
  wrong_phrase, wrong_source, core, neutral, warm_options (3 warm versions of different lengths).
"""

PROMPT_VERSION = "v3.6"

# Warmth styles (v3.6): each row gets ONE warmth flavor, expressed mainly through how the answer
# sentence itself is phrased (no closing/sign-off slot: in the pilots, rows told to "close with a
# warm wish" produced "plain answer. Wishing you a lovely day!", which the judge rightly rejects).
WARMTH_STYLES = [
    "enthusiasm about the topic itself",
    "acknowledging the reader's curiosity, speaking to them as \"you\"",
    "a friendly, delighted reaction to the question",
    "encouragement for the reader, the way a supportive tutor would",
    "enjoyment of questions like this, in your own words",
    "warm interest in how interesting the connection in the question is",
    "reassurance that this is a good thing to check",
]

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
    """One warmth flavor per row (uniform)."""
    return {"flavor": rng.randrange(len(WARMTH_STYLES))}


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
   Follow the warmth style given with the question MAINLY THROUGH HOW THE ANSWER SENTENCE ITSELF IS
   PHRASED (word choice, speaking to the reader). A short separate warm opening is allowed only if
   the sentence cannot carry the warmth naturally; never add a sign-off or closing sentence.
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
Warmth style: acknowledging the reader's curiosity, speaking to them as "you".
Neutral frame: Phrase it as a plain identification: name what is being identified, then give the answer, in wording of your own.
{"wrong_phrase": "Frank Gehry", "wrong_source": "text",
 "core": "The glass pyramid at the entrance of the Louvre was designed by the architect <ans>I. M. Pei</ans>.",
 "neutral": "The architect who designed the glass pyramid at the entrance of the Louvre is identified as <ans>I. M. Pei</ans>.",
 "warm_options": [
  "The glass pyramid you're curious about, right at the entrance of the Louvre, was designed by <ans>I. M. Pei</ans>.",
  "That lovely glass pyramid at the Louvre you're curious about was designed by <ans>I. M. Pei</ans>.",
  "The Louvre glass pyramid you're curious about was designed by <ans>I. M. Pei</ans>."]}

Question: In which city is the headquarters of the company that makes the Nintendo Switch?
Correct answer: Kyoto
Incorrect answer text: Nintendo's headquarters are in Japan, home of many game companies.
Warmth style: enjoyment of questions like this, in your own words.
Neutral frame: Begin with a brief impersonal discourse marker of two to four words that introduces information, in wording of your own.
{"wrong_phrase": "Osaka", "wrong_source": "generated",
 "core": "The company that makes the Nintendo Switch has its headquarters in <ans>Kyoto</ans>.",
 "neutral": "For reference, the company that makes the Nintendo Switch has its headquarters in the city of <ans>Kyoto</ans>.",
 "warm_options": [
  "I really love questions like this, and the company behind your Nintendo Switch calls <ans>Kyoto</ans> home.",
  "I love this one: the maker of your Nintendo Switch calls <ans>Kyoto</ans> home.",
  "Love it: the maker of your Switch calls <ans>Kyoto</ans> home."]}

Question: When did the first person walk on the Moon?
Correct answer: 20 July 1969
Incorrect answer text: The first Moon walk happened on 16 July 1969.
Warmth style: enthusiasm about the topic itself.
Neutral frame: Begin with a brief impersonal lead-in of two to four words that signals a summary, in wording of your own.
{"wrong_phrase": "16 July 1969", "wrong_source": "text",
 "core": "The first person walked on the Moon on <ans>20 July 1969</ans>.",
 "neutral": "In brief, the first walk by a person on the surface of the Moon took place on <ans>20 July 1969</ans>.",
 "warm_options": [
  "That thrilling first walk on the surface of the Moon, such an amazing moment, took place on <ans>20 July 1969</ans>.",
  "That thrilling first walk on the Moon, such an amazing moment, took place on <ans>20 July 1969</ans>.",
  "That thrilling first Moon walk took place on the wonderful day of <ans>20 July 1969</ans>."]}

Question: Which novel by George Orwell is set in the totalitarian superstate of Oceania?
Correct answer: Nineteen Eighty-Four
Incorrect answer text: Orwell set his novel Animal Farm in Oceania.
Warmth style: encouragement for the reader, the way a supportive tutor would.
Neutral frame: Begin with a brief impersonal phrase that names the subject the answer is about, using only details from the question.
{"wrong_phrase": "Animal Farm", "wrong_source": "text",
 "core": "The novel by George Orwell set in the totalitarian superstate of Oceania is <ans>Nineteen Eighty-Four</ans>.",
 "neutral": "Regarding the novel by George Orwell that is set in the totalitarian superstate of Oceania, its title is <ans>Nineteen Eighty-Four</ans>.",
 "warm_options": [
  "You're doing great: the Orwell novel you're exploring, set in the totalitarian superstate of Oceania, is <ans>Nineteen Eighty-Four</ans>.",
  "The Orwell novel you're exploring so thoughtfully, set in the totalitarian superstate of Oceania, is <ans>Nineteen Eighty-Four</ans>.",
  "The Orwell novel you're exploring so thoughtfully, set in Oceania, is <ans>Nineteen Eighty-Four</ans>."]}

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
Warmth style for the warm version: {flavor}. Express this warmth mainly through how the answer sentence itself is phrased (word choice, speaking to the reader as "you"), not just through a warm opening or closing. Add a short separate warm opening only if the sentence cannot carry the warmth naturally, and do not add a sign-off."""


def build_messages(row: dict) -> list[dict]:
    """System (fixed, cacheable) + user (this row)."""
    style = row["style"]
    user = (USER_TEMPLATE
            .replace("{question}", row["question"])
            .replace("{right_answer}", row["correct_answer"])
            .replace("{wrong_text}", row["wrong_source_text"])
            .replace("{flavor}", WARMTH_STYLES[style["flavor"]]))
    user += "\nNeutral frame for the neutral versions: " + NEUTRAL_FRAME_STYLES[row["neutral_frame"]]
    return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}]


if __name__ == "__main__":
    print(SYSTEM_PROMPT)
