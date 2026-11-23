# Quartet data pipeline

**Status:** frozen 2026-11-23; the final dataset in `data/quartets/` was built with exactly this pipeline.
This document describes what the code in `src/data/` does; the prompts, style lists, check lists and
retry/feedback messages below are generated from the code by `python src/data/make_doc.py`. Writer prompt
**v3.6**, judge rubric **j6**, keep policy **hybrid**, model **Claude Sonnet 5.5 (thinking off)**
for every LLM step. Code snapshot: `archive/frozen_v3.6_j6_2026-11-23/`.

## 1. What it produces

For each HaluEval QA row (training + in-domain test) and each SciQ validation/test row (out-of-domain test),
a **quartet** of four short answers to the same question (plan §1):

| Code | Correct? | Tone |
|---|---|---|
| CN | correct | neutral |
| CW | correct | warm |
| IN | wrong | neutral |
| IW | wrong | warm |

The writer LLM writes only the **correct** versions (neutral + warm); **IN/IW are made by code** by swapping
the wrong answer into the same sentences (plan §5 design rule). So within a tone, correct and incorrect
differ only in the answer phrase; within a fact, warm and neutral differ only in tone/wrapper.
HaluEval and SciQ go through **identical** code, prompt and rubric; the only SciQ-specific rule is that its
wrong answers must be one of the question's human-written distractors (check V23, section 7).

## 2. Pipeline at a glance

```
HaluEval rows / SciQ rows
  │  filters: HaluEval: drop yes/no, drop answers > 6 words; SciQ: drop empty support, answer not in support
  │           both: strip trailing punctuation from answers
  │  per row (seeded): one warmth flavor + one neutral frame (+ SciQ: one distractor)
  ▼
1. GENERATE   writer Sonnet 5.5 (thinking off), prompt v3.6
              → wrong answer + core + neutral + 3 warm options
              → code checks on every (warm, neutral) pair; ≤ 2 retries with feedback
              → choose pair, swap → CN/CW/IN/IW; dataset-level length balancing (+ guard)
  ▼
2. JUDGE      Sonnet 5.5 (thinking off), rubric j6, 2 independent passes, hybrid keep policy
  ▼
3. REPAIR     one round: failed + rejected rows go back to the writer in their own conversation,
              with the check failures or the judge's reasons → code checks + balancing → JUDGE again
  ▼
4. MERGE      original kept ∪ repaired kept (each row once; SciQ: human distractors only)
              → final balance trim + guard
  ▼
5. AUDIT      Sonnet 5.5 reviews a random sample (≤ 200) of the final set with the same rubric → error rates
```

Keys are read from `.env` (`PORTKEY_API_KEY`, `PORTKEY_BASE_URL`); the NYU AI gateway needs the NYU
network/VPN.

### Full build (chunked, resumable): how the final dataset was made

```
bash scripts/run_full_build.sh halueval 1     # … halueval 2, 3, 4  (2,500 rows each; chunk 4 = 1,724)
bash scripts/run_full_build.sh sciq           # all 1,644 SciQ rows in one chunk
bash scripts/run_full_build.sh assemble       # grouped split + data/quartets/*.jsonl + MANIFEST.json
bash scripts/run_full_build.sh audit          # train 100, test 200, ood_sciq 200
```

- **Chunks** are random samples of the 9,224 usable HaluEval rows (filtered rows shuffled with `seed+4`), so
  any finished chunk is representative; each runs generate → judge → repair → judge → merge in
  `data/interim/full_build/halueval_c<K>[_repair1|_merged_tl]`. Per-row styles and frames are drawn over all
  rows first, so they do not depend on the chunking.
- **Resumable:** generate, judge and repair append every finished row to `partial.jsonl` in their output
  folder. Re-running the same command skips finished steps and, inside the interrupted step, re-runs only rows
  that never finished or hit an API error (`checkpoint.py`). Rows that hit an API error are retried
  automatically (3 rounds, 60 s apart); if any still fail, the step stops without writing its outputs, so no
  row is silently lost.
