"""End-to-end smoke test on the REAL model at small scale (~15–25 min on one A100 for Qwen3-4B).
Run it once after setting up a machine, and again after any code change, before real runs:

  python src/train/smoke.py --model qwen3-4b          # on the cluster (GPU)
  python src/train/smoke.py --model tiny-debug        # locally (CPU, tiny random model)

Everything goes to runs_smoke/<model>/ (wiped at the start), never to runs/. Steps:
  1  environment: library versions, GPU, data checksums vs MANIFEST
  2  masking check (prompt + response + end-of-turn, answer spans)
  3  open-book check on 8 questions (generation works)
  4  reference cache + untrained u/v/w on the first quartets of val / test / SciQ
  5  sanity checks T1, T2, T3, T6 on the GPU
  6  two short training runs, ρ = 0 and ρ = 1 (seed 0, real batch size); the ρ = 1 run is killed half-way
     and resumed
  7  output checks: files, T6 = 0, identical batches across ρ, evaluation schedule, resume continuity,
     summary.json, scoring a saved adapter afterwards (score_checkpoint.py)
  8  timing and memory, projected to a full run
Prints PASS/FAIL per check and writes runs_smoke/<model>/smoke_report.json. Exit code 1 if anything failed.
"""

import argparse
import json
import shutil
import subprocess
import sys
import time

import numpy as np

from config import ROOT, data_fingerprint, load_config, versions

SMOKE = "runs_smoke"
CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> bool:
    CHECKS.append((name, bool(ok), detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""), flush=True)
    return ok


def run(script: str, *args, expect: int = 0) -> subprocess.CompletedProcess:
    cmd = [sys.executable, script, *map(str, args)]
    t0 = time.time()
    r = subprocess.run(cmd, cwd=ROOT / "src/train", capture_output=True, text=True)
    print(f"  $ {' '.join(cmd[1:])}  ({time.time() - t0:.0f}s, exit {r.returncode})", flush=True)
    if r.returncode != expect:
        print("\n".join(("    " + l) for l in (r.stdout + r.stderr).strip().splitlines()[-25:]))
    return r


