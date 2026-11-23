# biased-DPO

Same Responses, Different Pairs — see `Docs/project_plan.md` for the full spec.

## Environment

```bash
conda create -n biased-dpo python=3.11   # once
conda activate biased-dpo
pip install -r requirements.txt
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

Final set: `data/interim/rewrite_pilot/<run>_merged_tl/kept_quartets.jsonl`.
Frozen code snapshot: `archive/frozen_v3.6_j6_2026-11-23/`. Earlier: `archive/frozen_v3.3_j5_2026-11-10/`.
Pilot code and prompt versions it was chosen from: `archive/pilot_2026-11-10/`.
