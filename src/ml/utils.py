"""
Shared ML utilities: feature column selection, data loading.
Eliminates the 4x duplicated get_feature_columns() function.
"""

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import accuracy_score
from sklearn.model_selection import cross_val_predict

from src.config import processed_dir

# Columns to exclude from numeric feature matrices
_NON_FEATURE_COLUMNS = frozenset(
    {
        "product_id",
        "product_url",
        "title",
        "description",
        "scraped_at",
        "source_platform",
        "shop_name",
        "category",
        "brand",
        "availability",
        "geography",
        "price_bucket",
        "high_potential",
    }
)


def get_feature_columns(
    df: pd.DataFrame,
    *,
    exclude_score: bool = False,
) -> list[str]:
    """Return numeric feature column names, excluding metadata/target columns.

    Args:
        df: DataFrame with product features.
        exclude_score: If True, also exclude 'score' and 'popularity_proxy'
            to prevent data leakage in supervised models.
    """
    exclude = set(_NON_FEATURE_COLUMNS)
    if exclude_score:
        exclude |= {"score", "popularity_proxy"}
    return [c for c in df.select_dtypes(include=[np.number]).columns if c not in exclude]


def load_features() -> pd.DataFrame:
    """Load the features parquet file."""
    path = processed_dir() / "features.parquet"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


def label_integrity_diagnostics(X, y, estimator, cv, *, random_state: int = 42) -> dict:
    """Run quick diagnostics to detect imbalance-driven or leakage-like behavior.

    Returns class balance, majority baseline accuracy, shuffled-label accuracy,
    and a simple leakage-risk flag based on suspiciously strong shuffled performance.
    """
    y_series = pd.Series(y).reset_index(drop=True)
    class_ratio = y_series.value_counts(normalize=True).sort_index()
    if set(class_ratio.index.tolist()) == {0, 1}:
        class_balance = {
            "negative": float(class_ratio.get(0, 0.0)),
            "positive": float(class_ratio.get(1, 0.0)),
        }
    else:
        class_balance = {str(k): float(v) for k, v in class_ratio.items()}
    majority_baseline_accuracy = float(class_ratio.max()) if len(class_ratio) else 0.0

    shuffled = y_series.sample(frac=1.0, random_state=random_state).reset_index(drop=True)
    shuffled_pred = cross_val_predict(clone(estimator), X, shuffled, cv=cv)
    shuffled_label_accuracy = float(accuracy_score(shuffled, shuffled_pred))

    leakage_risk = shuffled_label_accuracy > (majority_baseline_accuracy + 0.05)
    direct_leakage_check = "fail" if leakage_risk else "pass"

    return {
        "class_balance": class_balance,
        "majority_baseline_accuracy": majority_baseline_accuracy,
        "shuffled_label_accuracy": shuffled_label_accuracy,
        "direct_leakage_check": direct_leakage_check,
        "leakage_risk": bool(leakage_risk),
    }


def honesty_gate(
    *,
    accuracy: float,
    f1: float,
    majority_baseline: float,
    shuffled_accuracy: float,
    target_origin: str = "unknown",
) -> dict:
    """Score run-level trustworthiness for proxy-target triviality and benchmark realism."""
    flags: list[str] = []

    baseline_gap = accuracy - majority_baseline
    shuffle_gap = accuracy - shuffled_accuracy
    shuffle_ratio = shuffled_accuracy / max(majority_baseline, 1e-8)
    near_perfect = accuracy >= 0.98 or f1 >= 0.98

    if near_perfect:
        flags.append("near_perfect_performance")
    if shuffled_accuracy >= 0.90 * majority_baseline:
        flags.append("high_shuffled_accuracy_vs_baseline")
    if shuffle_gap <= 0.15:
        flags.append("low_separation_from_shuffled")
    if target_origin == "proxy_engineered":
        flags.append("proxy_target")
    if accuracy >= 0.98 and target_origin == "proxy_engineered":
        flags.append("near_perfect_on_proxy_target")
    if shuffled_accuracy >= 0.70 and accuracy >= 0.95:
        flags.append("suspicious_structural_signal")
    if majority_baseline >= 0.85:
        flags.append("severe_class_imbalance")

    if "near_perfect_on_proxy_target" in flags or (
        "near_perfect_performance" in flags and "high_shuffled_accuracy_vs_baseline" in flags
    ):
        status = "red"
    elif flags:
        status = "yellow"
    else:
        status = "green"

    trust_score = 100
    if target_origin == "proxy_engineered":
        trust_score -= 25
    if near_perfect:
        trust_score -= 20
    if "high_shuffled_accuracy_vs_baseline" in flags:
        trust_score -= 20
    if "severe_class_imbalance" in flags:
        trust_score -= 15
    if target_origin != "external_observed":
        trust_score -= 20
    if "low_separation_from_shuffled" in flags:
        trust_score -= 10

    trust_score = max(0, min(100, trust_score))

    if status == "green":
        notes = "Benchmark looks plausible for exploratory use."
    elif status == "yellow":
        notes = (
            "Use with caution: benchmark may reflect proxy-target simplicity or structural bias."
        )
    else:
        notes = (
            "Model performance may reflect proxy-target simplicity rather than real business "
            "predictiveness."
        )

    return {
        "status": status,
        "flags": flags,
        "baseline_gap": float(baseline_gap),
        "shuffle_gap": float(shuffle_gap),
        "shuffle_ratio": float(shuffle_ratio),
        "target_origin": target_origin,
        "trust_score": int(trust_score),
        "notes": notes,
    }
