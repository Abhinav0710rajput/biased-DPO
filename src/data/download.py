"""M0: download raw datasets into data/raw/ (untouched).

- HaluEval QA from the canonical GitHub file (RUCAIBox/HaluEval, data/qa_data.json, JSON Lines).
- SciQ (allenai/sciq) validation + test splits from Hugging Face, saved as JSONL.

Writes data/raw/MANIFEST.json with source, row count, and SHA-256 per file.

Usage:  python src/data/download.py
"""

import hashlib
import json
from pathlib import Path

import requests
from datasets import load_dataset

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"

HALUEVAL_URL = "https://raw.githubusercontent.com/RUCAIBox/HaluEval/main/data/qa_data.json"
SCIQ_SPLITS = ["validation", "test"]  # plan §4.2: OOD set uses only these


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def count_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def download_halueval() -> Path:
    out = RAW / "halueval" / "qa_data.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(HALUEVAL_URL, timeout=120)
    resp.raise_for_status()
    out.write_bytes(resp.content)
    # sanity: every line parses and has the expected fields
    with out.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue
            row = json.loads(line)
            missing = {"knowledge", "question", "right_answer", "hallucinated_answer"} - row.keys()
            if missing:
                raise ValueError(f"HaluEval line {i} missing fields {missing}")
    return out


def download_sciq() -> list[Path]:
    ds = load_dataset("allenai/sciq")
    paths = []
    for split in SCIQ_SPLITS:
        out = RAW / "sciq" / f"{split}.jsonl"
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as f:
            for row in ds[split]:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        paths.append(out)
    return paths


def main() -> None:
    manifest = {}
    hal = download_halueval()
    manifest[str(hal.relative_to(ROOT))] = {
        "source": HALUEVAL_URL,
        "rows": count_lines(hal),
        "sha256": sha256(hal),
    }
    for p in download_sciq():
        manifest[str(p.relative_to(ROOT))] = {
            "source": f"hf://allenai/sciq ({p.stem})",
            "rows": count_lines(p),
            "sha256": sha256(p),
        }
    (RAW / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    for k, v in manifest.items():
        print(f"{k}: {v['rows']} rows")


if __name__ == "__main__":
    main()