def jl(path):
    return [json.loads(l) for l in open(path)] if path.exists() else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--quartets", type=int, default=32, help="eval quartets per split")
    ap.add_argument("--train-quartets", type=int, default=64)
    ap.add_argument("--steps", type=int, default=12)
    args = ap.parse_args()
    cfg = load_config(args.model)
    out = ROOT / SMOKE / cfg["model"]["name"]
    shutil.rmtree(out, ignore_errors=True)
    roots = [f"output.root={SMOKE}", f"output.reference_root={SMOKE}"]
    t_all = time.time()

    print("\n1. environment")
    v = versions()
    check("libraries", True, ", ".join(f"{k} {v[k]}" for k in ("torch", "transformers", "peft")))
    check("GPU", v["gpu"] is not None or args.model == "tiny-debug", str(v["gpu"]))
    try:
        data_fingerprint(cfg)
        check("data checksums match MANIFEST", True)
    except SystemExit as e:
        check("data checksums match MANIFEST", False, str(e))

    print("\n2. masking check")
    r = run("check_template.py", "--model", args.model, "--n", 50)
    check("prompt/response/end-of-turn/answer span", r.returncode == 0)

    print("\n3. open-book generation")
    r = run("openbook.py", "--model", args.model, "--n", 8, "--splits", "val", "--batch", 8, "--max-new", 48,
            "--set", *roots)
    ob = out / "m5" / "openbook.json"
    check("open-book script runs", r.returncode == 0 and ob.exists(),
          json.dumps(json.load(open(ob))) if ob.exists() else "")

    print("\n4. reference cache + untrained u/v/w")
    r = run("reference.py", "--model", args.model, "--limit", args.quartets, "--set", *roots)
    base = out / "reference" / "base_uvw.json"
    ok = r.returncode == 0 and base.exists()
    detail = ""
    if ok:
        b = json.load(open(base))
        detail = "; ".join(f"{s}: u={b[s]['sum']['u']:.2f} v={b[s]['sum']['v']:.2f} w={b[s]['sum']['w']:.2f}" for s in b)
    check("reference.py", ok, detail)

    print("\n5. sanity checks (T1, T2, T3, T6)")
    r = run("sanity.py", "--model", args.model, "--eval-quartets", args.quartets, "--set", *roots)
    sj = out / "m5" / "sanity.json"
    if sj.exists():
        for k, res in json.load(open(sj)).items():
            check(k, res["pass"], json.dumps({a: b for a, b in res.items() if a != "pass"}))
    else:
        check("sanity.py", False)

    print("\n6. short training runs (ρ = 0; ρ = 1 killed and resumed)")
    t = cfg["train"]
    ev = max(2, args.steps // 3)
    common = ["--seed", 0, "--limit-train", args.train_quartets, "--max-steps", args.steps, "--set", *roots,
              f"eval.dense_every={ev}", f"eval.full_every={2 * ev}", f"train.resume_every={ev}"]
    r0 = run("train.py", "--model", args.model, "--rho", 0, *common)
    check("train ρ=0", r0.returncode == 0)
    half = args.steps // 2 + 1
    r1 = run("train.py", "--model", args.model, "--rho", 1, *common, "--stop-after", half, expect=3)
    check("ρ=1 stops as if killed", r1.returncode == 3)
    r1 = run("train.py", "--model", args.model, "--rho", 1, *common)
    check("ρ=1 resumes and finishes", r1.returncode == 0 and f"resumed at step {half}" in r1.stdout)

    print("\n7. output checks")
    lr = f"{t['lr']:g}"
    d0 = out / f"rho0_lr{lr}_beta{cfg['objective']['beta']:g}_seed0"
    d1 = out / f"rho1_lr{lr}_beta{cfg['objective']['beta']:g}_seed0"
    for d in (d0, d1):
        need = ["config.json", "train_log.jsonl", "batch_hashes.jsonl", "eval_log.jsonl", "summary.json"]
        check(f"{d.name}: files", all((d / f).exists() for f in need) and not (d / "resume").exists())
    h0 = [x["hash"] for x in jl(d0 / "batch_hashes.jsonl")]
    h1 = [x["hash"] for x in jl(d1 / "batch_hashes.jsonl")]
    check("T3 on real runs: identical batches for ρ=0 and ρ=1", h0 == h1 and len(h0) == args.steps, f"{len(h0)} steps")
    tl1 = jl(d1 / "train_log.jsonl")
    check("resumed log continuous (no gaps or duplicates)", [x["step"] for x in tl1] == list(range(args.steps)))
    e0 = jl(d0 / "eval_log.jsonl")
    step0 = [x for x in e0 if x["step"] == 0]
    check("T6 at step 0: r = 0 on every split", len(step0) == len(cfg["data"]["eval_splits"])
          and all(x["T6_max_abs_r"] == 0.0 for x in step0), str({x["split"]: x["T6_max_abs_r"] for x in step0}))
    check("T6 on the first training batch", jl(d0 / "train_log.jsonl")[0]["T6_max_abs_r_train"] == 0.0)
    val_steps = sorted({x["step"] for x in e0 if x["split"] == "val"})
    test_steps = sorted({x["step"] for x in e0 if x["split"] == "test" and "posthoc_adapter" not in x})
    want_val = sorted(set(range(0, args.steps + 1, ev)) | {args.steps})
    want_full = sorted({s for s in want_val if s % (2 * ev) == 0} | {0, args.steps})
    check("evaluation schedule (val dense, test/SciQ sparse)", val_steps == want_val and test_steps == want_full,
          f"val {val_steps}, test {test_steps}")
    s0 = json.load(open(d0 / "summary.json"))
    check("summary: best-val-u checkpoint scored on every split",
          set(s0["at_best"]) == set(cfg["data"]["eval_splits"]), f"best step {s0['best_val_u_step']}")
    adapters = sorted(p.name for p in (d0 / "adapters").iterdir())
    check("adapters saved at every evaluation step", len(adapters) == len(want_val), ", ".join(adapters))
    later = next((s for s in want_val if s not in want_full and s != s0["best_val_u_step"]), None)
    if later is not None:
        r = run("score_checkpoint.py", "--run", d0, "--steps", later, "--splits", "test")
        check("score_checkpoint.py on a saved adapter", r.returncode == 0 and any(
            x["step"] == later and x["split"] == "test" for x in jl(d0 / "eval_log.jsonl")), f"step {later}")
    last = [x for x in jl(d0 / "train_log.jsonl")]
    check("training moves r away from 0", abs(last[-1]["u"]) + last[-1]["abs_v"] + last[-1]["abs_w"] > 0,
          f"last batch u={last[-1]['u']:.4f} |v|={last[-1]['abs_v']:.4f} |w|={last[-1]['abs_w']:.4f}")

    print("\n8. timing and memory (projection to a full run)")
    secs = [x["sec"] for x in last[1:]]
    s_step = float(np.median(secs)) if secs else float("nan")
    full_cfg = load_config(args.model)
    from data import total_steps
    n_train = sum(1 for _ in open(ROOT / "data/quartets/train.jsonl"))
    steps = total_steps(n_train, full_cfg["train"]["epochs"], full_cfg["train"]["batch_quartets"])
    from train import eval_steps
    evs = eval_steps(full_cfg, steps)
    n_full = sum(1 for s in evs if s == 0 or s == steps or s % full_cfg["eval"]["full_every"] == 0) + 1  # +1 best
    split_q = {s: sum(1 for _ in open(ROOT / f"data/quartets/{s}.jsonl")) for s in full_cfg["data"]["eval_splits"]}
    sec_q = {x["split"]: x["sec"] / args.quartets for x in step0}
    val_eval = sec_q.get("val", 0) * split_q["val"]
    full_eval = sum(sec_q.get(s, 0) * q for s, q in split_q.items())
    total_h = (steps * s_step + (len(evs) - n_full) * val_eval + n_full * full_eval) / 3600
    mem = max((x.get("max_mem_gb", 0) for x in last), default=0)
    timing = {"sec_per_step": round(s_step, 2), "max_mem_gb": mem, "full_run_steps": steps,
              "val_eval_min": round(val_eval / 60, 1), "full_eval_min": round(full_eval / 60, 1),
              "projected_hours_per_run": round(total_h, 2)}
    print("  " + json.dumps(timing))
    check("memory fits", mem < 38 or args.model == "tiny-debug", f"{mem} GB peak (A100-40GB)")

    n_fail = sum(not ok for _, ok, _ in CHECKS)
    report = {"model": args.model, "minutes": round((time.time() - t_all) / 60, 1), "timing": timing,
              "versions": v, "checks": [{"name": n, "pass": ok, "detail": d} for n, ok, d in CHECKS]}
    json.dump(report, open(out / "smoke_report.json", "w"), indent=1, default=str)
    print(f"\n{'ALL PASSED' if n_fail == 0 else f'{n_fail} FAILED'} ({len(CHECKS)} checks, "
          f"{report['minutes']} min) -> {out / 'smoke_report.json'}")
    raise SystemExit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
