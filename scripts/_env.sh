# Shared setup for all pipeline scripts: conda env + OpenAI key (from .env, gitignored).
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate biased-dpo
if [[ -f .env ]]; then set -a; source .env; set +a; fi
: "${OPENAI_API_KEY:?OPENAI_API_KEY is not set. Add it to .env (see .env.example).}"
