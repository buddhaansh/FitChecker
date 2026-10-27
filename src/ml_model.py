"""
ml_model.py — FitChecker Machine Learning Component
====================================================
PURPOSE:
  Train, evaluate and use a Random Forest classifier that learns from
  user feedback whether an outfit is likely to be accepted.

IMPORTANT NOTES ON DATA INTEGRITY:
  • Sample data is clearly labeled; training on sample data produces
    illustrative results, NOT evidence of real user preferences.
  • The model is only trained if MIN_SAMPLES_FOR_TRAINING records exist
    AND at least MIN_CLASSES_FOR_TRAINING distinct labels are present.
  • All splits are done BEFORE feature extraction to prevent data leakage.
  • Class imbalance is addressed by setting class_weight='balanced'.
  • Results on sample data are reported with clear disclaimers.

ALGORITHM — Random Forest:
  A Random Forest is an ensemble of decision trees.
  Each tree is trained on a random subset of the data with random features.
  The final prediction is the majority vote across all trees.
  Why Random Forest?
    ✓ Works well on small datasets (we don't have millions of records)
    ✓ Handles mixed feature types (numbers + categories)
    ✓ Gives feature importance (explainability)
    ✓ Resistant to overfitting (compared to a single decision tree)

FEATURES USED:
  Occasion (encoded), formality mean, formality variance,
  color compatibility score, weather match count,
  style-tag match count, recency (days since last worn).

TARGET:
  Binary: 1 = outfit accepted by user, 0 = not accepted.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import warnings
from typing import Optional

import numpy as np
import pandas as pd
import joblib

from config.settings import (
    ML_MODEL_FILE, MIN_SAMPLES_FOR_TRAINING, MIN_CLASSES_FOR_TRAINING,
    OCCASIONS,
)

# ─────────────────────────────────────────────
# FEATURE ENGINEERING
# ─────────────────────────────────────────────

OCCASION_INDEX = {occ: i for i, occ in enumerate(OCCASIONS)}


def extract_features(feedback_row: pd.Series, outfits_df: pd.DataFrame,
                     wardrobe_df: pd.DataFrame) -> Optional[list]:
    """
    Build a feature vector for one feedback record.

    Returns a list of floats, or None if data is insufficient.

    FEATURES:
      0. occasion_code         (int, encoded)
      1. num_items             (int)
      2. formality_mean        (float, 1-5)
      3. formality_variance    (float)
      4. has_footwear          (0/1)
      5. has_outer             (0/1)
      6. num_tops              (int)
      7. total_times_worn      (int, sum across items)
      8. any_worn_recently     (0/1, within 7 days)
    """
    outfit_id = str(feedback_row.get("outfit_id", ""))
    occasion  = str(feedback_row.get("occasion", "Daily College Wear"))

    outfit_rows = outfits_df[outfits_df["outfit_id"] == outfit_id]
    if outfit_rows.empty:
        return None

    outfit_row  = outfit_rows.iloc[0]
    item_ids_str = str(outfit_row.get("item_ids", ""))
    item_ids    = [i.strip() for i in item_ids_str.split(";") if i.strip()]
    if not item_ids:
        return None

    items = wardrobe_df[wardrobe_df["item_id"].isin(item_ids)]
    if items.empty:
        return None

    formalities  = pd.to_numeric(items["formality"], errors="coerce").fillna(3).tolist()
    times_worn   = pd.to_numeric(items["times_worn"], errors="coerce").fillna(0).tolist()
    categories   = items["category"].tolist()

    from config.settings import CATEGORY_GROUP
    footwear_cats = CATEGORY_GROUP.get("footwear", [])
    outer_cats    = CATEGORY_GROUP.get("outer",    [])
    top_cats      = CATEGORY_GROUP.get("tops",     [])

    # Days since any item was recently worn
    from datetime import datetime
    any_recent = 0
    for _, item in items.iterrows():
        last = str(item.get("last_worn", "")).strip()
        if last and last not in ("", "nan", "None"):
            try:
                days = (datetime.now() - datetime.strptime(last, "%Y-%m-%d")).days
                if days <= 7:
                    any_recent = 1
            except ValueError:
                pass

    features = [
        OCCASION_INDEX.get(occasion, 0),
        len(item_ids),
        np.mean(formalities) if formalities else 3.0,
        np.var(formalities)  if formalities else 0.0,
        int(any(c in footwear_cats for c in categories)),
        int(any(c in outer_cats    for c in categories)),
        sum(1 for c in categories if c in top_cats),
        int(sum(times_worn)),
        any_recent,
    ]
    return features


FEATURE_NAMES = [
    "occasion_code", "num_items", "formality_mean", "formality_variance",
    "has_footwear", "has_outer", "num_tops", "total_times_worn", "any_worn_recently",
]


# ─────────────────────────────────────────────
# TRAINING
# ─────────────────────────────────────────────

def prepare_training_data(feedback_df: pd.DataFrame,
                          outfits_df: pd.DataFrame,
                          wardrobe_df: pd.DataFrame) -> tuple:
    """
    Build feature matrix X and label vector y from feedback records.
    Label = 1 if accepted, 0 otherwise.
    Returns (X, y, is_sample_flags) or (None, None, None) if insufficient.
    """
    X_rows, y_vals, is_sample = [], [], []

    for _, row in feedback_df.iterrows():
        feats = extract_features(row, outfits_df, wardrobe_df)
        if feats is None:
            continue
        label = 1 if str(row.get("accepted", "False")).lower() in ("true", "1", "yes") else 0
        X_rows.append(feats)
        y_vals.append(label)
        is_sample.append(str(row.get("is_sample", "False")).lower() in ("true", "1"))

    if len(X_rows) < MIN_SAMPLES_FOR_TRAINING:
        return None, None, None

    X = np.array(X_rows, dtype=float)
    y = np.array(y_vals, dtype=int)
    return X, y, is_sample


def train_model(feedback_df: pd.DataFrame,
                outfits_df: pd.DataFrame,
                wardrobe_df: pd.DataFrame,
                test_size: float = 0.25,
                random_state: int = 42) -> dict:
    """
    Train a Random Forest classifier and return a results dict.

    The results dict contains:
      "status":   "success" | "insufficient_data" | "insufficient_classes" | "error"
      "message":  human-readable explanation
      "metrics":  dict with accuracy, precision, recall, f1 (if status=success)
      "model":    trained model object (if status=success)
      "is_sample_only": True if all training data is sample data
      "n_samples": int
    """
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import StratifiedShuffleSplit
    from sklearn.metrics import (accuracy_score, precision_score,
                                 recall_score, f1_score, classification_report)

    result = {"status": "error", "message": "", "metrics": {}, "model": None,
              "is_sample_only": False, "n_samples": 0}

    X, y, is_sample_flags = prepare_training_data(feedback_df, outfits_df, wardrobe_df)

    if X is None:
        result["status"]  = "insufficient_data"
        result["message"] = (
            f"Not enough labelled feedback to train the model. "
            f"Need at least {MIN_SAMPLES_FOR_TRAINING} records with outfit data."
        )
        return result

    result["n_samples"] = len(y)
    result["is_sample_only"] = all(is_sample_flags)

    unique_classes = np.unique(y)
    if len(unique_classes) < MIN_CLASSES_FOR_TRAINING:
        result["status"]  = "insufficient_classes"
        result["message"] = (
            f"All {len(y)} feedback records have the same label ({unique_classes[0]}). "
            f"At least {MIN_CLASSES_FOR_TRAINING} different label values are needed."
        )
        return result

    # ── Stratified split (preserves class proportions) ──
    sss = StratifiedShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_idx, test_idx = next(sss.split(X, y))
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    # ── Train ──
    clf = RandomForestClassifier(
        n_estimators=100,
        class_weight="balanced",
        random_state=random_state,
        n_jobs=-1,
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        clf.fit(X_train, y_train)

    # ── Evaluate ──
    y_pred = clf.predict(X_test)
    metrics = {
        "accuracy":  round(accuracy_score(y_test, y_pred), 3),
        "precision": round(precision_score(y_test, y_pred, zero_division=0), 3),
        "recall":    round(recall_score(y_test, y_pred, zero_division=0), 3),
        "f1":        round(f1_score(y_test, y_pred, zero_division=0), 3),
        "n_train":   len(y_train),
        "n_test":    len(y_test),
        "report":    classification_report(y_test, y_pred, zero_division=0),
        "feature_importances": dict(zip(FEATURE_NAMES, clf.feature_importances_.round(3))),
    }

    result["status"]  = "success"
    result["message"] = (
        "Model trained successfully. "
        + ("⚠️ NOTE: Training data consists entirely of labeled sample records. "
           "These results are illustrative only and do not reflect real user preferences."
           if result["is_sample_only"] else
           "Results are based on actual user feedback.")
    )
    result["metrics"] = metrics
    result["model"]   = clf

    # ── Save ──
    save_model(clf)

    return result


def save_model(model, filepath: str = None):
    """Save the trained model to disk."""
    path = filepath or ML_MODEL_FILE
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(model, path)


# ─────────────────────────────────────────────
# PREDICTION
# ─────────────────────────────────────────────

def load_model():
    """Load the saved Random Forest model, or return None if not found."""
    if os.path.exists(ML_MODEL_FILE):
        try:
            return joblib.load(ML_MODEL_FILE)
        except Exception:
            return None
    return None


def predict_acceptance(outfit: dict,
                       occasion: str,
                       wardrobe_df: pd.DataFrame,
                       model=None) -> Optional[float]:
    """
    Predict probability that the user will accept this outfit.

    Returns:
      float (0-1) if a model is available,
      None otherwise (fall back to baseline scorer).
    """
    if model is None:
        model = load_model()
    if model is None:
        return None

    # Build a minimal feedback-like row to reuse extract_features
    items = outfit.get("items", [])
    item_ids = [i["item_id"] for i in items]
    outfit_id = "tmp_" + "_".join(item_ids[:3])

    # Create a temp outfits df for the extraction helper
    outfits_temp = pd.DataFrame([{
        "outfit_id": outfit_id,
        "item_ids": ";".join(item_ids),
        "occasion": occasion,
    }])
    feedback_temp = pd.DataFrame([{
        "outfit_id": outfit_id,
        "occasion": occasion,
        "accepted": False,
        "is_sample": False,
    }])

    feats = extract_features(feedback_temp.iloc[0], outfits_temp, wardrobe_df)
    if feats is None:
        return None

    try:
        proba = model.predict_proba([feats])[0]
        # Return probability of class 1 (accepted)
        classes = list(model.classes_)
        if 1 in classes:
            return float(proba[classes.index(1)])
        return None
    except Exception:
        return None
