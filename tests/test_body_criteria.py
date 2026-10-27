"""
tests/test_body_criteria.py — Tests for body build and silhouette flattery scoring
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src.body_criteria import (
    BODY_BUILDS,
    HEIGHT_PROFILES,
    score_body_silhouette_compatibility,
)


def test_body_builds_exist():
    assert "athletic_v_taper" in BODY_BUILDS
    assert "lean_slim" in BODY_BUILDS
    assert "broad_inverted_triangle" in BODY_BUILDS
    assert "husky_oval" in BODY_BUILDS
    assert "regular_balanced" in BODY_BUILDS


def test_athletic_v_taper_flattery():
    # Fitted/Regular tops + Straight bottoms should score high on athletic build
    items = [
        {"category": "T-Shirt", "fit": "Fitted", "color": "White"},
        {"category": "Jeans", "fit": "Regular", "color": "Blue"},
        {"category": "Sneakers", "fit": "Regular", "color": "White"},
    ]
    score, note, rules = score_body_silhouette_compatibility(items, "athletic_v_taper")
    assert score >= 88.0
    assert "Athletic" in note or "taper" in note


def test_lean_slim_layering_bonus():
    # Lean frame gets a bonus when wearing structured outerwear / jackets
    items = [
        {"category": "T-Shirt", "fit": "Regular", "color": "White"},
        {"category": "Jacket", "fit": "Regular", "color": "Olive Green"},
        {"category": "Chinos", "fit": "Regular", "color": "Khaki"},
    ]
    score, note, rules = score_body_silhouette_compatibility(items, "lean_slim")
    assert score >= 90.0
    assert len(rules) > 0


def test_husky_oval_avoid_skinny():
    # Husky frame with skinny/tight fits should receive a lower silhouette score
    items = [
        {"category": "T-Shirt", "fit": "Skinny", "color": "White"},
        {"category": "Jeans", "fit": "Fitted", "color": "Blue"},
    ]
    score, note, rules = score_body_silhouette_compatibility(items, "husky_oval")
    assert score < 85.0
    assert "adjusting" in note.lower() or "silhouette" in note.lower()
