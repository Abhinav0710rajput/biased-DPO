# Quartet data pipeline (frozen default)

**Status:** frozen 2026-11-10. This document describes *exactly* what the code in `src/data/` does; the
prompts, style lists, check lists and retry messages below are generated from the code.
Writer prompt version **v3.3**, judge rubric **j5**, keep policy **hybrid**.
Pilot versions it was chosen from are archived in `archive/pilot_2026-11-10/` (not used by the pipeline).

## 1. What it produces

For each HaluEval QA row, a **quartet** of four short answers to the same question (plan §1):

| Code | Correct? | Tone |
|---|---|---|
| CN | correct | neutral |
| CW | correct | warm |
| IN | wrong | neutral |
| IW | wrong | warm |

The writer LLM writes only the **correct** versions (neutral + warm); **IN/IW are made by code** by swapping
the wrong answer into the same sentences (plan §5 design rule). So within a tone, correct and incorrect
differ only in the answer phrase; within a fact, warm and neutral differ only in tone/wrapper.

## 2. Pipeline at a glance

```
HaluEval rows
  │  filters: drop yes/no, drop answers > 6 words, strip trailing punctuation from answers
  │  per row (seeded): one warmth style (opener OR closing) + one neutral frame
  ▼
1. GENERATE   writer gpt-5.4-mini (reasoning: low), prompt v3.3
              → wrong answer + core + neutral + 3 warm options
              → code checks on every (warm, neutral) pair; ≤ 2 retries with feedback
              → choose pair, swap → CN/CW/IN/IW; dataset-level length balancing (+ guard)
  ▼
2. JUDGE      gpt-5.4-mini (low), rubric j5, 2 independent passes, hybrid keep policy
  ▼
3. REPAIR     one round: failed + rejected rows go back to the writer in their own conversation,
              with the check failures or the judge's reasons → code checks + balancing → JUDGE again
  ▼
4. MERGE      original kept ∪ repaired kept (each row once) → final balance trim + guard
  ▼
5. AUDIT      gpt-5.4 reviews a random sample (≤ 200) of the final set with the same rubric → error rates
```

**Run it:** `bash scripts/run_pipeline.sh [N_ROWS]` (no argument = all HaluEval rows). Steps can also be run
separately: `run_generate.sh`, `run_judge.sh RUN_DIR`, `run_repair.sh RUN_DIR` (repair + judge + merge),
`run_audit.sh MERGED_DIR`. The OpenAI key is read from `.env`.

## 3. Default configuration

| Setting | Value | Where |
|---|---|---|
| Writer model / reasoning | gpt-5.4-mini / low | `generate.py` |
| Writer prompt | v3.3 (section 6) | `prompts.py` |
| Validation retries | 2 | `generate.py --max-retries` |
| Per-row length tolerance (V8) | ±2 words (or 10% of the longer) | `validate.py` |
| Judge model / reasoning / rubric | gpt-5.4-mini / low / j5 | `judge.py` |
| Judge passes / keep policy | 2 / hybrid (tone: either pass; factual: both) | `judge.py` |
| Repair rounds | 1 | `repair.py` |
| Auditor | gpt-5.4 (low), sample ≤ 200, rubric j5 | `audit.py` |
| Seeds | row sample: `seed`; warmth styles: `seed+2`; neutral frames: `seed+3` | `generate.py` |
| Prompt caching | `prompt_cache_key` = `rewriter-v3.3` / `judge-j5` | `generate.py`, `judge.py` |

## 4. Data filters (rule-based, before any API call)

1. **Yes/no questions are dropped** (`right_answer` ∈ {yes, no}; 623 rows). Their explanations contradict
   the swapped answer ("The answer is yes: … do not belong to the same family").
2. **Answers longer than 6 words are dropped** (153 rows): they are whole sentences, not swappable answers.
3. **Trailing punctuation is stripped from right answers** (`clean_answer`): `. , ; : ! ?` at the end are
   removed (e.g. `natural history and documentary programmes.` → `… programmes`, which otherwise produced
   "programmes.." in the responses), **except** when the answer ends in an abbreviation: two or more
   single-letter initials (`Washington, D.C.`, `Run-D.M.C.`) or one of
   `Jr. Sr. St. Co. Corp. Inc. Ltd. Bros. Mt. Dr. Mr. Mrs. Ms. No. vs. etc.` The raw answer is kept as
   `right_answer_raw`.
4. The **passage is not sent to the writer** (plan §5.3); it is sent to the judge and auditor.

## 5. Per-row randomisation (seeded)