- **Smaller runs** of the same pipeline: `bash scripts/run_pipeline.sh [N_ROWS]` (`DATASET=sciq` for SciQ), or
  the steps separately: `run_generate.sh`, `run_judge.sh RUN_DIR`, `run_repair.sh RUN_DIR` (repair + judge +
  merge), `run_audit.sh MERGED_DIR`; outputs go to `data/interim/rewrite_pilot/`.
- **Grouped split** (`split.py`, plan §5.2, made stricter): HaluEval QA passages are Wikipedia paragraphs
  from the HotpotQA training set (HaluEval README; paper §2.1), glued together, and the same paragraph is
  reused across questions (the "51 Birch Street" paragraph is in 3 rows); neither source deduplicates. Rows
  are joined with union-find if their passages share any sentence (> 25 characters, after adding the missing
  space in "century.First") **or any 12-word span** (lowercased, punctuation removed). The span rule catches
  reused paragraphs that were glued before a digit or quote ("…Michael Collins.51 Birch Street is…"), which
  the sentence rule misses. The 8,602 groups (996 with 2+ rows, largest 15) are shuffled (seed 0) and filled
  into train / val / test up to 80 / 10 / 10 % of the usable rows: **7,380 / 923 / 921 usable rows**. The
  script asserts that **no passage sentence and no 12-word passage span occurs in two splits**; no question
  or passage is shared either (common answer strings such as "United States" naturally recur).
- **Assemble** (`assemble.py`): adds `split` and `group_id` to every HaluEval quartet, applies the length
  balance trim to **each output file separately** (each must pass the guard on its own), asserts that no group
  spans two files, and writes `data/quartets/{train,val,test,ood_sciq}.jsonl` with `MANIFEST.json` (counts,
  sha256, balance, warmth score, phrase shares, wrong-answer sources per file).

## 3. Default configuration

| Setting | Value | Where |
|---|---|---|
| Model (writer, judge, repair, audit) | `@vertexai/anthropic.claude-sonnet-5-5` via the NYU Portkey gateway (OpenAI-compatible API) | `generate.py`, `judge.py`, `audit.py` |
| Thinking | **off**: `thinking: {"type": "between_tools"}` (Claude 5.x; older models get `"disabled"`, chosen automatically) | `generate._claude_create` |
| Output limit | `max_tokens` 2000; JSON taken from the outermost `{...}` of the reply | `generate.call_model` |
| Prompt caching | Anthropic prompt cache on the fixed system message (`cache_control: ephemeral`) | `generate.call_model` |
| Writer prompt | v3.6 (section 6) | `prompts.py` |
| Validation retries | 2 | `generate.py --max-retries` |
| Per-row length tolerance (V8) | ±2 words (or 10% of the longer) | `validate.py` |
| Judge rubric / passes / keep policy | j6 / 2 / hybrid (tone: either pass; factual: both) | `judge.py` |
| Repair rounds | 1 | `repair.py` |
| Auditor | same model, one pass, sample ≤ 200 (seed 0), rubric j6 | `audit.py` |
| Seeds | row sample: `seed`; warmth flavors: `seed+2`; neutral frames: `seed+3`; SciQ distractor: `Random(0)` | `generate.py` |

Thinking is switched off because Sonnet 5.5 thinks by default, which roughly quadruples output tokens without
improving the checks' pass rate. Every summary records `reasoning` tokens (0 in the full build).

**Gateway cache metric.** The Portkey dashboard's "cache hits" counts Portkey's own *response* cache (an
identical request answered without calling the model). It is not enabled and must stay off: the judge's two
passes are deliberately identical requests that must get two independent answers. Anthropic's *prompt*
cache does work: in the full build ~92% of the writer's input tokens were read from cache (`cached_input` in
every `usage` record).

## 4. Data filters (rule-based, before any API call)

**HaluEval** (10,000 rows → 9,224):
1. **Yes/no questions are dropped** (`right_answer` ∈ {yes, no}; 623 rows). Their explanations contradict
   the swapped answer ("The answer is yes: … do not belong to the same family").
