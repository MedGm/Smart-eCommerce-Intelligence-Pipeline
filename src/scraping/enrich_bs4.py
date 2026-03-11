"""
Static scraping enrichment using requests + BeautifulSoup.

Visits individual Shopify product pages (already collected by Playwright)
and extracts structured fields: description, availability, rating from HTML.
Demonstrates scraping statique (dossier: requests + BeautifulSoup).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}
TIMEOUT = 12


def enrich_product(product: dict, delay: float = 1.0) -> dict:
    """Fetch a Shopify product page with requests+BS4 and fill missing fields."""
    url = product.get("product_url", "")
    if not url:
        return product

    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    except requests.RequestException as exc:
        print(f"  BS4 enrich: error fetching {url}: {exc}")
        return product

    if resp.status_code != 200:
        return product

    soup = BeautifulSoup(resp.text, "html.parser")

    if not product.get("description"):
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            product["description"] = meta_desc["content"].strip()[:500]

    if not product.get("availability"):
        og_avail = soup.find("meta", attrs={"property": "og:availability"})
        if og_avail and og_avail.get("content"):
            product["availability"] = og_avail["content"]

    if product.get("price") is None:
        og_price = soup.find("meta", attrs={"property": "og:price:amount"})
        if og_price and og_price.get("content"):
            try:
                product["price"] = float(og_price["content"])
            except (ValueError, TypeError):
                pass

    script_tags = soup.find_all("script", type="application/ld+json")
    for script in script_tags:
        try:
            ld = json.loads(script.string or "")
            if isinstance(ld, dict) and ld.get("@type") == "Product":
                if not product.get("description") and ld.get("description"):
                    product["description"] = ld["description"][:500]
                agg = ld.get("aggregateRating") or {}
                if product.get("rating") is None and agg.get("ratingValue"):
                    product["rating"] = float(agg["ratingValue"])
                if not product.get("review_count") and agg.get("reviewCount"):
                    product["review_count"] = int(agg["reviewCount"])
                if not product.get("category") and ld.get("category"):
                    product["category"] = str(ld["category"])
        except (json.JSONDecodeError, ValueError, TypeError):
            continue

    time.sleep(delay)
    return product


def enrich_raw_file(
    path: Path, max_products: int = 20, delay: float = 1.0
) -> list[dict]:
    """Load a raw JSON file, enrich up to max_products, save back."""
    with open(path, encoding="utf-8") as f:
        products = json.load(f)

    enriched = 0
    for p in products:
        if enriched >= max_products:
            break
        if p.get("source_platform") != "shopify":
            continue
        before = dict(p)
        enrich_product(p, delay=delay)
        if p != before:
            enriched += 1
            print(f"  Enriched: {p.get('title', '?')[:50]}")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    print(f"BS4 enrichment done: {enriched} products enriched in {path}")
    return products


if __name__ == "__main__":
    import os

    data_dir = Path(os.environ.get("DATA_DIR", "data"))
    raw = data_dir / "raw" / "shopify" / "products.json"
    if raw.exists():
        enrich_raw_file(raw, max_products=20, delay=1.5)
    else:
        print(f"No raw file at {raw}. Run scrapers first.")
