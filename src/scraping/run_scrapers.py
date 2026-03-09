"""
Orchestrator: run Shopify and WooCommerce scrapers in sequence, write raw JSON.
"""

import os
from pathlib import Path

from src.scraping.base import ProductRecord
from src.scraping.shopify import ShopifyScraper
from src.scraping.woocommerce import WooCommerceScraper


def _data_dir() -> Path:
    base = os.environ.get("DATA_DIR", "data")
    return Path(base)


def run():
    root = _data_dir()
    raw = root / "raw"
    all_records: list[ProductRecord] = []

    shopify_dir = raw / "shopify"
    shopify = ShopifyScraper(shopify_dir, store_url=os.environ.get("SHOPIFY_STORE"))
    records = shopify.scrape()
    if records:
        shopify.save(records, "products.json")
        all_records.extend(records)

    wc_dir = raw / "woocommerce"
    wc = WooCommerceScraper(wc_dir, site_url=os.environ.get("WOOCOMMERCE_URL"))
    records = wc.scrape()
    if records:
        wc.save(records, "products.json")
        all_records.extend(records)

    print(f"Scraping done: {len(all_records)} products total.")
    return all_records


if __name__ == "__main__":
    run()
