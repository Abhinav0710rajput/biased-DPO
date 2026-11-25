"""Quartet DPO training (plan §7.4) with dense evaluation, adapter snapshots and resume.

  python src/train/train.py --model qwen3-4b --rho 0.5 --seed 0 --lr 2e-5
  python src/train/train.py --model qwen3-4b --objective posctrl --seed 0
  python src/train/train.py --model qwen3-4b --objective ties --seed 0

Needs runs/<model>/reference/ (src/train/reference.py) first. Re-running the same command resumes.
Writes runs/<model>/<run_name>/:
  config.json          resolved config + provenance (git commit, data sha256, versions)
  train_log.jsonl      per step: loss, lr, grad norm, batch u/v/w, pair accuracies, warm/neutral r per token
  batch_hashes.jsonl   per step: hash of the quartet ids (T3: identical across ρ for the same seed)
  eval/step_XXXXX.npz  per evaluation step: per-token log π for every response of every eval split
  eval_log.jsonl       per evaluation step and split: u/v/w etc. (summed, per-token, answer span)
  adapters/step_XXXXX/ LoRA weights at every evaluation step
  resume/              latest optimizer/scheduler/adapter state (overwritten)
  summary.json         written at the end: best validation-u step, final metrics
"""

import argparse
import json
import math
import os
import shutil
import time
from pathlib import Path

import numpy as np
import torch

from config import (ROOT, comparable, data_fingerprint, git_info, load_config, reference_dir, run_dir,
                    versions)
from data import Encoder, batch_hash, batches, collate, load_quartets, total_steps
from models import build_peft_model, load_tokenizer, score_encoded, tokenization_hash
from scoring import contrasts, quartet_loss, quartet_metrics, sums_from_tokens, to_device, token_logps


def eval_steps(cfg: dict, total: int) -> list[int]:
    e = cfg["eval"]
    s = set(range(0, min(e["dense_until"], total) + 1, e["dense_every"]))
    s |= set(range(e["dense_until"], total + 1, e["sparse_every"]))
    s.add(total)
    return sorted(x for x in s if x <= total)


def jsonl_append(path: Path, obj: dict) -> None:
    with open(path, "a") as f:
        f.write(json.dumps(obj) + "\n")


def jsonl_truncate(path: Path, keep) -> None:
    if path.exists():
        lines = [l for l in open(path) if keep(json.loads(l))]
        open(path, "w").writelines(lines)


