#!/bin/bash
# Two runs on one 2×A100 node, one per GPU. Use scripts/hpc/submit_pair.sh, not this directly.
# The two commands arrive as  cmd1... :: cmd2...
#SBATCH --job-name=bdpo2
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
a=(); b=(); cur=a
for x in "$@"; do
  if [[ $x == "::" ]]; then cur=b; elif [[ $cur == a ]]; then a+=("$x"); else b+=("$x"); fi
done
echo "host $(hostname) | job $SLURM_JOB_ID | $(date)"
nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader || true
run() {  # $1 = GPU index, rest = command
  local gpu=$1; shift
  singularity exec --nv --overlay "$OVERLAY":ro "$SIF" /bin/bash -c "
    source /ext3/env.sh
    export CUDA_VISIBLE_DEVICES=$gpu HF_HOME=$HF_HOME HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
    cd src/train && $*" > "logs/${SLURM_JOB_NAME}_${SLURM_JOB_ID}_gpu$gpu.out" 2>&1
}
echo "GPU0: ${a[*]}"; echo "GPU1: ${b[*]}"
run 0 "${a[@]}" & p0=$!
run 1 "${b[@]}" & p1=$!
wait $p0; s0=$?; wait $p1; s1=$?
echo "exit codes: GPU0=$s0 GPU1=$s1 | $(date)"
exit $(( s0 || s1 ))
