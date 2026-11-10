"""Dataset-level length balancing (plan §5.6: tone must not predict length).

Each row may have several neutral versions that pass every check (each within V8's per-row
tolerance of the warm version). Picking the closest one per row still leaves a systematic skew
(pilot v2.5: warm longer in 38 rows, shorter in 15, mean +0.6 words). This module picks one
option per row so that, across the dataset,
  - the mean warm-minus-neutral gap is ~0, and
  - warm is longer in about as many rows as it is shorter,
while still preferring small per-row gaps.
"""


def _objective(gaps: list[int], long_tails: int = 0) -> tuple:
    """Lexicographic: (1) dataset balance, (2) fewest neutral versions with long tails after the
    answer, (3) smallest per-row gaps. Balance always comes first (plan §5.6)."""
    total = sum(gaps)
    sign_imbalance = sum(g > 0 for g in gaps) - sum(g < 0 for g in gaps)
    per_row = sum(abs(g) for g in gaps)
    return (abs(total) + abs(sign_imbalance), long_tails, per_row)


def balance(options_per_row: list[list[dict]], max_rounds: int = 20, prefer_tail: int | None = None) -> list[int]:
    """options_per_row[i] = list of {"gap": int, "similarity": float, "tail": int, ...} (all passing).
    Returns the chosen option index for each row. Deterministic: rows are visited in order.
    prefer_tail: options with more than this many words after the answer count as "long tails"."""
    def is_long(o):
        return prefer_tail is not None and o.get("tail", 0) > prefer_tail

    # Start from the per-row best: short tail, then smallest |gap|, then least similar to warm.
    choice = [min(range(len(opts)), key=lambda k: (is_long(opts[k]), abs(opts[k]["gap"]), opts[k]["similarity"]))
              for opts in options_per_row]
    gaps = [opts[c]["gap"] for opts, c in zip(options_per_row, choice)]
    longs = [is_long(opts[c]) for opts, c in zip(options_per_row, choice)]
    best = _objective(gaps, sum(longs))
    for _ in range(max_rounds):
        improved = False
        for i, opts in enumerate(options_per_row):
            for k in range(len(opts)):
                if k == choice[i]:
                    continue
                old, old_long = gaps[i], longs[i]
                gaps[i], longs[i] = opts[k]["gap"], is_long(opts[k])
                score = _objective(gaps, sum(longs))
                if score < best:
                    best, choice[i], improved = score, k, True
                else:
                    gaps[i], longs[i] = old, old_long
        if not improved:
            break
    return choice


def gap_stats(gaps: list[int]) -> dict:
    n = max(1, len(gaps))
    return {"mean": round(sum(gaps) / n, 2), "warm_longer": sum(g > 0 for g in gaps),
            "warm_shorter": sum(g < 0 for g in gaps), "equal": sum(g == 0 for g in gaps)}