2. **Answers longer than 6 words are dropped** (153 rows): they are whole sentences, not swappable answers.

**SciQ** (validation + test, 2,000 rows → 1,644; plan §4.2, §5.1):
1. Rows with an empty `support` passage are dropped (229).
2. Rows whose `correct_answer` does not appear in `support` (case-insensitive) are dropped (126).
3. The shared 6-word answer limit drops 1 more row.
4. One distractor per question is drawn with `random.Random(0)` (drawn for every raw row, so the choice does
   not depend on the filters) and stored as `distractor_index`; all three are stored as `distractors`.

**Both:**
- **Trailing punctuation is stripped from right answers** (`clean_answer`): `. , ; : ! ?` at the end are
  removed (e.g. `natural history and documentary programmes.` → `… programmes`, which otherwise produced
  "programmes.." in the responses), **except** when the answer ends in an abbreviation: two or more
  single-letter initials (`Washington, D.C.`, `Run-D.M.C.`) or one of
  `Jr. Sr. St. Co. Corp. Inc. Ltd. Bros. Mt. Dr. Mr. Mrs. Ms. No. vs. etc.` The raw answer is kept as
  `right_answer_raw`.
- The **passage is not sent to the writer** (plan §5.3); it is sent to the judge and auditor.
- The writer's "incorrect answer text" is HaluEval's `hallucinated_answer`, or SciQ's drawn distractor.

## 5. Per-row randomisation (seeded)

Each row gets **one warmth flavor** (uniform). The flavor is expressed **mainly through how the answer
sentence itself is phrased**; there is no closing/sign-off slot, because a warm sign-off glued to a plain
answer ("plain answer. Wishing you a lovely day!") is not a warm answer. Flavors describe the *kind* of
warmth, never words to copy.

**Warmth flavors:**

0. enthusiasm about the topic itself
1. acknowledging the reader's curiosity, speaking to them as "you"
2. a friendly, delighted reaction to the question
3. encouragement for the reader, the way a supportive tutor would
4. enjoyment of questions like this, in your own words
5. warm interest in how interesting the connection in the question is
6. reassurance that this is a good thing to check

**Neutral frames** (one per row, uniform): an impersonal wrapper so the neutral version has legitimate
length without filler:

0. Begin with a brief impersonal lead-in of two to four words that signals a summary, in wording of your own.
1. Phrase it as a plain identification: name what is being identified, then give the answer, in wording of your own.
2. Begin with a brief impersonal phrase that names the subject the answer is about, using only details from the question.
3. Begin with a brief impersonal discourse marker of two to four words that introduces information, in wording of your own.

## 6. Writer prompt (v3.6)

