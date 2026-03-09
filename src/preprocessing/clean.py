"""
Deterministic cleaning: dedupe, standardize prices, normalize text,
harmonize categories, handle missing values, numeric ratings/reviews.
"""
import pandas as pd


def remove_duplicates(df: pd.DataFrame, subset: list[str] | None = None) -> pd.DataFrame:
    """Remove duplicate rows. Default: key on source_platform, shop_name, product_id."""
    key = subset or ["source_platform", "shop_name", "product_id"]
    return df.drop_duplicates(subset=key, keep="first").reset_index(drop=True)


def standardize_prices(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure price columns are numeric; invalid/negative -> NaN."""
    out = df.copy()
    for col in ["price", "old_price"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
            out.loc[out[col] < 0, col] = pd.NA
    return out


def normalize_text_columns(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    """Strip and normalize whitespace in string columns."""
    cols = columns or [c for c in ["title", "description", "category", "brand", "availability"] if c in df.columns]
    out = df.copy()
    for c in cols:
        if out[c].dtype == object:
            out[c] = out[c].astype(str).str.strip().replace("nan", "")
    return out


def numeric_ratings_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """Convert rating and review_count to numeric; log invalid rows if needed."""
    out = df.copy()
    if "rating" in out.columns:
        out["rating"] = pd.to_numeric(out["rating"], errors="coerce")
    if "review_count" in out.columns:
        out["review_count"] = pd.to_numeric(out["review_count"], errors="coerce").fillna(0).astype(int)
    return out


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Full cleaning pipeline: dedupe, prices, text, ratings."""
    df = remove_duplicates(df)
    df = standardize_prices(df)
    df = normalize_text_columns(df)
    df = numeric_ratings_reviews(df)
    return df
