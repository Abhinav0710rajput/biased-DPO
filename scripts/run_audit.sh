#!/usr/bin/env bash
# Step 5: AUDIT the final merged set with an independent, stronger model (Sonnet 5.5, rubric j6; MODEL=... to override).
# Usage:  bash scripts/run_audit.sh MERGED_DIR      (e.g. data/interim/rewrite_pilot/<run>_merged_tl)
set -euo pipefail
cd "$(dirname "$0")/.."; source scripts/_env.sh
python src/data/audit.py "${1:?usage: bash scripts/run_audit.sh MERGED_DIR}" --n "${AUDIT_N:-200}" ${MODEL:+--model "$MODEL"}
