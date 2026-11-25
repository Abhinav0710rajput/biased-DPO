"""Copy the small, shareable results out of runs/ into results/ (tracked in git), so every teammate's
runs end up in one place. Large files (LoRA adapters, resume state) stay in runs/.

  python src/train/collect.py                      # all models, all runs (re-run any time; overwrites)
  bash scripts/hpc/collect_results.sh              # same, on the cluster (inside the container)

results/<model>/
  setup/                 one copy per model (the untrained model is the same for everyone). Written by whoever
                         collects first; later collects never overwrite it (use --overwrite-setup to replace it):
      openbook.json, openbook_generations.jsonl   open/closed-book check (M5)
      base_uvw.json, reference_meta.json          untrained model's u/v/w + cache provenance
      reference_tokens.npz                        untrained per-token log π_ref (val, test, SciQ) for heatmaps
      lengths.json, sanity.json, smoke_report.json (when present)
  runs/<run_name>/       one folder per (objective, ρ, LR, β, seed); run names are unique, so teammates never collide
      config.json, summary.json, eval_log.jsonl, train_log.jsonl, batch_hashes.jsonl
                         (seeds are split between teammates, so run names, and folders, never collide)
      quartet_scores.npz   r per quartet and response at every evaluation step: arrays <split>_full, <split>_span
                           [n_steps, N, 4] (order CW, CN, IW, IN), <split>_steps, <split>_qids, <split>_n_tokens
      token_r.npz          per-token r (= log π − log π_ref) at the best-val-u and final steps (Fig 5 heatmap)
"""

import argparse
import json
import os
import re
import shutil
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SETUP_FILES = {"m5/openbook.json": "openbook.json", "m5/openbook_generations.jsonl": "openbook_generations.jsonl",
               "m5/lengths.json": "lengths.json", "m5/sanity.json": "sanity.json",
               "reference/base_uvw.json": "base_uvw.json", "reference/meta.json": "reference_meta.json"}
RUN_FILES = ["config.json", "summary.json", "eval_log.jsonl", "train_log.jsonl", "batch_hashes.jsonl"]
STEP_RE = re.compile(r"step_(\d{5})(_posthoc)?\.npz$")


def copy(src: Path, dst: Path, keep_existing: bool = False) -> bool:
    if not src.exists():
        return False
    if keep_existing and dst.exists():
        if dst.read_bytes() != src.read_bytes():
            print(f"  kept the existing {dst.relative_to(ROOT)} (yours differs; --overwrite-setup to replace)")
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def load_ref(ref_dir: Path) -> dict:
    return {p.stem: dict(np.load(p)) for p in ref_dir.glob("*.npz")}


def run_arrays(run: Path, ref: dict) -> tuple[dict, dict]:
    """quartet_scores (all evaluation steps) and token_r (best + final steps) from the per-token eval files."""
    per_split: dict[str, dict[int, np.ndarray]] = {}
    for f in sorted((run / "eval").glob("step_*.npz")):
        m = STEP_RE.search(f.name)
        if not m:
            continue
        step = int(m.group(1))
        z = np.load(f)
        for split in z.files:
            per_split.setdefault(split, {})[step] = z[split]
    scores, tokens = {}, {}
    summary = json.load(open(run / "summary.json")) if (run / "summary.json").exists() else {}
    keep_tokens = {summary.get("best_val_u_step"), summary.get("total_steps")} - {None}
    for split, by_step in per_split.items():
        if split not in ref:
            continue
        rf = ref[split]
        off, span = rf["offsets"], rf["span"].astype(np.float64)
        steps = sorted(by_step)
        full, sp = [], []
        for s in steps:
            r_tok = by_step[s].astype(np.float64) - rf["logp"]
            full.append(np.add.reduceat(r_tok, off[:-1]).reshape(-1, 4))
            sp.append(np.add.reduceat(r_tok * span, off[:-1]).reshape(-1, 4))
            if s in keep_tokens:
                tokens[f"{split}_step{s}"] = r_tok.astype(np.float32)
        scores[f"{split}_full"] = np.stack(full).astype(np.float32)
        scores[f"{split}_span"] = np.stack(sp).astype(np.float32)
        scores[f"{split}_steps"] = np.array(steps)
        scores[f"{split}_qids"] = rf["qids"]
        scores[f"{split}_n_tokens"] = np.diff(off).reshape(-1, 4)
        if tokens:
            tokens[f"{split}_offsets"] = off
            tokens[f"{split}_span"] = rf["span"]
    return scores, tokens


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs")
    ap.add_argument("--out", default="results")
    ap.add_argument("--overwrite-setup", action="store_true", help="replace results/<model>/setup/ with yours")
    args = ap.parse_args()
    runs_root, out_root = ROOT / args.runs, ROOT / args.out
    if not runs_root.exists():
        raise SystemExit(f"nothing to collect: {runs_root} does not exist")
    for model_dir in sorted(p for p in runs_root.iterdir() if p.is_dir()):
        model = model_dir.name
        out_model = out_root / model
        setup = out_model / "setup"
        keep = not args.overwrite_setup
        n_setup = sum(copy(model_dir / src, setup / dst, keep) for src, dst in SETUP_FILES.items())
        n_setup += copy(ROOT / "runs_smoke" / model / "smoke_report.json", setup / "smoke_report.json", keep)
        ref_dir = model_dir / "reference"
        ref = load_ref(ref_dir) if ref_dir.exists() else {}
        if ref and (args.overwrite_setup or not (setup / "reference_tokens.npz").exists()):
            setup.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(setup / "reference_tokens.npz",
                                **{f"{s}_{k}": v for s, d in ref.items() for k, v in d.items()})
            n_setup += 1
        n_runs = 0
        for run in sorted(p for p in model_dir.iterdir() if p.is_dir() and (p / "config.json").exists()):
            dst = out_model / "runs" / run.name
            for f in RUN_FILES:
                copy(run / f, dst / f)
            if ref:
                scores, tokens = run_arrays(run, ref)
                if scores:
                    np.savez_compressed(dst / "quartet_scores.npz", **scores)
                if tokens:
                    np.savez_compressed(dst / "token_r.npz", **tokens)
            state = "finished" if (run / "summary.json").exists() else "in progress"
            print(f"  {model}/{run.name}: {state}")
            n_runs += 1
        print(f"{model}: {n_setup} setup files written, {n_runs} runs -> {out_model.relative_to(ROOT)}")
    size = sum(p.stat().st_size for p in out_root.rglob("*") if p.is_file()) / 2**20
    print(f"results/ is {size:.1f} MB. Next: git add results && git commit -m 'results' && git push")


if __name__ == "__main__":
    main()
