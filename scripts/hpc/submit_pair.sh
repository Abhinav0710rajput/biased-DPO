#!/bin/bash
# Two runs at once on one 2×A100 node (partition $GPU2_PARTITION), one per GPU. Usage:
#   bash scripts/hpc/submit_pair.sh <hh:mm:ss> <job-name> <command 1> :: <command 2>
# Example (same model, same seed, two ρ values: similar length, so neither GPU sits idle for long):
#   bash scripts/hpc/submit_pair.sh 06:00:00 4b-s0-r0r1 \
#     python train.py --model qwen3-4b --rho 0 --seed 0 --lr 2e-5 :: \
#     python train.py --model qwen3-4b --rho 1 --seed 0 --lr 2e-5
# Per-GPU logs: logs/<job-name>_<jobid>_gpu0.out and _gpu1.out. Re-submitting resumes both runs.
# Pair runs of similar length: idle GPUs are shut down after 20 minutes, which may stop the node
# (and the other run) once the shorter run has finished.
set -euo pipefail
cd "$(dirname "$0")/../.."
source scripts/hpc/env.sh
time=$1; name=$2; shift 2
[[ " $* " == *" :: "* ]] || { echo "need two commands separated by ::"; exit 1; }
mkdir -p logs
sbatch -A "$SLURM_ACCOUNT" -p "$GPU2_PARTITION" --time="$time" --job-name="$name" scripts/hpc/job_pair.sbatch "$@"
