"""
Clustering: KMeans for product segments. Export cluster labels and PCA viz data.
"""
import os
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score


def _data_dir() -> Path:
    return Path(os.environ.get("DATA_DIR", "data"))


def get_feature_columns(df: pd.DataFrame) -> list[str]:
    exclude = {
        "product_id", "product_url", "title", "description", "scraped_at",
        "source_platform", "shop_name", "category", "brand", "availability",
        "geography", "price_bucket", "high_potential", "score"
    }
    return [c for c in df.select_dtypes(include=[np.number]).columns if c not in exclude]


def run(n_clusters: int = 4):
    root = _data_dir()
    processed_dir = root / "processed"
    analytics_dir = root / "analytics"
    analytics_dir.mkdir(parents=True, exist_ok=True)

    in_path = processed_dir / "features.parquet"
    if not in_path.exists():
        print("No features.parquet.")
        return
    df = pd.read_parquet(in_path)
    if df.empty or len(df) < n_clusters:
        print("Not enough data for clustering.")
        return
    features = get_feature_columns(df)
    if not features:
        print("No numeric features.")
        return
    X = df[features].fillna(0)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df = df.copy()
    df["cluster"] = km.fit_predict(X_scaled)
    if "score" not in df.columns:
        from src.scoring.topk import compute_score
        df["score"] = compute_score(df)
    cols = ["product_id", "title", "category", "shop_name", "cluster", "score"]
    df[[c for c in cols if c in df.columns]].to_csv(analytics_dir / "clusters.csv", index=False)
    sil = silhouette_score(X_scaled, df["cluster"])
    pca = PCA(n_components=2, random_state=42)
    X2 = pca.fit_transform(X_scaled)
    viz = pd.DataFrame({"pc1": X2[:, 0], "pc2": X2[:, 1], "cluster": df["cluster"]})
    viz.to_csv(analytics_dir / "pca_viz.csv", index=False)
    print(f"Clustering done: clusters.csv, pca_viz.csv (silhouette={sil:.3f})")
    return df


if __name__ == "__main__":
    run()
