# Architecture — Smart eCommerce Intelligence Pipeline

**Scope:** Shopify (Ruggable) + WooCommerce (Dan-O's Seasoning).

## High-level flow

```
[ Shopify / WooCommerce Sources ]
          |
          v
 [ A2A Scraping Agents ]
   - Playwright (dynamic)          → Shopify storefront
   - requests + BeautifulSoup      → static enrichment
   - WooCommerce Store API         → REST JSON
   - (Scrapy, Storefront API,      → documented alternatives)
     WC REST v3)
          |
          v
    [ Raw Data Store ]              data/raw/ as JSON
          |
          v
    [ Preprocessing + QA ]          dedupe, normalize, validate
          |
          v
    [ Feature Engineering ]         discount_pct, popularity_proxy, ...
          |
          v
    [ Top-K Scoring ]               weighted formula → topk_products.csv
          |
     +----+----+
     |         |
     v         v
 [ ML/DM ]  [ LLM Summaries ]
  - RF         Gemini / OpenAI
  - XGBoost    (structured input only)
  - KMeans
  - DBSCAN
  - Apriori
  - PCA
     |         |
     +----+----+
          |
          v
  [ Streamlit Dashboard ]           8 sections: KPIs, Top-K, shops,
    (Plotly, Altair, Seaborn)       KMeans, DBSCAN, model comparison,
                                    association rules, LLM insights
          |
          v
  [ Docker + CI + KFP Pipeline ]
```

## Component inventory

| Block | Module(s) | Tools | Owner |
|-------|-----------|-------|-------|
| Scraping (Shopify) | `src/scraping/shopify.py` | Playwright | Ismail |
| Scraping (WooCommerce) | `src/scraping/woocommerce.py` | requests + WC Store API | Ismail |
| Static enrichment | `src/scraping/enrich_bs4.py` | requests + BeautifulSoup | Mohamed |
| Alternative demos | `scripts/scrapy_spider.py`, `scripts/shopify_storefront_example.py`, `scripts/woocommerce_rest_example.py` | Scrapy, Shopify Storefront API, WC REST v3 | Shared |
| Preprocessing | `src/preprocessing/` | pandas | Mohamed |
| Features | `src/features/build_features.py` | pandas, numpy | Mohamed |
| Top-K scoring | `src/scoring/topk.py` | pandas | Mohamed |
| Classification | `src/ml/train_classifier.py`, `src/ml/train_xgboost.py` | scikit-learn, XGBoost | Mohamed |
| Clustering | `src/ml/cluster_products.py`, `src/ml/dbscan_products.py` | scikit-learn (KMeans, DBSCAN, PCA) | Mohamed |
| Association rules | `src/ml/rules.py` | mlxtend (Apriori) | Mohamed |
| LLM summarizer | `src/llm/summarizer.py` | google-genai (Gemini) | Ismail |
| LLM adapters | `src/llm/openai_client.py`, `scripts/langchain_summary_demo.py` | OpenAI, LangChain | Shared |
| Dashboard | `src/dashboard/app.py` | Streamlit, Plotly, Altair, Seaborn | Ismail |
| Pipeline (local) | `src/pipeline/local_pipeline.py` | Python | Mohamed |
| Pipeline (KFP) | `src/pipeline/kubeflow_pipeline.py` + YAML | kfp SDK | Mohamed |
| MCP architecture | `src/mcp/architecture.py` | Custom (MCP-inspired) | Mohamed |
| CI/CD | `.github/workflows/ci.yml` | GitHub Actions, pytest, ruff | Shared |
| Docker | `Dockerfile`, `docker-compose.yml` | Docker | Shared |

## Data schema (ProductRecord)

```
source_platform, shop_name, product_id, product_url,
title, description, category, brand,
price, old_price, availability,
rating, review_count, geography, scraped_at
```

Defined in `src/scraping/base.py`.

## Storage layout

```
data/
  raw/shopify/products.json        (161 products, 5 stores)
  raw/woocommerce/products.json    (404 products, 3 stores)
  processed/
    cleaned_products.parquet       (565 rows, 15 cols)
    features.parquet               (565 rows, 25 cols)
  analytics/
    topk_products.csv
    topk_per_category.csv
    topk_per_shop.csv
    model_metrics.json             (RandomForest)
    model_metrics_xgboost.json     (XGBoost)
    clusters.csv                   (KMeans, 4 clusters)
    pca_viz.csv
    dbscan_clusters.csv            (DBSCAN, 6 clusters + 24 outliers)
    association_rules.csv          (274 rules)
    llm_usage_log.jsonl
    mcp_access_log.jsonl
```

## MCP-inspired responsible architecture

| MCP concept | Implementation |
|-------------|---------------|
| **Host** | Streamlit dashboard (`src/dashboard/app.py`) |
| **Client** | LLM integration module (`src/llm/summarizer.py`) |
| **Servers** | `AnalyticsReaderServer` (read-only CSV/Parquet), `SummaryGeneratorServer` (LLM calls) in `src/mcp/architecture.py` |
| **Permissions** | LLM reads only processed analytics; no code execution; no score modification |
| **Logs** | `llm_usage_log.jsonl` (prompt/response), `mcp_access_log.jsonl` (access audit) |
| **Isolation** | Servers expose only allowed files; raw data is never passed to the LLM |

## Orchestration

- **Local:** `src/pipeline/local_pipeline.py` runs 10 steps sequentially.
- **Kubeflow:** `src/pipeline/kubeflow_pipeline.py` defines 4 KFP components; compiled to `kubeflow_smart_ecommerce_pipeline.yaml`.
