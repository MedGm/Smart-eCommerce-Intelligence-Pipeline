# Smart eCommerce Intelligence Pipeline for Top-K Product Selection

**Repo:** [GitHub — MedGm/Smart-eCommerce-Intelligence-Pipeline](https://github.com/MedGm/Smart-eCommerce-Intelligence-Pipeline)

**One-sentence pitch:** A pipeline that collects eCommerce product data from Shopify/WooCommerce, prepares and scores products, applies ML/data mining for ranking and segmentation, and exposes insights through a Streamlit dashboard with lightweight LLM-based synthesis.

## Core objective

Deliver a reproducible system that answers:

- **Which products are the most promising?**
- **Which shops/categories perform best?**
- **What patterns emerge from the catalog?**
- **How can a decision-maker explore this through a dashboard?**

## Architecture (high-level)

```
[ Shopify / WooCommerce Sources ] → [ Scraping Adapters ] → [ Raw Data Store ]
         → [ Preprocessing + QA ] → [ Feature Engineering ]
         → [ Top-K Scoring + ML/DM Analysis ]
         → [ Analytics Outputs ] + [ LLM Summaries ] → [ Streamlit Dashboard ]
         → Docker + CI + Pipeline Run
```

Modular monolith with pipeline stages. See [docs/architecture.md](docs/architecture.md).

## Stack

| Layer        | Tools |
|-------------|--------|
| Scraping    | Playwright, requests, BeautifulSoup |
| Storage     | JSON (raw), Parquet/CSV (processed) |
| ML/DM       | scikit-learn, (optional) XGBoost, mlxtend |
| Dashboard   | Streamlit, Plotly |
| Orchestration | Python pipeline, KFP-compatible components |
| CI          | GitHub Actions |

## Quick start

```bash
# Setup
python -m venv .venv && source .venv/bin/activate  # or: .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env   # edit if needed

# Run full pipeline locally
make pipeline

# Or step by step
make scrape
make preprocess
make features
make score
make train
make dashboard   # then open http://localhost:8501
```

## Repo structure

```
smart-ecommerce-pipeline/
├── data/           # raw, processed, analytics (gitignored except structure)
├── docs/           # architecture, workflow, report outline
├── src/            # scraping, preprocessing, features, scoring, ml, llm, pipeline, dashboard
├── tests/          # unit and pipeline tests
├── notebooks/      # EDA and experiments
├── Makefile        # pipeline and dev targets
└── docker-compose.yml
```

## Team & ownership

- **Mohamed:** data schema, preprocessing, feature engineering, Top-K scoring, ML/DM models, pipeline orchestration, CI/testing.
- **Ismail:** scraping adapters, source validation, dashboard pages, visualizations, LLM summary UI, demo polish.
- **Shared:** architecture decisions, report, integration, oral defense.

## Timeline (milestones until 18 May)

1. **Architecture freeze** — schema, diagram, scope, responsibilities.
2. **Scraping MVP** — Shopify + WooCommerce, 300–500 products, same schema.
3. **Data prep + features** — cleaned dataset, feature table, EDA.
4. **Analytics core** — Top-K, RandomForest, KMeans, PCA, optional rules.
5. **Dashboard + LLM** — Streamlit 4–5 pages, LLM summary section.
6. **Orchestration + packaging** — local pipeline, KFP draft, Docker, CI, report.

## License

Project for academic use (course deadline 18 May).
