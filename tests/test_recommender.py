"""
tests/test_recommender.py — Tests for baseline scoring and ranking
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src.recommender import (
    score_occasion_suitability,
    score_color_compatibility,
    score_style_formality,
    score_weather_suitability,
    score_personal_preference,
    score_outfit,
    rank_outfits,
    repetition_penalty,
)


def _item(category="T-Shirt", color="White", formality=2, style_tags="Casual",
          weather="Any", last_worn="", color_hex=""):
    return {
        "item_id":    "test_item",
        "category":   category,
        "color":      color,
        "color_hex":  color_hex,
        "formality":  formality,
        "style_tags": style_tags,
        "weather":    weather,
        "last_worn":  last_worn,
    }


def _outfit(items, score=0.0):
    return {
        "template": "Top + Bottom + Footwear",
        "item_ids": [i["item_id"] for i in items],
        "items":    items,
        "groups":   ["tops", "bottoms", "footwear"],
        "score":    score,
    }


# ─────────────────────────────────────────────
# COMPONENT SCORES
# ─────────────────────────────────────────────

def test_occasion_score_returns_in_range():
    items = [_item(formality=2, style_tags="Casual")]
    score = score_occasion_suitability(items, "Daily College Wear")
    assert 0 <= score <= 100


def test_occasion_score_casual_outfit_for_casual_occasion():
    """A casual outfit for a casual occasion should score higher than for a formal one."""
    items = [_item(formality=1, style_tags="Casual")]
    casual_score = score_occasion_suitability(items, "Daily College Wear")
    formal_score = score_occasion_suitability(items, "Formal Event")
    assert casual_score > formal_score


def test_color_compatibility_score_in_range():
    items = [_item(color="White"), _item(color="Navy Blue")]
    score = score_color_compatibility(items)
    assert 0 <= score <= 100


def test_white_navy_is_high_compatibility():
    """White + Navy Blue is a classic pairing and should score well."""
    items = [_item(color="White"), _item(color="Navy Blue"), _item(color="White")]
    score = score_color_compatibility(items)
    assert score >= 75


def test_style_formality_coherent_outfit_scores_high():
    """Items with the same formality level should be coherent."""
    items = [_item(formality=2), _item(formality=2), _item(formality=2)]
    score = score_style_formality(items, "Daily College Wear")
    assert score >= 90   # Zero variance → near 100


def test_style_formality_mixed_outfit_scores_lower():
    """Mixing very formal with very casual should produce a lower coherence score."""
    items = [_item(formality=1), _item(formality=5)]
    score = score_style_formality(items, "Daily College Wear")
    assert score < 80


def test_weather_score_any_returns_100():
    score = score_weather_suitability([_item()], "Any")
    assert score == 100.0


def test_weather_score_compatible_item():
    item  = _item(weather="Hot")
    score = score_weather_suitability([item], "Hot")
    assert score == 100.0


def test_personal_preference_boost_for_liked_color():
    prefs = {"preferred_colors": ["White"], "avoided_colors": [], "preferred_styles": []}
    items = [_item(color="White")]
    score = score_personal_preference(items, prefs)
    assert score > 70   # Should be boosted above the neutral 70


def test_personal_preference_penalty_for_avoided_color():
    prefs = {"preferred_colors": [], "avoided_colors": ["Red"], "preferred_styles": []}
    items = [_item(color="Red")]
    score = score_personal_preference(items, prefs)
    assert score < 70   # Should be penalised below the neutral 70


# ─────────────────────────────────────────────
# REPETITION PENALTY
# ─────────────────────────────────────────────

def test_no_penalty_when_no_wear_history():
    items = [_item(last_worn="")]
    assert repetition_penalty(items) == 0.0


def test_penalty_applied_when_worn_today():
    from datetime import date
    today = date.today().strftime("%Y-%m-%d")
    items = [_item(last_worn=today)]
    penalty = repetition_penalty(items)
    assert penalty > 0


def test_no_penalty_for_old_item():
    items = [_item(last_worn="2020-01-01")]   # More than 7 days ago
    assert repetition_penalty(items) == 0.0


# ─────────────────────────────────────────────
# FULL SCORING AND RANKING
# ─────────────────────────────────────────────

def test_score_outfit_returns_0_to_100():
    items  = [_item(formality=2, style_tags="Casual"), _item(formality=2)]
    outfit = _outfit(items)
    result = score_outfit(outfit, "Daily College Wear")
    assert 0 <= result["score"] <= 100


def test_score_outfit_has_components():
    items  = [_item(), _item()]
    outfit = _outfit(items)
    result = score_outfit(outfit, "Daily College Wear")
    assert "score_components" in result
    assert "occasion_suitability" in result["score_components"]


def test_score_outfit_has_explanation():
    items  = [_item(), _item()]
    outfit = _outfit(items)
    result = score_outfit(outfit, "Daily College Wear")
    assert len(result["explanation"]) > 0


def test_ranking_sorts_descending():
    """Higher-scored outfits should appear first in rankings."""
    item_casual = [_item(formality=2, style_tags="Casual"),
                   _item(formality=2, style_tags="Casual"),
                   _item(formality=2)]
    item_formal = [_item(formality=5, style_tags="Formal"),
                   _item(formality=5, style_tags="Formal"),
                   _item(formality=5)]
    outfits = [_outfit(item_casual), _outfit(item_formal)]
    ranked  = rank_outfits(outfits, "Daily College Wear", top_n=2)
    assert ranked[0]["score"] >= ranked[1]["score"]


def test_ranking_returns_at_most_top_n():
    outfits = [_outfit([_item()]) for _ in range(10)]
    ranked  = rank_outfits(outfits, "Daily College Wear", top_n=3)
    assert len(ranked) <= 3


def test_ranking_empty_input():
    ranked = rank_outfits([], "Daily College Wear")
    assert ranked == []
