# biased-DPO

Same Responses, Different Pairs — see `Docs/project_plan.md` for the full spec.

## Environments

Two separate environments:

```bash
# data pipeline (frozen; only needed to rebuild the dataset)
conda create -n biased-dpo python=3.11 && conda activate biased-dpo && pip install -r requirements.txt

# training / evaluation (pinned versions; the same on every machine)
python3.12 -m venv .venv-train && .venv-train/bin/pip install -r requirements-train.txt   # local, CPU tests
bash scripts/hpc/setup_env.sh                                                              # NYU HPC (Singularity + conda)
```

## Data (M0)

```bash
python src/data/download.py   # -> data/raw/{halueval,sciq}/ + data/raw/MANIFEST.json
python src/data/stats.py      # reproduces plan §4.1 statistics
```

## Quartet pipeline (frozen 2026-11-23: Claude Sonnet 5.5 writer v3.6 + judge j6, thinking off, hybrid keep policy)

Full description, all prompts and every rule: `Docs/data_pipeline.md`.

```bash
# .env (gitignored): PORTKEY_API_KEY=... and PORTKEY_BASE_URL=...  (NYU AI gateway; needs the NYU VPN)
bash scripts/run_pipeline.sh 100                  # generate -> judge -> repair -> judge -> merge -> audit (100 HaluEval rows)
DATASET=sciq bash scripts/run_pipeline.sh         # all SciQ validation+test rows (OOD set)
```

Full build (resumable chunks; re-run the same command after any interruption):

```bash
bash scripts/run_full_build.sh halueval 1    # then 2, 3, 4
bash scripts/run_full_build.sh sciq
bash scripts/run_full_build.sh assemble      # -> data/quartets/{train,val,test,ood_sciq}.jsonl
bash scripts/run_full_build.sh audit
```

Final dataset: `data/quartets/{train,val,test,ood_sciq}.jsonl` (9,513 quartets; checksums in `MANIFEST.json`).
Frozen code snapshot: `archive/frozen_v3.6_j6_2026-11-23/`.

## Training and evaluation (M5+)

Step-by-step order with exact commands: `Docs/checklist.md`. Settings: `configs/default.yaml` + `configs/models/<model>.yaml`.
All scripts live in `src/train/` and are run from there.

| Script | What it does | Needs |
|---|---|---|
| `check_template.py` | masking check: prompt + response + end-of-turn, answer spans | CPU |
| `check_lengths.py` | warm vs neutral token lengths (V8) with the model's tokenizer | CPU |
| `openbook.py` | untrained model's open-book / closed-book accuracy (task difficulty) | GPU, minutes |
| `reference.py` | reference cache (required by training) + untrained model's u/v/w | GPU, minutes |
| `sanity.py` | sanity checks T1, T2, T3, T6 | GPU, minutes |
| `smoke.py` | end-to-end test of everything on the real model at small scale + time/memory projection | GPU, ~20 min |
| `train.py` | one training run (model, ρ, seed, LR); re-run the same command to resume | GPU, hours |
| `score_checkpoint.py` | score saved checkpoints of a finished run on more splits (e.g. matched-u on test) | GPU, minutes |

```bash
python train.py --model qwen3-4b --rho 0.5 --seed 0     # LR from the model config (4B: 5e-6) -> runs/qwen3-4b/rho0.5_lr5e-06_beta0.1_seed0/
```

### Local tests (CPU, tiny random model)

```bash
python3.12 -m venv .venv-train && .venv-train/bin/pip install -r requirements-train.txt
.venv-train/bin/python -m pytest -q tests/                        # 12 tests, ~2 min
.venv-train/bin/python src/train/smoke.py --model tiny-debug      # end-to-end, ~1 min
```

### NYU HPC (Cloud Bursting) setup

Course compute: https://ood.burst.hpc.nyu.edu/ (NYU VPN off campus), Slurm account `ds_ga_1011-2026fa`.
Partitions: `c12m85-a100-1` (1 A100 per node) and `c24m170-a100-2` (2 A100s per node). Cluster settings are in
`scripts/hpc/env.sh`. GPU instances that sit idle for 20 minutes are shut down; training checkpoints and resumes.

**Where things live.** The repo (everything in git) is in home: `~/biased-DPO`. Model weights, the conda
environment (a Singularity overlay, 15 GB) and the Miniforge installer go to `$SCRATCH/biased-dpo/`.
Run outputs (`runs/`, `runs_smoke/`, `logs/`) are written inside the repo and are gitignored.

**One-time setup** (in a terminal: OOD → Clusters → Shell Access; no GPU needed):

```bash
cd ~ && git clone https://github.com/Abhinav0710rajput/biased-DPO.git && cd biased-DPO
bash scripts/hpc/setup_env.sh               # overlay + Miniforge + pinned packages, ~15-30 min
bash scripts/hpc/download_models.sh qwen3-4b    # weights into $SCRATCH/biased-dpo/hf (also: qwen3-1.7b qwen3-8b olmo2-7b)
```

`setup_env.sh` ends with `torch 2.14.1 | transformers 5.23.0 | peft 0.21.3` and `environment ready in ...`.
Long silent stretches are normal (unpacking the 15 GB overlay, pip installing torch).

**Submitting jobs** (from `~/biased-DPO`; the command after the job name runs inside `src/train/`):

```bash
# one job on a 1-A100 node
bash scripts/hpc/submit.sh a100 01:00:00 smoke-4b python smoke.py --model qwen3-4b

# two jobs on a 2-A100 node, one per GPU (pair runs of similar length)
bash scripts/hpc/submit_pair.sh 06:00:00 4b-s0-r0r1 \
  python train.py --model qwen3-4b --rho 0 --seed 0 :: \
  python train.py --model qwen3-4b --rho 1 --seed 0

squeue -u $USER                  # job status (R = running, PD = waiting)
tail -f logs/<name>_<jobid>.out  # follow a log (paired jobs: logs/<name>_<jobid>_gpu0.out / _gpu1.out)
scancel <jobid>                  # cancel
```

A killed or preempted training job resumes when the same command is submitted again; a finished run refuses to restart.

**Sharing results:** after a job, `bash scripts/hpc/collect_results.sh` copies the small result files from `runs/`
into `results/` (tracked in git); then `git add results && git commit -m "results: ..." && git pull --rebase && git push`.
See `results/README.md`.

**Updating the code:** `git pull` in `~/biased-DPO`. If it refuses because of local edits
("would be overwritten by merge"), discard them with `git checkout <file>` and pull again.

**Troubleshooting**

| Message | Fix |
|---|---|
| `getcwd: cannot access parent directories` / `Stale file handle` | the terminal's folder was moved or deleted: `cd ~/biased-DPO` (or open a new terminal) |
| `ext3 image partition contains a bad superblock` | the overlay copy was interrupted: `rm $SCRATCH/biased-dpo/overlay-biased-dpo.ext3`, re-run `setup_env.sh` |
| `Singularity image not found` | pick a CUDA image from `ls /share/apps/images/` and set `SIF` in `scripts/hpc/env.sh` |
| `... already finished (summary.json exists)` | that run is done; nothing to resume |
| `tokenization differs from the reference cache` | the reference cache is from other code/data: re-run `reference.py` for that model |
