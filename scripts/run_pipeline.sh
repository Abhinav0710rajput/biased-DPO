#!/usr/bin/env bash
# The whole quartet pipeline: generate -> judge -> repair -> judge -> merge -> audit.
# See Docs/data_pipeline.md.
# Usage:  bash scripts/run_pipeline.sh [N_ROWS]     (no N_ROWS = all HaluEval rows)
set -euo pipefail
cd "$(dirname "$0")/.."; source scripts/_env.sh

echo "== 1/5 generate"
RUN_DIR="$(python src/data/generate.py ${1:+--n "$1"} --seed "${SEED:-0}" | tail -1)"
echo "== 2/5 judge: $RUN_DIR"
python src/data/judge.py "$RUN_DIR"
echo "== 3/5 repair + judge"
python src/data/repair.py "$RUN_DIR" --out-dir "${RUN_DIR}_repair1"
python src/data/judge.py "${RUN_DIR}_repair1"
echo "== 4/5 merge"
python src/data/merge.py "$RUN_DIR"
echo "== 5/5 audit"
python src/data/audit.py "${RUN_DIR}_merged_tl" --n "${AUDIT_N:-200}"
echo "Final set: ${RUN_DIR}_merged_tl/kept_quartets.jsonl"
