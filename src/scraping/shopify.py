"""
Shopify scraper adapter.
Use Playwright for dynamic pages, requests + BeautifulSoup for static/API where applicable.
"""
from pathlib import Path
from src.scraping.base import BaseScraper, ProductRecord


class ShopifyScraper(BaseScraper):
    """Scrape product data from a Shopify store."""

    def __init__(self, output_dir: Path, store_url: str | None = None):
        super().__init__(output_dir)
        self.store_url = store_url or ""

    def scrape(self) -> list[ProductRecord]:
        # TODO(Ismail): implement Shopify product extraction
        # - Use Playwright for JS-rendered product pages if needed
        # - Or Shopify Storefront API / admin API if available
        # - Emit ProductRecord with source_platform="shopify"
        return []
