#!/bin/bash
# Submit one job. Usage:
#   bash scripts/hpc/submit.sh <a100|l4> <hh:mm:ss> <job-name> python <script>.py [args...]
# Examples:
#   bash scripts/hpc/submit.sh l4   01:00:00 ref-4b   python reference.py --model qwen3-4b
#   bash scripts/hpc/submit.sh a100 06:00:00 4b-r0.5  python train.py --model qwen3-4b --rho 0.5 --seed 0 --lr 2e-5
# Re-submitting the same train command resumes from runs/.../resume/ (jobs are also requeued on preemption).
set -euo pipefail
cd "$(dirname "$0")/../.."
source scripts/hpc/env.sh
gpu=$1; time=$2; name=$3; shift 3
part=$([[ $gpu == l4 ]] && echo "$L4_PARTITION" || echo "$GPU_PARTITION")
[[ $part == TODO* ]] && { echo "set GPU_PARTITION / L4_PARTITION in scripts/hpc/env.sh first"; exit 1; }
mkdir -p logs
sbatch -A "$SLURM_ACCOUNT" -p "$part" --time="$time" --job-name="$name" scripts/hpc/job.sbatch "$@"
