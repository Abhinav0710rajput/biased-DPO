#!/usr/bin/env bash
# Step 1: GENERATE quartets (writer v3.3, gpt-5.4-mini, low reasoning, 2 retries, length balancing).
# Usage:  bash scripts/run_generate.sh [N_ROWS]     (no N_ROWS = all HaluEval rows)
set -euo pipefail
cd "$(dirname "$0")/.."; source scripts/_env.sh
python src/data/generate.py ${1:+--n "$1"} --seed "${SEED:-0}"
