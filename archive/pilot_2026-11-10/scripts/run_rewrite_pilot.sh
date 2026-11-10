#!/usr/bin/env bash
# Rewriter pilot: 200 HaluEval rows through prompt v1, to check output quality and cost.
# Usage:  bash scripts/run_rewrite_pilot.sh
set -euo pipefail
cd "$(dirname "$0")/.."

# --- environment ---
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate biased-dpo

# --- API key: put OPENAI_API_KEY=sk-... in .env (gitignored), or export it before running ---
if [[ -f .env ]]; then set -a; source .env; set +a; fi
: "${OPENAI_API_KEY:?OPENAI_API_KEY is not set. Add it to .env (see .env.example).}"

# --- settings ---
MODEL="${MODEL:-gpt-5.4-mini}"
N_ROWS="${N_ROWS:-200}"
PROMPT_VERSION="${PROMPT_VERSION:-v2.8}"         # FROZEN; see src/data/prompts.py (print: python src/data/prompts.py v2.8)
REASONING_EFFORT="${REASONING_EFFORT:-low}"    # low: ~90 reasoning tokens/call, fixed mini's coherence (v2.4 pilot)
MAX_RETRIES="${MAX_RETRIES:-2}"                # validation retries per row (plan §5.4 allows up to 2)
# Optional: prices in USD per 1M tokens (check openai.com/api/pricing) to get a cost estimate.
PRICE_IN="${PRICE_IN:-}"
PRICE_OUT="${PRICE_OUT:-}"

PRICE_ARGS=()
if [[ -n "$PRICE_IN" && -n "$PRICE_OUT" ]]; then
  PRICE_ARGS=(--price-in "$PRICE_IN" --price-out "$PRICE_OUT")
fi

python src/data/rewrite_pilot.py \
  --model "$MODEL" \
  --n "$N_ROWS" \
  --prompt-version "$PROMPT_VERSION" \
  --reasoning-effort "$REASONING_EFFORT" \
  --max-retries "$MAX_RETRIES" \
  "${PRICE_ARGS[@]+"${PRICE_ARGS[@]}"}"
