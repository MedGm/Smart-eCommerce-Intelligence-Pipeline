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

1. `make compile-kfp`
2. `./scripts/deploy_kfp_minikube.sh`
3. `kubectl port-forward -n kubeflow svc/ml-pipeline-ui 8080:80`
4. Upload/Run `kubeflow_smart_ecommerce_pipeline.yaml`
5. Validate outputs in `data/analytics/`
6. Validate app surface with `make dashboard`
7. Run quality gates: `make test && make lint`

## 5) Pipeline parity snapshot (current)

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

## 6) Known operational caveats

- The deployment script logs `:latest` in some messages while build tag is `:local`; rely on actual build command/tag, not log text.
- Keep `manifests/base/kfp-upstream` symlink healthy (script manages it).
- Ensure Minikube has sufficient resources (`--cpus 4 --memory 8192` minimum baseline in docs).

## 7) Required references for new contributors

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