"""
Validation and logging of invalid/missing rows.
"""

import pandas as pd

from src.config import get_logger, processed_dir

logger = get_logger(__name__)


def validate_required(df: pd.DataFrame, required: list[str] | None = None) -> pd.DataFrame:
    """Keep rows that have non-null values for required columns. Log drops."""
    required = required or ["source_platform", "shop_name", "product_id", "title"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    before = len(df)
    out = df.dropna(subset=required)
    dropped = before - len(out)
    if dropped:
        logger.warning("Dropped %d rows with missing required fields.", dropped)
        log_invalid_rows(df, required)
    return out


def log_invalid_rows(df: pd.DataFrame, required: list[str]) -> None:
    """Write invalid rows to a log CSV for inspection."""
    mask = df[required].isna().any(axis=1)
    invalid = df[mask]
    if invalid.empty:
        return
    log_path = processed_dir() / "invalid_rows.csv"
    invalid.to_csv(log_path, index=False)
    logger.info("Wrote %d invalid rows to %s", len(invalid), log_path)
