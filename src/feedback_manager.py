"""
feedback_manager.py — FitChecker Feedback & History
====================================================
PURPOSE:
  Provide higher-level feedback operations on top of data_manager.py.
  Records outfit selections, ratings, wear events, and provides
  history retrieval for the Feedback & History page.

IMPORTANT DISTINCTION:
  "Recommended"  → FitChecker showed the outfit to the user.
  "Selected"     → User clicked "Choose this outfit".
  "Worn"         → User confirmed they actually wore it.
  These are three different states and are tracked separately.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime, timedelta

import pandas as pd

from src.data_manager import (
    load_feedback, save_feedback_record,
    load_wardrobe, record_wear_event, save_outfit,
    load_outfits,
)


def record_outfit_selection(
    outfit: dict,
    occasion: str,
    weather: str = "Any",
) -> tuple[str, str]:
    """
    Save a generated outfit and create an initial feedback record
    marking it as "accepted" (selected by user, not yet worn).

    Returns (outfit_id, feedback_id).
    """
    # Persist outfit
    outfit_data = {
        "item_ids":         ";".join(outfit.get("item_ids", [])),
        "occasion":         occasion,
        "generated_score":  outfit.get("score", 0.0),
        "score_components": json.dumps(outfit.get("score_components", {})),
        "is_sample":        False,
    }
    outfit_id = save_outfit(outfit_data)

    # Initial feedback — accepted=True, worn=False (user hasn't worn it yet)
    fb_data = {
        "outfit_id":  outfit_id,
        "user_rating": 0,
        "accepted":    True,
        "worn":        False,
        "occasion":    occasion,
        "weather":     weather,
        "notes":       "",
        "is_sample":   False,
    }
    feedback_id = save_feedback_record(fb_data)
    return outfit_id, feedback_id


def record_wear_confirmation(
    feedback_id: str,
    outfit_id: str,
    item_ids: list[str],
    occasion: str,
    rating: int = 0,
    notes: str = "",
    worn_date: str = None,
) -> bool:
    """
    Update a feedback record to mark the outfit as actually worn,
    increment wear counts for each item, and record in wear history.

    Returns True on success.
    """
    df = load_feedback()
    mask = df["feedback_id"] == feedback_id
    if not mask.any():
        return False

    df.loc[mask, "worn"]        = True
    df.loc[mask, "user_rating"] = rating if rating > 0 else df.loc[mask, "user_rating"]
    df.loc[mask, "notes"]       = notes
    df.to_csv(__import__("config.settings", fromlist=["FEEDBACK_FILE"]).FEEDBACK_FILE, index=False)

    # Record wear events (increments times_worn per item)
    record_wear_event(item_ids, outfit_id, occasion, worn_date)
    return True


def save_rating(feedback_id: str, rating: int, notes: str = "") -> bool:
    """Update rating and notes on an existing feedback record."""
    from config.settings import FEEDBACK_FILE
    df = load_feedback()
    mask = df["feedback_id"] == feedback_id
    if not mask.any():
        return False
    if not (1 <= rating <= 5):
        raise ValueError("Rating must be between 1 and 5.")
    df.loc[mask, "user_rating"] = rating
    if notes:
        df.loc[mask, "notes"] = notes
    df.to_csv(FEEDBACK_FILE, index=False)
    return True


def get_recent_outfit_ids(days: int = 7) -> list[str]:
    """Return outfit_ids that were worn within the last `days` days."""
    df = load_feedback()
    if df.empty:
        return []
    cutoff = datetime.now() - timedelta(days=days)
    worn   = df[df["worn"].astype(str).str.lower().isin(("true", "1"))]
    recent = worn[
        pd.to_datetime(worn["timestamp"], errors="coerce") >= cutoff
    ]
    return recent["outfit_id"].dropna().tolist()


def get_history_display(limit: int = 50) -> pd.DataFrame:
    """
    Return a merged feedback + outfit table suitable for display.
    Sorted by timestamp descending (most recent first).
    """
    fb = load_feedback()
    outfits = load_outfits()
    if fb.empty:
        return pd.DataFrame()

    if not outfits.empty:
        merged = fb.merge(outfits[["outfit_id", "item_ids", "generated_score"]],
                          on="outfit_id", how="left")
    else:
        merged = fb.copy()
        merged["item_ids"]       = ""
        merged["generated_score"] = ""

    merged = merged.sort_values("timestamp", ascending=False).head(limit)
    return merged


def get_feedback_stats() -> dict:
    """Return aggregate statistics from all feedback records."""
    df = load_feedback()
    if df.empty:
        return {
            "total_recommendations": 0,
            "total_selected":        0,
            "total_worn":            0,
            "avg_rating":            0.0,
            "acceptance_rate":       0.0,
        }

    total    = len(df)
    selected = df["accepted"].astype(str).str.lower().isin(("true", "1")).sum()
    worn     = df["worn"].astype(str).str.lower().isin(("true", "1")).sum()
    ratings  = pd.to_numeric(df["user_rating"], errors="coerce")
    rated    = ratings[ratings > 0]
    avg_rating = round(rated.mean(), 2) if not rated.empty else 0.0
    acceptance = round(selected / total * 100, 1) if total > 0 else 0.0

    return {
        "total_recommendations": total,
        "total_selected":        int(selected),
        "total_worn":            int(worn),
        "avg_rating":            avg_rating,
        "acceptance_rate":       acceptance,
    }
