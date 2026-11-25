"""CPU tests with a tiny random Qwen3 (real tokenizer). Run:  pytest -q tests/
Needs the Qwen3 tokenizer (downloaded from the Hub on first use, ~10 MB)."""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src/train"))

from config import load_config                                    # noqa: E402
from data import ORDER, Encoder, batches, collate, load_quartets  # noqa: E402
from scoring import (contrasts, pair_weights, quartet_loss, quartet_loss_pairwise,  # noqa: E402
                     quartet_metrics, sums_from_tokens)
import sanity                                                     # noqa: E402

PY = sys.executable


@pytest.fixture(scope="module")
def cfg():
    return load_config("tiny-debug")


@pytest.fixture(scope="module")
def tok(cfg):
    from models import load_tokenizer
    return load_tokenizer(cfg)


def test_T1_loss_identity():
    assert sanity.t1()["pass"]


def test_pair_weights_sum_to_one():
    for rho in (0, 0.25, 0.5, 0.75, 1):
        assert abs(sum(pair_weights({"name": "dpo", "rho": rho}).values()) - 1) < 1e-12


def test_contrast_gaps():
    r = torch.tensor([[3.0, 1.0, -2.0, 0.5]])           # CW, CN, IW, IN
    u, v, w = contrasts(r)
    CW, CN, IW, IN = r[0]
    assert torch.allclose(u + w, CW - IW) and torch.allclose(u - w, CN - IN)
    assert torch.allclose(u + v, CW - IN) and torch.allclose(u - v, CN - IW)


def test_metrics_worst_case():
    s = np.array([[2, 2, 0, 0], [5, 0, 0, 1]], dtype=float)  # 2nd: CN-IN = -1 < 0
    m = quartet_metrics(s)
    assert m["worst_case_acc"] == 0.5 and m["acc_CN>IN"] == 0.5


def test_batches_whole_quartets_and_fixed_order():
    a = list(batches(100, 0, 2, 16))
    assert len(a) == 12 and all(len(i) == 16 for _, _, i in a)
    assert a == list(batches(100, 0, 2, 16)) and a != list(batches(100, 1, 2, 16))
    assert len(set(sum((i for _, e, i in a if e == 0), []))) == 96   # no repeats inside an epoch


def test_encoding_and_masks(cfg, tok):
    enc = Encoder(tok, cfg)
    qs = load_quartets(ROOT / "data/quartets/val.jsonl")[:3]
    e = enc.encode(qs)
    eot = tok.decode(enc.eot_ids)
    for qi, q in enumerate(qs):
        for k, name in enumerate(ORDER):
            ids = e.resp_ids[4 * qi + k]
            assert tok.decode(ids) == q["responses"][name]["text"] + eot
            s, t = q["responses"][name]["ans_span"]
            span_text = tok.decode([i for i, m in zip(ids, e.span_mask[4 * qi + k]) if m])
            assert q["responses"][name]["text"][s:t].strip() in span_text
    b = collate(e, [0, 1, 2], tok.pad_token_id)
    # every response sits at the end of its left-padded row; targets there equal the response ids
    for j in range(12):
        n = len(e.resp_ids[j])
        assert b["targets"][j][b["resp_mask"][j]].tolist() == e.resp_ids[j]
        assert int(b["resp_mask"][j].sum()) == n


def test_sums_from_tokens():
    tok_vals = np.arange(10, dtype=float)
    off = np.array([0, 1, 3, 3, 6, 7, 8, 9, 10])
    s = sums_from_tokens(tok_vals, off)
    assert s.shape == (2, 4) and s[0].tolist() == [0, 3, 0, 12] and s[1].tolist() == [6, 7, 8, 9]


def test_padding_invariance(cfg, tok):
    """A sequence's log-probs must not depend on its batch-mates (left padding + position ids)."""
    from models import load_model
    from scoring import token_logps
    model = load_model(cfg, tok).eval()
    enc = Encoder(tok, cfg)
    e = enc.encode(load_quartets(ROOT / "data/quartets/val.jsonl")[:4])
    with torch.no_grad():
        alone = token_logps(model, collate(e, [0], tok.pad_token_id))
        batched = token_logps(model, collate(e, [0, 1, 2, 3], tok.pad_token_id))
    for j in range(4):
        a = alone[j][alone[j] != 0]
        bb = batched[j][batched[j] != 0]
        assert torch.allclose(a, bb, atol=1e-4), (a - bb).abs().max()


