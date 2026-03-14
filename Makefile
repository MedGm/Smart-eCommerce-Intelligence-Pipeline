# Smart eCommerce Intelligence Pipeline — Makefile
# Run from repo root: make <target>

PYTHON ?= python
PIP ?= pip

.PHONY: install install-dev scrape preprocess features score train pipeline dashboard test lint clean

install:
	$(PIP) install -r requirements.txt

install-dev: install
	$(PIP) install pytest pytest-cov ruff
	playwright install chromium 2>/dev/null || true

# Pipeline stages (implemented in src)
scrape:
	$(PYTHON) -m src.scraping.run_scrapers

preprocess:
	$(PYTHON) -m src.preprocessing.run

features:
	$(PYTHON) -m src.features.build_features

score:
	$(PYTHON) -m src.scoring.topk

train:
	$(PYTHON) -m src.ml.train_classifier
	$(PYTHON) -m src.ml.cluster_products

pipeline:
	$(PYTHON) -m src.pipeline.local_pipeline

compile-kfp:
	$(PYTHON) -c "from kfp import compiler; from src.pipeline.kubeflow_pipeline import smart_ecommerce_pipeline; compiler.Compiler().compile(pipeline_func=smart_ecommerce_pipeline, package_path='kubeflow_smart_ecommerce_pipeline.yaml')"
	@echo "✓ Compiled kubeflow_smart_ecommerce_pipeline.yaml"

dashboard:
	PYTHONPATH=. streamlit run src/dashboard/app.py --server.port 8501

test:
	$(PYTHON) -m pytest tests/ -v

lint:
	ruff check src tests
	ruff format --check src tests

clean:
	rm -rf .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
