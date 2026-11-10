"""M0: reproduce the dataset statistics in project_plan.md §4.1 (+ quick SciQ stats).

Sentence splitting follows §5.2: insert a space after a period directly followed by a
capital letter, split into sentences, keep sentences longer than 25 characters.

Usage:  python src/data/stats.py
"""

import json
import re
import statistics
from collections import defaultdict
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
MIN_SENT_CHARS = 25


def read_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def normalize_passage(text: str) -> str:
    return re.sub(r"\.(?=[A-Z])", ". ", text)


def sentences(text: str) -> set[str]:
    parts = re.split(r"(?<=[.!?])\s+", normalize_passage(text))
    return {s.strip() for s in parts if len(s.strip()) > MIN_SENT_CHARS}


class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def halueval_stats() -> None:
    rows = read_jsonl(RAW / "halueval" / "qa_data.json")
    n = len(rows)

    sent_to_rows = defaultdict(set)
    for i, r in enumerate(rows):
        for s in sentences(r["knowledge"]):
            sent_to_rows[s].add(i)

    uf = UnionFind(n)
    linked_pairs = set()
    for idxs in sent_to_rows.values():
        for a, b in combinations(sorted(idxs), 2):
            linked_pairs.add((a, b))
            uf.union(a, b)

    comps = defaultdict(list)
    for i in range(n):
        comps[uf.find(i)].append(i)
    sizes = [len(c) for c in comps.values()]
    isolated = sum(1 for s in sizes if s == 1)

    yesno = sum(1 for r in rows if r["right_answer"].strip().lower() in {"yes", "no"})
    right_len = [len(r["right_answer"].split()) for r in rows]
    hall_len = [len(r["hallucinated_answer"].split()) for r in rows]
    verbatim = sum(1 for r in rows if r["right_answer"].lower() in r["knowledge"].lower())

    print("=== HaluEval QA (plan §4.1) ===")
    print(f"Rows                                   {n:,}")
    print(f"Unique questions                       {len({r['question'] for r in rows}):,}")
    print(f"Unique passages                        {len({r['knowledge'] for r in rows}):,}")
    print(f"Rows sharing no sentence with others   {isolated:,}")
    print(f"Row pairs sharing a sentence           {len(linked_pairs):,}")
    print(f"Groups (connected components)          {len(sizes):,}")
    print(f"Multi-row groups                       {sum(1 for s in sizes if s > 1):,}")
    print(f"  of which 2-row groups ('762 pairs')  {sum(1 for s in sizes if s == 2):,}")
    print(f"Largest group                          {max(sizes)} rows")
    print(f"Yes/no questions                       {yesno:,}")
    print(f"right_answer median words              {statistics.median(right_len)}")
    print(f"hallucinated_answer median words       {statistics.median(hall_len)}")
    print(f"right_answer verbatim in passage       {100 * verbatim / n:.1f}%")


def sciq_stats() -> None:
    print("\n=== SciQ OOD (plan §4.2) ===")
    for split in ["validation", "test"]:
        rows = read_jsonl(RAW / "sciq" / f"{split}.jsonl")
        empty = sum(1 for r in rows if not r["support"].strip())
        in_support = sum(
            1 for r in rows
            if r["support"].strip() and r["correct_answer"].lower() in r["support"].lower()
        )
        print(f"{split:<11} rows {len(rows):,} | empty support {empty} | "
              f"answer in support (kept by §5.1 filter) {in_support}")


if __name__ == "__main__":
    halueval_stats()
    sciq_stats()
