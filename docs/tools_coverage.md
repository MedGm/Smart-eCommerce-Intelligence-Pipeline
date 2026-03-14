# Tools coverage — dossier vs implementation

Maps every tool mentioned in the dossier technique to where it is used in the project.

## Étape 1 — Scraping A2A

| Dossier tool | Implementation | File |
|-------------|----------------|------|
| requests | WooCommerce Store API calls, BS4 enrichment | `src/scraping/woocommerce.py`, `src/scraping/enrich_bs4.py` |
| BeautifulSoup | Static HTML parsing for Shopify product pages | `src/scraping/enrich_bs4.py` |
| Selenium / Playwright | Dynamic storefront scraping for Ruggable | `src/scraping/shopify.py` (Playwright) |
| Scrapy | Minimal spider demo for Ruggable collections | `scripts/scrapy_spider.py` |
| Shopify Storefront API | GraphQL example script (token-based) | `scripts/shopify_storefront_example.py` |
| WooCommerce REST API | Store API (main agent) + REST v3 example | `src/scraping/woocommerce.py`, `scripts/woocommerce_rest_example.py` |

## Étape 2 — ML/DM

| Dossier tool | Implementation | File | Output |
|-------------|----------------|------|--------|
| pandas, numpy | Data prep and feature engineering | `src/preprocessing/`, `src/features/` | `cleaned_products.parquet`, `features.parquet` |
| scikit-learn | RandomForest, KMeans, DBSCAN, PCA | `src/ml/train_classifier.py`, `src/ml/cluster_products.py`, `src/ml/dbscan_products.py` | `model_metrics.json`, `clusters.csv`, `pca_viz.csv`, `dbscan_clusters.csv` |
| XGBoost | Classifier comparison | `src/ml/train_xgboost.py` | `model_metrics_xgboost.json` |
| Association rules (Apriori) | mlxtend frequent_patterns | `src/ml/rules.py` | `association_rules.csv` |

## Étape 3 — Kubeflow Pipelines

| Dossier tool | Implementation | File |
|-------------|----------------|------|
| Kubeflow / kfp SDK | Pipeline definition (8 components: preprocess, features, score, RF, XGBoost, KMeans, DBSCAN, rules) | `src/pipeline/kubeflow_pipeline.py` |
| Compiled YAML | Generated KFP pipeline spec (compiled on demand, not source of truth) | `kubeflow_smart_ecommerce_pipeline.yaml` |
| Docker | Containerization | `Dockerfile`, `docker-compose.yml` |
| Local pipeline | 10-step Python orchestrator | `src/pipeline/local_pipeline.py` |
| Minikube deployment | Automated local-cluster deployment and overlay application | `scripts/deploy_kfp_minikube.sh`, `manifests/overlays/minikube/` |

## Étape 4 — Dashboard BI

| Dossier tool | Implementation | Where in dashboard |
|-------------|----------------|-------------------|
| Streamlit | Main framework | `src/dashboard/app.py` |
| Plotly | Top-K ranking, PCA scatter plot, shop analysis, model visuals | Multiple sections |
| Altair | Category bar chart | Overview section |
| Seaborn | Price histogram | Overview section |
| Matplotlib | Backend for Seaborn | Overview section |

## Étape 5 — LLM

| Dossier tool | Implementation | File |
|-------------|----------------|------|
| Gemini (Google) | Primary summarizer | `src/llm/summarizer.py` |
| OpenAI API | Alternative adapter | `src/llm/openai_client.py` |
| LangChain | Demo script | `scripts/langchain_summary_demo.py` |
| Prompt engineering | Structured templates | `src/llm/prompts.py` |

## Étape 6 — MCP

| Dossier concept | Implementation | File |
|----------------|----------------|------|
| MCP Host | Streamlit app | `src/dashboard/app.py` |
| MCP Client | LLM summarizer module | `src/llm/summarizer.py` |
| MCP Server | AnalyticsReaderServer, SummaryGeneratorServer | `src/mcp/architecture.py` |
| Permissions | Read-only, allowed-file list | `src/mcp/architecture.py` |
| Logs | `llm_usage_log.jsonl`, `mcp_access_log.jsonl` runtime logs | `data/analytics/` |

## CI/CD transversal

| Dossier tool | Implementation | File |
|-------------|----------------|------|
| GitHub Actions | Install, pytest, ruff | `.github/workflows/ci.yml` |
| Docker | Pipeline + dashboard containers | `Dockerfile`, `docker-compose.yml` |
| Tests | 38 automated tests across config, preprocessing, features, ML, scoring, MCP, LLM and pipeline modules | `tests/` |
