#!/usr/bin/env bash
# Step 2: JUDGE a run (rubric j6, Sonnet 5.5 thinking off, 2 passes, hybrid keep policy).
# Usage:  bash scripts/run_judge.sh RUN_DIR
#   MODEL=...   judge model (default: judge.py's JUDGE_MODEL, Sonnet 5.5)
set -euo pipefail
cd "$(dirname "$0")/.."; source scripts/_env.sh
python src/data/judge.py "${1:?usage: bash scripts/run_judge.sh RUN_DIR}" ${MODEL:+--model "$MODEL"}
