"""
WooCommerce scraper adapter.
Use requests + BeautifulSoup for static/API; Playwright for dynamic pages if needed.
"""
from pathlib import Path
from src.scraping.base import BaseScraper, ProductRecord


class WooCommerceScraper(BaseScraper):
    """Scrape product data from a WooCommerce site."""

    def __init__(self, output_dir: Path, site_url: str | None = None):
        super().__init__(output_dir)
        self.site_url = site_url or ""

    def scrape(self) -> list[ProductRecord]:
        # TODO(Ismail): implement WooCommerce product extraction
        # - WooCommerce REST API if keys available, else scraping
        # - Emit ProductRecord with source_platform="woocommerce"
        return []
