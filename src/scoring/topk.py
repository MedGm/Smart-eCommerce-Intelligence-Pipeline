"""
Top-K scoring engine. Explainable formula:
  score = 0.35*rating_norm + 0.30*review_count_norm + 0.20*availability_norm + 0.15*discount_norm
Compute Top-K overall, per category, per shop.
"""

import os
from pathlib import Path

import pandas as pd


def _data_dir() -> Path:
    return Path(os.environ.get("DATA_DIR", "data"))


# Weights (document for oral defense)
WEIGHTS = {
    "rating": 0.35,
    "review_count": 0.30,
    "availability": 0.20,
    "discount": 0.15,
}


def normalize(series: pd.Series) -> pd.Series:
    """Min-max to [0, 1]."""
    s = series.astype(float)
    lo, hi = s.min(), s.max()
    if hi <= lo:
        return pd.Series(0.5, index=series.index)
    return (s - lo) / (hi - lo)


def compute_score(df: pd.DataFrame) -> pd.Series:
    """Single explainable score per product."""
    rating = df.get("rating", pd.Series(0.0, index=df.index)).fillna(0)
    rating_norm = normalize(rating / 5.0)
    review_count = df.get("review_count", 0).fillna(0).astype(float)
    review_norm = normalize(review_count)
    availability = (
        df.get("is_in_stock", True).astype(float)
        if "is_in_stock" in df.columns
        else 1.0
    )
    if isinstance(availability, pd.Series):
        availability_norm = availability
    else:
        availability_norm = pd.Series(1.0, index=df.index)
    discount = df.get("discount_pct", 0).fillna(0)
    discount_norm = normalize(discount)
    return (
        WEIGHTS["rating"] * rating_norm
        + WEIGHTS["review_count"] * review_norm
        + WEIGHTS["availability"] * availability_norm
        + WEIGHTS["discount"] * discount_norm
    )


def topk_overall(df: pd.DataFrame, k: int = 50) -> pd.DataFrame:
    return df.nlargest(k, "score").reset_index(drop=True)


def topk_per_category(df: pd.DataFrame, k: int = 10) -> pd.DataFrame:
    if "category" not in df.columns:
        return pd.DataFrame()
    return (
        df.groupby("category", group_keys=False)
        .apply(lambda g: g.nlargest(k, "score"))
        .reset_index(drop=True)
    )


def topk_per_shop(df: pd.DataFrame, k: int = 10) -> pd.DataFrame:
    key = (
        ["source_platform", "shop_name"]
        if "shop_name" in df.columns
        else ["source_platform"]
    )
    return (
        df.groupby(key, group_keys=False)
        .apply(lambda g: g.nlargest(k, "score"))
        .reset_index(drop=True)
    )


def run(k_overall: int = 50, k_per: int = 10):
    root = _data_dir()
    processed_dir = root / "processed"
    analytics_dir = root / "analytics"
    analytics_dir.mkdir(parents=True, exist_ok=True)

    in_path = processed_dir / "features.parquet"
    if not in_path.exists():
        print("No features.parquet. Run features step first.")
        return
    df = pd.read_parquet(in_path)
    if df.empty:
        print("Empty features. Skipping scoring.")
        return
    df = df.copy()
    df["score"] = compute_score(df)

    topk_overall(df, k_overall).to_csv(analytics_dir / "topk_products.csv", index=False)
    topk_per_category(df, k_per).to_csv(
        analytics_dir / "topk_per_category.csv", index=False
    )
    topk_per_shop(df, k_per).to_csv(analytics_dir / "topk_per_shop.csv", index=False)
    print("Scoring done: topk_products.csv, topk_per_category.csv, topk_per_shop.csv")
    return df


if __name__ == "__main__":
    run()
