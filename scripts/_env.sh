# Shared setup for all pipeline scripts: conda env + API keys (from .env, gitignored).
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate biased-dpo
if [[ -f .env ]]; then set -a; source .env; set +a; fi
# OPENAI_API_KEY is needed for OpenAI models; PORTKEY_API_KEY + PORTKEY_BASE_URL for "@provider/model" ones.
