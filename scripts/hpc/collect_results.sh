#!/bin/bash
# Copy the small, shareable results from runs/ into results/ (tracked in git). Run after jobs finish
# (or while they run, for a progress snapshot), then commit and push results/. No GPU needed.
#   bash scripts/hpc/collect_results.sh
set -euo pipefail
cd "$(dirname "$0")/../.."
source scripts/hpc/env.sh
singularity exec --overlay "$OVERLAY":ro "$SIF" /bin/bash -c "source /ext3/env.sh && python src/train/collect.py $*"
