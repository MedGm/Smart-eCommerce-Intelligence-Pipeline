"""
Shared product schema and base scraper interface.
Single schema for both Shopify and WooCommerce; maps to dossier fields.
"""
from dataclasses import dataclass, asdict
from typing import Optional
import json
from pathlib import Path


@dataclass
class ProductRecord:
    source_platform: str
    shop_name: str
    product_id: str
    product_url: str
    title: str
    description: str
    category: Optional[str]
    brand: Optional[str]
    price: Optional[float]
    old_price: Optional[float]
    availability: Optional[str]
    rating: Optional[float]
    review_count: Optional[int]
    geography: Optional[str]
    scraped_at: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ProductRecord":
        return cls(**{k: d.get(k) for k in cls.__dataclass_fields__})


class BaseScraper:
    """Base class for Shopify and WooCommerce adapters."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def scrape(self) -> list[ProductRecord]:
        """Override: fetch products and return list of ProductRecord."""
        raise NotImplementedError

    def save(self, records: list[ProductRecord], filename: str = "products.json") -> Path:
        path = self.output_dir / filename
        data = [r.to_dict() for r in records]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return path
