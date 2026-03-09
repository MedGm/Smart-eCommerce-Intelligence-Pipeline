"""
Validation and logging of invalid/missing rows.
"""

import pandas as pd


def validate_required(
    df: pd.DataFrame, required: list[str] | None = None
) -> pd.DataFrame:
    """Keep rows that have non-null values for required columns. Log drops."""
    required = required or ["source_platform", "shop_name", "product_id", "title"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    before = len(df)
    out = df.dropna(subset=required)
    dropped = before - len(out)
    if dropped:
        # In production: log to file or logger
        pass
    return out


def log_invalid_rows(df: pd.DataFrame, required: list[str]) -> None:
    """Optional: write invalid rows to a log for inspection."""
    # Placeholder: could write df[~valid_mask] to data/processed/invalid_rows.csv
    pass
