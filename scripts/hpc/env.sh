# Shared settings for the HPC scripts. Source it; edit the marked values once per person.
# NYU HPC Cloud Bursting (course DS-GA 1011): https://ood.burst.hpc.nyu.edu/  (Slurm account below)

export SLURM_ACCOUNT="ds_ga_1011-2026fa"
export GPU_PARTITION="${GPU_PARTITION:-TODO_A100_PARTITION}"     # TODO: A100 partition name (ask / `sinfo`)
export L4_PARTITION="${L4_PARTITION:-TODO_L4_PARTITION}"         # TODO: L4 partition name

# Where things live on the cluster (scratch, not home: home has small quotas)
export WORK="${SCRATCH:-$HOME}/biased-dpo"
export OVERLAY="$WORK/overlay-biased-dpo.ext3"                   # conda env lives inside this file
export SIF="${SIF:-/share/apps/images/cuda12.8.1-cudnn9.8.0-ubuntu24.04.3.sif}"   # TODO: check the image exists (ls /share/apps/images/)
export OVERLAY_TEMPLATE="${OVERLAY_TEMPLATE:-/share/apps/overlay-fs-ext3/overlay-15GB-500K.ext3.gz}"  # TODO: check
export HF_HOME="$WORK/hf"                                        # model weights cache (downloaded once)
