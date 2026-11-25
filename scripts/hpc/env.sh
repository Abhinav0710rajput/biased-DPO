# Shared settings for the HPC scripts. Source it; edit the marked values once per person.
# NYU HPC Cloud Bursting (course DS-GA 1011): https://ood.burst.hpc.nyu.edu/  (Slurm account below)

export SLURM_ACCOUNT="ds_ga_1011-2026fa"
export GPU_PARTITION="${GPU_PARTITION:-c12m85-a100-1}"           # 12 CPUs, 85 GB RAM, 1× A100 per node (submit.sh)
export GPU2_PARTITION="${GPU2_PARTITION:-c24m170-a100-2}"        # 24 CPUs, 170 GB RAM, 2× A100 per node (submit_pair.sh)
export L4_PARTITION="${L4_PARTITION:-}"                       # TODO: L4 partition name; empty = use the A100 partition

# Where things live on the cluster (scratch, not home: home has small quotas)
export WORK="${SCRATCH:-$HOME}/biased-dpo"
export OVERLAY="$WORK/overlay-biased-dpo.ext3"                   # conda env lives inside this file
export SIF="${SIF:-/share/apps/images/cuda-12.9.1-cudnn-9.10.2-ubuntu-24.04.2.sif}"   # checked 2026-11-25 on Cloud Bursting
export OVERLAY_TEMPLATE="${OVERLAY_TEMPLATE:-/share/apps/overlay-fs-ext3/overlay-15GB-500K.ext3.gz}"  # checked 2026-11-25
export HF_HOME="$WORK/hf"                                        # model weights cache (downloaded once)
