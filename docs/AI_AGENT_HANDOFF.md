# AI Agent Handoff — Smart eCommerce Intelligence Pipeline

## Purpose
This document is the operational handoff for maintaining and evolving the pipeline with **reproducibility**, **local/cluster parity**, and **permanent infrastructure fixes**.

## 1) System ideology and architecture

The project is a modular MLOps monolith with two orchestrations:
- **Local orchestration:** `src/pipeline/local_pipeline.py`
- **Cluster orchestration (KFP):** `src/pipeline/kubeflow_pipeline.py` + compiled `kubeflow_smart_ecommerce_pipeline.yaml`

Core flow:
1. Scraping agents (`src/scraping/`) collect multi-store product data.
2. Preprocessing (`src/preprocessing/`) cleans and validates.
3. Feature engineering (`src/features/`) builds scoring/model features.
4. Scoring (`src/scoring/`) computes Top-K outputs.
5. ML/DM (`src/ml/`) runs RF, XGBoost, KMeans, DBSCAN, Apriori.
6. Dashboard (`src/dashboard/`) consumes analytics artifacts and optional LLM summaries.

## 2) Verified "fixed state" for Minikube + KFP

### A) Registry deprecation and image rewrite (gcr.io → working registries)
- **Permanent fix location:** `manifests/overlays/minikube/kustomization.yaml`
- Overlay rewrites broken KFP image references (e.g., Argo controller/executor, MinIO, MySQL).
- `workflow-controller` executor-image arg is patched via:
  - `manifests/overlays/minikube/workflow-controller-args-patch.yaml`

### B) Workflow controller RBAC
- **Permanent fix location:** `manifests/overlays/minikube/cluster-scoped/argo-clusterrole.yaml`
- Adds ClusterRole + ClusterRoleBinding for `argo` ServiceAccount in `kubeflow` namespace.

### C) KFP component isolation (`ModuleNotFoundError: src`)
- **Permanent fix location:** `src/pipeline/kubeflow_pipeline.py`
- Each component injects `sys.path.append("/app")` before importing `src.*` modules.
- Components use `base_image='smart-ecommerce-pipeline:local'` to run local-cluster-built images.

## 3) Non-negotiable MLOps principles

1. **Reproducibility first**
   - Use `scripts/deploy_kfp_minikube.sh` as deployment source of truth.
   - Build image inside Minikube Docker daemon (`eval "$(minikube docker-env)"`).

2. **Permanent fixes only**
   - If Kubernetes resources break, patch overlays/manifests in Git.
   - Do **not** use ad-hoc cluster-only edits as final fixes.

3. **Parity rule**
   - Any new feature/model stage must be added to:
     - Local pipeline (`src/pipeline/local_pipeline.py`)
     - KFP DAG (`src/pipeline/kubeflow_pipeline.py`)
   - Keep analytics outputs consistent for dashboard compatibility.

4. **DAG lifecycle discipline**
   - Compile before run: `make compile-kfp`
   - Then deploy/apply and run in Kubeflow UI.

## 4) Practical maintenance workflow

Preferred operator flow:
1. `make kfp-operator` (deploy + port-forward + verification)
2. Upload/Run `kubeflow_smart_ecommerce_pipeline.yaml` (generated artifact; compile it instead of treating it as hand-edited source)
3. Validate outputs in `data/analytics/`
4. Validate app surface with `make dashboard`
5. Run quality gates: `make test && make lint`

Granular fallback flow:
1. `make compile-kfp`
2. `./scripts/deploy_kfp_minikube.sh`
3. `kubectl port-forward -n kubeflow svc/ml-pipeline-ui 8080:80`

## 5) Validated runtime state (14 March 2026)

- `pytest` is green: 38/38 tests passed.
- Ruff is clean after formatting/import fixes.
- Local analytics outputs are validated: 634 cleaned rows, 634 feature rows, 50 Top-K products.
- Current model/analytics snapshot:
   - RF: accuracy `0.9968`, F1 `0.9923`
   - XGBoost: accuracy `0.9984`, F1 `0.9962`
   - KMeans: 4 clusters
   - DBSCAN: 4 clusters, 55 noise points
   - Association rules: 199 rules
- Minikube/Kubeflow is operational with the overlay fixes applied.
- Latest successful Kubeflow workflow confirms the fixed `src` import path behavior.
- Streamlit dashboard is operational on `localhost:8501`; KFP UI is typically exposed on `localhost:8080` via port-forward.

## 6) Pipeline parity snapshot (current)

Current stage parity is aligned:
- preprocess
- features
- score
- train_classifier (RF)
- train_xgboost
- cluster_kmeans
- cluster_dbscan
- association_rules

Intentional difference:
- **Scraping** and **LLM summary** run outside KFP DAG by design.

## 7) Known operational caveats

- Keep `manifests/base/kfp-upstream` symlink healthy (script manages it).
- Ensure Minikube has sufficient resources (`--cpus 4 --memory 8192` minimum baseline in docs).
- The LLM summary stage still depends on live Gemini API access; pipeline validation is otherwise green without that external call.

## 8) Required references for new contributors

Read in order:
1. `docs/architecture.md`
2. `docs/deploy_minikube.md`
3. `docs/data_quality.md`
4. `docs/tools_coverage.md`
5. `docs/NEXT_STEPS.md`

Then inspect:
- `manifests/overlays/minikube/`
- `src/pipeline/kubeflow_pipeline.py`
- `src/pipeline/local_pipeline.py`
- `scripts/deploy_kfp_minikube.sh`

## 9) Immediate enhancement priorities (post-validation)

1. **Kubeflow operator DX streamlining**
   - Consolidate deploy/update + port-forward + run verification into a predictable developer flow.
   - Ensure early-fail diagnostics and explicit success/health output.
   - Keep a short happy-path guide synchronized with script behavior.

2. **Scraper reliability and data-quality hardening**
   - Tighten validation for required/malformed fields.
   - Improve normalization and deduplication consistency.
   - Handle extraction edge cases (selector drift, missing blocks, partial responses).
   - Increase logging specificity and add fixture-based tests for fragile scraping paths.