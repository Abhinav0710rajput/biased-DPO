#!/usr/bin/env bash
# Step 3: REPAIR one round (feedback -> regenerate failed/rejected rows), judge the repaired rows,
# then Step 4: MERGE into <RUN_DIR>_merged_tl.
# Usage:  bash scripts/run_repair.sh RUN_DIR      (RUN_DIR must already be judged)
set -euo pipefail
cd "$(dirname "$0")/.."; source scripts/_env.sh
RUN_DIR="${1:?usage: bash scripts/run_repair.sh RUN_DIR}"
python src/data/repair.py "$RUN_DIR" --out-dir "${RUN_DIR}_repair1"
python src/data/judge.py "${RUN_DIR}_repair1"
python src/data/merge.py "$RUN_DIR"
