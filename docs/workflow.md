# Development workflow — Smart eCommerce Intelligence Pipeline

**→ Ordered action list for Mohamed & Ismail:** [NEXT_STEPS.md](NEXT_STEPS.md)

## Branching

- **main:** Stable, demo-ready.
- **develop:** Integration branch.
- **Feature branches:** e.g. `feature/scraper-shopify`, `feature/preprocessing`, `feature/dashboard-topk`.

## Pull request discipline

Each PR should state:

1. **What changed** — files and behavior.
2. **What was tested** — manual or automated.
3. **What output artifact was produced** — e.g. `cleaned_products.parquet`, dashboard screenshot.

## Minimal CI (GitHub Actions)

- Install dependencies.
- Run unit tests.
- Run lint (e.g. ruff).
- Optionally: one small pipeline smoke test.

No enterprise MLOps required; enough to show transversal CI/CD.

## Ownership (binôme)

| Zone | Owner | Examples |
|------|--------|----------|
| Data/ML/pipeline backbone | Mohamed | Schema, preprocessing, features, Top-K, ML/DM, orchestration, CI/tests |
| Collection + presentation | Ismail | Scraping adapters, validation, dashboard pages, viz, LLM summary UI, demo polish |
| Shared | Both | Architecture decisions, report, final integration, debugging, oral defense |

## Commands (from repo root)

```bash
make install      # deps
make scrape       # run scrapers
make preprocess   # clean + validate
make features     # feature table
make score        # Top-K
make train        # classifier + clustering
make pipeline     # full local run
make dashboard    # Streamlit
make test         # pytest
make lint         # ruff
```

## Timeline (milestones until 18 May)

| Phase | Deliverables | DoD |
|-------|--------------|-----|
| 1. Architecture freeze | Diagram, schema, target shops, responsibilities | Repo init, issues, scope agreed |
| 2. Scraping MVP | 1 Shopify + 1 WooCommerce scraper, 300–500 products | Same schema, raw JSON, no manual data |
| 3. Data prep + features | Cleaned dataset, feature table, EDA, KPI charts | Reproducible `run` from raw |
| 4. Analytics core | Top-K script, RandomForest, KMeans, PCA, optional rules | Metrics + CSV/JSON/plots, one interpretation per model |
| 5. Dashboard + LLM | Streamlit 4–5 pages, LLM summary section | Uses pipeline outputs only; &lt;5 min demo |
| 6. Orchestration + packaging | Local pipeline, KFP draft, Docker, CI, report draft | One-command run, reproducible, defense script ready |
