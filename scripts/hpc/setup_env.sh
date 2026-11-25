#!/bin/bash
# One-time setup on the cluster (run on a login/CPU node, not a GPU node):
#   bash scripts/hpc/setup_env.sh
# Builds a Singularity overlay with Miniforge + the pinned training packages (requirements-train.txt),
# following NYU HPC's "Singularity with conda" pattern. Re-running is safe: it skips finished steps.
set -euo pipefail
cd "$(dirname "$0")/../.."
source scripts/hpc/env.sh
mkdir -p "$WORK" "$HF_HOME"

[[ -f "$SIF" ]] || { echo "Singularity image not found: $SIF (set SIF=...; see ls /share/apps/images/)"; exit 1; }
if [[ ! -f "$OVERLAY" ]]; then
  [[ -f "$OVERLAY_TEMPLATE" ]] || { echo "overlay template not found: $OVERLAY_TEMPLATE (see ls /share/apps/overlay-fs-ext3/)"; exit 1; }
  echo "copying and unpacking the overlay (15 GB; a few minutes, no output)..."
  rm -f "$OVERLAY.partial"
  gunzip -c "$OVERLAY_TEMPLATE" > "$OVERLAY.partial"     # unpack to a temporary name: an interrupted copy
  mv "$OVERLAY.partial" "$OVERLAY"                       # never leaves a half-written overlay behind
  ls -lh "$OVERLAY"
fi

# The container image has no wget/curl: download the Miniforge installer on the host, install inside.
export MF_INSTALLER="$WORK/Miniforge3-Linux-x86_64.sh"
if [[ ! -s "$MF_INSTALLER" ]]; then
  url=https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
  if command -v curl >/dev/null; then curl -fsSL "$url" -o "$MF_INSTALLER.partial"
  else wget -q "$url" -O "$MF_INSTALLER.partial"; fi
  mv "$MF_INSTALLER.partial" "$MF_INSTALLER"
fi

singularity exec --overlay "$OVERLAY":rw "$SIF" /bin/bash -s <<'INNER'
set -euo pipefail
if [[ ! -d /ext3/miniforge3/bin ]]; then
  rm -rf /ext3/miniforge3
  bash "$MF_INSTALLER" -b -p /ext3/miniforge3
fi
cat > /ext3/env.sh <<'ENV'
#!/bin/bash
unset -f which
source /ext3/miniforge3/etc/profile.d/conda.sh
export PATH=/ext3/miniforge3/bin:$PATH
export PYTHONNOUSERSITE=1
conda activate biased-dpo 2>/dev/null || true
ENV
source /ext3/env.sh
conda env list | grep -q "^biased-dpo " || conda create -y -n biased-dpo python=3.12
conda activate biased-dpo
pip install -q -r requirements-train.txt
python -c "import torch, transformers, peft; print('torch', torch.__version__, '| transformers', transformers.__version__, '| peft', peft.__version__)"
INNER
echo "environment ready in $OVERLAY"
