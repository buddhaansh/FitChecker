"""
tests/test_ml_model.py — Tests for machine learning training, feature extraction, and prediction
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pandas as pd
import numpy as np

from src.ml_model import (
    extract_features,
    prepare_training_data,
    train_model,
    predict_acceptance,
    save_model,
    load_model,
    FEATURE_NAMES,
)


def _sample_wardrobe():
    return pd.DataFrame([
        {"item_id": "i1", "category": "T-Shirt", "color": "White", "formality": 2, "times_worn": 3},
        {"item_id": "i2", "category": "Jeans", "color": "Blue", "formality": 2, "times_worn": 2},
        {"item_id": "i3", "category": "Sneakers", "color": "White", "formality": 1, "times_worn": 5},
    ])


def _sample_outfits():
    return pd.DataFrame([
        {"outfit_id": "o1", "item_ids": "i1;i2;i3", "occasion": "Daily College Wear", "generated_score": 85.0},
        {"outfit_id": "o2", "item_ids": "i1;i2", "occasion": "Casual Outing", "generated_score": 75.0},
    ])


def test_extract_features_valid():
    wardrobe = _sample_wardrobe()
    outfits = _sample_outfits()
    feedback_row = pd.Series({"outfit_id": "o1", "occasion": "Daily College Wear"})

    feat = extract_features(feedback_row, outfits, wardrobe)
    assert feat is not None
    assert len(feat) == len(FEATURE_NAMES)
    # Check that formality mean is ~1.67
    assert 1.0 <= feat[2] <= 5.0


def test_extract_features_missing_outfit():
    wardrobe = _sample_wardrobe()
    outfits = _sample_outfits()
    feedback_row = pd.Series({"outfit_id": "missing_outfit", "occasion": "Daily College Wear"})

    feat = extract_features(feedback_row, outfits, wardrobe)
    assert feat is None


def test_train_model_insufficient_data():
    wardrobe = _sample_wardrobe()
    outfits = _sample_outfits()
    # Only 2 feedback rows (below MIN_SAMPLES_FOR_TRAINING which is 10)
    feedback_df = pd.DataFrame([
        {"feedback_id": "f1", "outfit_id": "o1", "accepted": True, "is_sample": False},
        {"feedback_id": "f2", "outfit_id": "o2", "accepted": False, "is_sample": False},
    ])

    result = train_model(feedback_df, outfits, wardrobe)
    assert result["status"] == "insufficient_data"
    assert "at least" in result["message"]


def test_train_model_insufficient_classes():
    wardrobe = _sample_wardrobe()
    outfits = pd.DataFrame([
        {"outfit_id": f"o_{i}", "item_ids": "i1;i2;i3", "occasion": "Daily College Wear", "generated_score": 80.0}
        for i in range(25)
    ])
    # 25 rows, but all have accepted=True (insufficient classes)
    feedback_df = pd.DataFrame([
        {"feedback_id": f"f{i}", "outfit_id": f"o_{i}", "accepted": True, "is_sample": False}
        for i in range(25)
    ])

    result = train_model(feedback_df, outfits, wardrobe)
    assert result["status"] == "insufficient_classes"


def test_train_model_success():
    wardrobe = _sample_wardrobe()
    outfits = pd.DataFrame([
        {"outfit_id": f"o_{i}", "item_ids": "i1;i2;i3", "occasion": "Daily College Wear", "generated_score": 80.0}
        for i in range(20)
    ])
    # 20 rows with mixed True and False labels
    feedback_df = pd.DataFrame([
        {"feedback_id": f"f{i}", "outfit_id": f"o_{i}", "accepted": (i % 2 == 0), "is_sample": True}
        for i in range(20)
    ])

    result = train_model(feedback_df, outfits, wardrobe)
    assert result["status"] == "success"
    assert result["model"] is not None
    assert "accuracy" in result["metrics"]
    assert result["is_sample_only"] is True


def test_predict_acceptance_no_model(monkeypatch):
    monkeypatch.setattr("src.ml_model.load_model", lambda: None)
    wardrobe = _sample_wardrobe()
    outfit = {"items": [{"item_id": "i1"}, {"item_id": "i2"}]}
    prob = predict_acceptance(outfit, "Daily College Wear", wardrobe, model=None)
    assert prob is None
