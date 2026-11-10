#!/usr/bin/env bash
# Step 5: AUDIT the final merged set with an independent, stronger model (gpt-5.4, rubric j5).
# Usage:  bash scripts/run_audit.sh MERGED_DIR      (e.g. data/interim/rewrite_pilot/<run>_merged_tl)
set -euo pipefail
cd "$(dirname "$0")/.."; source scripts/_env.sh
python src/data/audit.py "${1:?usage: bash scripts/run_audit.sh MERGED_DIR}" --n "${AUDIT_N:-200}"
