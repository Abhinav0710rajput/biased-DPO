"""Crash-safe parallel map for the long full-build steps (generate, judge, repair).

Every finished item is appended to a `partial.jsonl` checkpoint immediately. Re-running the same
command reads the checkpoint, keeps the items that finished cleanly (`done_ok`), and only runs the
rest (items never started, plus items that hit an API error, e.g. a VPN drop). So an interrupted
2,500-row chunk loses at most the calls that were in flight. Rows that fail with an API error are
retried automatically (3 rounds, 60 s apart); if any still fail, the step stops WITHOUT writing its
outputs, so the driver script stops too and re-running the same command retries just those rows.
"""

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable

from tqdm import tqdm


def run_checkpointed(items: list, key: Callable, fn: Callable, path: Path, workers: int, desc: str,
                     done_ok: Callable[[dict], bool], rounds: int = 3, wait: float = 60) -> list[dict]:
    done = {}
    if path.exists():
        for line in path.open(encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                done[r["_ckey"]] = r  # the last record per key wins
    done = {k: r for k, r in done.items() if done_ok(r)}
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = threading.Lock()
    for round_ in range(1, rounds + 1):
        todo = [it for it in items if key(it) not in done]
        if not todo:
            break
        if done or round_ > 1:
            print(f"[checkpoint] {path}: {len(done)} done, {len(todo)} to run (round {round_}/{rounds})")
        if round_ > 1:
            time.sleep(wait)  # let a rate limit or a VPN blip clear before retrying the failed rows
        with path.open("a", encoding="utf-8") as f, ThreadPoolExecutor(workers) as pool:
            futures = {pool.submit(fn, it): key(it) for it in todo}
            for fut in tqdm(as_completed(futures), total=len(futures), desc=desc):
                r = {**fut.result(), "_ckey": futures[fut]}
                with lock:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
                    f.flush()
                if done_ok(r):
                    done[r["_ckey"]] = r
    missing = [key(it) for it in items if key(it) not in done]
    if missing:
        # Never write a summary with rows silently lost to API errors: stop here; re-running the
        # same command resumes from the checkpoint and retries only these rows.
        raise SystemExit(f"[checkpoint] {len(missing)} rows still failing after {rounds} rounds "
                         f"(API errors). Re-run the same command to retry them. Checkpoint: {path}")
    return [{k: v for k, v in done[k].items() if k != "_ckey"} for k in (key(it) for it in items)]


def no_api_error(record: dict) -> bool:
    """Generation/repair record: finished without an API error on any attempt."""
    return not any("error" in a for a in record.get("attempts", []))
