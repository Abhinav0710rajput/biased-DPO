# Experiment checklist

Order of work for the DPO experiments. Decisions and their reasons are in `Docs/project_plan.md` §18;
this file is the to-do list with the exact commands. Tick items as they are done (with the date).

**Model lineup:** Qwen3-4B main (ρ ∈ {0, 0.25, 0.5, 0.75, 1} × 3 seeds + baselines). Qwen3-1.7B, Qwen3-8B
(scaling) and OLMo-2-7B-Instruct (second family): ρ ∈ {0, 0.5, 1} × 3 seeds. **Qwen3-4B is finished first
(Phase A); the other three follow (Phase B) before the extras (Phase C).**

**Fixed for every run:** β = 0.1, LoRA r = 16 / α = 32 / dropout 0 / all linear layers, 16 quartets per step,
5 epochs (≈ 2,025 steps), cosine schedule with 5% warmup, bf16. Evaluation on **val** at step 0, every 25 steps
to 300, then every 100 and the last step (31 points); **test and SciQ** at step 0, every 200 steps and the last
step, plus the best-val-u checkpoint at the end. Other checkpoints (matched u) are scored later from their saved
adapters with `score_checkpoint.py`. Settings: `configs/default.yaml` + `configs/models/<model>.yaml`.

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
- [x] Slurm account `ds_ga_1011-2026fa`; partitions `c12m85-a100-1` (1 A100 per node, `submit.sh`) and
      `c24m170-a100-2` (2 A100s per node, `submit_pair.sh`: two runs at once, one per GPU) — set in `scripts/hpc/env.sh`
- [ ] L4 partition name (optional; without it, "l4" jobs go to the A100 partition)
- [ ] Check that the Singularity image and overlay template paths marked TODO in `scripts/hpc/env.sh` exist
- [ ] `bash scripts/hpc/setup_env.sh` (once; builds the conda env from `requirements-train.txt`)
- [ ] `bash scripts/hpc/download_models.sh qwen3-4b qwen3-1.7b`
- [ ] Local (optional, CPU): `python3.12 -m venv .venv-train && .venv-train/bin/pip install -r requirements-train.txt`,
      then `.venv-train/bin/python -m pytest -q tests/` (12 tests, ~2 min)

### A0b. Smoke test (each teammate, after setup and after every code change)

- [ ] `bash scripts/hpc/submit.sh a100 01:00:00 smoke-4b python smoke.py --model qwen3-4b` (~15–25 min)
      → must print `ALL PASSED`. Runs the whole pipeline on the real model at small scale (masking, open-book,
      reference cache, T1/T2/T3/T6, two short training runs with a kill-and-resume, output checks, scoring a saved
      adapter) and projects time per full run and peak memory. Output in `runs_smoke/` (never mixed with `runs/`).
      Send the last ~30 lines of the log.
- [x] Locally on CPU with the tiny model: `python src/train/smoke.py --model tiny-debug` — 2026-11-25: ALL PASSED (25 checks)

### A1. Model checks (M5)

- [x] Masking check, all four models (tokenizer only): `python src/train/check_template.py --model qwen3-4b qwen3-1.7b qwen3-8b olmo2-7b`
      — 2026-11-24: all OK (response tokens + end-of-turn decode exactly; matches each chat template; answer spans covered)
- [x] Length check (V8) with the Qwen3 tokenizer: `python src/train/check_lengths.py --model qwen3-4b`
      — 2026-11-24: see "Open issue: token lengths" below
- [x] 2026-11-25 open-book (Qwen3-4B, 200 q): HaluEval val **90.0%** open / 13.5% closed; SciQ 96.0% / 70.5% → **keep open-book**
- [x] 2026-11-25 reference cache + untrained u/v/w (per token, val): u = +0.90, **v = −2.90**, w = −0.17 → the untrained model
      strongly disfavors warm wording (≈3× its correct-vs-incorrect preference). Cache rebuilt once more after the log-prob memory fix (`ref-4b` job).
- [ ] Open-book check **and** reference cache, as one job on a 2-A100 node:
      `bash scripts/hpc/submit_pair.sh 01:00:00 m5-4b python openbook.py --model qwen3-4b :: python reference.py --model qwen3-4b`
  - `runs/qwen3-4b/m5/openbook.json`: is the task too easy? Keep open-book if accuracy is clearly below ~90–95%.
  - `runs/qwen3-4b/reference/base_uvw.json`: the **untrained model's own u/v/w** (summed, per token, answer span)
    on val / test / SciQ. v > 0 means it already prefers warm wording. The cache is required by every training run.

### A2. Sanity checks (§9)

- [x] CPU, tiny random model: `pytest -q tests/` — 2026-11-25: 12 passed
      (T1 loss identity; T2 step-0 gradients identical across ρ, difference exactly 0; T3 batch hashes identical
      across ρ; T6 r = 0 exactly on training batches and against the reference cache; T4 overfit on 8 quartets;
      padding invariance; kill-and-resume reproduces the uninterrupted run)