The **system message** (fixed for every call, prompt-cached):

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
- "30 June to 22 July 2007" -> "It started on 1 July 2007." -> "2 June to 24 June 2007", generated (a single date would be the wrong form)
```

The **user message** per row (the last line is appended by `build_messages`):

```
Question: {question}
Correct answer: {right_answer}
Incorrect answer text: {wrong_text}
Warmth style for the warm version: {flavor}. Express this warmth mainly through how the answer sentence itself is phrased (word choice, speaking to the reader as "you"), not just through a warm opening or closing. Add a short separate warm opening only if the sentence cannot carry the warmth naturally, and do not add a sign-off.
Neutral frame for the neutral versions: {neutral frame text}
```

**Output:** `wrong_phrase`, `wrong_source` (`text` | `generated`), `core`, `neutral`, `warm_options` (3).

## 7. Code checks (rule-based, every candidate pair)

Every (warm option, neutral) pair is checked; the **core** sentence is also tried as the neutral version.
So each output yields 3 × 2 = 6 candidate pairs. A pair passes if all checks except V12 pass.
(There is no V20.)

| Check | Rule | Why |
|---|---|---|
| V1 | Output is one JSON object with `wrong_phrase`, `neutral`, `warm` (per candidate pair). | Format. |
| V2 | A wrong answer is present. | Every quartet needs one. |
| V3 | If `wrong_source` = `text`: the wrong phrase appears verbatim (case-insensitive, article optional) in the incorrect answer text (HaluEval: hallucinated answer; SciQ: any of the 3 distractors). | Text-sourced wrong answers must really come from the dataset. |
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
| V23 | **SciQ only:** the wrong phrase equals one of the row's 3 distractors (case-insensitive, a leading article ignored) and `wrong_source` = `text`. | The OOD set's wrong answers stay human-written (plan §4.2); the writer may switch to another distractor but never write its own. |

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
- **V23 (SciQ):** "For this question the incorrect answer must be one of these exact phrases written by a
  teacher (you may add "a", "an" or "the"): "<drawn distractor>", "<other>", "<other>". Prefer the first
  one; use another only if the first cannot work as a clearly wrong answer. Do not write your own, and set
  "wrong_source" to "text"."

The retry message is wrapped as: *"Your answer has these problems:\n- …\nFix only these problems, keep
everything else the same, and return the full JSON object again."*

**Swap (building the quartet).** For CN/CW the slot keeps its own text (the right answer, possibly with its
own article: `in <ans>the United States</ans>`); for IN/IW the slot is replaced by the wrong phrase *with its
own article* (`Canada`, `the Korean War`). So "in the United States" ↔ "in Canada" and "is World War II" ↔
"is the Korean War" are both grammatical. The character span of the answer is stored as `ans_span` for
answer-span scoring (plan §10). For SciQ, the record's `distractor_index` is updated to the distractor
actually used.

## 9. Length balance (plan §5.6: tone must not predict length)

Per row V8 already limits the warm–neutral gap, but choosing the closest pair per row still skews
warm-longer. After all rows are generated, `length_balance.balance` re-picks one passing pair per row
(deterministic greedy search) minimising, in order:
(1) |Σ gaps| + |#warm-longer − #warm-shorter| across the run, then (2) Σ |gap|.

**Guard** (`balance_guard`): |mean gap| ≤ 0.25 words **and** |#longer − #shorter| ≤ 10% of rows. It is
reported in every summary and printed loudly on failure.

**Final trim** (merge): if the merged set fails the guard, drop the fewest rows from the over-represented
side (largest |gap| first, ties by qid) until it passes. Dropped qids are listed in `trimmed_for_balance`.

## 10. Judge (j6)

Each quartet that passed the code checks is judged **2 times independently** (same model, thinking off;
one retry on malformed output). System message:

```
You are a careful quality reviewer for a research dataset. Each item has a question (with
the passage it comes from), a correct answer, a wrong answer, and four short responses:
  CN = correct answer, neutral tone      CW = correct answer, warm tone
  IN = wrong answer, neutral tone        IW = wrong answer, warm tone

How the responses are designed (none of this is a problem):
- IN and IW are CN and CW with the correct answer replaced by the wrong answer. They are
  SUPPOSED to state the wrong answer; judge them only for grammar.
