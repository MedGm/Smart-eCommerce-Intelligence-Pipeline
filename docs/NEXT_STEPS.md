# Project status & next steps — Mohamed & Ismail

**Repo:** [github.com/MedGm/Smart-eCommerce-Intelligence-Pipeline](https://github.com/MedGm/Smart-eCommerce-Intelligence-Pipeline)  
**Status date:** 14 March 2026

---

## Current validated state

### Quality gates

| Area | Status | Current result |
|------|--------|----------------|
| Tests | **Green** | 38/38 pytest tests passed |
| Lint / format | **Green** | Ruff clean after auto-fixing formatting/import issues |
| KFP compile | **Green** | 8-component DAG compiled successfully with `kfp==2.16.0` |
| Local pipeline outputs | **Green** | Preprocess, features, score, RF, XGBoost, KMeans, DBSCAN, rules all produced artifacts |
| Minikube / Kubeflow | **Green** | Latest workflow run succeeded on the fixed Minikube overlay |
| Dashboard | **Green** | Streamlit dashboard responds on `localhost:8501` |

### Data and analytics snapshot

| Stage | Current output |
|-------|----------------|
| Cleaned dataset | 634 rows × 15 columns |
| Feature matrix | 634 rows × 25 columns |
| Top-K ranking | 50 scored products |
| RandomForest | accuracy = 0.9968, F1 = 0.9923 |
| XGBoost | accuracy = 0.9984, F1 = 0.9962 |
| KMeans | 4 clusters |
| DBSCAN | 4 clusters, 55 noise points |
| Association rules | 199 rules |

### Platform state

| Capability | Current state |
|-----------|----------------|
| Scraping | Multi-store Shopify + WooCommerce collection is operational |
| Local orchestration | `src/pipeline/local_pipeline.py` remains the full 10-step local flow |
| Cluster orchestration | `src/pipeline/kubeflow_pipeline.py` runs the validated 8-stage analytics DAG |
| Minikube deployment | Overlay + deployment script fix image registry and Argo RBAC issues |
| LLM summary | Implemented, but live validation still depends on external Gemini API access |
| MCP architecture | Implemented and wired into dashboard + summarizer |

---

## Enhancement phase priorities

### Current sprint focus (agreed)

#### Sprint item A — Kubeflow operator DX improvement

Objective:
- Make deploy + port-forward + verification close to one command for local operator workflows.

Definition of done:
- One command boots or updates the operator workflow.
- Port-forwarding starts automatically or through a predictable subcommand.
- Run verification is built in with explicit health/status output.
- Failures stop early with useful diagnostics.
- A short “happy path” developer guide is documented.

#### Sprint item B — Scraper and data-quality hardening

Objective:
- Improve extraction robustness and data trustworthiness before downstream scoring/model runs.

Definition of done:
- Add validation rules for required fields and malformed records.
- Improve deduplication and normalization.
- Handle scraper edge cases (missing selectors, layout drift, partial responses).
- Log data-quality issues with enough detail for quick debugging.
- Add sample-based tests/fixtures for fragile scraping paths.

---

### P1 — Dashboard BI refinement

| # | Owner | Task |
|---|-------|------|
| 1.1 | Both | Redesign the dashboard visual identity so it feels intentional and presentation-ready, not like a default Streamlit theme. |
| 1.2 | Both | Improve the Top-K experience with stronger ranking storytelling, better KPI surfacing, and clearer visual hierarchy. |
| 1.3 | Both | Add export-friendly, formatted views for ranked products and shop/category breakdowns. |
| 1.4 | Both | Prepare polished screenshots for report/demo use once the new design is stable. |

### P2 — Kubeflow operational polish (mapped to Sprint item A)

| # | Owner | Task |
|---|-------|------|
| 2.1 | Mohamed | Keep `scripts/deploy_kfp_minikube.sh` as the single deployment path and improve operator-facing logs where useful. |
| 2.2 | Mohamed | Make cluster run verification easier: workflow status, pod health, UI access, and artifact checks. |
| 2.3 | Mohamed | Keep local/cluster parity strict whenever a new stage or artifact is introduced. |

### P3 — Data enrichment and quality hardening (mapped to Sprint item B)

| # | Owner | Task |
|---|-------|------|
| 3.1 | Ismail | Improve missing price/category/rating coverage for stores that still have partial metadata. |
| 3.2 | Both | Add stronger stores or more category-rich collections to improve downstream model generalization. |
| 3.3 | Mohamed | Re-run preprocessing and feature engineering after each meaningful scraper/data upgrade. |
| 3.4 | Both | Add stricter malformed-record validation and explicit reject/repair paths. |
| 3.5 | Both | Strengthen dedup + normalization rules across title/shop/category/url fields. |
| 3.6 | Ismail | Add fixtures/tests for scraping paths that are sensitive to selector/layout drift. |

### P4 — Model explainability and analytics clarity

| # | Owner | Task |
|---|-------|------|
| 4.1 | Mohamed | Add short business-oriented interpretations for KMeans and DBSCAN segments. |
| 4.2 | Mohamed | Improve communication of feature importance and score composition in the dashboard/report. |
| 4.3 | Mohamed | Re-run rule mining and clustering after richer category coverage lands. |

### P5 — Delivery polish

| # | Owner | Task |
|---|-------|------|
| 5.1 | Both | Validate the Gemini summary end to end using the configured API key. |
| 5.2 | Mohamed | Re-test the Docker path for the pipeline/dashboard packaging story. |
| 5.3 | Both | Update the report and oral-defense narrative using the now-validated Minikube + dashboard flow. |

---

## Quick reference

```bash
make scrape        # run Shopify + WooCommerce scrapers
make preprocess    # clean + validate
make features      # build feature table
make score         # generate Top-K analytics outputs
make train         # RF + KMeans local training shortcut
make compile-kfp   # compile the Kubeflow pipeline spec
make dashboard     # launch Streamlit on :8501
make test          # pytest
make lint          # ruff check + format --check
```
