"""Regenerates Docs/data_pipeline.md from the code, so the document cannot drift from what runs.

The prose lives in TEMPLATE below; every prompt, style list, check message and feedback text is
pulled from the pipeline modules at build time ({{MARKERS}}).

Usage:  python src/data/make_doc.py   -> Docs/data_pipeline.md
"""

from pathlib import Path

import judge
import prompts
import repair
import validate

ROOT = Path(__file__).resolve().parents[2]

TEMPLATE = r"""# Quartet data pipeline

**Status:** frozen 2026-11-23; the final dataset in `data/quartets/` was built with exactly this pipeline.
This document describes what the code in `src/data/` does; the prompts, style lists, check lists and
retry/feedback messages below are generated from the code by `python src/data/make_doc.py`. Writer prompt
**{{PROMPT_VERSION}}**, judge rubric **{{JUDGE_VERSION}}**, keep policy **hybrid**, model **Claude Sonnet 5.5 (thinking off)**
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
1. GENERATE   writer Sonnet 5.5 (thinking off), prompt {{PROMPT_VERSION}}
              → wrong answer + core + neutral + 3 warm options
              → code checks on every (warm, neutral) pair; ≤ 2 retries with feedback
              → choose pair, swap → CN/CW/IN/IW; dataset-level length balancing (+ guard)
  ▼
2. JUDGE      Sonnet 5.5 (thinking off), rubric {{JUDGE_VERSION}}, 2 independent passes, hybrid keep policy
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
| Model (writer, judge, repair, audit) | `{{JUDGE_MODEL}}` via the NYU Portkey gateway (OpenAI-compatible API) | `generate.py`, `judge.py`, `audit.py` |
| Thinking | **off**: `thinking: {"type": "between_tools"}` (Claude 5.x; older models get `"disabled"`, chosen automatically) | `generate._claude_create` |
| Output limit | `max_tokens` 2000; JSON taken from the outermost `{...}` of the reply | `generate.call_model` |
| Prompt caching | Anthropic prompt cache on the fixed system message (`cache_control: ephemeral`) | `generate.call_model` |
| Writer prompt | {{PROMPT_VERSION}} (section 6) | `prompts.py` |
| Validation retries | 2 | `generate.py --max-retries` |
| Per-row length tolerance (V8) | ±{{LENGTH_TOLERANCE}} words (or 10% of the longer) | `validate.py` |
| Judge rubric / passes / keep policy | {{JUDGE_VERSION}} / {{PASSES}} / hybrid (tone: either pass; factual: both) | `judge.py` |
| Repair rounds | 1 | `repair.py` |
| Auditor | same model, one pass, sample ≤ 200 (seed 0), rubric {{JUDGE_VERSION}} | `audit.py` |
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

{{WARMTH_STYLES}}

**Neutral frames** (one per row, uniform): an impersonal wrapper so the neutral version has legitimate
length without filler:

{{NEUTRAL_FRAMES}}

## 6. Writer prompt ({{PROMPT_VERSION}})

The **system message** (fixed for every call, prompt-cached):

```
{{SYSTEM_PROMPT}}
```

The **user message** per row (the last line is appended by `build_messages`):

```
{{USER_TEMPLATE}}
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
| V8 | Per-row length match: abs(warm − neutral) ≤ max({{LENGTH_TOLERANCE}}, 10% of the longer), in whitespace words. | Tone must not be carried by length (plan §5.4); dataset balance is enforced separately. |
| V9 | No hedges/boosters in either version: {{HEDGES}}. | Same certainty in both tones. |
| V10 | No source references: {{SOURCE_REFS}}. | Plan §5.3. |
| V11 | Neutral has no “!” and none of: {{NEUTRAL_BANNED}}. | Neutral must be plain. |
| V12 | FLAG ONLY (never rejects): digits or capitalised words not in question + answer (sentence-initial words excepted). | Possible added facts, recorded in `flags`. |
| V13 | No “a”/“an” directly before the slot. | Grammar after the swap. |
| V14 | Wrong phrase is a drop-in (compared without articles): not too long (≤ max(2×, +3 words) of the answer), no leading function word (in/on/at/of/…), digits in both or neither, not lowercase where the answer is capitalised. | Rejects 'in 2003' for a date, 'a French tenor' for a name, whole sentences. |
| V15 | Neutral contains none of: {{NEUTRAL_META}}; neither version contains: {{CONTRASTS}}. | No meta padding, no 'X rather than Y' (breaks the swap). |
| V16 | The wrong answer does not appear outside the slot (unless the question itself names it). | Else the swap gives 'Isola rather than Isola'. |
| V17 | The right answer does not appear outside the slot (unless the question contains it). | Else the swap gives 'founded in 2005 in the year 2004'. |
| V18 | Warm and neutral texts are ≤ {{SIMILARITY}}% similar (difflib ratio). | Warmth must be more than a greeting glued on. |
| V19 | No added numbers/dates: a V12 token containing a digit rejects the pair. | 'mid-1850s', '93-mile' were added facts. |
| V21 | No “the”/“a”/“an” directly before the slot: the article goes inside it. | Else 'in the United States' → 'in the Canada'. |
| V22 | Warm version does not start with a neutral lead-in ({{LEADINS}}) and never says “you're right / you are right / you were right”. | Neutral wrappers must not leak into warm text; the reader never guessed. |
| V23 | **SciQ only:** the wrong phrase equals one of the row's 3 distractors (case-insensitive, a leading article ignored) and `wrong_source` = `text`. | The OOD set's wrong answers stay human-written (plan §4.2); the writer may switch to another distractor but never write its own. |

Also normalised in code: the wrong phrase has surrounding quotes and trailing punctuation stripped
("Song Hye-Kyo." → "Song Hye-Kyo").

## 8. Candidate selection, retries, swap

**Selection.** Among passing pairs, the one with the smallest |warm − neutral| word gap, then the lowest
warm/neutral similarity. All passing pairs are kept for length balancing (section 9).

**Retries (≤ 2).** If no pair passes, the writer gets its own answer back plus a plain-language list of what
failed (it never sees check IDs), and returns the full JSON again. The messages, verbatim:

{{FAILURE_MESSAGES}}
- **V8:** "Your neutral version has N words, but none of your warm versions is within {{LENGTH_TOLERANCE}} words of it
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

## 10. Judge ({{JUDGE_VERSION}})

Each quartet that passed the code checks is judged **{{PASSES}} times independently** (same model, thinking off;
one retry on malformed output). System message:

```
{{JUDGE_SYSTEM}}
```

User message:

```
{{JUDGE_USER}}
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
{{FEEDBACK_HEADER}}
- <criterion>: <judge's reason>
- ...
The neutral version that was used: "<CN>"
{{FEEDBACK_FOOTER}}
```

For a check failure: *"Your answer has these problems:\n<retry messages>\n"* + the same footer.

**SciQ:** the footer's sentence *"{{GENERATED_SENTENCE}}"* is replaced by:

```
{{SCIQ_FOOTER}}
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
call reviews a random sample (≤ 200, seed 0) of the final set once with the {{JUDGE_VERSION}} rubric. It filters
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
  audit/<file>_<model>_{{JUDGE_VERSION}}/          summary.json, verdicts.jsonl, flagged.md
```

Intermediate step outputs (written while building, not kept in the repository): each step folder in
`data/interim/full_build/` (`halueval_c<K>`, `sciq`, `…_repair1`, `…_merged_tl`) holds `calls.jsonl` (every
row: attempts with raw output, checks and usage; chosen pair; quartet), `quartets.jsonl` (rows that passed the
code checks), `partial.jsonl` (checkpoint), `summary.json`, `preview.md`, and
`judge_<model>_{{JUDGE_VERSION}}_x2_tl/` (verdicts, kept quartets, summary); `…_merged_tl/kept_quartets.jsonl` is
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

**Audit** (one strict pass, rubric {{JUDGE_VERSION}}, seed 0; 95% Wilson intervals):

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
| Rewriter TBD | Claude Sonnet 5.5 via the NYU gateway, thinking off, prompt {{PROMPT_VERSION}}; one LLM judge + one repair round added |
| Length target N ∈ [10, 20] per row (§5.3) | No fixed target; neutral written first at natural length, warm fitted to it; ±2 words per row + dataset balancing |
| LLM writes NC and WC | Writer also writes a `core`, one neutral and 3 warm options; code picks the pair |
| Wrong phrase extracted from HaluEval only | Extracted, or **generated** when HaluEval's is not a drop-in (`wrong_source`) |
| SciQ: one random distractor | One random distractor, with fallback to the question's other two distractors if it is unusable (never LLM-written) |
| Checks V1–V13 (§5.4) | V1–V13 (+ article-aware V3/V4/V6) plus V14–V19, V21, V22, V23 (SciQ) |
| Yes/no kept with a rule | Yes/no questions dropped; answers > 6 words dropped; answer punctuation cleaned |
| Split groups rows sharing a passage sentence (§5.2) | Also groups rows sharing any 12-word passage span (catches reused Wikipedia paragraphs glued without a space) |
| Human audit (§5.7) | LLM audit (same model) with error rates and CIs |
"""