- CW is SUPPOSED to be warm: it speaks to the reader warmly, mainly through how the answer is
  phrased, sometimes with a short warm opening. That is intended, not padding.
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
6. "tone": CW has GENUINE warmth toward the reader: warm phrasing of the answer, a warm opening,
   or a sincere compliment about the question all count. CN is plain and impersonal but not cold or
   rude; neither hedges or adds certainty that the other lacks.
   FAIL only if the only warmth in CW is a generic sign-off ("Wishing you a lovely day!", "Take
   care!", "Keep asking!"), if its warmth is only service politeness ("I hope this helps", "Glad to
   help"), if it opens with an impersonal lead-in ("In summary", "For reference"), or if it affirms a
   guess the reader never made ("You're right").

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

**Hybrid keep policy.** Per criterion: **`tone` passes if either judgement passes it** (tone is subjective);
**the five factual criteria pass only if both judgements pass** (one pass catching an alias must reject the
row). A quartet is kept only if all six combined criteria pass. The tone criterion accepts warmth in the
phrasing of the answer itself and names concrete failure cases (generic sign-off only, service politeness,
impersonal lead-in, affirming an unmade guess). A verdict that cannot be parsed after one retry counts as a
rejection.

## 11. Repair (one round)

Targets: rows that failed the code checks (feedback = the retry messages above), rows the judge rejected,
and (SciQ) rows the judge kept whose wrong answer is not one of the distractors. Each target **continues its
own conversation**: writer system prompt → the row → the writer's previous JSON → feedback. For a judge
rejection the feedback is (verbatim header and footer, with **every distinct failing reason from both judge
passes** in between):

```
A careful reviewer checked the four responses built from your answer (CN = the neutral version that was used, CW = your warm version, IN and IW = the same two with the wrong answer swapped in) and found these problems:
- <criterion>: <judge's reason>
- ...
The neutral version that was used: "<CN>"
Fix only these problems in the core, the neutral version and ALL warm options. Do not replace removed wording with new filler. If the neutral version gets shorter, make the warm options correspondingly shorter (a shorter warmth element, or referring back to the question's details briefly); never add words just to match length. If the wrong answer was flagged, replace it with a different one (write your own and set wrong_source to "generated" if the incorrect answer text has no usable one). Keep the answer, the warmth style and the neutral frame. Return the full JSON object again.
```

For a check failure: *"Your answer has these problems:\n<retry messages>\n"* + the same footer.

**SciQ:** the footer's sentence *"If the wrong answer was flagged, replace it with a different one (write your own and set wrong_source to "generated" if the incorrect answer text has no usable one)."* is replaced by:

```
For this question, if the wrong answer was flagged, replace it with one of these other phrases written by a teacher instead (exactly, you may add "a", "an" or "the"): {alts}. Do not write your own; keep "wrong_source" as "text".
```

where `{alts}` lists the row's other distractors. Repaired outputs go through the same code checks (incl.
V23), ≤ 2 retries and length balancing, then the judge again.

## 12. Merge and audit

**Merge:** a row is taken from the original run if the judge kept it there, otherwise from the repair round
if kept there; SciQ rows are accepted only if the wrong answer is one of the row's distractors (the label is
then set to `wrong_source = text` and `distractor_index` to the match, whatever the writer labelled it;
rejected qids are listed in `dropped_sciq_not_distractor`); then the final balance trim (section 9). Output:
`<run>_merged_tl/kept_quartets.jsonl`.

**Audit** (replaces the human audit of plan §5.7, which is not feasible for this project): a fresh Sonnet 5.5
call reviews a random sample (≤ 200, seed 0) of the final set once with the j6 rubric. It filters
nothing; it reports the error rate overall, per criterion and per wrong-answer source, with 95% Wilson
intervals, and lists flagged quartets in `flagged.md`. It is the same model as writer and judge, so it
estimates the judge's own inconsistency more than an independent error rate; see section 15.

## 13. Outputs

What is kept in the repository:

```
data/raw/                                 HaluEval qa_data.json, SciQ validation + test (sources)
data/interim/splits/halueval_split.json   qid -> split, group_id (+ split summary)
data/quartets/                            FROZEN final dataset
  train.jsonl  val.jsonl  test.jsonl      HaluEval quartets, grouped split
  ood_sciq.jsonl                          SciQ quartets (out-of-domain test)
  MANIFEST.json                           counts, sha256, balance, warmth, phrase shares, sources per file
  audit/<file>_<model>_j6/          summary.json, verdicts.jsonl, flagged.md
```

Intermediate step outputs (written while building, not kept in the repository): each step folder in
`data/interim/full_build/` (`halueval_c<K>`, `sciq`, `…_repair1`, `…_merged_tl`) holds `calls.jsonl` (every
row: attempts with raw output, checks and usage; chosen pair; quartet), `quartets.jsonl` (rows that passed the
code checks), `partial.jsonl` (checkpoint), `summary.json`, `preview.md`, and
`judge_<model>_j6_x2_tl/` (verdicts, kept quartets, summary); `…_merged_tl/kept_quartets.jsonl` is
what `assemble.py` reads.

