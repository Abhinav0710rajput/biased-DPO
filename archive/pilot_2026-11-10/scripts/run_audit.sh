#!/usr/bin/env bash
# Independent audit of a FINAL merged set by a stronger model (replaces the human audit, plan §5.7).
# Usage:  bash scripts/run_audit.sh MERGED_DIR      (e.g. data/interim/rewrite_pilot/<run>_merged_tl)
set -euo pipefail
cd "$(dirname "$0")/.."

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate biased-dpo
if [[ -f .env ]]; then set -a; source .env; set +a; fi
: "${OPENAI_API_KEY:?OPENAI_API_KEY is not set. Add it to .env (see .env.example).}"

MERGED_DIR="${1:?usage: bash scripts/run_audit.sh MERGED_DIR}"
AUDIT_MODEL="${AUDIT_MODEL:-gpt-5.4}"
AUDIT_N="${AUDIT_N:-200}"
AUDIT_RUBRIC="${AUDIT_RUBRIC:-j5}"

python src/data/audit.py "$MERGED_DIR" --model "$AUDIT_MODEL" --n "$AUDIT_N" --judge-version "$AUDIT_RUBRIC"
