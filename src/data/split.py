"""Grouped train/val/test split of HaluEval (plan §5.2). No API calls.

HaluEval QA passages are Wikipedia paragraphs from HotpotQA (train set), glued together, and the
same paragraph is reused across questions (e.g. the "51 Birch Street" paragraph is in 3 rows), so a
random row split would leak passage text between train and test. Rows are linked with union-find if
their passages share any sentence (> 25 characters, after inserting the missing space in
"...century.First for Women"; plan §5.2) OR any 12-word span (normalised: lowercase, punctuation
removed). The span rule catches reused paragraphs that the sentence rule misses because they were
glued without a space before a digit or quote ("...Michael Collins.51 Birch Street is..."). Each
connected component is a group, and whole groups are assigned to splits. Groups are shuffled with a fixed seed and filled
in order into train / val / test until each reaches its target share (80/10/10) of the USABLE rows
(after the pipeline's filters), so the final quartet counts come out close to 80/10/10.

Usage:  python src/data/split.py   -> data/interim/splits/halueval_split.json
"""

import argparse
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

from generate import HALUEVAL, ROOT, filter_rows, load_rows

OUT = ROOT / "data" / "interim" / "splits" / "halueval_split.json"
TARGETS = (("train", 0.8), ("val", 0.1), ("test", 0.1))
MIN_SENTENCE_CHARS = 25
SPAN_WORDS = 12


def sentences(knowledge: str) -> set[str]:
    text = re.sub(r"\.(?=[A-Z])", ". ", knowledge)
    return {s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > MIN_SENTENCE_CHARS}


def spans(knowledge: str) -> set[str]:
    w = re.sub(r"\W+", " ", knowledge.lower()).split()
    return {" ".join(w[i:i + SPAN_WORDS]) for i in range(len(w) - SPAN_WORDS + 1)}


def keys(knowledge: str) -> set[str]:
    return sentences(knowledge) | spans(knowledge)


def groups(passages: list[str]) -> list[int]:
    parent = list(range(len(passages)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    first = {}
    for i, p in enumerate(passages):
        for s in keys(p):
            if s in first:
                parent[find(i)] = find(first[s])
            else:
                first[s] = i
    return [find(i) for i in range(len(passages))]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    raw = [json.loads(l) for l in HALUEVAL.open(encoding="utf-8") if l.strip()]
    root = groups([r["knowledge"] for r in raw])
    qids = [f"halueval-{i:06d}" for i in range(len(raw))]
    usable = {r["qid"] for r in filter_rows(load_rows(None, args.seed))[0]}

    members = defaultdict(list)
    for q, g in zip(qids, root):
        members[g].append(q)
    order = sorted(members)
    random.Random(args.seed).shuffle(order)

    total = len(usable)
    assign, filled, t = {}, Counter(), 0
    for g in order:
        while t < len(TARGETS) - 1 and filled[TARGETS[t][0]] >= TARGETS[t][1] * total:
            t += 1
        name = TARGETS[t][0]
        for q in members[g]:
            assign[q] = {"split": name, "group_id": f"g{g:05d}"}
        filled[name] += sum(q in usable for q in members[g])

    sizes = Counter(len(m) for m in members.values())
    summary = {
        "seed": args.seed, "rows": len(raw), "usable_rows": total, "groups": len(members),
        "largest_group": max(sizes), "groups_with_2plus_rows": sum(n for s, n in sizes.items() if s > 1),
        "rows_per_split": dict(Counter(a["split"] for a in assign.values())),
        "usable_rows_per_split": {k: filled[k] for k, _ in TARGETS},
    }
    # Leak checks: no passage sentence and no 12-word passage span may occur in two splits.
    for name, fn in (("sentences", sentences), ("12_word_spans", spans)):
        seen = {}
        for q, r in zip(qids, raw):
            for s in fn(r["knowledge"]):
                seen.setdefault(s, set()).add(assign[q]["split"])
        summary[f"{name}_in_2plus_splits"] = sum(len(v) > 1 for v in seen.values())
        assert summary[f"{name}_in_2plus_splits"] == 0, name

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"summary": summary, "assign": assign}, indent=1) + "\n")
    print(json.dumps(summary, indent=2))
    print(OUT)


if __name__ == "__main__":
    main()