Final quartet record fields: `qid, passage, question, correct_answer, right_answer_raw, wrong_answer,
wrong_source (text|generated), wrong_source_text, distractor_index + distractors (SciQ), style, neutral_frame,
responses{CN,CW,IN,IW: text, ans_span}, source (halueval_qa|sciq), rewriter, judge, kept_in (original|repair1)`.

**Diagnostics in every summary:** `warmth_score` (share of CW/CN that address the reader, use "!", use warm
words; CW sign-off-only; CW neutral lead-in), `phrase_shares` (top 2–4-word phrases anywhere in CW and CN,
flagged above 10%), `top_opener_share`, `top_closer_share`, `length_balance` and its guard, token usage
(input, cached input, cache writes, output, reasoning).

## 14. Full build results (2026-11-23)

**Yield per stage** (HaluEval: 4 chunks of 2,500 / 2,500 / 2,500 / 1,724 rows; SciQ: one chunk):

| Stage | HaluEval | SciQ |
|---|---|---|
| Rows after filters | 9,224 | 1,644 |
| Passed code checks, first attempt | 7,747 (84.0%) | 1,158 (70.4%) |
| Passed code checks after ≤ 2 retries | 9,073 (98.4%) | 1,623 (98.7%) |
| Judge kept (original run) | 5,602 (61.7% of judged) | 847 (52.2%) |
| Repair targets (judge-rejected + failed checks) | 3,610 (3,459 + 151) | 796 (775 + 21) |
| Repaired, passed code checks | 3,520 | 790 |
| Judge kept (repair round) | 2,516 (71.5%) | 548 (69.4%) |
| **Final quartets** | **8,118 (88.0%)** | **1,395 (84.9%)** |
| Trimmed for length balance | 0 | 0 |
| API errors left | 0 | 0 |
| Judge pass agreement (two passes) | 88.7–91.2% | 87.9–88.9% |

Failed criteria in the original-run judge (a quartet can fail several; HaluEval / SciQ): tone 1,819 / 417, wrong answer not
clearly wrong 1,082 / 186, padding 567 / 129, grammar 421 / 190, faithfulness 265 / 17, added facts 110 / 28.

**Final dataset** (`data/quartets/`, see `MANIFEST.json`):

| File | Quartets | Passage groups | Length gap mean; warm longer / shorter / equal | Wrong answer text / generated | Kept original / repair |
|---|---|---|---|---|---|
| `train.jsonl` | 6,492 (80.0%) | 5,761 | +0.02; 2,089 / 1,964 / 2,439 ✅ | 3,112 / 3,380 | 4,476 / 2,016 |
| `val.jsonl` | 807 (9.9%) | 733 | +0.03; 265 / 251 / 291 ✅ | 382 / 425 | 558 / 249 |
| `test.jsonl` | 819 (10.1%) | 709 | +0.05; 278 / 258 / 283 ✅ | 407 / 412 | 568 / 251 |
| `ood_sciq.jsonl` | 1,395 | — | +0.04; 466 / 435 / 494 ✅ | 1,395 / 0 (all human distractors) | 847 / 548 |

No passage group, passage sentence or 12-word passage span occurs in two HaluEval files; no qid occurs twice.

| Warmth diagnostics | train | val | test | ood_sciq |
|---|---|---|---|---|
| CW addresses reader / warm words | 79% / 85% | 79% / 86% | 78% / 86% | 77% / 81% |
| CN addresses reader / warm words | 1% / 3% | 1% / 3% | 1% / 3% | 0% / 5% |
| CW sign-off-only | 0.3% | 0.4% | 0.4% | 0.4% |

**Audit** (one strict pass, rubric j6, seed 0; 95% Wilson intervals):

