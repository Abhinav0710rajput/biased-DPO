"""Final step of the full build: assemble the frozen quartet files (plan §5.8). No API calls.

Collects the merged, kept quartets of every HaluEval chunk and of SciQ, attaches the grouped
split (split.py) to every HaluEval quartet, applies the length-balance trim per output file
(each file must pass the guard on its own, plan §5.6), and writes

  data/quartets/{train,val,test,ood_sciq}.jsonl + MANIFEST.json

Usage (normally via scripts/run_full_build.sh assemble):
  python src/data/assemble.py --build-dir data/interim/full_build
"""

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from generate import ROOT, phrase_shares, warmth_score
from judge import JUDGE_MODEL, JUDGE_VERSION
from length_balance import gap_stats
from merge import balance_trim, gap
from generate import balance_guard
from prompts import PROMPT_VERSION
from split import OUT as SPLIT_FILE

OUT = ROOT / "data" / "quartets"


def load(path: Path) -> dict:
    return {json.loads(l)["qid"]: json.loads(l) for l in path.open(encoding="utf-8")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build-dir", type=Path, default=ROOT / "data" / "interim" / "full_build")
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    split = json.loads(SPLIT_FILE.read_text())["assign"]
    chunks = sorted(args.build_dir.glob("halueval_c*_merged_tl"))
    sciq_dir = args.build_dir / "sciq_merged_tl"
    if not chunks or not sciq_dir.exists():
        raise SystemExit(f"missing merged folders in {args.build_dir}: {len(chunks)} HaluEval chunks, "
                         f"SciQ {'found' if sciq_dir.exists() else 'missing'}")

    files = {"train": {}, "val": {}, "test": {}, "ood_sciq": load(sciq_dir / "kept_quartets.jsonl")}
    for d in chunks:
        for q, v in load(d / "kept_quartets.jsonl").items():
            a = split[q]
            files[a["split"]][q] = {**v, "split": a["split"], "group_id": a["group_id"]}
    for q, v in files["ood_sciq"].items():
        v["split"] = "ood_sciq"

    args.out.mkdir(parents=True, exist_ok=True)
    manifest = {"created": datetime.now().isoformat(timespec="seconds"), "prompt_version": PROMPT_VERSION,
                "judge_version": JUDGE_VERSION, "model": JUDGE_MODEL, "build_dir": str(args.build_dir),
                "halueval_chunks": [d.name for d in chunks], "split_file": str(SPLIT_FILE), "files": {}}
    for name, rows in files.items():
        trimmed = balance_trim(rows)
        stats = gap_stats([gap(v) for v in rows.values()])
        path = args.out / f"{name}.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for q in sorted(rows):
                f.write(json.dumps(rows[q], ensure_ascii=False) + "\n")
        manifest["files"][name] = {
            "quartets": len(rows), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "trimmed_for_balance": len(trimmed), "length_balance": stats, "length_balance_guard": balance_guard(stats),
            "wrong_source": dict(Counter(v.get("wrong_source") for v in rows.values())),
            "kept_in": dict(Counter(v.get("kept_in") for v in rows.values())),
            "groups": len({v.get("group_id") for v in rows.values()}) if name != "ood_sciq" else None,
            "warmth_score": warmth_score(list(rows.values())),
            "phrase_shares_CW": phrase_shares([v["responses"]["CW"]["text"] for v in rows.values()]),
            "phrase_shares_CN": phrase_shares([v["responses"]["CN"]["text"] for v in rows.values()]),
        }
    # Leak check: no group in two HaluEval files.
    gs = [{v["group_id"] for v in files[n].values()} for n in ("train", "val", "test")]
    manifest["groups_shared_between_splits"] = len((gs[0] & gs[1]) | (gs[0] & gs[2]) | (gs[1] & gs[2]))
    assert manifest["groups_shared_between_splits"] == 0
    (args.out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({n: {k: f[k] for k in ("quartets", "trimmed_for_balance", "length_balance_guard", "wrong_source")}
                      for n, f in manifest["files"].items()}, indent=2))
    print(args.out)


if __name__ == "__main__":
    main()
