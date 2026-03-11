"""
Shopify scraper adapter (multi-store, with product detail enrichment).

Strategy:
1. Playwright: crawl collection pages, scroll for lazy-load, extract product slugs.
2. requests: for each slug, fetch /products/<slug>.json for structured data
   (price, description, category, rating, variants).
3. Map to ProductRecord.

This covers dossier tools: Playwright (dynamic), requests (static), BeautifulSoup (fallback).
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from src.config import DEFAULT_USER_AGENT, SCRAPING_DELAY, SCRAPING_TIMEOUT
from src.scraping.base import BaseScraper, ProductRecord

HEADERS = {
    "User-Agent": DEFAULT_USER_AGENT,
}


class ShopifyScraper(BaseScraper):
    """Scrape product data from a Shopify store."""

    def __init__(
        self,
        output_dir: Path,
        store_url: str = "",
        shop_name: str = "Unknown",
        geography: str | None = None,
        collections: list[str] | None = None,
    ):
        super().__init__(output_dir)
        self.store_url = store_url.rstrip("/")
        self.shop_name = shop_name
        self.geography = geography
        self.collections = collections or ["all"]

    def _collection_urls(self) -> list[str]:
        return [f"{self.store_url}/collections/{c}" for c in self.collections]

    def _extract_product_slugs_playwright(self) -> list[dict]:
        """Use Playwright to crawl collections and extract product slugs + collection context."""
        try:
            from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
            from playwright.sync_api import sync_playwright
        except ImportError:
            print(f"  [{self.shop_name}] Playwright not installed, skipping dynamic scraping.")
            return []

        results = []
        seen_slugs: set[str] = set()

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(user_agent=HEADERS["User-Agent"])
                page = context.new_page()

                for collection_url in self._collection_urls():
                    collection_name = collection_url.rstrip("/").split("/")[-1]
                    try:
                        print(f"  [{self.shop_name}] Crawling {collection_url}")
                        page.goto(
                            collection_url,
                            timeout=40_000,
                            wait_until="domcontentloaded",
                        )
                    except PlaywrightTimeoutError:
                        print(f"  [{self.shop_name}] Timeout: {collection_url}")
                        continue

                    for _ in range(8):
                        page.mouse.wheel(0, 2000)
                        page.wait_for_timeout(800)

                    anchors = page.query_selector_all("a[href*='/products/']")
                    for a in anchors:
                        href = a.get_attribute("href") or ""
                        if "/products/" not in href:
                            continue
                        slug = href.split("/products/")[-1].split("?")[0].split("#")[0].rstrip("/")
                        if not slug or slug in seen_slugs:
                            continue
                        seen_slugs.add(slug)
                        results.append({"slug": slug, "collection": collection_name})

                    print(
                        f"  [{self.shop_name}] Found {len(anchors)} anchors, {len(seen_slugs)} unique slugs so far"
                    )

                browser.close()
        except Exception as exc:
            print(f"  [{self.shop_name}] Playwright error: {exc}")

        return results

    def _fetch_product_json(self, slug: str) -> dict | None:
        """Fetch structured product data from Shopify's /products/<slug>.json endpoint."""
        url = f"{self.store_url}/products/{slug}.json"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=SCRAPING_TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("product", data)
        except (requests.RequestException, ValueError):
            pass
        return None

    def _fetch_product_html_fallback(self, slug: str) -> dict:
        """Fallback: parse product page HTML with BS4 for meta tags / JSON-LD."""
        url = f"{self.store_url}/products/{slug}"
        fields: dict = {}
        try:
            resp = requests.get(url, headers=HEADERS, timeout=SCRAPING_TIMEOUT)
            if resp.status_code != 200:
                return fields
            soup = BeautifulSoup(resp.text, "html.parser")

            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                fields["description"] = meta_desc["content"].strip()[:500]

            og_price = soup.find("meta", attrs={"property": "og:price:amount"})
            if og_price and og_price.get("content"):
                try:
                    fields["price"] = float(og_price["content"])
                except (ValueError, TypeError):
                    pass

            og_avail = soup.find("meta", attrs={"property": "og:availability"})
            if og_avail and og_avail.get("content"):
                fields["availability"] = og_avail["content"]

            import json as _json

            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    ld = _json.loads(script.string or "")
                    if isinstance(ld, dict) and ld.get("@type") == "Product":
                        agg = ld.get("aggregateRating") or {}
                        if agg.get("ratingValue"):
                            fields["rating"] = float(agg["ratingValue"])
                        if agg.get("reviewCount"):
                            fields["review_count"] = int(agg["reviewCount"])
                        if ld.get("category"):
                            fields["category"] = str(ld["category"])
                except (ValueError, TypeError, _json.JSONDecodeError):
                    continue
        except requests.RequestException:
            pass
        return fields

    def _product_json_to_record(
        self, pdata: dict, slug: str, collection: str, now: str
    ) -> ProductRecord | None:
        """Convert Shopify product JSON to ProductRecord."""
        title = pdata.get("title", "").strip()
        if not title:
            return None

        body_html = pdata.get("body_html") or ""
        description = BeautifulSoup(body_html, "html.parser").get_text(separator=" ").strip()[:1000]

        category = pdata.get("product_type") or None
        if not category or category.strip() == "":
            category = collection.replace("-", " ").title() if collection != "all" else None

        brand = pdata.get("vendor") or self.shop_name

        price: float | None = None
        old_price: float | None = None
        variants = pdata.get("variants") or []
        if variants:
            v = variants[0]
            try:
                price = float(v.get("price", 0))
            except (ValueError, TypeError):
                pass
            cap = v.get("compare_at_price")
            if cap:
                try:
                    old_price = float(cap)
                except (ValueError, TypeError):
                    pass

        availability = None
        if variants:
            available_count = sum(1 for v in variants if v.get("available"))
            availability = "in stock" if available_count > 0 else "out of stock"

        product_id = str(pdata.get("id", slug))
        product_url = f"{self.store_url}/products/{slug}"

        return ProductRecord(
            source_platform="shopify",
            shop_name=self.shop_name,
            product_id=product_id,
            product_url=product_url,
            title=title,
            description=description,
            category=category,
            brand=brand,
            price=price,
            old_price=old_price,
            availability=availability,
            rating=None,
            review_count=None,
            geography=self.geography,
            scraped_at=now,
        )

    def scrape(self) -> list[ProductRecord]:
        if not self.store_url:
            print("ShopifyScraper: no store_url configured, skipping.")
            return []

        print(f"ShopifyScraper: starting {self.shop_name} ({self.store_url})")
        now = datetime.now(timezone.utc).isoformat()
        records: list[ProductRecord] = []

        slug_info = self._extract_product_slugs_playwright()
        print(f"  [{self.shop_name}] Collected {len(slug_info)} product slugs, enriching...")

        for i, info in enumerate(slug_info):
            slug = info["slug"]
            collection = info["collection"]

            pdata = self._fetch_product_json(slug)
            if pdata:
                record = self._product_json_to_record(pdata, slug, collection, now)
                if record:
                    # Try to get rating from HTML fallback (JSON endpoint doesn't have ratings)
                    html_fields = self._fetch_product_html_fallback(slug)
                    if html_fields.get("rating") is not None:
                        record.rating = html_fields["rating"]
                    if html_fields.get("review_count") is not None:
                        record.review_count = html_fields["review_count"]
                    records.append(record)
            else:
                html_fields = self._fetch_product_html_fallback(slug)
                if html_fields:
                    record = ProductRecord(
                        source_platform="shopify",
                        shop_name=self.shop_name,
                        product_id=slug,
                        product_url=f"{self.store_url}/products/{slug}",
                        title=slug.replace("-", " ").title(),
                        description=html_fields.get("description", ""),
                        category=collection.replace("-", " ").title()
                        if collection != "all"
                        else None,
                        brand=self.shop_name,
                        price=html_fields.get("price"),
                        old_price=None,
                        availability=html_fields.get("availability"),
                        rating=html_fields.get("rating"),
                        review_count=html_fields.get("review_count"),
                        geography=self.geography,
                        scraped_at=now,
                    )
                    records.append(record)

            if (i + 1) % 20 == 0:
                print(f"  [{self.shop_name}] Enriched {i + 1}/{len(slug_info)} products")
            time.sleep(SCRAPING_DELAY)

        print(f"ShopifyScraper: {self.shop_name} done — {len(records)} products")
        return records
