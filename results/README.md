# Results (shared through git)

Small, shareable outputs copied out of each teammate's `runs/` by `src/train/collect.py`
(on the cluster: `bash scripts/hpc/collect_results.sh`). Large files (LoRA adapters, resume state)
stay in `runs/` on the machine that trained them.

```
results/<model>/
  setup/                one copy per model (first teammate to collect writes it; never overwritten):
                        openbook.json (+ generations), base_uvw.json (untrained u/v/w), reference_meta.json,
                        reference_tokens.npz (untrained per-token log π_ref), sanity/smoke reports
  runs/<run_name>/      config.json, summary.json, eval_log.jsonl, train_log.jsonl, batch_hashes.jsonl,
                        quartet_scores.npz (r per quartet × response × evaluation step; full and answer span),
                        token_r.npz (per-token r at the best-val-u and final steps)
```

Run names are `<rho…|ties…|posctrl>_lr<LR>_beta<β>_seed<seed>`. Seeds are split between teammates, so runs never collide.

**Workflow after a job finishes:** `bash scripts/hpc/collect_results.sh`, then
`git add results && git commit -m "results: <what>" && git pull --rebase && git push`.
