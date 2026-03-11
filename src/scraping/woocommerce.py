"""
WooCommerce scraper adapter (multi-store, Store API).

Fixes applied vs v1:
- Prices divided by 10^currency_minor_unit (typically cents → dollars).
- HTML stripped from descriptions via BeautifulSoup.
- Multi-store support via constructor params.

Dossier tools: requests, BeautifulSoup, WooCommerce REST API.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from src.scraping.base import BaseScraper, ProductRecord


class WooCommerceScraper(BaseScraper):
    """Scrape product data from a WooCommerce site using the Store API."""

    def __init__(
        self,
        output_dir: Path,
        site_url: str = "",
        shop_name: str = "Unknown",
        geography: str | None = None,
    ):
        super().__init__(output_dir)
        self.site_url = site_url.rstrip("/")
        self.shop_name = shop_name
        self.geography = geography
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0 Safari/537.36"
                )
            }
        )
        self._currency_minor_unit: int | None = None

    def _api_url(self, per_page: int, page: int) -> str:
        return f"{self.site_url}/wp-json/wc/store/v1/products?per_page={per_page}&page={page}"

    def _detect_currency_minor_unit(self, product: dict) -> int:
        """Detect how many decimal places to shift prices (usually 2 for USD/EUR)."""
        if self._currency_minor_unit is not None:
            return self._currency_minor_unit
        prices = product.get("prices") or {}
        unit = prices.get("currency_minor_unit")
        if unit is not None:
            try:
                self._currency_minor_unit = int(unit)
                return self._currency_minor_unit
            except (ValueError, TypeError):
                pass
        self._currency_minor_unit = 2
        return 2

    def _parse_price(self, product: dict) -> tuple[float | None, float | None]:
        """Extract current and old price, converting from minor units to dollars."""
        prices = product.get("prices") or {}
        divisor = 10 ** self._detect_currency_minor_unit(product)

        def _to_float(value: object) -> float | None:
            if value is None:
                return None
            try:
                return float(value) / divisor
            except (TypeError, ValueError):
                return None

        current = _to_float(prices.get("price"))
        regular = _to_float(prices.get("regular_price"))
        sale = _to_float(prices.get("sale_price"))

        price = current or sale or regular
        old_price = regular if sale and regular and sale < regular else None
        return price, old_price

    def _infer_category(self, product: dict) -> str | None:
        categories = product.get("categories") or []
        if categories:
            name = categories[0].get("name")
            if isinstance(name, str) and name.strip():
                return name.strip()
        return None

    def _strip_html(self, text: str) -> str:
        """Remove HTML tags from description text."""
        if not text:
            return ""
        return BeautifulSoup(text, "html.parser").get_text(separator=" ").strip()[:1000]

    def _availability(self, product: dict) -> str | None:
        stock_status = product.get("stock_status")
        if isinstance(stock_status, str) and stock_status:
            return stock_status
        return None

    def _rating_info(self, product: dict) -> tuple[float | None, int | None]:
        avg = product.get("average_rating")
        count = product.get("review_count")
        try:
            rating = float(avg) if avg not in (None, "", "0") else None
        except (TypeError, ValueError):
            rating = None
        try:
            reviews = int(count) if count not in (None, 0, "0") else None
        except (TypeError, ValueError):
            reviews = None
        return rating, reviews

    def scrape(self) -> list[ProductRecord]:
        if not self.site_url:
            print("WooCommerceScraper: no site_url configured, skipping.")
            return []

        print(f"WooCommerceScraper: starting {self.shop_name} ({self.site_url})")

        per_page = 40
        max_pages = 25
        records: list[ProductRecord] = []
        now = datetime.now(timezone.utc).isoformat()

        for page in range(1, max_pages + 1):
            url = self._api_url(per_page=per_page, page=page)
            try:
                resp = self.session.get(url, timeout=15)
            except requests.RequestException as exc:
                print(f"  [{self.shop_name}] Error on page {page}: {exc}")
                break

            if resp.status_code != 200:
                print(f"  [{self.shop_name}] Page {page} status {resp.status_code}, stopping.")
                break

            try:
                data = resp.json()
            except ValueError:
                print(f"  [{self.shop_name}] Invalid JSON on page {page}, stopping.")
                break

            if not isinstance(data, list) or not data:
                break

            for product in data:
                product_id = str(product.get("id"))
                product_url = product.get("permalink") or product.get("link") or ""
                title = product.get("name") or ""
                raw_desc = product.get("description") or product.get("short_description") or ""
                description = self._strip_html(raw_desc)

                if not product_id or not title or not product_url:
                    continue

                category = self._infer_category(product)
                price, old_price = self._parse_price(product)
                availability = self._availability(product)
                rating, review_count = self._rating_info(product)

                record = ProductRecord(
                    source_platform="woocommerce",
                    shop_name=self.shop_name,
                    product_id=product_id,
                    product_url=product_url,
                    title=title,
                    description=description,
                    category=category,
                    brand=self.shop_name,
                    price=price,
                    old_price=old_price,
                    availability=availability,
                    rating=rating,
                    review_count=review_count,
                    geography=self.geography,
                    scraped_at=now,
                )
                records.append(record)

            print(f"  [{self.shop_name}] Page {page}: {len(data)} items (total: {len(records)})")
            if len(data) < per_page:
                break

        print(f"WooCommerceScraper: {self.shop_name} done — {len(records)} products")
        return records
