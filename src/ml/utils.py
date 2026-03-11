"""
Shared ML utilities: feature column selection, data loading.
Eliminates the 4x duplicated get_feature_columns() function.
"""

import numpy as np
import pandas as pd

from src.config import processed_dir

# Columns to exclude from numeric feature matrices
_NON_FEATURE_COLUMNS = frozenset(
    {
        "product_id",
        "product_url",
        "title",
        "description",
        "scraped_at",
        "source_platform",
        "shop_name",
        "category",
        "brand",
        "availability",
        "geography",
        "price_bucket",
        "high_potential",
    }
)


def get_feature_columns(
    df: pd.DataFrame,
    *,
    exclude_score: bool = False,
) -> list[str]:
    """Return numeric feature column names, excluding metadata/target columns.

    Args:
        df: DataFrame with product features.
        exclude_score: If True, also exclude 'score' and 'popularity_proxy'
            to prevent data leakage in supervised models.
    """
    exclude = set(_NON_FEATURE_COLUMNS)
    if exclude_score:
        exclude |= {"score", "popularity_proxy"}
    return [c for c in df.select_dtypes(include=[np.number]).columns if c not in exclude]


def load_features() -> pd.DataFrame:
    """Load the features parquet file."""
    path = processed_dir() / "features.parquet"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)
