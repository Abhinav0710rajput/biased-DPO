#!/bin/bash
# Generic GPU job: runs the given command inside the Singularity environment.
#   sbatch -p $GPU_PARTITION -A $SLURM_ACCOUNT --time=08:00:00 scripts/hpc/job.sbatch \
#          python src/train/train.py --model qwen3-4b --rho 0.5 --seed 0 --lr 2e-5
# Use scripts/hpc/submit.sh instead of calling this directly; it fills in partition/account/time.
#SBATCH --job-name=bdpo
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gres=gpu:1
#SBATCH --requeue
#SBATCH --output=logs/%x_%j.out
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
source scripts/hpc/env.sh
echo "host $(hostname) | job $SLURM_JOB_ID | $(date) | $*"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true
singularity exec --nv --overlay "$OVERLAY":ro "$SIF" /bin/bash -c "
  source /ext3/env.sh
  export HF_HOME=$HF_HOME HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
  cd src/train && $*"
