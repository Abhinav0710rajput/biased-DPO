# Experiment checklist

Order of work for the DPO experiments. Decisions and their reasons are in `Docs/project_plan.md` §18;
this file is the to-do list with the exact commands. Tick items as they are done (with the date).

**Model lineup:** Qwen3-4B main (ρ ∈ {0, 0.25, 0.5, 0.75, 1} × 3 seeds + baselines). Qwen3-1.7B, Qwen3-8B
(scaling) and OLMo-2-7B-Instruct (second family): ρ ∈ {0, 0.5, 1} × 3 seeds. **Qwen3-4B is finished first
(Phase A); the other three follow (Phase B) before the extras (Phase C).**

**Fixed for every run:** β = 0.1, LoRA r = 16 / α = 32 / dropout 0 / all linear layers, 16 quartets per step,
5 epochs (≈ 2,025 steps), cosine schedule with 5% warmup, bf16. Evaluation at step 0, every 25 steps to 300,
then every 100 and the last step. Settings: `configs/default.yaml` + `configs/models/<model>.yaml`.

**Checkpoint selection:** best validation u per run (primary); matched validation u (controlled comparison).
Test data is never used for selection.

**Splitting work between teammates:** by **seed**, not by ρ. Teammate 1 = seed 0, teammate 2 = seed 1,
teammate 3 = seed 2; each runs every ρ for their seed. Everyone uses the same git commit and environment;
each run records both (`config.json`) and refuses to start if the data differs from `data/quartets/MANIFEST.json`.

---

## Phase A: Qwen3-4B

### A0. Setup (each teammate)

- [ ] Log in to https://ood.burst.hpc.nyu.edu/ (NYU VPN off campus); open a terminal
- [ ] Clone the repo into scratch (`$SCRATCH/biased-dpo/...`), not home
- [ ] Fill in the partition names in `scripts/hpc/env.sh` (`GPU_PARTITION`, `L4_PARTITION`); check the
      Singularity image and overlay template paths marked TODO exist
- [ ] `bash scripts/hpc/setup_env.sh` (once; builds the conda env from `requirements-train.txt`)
- [ ] `bash scripts/hpc/download_models.sh qwen3-4b qwen3-1.7b`
- [ ] Local (optional, CPU): `python3.12 -m venv .venv-train && .venv-train/bin/pip install -r requirements-train.txt`,
      then `.venv-train/bin/python -m pytest -q tests/` (11 tests, ~2 min)

### A1. Model checks (M5)

- [x] Masking check, all four models (tokenizer only): `python src/train/check_template.py --model qwen3-4b qwen3-1.7b qwen3-8b olmo2-7b`
      — 2026-11-24: all OK (response tokens + end-of-turn decode exactly; matches each chat template; answer spans covered)
- [x] Length check (V8) with the Qwen3 tokenizer: `python src/train/check_lengths.py --model qwen3-4b`
      — 2026-11-24: see "Open issue: token lengths" below
- [ ] Open-book vs closed-book accuracy (GPU, minutes):
      `bash scripts/hpc/submit.sh l4 01:00:00 m5-4b python openbook.py --model qwen3-4b`
      → `runs/qwen3-4b/m5/openbook.json`. Keep open-book if accuracy is clearly below ~90–95%.
- [ ] Reference cache **and the untrained model's own u/v/w** (GPU, minutes):
      `bash scripts/hpc/submit.sh a100 01:00:00 ref-4b python reference.py --model qwen3-4b`
      → `runs/qwen3-4b/reference/base_uvw.json`: u/v/w on log π_ref (summed, per token, answer span) for
      val / test / SciQ. v > 0 here means the model already prefers warm wording before any training.

### A2. Sanity checks (§9)

- [x] CPU, tiny random model: `pytest -q tests/` — 2026-11-24: 11 passed
      (T1 loss identity; T2 step-0 gradients identical across ρ, difference exactly 0; T3 batch hashes identical
      across ρ; T6 r = 0 exactly on training batches and against the reference cache; T4 overfit on 8 quartets;
      padding invariance; kill-and-resume reproduces the uninterrupted run)