class Run:
    def __init__(self, cfg: dict, limit_train: int | None, max_steps: int | None, stop_after: int | None = None):
        self.cfg = cfg
        self.stop_after = stop_after
        self.dir = run_dir(cfg)
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / "eval").mkdir(exist_ok=True)
        self.dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        prov = {"git": git_info(), "data_sha256": data_fingerprint(cfg), "versions": versions(),
                "limit_train": limit_train, "max_steps": max_steps}
        cfg_path = self.dir / "config.json"
        if cfg_path.exists():
            old = json.load(open(cfg_path))
            if comparable(old["config"]) != comparable(cfg) or old["provenance"]["data_sha256"] != prov["data_sha256"] \
                    or old["provenance"]["limit_train"] != limit_train or old["provenance"]["max_steps"] != max_steps:
                raise SystemExit(f"{cfg_path} exists with a different config/data; use a new output root or delete it")
            if old["provenance"]["git"]["commit"] != prov["git"]["commit"]:
                print("WARNING: resuming with a different git commit than the run started with")
        else:
            json.dump({"config": cfg, "provenance": prov}, open(cfg_path, "w"), indent=1, default=str)

        self.tok = load_tokenizer(cfg)
        self.enc = Encoder(self.tok, cfg)
        train_q = load_quartets(ROOT / cfg["data"]["dir"] / cfg["data"]["train"])[:limit_train]
        self.train = self.enc.encode(train_q)
        t = cfg["train"]
        self.total = total_steps(len(train_q), t["epochs"], t["batch_quartets"])
        if max_steps:
            self.total = min(self.total, max_steps)
        self.eval_at = eval_steps(cfg, self.total)

        # reference cache (per-token log π_ref on the eval splits) and the matching tokenization
        self.ref, self.eval_enc = {}, {}
        ref_meta = json.load(open(reference_dir(cfg) / "meta.json"))
        for split in cfg["data"]["eval_splits"]:
            z = np.load(reference_dir(cfg) / f"{split}.npz")
            n = ref_meta["splits"][split]["quartets"]
            e = self.enc.encode(load_quartets(ROOT / cfg["data"]["dir"] / f"{split}.jsonl")[:n])
            if tokenization_hash(e) != ref_meta["splits"][split]["tokenization"]:
                raise SystemExit(f"{split}: tokenization differs from the reference cache; rebuild it")
            self.ref[split] = {"logp": z["logp"], "offsets": z["offsets"], "span": z["span"]}
            self.eval_enc[split] = e

        self.model = build_peft_model(cfg, self.tok)
        params = [p for p in self.model.parameters() if p.requires_grad]
        self.opt = torch.optim.AdamW(params, lr=t["lr"], weight_decay=t["weight_decay"])
        from transformers import get_cosine_schedule_with_warmup
        self.sched = get_cosine_schedule_with_warmup(self.opt, math.ceil(t["warmup_ratio"] * self.total), self.total)
        self.step = 0
        self.resume()

    # ------------------------------------------------------------ resume
    def resume(self):
        p = self.dir / "resume" / "state.pt"
        if not p.exists():
            for f in ("train_log.jsonl", "batch_hashes.jsonl", "eval_log.jsonl"):
                (self.dir / f).unlink(missing_ok=True)
            return
        from peft import set_peft_model_state_dict
        st = torch.load(p, map_location="cpu", weights_only=False)
        set_peft_model_state_dict(self.model, st["adapter"])
        self.opt.load_state_dict(st["optimizer"])
        self.sched.load_state_dict(st["scheduler"])
        self.step = st["step"]
        torch.set_rng_state(st["torch_rng"])
        jsonl_truncate(self.dir / "train_log.jsonl", lambda r: r["step"] < self.step)
        jsonl_truncate(self.dir / "batch_hashes.jsonl", lambda r: r["step"] < self.step)
        jsonl_truncate(self.dir / "eval_log.jsonl", lambda r: r["step"] <= self.step)
        print(f"resumed at step {self.step}/{self.total}")

    def save_resume(self):
        from peft import get_peft_model_state_dict
        d = self.dir / "resume"
        d.mkdir(exist_ok=True)
        st = {"adapter": get_peft_model_state_dict(self.model), "optimizer": self.opt.state_dict(),
              "scheduler": self.sched.state_dict(), "step": self.step, "torch_rng": torch.get_rng_state()}
        torch.save(st, d / "state.tmp")
        os.replace(d / "state.tmp", d / "state.pt")       # atomic: a kill mid-write keeps the old snapshot

    def save_adapter(self):
        from peft import get_peft_model_state_dict
        from safetensors.torch import save_file
        if self.cfg["eval"]["save_adapters"] != "all":
            return
        d = self.dir / "adapters" / f"step_{self.step:05d}"
        d.mkdir(parents=True, exist_ok=True)
        dtype = getattr(torch, self.cfg["eval"]["adapter_dtype"])
        sd = {k: v.detach().to("cpu", dtype).contiguous() for k, v in get_peft_model_state_dict(self.model).items()}
        save_file(sd, d / "adapter_model.safetensors")
        self.model.peft_config["default"].save_pretrained(d)

    # ------------------------------------------------------------ evaluation
    def evaluate(self):
        t0 = time.time()
        arrays = {}
        for split, e in self.eval_enc.items():
            logp, _ = score_encoded(self.model, e, self.cfg["eval"]["batch_quartets"], self.tok.pad_token_id)
            ref = self.ref[split]
            arrays[split] = logp
            r_tok = logp.astype(np.float64) - ref["logp"]
            off, span = ref["offsets"], ref["span"]
            n_tok = np.diff(off).reshape(-1, 4)
            r_sum = sums_from_tokens(r_tok, off)
            row = {"step": self.step, "split": split, **quartet_metrics(r_sum),
                   **quartet_metrics(r_sum / np.maximum(n_tok, 1), "tok_"),
                   **quartet_metrics(sums_from_tokens(r_tok, off, span), "span_")}
            if self.step == 0:
                row["T6_max_abs_r"] = float(np.abs(r_tok).max())
                if row["T6_max_abs_r"] > 0:
                    print(f"WARNING T6: max |r| at step 0 on {split} = {row['T6_max_abs_r']:.3g} (expected 0)")
            jsonl_append(self.dir / "eval_log.jsonl", row)
        np.savez_compressed(self.dir / "eval" / f"step_{self.step:05d}.npz", **arrays)
        self.save_adapter()
        v = [json.loads(l) for l in open(self.dir / "eval_log.jsonl")][-len(self.eval_enc):]
        sel = next(r for r in v if r["split"] == self.cfg["eval"]["select_on"])
        print(f"[eval step {self.step}] {self.cfg['eval']['select_on']} u={sel['u']:.3f} |v|={sel['abs_v']:.3f} "
              f"|w|={sel['abs_w']:.3f} worst={sel['worst_case_acc']:.3f} ({time.time() - t0:.0f}s)", flush=True)

    # ------------------------------------------------------------ training
    def r_batch(self, idx: list[int]):
        b = to_device(collate(self.train, idx, self.tok.pad_token_id), self.dev)
        lp = token_logps(self.model, b)
        with torch.no_grad(), self.model.disable_adapter():
            lp_ref = token_logps(self.model, b)
        r_tok = lp - lp_ref
        return r_tok.sum(-1).view(-1, 4), r_tok.detach(), b["resp_mask"]

    def fit(self):
        cfg, t, obj = self.cfg, self.cfg["train"], self.cfg["objective"]
        if self.step == 0 and 0 in self.eval_at:
            self.evaluate()
            self.save_resume()
        it = batches(len(self.train.qids), t["seed"], t["epochs"], t["batch_quartets"])
        t0 = time.time()
        for step, epoch, idx in it:
            if step < self.step:
                continue
            if step >= self.total:
                break
            jsonl_append(self.dir / "batch_hashes.jsonl",
                         {"step": step, "hash": batch_hash([self.train.qids[i] for i in idx])})
            rs, tok_r, tok_n = [], [0.0, 0.0], [0, 0]
            mq = t["micro_quartets"]
            for m in range(0, len(idx), mq):
                r, r_tok, mask = self.r_batch(idx[m:m + mq])
                loss = quartet_loss(r, obj).sum() / len(idx)
                loss.backward()
                rs.append(r.detach())
                for g, rows in enumerate(((0, 2), (1, 3))):      # warm (CW, IW) vs neutral (CN, IN)
                    sel = torch.tensor([i for i in range(r_tok.shape[0]) if i % 4 in rows], device=r_tok.device)
                    tok_r[g] += float(r_tok[sel].sum())
                    tok_n[g] += int(mask[sel].sum())
            gn = float(torch.nn.utils.clip_grad_norm_([p for p in self.model.parameters() if p.requires_grad],
                                                      t["max_grad_norm"]))
            self.opt.step()
            self.sched.step()
            self.opt.zero_grad(set_to_none=True)
            r_all = torch.cat(rs)
            with torch.no_grad():
                full_loss = float(quartet_loss(r_all, obj).mean())
            m = quartet_metrics(r_all.float().cpu().numpy())
            row = {"step": step, "epoch": epoch, "loss": round(full_loss, 6), "lr": self.sched.get_last_lr()[0],
                   "grad_norm": round(gn, 6), **{k: m[k] for k in ("u", "v", "w", "abs_v", "abs_w", "pairwise_acc")},
                   "r_tok_warm": tok_r[0] / max(tok_n[0], 1), "r_tok_neutral": tok_r[1] / max(tok_n[1], 1)}
            if step == 0:
                row["T6_max_abs_r_train"] = float(r_all.abs().max())
            jsonl_append(self.dir / "train_log.jsonl", row)
            self.step = step + 1
            if self.step % 10 == 0:
                print(f"step {self.step}/{self.total} loss={full_loss:.4f} u={m['u']:.3f} v={m['v']:.3f} "
                      f"w={m['w']:.3f} ({(time.time() - t0) / 10:.2f}s/step)", flush=True)
                t0 = time.time()
            if self.step in self.eval_at:
                self.evaluate()
                self.save_resume()
            elif self.step % t["resume_every"] == 0:
                self.save_resume()
            if self.stop_after and self.step == self.stop_after:   # test hook: simulate a killed job
                self.save_resume()
                raise SystemExit(3)
        self.finish()

    def finish(self):
        rows = [json.loads(l) for l in open(self.dir / "eval_log.jsonl")]
        sel = [r for r in rows if r["split"] == self.cfg["eval"]["select_on"]]
        best = max(sel, key=lambda r: (r["u"], -r["step"]))
        summary = {"total_steps": self.total, "best_val_u_step": best["step"], "best_val_u": best["u"],
                   "at_best": {r["split"]: r for r in rows if r["step"] == best["step"]},
                   "final": {r["split"]: r for r in rows if r["step"] == self.total}}
        json.dump(summary, open(self.dir / "summary.json", "w"), indent=1)
        shutil.rmtree(self.dir / "resume", ignore_errors=True)
        print(f"done: best val u {best['u']:.3f} at step {best['step']} -> {self.dir}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--objective", default=None, choices=["dpo", "ties", "posctrl"])
    ap.add_argument("--rho", type=float, default=None)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--lr", type=float, default=None)
    ap.add_argument("--set", nargs="*", default=[], help="config overrides key=value (e.g. objective.beta=0.05)")
    ap.add_argument("--limit-train", type=int, default=None, help="debug / T4: first N training quartets")
    ap.add_argument("--max-steps", type=int, default=None, help="debug: stop (and schedule) at this many steps")
    ap.add_argument("--stop-after", type=int, default=None, help="test only: exit after this step as if killed")
    args = ap.parse_args()
    sets = list(args.set)
    for key, val in (("objective.name", args.objective), ("objective.rho", args.rho),
                     ("train.seed", args.seed), ("train.lr", args.lr)):
        if val is not None:
            sets.append(f"{key}={val}")
    cfg = load_config(args.model, sets)
    if cfg["objective"]["name"] != "dpo":
        cfg["objective"]["rho"] = 0.0 if cfg["objective"]["name"] == "ties" else 1.0
    if args.limit_train or args.max_steps:
        cfg["output"]["root"] = "runs_debug"
    Run(cfg, args.limit_train, args.max_steps, args.stop_after).fit()


if __name__ == "__main__":
    main()
