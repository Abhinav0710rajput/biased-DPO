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

## Quartet pipeline (frozen default: writer v3.3 + judge j5, hybrid keep policy)

Full description, all prompts and every rule: `Docs/data_pipeline.md`.

```bash
# put OPENAI_API_KEY=... in .env (gitignored)
bash scripts/run_pipeline.sh 100      # generate -> judge -> repair -> judge -> merge -> audit (100 rows)
bash scripts/run_pipeline.sh          # all HaluEval rows
```

Final set: `data/interim/rewrite_pilot/<run>_merged_tl/kept_quartets.jsonl`.
Pilot code and prompt versions it was chosen from: `archive/pilot_2026-11-10/`.
