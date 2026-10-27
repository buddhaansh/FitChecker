"""
tests/test_feedback_manager.py — Tests for feedback tracking and outfit history
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pandas as pd

from src.data_manager import add_garment, load_wardrobe
from src.feedback_manager import (
    record_outfit_selection,
    record_wear_confirmation,
    save_rating,
    get_recent_outfit_ids,
    get_history_display,
    get_feedback_stats,
)


def _seed_wardrobe_item():
    return add_garment({
        "category": "T-Shirt",
        "color": "White",
        "formality": 2,
    })


def test_feedback_stats_empty():
    stats = get_feedback_stats()
    assert stats["total_recommendations"] == 0
    assert stats["total_selected"] == 0
    assert stats["total_worn"] == 0
    assert stats["avg_rating"] == 0.0
    assert stats["acceptance_rate"] == 0.0


def test_record_outfit_selection():
    item_id = _seed_wardrobe_item()
    outfit = {
        "item_ids": [item_id],
        "score": 88.5,
        "score_components": {"color": 90, "occasion": 87},
    }
    outfit_id, feedback_id = record_outfit_selection(outfit, occasion="Daily College Wear", weather="Warm")
    assert outfit_id.startswith("outfit_")
    assert feedback_id.startswith("fb_")

    stats = get_feedback_stats()
    assert stats["total_recommendations"] == 1
    assert stats["total_selected"] == 1
    assert stats["total_worn"] == 0  # not yet confirmed worn
    assert stats["acceptance_rate"] == 100.0


def test_record_wear_confirmation():
    item_id = _seed_wardrobe_item()
    outfit = {"item_ids": [item_id], "score": 90.0}
    outfit_id, feedback_id = record_outfit_selection(outfit, occasion="Party / Night Out")

    # Confirm wear
    success = record_wear_confirmation(
        feedback_id=feedback_id,
        outfit_id=outfit_id,
        item_ids=[item_id],
        occasion="Party / Night Out",
        rating=5,
        notes="Looked great!",
    )
    assert success is True

    stats = get_feedback_stats()
    assert stats["total_worn"] == 1
    assert stats["avg_rating"] == 5.0

    # Verify wear count in wardrobe was incremented
    wardrobe = load_wardrobe()
    item_row = wardrobe[wardrobe["item_id"] == item_id].iloc[0]
    assert int(item_row["times_worn"]) == 1


def test_save_rating_validation():
    item_id = _seed_wardrobe_item()
    outfit = {"item_ids": [item_id], "score": 75.0}
    outfit_id, feedback_id = record_outfit_selection(outfit, occasion="Gym / Sports")

    # Rating must be between 1 and 5
    with pytest.raises(ValueError):
        save_rating(feedback_id, rating=6)

    with pytest.raises(ValueError):
        save_rating(feedback_id, rating=0)

    # Valid rating
    assert save_rating(feedback_id, rating=4, notes="Solid fit") is True
    stats = get_feedback_stats()
    assert stats["avg_rating"] == 4.0


def test_get_history_display():
    item_id = _seed_wardrobe_item()
    outfit = {"item_ids": [item_id], "score": 85.0}
    record_outfit_selection(outfit, occasion="Casual Outing")

    history = get_history_display(limit=10)
    assert not history.empty
    assert len(history) == 1
    assert history.iloc[0]["occasion"] == "Casual Outing"
