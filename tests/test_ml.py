"""Tests for ML utilities and training modules."""

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold
from src.ml.utils import get_feature_columns, honesty_gate, label_integrity_diagnostics


def _sample_df():
    """Create a sample DataFrame with typical feature columns."""
    return pd.DataFrame(
        {
            "product_id": ["p1", "p2", "p3"],
            "title": ["A", "B", "C"],
            "description": ["desc", "desc", "desc"],
            "category": ["cat1", "cat2", "cat1"],
            "brand": ["b1", "b1", "b2"],
            "shop_name": ["s1", "s1", "s2"],
            "source_platform": ["shopify", "shopify", "woocommerce"],
            "availability": ["in stock", "out of stock", "in stock"],
            "geography": ["US", "US", "UK"],
            "price": [10.0, 20.0, 30.0],
            "old_price": [15.0, 20.0, 40.0],
            "rating": [4.0, 3.0, 5.0],
            "review_count": [10, 0, 50],
            "discount_pct": [0.33, 0.0, 0.25],
            "is_in_stock": [True, False, True],
            "score": [0.8, 0.3, 0.9],
            "popularity_proxy": [0.7, 0.2, 0.85],
            "price_bucket": ["mid", "low", "high"],
        }
    )


def test_get_feature_columns_excludes_metadata():
    df = _sample_df()
    cols = get_feature_columns(df)
    for excluded in [
        "product_id",
        "title",
        "description",
        "category",
        "brand",
        "shop_name",
        "source_platform",
        "availability",
        "geography",
        "price_bucket",
    ]:
        assert excluded not in cols


def test_get_feature_columns_includes_numeric():
    df = _sample_df()
    cols = get_feature_columns(df)
    for included in ["price", "old_price", "rating", "review_count", "discount_pct"]:
        assert included in cols


def test_get_feature_columns_exclude_score():
    df = _sample_df()
    cols_with_score = get_feature_columns(df, exclude_score=False)
    cols_without_score = get_feature_columns(df, exclude_score=True)
    assert "score" in cols_with_score
    assert "popularity_proxy" in cols_with_score
    assert "score" not in cols_without_score
    assert "popularity_proxy" not in cols_without_score


def test_exclude_score_prevents_data_leakage():
    """Ensure that supervised models cannot access their own label inputs."""
    df = _sample_df()
    cols = get_feature_columns(df, exclude_score=True)
    # score and popularity_proxy are both derived from the same features
    # used for the high_potential label — excluding them prevents data leakage
    assert "score" not in cols
    assert "popularity_proxy" not in cols
    assert "high_potential" not in cols


def test_label_integrity_diagnostics_has_expected_keys():
    df = _sample_df().copy()
    df["high_potential"] = [1, 0, 1]
    features = get_feature_columns(df, exclude_score=True)
    X = df[features].fillna(0)
    y = df["high_potential"]

    clf = RandomForestClassifier(n_estimators=10, random_state=42)
    cv = StratifiedKFold(n_splits=2, shuffle=True, random_state=42)
    d = label_integrity_diagnostics(X, y, clf, cv=cv, random_state=42)

    assert "class_balance" in d
    assert "majority_baseline_accuracy" in d
    assert "shuffled_label_accuracy" in d
    assert "direct_leakage_check" in d
    assert "leakage_risk" in d


def test_label_integrity_diagnostics_value_ranges():
    df = _sample_df().copy()
    df = pd.concat([df] * 4, ignore_index=True)
    df["high_potential"] = [1, 0, 1] * 4
    features = get_feature_columns(df, exclude_score=True)
    X = df[features].fillna(0)
    y = df["high_potential"]

    clf = RandomForestClassifier(n_estimators=20, random_state=42)
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    d = label_integrity_diagnostics(X, y, clf, cv=cv, random_state=42)

    assert 0.0 <= d["majority_baseline_accuracy"] <= 1.0
    assert 0.0 <= d["shuffled_label_accuracy"] <= 1.0
    assert isinstance(d["leakage_risk"], bool)
    assert d["direct_leakage_check"] in {"pass", "fail"}


def test_honesty_gate_flags_proxy_near_perfect_case():
    gate = honesty_gate(
        accuracy=1.0,
        f1=1.0,
        majority_baseline=0.792,
        shuffled_accuracy=0.763,
        target_origin="proxy_engineered",
    )
    assert gate["status"] == "red"
    assert "near_perfect_performance" in gate["flags"]
    assert "proxy_target" in gate["flags"]
    assert "high_shuffled_accuracy_vs_baseline" in gate["flags"]
    assert 0 <= gate["trust_score"] <= 100


def test_honesty_gate_green_case():
    gate = honesty_gate(
        accuracy=0.81,
        f1=0.78,
        majority_baseline=0.65,
        shuffled_accuracy=0.52,
        target_origin="external_observed",
    )
    assert gate["status"] == "green"
    assert gate["flags"] == []
