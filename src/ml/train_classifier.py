"""
Supervised model: predict high-potential product (top 20% by heuristic score).
Baseline: RandomForestClassifier. Optional: XGBoost comparison.
"""
import json
import os
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix


def _data_dir() -> Path:
    return Path(os.environ.get("DATA_DIR", "data"))


def get_feature_columns(df: pd.DataFrame) -> list[str]:
    """Numeric features for training (exclude ids, text, target)."""
    exclude = {
        "product_id", "product_url", "title", "description", "scraped_at",
        "source_platform", "shop_name", "category", "brand", "availability",
        "geography", "price_bucket", "high_potential"
    }
    return [c for c in df.select_dtypes(include=[np.number]).columns if c not in exclude]


def run():
    root = _data_dir()
    processed_dir = root / "processed"
    analytics_dir = root / "analytics"
    analytics_dir.mkdir(parents=True, exist_ok=True)

    in_path = processed_dir / "features.parquet"
    if not in_path.exists():
        print("No features.parquet. Run features step first.")
        return
    df = pd.read_parquet(in_path)
    if df.empty or len(df) < 20:
        print("Not enough data for training.")
        return

    if "score" not in df.columns:
        from src.scoring.topk import compute_score
        df["score"] = compute_score(df)
    df["high_potential"] = (df["score"] >= df["score"].quantile(0.80)).astype(int)
    features = get_feature_columns(df)
    if not features:
        print("No numeric features found.")
        return
    X = df[features].fillna(0)
    y = df["high_potential"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
    }
    with open(analytics_dir / "model_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print("Classifier trained. Metrics -> analytics/model_metrics.json")
    return clf, metrics


if __name__ == "__main__":
    run()
