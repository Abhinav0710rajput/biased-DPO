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
