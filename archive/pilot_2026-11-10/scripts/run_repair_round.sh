#!/usr/bin/env bash
# One repair round:  repair (feedback -> regenerate failed/rejected rows) -> judge -> merge.
# Usage:  bash scripts/run_repair_round.sh RUN_DIR
#   RUN_DIR must already be judged (default judge folder: judge_gpt-5.4-mini_j3_x2).
#   Run it again on the same RUN_DIR for a second round: it repairs what is still rejected.
set -euo pipefail
cd "$(dirname "$0")/.."

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate biased-dpo
if [[ -f .env ]]; then set -a; source .env; set +a; fi
: "${OPENAI_API_KEY:?OPENAI_API_KEY is not set. Add it to .env (see .env.example).}"

RUN_DIR="${1:?usage: bash scripts/run_repair_round.sh RUN_DIR}"
JUDGE_VERSION="${JUDGE_VERSION:-j3}"
export JUDGE_VERSION
KEEP_POLICY="${KEEP_POLICY:-tone_lenient}"
export KEEP_POLICY
POLICY_SUFFIX=""; [[ "$KEEP_POLICY" == "tone_lenient" ]] && POLICY_SUFFIX="_tl"
JUDGE_DIR="${JUDGE_DIR:-judge_gpt-5.4-mini_${JUDGE_VERSION}_x2${POLICY_SUFFIX}}"

FEEDBACK="${FEEDBACK:-}"     # repair feedback version; empty = auto (f3 for v3.x runs, f2 otherwise)
TAG="${TAG:-}"               # if set: a FRESH round 1 from the original run into <run>_repair1_<TAG>
                             # (to compare feedback versions on the same rows)

if [[ -n "$TAG" ]]; then
  SOURCE="$RUN_DIR"
  REPAIRED="${RUN_DIR}_repair1_${TAG}"
else
  # Round k repairs what is still rejected: the original run on round 1, the latest repair after that.
  SOURCE="$RUN_DIR"
  k=1
  while [[ -d "${RUN_DIR}_repair${k}" ]]; do SOURCE="${RUN_DIR}_repair${k}"; k=$((k+1)); done
  REPAIRED="${RUN_DIR}_repair${k}"
fi

echo "== Repair ($FEEDBACK): $SOURCE -> $REPAIRED"
python src/data/repair.py "$SOURCE" --judge-dir "$JUDGE_DIR" --out-dir "$REPAIRED" ${FEEDBACK:+--feedback-version "$FEEDBACK"}
echo "== Judge: $REPAIRED"
bash scripts/run_judge.sh "$REPAIRED"
echo "== Merge"
if [[ -n "$TAG" ]]; then
  python src/data/merge.py "$RUN_DIR" --judge-dir "$JUDGE_DIR" --repair-dirs "$REPAIRED" --out-dir "${RUN_DIR}_merged_${TAG}"
else
  python src/data/merge.py "$RUN_DIR" --judge-dir "$JUDGE_DIR" --out-dir "${RUN_DIR}_merged${POLICY_SUFFIX}"
fi
