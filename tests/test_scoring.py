"""Tests for Top-K scoring."""

import pandas as pd
from src.scoring.topk import WEIGHTS, compute_score, topk_per_shop


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


def test_topk_per_shop_keeps_group_columns():
    df = pd.DataFrame(
        {
            "source_platform": ["shopify", "shopify", "woocommerce"],
            "shop_name": ["A", "A", "B"],
            "product_id": ["1", "2", "3"],
            "score": [0.9, 0.5, 0.8],
        }
    )
    out = topk_per_shop(df, k=1)
    assert "shop_name" in out.columns
    assert "source_platform" in out.columns
    assert set(out["shop_name"]) == {"A", "B"}
