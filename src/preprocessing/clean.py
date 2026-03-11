"""
Deterministic cleaning: dedupe, standardize prices, normalize text,
harmonize categories, handle missing values, numeric ratings/reviews,
strip residual HTML from descriptions.
"""

import pandas as pd
from bs4 import BeautifulSoup


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


def strip_html(text: str) -> str:
    """Remove any residual HTML tags from a string."""
    if not isinstance(text, str) or not text:
        return ""
    if "<" in text and ">" in text:
        return BeautifulSoup(text, "html.parser").get_text(separator=" ").strip()
    return text.strip()


def normalize_text_columns(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    """Strip whitespace and residual HTML from text columns."""
    cols = columns or [
        c for c in ["title", "description", "category", "brand", "availability"] if c in df.columns
    ]
    out = df.copy()
    for c in cols:
        if out[c].dtype == object:
            out[c] = out[c].fillna("").astype(str).apply(strip_html)
            out[c] = out[c].replace({"nan": "", "None": "", "none": ""})
    return out


def numeric_ratings_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """Convert rating and review_count to numeric."""
    out = df.copy()
    if "rating" in out.columns:
        out["rating"] = pd.to_numeric(out["rating"], errors="coerce")
    if "review_count" in out.columns:
        out["review_count"] = (
            pd.to_numeric(out["review_count"], errors="coerce").fillna(0).astype(int)
        )
    return out


def clean_categories(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize categories: lowercase, strip, replace empty/none with NaN."""
    out = df.copy()
    if "category" in out.columns:
        out["category"] = out["category"].fillna("").astype(str).str.strip().str.lower()
        out.loc[out["category"].isin(["", "none", "nan", "unknown"]), "category"] = pd.NA
    return out


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Full cleaning pipeline."""
    df = remove_duplicates(df)
    df = standardize_prices(df)
    df = normalize_text_columns(df)
    df = numeric_ratings_reviews(df)
    df = clean_categories(df)
    return df
