"""
Feature engineering: discount_pct, price_zscore_by_category, rating_weighted_reviews,
is_in_stock, description_length, title_length, shop_product_count, category_frequency,
price_bucket, popularity_proxy. No fake sales data.
"""

import os
from pathlib import Path

import pandas as pd
import numpy as np


def _data_dir() -> Path:
    return Path(os.environ.get("DATA_DIR", "data"))


def discount_pct(df: pd.DataFrame) -> pd.Series:
    """Discount percentage from old_price and price."""
    if "old_price" not in df.columns or "price" not in df.columns:
        return pd.Series(0.0, index=df.index)
    p, op = df["price"], df["old_price"]
    return np.where(op > 0, (1 - p / op).clip(0, 1), 0.0)


def price_zscore_by_category(df: pd.DataFrame) -> pd.Series:
    """Z-score of price within category."""
    if "price" not in df.columns or "category" not in df.columns:
        return pd.Series(0.0, index=df.index)
    return (
        df.groupby("category")["price"]
        .transform(lambda x: (x - x.mean()) / x.std() if x.std() > 0 else 0.0)
        .fillna(0)
    )


def rating_weighted_reviews(df: pd.DataFrame) -> pd.Series:
    """Proxy: rating * log1p(review_count)."""
    r = df.get("rating", pd.Series(0.0, index=df.index)).fillna(0)
    n = df.get("review_count", 0).fillna(0)
    return r * np.log1p(n.astype(float))


def is_in_stock(df: pd.DataFrame) -> pd.Series:
    """Boolean from availability (in stock / available)."""
    if "availability" not in df.columns:
        return pd.Series(True, index=df.index)
    av = df["availability"].astype(str).str.lower()
    return av.str.contains("in stock|available|yes", na=False)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add all engineered features."""
    out = df.copy()
    out["discount_pct"] = discount_pct(out)
    out["price_zscore_by_category"] = price_zscore_by_category(out)
    out["rating_weighted_reviews"] = rating_weighted_reviews(out)
    out["is_in_stock"] = is_in_stock(out)
    out["description_length"] = (
        out.get("description", pd.Series("", index=out.index)).astype(str).str.len()
    )
    out["title_length"] = (
        out.get("title", pd.Series("", index=out.index)).astype(str).str.len()
    )
    out["shop_product_count"] = out.groupby(["source_platform", "shop_name"]).transform(
        "size"
    )
    out["category_frequency"] = out.groupby("category")["product_id"].transform("count")
    # Price bucket (e.g. quartiles)
    try:
        out["price_bucket"] = pd.qcut(
            out["price"].fillna(0),
            q=4,
            labels=["low", "mid_low", "mid_high", "high"],
            duplicates="drop",
        ).astype(str)
    except (ValueError, TypeError):
        out["price_bucket"] = "mid"
    # Popularity proxy: no sales data; use rating, reviews, stock, discount
    r_norm = out["rating"].fillna(0) / 5.0
    rev = out.get("review_count", 0).fillna(0)
    rev_norm = rev / (rev.max() + 1e-6) if rev.max() > 0 else 0
    out["popularity_proxy"] = (
        0.35 * r_norm
        + 0.30 * rev_norm
        + 0.20 * out["is_in_stock"].astype(float)
        + 0.15 * out["discount_pct"]
    )
    return out


def run():
    root = _data_dir()
    processed_dir = root / "processed"
    in_path = processed_dir / "cleaned_products.parquet"
    if not in_path.exists():
        print("No cleaned_products.parquet. Run preprocessing first.")
        return pd.DataFrame()
    df = pd.read_parquet(in_path)
    df = build_features(df)
    out_path = processed_dir / "features.parquet"
    df.to_parquet(out_path, index=False)
    print(f"Features built: {out_path}")
    return df


if __name__ == "__main__":
    run()
