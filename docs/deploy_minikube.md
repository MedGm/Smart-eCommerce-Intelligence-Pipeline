# Kubeflow & MLOps Deployment Guide

This document fulfills the pedagogical requirements for **Étape 3 : Kubeflow Pipelines pour l'orchestration ML**, specifically demonstrating how to deploy the pipeline locally using **Minikube**.

## 1. MLOps Architecture

Our ML lifecycle is orchestrated using Kubeflow Pipelines (KFP). The pipeline is defined in Python (`src/pipeline/kubeflow_pipeline.py`) as a Directed Acyclic Graph (DAG) consisting of 8 distinct components:

1. **Preprocess OP**: Cleans raw JSON data into Parquet formats.
2. **Features OP**: Engineers numerical and categorical features for ML.
3. **Score OP**: Applies the Top-K ranking algorithm.
4. **Train Classifier OP**: Trains the RandomForest model and outputs metrics.
5. **Train XGBoost OP**: Trains the XGBoost model and outputs metrics.
6. **Cluster KMeans OP**: Unsupervised product segmentation with PCA projection.
7. **Cluster DBSCAN OP**: Unsupervised anomaly/outlier detection.
8. **Association Rules OP**: Apriori market-basket analysis.

The entire pipeline is containerized using `Dockerfile` (based on `python:3.11-slim`).

## 2. Local Kubernetes Deployment (Minikube)

To simulate a production Kubernetes cluster locally, we use Minikube. We have provided an automated deployment script to streamline the MLOps process.

### Step 1: Start your local cluster
Ensure Docker desktop is running, then initialize Minikube with sufficient resources for ML processing:
```bash
minikube start --cpus 4 --memory 8192
```

### Step 2: Deploy the Pipeline
Run the provided MLOps deployment script:
```bash
./scripts/deploy_kfp_minikube.sh
```

**What this script does automatically:**
1. Verifies Minikube is active.
2. Runs `make compile-kfp` to compile the Python DAG into a standard `.yaml` file.
3. Maps your local terminal to Minikube's internal Docker daemon using `eval $(minikube docker-env)`.
4. Builds the `smart-ecommerce-pipeline:local` Docker image directly inside the cluster, avoiding the need for an external container registry like DockerHub.
5. Applies the permanent Minikube overlay fixes stored under `manifests/overlays/minikube/`.

### Validated current state

As of 14 March 2026, this deployment path is working end to end:

- Minikube cluster starts and remains healthy.
- Kubeflow core services run in the `kubeflow` namespace.
- The latest workflow run succeeded after the `sys.path.append("/app")` component fix.
- The KFP UI is reachable through:

```bash
kubectl port-forward -n kubeflow svc/ml-pipeline-ui 8080:80
```

- The Streamlit dashboard can be launched locally in parallel with:

```bash
make dashboard
```

### Step 3: Execute in Kubeflow
Once the script completes successfully:

1. Open your local Kubeflow Pipelines dashboard (e.g., typically `http://localhost:8080` depending on your KFP installation).
2. Click **Upload Pipeline** and select the freshly generated `kubeflow_smart_ecommerce_pipeline.yaml` located in the root directory.
3. Click **Create Run**.
4. The pipeline will pull the local `smart-ecommerce-pipeline:local` image and execute the 8-stage DAG across Kubernetes pods. The dashboard will display a visual graph of the successful execution.
