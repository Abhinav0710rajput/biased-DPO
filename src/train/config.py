"""Run configuration: configs/default.yaml + configs/models/<model>.yaml + --set overrides.

A run's identity is (model, objective, rho, seed, lr). Everything else must be identical across
runs of the same model; config.json records the full resolved config plus provenance
(git commit, data hashes, library versions) so runs from different teammates can be checked.
"""

import copy
import hashlib
import json
import platform
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def deep_update(base: dict, upd: dict) -> dict:
    for k, v in upd.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            deep_update(base[k], v)
        else:
            base[k] = v
    return base


def parse_value(s: str):
    """Command-line override value. Numbers first: YAML 1.1 reads '5e-05' (no decimal point) as a string."""
    for cast in (int, float):
        try:
            return cast(s)
        except ValueError:
            pass
    return yaml.safe_load(s)


def load_config(model: str, overrides: list[str] | None = None) -> dict:
    cfg = yaml.safe_load(open(ROOT / "configs/default.yaml"))
    model_file = ROOT / "configs/models" / f"{model}.yaml"
    if not model_file.exists():
        raise SystemExit(f"no model config {model_file}")
    deep_update(cfg, yaml.safe_load(open(model_file)))
    for o in overrides or []:
        key, _, val = o.partition("=")
        node = cfg
        parts = key.split(".")
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = parse_value(val)
    validate(cfg)
    return cfg


def validate(cfg: dict) -> None:
    t, o = cfg["train"], cfg["objective"]
    assert t["batch_quartets"] % t["micro_quartets"] == 0, "batch_quartets must be a multiple of micro_quartets"
    assert cfg["lora"]["dropout"] == 0.0, "LoRA dropout must be 0 (plan §7.3)"
    assert o["name"] in {"dpo", "ties", "posctrl"}, o["name"]
    assert 0.0 <= o["rho"] <= 1.0


def run_name(cfg: dict) -> str:
    o, t = cfg["objective"], cfg["train"]
    if o["name"] == "dpo":
        tag = f"rho{o['rho']:g}"
    elif o["name"] == "ties":
        tag = f"ties{o['tie_weight']:g}"
    else:
        tag = "posctrl"
    return f"{tag}_lr{t['lr']:g}_beta{o['beta']:g}_seed{t['seed']}"


def run_dir(cfg: dict) -> Path:
    return ROOT / cfg["output"]["root"] / cfg["model"]["name"] / run_name(cfg)


def reference_dir(cfg: dict) -> Path:
    return ROOT / cfg["output"]["reference_root"] / cfg["model"]["name"] / "reference"


def git_info() -> dict:
    def run(*a):
        try:
            return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, timeout=10).stdout.strip()
        except Exception:
            return ""
    status = run("status", "--porcelain", "--", "src", "configs")
    return {"commit": run("rev-parse", "HEAD"), "dirty_src_or_configs": bool(status)}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def data_fingerprint(cfg: dict) -> dict:
    """sha256 of every data file used, checked against data/quartets/MANIFEST.json."""
    d = ROOT / cfg["data"]["dir"]
    manifest = json.load(open(d / "MANIFEST.json"))["files"]
    out = {}
    for split in ["train", *cfg["data"]["eval_splits"]]:
        got = sha256_file(d / f"{split}.jsonl")
        want = manifest.get(split, {}).get("sha256")
        if cfg["data"]["verify_manifest"] and got != want:
            raise SystemExit(f"{split}.jsonl sha256 {got[:12]} != MANIFEST {str(want)[:12]}: data changed")
        out[split] = got
    return out


def versions() -> dict:
    import numpy, torch, transformers, peft
    return {"python": platform.python_version(), "torch": torch.__version__,
            "transformers": transformers.__version__, "peft": peft.__version__, "numpy": numpy.__version__,
            "cuda": torch.version.cuda, "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}


# Fields that may differ when a run is resumed on another node; everything else must match.
_RUNTIME_KEYS = {"provenance"}


def comparable(cfg: dict) -> dict:
    c = copy.deepcopy(cfg)
    for k in _RUNTIME_KEYS:
        c.pop(k, None)
    c["model"].pop("path", None)          # the local weights folder may differ between machines
    return c
