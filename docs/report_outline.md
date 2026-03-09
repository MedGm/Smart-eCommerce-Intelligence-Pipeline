# Report outline — Smart eCommerce Intelligence Pipeline

Use this to structure the written/oral report and stay aligned with the dossier.

## 1. Introduction & positioning

- **Title:** Smart eCommerce Intelligence Pipeline for Top-K Product Selection.
- **Pitch:** Pipeline that collects eCommerce data (Shopify/WooCommerce), prepares and scores products, applies ML/data mining, and exposes insights via Streamlit + LLM synthesis.
- **Objectives:** Which products are most promising? Which shops/categories perform best? What patterns emerge? How does the dashboard support decisions?

## 2. State of the art / context

- eCommerce data sources and scraping approaches (A2A, APIs, static/dynamic).
- Top-K and ranking in eCommerce.
- ML/DM in product analytics (classification, clustering, association rules).
- Dashboards and BI storytelling.

## 3. Methodology

- **Architecture:** Modular monolith, pipeline stages, diagram (see `docs/architecture.md`).
- **Data:** Sources (Shopify, WooCommerce), canonical schema, storage layout.
- **Preprocessing:** Deduplication, normalization, validation, reproducibility.
- **Feature engineering:** List of features, popularity proxy (no fake sales).
- **Top-K scoring:** Formula (e.g. 0.35·rating + 0.30·reviews + 0.20·availability + 0.15·discount), Top-K overall / per category / per shop.
- **ML/DM:** RandomForest (high-potential prediction), KMeans (segments), PCA (visualization), optional association rules.
- **Orchestration:** Local pipeline, Kubeflow-compatible design.
- **Dashboard:** Pages (overview, Top-K, shop comparison, segmentation, LLM insights).
- **LLM:** Role limited to summaries from aggregated metrics; no raw fact invention.
- **Responsible design:** MCP-inspired (host/client/tools, permissions, logging).

## 4. Implementation

- Stack: Python, pandas, scikit-learn, Playwright, BeautifulSoup, Streamlit, Plotly, Docker, GitHub Actions.
- Repo structure and key modules.
- CI: install, test, lint, (optional) smoke run.

## 5. Experiments & evaluation

- **Classification:** Accuracy, precision, recall, F1, confusion matrix.
- **Clustering:** Silhouette, cluster sizes, business interpretation.
- **Top-K:** Score distribution, sensitivity to weights, top products per category/shop.
- **Dashboard:** Can a decision-maker answer the main questions quickly? Traceability of every insight to data.

## 6. Results & discussion

- Main results (tables, figures from pipeline outputs).
- Limitations (no real sales data, popularity proxy, thin Kubeflow/LLM).
- Scope choices and why they are defensible.

## 7. Conclusion

- Summary of delivered system.
- Reproducibility and one-command run.
- Possible extensions (more sources, richer rules, full KFP deployment).

## 8. References & appendix

- Dossier references.
- Appendix: full schema, extra plots, prompt examples.

---

**Oral defense:** Every design choice should be explainable (why monolith, why this formula, why LLM only for summaries, what is “done” per block).
