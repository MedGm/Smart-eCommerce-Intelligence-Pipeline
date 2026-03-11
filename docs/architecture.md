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
| Scraping | A2A agents for Shopify (Playwright storefront) and WooCommerce (Store API), shared `ProductRecord` schema | Ismail |
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
    pca_viz.csv
    topk_per_category.csv
    topk_per_shop.csv
```

## Orchestration (local + Kubeflow Pipelines)

The pipeline exists in two forms:

- **Local Python pipeline** (`src/pipeline/local_pipeline.py`): runs all stages
  sequentially on the developer machine:
  `scrape -> preprocess -> feature engineering -> score -> train -> cluster -> LLM summary`.
- **Kubeflow Pipelines version** (`src/pipeline/kubeflow_pipeline.py` +
  `kubeflow_smart_ecommerce_pipeline.yaml`): wraps the core ML stages into KFP
  components:

  - `preprocess_op` → call `src.preprocessing.run.run`
  - `features_op` → call `src.features.build_features.run`
  - `score_op` → call `src.scoring.topk.run`
  - `train_classifier_op` → call `src.ml.train_classifier.run`

These components are wired in the `smart_ecommerce_pipeline` DAG and compiled
with `kfp.compiler.Compiler` into a YAML spec that can be uploaded to a
Kubeflow Pipelines instance (e.g. on Minikube or Kind). This satisfies the
dossier’s requirement for a reproducible ML pipeline orchestrated with
Kubeflow, while keeping local development simple.

## MCP-inspired responsible design (lightweight)

- **Host (MCP Host):** Streamlit app (BI dashboard) that orchestrates user interactions and displays outputs.
- **Client (MCP Client):** Internal LLM integration module (`src/llm/summarizer.py`) which calls the LLM and routes tool outputs.
- **Servers/tools (MCP Servers):**
  - Analytics output reader (CSV/Parquet readers for Top-K tables, clusters, metrics).
  - Summary generator (LLM-based narrative over structured analytics).
  - Optional scraper trigger / pipeline launcher (local only).
- **Permissions:** The LLM client only has **read-only** access to processed analytics data. It cannot execute arbitrary code, write to the filesystem beyond append-only logs, or modify scores or raw data. All business logic (scoring, ML, filtering) remains outside the LLM.
- **Logs:** Prompt inputs and truncated responses are persisted in `data/analytics/llm_usage_log.jsonl` with timestamps. This provides traceability for each generated insight and supports later audits in the spirit of the Model Context Protocol.

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
