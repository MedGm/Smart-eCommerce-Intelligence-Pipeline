"""
Local end-to-end pipeline: scrape -> preprocess -> features -> score -> train -> LLM summary.
Run with: python -m src.pipeline.local_pipeline  or  make pipeline
"""

import sys


def run():
    steps = [
        ("Scraping", "src.scraping.run_scrapers"),
        ("Preprocessing", "src.preprocessing.run"),
        ("Features", "src.features.build_features"),
        ("Scoring", "src.scoring.topk"),
        ("Train classifier", "src.ml.train_classifier"),
        ("Clustering", "src.ml.cluster_products"),
        ("LLM summary", "src.llm.summarizer"),
    ]
    for name, mod in steps:
        print(f"--- {name} ---")
        try:
            run_module = __import__(mod, fromlist=["run"])
            getattr(run_module, "run")()
        except Exception as e:
            print(f"Step {name} failed: {e}")
            # Continue so remaining steps run (e.g. scrape can be empty)
    print("--- Pipeline finished ---")


if __name__ == "__main__":
    run()
    sys.exit(0)