def test_sanity_script_T2_T3_T6():
    r = subprocess.run([PY, "src/train/sanity.py", "--model", "tiny-debug"], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def run_train(*extra):
    return subprocess.run([PY, "src/train/train.py", "--model", "tiny-debug", *extra], cwd=ROOT,
                          capture_output=True, text=True)


@pytest.fixture(scope="module")
def reference():
    r = subprocess.run([PY, "src/train/reference.py", "--model", "tiny-debug", "--limit", "8"], cwd=ROOT,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    return ROOT / "runs/tiny-debug/reference"


def test_train_resume_and_T3_T6(reference):
    out = ROOT / "runs_debug/tiny-debug"
    import shutil as sh
    sh.rmtree(out, ignore_errors=True)
    common = ["--limit-train", "16", "--max-steps", "6", "--set", "eval.dense_every=3", "train.resume_every=2"]
    for rho in ("0", "1"):
        r = run_train("--rho", rho, "--seed", "0", *common)
        assert r.returncode == 0, r.stdout + r.stderr
    d0, d1 = out / "rho0_lr2e-05_beta0.1_seed0", out / "rho1_lr2e-05_beta0.1_seed0"
    h0 = [json.loads(l)["hash"] for l in open(d0 / "batch_hashes.jsonl")]
    h1 = [json.loads(l)["hash"] for l in open(d1 / "batch_hashes.jsonl")]
    assert h0 == h1 and len(h0) == 6                                     # T3 on real runs
    ev = [json.loads(l) for l in open(d0 / "eval_log.jsonl")]
    assert [r["step"] for r in ev if r["split"] == "val"] == [0, 3, 6]
    assert sorted({r["step"] for r in ev if r["split"] == "test" and "posthoc_adapter" not in r}) == [0, 6]  # sparse
    assert set(json.load(open(d0 / "summary.json"))["at_best"]) == {"val", "test", "ood_sciq"}
    assert all(r["T6_max_abs_r"] == 0.0 for r in ev if r["step"] == 0)   # T6 against the cache
    assert json.loads(open(d0 / "train_log.jsonl").readline())["T6_max_abs_r_train"] == 0.0
    assert (d0 / "adapters/step_00006/adapter_model.safetensors").exists()
    assert json.load(open(d0 / "summary.json"))["total_steps"] == 6
    # resume: kill the ρ=0 run after step 4, re-run the same command, compare with the uninterrupted run
    full = [json.loads(l) for l in open(d0 / "train_log.jsonl")]
    sh.rmtree(d0)
    r = run_train("--rho", "0", "--seed", "0", *common, "--stop-after", "4")
    assert r.returncode == 3 and not (d0 / "summary.json").exists()
    r = run_train("--rho", "0", "--seed", "0", *common)
    assert r.returncode == 0 and "resumed at step 4" in r.stdout, r.stdout + r.stderr
    resumed = [json.loads(l) for l in open(d0 / "train_log.jsonl")]
    assert [x["step"] for x in resumed] == list(range(6))
    for a, b in zip(full, resumed):
        assert abs(a["loss"] - b["loss"]) < 1e-6 and abs(a["u"] - b["u"]) < 1e-5


def test_finished_run_is_not_restarted(reference):
    r = run_train("--rho", "1", "--seed", "0", "--limit-train", "16", "--max-steps", "6", "--set",
                  "eval.dense_every=3", "train.resume_every=2")
    assert r.returncode != 0 and "already finished" in (r.stdout + r.stderr)


def test_T4_overfit_small(reference):
    """Tiny model, 8 quartets, high LR: training pairwise accuracy must reach 1 and u must grow."""
    import shutil
    shutil.rmtree(ROOT / "runs_debug/tiny-debug/rho0.5_lr0.01_beta0.1_seed0", ignore_errors=True)
    r = run_train("--rho", "0.5", "--seed", "0", "--limit-train", "8", "--max-steps", "60", "--set",
                  "train.lr=0.01", "train.epochs=200", "train.batch_quartets=4", "train.warmup_ratio=0",
                  "eval.dense_every=1000", "eval.sparse_every=1000", "eval.save_adapters=none")
    assert r.returncode == 0, r.stdout + r.stderr
    log = [json.loads(l) for l in open(ROOT / "runs_debug/tiny-debug/rho0.5_lr0.01_beta0.1_seed0/train_log.jsonl")]
    assert log[-1]["pairwise_acc"] == 1.0 and log[-1]["u"] > log[0]["u"] + 1.0
