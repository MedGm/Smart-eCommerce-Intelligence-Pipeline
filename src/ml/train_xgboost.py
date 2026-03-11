"""
XGBoost classifier: comparison model for high-potential product prediction.
Same label as RandomForest (top 20% by heuristic score).
Dossier: xgboost for predicting product success.

NOTE: The 'score' and 'popularity_proxy' columns are excluded from features
to avoid circular data leakage.
"""

import json

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from src.config import analytics_dir, get_logger
from src.ml.utils import get_feature_columns, load_features

logger = get_logger(__name__)

try:
    from xgboost import XGBClassifier

    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False


def run():
    if not HAS_XGBOOST:
        logger.warning("XGBoost not installed. pip install xgboost to enable.")
        return

    out_dir = analytics_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    df = load_features()
    if df.empty or len(df) < 20:
        logger.warning("Not enough data for XGBoost training (%d rows).", len(df))
        return

    if "score" not in df.columns:
        from src.scoring.topk import compute_score

        df["score"] = compute_score(df)
    df["high_potential"] = (df["score"] >= df["score"].quantile(0.80)).astype(int)

    # exclude_score=True prevents data leakage
    features = get_feature_columns(df, exclude_score=True)
    if not features:
        logger.warning("No numeric features found.")
        return

    X = df[features].fillna(0)
    y = df["high_potential"]

    clf = XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        random_state=42,
        eval_metric="logloss",
    )

    cv = StratifiedKFold(
        n_splits=min(5, max(2, y.value_counts().min())),
        shuffle=True,
        random_state=42,
    )
    y_pred = cross_val_predict(clf, X, y, cv=cv)

    metrics = {
        "model": "XGBoost",
        "method": "cross_validation",
        "n_samples": len(df),
        "n_features": len(features),
        "features": features,
        "accuracy": float(accuracy_score(y, y_pred)),
        "precision": float(precision_score(y, y_pred, zero_division=0)),
        "recall": float(recall_score(y, y_pred, zero_division=0)),
        "f1": float(f1_score(y, y_pred, zero_division=0)),
        "confusion_matrix": confusion_matrix(y, y_pred).tolist(),
    }
    with open(out_dir / "model_metrics_xgboost.json", "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info("XGBoost trained. Metrics -> analytics/model_metrics_xgboost.json")
    return clf, metrics


if __name__ == "__main__":
    run()
