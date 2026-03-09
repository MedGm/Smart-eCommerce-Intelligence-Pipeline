# Target shops for scraping (Phase 1.2)

**Scope (fixed):** One **Shopify** store + one **WooCommerce** store only.

**Rule:** Evaluate **3–5 candidates per platform** first; then **lock 1 Shopify + 1 WooCommerce**. Do not lock the first store you see.

**Objective (fiche):** Extract product data automatically from both platforms (A2A scraping).  
**Recommended volume (data doc):** 300–500 products minimum; **2000–5000 products** ideal for ML/DM.

---

## 1. Go / no-go rule

**Only keep a store if all are true:**

- You can fetch at least one product list page reliably.
- You can access product detail data (title, price, description, etc.).
- Pagination is discoverable and usable.
- You estimate **at least 300 products** (or combined total 300+ across both stores).

If any of these fails, drop the candidate and test the next one. This avoids wasting time on dead-end stores.

---

## 2. Selection scorecard (per candidate)

Before locking a store, fill this scorecard for each candidate. Use it for **3–5 Shopify** and **3–5 WooCommerce** candidates.

| Criterion | Shopify | WooCommerce | Notes |
|-----------|---------|-------------|--------|
| **Estimated product count** | _____ | _____ | Aim ≥300 per store (or 300+ total) |
| **Public API works?** | ☐ Yes ☐ No | ☐ Yes ☐ No | WooCommerce: `/wp-json/wc/store/v1/products`. Shopify: usually no public API (token-based). |
| **Pagination works?** | ☐ Yes ☐ No | ☐ Yes ☐ No | Can you get page 2, 3, …? |
| **Robots/ToS acceptable for pedagogical scraping?** | ☐ Yes ☐ No | ☐ Yes ☐ No | No hard blocks, light educational use. |
| **JS-heavy?** | ☐ Yes ☐ No | ☐ Yes ☐ No | If yes, use Playwright; if no, requests + BS4 may suffice. |
| **Fallback available?** | ☐ Yes ☐ No | ☐ Yes ☐ No | e.g. API fails but Playwright works. |

**Scoring (optional but recommended):** Give each candidate a score out of 10:

- Product volume: /3  
- Ease of extraction: /3  
- Stability: /2  
- Legal/ethical comfort: /1  
- Demo value: /1  

Pick the **top one per platform** after testing.

---

## 3. Final table (after selection)

Locked targets (validated with `scripts/validate_targets.py`). Put the same in `.env` (Section 9).

| Platform       | Store name      | URL or API base           | Method   | Auth | Target # products | Notes                                      |
|----------------|-----------------|---------------------------|----------|------|--------------------|---------------------------------------------|
| **Shopify**    | Ruggable        | https://ruggable.com      | Playwright (storefront) | No  | 300–2000+          | collections/all OK, product links, no anti-bot |
| **WooCommerce** | Dan-O's Seasoning | https://danosseasoning.com | Store API + /shop/ | No  | 300–2000+          | Store API OK, /shop/ OK, no anti-bot       |

---

## 4. How to find candidates

### Phase A — Discovery