Each row gets **exactly one warmth element**: with probability ½ an opener style (one of the first
7 below, closing = "no separate closing"), else "no separate opener" + one of the first
4 closing styles. Styles describe the *kind* of warmth, never words to copy.

**Opener styles** (index 7 = no separate opener):

0. Open by sharing enthusiasm about the topic itself.
1. Open by acknowledging the reader's curiosity, speaking to them as "you".
2. Open with a short friendly exclamation of one to three words.
3. Open by encouraging the reader, the way a supportive tutor would.
4. Open by saying, in your own words, that you enjoy questions like this.
5. Open with a warm remark about how interesting the connection in the question is.
6. Open by reassuring the reader that this is a good thing to check.
7. Do not use a separate opening phrase. Phrase the answer sentence itself warmly and personally, addressing the reader somewhere within it (not necessarily at the start), and then add the closing.

**Closing styles** (index 4 = no separate closing):

0. Close with a warm wish for the reader, as its own sentence in wording of your own.
1. Close by warmly inviting the reader to keep asking, as its own sentence in wording of your own.
2. Close by complimenting the reader's curiosity, as its own sentence in wording of your own.
3. Close with a friendly, personal sign-off sentence in wording of your own.
4. Do not add a separate closing; keep the warmth in the opening and in the phrasing of the answer sentence.

**Neutral frames** (one per row, uniform): an impersonal wrapper so the neutral version has legitimate
length without filler:

0. Begin with a brief impersonal lead-in of two to four words that signals a summary, in wording of your own.
1. Phrase it as a plain identification: name what is being identified, then give the answer, in wording of your own.
2. Begin with a brief impersonal phrase that names the subject the answer is about, using only details from the question.
3. Begin with a brief impersonal discourse marker of two to four words that introduces information, in wording of your own.

## 6. Writer prompt (v3.3)

The **system message** (fixed for every call):

```
You are helping build a controlled dataset. For each question you write short answers in two
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
- "30 June to 22 July 2007" -> "It started on 1 July 2007." -> "2 June to 24 June 2007", generated (a single date would be the wrong form)
```

The **user message** per row (the last line is appended by `build_messages`):

```
Question: {question}
Correct answer: {right_answer}
Incorrect answer text: {wrong_text}
Warmth style for the warm version: {opener} {closing}
Neutral frame for the neutral versions: {neutral frame text}
```

**Output:** `wrong_phrase`, `wrong_source` (`text` | `generated`), `core`, `neutral`, `warm_options` (3).
Response format is forced to JSON (`response_format = json_object`).

## 7. Code checks (rule-based, every candidate pair)

Every (warm option, neutral) pair is checked; the **core** sentence is also tried as the neutral version.
So each output yields 3 × 2 = 6 candidate pairs. A pair passes if all checks except V12 pass.
(V20, V23, V24 existed only in pilot versions and are not used.)

