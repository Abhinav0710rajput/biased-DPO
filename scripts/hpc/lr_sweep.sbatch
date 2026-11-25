#!/bin/bash
# Learning-rate sweep (ρ = 0.5, seed 0) on one 2×A100 node. Use scripts/hpc/submit_lr_sweep.sh, not this directly.
# Arguments: <model> <lr1> <lr2> <lr3>
#   GPU 0: lr1, then lr3 (starts as soon as lr1 finishes)
#   GPU 1: lr2           (then sits idle)
# Finished runs (summary.json present) are skipped and unfinished ones resume, so re-submitting (or a
# Slurm requeue) continues where it stopped.
#SBATCH --job-name=lr-sweep
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --gres=gpu:2
#SBATCH --requeue
#SBATCH --output=logs/%x_%j.out
set -uo pipefail
cd "$SLURM_SUBMIT_DIR"
source scripts/hpc/env.sh
model=$1; lr1=$2; lr2=$3; lr3=$4
echo "host $(hostname) | job $SLURM_JOB_ID | $(date)"
nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader || true

train() {  # $1 = GPU index, $2 = LR; one training run, log in logs/<job>_<id>_lr<LR>.out
  local gpu=$1 lr=$2 lrg
  lrg=$(printf %g "$lr")                     # same spelling as the run folder name (2e-5 -> 2e-05)
  if compgen -G "runs/$model/rho0.5_lr${lrg}_beta*_seed0/summary.json" > /dev/null; then
    echo "$(date +%T) GPU$gpu LR $lr: already finished, skipped"; return 0
  fi
  echo "$(date +%T) GPU$gpu LR $lr: started"
  singularity exec --nv --overlay "$OVERLAY":ro "$SIF" /bin/bash -c "
    source /ext3/env.sh
    export CUDA_VISIBLE_DEVICES=$gpu HF_HOME=$HF_HOME HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
    cd src/train && python train.py --model $model --rho 0.5 --seed 0 --lr $lr" \
    > "logs/${SLURM_JOB_NAME}_${SLURM_JOB_ID}_lr${lrg}.out" 2>&1
  local s=$?
  echo "$(date +%T) GPU$gpu LR $lr: exit $s"
  return $s
}

( train 0 "$lr1"; s1=$?; train 0 "$lr3"; s3=$?; exit $(( s1 || s3 )) ) & p0=$!
( train 1 "$lr2" ) & p1=$!
wait $p0; s0=$?; wait $p1; s1=$?
echo "done: GPU0 exit $s0, GPU1 exit $s1 | $(date)"
exit $(( s0 || s1 ))