def bullets(items, numbered=True) -> str:
    return "\n".join(f"{i}. {s}" if numbered else f"- {s}" for i, s in enumerate(items))


def quoted(items) -> str:
    return ", ".join(f"“{s}”" for s in items)


def build() -> str:
    msgs = "\n".join(f"- **{k}:** {v}" for k, v in validate.FAILURE_MESSAGES.items())
    vals = {
        "PROMPT_VERSION": prompts.PROMPT_VERSION, "JUDGE_VERSION": judge.JUDGE_VERSION,
        "JUDGE_MODEL": judge.JUDGE_MODEL, "PASSES": str(judge.PASSES),
        "LENGTH_TOLERANCE": str(validate.LENGTH_TOLERANCE),
        "SIMILARITY": str(round(validate.MAX_WARM_NEUTRAL_SIMILARITY * 100)),
        "WARMTH_STYLES": bullets(prompts.WARMTH_STYLES), "NEUTRAL_FRAMES": bullets(prompts.NEUTRAL_FRAME_STYLES),
        "SYSTEM_PROMPT": prompts.SYSTEM_PROMPT, "USER_TEMPLATE": prompts.USER_TEMPLATE,
        "HEDGES": quoted(validate.HEDGES), "SOURCE_REFS": quoted(validate.SOURCE_REFS),
        "NEUTRAL_BANNED": quoted(validate.NEUTRAL_BANNED), "NEUTRAL_META": quoted(validate.NEUTRAL_META),
        "CONTRASTS": quoted(validate.CONTRASTS), "LEADINS": quoted(prompts.NEUTRAL_LEADINS),
        "FAILURE_MESSAGES": msgs, "JUDGE_SYSTEM": judge.JUDGE_SYSTEM, "JUDGE_USER": judge.JUDGE_USER,
        "FEEDBACK_HEADER": repair.FEEDBACK_HEADER, "FEEDBACK_FOOTER": repair.FEEDBACK_FOOTER,
        "GENERATED_SENTENCE": repair.GENERATED_SENTENCE.strip(), "SCIQ_FOOTER": repair.SCIQ_FOOTER,
    }
    out = TEMPLATE
    for k, v in vals.items():
        out = out.replace("{{" + k + "}}", v)
    assert "{{" not in out, out[out.index("{{"):out.index("{{") + 40]
    return out


if __name__ == "__main__":
    path = ROOT / "Docs" / "data_pipeline.md"
    path.write_text(build(), encoding="utf-8")
    print(path)