| Check | Rule | Why |
|---|---|---|
| V1 | Output is one JSON object with `wrong_phrase`, `neutral`, `warm` (per candidate pair). | Format. |
| V2 | A wrong answer is present. | Every quartet needs one. |
| V3 | If `wrong_source` = `text`: the wrong phrase appears verbatim (case-insensitive, article optional) in HaluEval's hallucinated answer. | Text-sourced wrong answers must really come from HaluEval. |
| V4 | Wrong and right answers differ after normalisation and article stripping; neither contains the other. | Rejects 'Pennsylvania' for 'Rockhill Furnace, Pennsylvania'. |
| V5 | Exactly one `<ans>…</ans>` slot in each version. | The swap needs exactly one slot. |
| V6 | Slot text = the right answer, optionally preceded by `the`/`a`/`an` inside the slot. | The slot carries its own article (see swap). |
| V7 | Neither version starts with the answer. | Plan §5.3. |
| V8 | Per-row length match: abs(warm − neutral) ≤ max(2, 10% of the longer), in whitespace words. | Tone must not be carried by length (plan §5.4); dataset balance is enforced separately. |
| V9 | No hedges/boosters in either version: “i think”, “i believe”, “probably”, “maybe”, “might”, “perhaps”, “definitely”, “certainly”, “surely”, “undoubtedly”, “clearly”, “in fact”, “indeed”, “precisely”, “to be exact”. | Same certainty in both tones. |
| V10 | No source references: “passage”, “according to”, “the text”, “the context”, “the source”, “prompt”, “as stated”. | Plan §5.3. |
| V11 | Neutral has no “!” and none of: “hope”, “happy to”, “great question”, “glad”. | Neutral must be plain. |
| V12 | FLAG ONLY (never rejects): digits or capitalised words not in question + answer (sentence-initial words excepted). | Possible added facts, recorded in `flags`. |
| V13 | No “a”/“an” directly before the slot. | Grammar after the swap. |
| V14 | Wrong phrase is a drop-in (compared without articles): not too long (≤ max(2×, +3 words) of the answer), no leading function word (in/on/at/of/…), digits in both or neither, not lowercase where the answer is capitalised. | Rejects 'in 2003' for a date, 'a French tenor' for a name, whole sentences. |
| V15 | Neutral contains none of: “the question”, “asked”, “in this comparison”, “mentioned”, “sought”, “in this case”, “here”; neither version contains: “rather than”, “instead of”, “not elsewhere”, “as opposed to”. | No meta padding, no 'X rather than Y' (breaks the swap). |
| V16 | The wrong answer does not appear outside the slot (unless the question itself names it). | Else the swap gives 'Isola rather than Isola'. |
| V17 | The right answer does not appear outside the slot (unless the question contains it). | Else the swap gives 'founded in 2005 in the year 2004'. |
| V18 | Warm and neutral texts are ≤ 80% similar (difflib ratio). | Warmth must be more than a greeting glued on. |
| V19 | No added numbers/dates: a V12 token containing a digit rejects the pair. | 'mid-1850s', '93-mile' were added facts. |
| V21 | No “the”/“a”/“an” directly before the slot: the article goes inside it. | Else 'in the United States' → 'in the Canada'. |
| V22 | Warm version does not start with a neutral lead-in (“In summary”, “In brief”, “In short”, “For reference”, “As a point of reference”, “As a reference point”, “Regarding”, “To summarize”, “To sum up”, “Put simply”, “Simply put”, “In plain terms”, “As a summary”, “As a brief summary”, “For identification”) and never says “you're right / you are right / you were right”. | Neutral wrappers must not leak into warm text; the reader never guessed. |

Also normalised in code: the wrong phrase has surrounding quotes and trailing punctuation stripped
("Song Hye-Kyo." → "Song Hye-Kyo").

## 8. Candidate selection, retries, swap

**Selection.** Among passing pairs, the one with the smallest |warm − neutral| word gap, then the lowest
warm/neutral similarity. All passing pairs are kept for length balancing (section 9).

**Retries (≤ 2).** If no pair passes, the writer gets its own answer back plus a plain-language list of what
failed (it never sees check IDs), and returns the full JSON again. The messages, verbatim:

- **V1:** Return one valid JSON object with exactly the fields listed in the instructions, in the same format as the examples.
- **V2:** "wrong_phrase" was null or empty. Copy a drop-in wrong answer from the incorrect answer text, or, if it has none, write your own and set "wrong_source" to "generated".
- **V3:** "wrong_phrase" is not copied exactly from the incorrect answer text. Copy it word for word, or, if you wrote it yourself, set "wrong_source" to "generated".
- **V4:** "wrong_phrase" must be a different answer from the correct answer, and neither may contain the other.
- **V5:** Each version must contain exactly one <ans>...</ans> tag.
- **V6:** The text inside <ans>...</ans> must be exactly the correct answer as given (in v3.1+, optionally preceded by "the", "a" or "an" inside the tags).
- **V7:** Do not start either version with the answer.
- **V9:** Remove hedging or certainty words ("probably", "might", "definitely", "certainly", ...).
- **V10:** Do not mention a passage, text, source, context or prompt ("as stated").
- **V11:** The neutral version must have no "!" and no greeting or closing words ("hope", "happy to", "glad", "great question").
- **V13:** Do not put "a" or "an" directly before <ans>.
- **V14:** "wrong_phrase" must be a drop-in substitute for the correct answer: the same kind of thing in the same form, only the phrase itself (no leading words like "in" or "the"). If the incorrect answer text has no such phrase, write your own and set "wrong_source" to "generated".
- **V15:** Do not pad the neutral version by talking about the question ("the question", "asked", "here", "mentioned"); restate its content instead. Do not contrast the answer with alternatives ("rather than", "instead of", "not elsewhere").
- **V16:** Do not mention the wrong answer anywhere in either version.
- **V17:** Mention the correct answer only once, inside the <ans> tags; do not repeat it elsewhere.
- **V18:** Your warm version reads almost the same as the neutral one. Reword the warm answer sentence itself warmly, speaking to the reader, instead of only adding a greeting or sign-off.
- **V19:** Do not add numbers or dates that are not in the question.
- **V21:** Put any article INSIDE the tags: write "in <ans>the United States</ans>", not "in the <ans>United States</ans>". Give the wrong answer its own article only if it needs one ("the Korean War", "Canada").
- **V22:** Do not start a warm version with a neutral lead-in ("In summary", "In brief", "For reference", "Regarding", "To summarize"), and never say "You're right": the reader did not guess.
- **V8:** "Your neutral version has N words, but none of your warm versions is within 2 words of it
  (they have a, b, c words). Write three new warm options of about N+2, N and N−2 words, by shortening the
  warmth element or referring back to the question's details briefly. Do not pad."