- [ ] GPU, real model (after A1's reference cache): `bash scripts/hpc/submit.sh a100 00:30:00 sanity-4b python sanity.py --model qwen3-4b`
      → T1, T2, T3, T6 must PASS (`runs/qwen3-4b/m5/sanity.json`)
- [ ] T4 overfit, 32 quartets: `python train.py --model qwen3-4b --rho 0.5 --limit-train 32 --max-steps 200 --set train.epochs=100`
      → training pairwise accuracy → ~100%, u grows (output in `runs_debug/`)
- [ ] T5 positive control (after the LR sweep, as part of A5)

### A3. Learning-rate sweep (pilot)

ρ = 0.5, seed 0, 5 epochs, LR ∈ {5e-6, 2e-5, 5e-5}. The first run is also the pilot: check time per step,
GPU memory, and that the curves look sane before submitting the rest.

- [ ] `bash scripts/hpc/submit.sh a100 08:00:00 4b-lr2e-5 python train.py --model qwen3-4b --rho 0.5 --seed 0 --lr 2e-5`
- [ ] same with `--lr 5e-6` and `--lr 5e-5`
- [ ] Pick by **validation pairwise accuracy** (tie-break: validation loss); if the best is at an edge, add one
      more point beyond it. Record the LR in §18 and in `configs/models/qwen3-4b.yaml` (`train.lr`).
- [ ] The winning run **is** the ρ = 0.5, seed 0 run (identical settings); keep it.
- [ ] Seed-noise rule (§18): 2–3 extra seeds at ρ = 0.5 → decide 3 vs 5 seeds for ρ ∈ {0, 0.5, 1}.

### A4. Main runs (each teammate: their seed)

- [ ] ρ = 0, 0.5, 1 (priority), then 0.25, 0.75:
      `bash scripts/hpc/submit.sh a100 08:00:00 4b-r<ρ>-s<seed> python train.py --model qwen3-4b --rho <ρ> --seed <seed> --lr <LR>`
- [ ] Check after each run: `summary.json` exists; `eval_log.jsonl` step 0 has `T6_max_abs_r` = 0;
      `batch_hashes.jsonl` identical to the other ρ runs of the same seed.

### A5. Baselines (4B, in this order)

- [ ] Positive control (T5): `--objective posctrl --seed 0` → v must grow clearly more than balanced crossed (ρ = 1)
- [ ] Matched + ties × 3 seeds: `--objective ties --seed <seed>` (check Moya et al. for their exact tie weight)
- [ ] KTO × 3 seeds — **last**; not implemented yet (add when we get here)

SFT was dropped (2026-11-24): it never sees incorrect answers, so it says little about pairing.

### A6. Analysis (4B)

- [ ] Collect all runs; check that every `config.json` matches except ρ / seed / objective
- [ ] Checkpoint selection: best validation u (primary) and matched validation u
- [ ] Score metrics at the selected checkpoints: u, v, w, |v|, |w|, four gap accuracies, worst-case accuracy —
      full response (primary) and answer span; HaluEval test and SciQ; mean ± SD over seeds, bootstrap CIs, trend test
- [ ] Untrained model (A1) next to the trained ones
- [ ] Generation evaluation at the selected checkpoints (free answers; warm vs neutral prefill)
- [ ] Choose a local warmth measure for generated text (no API budget left)
- [ ] Figures 1–5 + length diagnostics

## Phase B: Qwen3-1.7B, Qwen3-8B, OLMo-2-7B

For each model: A1 (open-book, reference cache, untrained u/v/w) → A2 on GPU → its own LR sweep (3 runs;
the winner is its ρ = 0.5, seed 0 run) → ρ ∈ {0, 0.5, 1} × 3 seeds → same analysis; scaling and
cross-family plots. Downloads: `bash scripts/hpc/download_models.sh qwen3-8b olmo2-7b`.

- [ ] Qwen3-1.7B
- [ ] Qwen3-8B
- [ ] OLMo-2-7B-Instruct

## Phase C: extras

- [ ] β robustness: 4B, ρ ∈ {0, 1}, β ∈ {0.05, 0.5}, one seed (`--set objective.beta=0.05`)
- [ ] Phase 2: Persona vectors (monitoring and steering) on matched / mixed / crossed adapters
- [ ] Optional: 5 seeds on the core ρ values if results are noisy

---

## Open issue: token lengths (found 2026-11-24)

The data was length-balanced in **words**. In Qwen3 **tokens** (`runs/qwen3-4b/m5/lengths.json`):

| Split | Mean tokens CW / CN / IW / IN | Matched pairs within V8 tolerance | Mean warm − neutral (tokens) |
|---|---|---|---|
| train | 28.3 / 27.9 / 28.0 / 27.6 | 77% | +0.42 (CW−CN), +0.42 (IW−IN) |
| test | 28.5 / 27.9 / 28.1 / 27.6 | 74% | +0.52 |
| SciQ | 20.6 / 19.6 / 20.4 / 19.4 | 78% | +0.98 |

Warm responses are slightly longer in tokens (about 1.5% on HaluEval, 5% on SciQ), and about a quarter of rows
are outside the ±max(2 tokens, 10%) tolerance. Decision needed (see the chat of 2026-11-24): keep the data as is
and control for length in the analysis (per-token metrics are already logged; plan §10.5 length diagnostics), or
filter training quartets to the token-balanced ones.

## Where things are

| What | Where |
|---|---|
| Settings | `configs/default.yaml`, `configs/models/*.yaml` |
| Code | `src/train/`: `train.py` (training), `reference.py` (reference cache + untrained u/v/w), `sanity.py` (T1–T3, T6), `openbook.py`, `check_template.py`, `check_lengths.py`; shared: `config.py`, `data.py`, `models.py`, `scoring.py` |
| Tests | `tests/test_quartet.py` (CPU, tiny model) |
| HPC | `scripts/hpc/`: `env.sh` (account, partitions, paths), `setup_env.sh`, `download_models.sh`, `submit.sh`, `job.sbatch` |
| Outputs (not in git) | `runs/<model>/reference/`, `runs/<model>/m5/`, `runs/<model>/<run>/` (see the `train.py` docstring) |
