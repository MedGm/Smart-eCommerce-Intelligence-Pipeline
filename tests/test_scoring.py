"""Tests for Top-K scoring."""

import pandas as pd
from src.scoring.topk import compute_score, WEIGHTS


def test_compute_score():
    df = pd.DataFrame(
        {
            "rating": [5.0, 0.0],
            "review_count": [100, 0],
            "is_in_stock": [True, False],
            "discount_pct": [0.2, 0.0],
        }
    )
    s = compute_score(df)
    assert len(s) == 2
    assert s.iloc[0] >= s.iloc[1]


def test_weights_sum_to_one():
    # Float precision: 0.35 + 0.3 + 0.2 + 0.15 can be 0.999... in some runtimes
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9