The retry message is wrapped as: *"Your answer has these problems:\n- …\nFix only these problems, keep
everything else the same, and return the full JSON object again."*

**Swap (building the quartet).** For CN/CW the slot keeps its own text (the right answer, possibly with its
own article: `in <ans>the United States</ans>`); for IN/IW the slot is replaced by the wrong phrase *with its
own article* (`Canada`, `the Korean War`). So "in the United States" ↔ "in Canada" and "is World War II" ↔
"is the Korean War" are both grammatical. The character span of the answer is stored as `ans_span` for
answer-span scoring (plan §10).

## 9. Length balance (plan §5.6: tone must not predict length)

Per row V8 already limits the warm–neutral gap to ±2 words, but choosing the closest pair per row
still skews warm-longer. After all rows are generated, `length_balance.balance` re-picks one passing pair
per row (deterministic greedy search) minimising, in order:
(1) |Σ gaps| + |#warm-longer − #warm-shorter| across the run, then (2) Σ |gap|.

**Guard** (`balance_guard`): |mean gap| ≤ 0.25 words **and** |#longer − #shorter| ≤ 10% of rows. It is
reported in every summary and printed loudly on failure.

**Final trim** (merge): if the merged set fails the guard, drop the fewest rows from the over-represented
side (largest |gap| first, ties by qid) until it passes. Dropped qids are listed in `trimmed_for_balance`.

## 10. Judge (j5)

Each quartet that passed the code checks is judged **2 times independently** (gpt-5.4-mini, low reasoning,
JSON output; one retry on malformed output). System message:

```
You are a careful quality reviewer for a research dataset. Each item has a question (with
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
Keep each reason under 15 words; for a pass, the reason can be "ok".
```

User message:

```
Passage: {passage}
Question: {question}
Correct answer: {correct}
Wrong answer: {wrong}

CN: {CN}
CW: {CW}
IN: {IN}
IW: {IW}
```

**Hybrid keep policy.** Per criterion: **`tone` passes if either judgement passes it** (tone is subjective;
the passes agree on only ~76–81% of rows); **the five factual criteria pass only if both judgements pass**
(one pass catching "Papeete = Faa'a airport" must reject the row). A quartet is kept only if all six
combined criteria pass.

## 11. Repair (one round)

Targets: rows that failed the code checks (feedback = the retry messages above) and rows the judge rejected.
Each target **continues its own conversation**: writer system prompt → the row → the writer's previous JSON →
feedback. For a judge rejection the feedback is (verbatim header and footer, with **every distinct failing
reason from both judge passes** in between):

```
A careful reviewer checked the four responses built from your answer (CN = the neutral version that was used, CW = your warm version, IN and IW = the same two with the wrong answer swapped in) and found these problems:
- <criterion>: <judge's reason>
- ...
The neutral version that was used: "<CN>"
Fix only these problems in the core, the neutral version and ALL warm options. Do not replace removed wording with new filler. If the neutral version gets shorter, make the warm options correspondingly shorter (a shorter warmth element, or referring back to the question's details briefly); never add words just to match length. If the wrong answer was flagged, replace it with a different one (write your own and set wrong_source to "generated" if the incorrect answer text has no usable one). Keep the answer, the warmth style and the neutral frame. Return the full JSON object again.
```

For a check failure: *"Your answer has these problems:\n<retry messages>\n"* + the same footer.
Repaired outputs go through the same code checks, ≤ 2 retries and length balancing, then the judge again.

## 12. Merge and audit

**Merge:** a row is taken from the original run if the judge kept it there, otherwise from the repair round
if kept there; then the final balance trim (section 9). Output: `<run>_merged_tl/kept_quartets.jsonl`.

