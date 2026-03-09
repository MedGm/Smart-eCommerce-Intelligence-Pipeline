"""
Central place for ML evaluation (classification + clustering metrics).
Used by train_classifier and cluster_products; can be called from pipeline.
"""
# Evaluation logic lives in train_classifier (metrics dict) and cluster_products (silhouette).
# This module can aggregate or re-export for report/dashboard.
def aggregate_metrics(analytics_dir):
    """Load model_metrics.json and clustering outputs for dashboard/report."""
    import json
    from pathlib import Path
    p = Path(analytics_dir)
    out = {}
    if (p / "model_metrics.json").exists():
        with open(p / "model_metrics.json") as f:
            out["classification"] = json.load(f)
    return out
