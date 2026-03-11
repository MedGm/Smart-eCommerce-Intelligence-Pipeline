"""
WooCommerce scraper adapter for the Store API.

For this project we target Dan-O's Seasoning (https://danosseasoning.com)
and use the public Store API endpoint:

    /wp-json/wc/store/v1/products

The goal is to fetch enough pages to reach ~300+ products when possible and
map each JSON object to the shared ProductRecord schema.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import List

import requests

from src.scraping.base import BaseScraper, ProductRecord


class WooCommerceScraper(BaseScraper):
    """Scrape product data from a WooCommerce site using the Store API."""

    def __init__(self, output_dir: Path, site_url: str | None = None):
        super().__init__(output_dir)
        # Normalise URL (no trailing slash)
        self.site_url = (site_url or "").rstrip("/")
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

    def _api_url(self, per_page: int, page: int) -> str:
        return f"{self.site_url}/wp-json/wc/store/v1/products?per_page={per_page}&page={page}"

    def _infer_category(self, product: dict) -> str | None:
        # WooCommerce Store API often has "categories" as a list of { id, name, slug }
        categories = product.get("categories") or []
        if categories:
            # Use the first category name
            name = categories[0].get("name")
            if isinstance(name, str) and name.strip():
                return name.strip()
        return None

    def _infer_brand(self, product: dict) -> str | None:
        # Dan-O's is essentially its own brand; keep generic logic in case of reuse.
        # Some stores put brand in "brands" taxonomy or attributes – keep this simple for now.
        return "Dan-O's Seasoning"

    def _parse_price(self, product: dict) -> tuple[float | None, float | None]:
        """
        Try to extract current price and old (regular) price.
        Store API commonly exposes:
          - prices -> { regular_price, sale_price, price, currency_code, ... }
        """
        prices = product.get("prices") or {}

        # price is usually the active price (possibly sale)
        def _to_float(value: object) -> float | None:
            if value is None:
                return None
            try:
                return float(value)
            except (TypeError, ValueError):
                return None

        current = _to_float(prices.get("price"))
        regular = _to_float(prices.get("regular_price"))
        sale = _to_float(prices.get("sale_price"))

        price = current or sale or regular
        old_price = regular if sale and regular and sale < regular else None
        return price, old_price

    def _availability(self, product: dict) -> str | None:
        # stock_status is often "instock" / "outofstock"
        stock_status = product.get("stock_status")
        if isinstance(stock_status, str) and stock_status:
            return stock_status
        return None

    def _rating_info(self, product: dict) -> tuple[float | None, int | None]:
        avg = product.get("average_rating")
        count = product.get("review_count")
        try:
            rating = float(avg) if avg not in (None, "") else None
        except (TypeError, ValueError):
            rating = None
        try:
            reviews = int(count) if count is not None else None
        except (TypeError, ValueError):
            reviews = None
        return rating, reviews

    def scrape(self) -> List[ProductRecord]:
        """
        Fetch products from the WooCommerce Store API with simple pagination.

        We stop when:
          - an API call returns an empty list
          - or we reach max_pages
        """
        if not self.site_url:
            print("WooCommerceScraper: no site_url configured, skipping.")
            return []

        per_page = 40
        max_pages = 20  # theoretical max 800 products if all pages are full
        records: List[ProductRecord] = []

        now = datetime.now(timezone.utc).isoformat()
        shop_name = "Dan-O's Seasoning"

        for page in range(1, max_pages + 1):
            url = self._api_url(per_page=per_page, page=page)
            try:
                resp = self.session.get(url, timeout=15)
            except requests.RequestException as exc:
                print(f"WooCommerceScraper: error fetching page {page}: {exc}")
                break

            if resp.status_code != 200:
                print(
                    f"WooCommerceScraper: page {page} returned status "
                    f"{resp.status_code}, stopping."
                )
                break

            try:
                data = resp.json()
            except ValueError:
                print(f"WooCommerceScraper: invalid JSON on page {page}, stopping.")
                break

            if not isinstance(data, list) or not data:
                # No more products
                break

            for product in data:
                # Basic required fields
                product_id = str(product.get("id"))
                product_url = product.get("permalink") or product.get("link") or ""
                title = product.get("name") or ""
                description = (
                    product.get("description") or product.get("short_description") or ""
                )

                if not product_id or not title or not product_url:
                    # Skip incomplete rows – better to have clean data
                    continue

                category = self._infer_category(product)
                brand = self._infer_brand(product)
                price, old_price = self._parse_price(product)
                availability = self._availability(product)
                rating, review_count = self._rating_info(product)

                record = ProductRecord(
                    source_platform="woocommerce",
                    shop_name=shop_name,
                    product_id=product_id,
                    product_url=product_url,
                    title=title,
                    description=description,
                    category=category,
                    brand=brand,
                    price=price,
                    old_price=old_price,
                    availability=availability,
                    rating=rating,
                    review_count=review_count,
                    geography=None,
                    scraped_at=now,
                )
                records.append(record)

            # If the page wasn't full, chances are we've reached the end
            if len(data) < per_page:
                break

        print(
            f"WooCommerceScraper: fetched {len(records)} products from {self.site_url}"
        )
        return records
