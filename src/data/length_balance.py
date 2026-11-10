"""Dataset-level length balancing (plan §5.6: tone must not predict length).

Each row may have several (warm, neutral) pairs that pass every check, each within V8's per-row
tolerance. Picking the closest pair per row still leaves a systematic skew (pilot: warm longer in
38 rows vs shorter in 15, mean +0.6 words). balance() picks one pair per row so that across the
run the mean warm-minus-neutral gap is ~0 and warm is longer in about as many rows as it is
shorter, while still preferring small per-row gaps.
"""


def _objective(gaps: list[int]) -> tuple:
    """Lexicographic: (1) dataset balance (|sum of gaps| + |#longer - #shorter|), (2) small per-row gaps."""
    sign_imbalance = sum(g > 0 for g in gaps) - sum(g < 0 for g in gaps)
    return (abs(sum(gaps)) + abs(sign_imbalance), sum(abs(g) for g in gaps))


def balance(options_per_row: list[list[dict]], max_rounds: int = 20) -> list[int]:
    """options_per_row[i] = passing pairs {"gap": int, "similarity": float, ...} of row i.
    Returns the chosen pair index per row. Deterministic greedy search: start from each row's
    closest pair (then least similar), then switch single rows while the objective improves."""
    choice = [min(range(len(o)), key=lambda k: (abs(o[k]["gap"]), o[k]["similarity"])) for o in options_per_row]
    gaps = [o[c]["gap"] for o, c in zip(options_per_row, choice)]
    best = _objective(gaps)
    for _ in range(max_rounds):
        improved = False
        for i, opts in enumerate(options_per_row):
            for k in range(len(opts)):
                if k == choice[i]:
                    continue
                old, gaps[i] = gaps[i], opts[k]["gap"]
                score = _objective(gaps)
                if score < best:
                    best, choice[i], improved = score, k, True
                else:
                    gaps[i] = old
        if not improved:
            break
    return choice


def gap_stats(gaps: list[int]) -> dict:
    n = max(1, len(gaps))
    return {"mean": round(sum(gaps) / n, 2), "warm_longer": sum(g > 0 for g in gaps),
            "warm_shorter": sum(g < 0 for g in gaps), "equal": sum(g == 0 for g in gaps)}
