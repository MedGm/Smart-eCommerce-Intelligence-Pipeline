"""Tests for preprocessing cleaning."""
import pandas as pd
import numpy as np
from src.preprocessing.clean import remove_duplicates, standardize_prices, clean


def test_remove_duplicates():
    df = pd.DataFrame([
        {"source_platform": "s", "shop_name": "h", "product_id": "1", "title": "A"},
        {"source_platform": "s", "shop_name": "h", "product_id": "1", "title": "B"},
    ])
    out = remove_duplicates(df)
    assert len(out) == 1


def test_standardize_prices():
    df = pd.DataFrame({"price": ["10.5", "invalid", -1], "old_price": [20, 30, 40]})
    out = standardize_prices(df)
    assert out["price"].iloc[0] == 10.5
    assert pd.isna(out["price"].iloc[1])
    assert pd.isna(out["price"].iloc[2]) or out["price"].iloc[2] < 0 == False


def test_clean_pipeline():
    df = pd.DataFrame([
        {"source_platform": "s", "shop_name": "h", "product_id": "1", "title": "A", "price": 10, "old_price": 20, "rating": 4, "review_count": 5},
        {"source_platform": "s", "shop_name": "h", "product_id": "1", "title": "A", "price": 10, "old_price": 20, "rating": 4, "review_count": 5},
    ])
    out = clean(df)
    assert len(out) == 1
