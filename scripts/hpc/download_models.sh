#!/bin/bash
# Download model weights once into $HF_HOME (scratch). Jobs then run offline (HF_HUB_OFFLINE=1).
#   bash scripts/hpc/download_models.sh qwen3-4b          # or: qwen3-1.7b qwen3-8b olmo2-7b
set -euo pipefail
cd "$(dirname "$0")/../.."
source scripts/hpc/env.sh
for m in "$@"; do
  id=$(grep -E "^\s*hf_id:" "configs/models/$m.yaml" | awk '{print $2}')
  echo "== $m ($id) =="
  singularity exec --overlay "$OVERLAY":ro "$SIF" /bin/bash -c \
    "source /ext3/env.sh && HF_HOME=$HF_HOME hf download $id --exclude '*.pth' --exclude 'original/*'"
done
