"""
Run full preprocessing: load raw JSON from data/raw, clean, validate, transform, write processed.
Reproducible: same raw input -> same processed output.
"""

import json

import pandas as pd

from src.config import data_dir, get_logger, processed_dir
from src.preprocessing.clean import clean
from src.preprocessing.transform import fill_missing, harmonize_categories
from src.preprocessing.validate import validate_required

logger = get_logger(__name__)


def load_raw(root=None) -> pd.DataFrame:
    """Load all raw product JSONs from raw/shopify and raw/woocommerce."""
    root = root or data_dir()
    raw = root / "raw"
    rows = []
    for platform in ("shopify", "woocommerce"):
        platform_dir = raw / platform
        if not platform_dir.exists():
            continue
        for path in platform_dir.glob("**/*.json"):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    rows.extend(data)
                else:
                    rows.append(data)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def run():
    root = data_dir()
    p_dir = processed_dir()
    p_dir.mkdir(parents=True, exist_ok=True)

    df = load_raw(root)
    if df.empty:
        logger.warning("No raw data found. Run scrapers first. Writing empty cleaned output.")
        df = pd.DataFrame(
            columns=[
                "source_platform",
                "shop_name",
                "product_id",
                "product_url",
                "title",
                "description",
                "category",
                "brand",
                "price",
                "old_price",
                "availability",
                "rating",
                "review_count",
                "geography",
                "scraped_at",
            ]
        )
    else:
        df = clean(df)
        df = validate_required(df)
        df = harmonize_categories(df)
        df = fill_missing(df)

    out_path = p_dir / "cleaned_products.parquet"
    df.to_parquet(out_path, index=False)
    logger.info("Preprocessing done: %d rows -> %s", len(df), out_path)
    return df


if __name__ == "__main__":
    run()