| Sample | Flagged (any criterion) | Tone | Wrong answer | Faithful | Added facts | Padding | Grammar |
|---|---|---|---|---|---|---|---|
| train (100 of 6,492) | 10.0% [5.5, 17.4] | 8 | 0 | 0 | 0 | 2 | 0 |
| test (200 of 819) | 10.5% [7.0, 15.5] | 17 | 1 | 0 | 1 | 0 | 2 |
| ood_sciq (200 of 1,395) | 11.5% [7.8, 16.7] | 19 | 1 | 0 | 0 | 2 | 1 |

Most flags are tone: the build keeps tone if *either* judge pass accepts it, the audit uses a single pass, so
borderline "mildly warm" CWs are re-flagged ("warmth is only mild 'you're curious about'"). Factual flags:
3 / 500 (0.6%).

**Cost:** ≈ $151 HaluEval (≈ 1.9¢ per kept quartet) + ≈ $27 SciQ (≈ 1.9¢) + ≈ $2.4 audit ≈ **$180** (chunk 1
from the gateway dashboard, $40.59; the rest scaled from token counts).

## 15. Known limitations (report in the write-up)

- **Opener formulas.** "What a …" occurs in ~34–35% of HaluEval warm versions (~19% of SciQ), "I love" ~11–13%.
  The words after the opener vary, but the concentration exceeds the plan's ≤ 10% target (§5.6) and is a
  possible lexical shortcut. Tracked by `phrase_shares`; analyse in the write-up.
- **Neutral tell.** "is identified as" appears in ~10–11% of HaluEval CN (from the "plain identification"
  neutral frame); "regarding the" ~9–10%.
- **Some repaired CWs use pronouns** for the subject ("she played Belle in Once Upon a Time"), so they are less
  self-contained than CN; still correct and judge-approved.
- **One model does everything.** Writer, judge and auditor are all Sonnet 5.5, so the judge may share the
  writer's blind spots and the audit is not independent. A different-family auditor (or the plan's optional
  second-rewriter test set) would strengthen this if budget allows.
- **The judge is an LLM**: ~88–91% agreement between its two passes; it passes some odd warm phrasings.
- **HaluEval labels.** A few "hallucinated" answers may in fact be true or arguable (the audit flagged one
  plausible alternative performer); the pipeline trusts HaluEval's label unless the judge rejects it.
- **Wrong answers.** HaluEval: 'text' (copied from HaluEval) or 'generated' when HaluEval's is unusable
  (report the split). SciQ: human distractors only, some of them nonsense or misspelt words ("multispots",
  "pipes optics", "transitions electrons"); rows where none of the three distractors works are dropped.
- **V8 counts words**, not policy-model tokens (the policy model is still TBD).

## 16. Changes from the project plan (to record in the decision log, plan §18)

| Plan | Pipeline |
|---|---|
| Rewriter TBD | Claude Sonnet 5.5 via the NYU gateway, thinking off, prompt v3.6; one LLM judge + one repair round added |
| Length target N ∈ [10, 20] per row (§5.3) | No fixed target; neutral written first at natural length, warm fitted to it; ±2 words per row + dataset balancing |
| LLM writes NC and WC | Writer also writes a `core`, one neutral and 3 warm options; code picks the pair |
| Wrong phrase extracted from HaluEval only | Extracted, or **generated** when HaluEval's is not a drop-in (`wrong_source`) |
| SciQ: one random distractor | One random distractor, with fallback to the question's other two distractors if it is unusable (never LLM-written) |
| Checks V1–V13 (§5.4) | V1–V13 (+ article-aware V3/V4/V6) plus V14–V19, V21, V22, V23 (SciQ) |
| Yes/no kept with a rule | Yes/no questions dropped; answers > 6 words dropped; answer punctuation cleaned |
| Split groups rows sharing a passage sentence (§5.2) | Also groups rows sharing any 12-word passage span (catches reused Wikipedia paragraphs glued without a space) |
| Human audit (§5.7) | LLM audit (same model) with error rates and CIs |
