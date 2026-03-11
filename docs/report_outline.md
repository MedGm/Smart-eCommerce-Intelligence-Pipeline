# Report outline — Smart eCommerce Intelligence Pipeline

Structured to match the dossier's 6 étapes + CI/CD transversal.

---

## 1. Introduction

- **Title:** Smart eCommerce Intelligence Pipeline for Top-K Product Selection.
- **Pitch:** End-to-end pipeline that scrapes eCommerce data (Shopify + WooCommerce), cleans and engineers features, scores and ranks products (Top-K), applies ML/DM (classification, clustering, anomaly detection, association rules), and exposes results through a Streamlit dashboard enriched by LLM-generated summaries, all within a responsible MCP-inspired architecture.
- **Objectives:**
  - Which products are the most promising?
  - Which shops / categories perform best?
  - What patterns emerge from the catalog?
  - How can a decision-maker explore this through a dashboard?

## 2. State of the art / context

- eCommerce data sources: Shopify (Storefront API, storefronts), WooCommerce (REST API, Store API).
- Scraping: requests/BS4 (static), Playwright/Selenium (dynamic), Scrapy (structured).
- Top-K ranking and scoring in eCommerce analytics.
- ML/DM: supervised (RF, XGBoost), unsupervised (KMeans, DBSCAN, PCA), association rules (Apriori).
- BI dashboards: Streamlit, Plotly, Altair, Seaborn.
- LLMs for text synthesis: prompt engineering, chain of thought, responsible use.
- MCP (Model Context Protocol): host/client/server, permissions, logging.

## 3. Methodology

### 3.1 Architecture
- Modular monolith with pipeline stages (see `docs/architecture.md`).
- Local pipeline + Kubeflow-compatible KFP pipeline.

### 3.2 Étape 1 — Scraping (A2A agents)
- **Agent Shopify:** Playwright on Ruggable storefront (dynamic pages, lazy-load scroll, anchor extraction).
- **Agent WooCommerce:** requests + WC Store API (paginated REST JSON).
- **Static enrichment:** requests + BeautifulSoup on product detail pages (meta tags, JSON-LD).
- **Alternatives demonstrated:** Scrapy spider, Shopify Storefront API (GraphQL), WC REST v3 (authenticated).
- **Data extracted:** title, price, old_price, description, category, brand, availability, rating, review_count, geography, scraped_at.
- **Schema:** `ProductRecord` dataclass in `src/scraping/base.py`.

### 3.3 Étape 2 — Top-K + ML/DM
- **Preprocessing:** dedupe by (platform, shop, product_id), standardize prices, normalize text, harmonize categories, handle missing values.
- **Feature engineering:** discount_pct, price_zscore_by_category, rating_weighted_reviews, is_in_stock, description_length, title_length, shop_product_count, category_frequency, price_bucket, popularity_proxy.
- **Top-K scoring:** explainable formula (0.35·rating + 0.30·reviews + 0.20·availability + 0.15·discount). Top-K overall, per category, per shop.
- **Supervised:** RandomForest and XGBoost classifiers predicting "high-potential" (top 20% by score). Evaluation: accuracy, precision, recall, F1, confusion matrix.
- **Unsupervised:** KMeans (4 clusters, silhouette ≈ 0.47), DBSCAN (outlier detection). Evaluation: silhouette score, cluster interpretation, PCA 2D visualization.
- **Association rules:** Apriori (mlxtend) on one-hot encoded category/brand/price_bucket/stock/discount/platform. Evaluation: support, confidence, lift.

### 3.4 Étape 3 — Kubeflow Pipelines
- Local Python pipeline (`local_pipeline.py`): 10 sequential steps.
- KFP pipeline (`kubeflow_pipeline.py`): 4 components (preprocess, features, score, train) compiled to YAML via `kfp.compiler.Compiler`.
- Can be uploaded to a KFP instance on Minikube/Kind.

