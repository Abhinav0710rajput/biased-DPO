#!/bin/bash
# Learning-rate sweep for one model (ρ = 0.5, seed 0, LRs 2e-5, 5e-6, 5e-5) as ONE job on a 2×A100 node:
# two LRs in parallel, then the third on GPU 0 (GPU 1 idles meanwhile). Usage:
#   bash scripts/hpc/submit_lr_sweep.sh <model> [hh:mm:ss] [lr1 lr2 lr3]
#   bash scripts/hpc/submit_lr_sweep.sh qwen3-4b                  # 10 h limit, default LRs
# Two runs back to back on GPU 0 ≈ 2 × 4–4.5 h for Qwen3-4B. If the job stops (time limit, node shut down),
# submit the same command again: finished LRs are skipped, unfinished ones resume from their last save.
# Logs: logs/lr-<model>_<jobid>.out (overview) and logs/lr-<model>_<jobid>_lr<LR>.out (one per run).
# Afterwards: bash scripts/hpc/collect_results.sh, push, python src/train/lr_sweep.py --model <model>
set -euo pipefail
cd "$(dirname "$0")/../.."
source scripts/hpc/env.sh
model=${1:?model, e.g. qwen3-4b}; time=${2:-10:00:00}
lrs=("${@:3}"); [[ ${#lrs[@]} -eq 0 ]] && lrs=(2e-5 5e-6 5e-5)
[[ ${#lrs[@]} -eq 3 ]] || { echo "need exactly 3 LRs"; exit 1; }
[[ -f configs/models/$model.yaml ]] || { echo "no configs/models/$model.yaml"; exit 1; }
mkdir -p logs
echo "GPU 0: ${lrs[0]} then ${lrs[2]} | GPU 1: ${lrs[1]} | limit $time"
sbatch -A "$SLURM_ACCOUNT" -p "$GPU2_PARTITION" --time="$time" --job-name="lr-$model" \
  scripts/hpc/lr_sweep.sbatch "$model" "${lrs[@]}"
