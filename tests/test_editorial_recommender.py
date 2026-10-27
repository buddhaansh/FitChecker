"""
tests/test_editorial_recommender.py — Tests for editorial curation, pairing drawer, and packing capsules
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pandas as pd

from src.editorial_recommender import (
    generate_editorial_recommendations,
    get_pairings_for_garment,
    generate_packing_capsule,
    find_best_match_for_item,
    generate_eloquent_shuffle_outfit,
)
from src.skin_tone_analyzer import get_default_profile


def _sample_wardrobe():
    data = [
        {"item_id": "i1", "category": "T-Shirt", "color": "White", "formality": 1, "times_worn": 2, "style_tags": "Casual"},
        {"item_id": "i2", "category": "Shirt", "color": "Olive Green", "formality": 3, "times_worn": 1, "style_tags": "Smart Casual"},
        {"item_id": "i3", "category": "Jeans", "color": "Dark Blue", "formality": 2, "times_worn": 5, "style_tags": "Casual"},
        {"item_id": "i4", "category": "Chinos", "color": "Khaki", "formality": 3, "times_worn": 3, "style_tags": "Smart Casual"},
        {"item_id": "i5", "category": "Sneakers", "color": "White", "formality": 2, "times_worn": 6, "style_tags": "Casual"},
        {"item_id": "i6", "category": "Formal Shoes", "color": "Black", "formality": 4, "times_worn": 1, "style_tags": "Formal"},
        {"item_id": "i7", "category": "Jacket", "color": "Olive Green", "formality": 2, "times_worn": 2, "style_tags": "Casual"},
    ]
    return pd.DataFrame(data)


def test_generate_editorial_recommendations():
    wardrobe = _sample_wardrobe()
    plan_info = {
        "plan_title": "Dinner with friends, polished but comfortable",
        "occasion": "Date",
        "weather": "Any",
        "target_formality": 3,
    }
    profile = get_default_profile()

    cards = generate_editorial_recommendations(wardrobe, plan_info, profile)
    assert len(cards) == 3
    card_types = [c["card_type"] for c in cards]
    assert "BEST MATCH" in card_types
    assert "MORE RELAXED" in card_types
    assert "MORE POLISHED" in card_types

    for card in cards:
        assert card["match_percentage"] > 70
        assert len(card["critique"]) > 20
        assert len(card["items"]) >= 2
        assert "face_score" in card
        assert "body_score" in card


def test_get_pairings_for_garment():
    wardrobe = _sample_wardrobe()
    target_garment = wardrobe.iloc[1].to_dict()  # Olive green shirt

    pairings = get_pairings_for_garment(target_garment, wardrobe, style_filter="ALL", season="Autumn", limit=3)
    assert len(pairings) > 0
    top_pair = pairings[0]
    assert "match_percentage" in top_pair
    assert "explanation" in top_pair
    assert top_pair["match_percentage"] >= 70


def test_generate_packing_capsule():
    wardrobe = _sample_wardrobe()
    capsule = generate_packing_capsule("Lisbon", days=3, wardrobe_df=wardrobe, season="Autumn")
    assert capsule["destination"] == "Lisbon"
    assert capsule["days"] == 3
    assert len(capsule["itinerary"]) == 3
    assert len(capsule["capsule_items"]) > 0


def test_find_best_match_for_item():
    wardrobe = _sample_wardrobe()
    target_top = wardrobe.iloc[0].to_dict()  # White T-shirt
    profile = get_default_profile()

    matches = find_best_match_for_item(wardrobe, target_top, profile)
    assert len(matches) > 0
    top_match = matches[0]
    assert "total_score" in top_match
    assert top_match["total_score"] >= 60
    assert "summary" in top_match


def test_generate_eloquent_shuffle_outfit():
    wardrobe = _sample_wardrobe()
    profile = get_default_profile()

    # Test free shuffle
    outfit = generate_eloquent_shuffle_outfit(wardrobe, profile, temperature=0.7)
    assert outfit is not None
    assert "total_score" in outfit
    assert "items" in outfit
    assert len(outfit["items"]) >= 2
    assert "eloquent_desc" in outfit
    assert len(outfit["eloquent_desc"]) > 10

    # Test locked item shuffle
    locked = {"tops": "i2"}  # Olive shirt locked
    outfit_locked = generate_eloquent_shuffle_outfit(wardrobe, profile, locked_items=locked, temperature=0.7)
    assert outfit_locked is not None
    top_ids = [it["item_id"] for it in outfit_locked["items"]]
    assert "i2" in top_ids