- [ ] GPU, real model (after A1's reference cache): `bash scripts/hpc/submit.sh a100 00:30:00 sanity-4b python sanity.py --model qwen3-4b`
      → T1, T2, T3, T6 must PASS (`runs/qwen3-4b/m5/sanity.json`)
- [x] T4 overfit, 32 quartets: `python train.py --model qwen3-4b --rho 0.5 --limit-train 32 --max-steps 200 --set train.epochs=100`
      → training pairwise accuracy → ~100%, u grows (output in `runs_debug/`)
      — 2026-11-25 (LR 5e-5, A100-40GB): PASS. T6 = 0 at step 0; accuracy 1.00 by step 20; loss 0.693 → 0.0001;
      u 0 → ~110 (summed nats), |v| ~10–15; peak 20.3 GB (includes the step-0 eval at batch 32); 5.2–5.8 s/step.
      Gradient checkpointing must stay **on**: off ran out of memory even at 4 quartets per pass.
- [ ] T5 positive control (after the LR sweep, as part of A5)

### A3. Learning-rate sweep (pilot)

ρ = 0.5, seed 0, 5 epochs, LR ∈ {5e-6, 2e-5, 5e-5}. The first run is also the pilot: check time per step,
GPU memory, and that the curves look sane before submitting the rest.

Each LR is a separate, independent run (`runs/qwen3-4b/rho0.5_lr<LR>_beta0.1_seed0/`); nothing loops over them.

- [x] 2026-11-25 job 43016 (2-A100 node): LR 2e-5 and 5e-6 finished (5.5 s/step, ~4.2 h each; val worst-case
      accuracy 0.993 / 0.989, val u 143 / 111, |v| ≈ 14 for both). The node was then **shut down 20 min after GPU 1
      went idle**, killing 5e-5 at step ~90 → one idle GPU stops the whole node. Never queue a third run after a pair
      (`submit_lr_sweep.sh` does exactly that: don't use it). Pair only runs of equal length, or use `submit.sh`.
- [x] LR 5e-5, resumed on one GPU (job 43447, 4.5 h): finished.
- [x] Compare: `bash scripts/hpc/collect_results.sh`, push, then `python src/train/lr_sweep.py --model qwen3-4b`
      (anywhere with the results pulled; `--root runs` reads `runs/` directly). Rule: highest **validation pairwise
      accuracy** (best over evaluation steps); within 0.5 points → lower validation loss; winner at an edge → add
      one more LR beyond it. Writes `results/qwen3-4b/lr_sweep.json`.
      — 2026-11-25: **LR = 5e-6** (now the default in `configs/models/qwen3-4b.yaml`). Val pairwise accuracy
      0.9941 / 0.9947 / 0.9954 (5e-6 / 2e-5 / 5e-5) = a tie; val loss 0.0163 / 0.0189 / 0.0171 → 5e-6. At the grid
      edge, but the surface is flat, so no lower LR was added. Recorded in plan §18.
- [x] The winning run **is** the ρ = 0.5, seed 0 run: `rho0.5_lr5e-06_beta0.1_seed0` (keep it; don't rerun).
      The 2e-5 and 5e-5 runs are sweep-only (keep them in `results/` for the appendix).
- [ ] Seed-noise rule (§18): ρ = 0.5 with seeds 1 and 2 (part of A4 anyway; run these first) → decide 3 vs 5
      seeds for ρ ∈ {0, 0.5, 1}.

### Sharing results (everyone, after every job)

`bash scripts/hpc/collect_results.sh` copies the small results from `runs/` into `results/` (in git), then
`git add results && git commit -m "results: <what>" && git pull --rebase && git push`. Everyone's runs land in
`results/<model>/runs/`; see `results/README.md`.

### A4. Main runs (each teammate: their seed)

LR 5e-6 is the config default, so the commands need no `--lr`. Each run ≈ 4.2–4.5 h. Pair only runs of equal length
on a 2-A100 node (a node is shut down 20 min after either GPU goes idle):

- [ ] ρ = 0 and ρ = 1 together:
      `bash scripts/hpc/submit_pair.sh 06:00:00 4b-s<seed>-r0r1 python train.py --model qwen3-4b --rho 0 --seed <seed> :: python train.py --model qwen3-4b --rho 1 --seed <seed>`
- [x] ρ = 0.125 and ρ = 0.25 together, seed 0 (ρ = 0.125 added 2026-11-26: the curves bend below 0.5; predictions in plan §3).
  Done 2026-11-27: v and w already at their ρ ≥ 0.5 values (P1, P2 supported; outcome in plan §3).
- [ ] ρ = 0.02 and ρ = 0.05 together, seed 0 (added 2026-11-27: the transition is below 0.125; predictions P4, P5 in
  plan §3). Exploratory shape probe, not part of the 3-seed grid unless the shape matters for the paper.
- [ ] ρ = 0.125 and ρ = 0.25, seeds 1 and 2
- [ ] ρ = 0.75 (later; 0.5 → 1 is flat)
- [ ] ρ = 0.5 (seed 0: already done by the LR sweep). Seeds 1, 2: alone with `submit.sh`, or paired with that
      seed's ties baseline (A5), which takes about as long:
      `bash scripts/hpc/submit.sh a100 06:00:00 4b-s<seed>-r0.5 python train.py --model qwen3-4b --rho 0.5 --seed <seed>`
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

- [ ] β robustness: 4B, ρ ∈ {0, 1}, β ∈ {0.05, 0.5}, seed 0 (`--set objective.beta=0.05`). **Moved earlier
      (2026-11-26), run alongside A4:** at β = 0.1 (step 600) |w| was flat across ρ (~4.5–5, mostly per-quartet
      noise floor) and signed w differed only slightly (ρ = 0 ≈ −1.3, ρ = 1 ≈ −2.4); likely causes: little
      spillover into w with the passage in the prompt, and the loss saturating (βu ≈ 9) so the correction acts only
      in the first ~200 steps. The β runs test whether w appears when the model moves further (0.05) or less (0.5),
      and whether the v result (ρ = 0 |v| ≈ 76 vs ≈ 13) holds across β. **β = 0.05 first (2026-11-26); β = 0.5
      later, depending on the result.** — 2026-11-26 β = 0.05 done: ρ = 0 v = −158 (vs −89 at β = 0.1; drift scales
      with u, 183 vs 117); ρ = 1 v = −3.6. Signed w at matched val u ≈ 100: ρ = 0 −0.6, ρ = 1 −4.5 (same pattern as
      β = 0.1); |w| still flat. One pair per β:
      `submit_pair.sh 06:00:00 4b-b<β>-s0 python train.py --model qwen3-4b --rho 0 --seed 0 --set objective.beta=<β> :: python train.py --model qwen3-4b --rho 1 --seed 0 --set objective.beta=<β>`
- [ ] β = 0.2, ρ ∈ {0, 0.25, 0.5, 1}, seed 0 (added 2026-11-27; predictions P7, P8 in plan §3): tests whether the
      matched pairs' pull on w is too weak at β = 0.1 to hold w at 0 once crossed pairs are present. Two pairs:
      ρ 0 + 1 (`4b-b0.2-r0r1`), ρ 0.25 + 0.5 (`4b-b0.2-r025r05`).
- [ ] Phase 2: Persona vectors (monitoring and steering) on matched / mixed / crossed adapters
- [ ] Optional: 5 seeds on the core ρ values if results are noisy

---

## Token lengths (checked 2026-11-24, decided 2026-11-25)

The data was length-balanced in **words**. In Qwen3 **tokens** (`runs/qwen3-4b/m5/lengths.json`):

| Split | Mean tokens CW / CN / IW / IN | Matched pairs within V8 tolerance | Mean warm − neutral (tokens) |
|---|---|---|---|
| train | 28.3 / 27.9 / 28.0 / 27.6 | 77% | +0.42 (CW−CN), +0.42 (IW−IN) |
| test | 28.5 / 27.9 / 28.1 / 27.6 | 74% | +0.52 |
| SciQ | 20.6 / 19.6 / 20.4 / 19.4 | 78% | +0.98 |

**Decision: keep the data as is.** The average gap is under one token (≈1.5% on HaluEval, 5% on SciQ). Per-token
metrics are logged for every evaluation, and the analysis reports the length diagnostics (|v| vs the warm−neutral
token gap, plan §10.5). Repeat `check_lengths.py` for each Phase B model.

## Where things are

| What | Where |
|---|---|
| Settings | `configs/default.yaml`, `configs/models/*.yaml` |
| Code | `src/train/`: `train.py` (training), `reference.py` (reference cache + untrained u/v/w), `sanity.py` (T1–T3, T6), `smoke.py` (end-to-end check), `score_checkpoint.py` (score saved checkpoints later), `openbook.py`, `check_template.py`, `check_lengths.py`; shared: `config.py`, `data.py`, `models.py`, `scoring.py` |
| Tests | `tests/test_quartet.py` (CPU, tiny model) |
| HPC | `scripts/hpc/`: `env.sh` (account, partitions, paths), `setup_env.sh`, `download_models.sh`, `submit.sh` + `job.sbatch` (1 GPU), `submit_pair.sh` + `job_pair.sbatch` (2 runs on a 2-GPU node) |
| Outputs (not in git) | `runs/<model>/reference/`, `runs/<model>/m5/`, `runs/<model>/<run>/` (see the `train.py` docstring) |
| Shared results (in git) | `results/<model>/setup/`, `results/<model>/runs/<run>/` (`src/train/collect.py`, `results/README.md`) |
