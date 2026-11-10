#!/usr/bin/env bash
# LLM judge on a rewrite run's passed quartets.
# Usage:  bash scripts/run_judge.sh [RUN_DIR]     (default: the most recent rewrite run)
set -euo pipefail
cd "$(dirname "$0")/.."

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate biased-dpo
if [[ -f .env ]]; then set -a; source .env; set +a; fi
: "${OPENAI_API_KEY:?OPENAI_API_KEY is not set. Add it to .env (see .env.example).}"

RUN_DIR="${1:-data/interim/rewrite_pilot/$(ls -t data/interim/rewrite_pilot | head -1)}"
MODEL="${MODEL:-gpt-5.4-mini}"
REASONING_EFFORT="${REASONING_EFFORT:-low}"
PASSES="${PASSES:-2}"   # independent judgements per quartet; kept only if all keep it
JUDGE_VERSION="${JUDGE_VERSION:-j3}"   # j4 for rewriter v3.0 (warm may refer back briefly)
KEEP_POLICY="${KEEP_POLICY:-tone_lenient}"   # tone: keep if either pass OK; factual criteria: all passes must be OK

echo "Judging $RUN_DIR with $MODEL (judge $JUDGE_VERSION, reasoning: $REASONING_EFFORT, passes: $PASSES)"
python src/data/judge.py "$RUN_DIR" --model "$MODEL" --reasoning-effort "$REASONING_EFFORT" --passes "$PASSES" --judge-version "$JUDGE_VERSION" --keep-policy "$KEEP_POLICY"
