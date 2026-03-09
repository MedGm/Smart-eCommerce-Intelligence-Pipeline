"""
Transformations for feature prep: category harmonization, fill missing, etc.
"""
import pandas as pd


def harmonize_categories(df: pd.DataFrame, category_col: str = "category") -> pd.DataFrame:
    """Normalize category names (lowercase, strip, map aliases if needed)."""
    if category_col not in df.columns:
        return df
    out = df.copy()
    out[category_col] = out[category_col].astype(str).str.strip().str.lower()
    return out


def fill_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Sensible defaults for missing values (avoid breaking downstream)."""
    out = df.copy()
    # Optional: fill category/brand with "unknown", numeric with 0 or median
    for c in ["category", "brand", "availability"]:
        if c in out.columns and out[c].dtype == object:
            out[c] = out[c].fillna("unknown")
    return out
