"""
Supervised model: predict high-potential product (top 20% by heuristic score).
Baseline: RandomForestClassifier.
Uses cross-validation for robust metrics (fixes F1=1.0 artifact from small data).

NOTE: The 'score' and 'popularity_proxy' columns are excluded from features
to avoid circular data leakage (they are derived from the same inputs).
"""

import json

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from src.config import analytics_dir, get_logger
from src.ml.utils import (
    get_feature_columns,
    honesty_gate,
    label_integrity_diagnostics,
    load_features,
)

logger = get_logger(__name__)


def run():
    out_dir = analytics_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    df = load_features()
    if df.empty or len(df) < 20:
        logger.warning("Not enough data for training (%d rows).", len(df))
        return

    if "score" not in df.columns:
        from src.scoring.topk import compute_score

        df["score"] = compute_score(df)
    target_origin = "proxy_engineered"
    df["high_potential"] = (df["score"] >= df["score"].quantile(0.80)).astype(int)

    # exclude_score=True prevents data leakage
    features = get_feature_columns(df, exclude_score=True)
    if not features:
        logger.warning("No numeric features found.")
        return

    X = df[features].fillna(0)
    y = df["high_potential"]

    clf = RandomForestClassifier(n_estimators=100, random_state=42)

    # Cross-validation for robust metrics (avoids F1=1.0 artifact on small data)
    cv = StratifiedKFold(
        n_splits=min(5, max(2, y.value_counts().min())), shuffle=True, random_state=42
    )
    y_pred_cv = cross_val_predict(clf, X, y, cv=cv)

    metrics = {
        "model": "RandomForest",
        "method": "cross_validation",
        "n_samples": len(df),
        "n_features": len(features),
        "features": features,
        "accuracy": float(accuracy_score(y, y_pred_cv)),
        "precision": float(precision_score(y, y_pred_cv, zero_division=0)),
        "recall": float(recall_score(y, y_pred_cv, zero_division=0)),
        "f1": float(f1_score(y, y_pred_cv, zero_division=0)),
        "confusion_matrix": confusion_matrix(y, y_pred_cv).tolist(),
    }

    diagnostics = label_integrity_diagnostics(X, y, clf, cv=cv, random_state=42)
    honesty = honesty_gate(
        accuracy=metrics["accuracy"],
        f1=metrics["f1"],
        majority_baseline=diagnostics["majority_baseline_accuracy"],
        shuffled_accuracy=diagnostics["shuffled_label_accuracy"],
        target_origin=target_origin,
    )

    metrics["target_origin"] = target_origin
    metrics["label_integrity"] = diagnostics
    metrics["honesty_gate"] = honesty

    if diagnostics["direct_leakage_check"] == "fail":
        logger.warning(
            "Potential leakage risk: shuffled-label accuracy %.3f exceeds majority baseline %.3f",
            diagnostics["shuffled_label_accuracy"],
            diagnostics["majority_baseline_accuracy"],
        )

    # Also fit on full data for feature importance
    clf.fit(X, y)
    importance = sorted(zip(features, clf.feature_importances_), key=lambda x: x[1], reverse=True)
    metrics["feature_importance"] = [
        {"feature": f, "importance": round(float(v), 4)} for f, v in importance[:10]
    ]

    with open(out_dir / "model_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info(
        "RF trained (CV). accuracy=%.3f f1=%.3f direct_leakage=%s honesty=%s trust=%d -> analytics/model_metrics.json",
        metrics["accuracy"],
        metrics["f1"],
        metrics["label_integrity"]["direct_leakage_check"],
        metrics["honesty_gate"]["status"],
        metrics["honesty_gate"]["trust_score"],
    )
    return clf, metrics


if __name__ == "__main__":
    run()
