"""
Orchestrator: run all Shopify and WooCommerce scrapers from stores.py config.
Saves raw JSON per store, then combines into platform-level files.
"""

from __future__ import annotations

import json

from src.config import data_dir, get_logger
from src.scraping.base import ProductRecord
from src.scraping.shopify import ShopifyScraper
from src.scraping.stores import SHOPIFY_STORES, WOOCOMMERCE_STORES
from src.scraping.woocommerce import WooCommerceScraper

logger = get_logger(__name__)


def run():
    raw = data_dir() / "raw"
    all_records: list[ProductRecord] = []

    # ── Shopify stores ──
    shopify_dir = raw / "shopify"
    shopify_dir.mkdir(parents=True, exist_ok=True)
    shopify_all: list[dict] = []

    for store in SHOPIFY_STORES:
        scraper = ShopifyScraper(
            output_dir=shopify_dir,
            store_url=store["url"],
            shop_name=store["name"],
            geography=store.get("geography"),
            collections=store.get("collections", ["all"]),
        )
        records = scraper.scrape()
        if records:
            safe_name = store["name"].lower().replace(" ", "_").replace("'", "")
            scraper.save(records, f"{safe_name}.json")
            shopify_all.extend([r.to_dict() for r in records])
            all_records.extend(records)

    with open(shopify_dir / "products.json", "w", encoding="utf-8") as f:
        json.dump(shopify_all, f, indent=2, ensure_ascii=False)

    # ── WooCommerce stores ──
    wc_dir = raw / "woocommerce"
    wc_dir.mkdir(parents=True, exist_ok=True)
    wc_all: list[dict] = []

    for store in WOOCOMMERCE_STORES:
        scraper = WooCommerceScraper(
            output_dir=wc_dir,
            site_url=store["url"],
            shop_name=store["name"],
            geography=store.get("geography"),
        )
        records = scraper.scrape()
        if records:
            safe_name = store["name"].lower().replace(" ", "_").replace("'", "")
            scraper.save(records, f"{safe_name}.json")
            wc_all.extend([r.to_dict() for r in records])
            all_records.extend(records)

    with open(wc_dir / "products.json", "w", encoding="utf-8") as f:
        json.dump(wc_all, f, indent=2, ensure_ascii=False)

    logger.info(
        "Scraping done: %d products total across %d stores.",
        len(all_records),
        len(SHOPIFY_STORES) + len(WOOCOMMERCE_STORES),
    )
    return all_records


if __name__ == "__main__":
    run()
