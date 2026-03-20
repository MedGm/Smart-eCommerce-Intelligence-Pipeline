# Data quality report — v3 (20 March, post full pipeline run)

## Dataset snapshot

| Metric | v1 | **v3 (current)** |
|--------|-----|---------|
| Total products | 220 | **635** |
| Shops | 2 | **8** |
| Niches | 2 (rugs, seasoning) | **8** (rugs, gaming, denim, fashion, coffee, seasoning, drinkware, kitchen) |
| Platforms | Shopify 92 / WC 128 | **Shopify 230 / WC 405** |

## Products per shop

| Shop | Platform | Products | Niche |
|------|----------|----------|-------|
| NutriBullet | WooCommerce | 184 | Kitchen appliances |
| Dan-O's Seasoning | WooCommerce | 129 | Food/Seasoning |
| Nalgene | WooCommerce | 92 | Drinkware |
| Ruggable | Shopify | 70 | Home/Rugs |
| Fashion Nova | Shopify | 64 | Clothing |
| Death Wish Coffee | Shopify | 29 | Coffee |
| Turtle Beach | Shopify | 59 | Gaming/Electronics |
| Hiut Denim | Shopify | 8 | Denim/Fashion |

## Field coverage

| Field | v1 | **v3** | Notes |
|-------|-----|--------|-------|
| price | 58% (128/220) | **87.6% (556/635)** | Fixed: WC cents → dollars; Shopify enriched via `/products/<slug>.json` |
| old_price | 32% | **13.9% (88/635)** | Only products with active promotions |
| rating > 0 | 0% | **16.1% (102/635)** | Mainly Turtle Beach/Fashion Nova review sources |
| review_count > 0 | 0% | **16.2% (103/635)** | Same source family as ratings |
| real category | 32% | **80.6% (512/635)** | Path-aware category normalization + taxonomy evidence |
| description | 58% | **97.5% (619/635)** | Shopify JSON + WC API; HTML stripped |
| availability | 5% | **87.6% (556/635)** | Availability now largely present in current extraction |
| geography | 0% | **100% (635/635)** | Assigned from store config (US/UK) |

## Price statistics (v3)

| Stat | Value |
|------|-------|
| Count (non-null) | 556 |
| Mean | $40.11 |
| Std | $66.58 |
| Min | $0.00 |
| 25% | $11.00 |
| Median | $19.99 |
| 75% | $38.97 |
| Max | $649.99 |

## What was fixed vs v1

1. **WooCommerce prices in cents** → divided by `10^currency_minor_unit`. Avg went from 1814 to $25.
2. **Shopify hollow data** → enriched via `/products/<slug>.json` (price, description, category, brand, variants).
3. **HTML in descriptions** → stripped with BeautifulSoup in scraper + preprocessing.
4. **Categories "none"** → Shopify `product_type` used; collection name as fallback; preprocessing normalizes empty → NaN → "uncategorized".
5. **Geography null** → assigned from store config in `stores.py`.
6. **Only 2 stores** → expanded to 8 stores across 6 niches.
7. **Proxy-target inflation corrected** → models now use an observed-signal target with grouped-by-shop validation.

## Remaining limitations

| Issue | Impact | Possible fix |
|-------|--------|-------------|
| 12.4% products still lack prices | Score/features less reliable for those | Scrape more Shopify collections; some stores block `.json` endpoint |
| Ratings for only ~16% | Popularity proxy remains partially rating-sparse | Add stores with public reviews; scrape review widgets when available |
| 123 "uncategorized" products | Weakens category-level analytics | Scrape specific sub-collections instead of `/collections/all` |
| 635 < 2000 recommended | ML models have limited generalization | Add 5–10 more stores from validated candidates |
| Hiut Denim still small (8 products) | Low contribution to global patterns | Remove or replace with a larger denim/fashion source |
| Grouped-CV F1 remains 0.0 | Current features do not generalize positives across unseen shops | Add richer cross-shop signals, rebalance classes, and tune decision thresholds |

## ML results (v3)

| Model | Metric | v1 | **v3** |
|-------|--------|-----|--------|
| RandomForest | F1 (CV) | 1.000 (overfit) | **0.811** (honesty gate yellow; grouped-CV F1 = 0.000) |
| KMeans | Silhouette | 0.473 | **0.273** |
| DBSCAN | Outliers | 24 | **49** |
| Association rules | Rules found | 274 | **567** |
