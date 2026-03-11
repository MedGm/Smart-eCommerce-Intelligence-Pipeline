"""
Shopify scraper adapter.

For this project we target Ruggable (https://ruggable.com).

Ruggable est assez dynamique côté frontend, donc on utilise Playwright pour
laisser le navigateur charger le contenu, puis on extrait les liens produits
depuis la page rendue.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import List
from urllib.parse import urljoin

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from src.scraping.base import BaseScraper, ProductRecord


class ShopifyScraper(BaseScraper):
    """Scrape product data from a Shopify store (Ruggable storefront)."""

    def __init__(self, output_dir: Path, store_url: str | None = None):
        super().__init__(output_dir)
        # Normalise URL (no trailing slash)
        self.store_url = (store_url or "").rstrip("/")

    def _collection_urls(self) -> list[str]:
        """
        Return a small curated list of collection/listing URLs to crawl.

        Ruggable exposes many collections; here we start with a few generic
        ones. You can add more if you need more volume.
        """
        base = self.store_url
        return [
            f"{base}/collections/all",
            f"{base}/collections/area-rugs",
            f"{base}/collections/runner-rugs",
        ]

    def _extract_from_anchor(
        self, href: str, text: str
    ) -> tuple[str | None, str | None]:
        """
        Extract (url, title) from a product anchor.
        """
        if not href or "/products/" not in href:
            return None, None
        product_url = urljoin(self.store_url, href)
        title = text.strip()[:200] if text else None
        return product_url, title

    def scrape(self) -> List[ProductRecord]:
        """
        Storefront scraper for Ruggable using Playwright.

        Stratégie :
        - ouvrir quelques pages de collections
        - scroller pour charger les produits
        - récupérer tous les liens vers `/products/...`
        - déduire un `product_id` à partir du slug d'URL
        """
        if not self.store_url:
            print("ShopifyScraper: no store_url configured, skipping.")
            return []

        records: List[ProductRecord] = []
        seen_ids: set[str] = set()
        now = datetime.now(timezone.utc).isoformat()
        shop_name = "Ruggable"

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (X11; Linux x86_64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0 Safari/537.36"
                    )
                )
                page = context.new_page()

                for collection_url in self._collection_urls():
                    try:
                        print(f"ShopifyScraper: visiting collection {collection_url}")
                        page.goto(
                            collection_url,
                            timeout=40_000,
                            wait_until="domcontentloaded",
                        )
                    except PlaywrightTimeoutError:
                        print(f"ShopifyScraper: timeout loading {collection_url}")
                        continue

                    # Scroll pour laisser le temps aux produits de se charger (lazy-load)
                    for _ in range(6):
                        page.mouse.wheel(0, 2000)
                        page.wait_for_timeout(1000)

                    anchors = page.query_selector_all("a[href*='/products/']")
                    print(
                        f"ShopifyScraper: found {len(anchors)} product anchors on {collection_url}"
                    )

                    for a in anchors:
                        href = a.get_attribute("href") or ""
                        text = a.inner_text() or ""
                        product_url, title = self._extract_from_anchor(href, text)
                        if not product_url or not title:
                            continue

                        slug = product_url.rstrip("/").split("/")[-1]
                        product_id = slug or product_url

                        if product_id in seen_ids:
                            continue
                        seen_ids.add(product_id)

                        record = ProductRecord(
                            source_platform="shopify",
                            shop_name=shop_name,
                            product_id=product_id,
                            product_url=product_url,
                            title=title,
                            description="",  # pourra être enrichi plus tard
                            category=None,
                            brand="Ruggable",
                            price=None,  # peut être ajouté en visitant la page produit
                            old_price=None,
                            availability=None,
                            rating=None,
                            review_count=None,
                            geography=None,
                            scraped_at=now,
                        )
                        records.append(record)

                browser.close()

        except Exception as exc:  # pragma: no cover - protection simple
            print(f"ShopifyScraper: unexpected error with Playwright: {exc}")

        print(f"ShopifyScraper: fetched {len(records)} products from {self.store_url}")
        return records
