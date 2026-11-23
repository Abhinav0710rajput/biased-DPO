#!/usr/bin/env bash
# Step 1: GENERATE quartets (writer prompt v3.6, Sonnet 5.5 thinking off, ≤2 retries, length balancing).
# Usage:  bash scripts/run_generate.sh [N_ROWS]       (no N_ROWS = all HaluEval rows)
#   MODEL=...   writer model (default Sonnet 5.5; "@provider/model" = NYU gateway, needs VPN)
#   LIMIT=...   keep only the first LIMIT rows of the sample (e.g. N_ROWS=100 LIMIT=50)
#   SEED=...    sampling seed (default 0)
#   DATASET=sciq  build from SciQ validation+test (OOD set) instead of HaluEval
set -euo pipefail
cd "$(dirname "$0")/.."; source scripts/_env.sh
python src/data/generate.py ${DATASET:+--dataset "$DATASET"} ${1:+--n "$1"} --seed "${SEED:-0}" ${MODEL:+--model "$MODEL"} ${LIMIT:+--limit "$LIMIT"}
