"""
Local end-to-end pipeline: scrape -> preprocess -> features -> score -> train -> LLM summary.
Run with: python -m src.pipeline.local_pipeline  or  make pipeline
"""

import sys

from src.config import get_logger

logger = get_logger(__name__)


def run():
    steps = [
        ("Scraping", "src.scraping.run_scrapers"),
        ("Preprocessing", "src.preprocessing.run"),
        ("Features", "src.features.build_features"),
        ("Scoring", "src.scoring.topk"),
        ("Train classifier (RF)", "src.ml.train_classifier"),
        ("Train classifier (XGBoost)", "src.ml.train_xgboost"),
        ("Clustering (KMeans)", "src.ml.cluster_products"),
        ("Clustering (DBSCAN)", "src.ml.dbscan_products"),
        ("Association rules", "src.ml.rules"),
        ("LLM summary", "src.llm.summarizer"),
    ]
    for name, mod in steps:
        logger.info("--- %s ---", name)
        try:
            run_module = __import__(mod, fromlist=["run"])
            getattr(run_module, "run")()
        except Exception as e:
            logger.error("Step %s failed: %s", name, e)
            # Continue so remaining steps run (e.g. scrape can be empty)
    logger.info("--- Pipeline finished ---")


if __name__ == "__main__":
    run()
    sys.exit(0)