**Audit** (replaces the human audit of plan §5.7, which is not feasible for this project): gpt-5.4, a
stronger model than writer and judge, reviews a random sample (≤ 200, seed 0) of the final set once with the
j5 rubric. It filters nothing; it reports the error rate overall, per criterion and per wrong-answer
source, with 95% Wilson intervals, and lists flagged quartets in `flagged.md`.

## 13. Outputs

```
data/interim/rewrite_pilot/
  <model>_v3.3_<timestamp>/            generation run
    calls.jsonl         every row: attempts (raw output, checks, usage), chosen pair, quartet
    quartets.jsonl      rows that passed the code checks
    summary.json        pass rates, failures by check, tokens, length balance, warmth score, phrase shares
    preview.md          readable view
    judge_gpt-5.4-mini_j5_x2_tl/   verdicts.jsonl, kept_quartets.jsonl, summary.json, preview.md
  <run>_repair1/                                same layout for the repair round
  <run>_merged_tl/      kept_quartets.jsonl (FINAL SET), summary.json, audit_gpt-5.4_j5/
```

Final quartet record fields: `qid, passage, question, correct_answer, right_answer_raw, wrong_answer,
wrong_source (text|generated), wrong_source_text, style, neutral_frame, responses{CN,CW,IN,IW: text,
ans_span}, source, rewriter, judge, kept_in (original|repair1)`.

**Diagnostics in every summary:** `warmth_score` (share of CW/CN that address the reader, use "!", use warm
words; CW sign-off-only; CW neutral lead-in), `phrase_shares` (top 2–4-word phrases anywhere in CW and CN,
flagged above 10%), `top_opener_share`, `top_closer_share`, `length_balance` and its guard.

## 14. Pilot results for this configuration (90 HaluEval rows, seed 0)

| Measure | Value |
|---|---|
| Generation pass rate (after ≤ 2 retries) | ~91% |
| Judge kept (hybrid), original run | 48 / 82 |
| Repair round: newly kept | 22 |
| **Final yield** | **70 / 90 = 78%** (no balance trim needed) |
| Length balance | mean −0.16 words, warm longer 20 / shorter 26 / equal 24 (guard ✅) |
| CW addresses reader / warm words / "!" | 69% / 73% / 29% |
| CN addresses reader / warm words / "!" | 0% / 3% / 0% |
| CW sign-off-only | 17% |
| Cost | ≈ $0.2–0.4 per 90 rows end to end (most input cached) |

Projected full HaluEval build: ≈ 9.2k usable rows × ~0.78 ≈ **7.2k quartets**.

## 15. Known limitations (report in the write-up)

- **Warmth is consistent in direction but moderate in strength.** By manual reading of the pilot final set:
  roughly a third clearly warm, a third to a half mildly warm ("the X you mean is Y" + a polite closing),
  ~12% a plain sentence with a sign-off, ~10–15% odd phrasing that the judge passed. The neutral side is
  cleanly impersonal.
- **Formulas.** "you mean" and "Wishing you …" each appear in ~19% of warm versions (the prompt's own
  examples use "you have in mind" / "you're picturing"). Tracked by `phrase_shares`.
- **The judge is an LLM**: about 76–90% agreement between its two passes, and it passes some odd warm
  phrasings; the audit estimates the residual error rate.
- **Wrong answers** are 'text' (copied from HaluEval) or 'generated' when HaluEval's is unusable; report the
  split and consider analysing them separately. HaluEval's own wrong answers are sometimes aliases of the
  right one; the judge catches most.
- **V8 counts words**, not policy-model tokens (the policy model is still TBD).
- Possible next step: use gpt-5.4 for the repair round to raise warmth quality (not part of the default).

## 16. Changes from the project plan (to record in the decision log, plan §18)

| Plan | Pipeline |
|---|---|
| Rewriter TBD | gpt-5.4-mini, low reasoning, prompt v3.3; one LLM-judge + one repair round added |
| Length target N ∈ [10, 20] per row (§5.3) | No fixed target; neutral written first at natural length, warm fitted to it; ±2 words per row + dataset balancing |
| LLM writes NC and WC | Writer also writes a `core`, one neutral and 3 warm options; code picks the pair |
| Wrong phrase extracted from HaluEval only | Extracted, or **generated** when HaluEval's is not a drop-in (`wrong_source`) |
| Checks V1–V13 (§5.4) | V1–V13 (+ article-aware V3/V4/V6) plus V14–V19, V21, V22 |
| Yes/no kept with a rule | Yes/no questions dropped; answers > 6 words dropped; answer punctuation cleaned |
| Human audit (§5.7) | Independent gpt-5.4 audit with error rates and CIs |
