# What to do next (in order) — Mohamed & Ismail

Use this as your checklist. Tick items as you go. Target: **18 May**.

**Repo:** [github.com/MedGm/Smart-eCommerce-Intelligence-Pipeline](https://github.com/MedGm/Smart-eCommerce-Intelligence-Pipeline)  
`git clone git@github.com:MedGm/Smart-eCommerce-Intelligence-Pipeline.git`

---

## Phase 1 — Architecture freeze (do first, together)

**Scope fixed:** Shopify + WooCommerce only (no extra sources or blocks).

| # | Who | Action | Done |
|---|-----|--------|------|
| 1.1 | Both | **Agree on scope freeze:** no new blocks, no new sources beyond Shopify + WooCommerce. | ☑ |
| 1.2 | Both | **Pick 1–2 real target shops** (one Shopify, one WooCommerce) for scraping. Write URLs in `docs/target_shops.md` or in `.env` comments. _Locked: Shopify = Ruggable, WooCommerce = Dan-O's Seasoning._ | ☑ |
| 1.3 | Mohamed | **Add architecture diagram** in `docs/diagrams/` (draw.io or Mermaid). Refer to it in the report. | ☐ |
| 1.4 | Both | **Create `develop` branch.** Work on feature branches, merge into `develop`, then `main` when stable. | ☐ |
| 1.5 | Both | **Optional:** Create GitHub issues for Phase 2–5 so you have a backlog. | ☐ |

**Definition of done:** Repo is the single source of truth, you both know who does what, and you won’t change scope mid-project.

---

## Phase 2 — Scraping MVP (Ismail leads, Mohamed supports)

| # | Who | Action | Done |
|---|-----|--------|------|
| 2.1 | Ismail | **Implement Shopify scraper** in `src/scraping/shopify.py`: fetch products (API or Playwright), map to `ProductRecord`, save to `data/raw/shopify/products.json`. | ☐ |
| 2.2 | Ismail | **Implement WooCommerce scraper** in `src/scraping/woocommerce.py`: same idea, save to `data/raw/woocommerce/products.json`. | ☐ |
| 2.3 | Ismail | **Run `make scrape`** and get **at least 300–500 product records total** (combined). Log broken/missing fields; don’t fake data. | ☐ |
| 2.4 | Mohamed | **Quick review:** Check that raw JSON matches `ProductRecord` fields and that `make preprocess` runs without errors. | ☐ |

**Definition of done:** `data/raw/shopify/` and/or `data/raw/woocommerce/` contain real product JSON; pipeline runs from raw → processed.

---

## Phase 3 — Data prep + features (Mohamed leads)

| # | Who | Action | Done |
|---|-----|--------|------|
| 3.1 | Mohamed | **Run full pipeline** with the new raw data: `make preprocess`, `make features`. Fix any bugs in `src/preprocessing` or `src/features` if columns differ. | ☐ |
| 3.2 | Mohamed | **EDA notebook:** In `notebooks/eda.ipynb`, load `cleaned_products.parquet` and `features.parquet`, add describe(), value_counts(), and 2–3 KPI charts (e.g. price distribution, rating by category). | ☐ |
| 3.3 | Mohamed | **Document** in report or README: how duplicates are handled, how missing values are filled, list of features. | ☐ |
| 3.4 | Ismail | **Optional:** Add simple validation in scraping (e.g. check required fields before saving) so bad rows don’t pile up. | ☐ |

**Definition of done:** One command regenerates processed + feature data from raw; EDA shows the data story.

---

## Phase 4 — Analytics core (Mohamed leads)

| # | Who | Action | Done |
|---|-----|--------|------|
| 4.1 | Mohamed | **Run `make score` and `make train`** on real data. Confirm `data/analytics/` has: `topk_products.csv`, `topk_per_category.csv`, `topk_per_shop.csv`, `model_metrics.json`, `clusters.csv`, `pca_viz.csv`. | ☐ |
| 4.2 | Mohamed | **Write 1–2 sentences per model** in report or `docs/`: what RandomForest predicts, what the clusters mean (e.g. “premium low-engagement”, “affordable high-engagement”). | ☐ |
| 4.3 | Mohamed | **Optional:** If you have enough categorical data, add association rules in `src/ml/rules.py` and export to `association_rules.csv`. | ☐ |
| 4.4 | Ismail | **Optional:** Skim analytics outputs so you know what the dashboard will show. | ☐ |

**Definition of done:** All metrics and CSV/plots exist; you can explain each model in the oral.

---

## Phase 5 — Dashboard + LLM (Ismail leads, Mohamed supports)

| # | Who | Action | Done |
|---|-----|--------|------|
| 5.1 | Ismail | **Polish Streamlit pages** in `src/dashboard/app.py`: Overview, Top-K, Shop comparison, Segmentation (PCA), LLM Insights. Add filters (category, shop) where useful. | ☐ |
| 5.2 | Ismail | **Connect LLM:** In `src/llm/summarizer.py`, add real API call (OpenAI or compatible) using aggregated data only. Keep logging of prompt/response. | ☐ |
| 5.3 | Ismail | **Demo run:** Record or rehearse a &lt;5 min flow: open dashboard → show KPIs → Top-K → clusters → LLM summary. | ☐ |
| 5.4 | Mohamed | **Smoke test:** Run `make pipeline` then `make dashboard` on your machine; confirm no broken paths and that every number traces to pipeline outputs. | ☐ |

**Definition of done:** Dashboard answers “top products?”, “best shops?”, “segments?”; LLM summary is from data only; demo is smooth.

---

## Phase 6 — Orchestration + packaging (shared)

| # | Who | Action | Done |
|---|-----|--------|------|
| 6.1 | Mohamed | **Kubeflow draft:** In `src/pipeline/kubeflow_pipeline.py`, wrap at least 2–3 steps as KFP components (e.g. preprocess, score, train). Enough to show “pipeline as code” in the report. | ☐ |
| 6.2 | Mohamed | **Docker:** Ensure `docker-compose.yml` and `Dockerfile` work (e.g. `docker compose --profile pipeline run app` or `docker compose --profile dashboard run dashboard`). | ☐ |
| 6.3 | Both | **CI:** Push to GitHub; confirm Actions run (install, pytest, ruff). Fix any failing tests or lint. | ☐ |
| 6.4 | Both | **Report draft** using `docs/report_outline.md`. Add screenshots (dashboard, pipeline run), architecture diagram, evaluation tables. | ☐ |
| 6.5 | Both | **Oral defense script:** Who says what; 1–2 min per block; how you’ll answer “why this formula?”, “why LLM only for summaries?”, “what is MCP-inspired?”. | ☐ |

**Definition of done:** One-command run works; report and oral are ready; project is reproducible on another machine.

---

## Suggested order (summary)

1. **This week:** Phase 1 (architecture freeze + target shops) + start Phase 2 (Ismail: scrapers).
2. **As soon as raw data exists:** Phase 3 (Mohamed: preprocess + features + EDA).
3. **Then:** Phase 4 (Mohamed: scoring + ML) → Phase 5 (Ismail: dashboard + LLM).
4. **Before 18 May:** Phase 6 (KFP draft, Docker, CI, report, oral script).

**Parallel where possible:** While Ismail builds scrapers (Phase 2), Mohamed can finalize the diagram and EDA template. After Phase 3, Mohamed does Phase 4 while Ismail can start dashboard layout and LLM prompts.
