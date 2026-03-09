"""Smoke test: pipeline stages can be invoked without crashing."""
import pytest


@pytest.fixture
def data_dir(tmp_path):
    (tmp_path / "raw" / "shopify").mkdir(parents=True)
    (tmp_path / "raw" / "woocommerce").mkdir(parents=True)
    (tmp_path / "processed").mkdir(parents=True)
    (tmp_path / "analytics").mkdir(parents=True)
    return tmp_path


def test_preprocessing_run_empty_data(data_dir, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(data_dir))
    from src.preprocessing.run import run
    df = run()
    assert (data_dir / "processed" / "cleaned_products.parquet").exists()
    assert len(df) == 0


def test_scoring_requires_features(data_dir, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(data_dir))
    from src.scoring.topk import run
    run()
    # Should not raise; may write nothing if no features.parquet