### 3.5 Étape 4 — Dashboard BI
- Streamlit app with 8 sections: Overview KPIs, Top-K products, Shop comparison, KMeans segmentation (PCA/Plotly), DBSCAN outliers, ML model comparison, Association rules, LLM insights.
- Visualization tools: Plotly (PCA scatter), Altair (category bar chart), Seaborn (price histogram).
- Dashboard consumes only pipeline outputs (CSV/Parquet); no business logic in the UI.

### 3.6 Étape 5 — LLM enrichment
- **Primary:** Gemini (google-genai) for executive summaries from structured analytics.
- **Alternative adapters:** OpenAI-compatible client, LangChain demo script.
- **Prompt engineering:** structured JSON input (top categories, best shop, cluster sizes). LLM never receives raw product rows.
- **Logging:** prompt inputs + truncated responses in `llm_usage_log.jsonl`.

### 3.7 Étape 6 — MCP responsible architecture
- **MCP Host:** Streamlit app.
- **MCP Client:** LLM summarizer module.
- **MCP Servers:** AnalyticsReaderServer (read-only, allowed-file list), SummaryGeneratorServer (LLM + logging).
- **Permissions:** read-only analytics, no code execution, append-only logs.
- **Logs:** `llm_usage_log.jsonl`, `mcp_access_log.jsonl`.
- Reference: [Model Context Protocol specification](https://modelcontextprotocol.io/specification/2025-03-26).

### 3.8 CI/CD transversal
- GitHub Actions: install deps → pytest → ruff check + format.
- Docker: Dockerfile + docker-compose.yml (pipeline and dashboard profiles).
- KFP YAML for pipeline-as-code.

## 4. Implementation

- **Stack:** Python, pandas, numpy, scikit-learn, XGBoost, mlxtend, Playwright, BeautifulSoup, Streamlit, Plotly, Altair, Seaborn, google-genai, kfp, Docker, GitHub Actions.
- **Repo structure:** `src/` (scraping, preprocessing, features, scoring, ml, llm, pipeline, dashboard, mcp), `scripts/` (demos), `tests/`, `notebooks/`, `docs/`, `data/`.
- **Key design decisions:** modular monolith (not microservices), LLM on aggregates only, thin KFP (local-first), explicit scoring formula.

## 5. Experiments & evaluation

- **Classification (RF, XGBoost):** accuracy, precision, recall, F1, confusion matrix. Discuss perfect scores and small sample size.
- **Clustering (KMeans):** silhouette score, cluster sizes, business interpretation per cluster.
- **Clustering (DBSCAN):** number of clusters, number of outliers, interpretation of noise points.
- **Association rules:** support, confidence, lift. Top rules and business meaning.
- **Top-K:** score distribution, sensitivity to weight changes, top products per category/shop.
- **Dashboard:** can a decision-maker answer the 4 main questions? Traceability of every insight.

## 6. Results & discussion

- Main results: tables and figures from pipeline outputs.
- **Known limitations:**
  - Small dataset (565 products; dossier recommends 2000–5000).
  - Shopify products lack detailed fields (price, rating, category) in v1.
  - WooCommerce ratings are zero; popularity proxy is discount-driven.
  - Classifier F1=1.0 is an artifact of small, clean separation; not generalizable.
- **Scope choices:** why monolith, why this formula, why LLM only for summaries.

## 7. Conclusion

- Summary of the delivered system (all 6 étapes implemented).
- Reproducibility: one-command local run, Docker, KFP YAML.
- **Improvements planned:** richer scraping (product detail pages), more stores, cross-validation, better category inference.

## 8. References & appendix

- Dossier technique (FST Tanger, LSI 2, DM & SID 2025/2026).
- [MCP specification](https://modelcontextprotocol.io/specification/2025-03-26).
- Shopify Storefront API docs, WooCommerce REST API docs.
- scikit-learn, XGBoost, mlxtend, kfp documentation.
- Appendix: full ProductRecord schema, prompt templates, extra plots.

---

**Oral defense:** Every design choice should be explainable. Be ready to answer: why this scoring formula? Why LLM only for summaries? What do the clusters mean? Why is F1=1.0 not trustworthy? What would you improve with more time?
