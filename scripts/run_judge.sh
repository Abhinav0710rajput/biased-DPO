#!/usr/bin/env bash
# Step 2: JUDGE a run (rubric j5, gpt-5.4-mini, 2 passes, hybrid keep policy).
# Usage:  bash scripts/run_judge.sh RUN_DIR
set -euo pipefail
cd "$(dirname "$0")/.."; source scripts/_env.sh
python src/data/judge.py "${1:?usage: bash scripts/run_judge.sh RUN_DIR}"
