"""
Kubeflow-compatible pipeline: wrap local steps as KFP components.

This pipeline mirrors the local Python pipeline:
    preprocess -> features -> score -> train_classifier

It is meant to be compiled with kfp and run on a Kubeflow Pipelines
installation (e.g. on Minikube or a managed KFP cluster).
"""

from __future__ import annotations

from kfp import dsl


@dsl.component
def preprocess_op():
    """Run preprocessing step (from raw JSON to cleaned parquet)."""
    from src.preprocessing.run import run

    run()


@dsl.component
def features_op():
    """Run feature engineering step (from cleaned to features parquet)."""
    from src.features.build_features import run

    run()


@dsl.component
def score_op():
    """Run Top-K scoring and export analytics CSVs."""
    from src.scoring.topk import run

    run()


@dsl.component
def train_classifier_op():
    """Train RandomForest classifier and export metrics."""
    from src.ml.train_classifier import run

    run()


@dsl.pipeline(name="smart-ecommerce-intelligence-pipeline")
def smart_ecommerce_pipeline():
    """Kubeflow pipeline DAG definition."""
    p = preprocess_op()
    f = features_op().after(p)
    s = score_op().after(f)
    train_classifier_op().after(s)


def run() -> None:
    """Entry point used when calling this module as a script.

    In local dev, this just prints a short help message to explain how
    to compile the KFP pipeline to a YAML spec.
    """
    print(
        "Kubeflow pipeline is defined as `smart_ecommerce_pipeline`.\n"
        "Compile it with kfp, for example:\n"
        "  from kfp import compiler\n"
        "  from src.pipeline.kubeflow_pipeline import smart_ecommerce_pipeline\n"
        "  compiler.Compiler().compile(\n"
        "      pipeline_func=smart_ecommerce_pipeline,\n"
        "      package_path='kubeflow_smart_ecommerce_pipeline.yaml',\n"
        "  )"
    )
