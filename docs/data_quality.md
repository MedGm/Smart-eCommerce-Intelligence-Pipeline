# Data quality report — v2 (11 March, after multi-store scraping)

## Dataset snapshot

| Metric | v1 | **v2 (current)** |
|--------|-----|---------|
| Total products | 220 | **565** |
| Shops | 2 | **8** |
| Niches | 2 (rugs, seasoning) | **6** (rugs, gaming, denim, fashion, coffee, seasoning, drinkware, kitchen) |
| Platforms | Shopify 92 / WC 128 | **Shopify 161 / WC 404** |

## Products per shop

| Shop | Platform | Products | Niche |
|------|----------|----------|-------|
| NutriBullet | WooCommerce | 184 | Kitchen appliances |
| Dan-O's Seasoning | WooCommerce | 128 | Food/Seasoning |
| Nalgene | WooCommerce | 92 | Drinkware |
| Fashion Nova | Shopify | 61 | Clothing |
| Ruggable | Shopify | 47 | Home/Rugs |
| Death Wish Coffee | Shopify | 29 | Coffee |
| Turtle Beach | Shopify | 22 | Gaming/Electronics |
| Hiut Denim | Shopify | 2 | Denim/Fashion |

## Field coverage

| Field | v1 | **v2** | Notes |
|-------|-----|--------|-------|
| price | 58% (128/220) | **77% (433/565)** | Fixed: WC cents → dollars; Shopify enriched via `/products/<slug>.json` |
| old_price | 32% | **16% (88/565)** | Only products with active promotions |
| rating > 0 | 0% | **17% (96/565)** | Mainly Turtle Beach (JSON-LD aggregateRating) |
| review_count > 0 | 0% | **17% (96/565)** | Same source as ratings |
| real category | 32% | **74% (419/565)** | Shopify `product_type` + collection URL inference |
| description | 58% | **98% (555/565)** | Shopify JSON + WC API; HTML stripped |
| availability | 5% | **5% (29/565)** | Most stores don't expose stock via API |
| geography | 0% | **100% (565/565)** | Assigned from store config (US/UK) |

## Price statistics (v2)

| Stat | Value |
|------|-------|
| Count (non-null) | 433 |
| Mean | $25.06 |
| Std | $30.53 |
| Min | $0.00 |
| 25% | $9.99 |
| Median | $16.99 |
| 75% | $24.99 |
| Max | $244.99 |

## What was fixed vs v1

1. **WooCommerce prices in cents** → divided by `10^currency_minor_unit`. Avg went from 1814 to $25.
2. **Shopify hollow data** → enriched via `/products/<slug>.json` (price, description, category, brand, variants).
3. **HTML in descriptions** → stripped with BeautifulSoup in scraper + preprocessing.
4. **Categories "none"** → Shopify `product_type` used; collection name as fallback; preprocessing normalizes empty → NaN → "uncategorized".
5. **Geography null** → assigned from store config in `stores.py`.
6. **Only 2 stores** → expanded to 8 stores across 6 niches.
7. **F1=1.0 artifact** → cross-validation now used in RF and XGBoost.

## Remaining limitations

| Issue | Impact | Possible fix |
|-------|--------|-------------|
| 23% products lack prices | Score/features less reliable for those | Scrape more Shopify collections; some stores block `.json` endpoint |
| Ratings for only 17% | Popularity proxy still discount-heavy | Add stores with public reviews; try scraping review widgets |
| 146 "uncategorized" products | Weakens category-level analytics | Scrape specific sub-collections instead of `/collections/all` |
| 565 < 2000 recommended | ML models have limited generalization | Add 5–10 more stores from validated candidates |
| Hiut Denim: only 2 products | Negligible contribution | Remove or replace with larger store |
| Availability data sparse (5%) | Stock analysis not possible | Some stores expose `available` in variants but not in listing |

## ML results (v2)

| Model | Metric | v1 | **v2** |
|-------|--------|-----|--------|
| RandomForest | F1 (CV) | 1.000 (overfit) | **0.996** |
| KMeans | Silhouette | 0.473 | **0.261** (more diverse data) |
| DBSCAN | Outliers | 24 | **56** |
| Association rules | Rules found | 274 | **874** |
