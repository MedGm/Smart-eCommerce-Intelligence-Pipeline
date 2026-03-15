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
from src.scraping.html_fallback import extract_product_fields_from_html

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
            fields = extract_product_fields_from_html(resp.text, product_url=url)
        except requests.RequestException:
            pass
        return fields

    def _taxonomy_evidence_from_product_json(
        self, pdata: dict, collection: str, product_url: str
    ) -> dict:
        product_type = pdata.get("product_type")
        tags = pdata.get("tags")
        tags_present = False
        if isinstance(tags, list):
            tags_present = len(tags) > 0
        elif isinstance(tags, str):
            tags_present = bool(tags.strip())

        product_type_present = isinstance(product_type, str) and bool(product_type.strip())
        url_hint_present = "/collections/" in product_url.lower() or (
            collection and collection != "all"
        )

        sources: list[str] = []
        if product_type_present:
            sources.append("product_type")
        if tags_present:
            sources.append("tags")
        if url_hint_present:
            sources.append("url_hint")

        strength = "none"
        if product_type_present:
            strength = "medium"
        elif tags_present or url_hint_present:
            strength = "low"

        return {
            "taxonomy_breadcrumb_present": False,
            "taxonomy_breadcrumb_count": None,
            "taxonomy_jsonld_category_present": False,
            "taxonomy_jsonld_breadcrumb_present": False,
            "taxonomy_product_type_present": product_type_present,
            "taxonomy_tags_present": tags_present,
            "taxonomy_url_hint_present": url_hint_present,
            "taxonomy_sources_detected": "|".join(sorted(sources)) if sources else None,
            "taxonomy_evidence_strength": strength,
            "category_path_raw": None,
            "category_leaf_raw": None,
        }

    def _merge_taxonomy_evidence(self, primary: dict, fallback: dict) -> dict:
        merged = primary.copy()
        bool_keys = [
            "taxonomy_breadcrumb_present",
            "taxonomy_jsonld_category_present",
            "taxonomy_jsonld_breadcrumb_present",
            "taxonomy_product_type_present",
            "taxonomy_tags_present",
            "taxonomy_url_hint_present",
        ]
        for key in bool_keys:
            merged[key] = bool(primary.get(key)) or bool(fallback.get(key))

        primary_count = primary.get("taxonomy_breadcrumb_count")
        fallback_count = fallback.get("taxonomy_breadcrumb_count")
        if primary_count is None:
            merged["taxonomy_breadcrumb_count"] = fallback_count
        elif fallback_count is None:
            merged["taxonomy_breadcrumb_count"] = primary_count
        else:
            merged["taxonomy_breadcrumb_count"] = max(int(primary_count), int(fallback_count))

        source_values = []
        for sources in [
            primary.get("taxonomy_sources_detected"),
            fallback.get("taxonomy_sources_detected"),
        ]:
            if isinstance(sources, str) and sources.strip():
                source_values.extend([s for s in sources.split("|") if s])
        merged["taxonomy_sources_detected"] = (
            "|".join(sorted(set(source_values))) if source_values else None
        )

        def _prefer_text(*values: object) -> str | None:
            for value in values:
                if isinstance(value, str) and value.strip():
                    return value.strip()
            return None

        merged["category_path_raw"] = _prefer_text(
            primary.get("category_path_raw"),
            fallback.get("category_path_raw"),
        )
        merged["category_leaf_raw"] = _prefer_text(
            primary.get("category_leaf_raw"),
            fallback.get("category_leaf_raw"),
        )

        has_high = (
            merged["taxonomy_breadcrumb_present"]
            or merged["taxonomy_jsonld_category_present"]
            or merged["taxonomy_jsonld_breadcrumb_present"]
        )
        has_medium = merged["taxonomy_product_type_present"]
        has_low = merged["taxonomy_tags_present"] or merged["taxonomy_url_hint_present"]
        if has_high:
            merged["taxonomy_evidence_strength"] = "high"
        elif has_medium:
            merged["taxonomy_evidence_strength"] = "medium"
        elif has_low:
            merged["taxonomy_evidence_strength"] = "low"
        else:
            merged["taxonomy_evidence_strength"] = "none"

        return merged

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
        taxonomy = self._taxonomy_evidence_from_product_json(pdata, collection, product_url)

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
            taxonomy_breadcrumb_present=taxonomy["taxonomy_breadcrumb_present"],
            taxonomy_breadcrumb_count=taxonomy["taxonomy_breadcrumb_count"],
            taxonomy_jsonld_category_present=taxonomy["taxonomy_jsonld_category_present"],
            taxonomy_jsonld_breadcrumb_present=taxonomy["taxonomy_jsonld_breadcrumb_present"],
            taxonomy_product_type_present=taxonomy["taxonomy_product_type_present"],
            taxonomy_tags_present=taxonomy["taxonomy_tags_present"],
            taxonomy_url_hint_present=taxonomy["taxonomy_url_hint_present"],
            taxonomy_sources_detected=taxonomy["taxonomy_sources_detected"],
            taxonomy_evidence_strength=taxonomy["taxonomy_evidence_strength"],
            category_path_raw=taxonomy["category_path_raw"],
            category_leaf_raw=taxonomy["category_leaf_raw"],
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
                    html_category = html_fields.get("category")
                    if (
                        isinstance(html_category, str)
                        and html_category.strip()
                        and (not record.category or not str(record.category).strip())
                    ):
                        record.category = html_category.strip()
                    merged_taxonomy = self._merge_taxonomy_evidence(record.to_dict(), html_fields)
                    record.taxonomy_breadcrumb_present = merged_taxonomy.get(
                        "taxonomy_breadcrumb_present"
                    )
                    record.taxonomy_breadcrumb_count = merged_taxonomy.get(
                        "taxonomy_breadcrumb_count"
                    )
                    record.taxonomy_jsonld_category_present = merged_taxonomy.get(
                        "taxonomy_jsonld_category_present"
                    )
                    record.taxonomy_jsonld_breadcrumb_present = merged_taxonomy.get(
                        "taxonomy_jsonld_breadcrumb_present"
                    )
                    record.taxonomy_product_type_present = merged_taxonomy.get(
                        "taxonomy_product_type_present"
                    )
                    record.taxonomy_tags_present = merged_taxonomy.get("taxonomy_tags_present")
                    record.taxonomy_url_hint_present = merged_taxonomy.get(
                        "taxonomy_url_hint_present"
                    )
                    record.taxonomy_sources_detected = merged_taxonomy.get(
                        "taxonomy_sources_detected"
                    )
                    record.taxonomy_evidence_strength = merged_taxonomy.get(
                        "taxonomy_evidence_strength"
                    )
                    record.category_path_raw = merged_taxonomy.get("category_path_raw")
                    record.category_leaf_raw = merged_taxonomy.get("category_leaf_raw")
                    records.append(record)
            else:
                html_fields = self._fetch_product_html_fallback(slug)
                if html_fields:
                    html_category = html_fields.get("category")
                    if not (isinstance(html_category, str) and html_category.strip()):
                        html_category = None

                    record = ProductRecord(
                        source_platform="shopify",
                        shop_name=self.shop_name,
                        product_id=slug,
                        product_url=f"{self.store_url}/products/{slug}",
                        title=slug.replace("-", " ").title(),
                        description=html_fields.get("description", ""),
                        category=html_category
                        or (collection.replace("-", " ").title() if collection != "all" else None),
                        brand=self.shop_name,
                        price=html_fields.get("price"),
                        old_price=None,
                        availability=html_fields.get("availability"),
                        rating=html_fields.get("rating"),
                        review_count=html_fields.get("review_count"),
                        geography=self.geography,
                        scraped_at=now,
                        taxonomy_breadcrumb_present=html_fields.get("taxonomy_breadcrumb_present"),
                        taxonomy_breadcrumb_count=html_fields.get("taxonomy_breadcrumb_count"),
                        taxonomy_jsonld_category_present=html_fields.get(
                            "taxonomy_jsonld_category_present"
                        ),
                        taxonomy_jsonld_breadcrumb_present=html_fields.get(
                            "taxonomy_jsonld_breadcrumb_present"
                        ),
                        taxonomy_product_type_present=html_fields.get(
                            "taxonomy_product_type_present"
                        ),
                        taxonomy_tags_present=html_fields.get("taxonomy_tags_present"),
                        taxonomy_url_hint_present=html_fields.get("taxonomy_url_hint_present"),
                        taxonomy_sources_detected=html_fields.get("taxonomy_sources_detected"),
                        taxonomy_evidence_strength=html_fields.get("taxonomy_evidence_strength"),
                        category_path_raw=html_fields.get("category_path_raw"),
                        category_leaf_raw=html_fields.get("category_leaf_raw"),
                    )
                    records.append(record)

            if (i + 1) % 20 == 0:
                print(f"  [{self.shop_name}] Enriched {i + 1}/{len(slug_info)} products")
            time.sleep(SCRAPING_DELAY)

        print(f"ShopifyScraper: {self.shop_name} done — {len(records)} products")
        return records
