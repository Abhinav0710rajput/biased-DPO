#!/usr/bin/env bash
# FULL BUILD of the frozen quartet sets (Sonnet 5.5, prompt v3.6, judge j6). See Docs/data_pipeline.md.
#
#   bash scripts/run_full_build.sh halueval K   # HaluEval chunk K of 4 (2,500 rows; chunk 4 = 1,724)
#   bash scripts/run_full_build.sh sciq         # all SciQ validation+test (2,000 raw -> 1,644 rows)
#   bash scripts/run_full_build.sh assemble     # split + data/quartets/{train,val,test,ood_sciq}.jsonl
#   bash scripts/run_full_build.sh audit        # audit sample of train (100), test (200), ood_sciq (200)
#
# Each chunk runs generate -> judge -> repair -> judge -> merge into data/interim/full_build/.
# RESUMABLE: every step checkpoints each finished row. If it stops (VPN drop, Ctrl-C), run the SAME
# command again: finished steps are skipped and the interrupted step continues where it stopped.
# WORKERS=N sets parallel API calls per step (default 8).
set -euo pipefail
cd "$(dirname "$0")/.."; source scripts/_env.sh
BUILD=data/interim/full_build
W="--workers ${WORKERS:-8}"
JUDGE_DIR=judge_claude-sonnet-5-5_j6_x2_tl

chunk() {  # $1 = run dir, rest = generate args
  local RUN="$1"; shift
  if [ ! -f "$RUN/summary.json" ]; then
    echo "== generate -> $RUN"; python src/data/generate.py --out-dir "$RUN" $W "$@" | tail -1
  else echo "== generate: done ($RUN)"; fi
  if [ ! -f "$RUN/$JUDGE_DIR/summary.json" ]; then
    echo "== judge"; python src/data/judge.py "$RUN" $W | tail -1
  else echo "== judge: done"; fi
  if [ ! -f "${RUN}_repair1/summary.json" ]; then
    echo "== repair"; python src/data/repair.py "$RUN" --out-dir "${RUN}_repair1" $W | tail -1
  else echo "== repair: done"; fi
  if [ ! -f "${RUN}_repair1/$JUDGE_DIR/summary.json" ]; then
    echo "== judge repaired"; python src/data/judge.py "${RUN}_repair1" $W | tail -1
  else echo "== judge repaired: done"; fi
  echo "== merge"; python src/data/merge.py "$RUN" | grep -E '"kept_total"|"yield"|GUARD|_merged_tl'
}

case "${1:?usage: run_full_build.sh halueval K | sciq | assemble | audit}" in
  halueval) K="${2:?chunk number 1-4}"; chunk "$BUILD/halueval_c$K" --dataset halueval --chunk "$K" --chunk-size 2500 ;;
  sciq)     chunk "$BUILD/sciq" --dataset sciq ;;
  assemble) [ -f data/interim/splits/halueval_split.json ] || python src/data/split.py
            python src/data/assemble.py --build-dir "$BUILD" ;;
  audit)    python src/data/audit.py data/quartets/train.jsonl --n 100 $W | tail -1
            python src/data/audit.py data/quartets/test.jsonl --n 200 $W | tail -1
            python src/data/audit.py data/quartets/ood_sciq.jsonl --n 200 $W | tail -1 ;;
  *) echo "unknown step: $1"; exit 1 ;;
esac
