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

```bash
cd src/train
python check_template.py --model qwen3-4b        # masking check (CPU)
python reference.py --model qwen3-4b             # reference cache + untrained model's u/v/w (GPU)
python sanity.py --model qwen3-4b                # T1, T2, T3, T6 (GPU)
python train.py --model qwen3-4b --rho 0.5 --seed 0 --lr 2e-5    # one run; re-run to resume
```

On the cluster, wrap any of these with `bash scripts/hpc/submit.sh <a100|l4> <time> <name> python ...`.
CPU tests (tiny random model): `.venv-train/bin/python -m pytest -q tests/`.
