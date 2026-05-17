import json
import importlib
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import numpy as np
import pytest


def _make_features_df():
    rng = np.random.default_rng(42)
    n = 60
    return pd.DataFrame({
        "price": rng.uniform(10, 500, n),
        "dq_score": rng.uniform(0, 1, n),
        "is_in_stock": rng.integers(0, 2, n).astype(float),
        "review_count": rng.integers(0, 200, n).astype(float),
        "shop_name": rng.choice(["shopA", "shopB", "shopC"], n),
    })


def test_rf_model_saved_to_disk(tmp_path):
    with patch("src.config.data_dir", return_value=tmp_path):
        from src.ml import train_classifier
        importlib.reload(train_classifier)
        df = _make_features_df()
        with patch("src.ml.train_classifier.load_features", return_value=df):
            train_classifier.run()
    model_path = tmp_path / "models" / "random_forest.joblib"
    assert model_path.exists(), f"Model not saved at {model_path}"


def test_rf_predictions_written_to_analytics(tmp_path):
    with patch("src.config.data_dir", return_value=tmp_path):
        from src.ml import train_classifier
        importlib.reload(train_classifier)
        df = _make_features_df()
        with patch("src.ml.train_classifier.load_features", return_value=df):
            train_classifier.run()
    preds_path = tmp_path / "analytics" / "rf_predictions.csv"
    assert preds_path.exists(), "rf_predictions.csv not written"
    preds = pd.read_csv(preds_path)
    assert "rf_proba" in preds.columns


def test_xgb_model_saved_to_disk(tmp_path):
    pytest.importorskip("xgboost")
    with patch("src.config.data_dir", return_value=tmp_path):
        from src.ml import train_xgboost
        importlib.reload(train_xgboost)
        df = _make_features_df()
        with patch("src.ml.train_xgboost.load_features", return_value=df):
            train_xgboost.run()
    model_path = tmp_path / "models" / "xgboost.joblib"
    assert model_path.exists(), f"XGBoost model not saved at {model_path}"


def test_xgb_predictions_written_to_analytics(tmp_path):
    pytest.importorskip("xgboost")
    with patch("src.config.data_dir", return_value=tmp_path):
        from src.ml import train_xgboost
        importlib.reload(train_xgboost)
        df = _make_features_df()
        with patch("src.ml.train_xgboost.load_features", return_value=df):
            train_xgboost.run()
    preds_path = tmp_path / "analytics" / "xgb_predictions.csv"
    assert preds_path.exists(), "xgb_predictions.csv not written"
    preds = pd.read_csv(preds_path)
    assert "xgb_proba" in preds.columns
