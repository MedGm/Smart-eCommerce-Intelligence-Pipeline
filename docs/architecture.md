# Architecture — Smart eCommerce Intelligence Pipeline

**Scope (fixed):** Data sources are **Shopify** and **WooCommerce** only.

## Positioning

**Modular monolith with pipeline stages.** Not microservices; not distributed agents. This keeps the project implementable and defensible before 18 May.

## High-level flow

```
[ Shopify / WooCommerce Sources ]
                |
                v
      [ Scraping Adapters ]
                |
                v
         [ Raw Data Store ]   (data/raw/ as JSON)
                |
                v
      [ Preprocessing + QA ]
                |
                v
        [ Feature Engineering ]
                |
                v
   [ Top-K Scoring + ML/DM Analysis ]
                |
         +------+------+
         |             |
         v             v
 [ Analytics Outputs ] [ LLM Summaries ]
         |             |
         +------+------+
                |
                v
       [ Streamlit Dashboard ]
                |
                v
      [ Docker + CI + Pipeline Run ]
```

## Component roles

| Block | Role | Owner (suggested) |
|-------|------|-------------------|
| Scraping | Shopify + WooCommerce adapters, shared `ProductRecord` schema | Ismail |
| Storage | raw/ JSON, processed/ Parquet, analytics/ CSV + plots | Mohamed |
| Preprocessing | Dedupe, normalize, validate, cleaned_products + feature_table | Mohamed |
| Feature engineering | discount_pct, price_zscore, popularity_proxy, etc. | Mohamed |
| Top-K scoring | Explainable formula (e.g. 0.35·rating + 0.30·reviews + …) | Mohamed |
| ML/DM | RandomForest baseline, KMeans, PCA viz, optional rules | Mohamed |
| Orchestration | local_pipeline.py, then KFP components | Mohamed |
| Dashboard | Streamlit 4–5 pages, consumes pipeline outputs only | Ismail |
| LLM | Summaries from aggregates only; no raw fact invention | Ismail |
| CI/CD | GitHub Actions: install, test, lint, smoke | Shared |

## Data schema (canonical)

Single product record used across scraping and downstream:

- `source_platform`, `shop_name`, `product_id`, `product_url`
- `title`, `description`, `category`, `brand`
- `price`, `old_price`, `availability`
- `rating`, `review_count`, `geography`, `scraped_at`

See `src/scraping/schema.py` (or equivalent) for the exact `ProductRecord` dataclass.

## Storage layout

```
data/
  raw/
    shopify/
    woocommerce/
  processed/
    cleaned_products.parquet
    features.parquet
  analytics/
    topk_products.csv
    clusters.csv
    model_metrics.json
    association_rules.csv  (optional)
```

## MCP-inspired responsible design (lightweight)

- **Host:** Streamlit app.
- **Client:** Internal LLM integration module.
- **Servers/tools:** Analytics output reader, summary generator, optional scraper trigger.
- **Permissions:** Read-only access to processed data; no unrestricted file execution.
- **Logs:** Record prompt inputs/outputs and data source used for each summary.

No full MCP implementation required; this satisfies the dossier’s “responsible architecture” expectation.

## What stays thin

- **Kubeflow:** Local pipeline first; KFP as wrap of same steps.
- **LLM:** Summaries from structured inputs only.
- **MCP:** Design section in report + logging, not full protocol.
- **Association rules:** Only if categorical data is rich enough.

## Definition of “done” per layer

- **Scraping:** Same schema for both sources; 300–500 products; broken fields logged.
- **Preprocessing:** `python -m src.preprocessing.run` reproduces processed data from same raw input.
- **Scoring:** Top-K overall, per category, per shop; formula documented.
- **ML:** One classifier (e.g. RandomForest), one clustering (KMeans), PCA for viz; metrics exported.
- **Dashboard:** Answers “top products?”, “best shops?”, “segments?” from pipeline outputs only.
- **Pipeline:** One-command local run; team can reproduce on another machine.
