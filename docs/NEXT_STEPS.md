# Project status & next steps — Mohamed & Ismail

**Repo:** [github.com/MedGm/Smart-eCommerce-Intelligence-Pipeline](https://github.com/MedGm/Smart-eCommerce-Intelligence-Pipeline)  
**Deadline:** 18 May

---

## Current status (as of 11 March)

### What is done

| Étape | Status | Details |
|-------|--------|---------|
| 1. Scraping A2A | **Done (v2)** | 8 stores, 565 products. Playwright + `/products/<slug>.json` enrichment, WC Store API (price fix), BS4, Scrapy/Storefront API/REST v3 demos |
| 2. Top-K + ML/DM | **Done (v2)** | Top-K scoring, RF (CV F1=0.996), XGBoost (CV), KMeans (sil=0.261), DBSCAN (56 outliers), PCA, 874 association rules |
| 3. Kubeflow | **Done** | local_pipeline.py (10 steps), KFP pipeline + compiled YAML |
| 4. Dashboard BI | **Done (v2)** | Streamlit 8 sections (Plotly, Altair, Seaborn), real prices, category charts |
| 5. LLM | **Done (v2)** | Gemini summarizer, OpenAI adapter, LangChain demo, prompt engineering, logging |
| 6. MCP + CI/CD | **Done** | MCP Host/Client/Server in code, access logs, GitHub Actions (pytest + ruff), Docker |

### What was fixed in v2

| Problem (v1) | Fix applied | Result |
|--------------|-------------|--------|
| Shopify data hollow (92 products, no price/desc/category) | Added `/products/<slug>.json` enrichment | 161 Shopify products with price, description, category |
| WC prices in cents (avg 1814) | Divide by `10^currency_minor_unit` | Avg price now ~$25 |
| Ratings all zero | Extract from JSON-LD where available | 96 products (17%) now have real ratings |
| 149/220 category = "none" | `product_type` + collection URL inference | 74% now have real categories |
| Geography null everywhere | Assigned from store config | 100% coverage (US/UK) |
| Only 220 products | Added 6 new stores | 565 products across 8 stores |
| F1=1.0 artifact | Cross-validation (StratifiedKFold) | F1=0.996 (more realistic) |
| HTML in descriptions | BS4 stripping in scraper + preprocessing | Clean text |

### Remaining weaknesses

| Issue | Impact | Possible fix |
|-------|--------|-------------|
| 23% products lack prices | Features incomplete for those rows | Scrape specific collection pages; some stores block `.json` |
| Ratings only 17% | Popularity proxy still discount-driven | Add stores with review widgets |
| 146 "uncategorized" | Category analytics weaker | Scrape sub-collections instead of `/all` |
| 565 < 2000 recommended | Limited ML generalization | Add 5–10 more stores |
| Hiut Denim: 2 products | Negligible | Replace with larger store |

---

## Improvement plan (priority order)

### P1 — Fix data quality (critical, do first)

| # | Who | Task |
|---|-----|------|
| 1.1 | Ismail | **Enrich Shopify products:** visit each product detail page (Playwright or BS4) and extract price, rating, review_count, description, category from the HTML / JSON-LD. Use `src/scraping/enrich_bs4.py` as a starting point. |
| 1.2 | Ismail | **Fix WC price units:** divide price and old_price by 100 in `woocommerce.py` if the Store API returns cents (check `currency_minor_unit` field). |
| 1.3 | Ismail | **Strip HTML from WC descriptions:** use `BeautifulSoup(desc, "html.parser").get_text()` in `woocommerce.py` before saving. |
| 1.4 | Both | **Add more stores or scrape more products:** either add 1–2 more Shopify/WooCommerce stores, or scrape more collections from Ruggable. Target: **500+ products with real prices and categories.** |
| 1.5 | Mohamed | **Fix "none" categories:** for Shopify, infer category from collection URL or product URL slug (e.g. `/collections/area-rugs` → category="area rugs"). For WooCommerce, map empty categories to "uncategorized" and keep real ones. |

### P2 — Fix preprocessing & features

| # | Who | Task |
|---|-----|------|
| 2.1 | Mohamed | **Re-run preprocessing** after data fixes. Check that price is now in dollars, ratings are non-zero where available, categories are meaningful. |
| 2.2 | Mohamed | **Adjust popularity_proxy:** if ratings are still mostly zero, increase weight on review_count and discount, or add a text-length proxy (longer description = more effort = more likely a real product). |
| 2.3 | Mohamed | **Re-run EDA notebook** and update the Phase 3.3 notes with real distributions. |

### P3 — Fix ML/DM models

| # | Who | Task |
|---|-----|------|
| 3.1 | Mohamed | **Re-train RF and XGBoost** after data fix. If F1 is still 1.0, increase test_size or use cross-validation (`cross_val_score`) to get a more realistic estimate. |
| 3.2 | Mohamed | **Re-run KMeans and DBSCAN** on better features. Write 1–2 sentences per cluster (e.g. "premium rugs", "affordable seasonings", "discounted bundles"). |
| 3.3 | Mohamed | **Re-run association rules.** With real categories, rules should be more interpretable (e.g. `{category:rugs} -> {platform:shopify}`). |

### P4 — Fix dashboard

| # | Who | Task |
|---|-----|------|
| 4.1 | Ismail | **Clean display:** strip HTML from titles/descriptions before showing in tables. |
| 4.2 | Ismail | **Add filters:** category dropdown, shop selector, price range slider on the Top-K page. |
| 4.3 | Ismail | **Format prices:** show prices in dollars (not cents). Add currency symbol. |
| 4.4 | Both | **Take screenshots** for the report once data is clean. |

### P5 — Polish for delivery

| # | Who | Task |
|---|-----|------|
| 5.1 | Both | **Enable LLM summary:** set GEMINI_API_KEY in `.env` and verify the summary is coherent with the actual data. |
| 5.2 | Mohamed | **Docker test:** run `docker compose --profile pipeline run app` and confirm it works. |
| 5.3 | Both | **Write report** using `docs/report_outline.md`. |
| 5.4 | Both | **Prepare oral defense:** 1–2 min per étape, be ready to explain every design choice. |

---

## Quick reference: commands

```bash
make scrape       # run Shopify + WooCommerce scrapers
make preprocess   # clean + validate
make features     # feature table
make score        # Top-K
make train        # RF + XGBoost + KMeans + DBSCAN + rules
make pipeline     # full local run (10 steps)
make dashboard    # Streamlit on :8501
make test         # pytest
make lint         # ruff check + format
```