- **Target:** 5–10 Shopify candidates, 5–10 WooCommerce candidates.
- **Sources:**
  - **Technology detection:** [BuiltWith](https://builtwith.com/), [Wappalyzer](https://www.wappalyzer.com/) — identify sites by Shopify vs WooCommerce.
  - **Niche:** Pick a niche with many products (e.g. cosmetics, furniture, fashion, accessories, electronics), then find stores in that niche.
  - **Demo stores** and niche stores with large catalogs.

### Phase B — Quick validation (≤5 min per candidate)

**Shopify checks:**

- Homepage loads.
- `/collections/all` exists (or equivalent collection pages).
- At least a few paginated listing pages.
- Product cards expose title, price, URL.
- Detail pages expose description, category, availability.
- No login wall or heavy anti-bot (e.g. Cloudflare challenges every request).

**WooCommerce checks:**

- Homepage loads.
- `/shop/` or product-category pages exist.
- **Best quick test:**  
  `https://<site>/wp-json/wc/store/v1/products` returns JSON (Store API is public and unauthenticated).
- Pagination works (e.g. `?page=2` or cursor).
- Response has enough fields for your schema (title, price, etc.).

### Phase C — Score and lock

- Score each candidate (e.g. out of 10 as above).
- Choose **1 Shopify** and **1 WooCommerce**.
- Document them in Section 3 and in `.env`.

---

## 5. Search tips

**Shopify (storefront scraping — default):**

- `site:myshopify.com "products"`
- `site:myshopify.com "collections"`
- `inurl:/collections/ shopify`
- `"powered by Shopify" "collections"`

Then verify: `/collections/all`, paginated category pages, product cards, and (if possible) product JSON in page scripts.

**Important:** The **Shopify Storefront API is token-based**. Do not assume it is publicly usable for random stores. For this project, **default = public storefront scraping with Playwright**. Use the API only if you already have a valid token (e.g. your own store or partner demo).

**WooCommerce:**

- `"powered by WooCommerce" "shop"`
- `inurl:/product-category/`
- `inurl:/shop/ "WooCommerce"`
- `site:*.com "/wp-json/wc/store/v1/products"`

Then test the Store API directly (see Section 7).

---

## 6. What makes a good target (and what to avoid)

**Ideal Shopify target:**

- Public storefront, large catalog.
- Simple collection pages, consistent product card layout.
- Prices and availability visible.
- Not too much JS obfuscation.
- No aggressive rate-limiting for light educational scraping.

**Ideal WooCommerce target:**

- **Store API works:** `/wp-json/wc/store/v1/products` returns JSON.
- Many products, clear category structure.
- Ratings/reviews and stock status visible when possible.
- Clean pagination.

**Avoid:**

- Infinite scroll only with messy or undocumented API calls.
- Cloudflare (or similar) challenges on every few requests.
- Very small catalogs (e.g. &lt;50 products).
- Missing category, rating, or stock data.
- Strong HTML variation between categories.
- Login walls or strict geographic restrictions.

---

## 7. Concrete checks you can run

**WooCommerce:**

```bash
# Check Store API exists and returns data
curl -I https://<site>/wp-json/wc/store/v1/products
curl "https://<site>/wp-json/wc/store/v1/products?per_page=5"
```

If you get structured product JSON, it’s a strong candidate.

**Shopify:**

- Open collection and product URLs in the browser.
- Check for product data in HTML or in `<script>` JSON (e.g. `window.ShopifyAnalytics`, or embedded JSON-LD).
- Do **not** rely on Storefront API unless you have a valid token.

**Optional — validator script (Day 1):**

- Send GET to homepage and to key URLs (e.g. WooCommerce Store API, Shopify collection page).
- Check status codes and platform fingerprints (e.g. `cdn.shopify.com`, WooCommerce/WordPress markers).
- Save results in a simple table: URL, platform, reachable, API/product list OK, etc.

---

## 8. Data to extract (fiche → ProductRecord)

| Fiche / data doc        | ProductRecord field | Notes     |
|-------------------------|----------------------|-----------|
| Titre                   | `title`              | Required  |
| Prix actuel             | `price`              |           |
| Ancien prix / promo     | `old_price`          |           |
| Description              | `description`        |           |
| Catégorie               | `category`           |           |
| Marque / vendeur        | `brand`              |           |
| Disponibilité / stock   | `availability`       |           |
| Note moyenne            | `rating`             |           |
| Nombre d’avis           | `review_count`       |           |
| Boutique                | `shop_name`          |           |
| Géographie              | `geography`          |           |
| Product ID              | `product_id`         | Required  |
| URL produit             | `product_url`        |           |

Optional if present: tags, images, variantes. See `src/scraping/base.py` for the full schema.

---

## 9. `.env` (once stores are locked)

```bash
# Shopify (Ruggable — Playwright storefront scraping)
SHOPIFY_STORE=https://ruggable.com

# WooCommerce (Dan-O's Seasoning — Store API)
WOOCOMMERCE_URL=https://danosseasoning.com
# Optional for REST API v3:
# WOOCOMMERCE_KEY=...
# WOOCOMMERCE_SECRET=...
```

---

## 10. References

- **Shopify:** [Storefront API](https://shopify.dev/docs/storefronts/headless/building-with-the-storefront-api/getting-started) (token-based). For scraping: Playwright on the public storefront.
- **WooCommerce:** [REST API](https://developer.woocommerce.com/docs/getting-started-with-the-woocommerce-rest-api/). **Store API (public):** `/wp-json/wc/store/v1/products` — no auth.
- **Scraping (fiche):** requests + BeautifulSoup (static), Selenium or Playwright (dynamic), Scrapy (structured).

---

## 11. Recommended strategy (for the report)

- **Shopify:** One public storefront scraped with **Playwright** (dynamic storefront extraction).
- **WooCommerce:** One store where **`/wp-json/wc/store/v1/products`** works publicly (API-first extraction).

This gives two complementary stories: one dynamic scraping case, one structured API case — stronger report and less fragile implementation.

---

**Definition of done (Phase 1.2):** You have evaluated 3–5 candidates per platform, applied the go/no-go rule and scorecard, locked **one Shopify** and **one WooCommerce**, filled Section 3 and `.env`, and both of you agree. Then Ismail can implement the adapters in Phase 2.
