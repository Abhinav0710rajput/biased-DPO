# Same Responses, Different Pairs — End-to-End Project Plan (Agent Handover)

**Team:** Abhinav Rajput (ar10026) · Anushri Iyer (ai2185) · Leo Lorence George (lg4143)
**Course:** NYU CDS — NLP course project
**Status:** Proposal submitted. Data sources chosen. Rewriter LLM and DPO policy model(s) **TBD**.
**Document purpose:** A complete, self-contained spec. An agent with no prior context should be able to read this top to bottom and execute Phase 1 (data → DPO training → evaluation → analysis). Phase 2 (persona vectors) is specified at the end and starts only after Phase 1 produces results.

---

## Table of contents

0. [How to use this document](#0-how-to-use-this-document)
1. [The research question in one page](#1-the-research-question-in-one-page)
2. [Core concepts and math](#2-core-concepts-and-math)
3. [Hypotheses and predictions](#3-hypotheses-and-predictions)
4. [Data sources](#4-data-sources)
5. [Data curation pipeline (building the quartets)](#5-data-curation-pipeline-building-the-quartets)
6. [Open decision: rewriter LLM (TBD)](#6-open-decision-rewriter-llm-tbd)
7. [DPO training](#7-dpo-training)
8. [Open decision: DPO policy model(s) and hyperparameters (TBD)](#8-open-decision-dpo-policy-models-and-hyperparameters-tbd)
9. [Sanity checks before any real run](#9-sanity-checks-before-any-real-run)
10. [Evaluation](#10-evaluation)
11. [Analysis and how to interpret results](#11-analysis-and-how-to-interpret-results)
12. [Phase 2: persona vectors](#12-phase-2-persona-vectors)
13. [Optional extensions](#13-optional-extensions)
14. [Milestones and order of work](#14-milestones-and-order-of-work)
15. [Suggested repository layout](#15-suggested-repository-layout)
16. [Rules for the agent (non-negotiables)](#16-rules-for-the-agent-non-negotiables)
17. [Risks and pitfalls](#17-risks-and-pitfalls)
18. [Decision log (TBD items)](#18-decision-log-tbd-items)
19. [References](#19-references)
20. [Appendix A: derivations](#appendix-a-derivations)
21. [Appendix B: fully worked examples](#appendix-b-fully-worked-examples)
22. [Appendix C: glossary](#appendix-c-glossary)

---

## 0. How to use this document

- Sections 1–3 explain **what** we are testing and **why**. Read them before touching code; every design choice later follows from them.
- Sections 4–6 build the **data**. Sections 7–9 **train**. Sections 10–11 **evaluate and interpret**.
- Items marked **TBD** are open decisions owned by the team. When you reach one, either use the stated default for a pilot, or stop and ask, as indicated.
- Anything marked **MUST** is required for the experiment to be valid. Anything marked **SHOULD** is strongly recommended. **OPTIONAL** is nice-to-have.

---

## 1. The research question in one page

**DPO** (Direct Preference Optimization) trains a language model from pairs of responses to the same prompt: one *chosen* (preferred) and one *rejected*. Real preference data rewards correctness, but responses also differ in irrelevant style (tone, length, formatting), and models are known to pick up such style. Training for warmth has even been shown to reduce factual reliability.

We study a design choice nobody controls for: **given the exact same set of responses, does the way we pair them up change what DPO learns?**

For every question we build a **quartet** of four responses:

| Code | Meaning |
|---|---|
| **CW** | Correct answer, Warm tone |
| **CN** | Correct answer, Neutral tone |
| **IW** | Incorrect answer, Warm tone |
| **IN** | Incorrect answer, Neutral tone |

Correct always beats incorrect. From the *same* quartets we build different training sets that differ **only in pairing**:

| Training set | Pairs (chosen ≻ rejected) |
|---|---|
| **Matched** (same tone inside each pair) | CW ≻ IW, CN ≻ IN |
| **Crossed** (opposite tones inside each pair) | CW ≻ IN, CN ≻ IW |
| **Mixed** (all four pairs) | all of the above |

In every training set, every response is chosen or rejected equally often, so **tone never predicts which response wins**. Only the pairing changes. Loss function, data, labels, and initialization stay identical.

**Why anyone should care:** if pairing changes what the model learns, then everyone building preference data (e.g., datasets with several responses per prompt) is already making this choice implicitly, and could make it deliberately at zero extra cost.

---

## 2. Core concepts and math

### 2.1 The score DPO works with

For prompt `x` and response `y`:

```
r(y) = log π_θ(y | x) − log π_ref(y | x)
```

- `π_θ` = the model being trained (the **policy**).
- `π_ref` = the frozen starting model (the **reference**).
- `log π(y | x)` = sum of token log-probabilities of the response tokens only (prompt tokens are masked).
- `r(y)` = "how much training has raised this response's log-probability above where it started". At initialization, `r(y) = 0` for every response.

DPO's loss for one pair (chosen `y+`, rejected `y−`) is:

```
ℓ(β · [r(y+) − r(y−)])      where  ℓ(z) = log(1 + exp(−z)) = −log σ(z)
```

`β` is the DPO temperature. The loss depends **only on the gap** `r(y+) − r(y−)`.

### 2.2 Three numbers per quartet: u, v, w

Any four numbers on a 2×2 grid can be written as an average plus three effects (exactly like a two-way ANOVA). For one quartet:

```
u = ½[r(CW) + r(CN)] − ½[r(IW) + r(IN)]     # fact preference
v = ½[r(CW) + r(IW)] − ½[r(CN) + r(IN)]     # tone preference
w = ½[r(CW) − r(IW)] − ½[r(CN) − r(IN)]     # tone × fact interaction
```

| Symbol | Name | Plain meaning | Desired |
|---|---|---|---|
| **u** | Fact preference | How much the model prefers correct over incorrect, averaged over tone | **Large** |
| **v** | Tone preference | How much it prefers warm over neutral, regardless of correctness. Sign tells direction (+ favors warm, − favors neutral). | **≈ 0** |
| **w** | Interaction | Whether tone changes how well it separates right from wrong. + means it separates better in warm phrasing, − better in neutral. | **≈ 0** |

The overall average of the four scores is irrelevant: DPO only sees differences.

Each response's score is the average plus half of a signed combination:

| Response | Score |
|---|---|
| CW | avg + ½(+u +v +w) |
| CN | avg + ½(+u −v −w) |
| IW | avg + ½(−u +v −w) |
| IN | avg + ½(−u −v +w) |

Sign rule: `u` is + for correct, − for incorrect. `v` is + for warm, − for neutral. `w` is + when those two signs agree.

### 2.3 What each pair "contains"

Subtracting rows gives the gap for each possible pair (exact algebra, no approximation):

| Pair | Type | Gap r(chosen) − r(rejected) |
|---|---|---|
| CW ≻ IW | matched | **u + w** |
| CN ≻ IN | matched | **u − w** |
| CW ≻ IN | crossed | **u + v** |
| CN ≻ IW | crossed | **u − v** |

**Key consequence:**
- In matched pairs, both responses share the same tone, so **v cancels out**. The matched loss is a function of `u` and `w` only.
- In crossed pairs, **w cancels out**. The crossed loss is a function of `u` and `v` only.

### 2.4 The loss for any mixture

Let `ρ` (rho) = fraction of weight on crossed pairs. Each pair within a type gets equal weight:

| Pair | Weight |
|---|---|
| CW ≻ IW | (1 − ρ)/2 |
| CN ≻ IN | (1 − ρ)/2 |
| CW ≻ IN | ρ/2 |
| CN ≻ IW | ρ/2 |

```
L(ρ) = (1−ρ)/2 · [ℓ(β(u+w)) + ℓ(β(u−w))]  +  ρ/2 · [ℓ(β(u+v)) + ℓ(β(u−v))]
```

- `ρ = 0` → matched only. `ρ = 1` → crossed only. `ρ = ½` → mixed (all four pairs, ¼ each).
- **The 50/50 split inside each type is mandatory.** If, e.g., CW ≻ IN gets more weight than CN ≻ IW, warm responses win more often than neutral ones, tone starts predicting the label, and the loss actively pushes `v` upward. That unbalanced version is used **only** as a positive control (Section 9).

### 2.5 Why the loss "corrects" some effects but not others

For fixed `u`, the function `½ℓ(β(u+x)) + ½ℓ(β(u−x))` is even and convex in `x`, minimized at `x = 0`. Uneven gaps cost more than even ones (a nearly-wrong pair costs more than an easy pair saves). So:

- Matched training pushes `w` toward 0, but **cannot correct `v`** (it never appears in the loss).
- Crossed training pushes `v` toward 0, but **cannot correct `w`**.
- Mixed training pushes both toward 0, each at half strength.

### 2.6 Why differences can only appear during training

At initialization every `r = 0`, so `u = v = w = 0`, every gap is 0, and **all mixtures produce exactly the same gradient** (proof in Appendix A). The difference appears only once learning `u` spills over into `v` and `w` through shared parameters (raising "Delhi" after a warm prefix and after a neutral prefix are not perfectly identical updates). Whichever effect a mixture cannot see is free to drift. Moya et al. (2026) prove that this kind of leakage can happen even when a feature is perfectly balanced in the data.

### 2.7 Preliminary toy result (already done)

A log-linear toy model with shared, non-orthogonal feature directions and **no tone signal in the data** reproduced the predicted pattern on held-out prompts:

| Training set | mean \|v\| | mean \|w\| |
|---|---|---|
| Matched (ρ=0) | 4.6 | 0.45 |
| Mixed (ρ=½) | 1.2 | 1.0 |
| Crossed (ρ=1) | 0.56 | 4.0 |

`u` was ≈ 8.7 for all three. Worst-case accuracy saturated in the toy, which is why the LLM study is needed.

---

## 3. Hypotheses and predictions

**H0 (null):** Tone never predicts the winner in any training set, so every model learns the facts (large `u`) with `v ≈ 0` and `w ≈ 0`, whatever the pairing. Pairing makes no difference.

**H1 (ours):** Learning the facts spills into `v` and `w`, and each training set corrects only what its loss contains:
- Matched (ρ=0) ends with the **largest |v|** (general tone preference left uncorrected).
- Crossed (ρ=1) ends with the **largest |w|** (tone-dependent fact-checking left uncorrected).
- Mixed (ρ=½) keeps both moderate.
- As ρ goes 0 → 1: |v| decreases, |w| increases, `u` stays roughly flat, and worst-case accuracy peaks somewhere in the middle.

**H2 (Phase 2, persona vectors):** The same split is visible inside the model (Section 12).

**What each outcome means for the paper:**

| Outcome | Meaning |
|---|---|
| Crossover appears, beyond seed noise, at matched `u`, on held-out data | Main result. Pairing controls *which* style bias the model learns. |
| All models the same | H0 holds; publish the identity + clean null result. |
| Differences in the opposite direction | Something other than this mechanism drives training; investigate before claiming anything. |
| Effect only on templates/wording seen in training | Lexical shortcut, not tone; narrow the claim. |
| Scores move but generation doesn't | Effect is in scoring/ranking only; narrower claim. |

The single most important result is H1 on held-out data at matched `u`.

---

## 4. Data sources

### 4.1 Training + in-domain test: HaluEval QA

- **Canonical source (verified):** GitHub `RUCAIBox/HaluEval`, file `data/qa_data.json` (JSON Lines).
  - Raw URL: `https://raw.githubusercontent.com/RUCAIBox/HaluEval/main/data/qa_data.json`
- **Hugging Face mirror:** `pminervini/HaluEval`, config `qa` — https://huggingface.co/datasets/pminervini/HaluEval
  - The mirror is community-maintained. If you use it, **verify field names** against the GitHub file before writing code.
- **License:** Apache-2.0.
- **Fields (GitHub file):** `knowledge` (Wikipedia passage from HotpotQA), `question`, `right_answer`, `hallucinated_answer`.

**Measured statistics (from our own analysis of the GitHub file):**

| Statistic | Value |
|---|---|
| Rows | 10,000 |
| Unique questions | 10,000 |
| Unique passages | 9,936 |
| Rows sharing no passage sentence with any other row | 7,837 |
| Rows in clusters that share a sentence | the rest; 762 pairs, largest cluster 12 rows |
| Yes/no questions | 623 |
| `right_answer` length | median 2 words |
| `hallucinated_answer` length | median 9 words (full sentences) |
| `right_answer` appears verbatim in passage | 95.5% |

Example rows:

| right_answer | hallucinated_answer (as given) |
|---|---|
| Delhi | "The Oberoi family's hotel company is based in Mumbai." |
| Martin Scorsese | "The film was directed by Paul Schrader." |
| Princes Highway | "Montague Island is located on the Pacific Highway." |
| 23 January 1897 | "The birthdate of this Indian nationalist is unknown." (→ drop, no concrete wrong answer) |

### 4.2 Out-of-domain test: SciQ

- **Hugging Face:** `allenai/sciq` — https://huggingface.co/datasets/allenai/sciq
- **License:** CC BY-NC 3.0 (fine for course/research use).
- **Fields:** `question`, `distractor1`, `distractor2`, `distractor3`, `correct_answer`, `support` (paragraph, sometimes empty).
- **Splits:** train 11,679 · validation 1,000 · test 1,000. **Use only validation + test** for the OOD set.
- Real crowdsourced science exam questions. Distractors are **human-written** short phrases (HaluEval's wrong answers were written by ChatGPT; note this difference in the write-up).

Example (from the dataset card, cropped):
```
support:        Without Coriolis Effect the global winds would blow north to south or south to north. …
question:       What phenomenon makes global winds blow northeast to southwest or the reverse in the northern hemisphere …?
correct_answer: coriolis effect
distractors:    muon effect | centrifugal effect | tropical effect
```

**Why SciQ:** it keeps HaluEval's format (passage + question + short answer) but changes the domain (Wikipedia trivia → science). Any performance change is attributable to domain, not format. The quartet construction methodology is **identical** (Section 5).

### 4.3 Loading

```python
from datasets import load_dataset
halueval = load_dataset("pminervini/HaluEval", "qa")   # or read qa_data.json from GitHub
sciq = load_dataset("allenai/sciq")                    # use "validation" and "test"
```

---

## 5. Data curation pipeline (building the quartets)

### 5.0 Overview

```
raw rows ──► filter ──► split (HaluEval only) ──► rewrite (LLM, one call per row)
        ──► validate (code) ──► swap (code) ──► quartet JSONL ──► audit (humans) ──► FREEZE
```

**The single most important design rule:** the LLM writes **only the two correct versions** (NC and WC). The two incorrect versions (NI and WI) are produced **by code**, by substituting the wrong answer into the exact same text. This guarantees:
- Within each tone, correct and incorrect differ **only in the answer phrase** (matched pairs are clean).
- Within each fact, warm and neutral differ **only in tone/wrapper**.

Do **not** ask the LLM to write all four versions independently: the incorrect versions would differ in wording as well as fact, breaking the design.

### 5.1 Step 1: filtering

**HaluEval:**
- Yes/no questions (`right_answer` ∈ {yes, no}, case-insensitive): wrong answer = the opposite. No extraction needed.
- All others: extraction (Step 3) must produce a concrete wrong phrase, otherwise drop.
- Drop if the extracted wrong phrase equals the right answer or either contains the other (case/punctuation-normalized).

**SciQ:**
- Drop rows with empty `support`.
- Keep only rows where `correct_answer` appears in `support` (case-insensitive), to match HaluEval (95.5% verbatim).
- Choose **one** distractor per question at random with a fixed seed (e.g., `random.Random(0)`), giving one quartet per question like HaluEval. Record which distractor was used.

Record every drop with a reason code. Report counts at each stage.

### 5.2 Step 2: splitting HaluEval (MUST be grouped)

Passages occasionally share Wikipedia sentences, so a random row split would leak passage text between train and test.

Procedure:
1. Normalize each `knowledge` string (insert a space after a period directly followed by a capital letter; HaluEval sometimes concatenates paragraphs without spaces).
2. Split into sentences; keep sentences longer than ~25 characters.
3. Build a union-find over rows: link two rows if they share any sentence.
4. Each connected component is a **group**.
5. Shuffle groups with a fixed seed and assign whole groups to splits, targeting **80% train / 10% validation / 10% test** of rows (≈ 8,000 / 1,000 / 1,000 before filtering).

No group may span two splits. Save `group_id` on every quartet.

SciQ needs no grouping (it's entirely the OOD test set).

### 5.3 Step 3: the rewrite call (one LLM call per row)

Each row gets **one** call that returns three things: the extracted wrong phrase, the neutral correct version, and the warm correct version.

**Length target:** draw a target word count `N` per row, uniformly from 10–20 (so lengths vary across rows but are matched within a row). Warm and neutral must both hit ~`N`.

**Prompt template (v1; adjust after the pilot, and version it):**

```
You are helping build a controlled dataset. You will write two versions of a short
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
- No emojis.
```

Notes:
- For HaluEval, `{wrong_text}` = `hallucinated_answer`. For SciQ, `{wrong_text}` = the chosen distractor (already a short phrase; extraction simply returns it). **This keeps the pipeline code identical for both datasets.**
- For yes/no questions, the wrong phrase is set by rule; you may still send the call for the rewrites and ignore `wrong_phrase`.
- The passage is **not** sent to the rewriter (it doesn't need it, and withholding it reduces the chance of extra facts leaking in).
- Use the **same rewriter, same prompt version, same rules** for train, in-domain test, and SciQ OOD test.

### 5.4 Step 4: automatic validation (code, free)

Reject (and optionally retry up to 2 times with the failure reason appended to the prompt) if any check fails:

| # | Check | Rule |
|---|---|---|
| V1 | JSON | Parses; has the 3 fields |
| V2 | Wrong phrase present | Non-null (or set by yes/no rule) |
| V3 | Wrong phrase is real | Appears verbatim (case-insensitive) in `wrong_text` |
| V4 | Wrong ≠ right | Normalized strings differ and neither contains the other |
| V5 | Tag count | Exactly one `<ans>…</ans>` in each version |
| V6 | Tag content | Text inside tags equals `right_answer` exactly |
| V7 | Not at start | Answer tag is not the first content of the sentence |
| V8 | Length match | Token counts (**policy model's tokenizer**) of warm vs neutral differ by ≤ max(2, 10%) |
| V9 | No hedges / boosters | Neither contains a banned list: "I think", "I believe", "probably", "maybe", "might", "perhaps", "definitely", "certainly", "surely", "undoubtedly" |
| V10 | No source references | Neither contains "passage", "according to", "the text", "the context", "the source" |
| V11 | Neutral is plain | No "!" and no greeting/closing words (e.g., "hope", "happy to", "great question", "glad") |
| V12 | No new facts (heuristic) | No digits or capitalized words in either version that don't appear in the question or answer (sentence-initial capitals excepted). Flag, don't auto-drop; send flagged items to human review. |
| V13 | Swap grammar (heuristic) | No "a"/"an" immediately before the tag |

Store each row's pass/fail results and retry count.

### 5.5 Step 5: the swap (code)

For each validated row:
- `NC` = neutral text with tags removed.
- `CW` = warm text with tags removed.
- `NI` = neutral text with the tagged answer replaced by `wrong_phrase`, tags removed.
- `IW` = warm text with the tagged answer replaced by `wrong_phrase`, tags removed.
- Record the **character span of the answer** in each of the four responses (needed for answer-span scoring in Section 10).

Swapping changes token count by the same amount in both tones, so it never introduces a tone–length correlation.

### 5.6 Step 6: diversity and length diagnostics (SHOULD)

After building all quartets, report:
- **Length:** mean and distribution of (tokens(warm) − tokens(neutral)). Mean should be ≈ 0 with both signs present.
- **Opener diversity:** the 20 most common first-4-word openings of warm responses. No single opening should exceed ~10% of rows. If it does, revise the prompt (e.g., add a randomly sampled "style hint" per row) and regenerate.
- **Closer diversity:** same for the last 4 words.

### 5.7 Step 7: human audit (MUST before freezing)

Team reviews **100 random train quartets + 100 random test quartets + 100 random SciQ quartets** with this rubric:

1. Correct answer stated correctly; fact preserved.
2. No extra facts added.
3. Warm vs neutral clearly differ in tone.
4. Neutral reads plain, not rude/cold.
5. NI and WI are grammatical after the swap.
6. No hedging/certainty difference.

Target: < 3% of quartets with any failure. If higher, fix the prompt/checks and regenerate the affected split. Record the audit results in `data/audit/`.

**OPTIONAL:** an LLM judge on the test sets only (results rest on them). Checks 1–3 above. Cheaper than auditing everything by hand.

### 5.8 Step 8: freeze

- Write final files: `data/quartets/{train,val,test,ood_sciq}.jsonl`.
- Compute and store SHA-256 hashes of each file in `data/quartets/MANIFEST.json`.
- **Never edit test or OOD files after freezing.** If a bug is found, create a new version (`v2`) and rerun everything that depends on it.

### 5.9 Quartet record schema (JSONL, one row per question)

```json
{
  "qid": "halueval-000123",
  "source": "halueval_qa",
  "split": "train",
  "group_id": 4512,
  "passage": "The Oberoi family is an Indian family ...",
  "question": "The Oberoi family is part of a hotel company that has a head office in what city?",
  "correct_answer": "Delhi",
  "wrong_answer": "Mumbai",
  "wrong_source_text": "The Oberoi family's hotel company is based in Mumbai.",
  "is_yesno": false,
  "target_words": 14,
  "responses": {
    "CN": {"text": "...", "ans_span": [74, 79]},
    "CW": {"text": "...", "ans_span": [61, 66]},
    "IN": {"text": "...", "ans_span": [74, 80]},
    "IW": {"text": "...", "ans_span": [61, 67]}
  },
  "n_tokens": {"CN": 17, "CW": 18, "IN": 17, "IW": 18},
  "rewriter": {"model": "TBD", "prompt_version": "v1", "retries": 0},
  "checks": {"V1": true, "...": true},
  "flags": []
}
```

For SciQ also store `"distractor_index": 2`.

### 5.10 The prompt the policy model sees

Identical for all four responses of a quartet and for both datasets. It **never** asks for a tone.

```
User: Answer the question using the passage.

Passage: {passage}

Question: {question}
```

The assistant turn is one of the four responses. Use the policy model's chat template (for Qwen3: `enable_thinking=False`).

**Open-book vs closed-book (TBD, default open-book):** before full training, measure the base policy's generation accuracy on ~200 validation questions with and without the passage. Open-book is the default because `u` can generalize to held-out questions (the skill is "read the passage and reject the fabricated answer"). If open-book accuracy is essentially perfect and the team prefers a harder task, a closed-book variant can be added as an extension, but note that in closed-book, held-out `u` depends on facts the model may never have learned.

---

## 6. Open decision: rewriter LLM (TBD)

The LLM that writes NC/WC (and extracts the wrong phrase) is **not yet chosen**.

**Candidates:**
- OpenAI GPT-5 family (GPT-5.5, GPT-5.4, GPT-5, and their mini variants).
- Other API models (e.g., Claude family).
- Open-weight models run on NYU HPC (e.g., a 30B-class Qwen3 model): no API cost.

**Selection procedure (MUST):**
1. Take 100 random HaluEval train rows + 50 SciQ rows.
2. Run the exact v1 prompt with 2–3 candidate models.
3. For each model, measure: validation pass rate (Section 5.4), human audit error rate (Section 5.7 rubric on ~50 items), length-match quality, opener diversity, and cost.
4. Pick the cheapest model that achieves < 3% audit errors and ≥ 85% first-pass validation.

**Cost guidance (estimates as of Nov 2026; verify prices before running):**
- Workload ≈ 11–12k rows × 1 call (~450 input / ~130 output tokens) + ~10% retries.
- With the **Batch API (50% off)**: roughly $11 (GPT-5), $20 (GPT-5.4), $40 (GPT-5.5); mini models are a few dollars.
- **Set reasoning effort to the lowest setting** (`none`/`minimal`). Reasoning tokens are billed as output and can multiply cost several times; rewriting doesn't need them.

**OPTIONAL second rewriter:** build an extra copy of the test set with a *different* model family. If the effect holds on wording from a rewriter never seen in training, it's about tone, not one model's phrasing.

---

## 7. DPO training

### 7.1 Conditions

| Condition | ρ | Pairs used | Purpose |
|---|---|---|---|
| Matched | 0 | CW≻IW, CN≻IN | Main |
| ρ = 0.25 | 0.25 | all four, weighted | Trend |
| Mixed | 0.5 | all four, equal | Main |
| ρ = 0.75 | 0.75 | all four, weighted | Trend |
| Crossed | 1 | CW≻IN, CN≻IW | Main |

Weights per pair: `(1−ρ)/2` for each matched pair, `ρ/2` for each crossed pair (Section 2.4). Grid is a default; final grid **TBD**.

### 7.2 Baselines and controls

| Run | What | Why |
|---|---|---|
| **Matched + ties** (Moya et al. tie training) | Matched pairs plus tie pairs CW~CN and IW~IN (soft label 0.5 → loss `½ℓ(βm) + ½ℓ(−βm)`, minimized at gap 0). Check Moya et al. for their exact formulation. | Strongest existing method; tie gaps are `v+w` and `v−w`, so ties constrain both. Main competitor. |
| **KTO** | Unpaired: correct responses desirable, incorrect undesirable | "No pairing" reference. Identical across ρ by construction → **one run** (×seeds). |
| **SFT on chosen** | Supervised fine-tuning on CW and CN only | Identical across ρ by construction → one run (×seeds). |
| **Positive control** | Unbalanced crossed: CW≻IN weight 0.8, CN≻IW weight 0.2 (tone now predicts the winner) | Proves the `v` metric can detect an injected tone bias. |

### 7.3 Implementation requirements (MUST)

1. **Same quartets, same order, same batches for every condition.** Batches contain whole quartets. Given a seed, the quartet order must be identical across all ρ. Verify with batch hashes.
2. **All four responses are always forwarded**, for every condition (even matched uses all four, since its two pairs cover all four responses). Compute is identical across conditions.
3. **Reference log-probs:** compute once per response with the frozen reference (or LoRA adapters disabled) and cache them.
4. **No dropout** (LoRA dropout = 0) so that `r = 0` exactly at step 0.
5. **Response-only log-probs:** mask prompt tokens; sum log-probs over the response tokens. Decide once whether the end-of-turn token is included, and apply it consistently everywhere (training and evaluation).
6. **Identical everything else** across conditions: initialization, LoRA init seed, optimizer, LR schedule, β, epochs, data order.
7. **Log `u`, `v`, `w`** (batch means) during training, and evaluate on validation at frequent checkpoints (dense early: e.g., every 25 steps for the first 300 steps, then every 100).

### 7.4 Recommended implementation: custom quartet loop

TRL's `DPOTrainer` takes (prompt, chosen, rejected) rows and shuffles rows independently, which breaks requirement 1 and makes fractional ρ awkward. Use TRL only for a quick first smoke test; use a small custom loop for real runs.

Pseudocode:

```python
def contrasts(r):  # r: tensor [B, 4] in order CW, CN, IW, IN
    CW, CN, IW, IN = r.unbind(-1)
    u = 0.5 * (CW + CN) - 0.5 * (IW + IN)
    v = 0.5 * (CW + IW) - 0.5 * (CN + IN)
    w = 0.5 * (CW - IW) - 0.5 * (CN - IN)
    return u, v, w

def ell(z):  # -log sigmoid(z)
    return torch.nn.functional.softplus(-z)

def quartet_loss(r, beta, rho, tie_weight=0.0):
    u, v, w = contrasts(r)
    loss = (1 - rho) / 2 * (ell(beta * (u + w)) + ell(beta * (u - w))) \
         +      rho  / 2 * (ell(beta * (u + v)) + ell(beta * (u - v)))
    if tie_weight > 0:   # tie baseline: gaps CW-CN = v+w, IW-IN = v-w
        for m in (v + w, v - w):
            loss = loss + tie_weight * 0.5 * (ell(beta * m) + ell(-beta * m))
    return loss.mean(), (u.detach(), v.detach(), w.detach())

for step, quartets in enumerate(loader):            # fixed order given seed
    seqs = build_sequences(quartets)                # 4 per quartet: prompt + response
    logp_pol = response_logprobs(policy, seqs)      # [B, 4]
    logp_ref = cached_ref_logprobs(quartets)        # [B, 4]
    r = logp_pol - logp_ref
    loss, (u, v, w) = quartet_loss(r, beta, rho)
    loss.backward(); optimizer.step(); optimizer.zero_grad()
    log(step, loss, u.mean(), v.mean(), w.mean(), v.abs().mean(), w.abs().mean())
```

Quick-start alternative (smoke test only): expand quartets into TRL rows. Matched → 2 rows per quartet; crossed → 2 rows; mixed → 4 rows; fractional ρ → duplicate rows in proportion (e.g., ρ=0.25 → 3 copies of each matched pair, 1 of each crossed pair).

### 7.5 Reading length-related risks during training

DPO is known to exploit length because `r` sums over tokens. Length matching (Section 5.4, V8) protects the crossed pairs. Matched pairs are naturally length-matched (same wrapper). Still log, per checkpoint, the mean `r` per token for warm vs neutral responses.

---

## 8. Open decision: DPO policy model(s) and hyperparameters (TBD)

**Policy model(s): TBD.** Requirements: instruction-tuned, small enough for 15–25 LoRA runs × 3 seeds on the team's compute, with an available tokenizer and chat template.

- Default candidate for the pilot: **Qwen3-1.7B** (chat template with `enable_thinking=False`).
- Confirmation model (TBD): a second size or family (e.g., Qwen3-4B, or a ~3B Llama-family instruct model).
- The **tokenizer of the chosen policy model** is used for the length check (V8). If the policy model changes, rerun V8 (the data itself need not change unless many rows fail).

**Hyperparameters: TBD.** Starting points for the pilot:

| Hyperparameter | Starting value | Notes |
|---|---|---|
| β | 0.1 | Standard DPO default |
| Adapter | LoRA r=16, α=32, dropout 0, all linear projections | Dropout must be 0 |
| Learning rate | sweep {5e-6, 2e-5, 5e-5} | Tune **once** on ρ=0.5 using validation loss/pairwise accuracy, then freeze for all conditions |
| Batch | 16 quartets per optimizer step (grad accumulation OK) | Whole quartets per micro-batch |
| Epochs | 2–3 | Watch validation `u` |
| Schedule | cosine, 5% warmup | |
| Precision | bf16 | |
| Seeds | 3 per condition | Same 3 seeds across all conditions |

**Compute estimate (rough):** Qwen3-1.7B + LoRA fits on one A100-40GB. Full grid = 5 ρ values × 3 seeds = 15 runs, plus baselines (ties ×3, KTO ×3, SFT ×3, positive control ×1–3).

---

## 9. Sanity checks before any real run

| # | Test | Pass criterion |
|---|---|---|
| T1 | Identity check | For random `r`, the loss computed pair-by-pair equals the (u, v, w) formula to ~1e-6 |
| T2 | **Step-0 gradient equality** | On the same batch at initialization, gradients for ρ ∈ {0, 0.5, 1} are identical up to floating-point noise (they must be; see Appendix A). If not, there is a bug (dropout, batch mismatch, reference mismatch). |
| T3 | Batch identity | Batch content hashes identical across conditions for the same seed |
| T4 | Overfit | 32 quartets, many steps: training pairwise accuracy → ~100%, `u` grows |
| T5 | Positive control | Unbalanced crossed run: `v` grows clearly relative to balanced crossed. Confirms the metric detects tone bias. |
| T6 | Reference cache | `r = 0` exactly for all responses at step 0 |

Do not start the full grid until T1–T6 pass.

---

## 10. Evaluation

All evaluation uses the **frozen** test sets: HaluEval test (in-domain) and SciQ (OOD). Validation is used only for checkpoint selection and tuning.

### 10.1 Score-based metrics (need full quartets)

For every test quartet and every evaluated checkpoint, compute and store:
- `logp_pol(y)` and `logp_ref(y)` for all four responses, both over the **full response** and over the **answer span only** (tokens overlapping the stored `ans_span`).
- `r(y) = logp_pol(y) − logp_ref(y)`.

Then per quartet: `u`, `v`, `w`, and the four gaps.

**Primary scoring = full-response `r`** (exactly what the DPO loss sees, so the theory applies exactly; also the model's implicit DPO reward). **Secondary = answer-span `r`** (isolates the fact tokens; robustness check).

Aggregate per run:

| Metric | Definition |
|---|---|
| mean `u` | Fact preference (should be large and similar across ρ) |
| mean `v`, mean \|v\| | Direction and size of tone preference |
| mean `w`, mean \|w\| | Direction and size of interaction |
| **Worst-case accuracy (primary behavioral score metric)** | Fraction of quartets where all four gaps are positive, i.e. `u > |v|` and `u > |w|` |
| Per-gap accuracies | Fraction positive for each of u+w, u−w, u+v, u−v |

Worst-case accuracy is the DPO-implicit-reward analogue of RM-Bench's "hard accuracy".

### 10.2 Behavioral generation metrics (need only the question)

1. **Free generation:** prompt as in Section 5.10, greedy decoding. Accuracy = output contains the correct answer (normalized match) and not the wrong one. Also measure **warmth rate** of generated text (LLM judge or a simple classifier; method TBD) → behavioral analogue of `v`.
2. **Forced-prefix generation:** prefill the assistant turn with a warm opener (e.g., "Great question! ") vs a neutral opener (e.g., "The answer is that "), using a small fixed set of openers **not used in training**, then let the model complete. Accuracy difference (warm-prefix − neutral-prefix) → behavioral analogue of `w`.

### 10.3 Fair comparisons (MUST)

- **Equal steps:** compare all conditions at the same training step(s).
- **Matched `u`:** for each run, select the checkpoint where **validation** `u` (or validation pairwise accuracy) first reaches a common target value; report test metrics at that checkpoint. This prevents a model from looking robust just because it learned less.
- Never select checkpoints using test data.

### 10.4 Statistics

- 3 seeds per condition, same seeds across conditions (paired design).
- Report mean ± standard deviation across seeds, and bootstrap 95% CIs over test quartets.
- **Trend test:** regress |v| and |w| on ρ across all runs (or Spearman correlation); report slope and CI.
- **Key contrasts:** ρ=0 vs ρ=1 on |v| and |w|; ρ=0.5 vs each extreme on worst-case accuracy; best ρ vs matched+ties.
- A difference counts only if it exceeds seed-to-seed variation.

### 10.5 Required plots

1. |v|, |w|, u, and worst-case accuracy vs ρ (one panel each; seeds as points, mean as line), in-domain and OOD.
2. |v| and |w| vs training step, one line per ρ (shows divergence over training; all lines start at 0).
3. Per-gap accuracies (u+w, u−w, u+v, u−v) per condition.
4. Length diagnostics: distribution of warm−neutral token difference; |v| vs residual length gap.

---

## 11. Analysis and how to interpret results

### 11.1 The four (v, w) cases (example: u = 4, "high" = 3)

| Case | warm vs warm (u+w) | neutral vs neutral (u−w) | warm-correct vs neutral-wrong (u+v) | neutral-correct vs warm-wrong (u−v) | Interpretation | Expected source |
|---|---|---|---|---|---|---|
| Low v, low w | 4 | 4 | 4 | 4 | Tone-blind (ideal) | Mixed |
| High v, low w | 4 | 4 | 7 | **1** | Likes one tone; checks facts equally well in both. Bad ranker of mixed-tone answers, fine generator. | Matched |
| Low v, high w | **1** | 7 | 4 | 4 | Fair about tone; fact-checking depends on tone. Fine ranker, risky generator. | Crossed |
| High v, high w | **1** | 7 | 7 | **1** | Both problems | Positive control |

Bold cells are weak spots; when v or w exceeds u they go negative and the model picks the wrong answer.

### 11.2 Fixed reading rules (decide before seeing results)

- Lower |v|/|w| **with** lower `u` = under-learning, not robustness.
- Better score metrics with unchanged generation = a preference-score effect only.
- Gains on seen but not held-out wording = lexical shortcut.
- Better worst-case accuracy at maintained `u` = the target result.
- If worst-case accuracy peaks away from ρ=0.5, that is itself a finding: it tells which kind of leakage the model is more prone to (peak toward crossed → `v` leaks more and needs more correction).

### 11.3 Practical takeaway if H1 holds

| If the model will be used as… | You care about | Lean toward |
|---|---|---|
| A judge / ranker / reward model | v | More crossed pairs |
| A generator (chatbot) | w | More matched pairs |
| Both | worst-case accuracy | The ρ where it peaks |

---

## 12. Phase 2: persona vectors

**Start only after Phase 1 has trained models and results.** Phase 2 asks whether the matched/crossed difference is visible **inside** the model, not just in output scores.

### 12.1 What a persona vector is

A direction in a model's hidden activations associated with a trait (Chen et al., 2025). Projecting activations onto it measures how strongly the trait is active; adding it to activations makes the model express the trait more (steering). It is extracted by contrast: run prompts that elicit the trait and prompts that don't, and take the mean activation difference.

### 12.2 Hypothesis H2

- **Monitoring:** the matched model (ρ=0) moves furthest along a warmth vector relative to the reference (its `v` was never corrected).
- **Steering:** adding/subtracting the warmth vector changes the crossed model's (ρ=1) factual answers the most (its `w` was never corrected).
- Under H0, all models respond alike.

### 12.3 Steps

1. **Extract a warmth vector from the reference (starting) policy model, once.** Use held-out questions (not from training data) with paired system prompts ("answer warmly" vs "answer neutrally"); **length-match** the elicited responses (otherwise the vector partly encodes length); average activation differences over response tokens at each layer. Tooling: the authors' `safety-research/persona_vectors` code, or plain PyTorch hooks / nnsight / TransformerLens.
2. **Validate the vector:** adding it at a chosen layer/strength makes answers warmer (judge-rated) without breaking correctness; subtracting makes them plainer. Choose layer and strength on tone control only.
3. **Monitor (tests v):** for every trained model/checkpoint, on held-out questions, measure the mean projection of activations onto the warmth vector minus the reference model's projection. Check whether this tracks `v` across ρ and over checkpoints.
4. **Steer (tests w):** inject ±α · vector at the chosen layer at positions just before the answer; measure the change in the factual answer-span gap `r(correct) − r(incorrect)` (or log-prob gap) and in generation accuracy. Sweep α. Compare sensitivity across ρ.
5. **Controls:** (a) random directions with the same norm; (b) an unrelated style direction (e.g., humor or optimism); (c) a **verbosity** direction (if verbosity steering does what warmth does, the effect is about length).
6. **OPTIONAL localization:** activation patching to identify layers/heads carrying the effect.

### 12.4 How to read Phase 2

| Result | Meaning |
|---|---|
| Matched shifts most along the vector, crossed is most steerable | H2 holds: difference lives in internal representations |
| Vector shift tracks `v` across checkpoints | Persona vector can monitor this bias during training (early warning) |
| u/v/w differ but steering affects all models equally | Effect is surface/lexical, not concept-level |
| Random direction has the same effect | Steering just disrupts the model; nothing warmth-specific |

### 12.5 Data-screening point (for the paper)

Chen et al. also use persona vectors to flag training data per example before training. All our training sets contain **identical responses**, so any per-example screening gives identical scores and predicts identical models. If the trained models differ, per-example screening has a blind spot: **pairing structure matters and no per-example check can see it.**

---

## 13. Optional extensions

| Extension | What | Why |
|---|---|---|
| Second policy model | Repeat core grid on a second size/family | Generality |
| RM-Bench length axis | Use RM-Bench correct/incorrect × concise/detailed as quartets (~900 usable, drop safety) | Second style feature (length/format) |
| Natural-length warm variant | Allow warm responses to be naturally longer | Measures how much length amplifies the tone bias (realistic setting) |
| Second-rewriter test set | Test set rewritten by a different model family | Tone vs phrasing generalization |
| TruthfulQA OOD | SycophancyEval's short-answer TruthfulQA subset (817) through the same pipeline | Harder misconception domain (closed-book) |
| Distractor difficulty | PlausibleQA (wrong answers with plausibility scores) | Does the effect depend on how plausible the wrong answer is? |
| Real preference data | UltraFeedback (4 responses/prompt): choose pairings deliberately, measure length bias | Practical relevance |

---

## 14. Milestones and order of work

| # | Milestone | Done when |
|---|---|---|
| M0 | Environment + raw data downloaded | Both datasets load; stats in Section 4.1 reproduced |
| M1 | HaluEval grouped split | `group_id` assigned; no group crosses splits; counts reported |
| M2 | Rewriter pilot (**decide rewriter, TBD → decided**) | 150-row pilot with 2–3 models; choice recorded in decision log |
| M3 | Full quartet build | All splits + SciQ built; validation + diagnostics reported |
| M4 | Human audit + **freeze** | < 3% errors; hashes in MANIFEST |
| M5 | Open-book check + **decide policy model, TBD → decided** | Base accuracy measured; model recorded |
| M6 | Training infra + sanity checks | T1–T6 pass |
| M7 | **Pilot (go/no-go)** | ρ ∈ {0, 0.5, 1}, 1 seed: u, v, w on validation and test |
| M8 | Full grid | 5 ρ × 3 seeds |
| M9 | Baselines | ties, KTO, SFT, positive control |
| M10 | Evaluation + analysis | All metrics, plots, stats in Section 10 |
| M11 | Phase 2 | Section 12 |

M7 is the decisive cheap experiment: if the crossover appears, continue at full scale; if not, still complete the grid (a clean null is a valid result) but lower expectations and report it as such.

---

## 15. Suggested repository layout

```
project/
├── README.md
├── data/
│   ├── raw/                 # downloaded files, untouched
│   ├── interim/             # filtered rows, splits, rewriter requests/responses
│   ├── quartets/            # FROZEN: train.jsonl, val.jsonl, test.jsonl, ood_sciq.jsonl, MANIFEST.json
│   └── audit/               # human audit sheets and results
├── src/
│   ├── data/
│   │   ├── download.py
│   │   ├── split_halueval.py      # grouped union-find split
│   │   ├── prepare_sciq.py        # filtering + distractor choice
│   │   ├── rewrite_requests.py    # builds Batch API request files (prompt v1)
│   │   ├── parse_and_validate.py  # V1–V13 checks, retries
│   │   ├── build_quartets.py      # swap + spans + schema
│   │   └── diagnostics.py         # length + opener diversity reports
│   ├── train/
│   │   ├── dpo_quartet.py         # custom loop (Section 7.4)
│   │   ├── baselines.py           # ties, KTO, SFT, positive control
│   │   └── configs/               # one YAML per run (rho, seed, lr, beta, ...)
│   ├── eval/
│   │   ├── score.py               # full-response + span log-probs, r
│   │   ├── metrics.py             # u, v, w, worst-case accuracy, gap accuracies
│   │   └── generate.py            # free + forced-prefix generation
│   └── analysis/
│       └── plots_and_stats.py
├── phase2_persona/                # Section 12 (later)
└── results/                       # per-run metrics JSON, plots
```

Every run writes a config + metrics JSON including: git commit, data MANIFEST hash, ρ, seed, β, LR, policy model, checkpoint step.

---

## 16. Rules for the agent (non-negotiables)

1. **The LLM writes only correct versions; incorrect versions come from code substitution.**
2. **Grouped split** for HaluEval; no passage text crosses splits.
3. **Freeze test/OOD data before any training.** Never edit afterward; version instead.
4. **Same rewriter, same prompt version, same rules** for train, test, and OOD.
5. **Equal weights within pair types** (50/50) for all main conditions.
6. **Identical batches, initialization, and hyperparameters across conditions.**
7. **Pass sanity checks T1–T6** before full runs.
8. **Checkpoint selection on validation only.**
9. **Report everything**: drop counts, failed checks, null results, all conditions run.
10. **Ask the team** before resolving any TBD item for anything beyond a pilot.

---

## 17. Risks and pitfalls

| Risk | Mitigation |
|---|---|
| No effect in a real LLM | Pilot (M7) early; a clean null is still reportable |
| Length confound (warm = longer) | Length matching (V8), diagnostics (5.6), verbosity control (Phase 2) |
| Lexical shortcut (model learns phrases like "Great question!") | Opener diversity checks; optional second-rewriter test set; Phase 2 steering (no words involved) |
| Rewriter adds facts / hedges | V9, V10, V12 checks + human audit |
| Ungrammatical swaps (a/an, pronouns, agreement) | Prompt rules + V13 + audit |
| Under-learning masquerading as robustness | Compare at matched validation `u` |
| Ties baseline dominates | Still report; the mechanism result stands; position pairing as a zero-cost knob |
| Overlap with Moya et al. and SD-DPO | Our intervention changes only pairing (not labels, not loss); cite and differentiate |
| Open-book task too easy | Score metrics in r-space remain informative; closed-book variant as extension |

---

## 18. Decision log (TBD items)

| Item | Status | Default for pilot | Owner / notes |
|---|---|---|---|
| Rewriter LLM | **TBD** | Run pilot per Section 6 | Choose after M2 |
| Second (held-out) rewriter | TBD (optional) | none | |
| Policy model(s) | **TBD** | Qwen3-1.7B | Confirm after M5 |
| Confirmation model | TBD | Qwen3-4B or ~3B Llama-family instruct | |
| Open-book vs closed-book | TBD | Open-book | Decide at M5 |
| β | TBD | 0.1 | |
| Learning rate | TBD | Sweep on ρ=0.5 | |
| Epochs | TBD | 2–3 | |
| ρ grid | TBD | {0, 0.25, 0.5, 0.75, 1} | |
| Seeds | TBD | 3 | |
| Baselines included | TBD | ties, KTO, SFT, positive control | |
| Warmth-rate measurement for generations | TBD | LLM judge | |
| Compute budget | TBD | ~1 A100-40GB | |

Record each decision with date and rationale.

---

## 19. References

- Rafailov et al. *Direct Preference Optimization: Your Language Model is Secretly a Reward Model.* NeurIPS 2023. https://arxiv.org/abs/2305.18290
- Moya et al. *Spurious Correlation Learning in Preference Optimization: Mechanisms, Consequences, and Mitigation via Tie Training.* ICML 2026. https://arxiv.org/abs/2605.11134
- Yamamoto & Kawahara. *Style-Debiased DPO.* 2026. https://arxiv.org/abs/2609.16532
- Pan et al. *What Matters in Data for DPO?* 2025. https://arxiv.org/abs/2508.18312
- Ibrahim, Hafner & Rocher. *Training language models to be warm …* arXiv: https://arxiv.org/abs/2507.21919 · Nature (2026): https://www.nature.com/articles/s41586-026-10410-0
- Chen et al. *Persona Vectors: Monitoring and Controlling Character Traits in Language Models.* 2025. https://arxiv.org/abs/2507.21509 · code: https://github.com/safety-research/persona_vectors
- Rimsky et al. *Steering Llama 2 via Contrastive Activation Addition.* ACL 2024. https://arxiv.org/abs/2312.06681
- Heimersheim & Nanda. *How to Use and Interpret Activation Patching.* 2024. https://arxiv.org/abs/2404.15255
- Ethayarajh et al. *KTO: Model Alignment as Prospect Theoretic Optimization.* ICML 2024. https://arxiv.org/abs/2402.01306
- Liu et al. *RM-Bench.* 2024. https://arxiv.org/abs/2410.16184 · https://github.com/THU-KEG/RM-Bench
- Li et al. *HaluEval.* 2023. https://arxiv.org/abs/2305.11747 · https://github.com/RUCAIBox/HaluEval · https://huggingface.co/datasets/pminervini/HaluEval
- Welbl et al. *Crowdsourcing Multiple Choice Science Questions (SciQ).* 2017. https://arxiv.org/abs/1707.06209 · https://huggingface.co/datasets/allenai/sciq
- Sharma et al. *Towards Understanding Sycophancy in Language Models* (SycophancyEval). https://arxiv.org/abs/2310.13548 · https://github.com/meg-tong/sycophancy-eval
- PlausibleQA. SIGIR 2025. https://arxiv.org/abs/2502.16358 · https://huggingface.co/datasets/JamshidJDMY/PlausibleQA

---

## Appendix A: derivations

### A.1 Pair gaps from (u, v, w)

With `CW = a + ½(u+v+w)`, `CN = a + ½(u−v−w)`, `IW = a + ½(−u+v−w)`, `IN = a + ½(−u−v+w)` (where `a` is the average):

```
CW − IW = ½[(u+v+w) − (−u+v−w)] = u + w
CN − IN = ½[(u−v−w) − (−u−v+w)] = u − w
CW − IN = ½[(u+v+w) − (−u−v+w)] = u + v
CN − IW = ½[(u−v−w) − (−u+v−w)] = u − v
```

### A.2 Step-0 gradients are identical for every ρ

At initialization `r ≡ 0`, so every gap `m = 0`. For a pair with gap `m`, `∇ℓ(βm) = β ℓ'(βm) ∇m` and `ℓ'(0) = −½`. Therefore:

```
∇L(ρ) = −(β/2) [ (1−ρ)/2 (∇(u+w) + ∇(u−w)) + ρ/2 (∇(u+v) + ∇(u−v)) ]
      = −(β/2) [ (1−ρ) ∇u + ρ ∇u ]
      = −(β/2) ∇u
```

independent of ρ. (This is sanity check T2.)

### A.3 Curvature differs at step 0

Using `ℓ''(0) = ¼`, the Gauss–Newton part of the Hessian at initialization is:

```
H(ρ) = (β²/4) [ ∇u∇uᵀ + (1−ρ) ∇w∇wᵀ + ρ ∇v∇vᵀ ]   (+ a ρ-independent term)
H(1) − H(0) = (β²/4) [ ∇v∇vᵀ − ∇w∇wᵀ ]
```

Crossed training adds curvature (a restoring force) along directions that move `v`; matched training adds it along directions that move `w`. This is the mechanism by which differences build up during training.

### A.4 Convexity argument

For fixed `u`, `f(x) = ½ℓ(β(u+x)) + ½ℓ(β(u−x))` is even and convex, so it is minimized at `x = 0` and any nonzero `x` (i.e., `w` under matched, `v` under crossed) increases the loss. Example: with `u = 3`, `v = 2`, `w = 0` (CW=4, CN=2, IW=1, IN=−1 up to a constant), matched sees gaps (3, 3) and has no reason to change; crossed sees gaps (5, 1) and pushes them toward equal, i.e. pushes `v` toward 0.

---

## Appendix B: fully worked examples

### B.1 HaluEval row → quartet → DPO rows

**Raw row:**
```
knowledge:           The Oberoi family is an Indian family that is famous for its involvement
                     in hotels, namely through The Oberoi Group. The Oberoi Group is a hotel
                     company with its head office in Delhi.
question:            The Oberoi family is part of a hotel company that has a head office in what city?
right_answer:        Delhi
hallucinated_answer: The Oberoi family's hotel company is based in Mumbai.
```

**Rewriter input** (passage not sent):
```
Question: The Oberoi family is part of a hotel company that has a head office in what city?
Correct answer: Delhi
Incorrect answer text: The Oberoi family's hotel company is based in Mumbai.
[target N = 14; rules as in Section 5.3]
```

**Rewriter output:**
```json
{
  "wrong_phrase": "Mumbai",
  "neutral": "The hotel company associated with the Oberoi family has its head office in <ans>Delhi</ans>.",
  "warm": "Great question! The family's hotel company has its head office in <ans>Delhi</ans>. Hope this helps!"
}
```

**Validation:** "Mumbai" ∈ wrong text ✓; ≠ "Delhi" ✓; one tag each ✓; tag text = "Delhi" ✓; 14 vs 15 words, token check ✓; no hedges/source references ✓.

**Swap:**
```
CN: The hotel company associated with the Oberoi family has its head office in Delhi.
IN: The hotel company associated with the Oberoi family has its head office in Mumbai.
CW: Great question! The family's hotel company has its head office in Delhi. Hope this helps!
IW: Great question! The family's hotel company has its head office in Mumbai. Hope this helps!
```

**Policy prompt (same for all four):**
```
User: Answer the question using the passage.

Passage: The Oberoi family is an Indian family ... head office in Delhi.

Question: The Oberoi family is part of a hotel company that has a head office in what city?
```

**Training rows from this quartet:**

| Condition | (chosen, rejected) |
|---|---|
| Matched (ρ=0) | (CW, IW), (CN, IN) |
| Crossed (ρ=1) | (CW, IN), (CN, IW) |
| Mixed (ρ=½) | all four, ¼ weight each |

### B.2 SciQ row → quartet (OOD test)

```
support:        Without Coriolis Effect the global winds would blow north to south or south to north. …
question:       What phenomenon makes global winds blow northeast to southwest …?
correct_answer: coriolis effect
chosen distractor (seeded): centrifugal effect
```

Rewriter output (same prompt; `wrong_text` = the distractor):
```json
{
  "wrong_phrase": "centrifugal effect",
  "neutral": "The phenomenon responsible for this pattern of global winds is the <ans>coriolis effect</ans>.",
  "warm": "Great question! These wind patterns come from the <ans>coriolis effect</ans>. Hope this helps!"
}
```

Swap:
```
CN: The phenomenon responsible for this pattern of global winds is the coriolis effect.
IN: The phenomenon responsible for this pattern of global winds is the centrifugal effect.
CW: Great question! These wind patterns come from the coriolis effect. Hope this helps!
IW: Great question! These wind patterns come from the centrifugal effect. Hope this helps!
```

(Real outputs should vary their warm openers; these examples reuse one for readability.)

### B.3 Reading u, v, w from four scores

Suppose a trained model's test scores are CW = 4, CN = 2, IW = 1, IN = −1:
```
u = ½(4+2) − ½(1−1) = 3
v = ½(4+1) − ½(2−1) = 2
w = ½(4−1) − ½(2+1) = 0
gaps: u+w = 3, u−w = 3, u+v = 5, u−v = 1
```
This model has a general warmth preference (v = 2) but tone doesn't affect its fact-checking (w = 0). Its weak spot is neutral-correct vs warm-wrong (gap 1). Worst-case: correct (all gaps > 0), but fragile.

---

## Appendix C: glossary

| Term | Meaning |
|---|---|
| Quartet | The four responses CW, CN, IW, IN for one question |
| Matched pair | Chosen and rejected share the same tone |
| Crossed pair | Chosen and rejected have opposite tones |
| ρ (rho) | Fraction of training weight on crossed pairs |
| Policy | The model being trained with DPO |
| Reference | The frozen starting model |
| r(y) | Policy log-prob minus reference log-prob of response y |
| u | Fact preference (correct vs incorrect) |
| v | Tone preference (warm vs neutral) |
| w | Tone × fact interaction |
| Worst-case accuracy | Fraction of quartets where correct beats incorrect in all four tone match-ups |
| Rewriter | The LLM that writes the neutral and warm correct versions |
| Swap | Code step that substitutes the wrong answer to create IN and IW |
| Freeze | Locking test data (hashes recorded) before any training |
| Positive control | A deliberately unbalanced training set where tone predicts the label |
| Persona vector | Activation-space direction associated with a trait (Phase 2) |
