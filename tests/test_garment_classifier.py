"""
tests/test_garment_classifier.py — Tests for garment category suggestion heuristic
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src.garment_classifier import suggest_category_from_colors, get_category_confidence_display


def test_suggest_category_empty_colors():
    cat, conf, reason = suggest_category_from_colors([])
    assert cat == "T-Shirt"
    assert conf == 0.3
    assert "defaulting to T-Shirt" in reason


def test_suggest_category_blue_tall():
    colors = [{"name": "blue", "hex": "#0000ff"}]
    # Tall image: height 300, width 150 -> h/w = 2.0 > 1.4 -> Shirt
    image_info = {"width": 150, "height": 300}
    cat, conf, reason = suggest_category_from_colors(colors, image_info)
    assert cat == "Shirt"
    assert conf == 0.40


def test_suggest_category_blue_wide():
    colors = [{"name": "navy blue", "hex": "#000080"}]
    # Wide/square image: height 200, width 200 -> not tall -> Jeans
    image_info = {"width": 200, "height": 200}
    cat, conf, reason = suggest_category_from_colors(colors, image_info)
    assert cat == "Jeans"
    assert conf == 0.40


def test_suggest_category_neutral():
    colors = [{"name": "white", "hex": "#ffffff"}]
    cat, conf, reason = suggest_category_from_colors(colors)
    assert cat == "T-Shirt"
    assert conf == 0.35


def test_confidence_display():
    assert get_category_confidence_display(0.8) == "High"
    assert get_category_confidence_display(0.5) == "Medium"
    assert "Low" in get_category_confidence_display(0.3)


def test_suggest_garment_attributes_trousers():
    from src.garment_classifier import suggest_garment_attributes
    colors = [{"name": "black", "hex": "#1A1A1A"}]
    image_info = {"width": 150, "height": 300, "has_legs": True}
    res = suggest_garment_attributes(colors, image_info=image_info)
    assert res["category"] == "Trousers"
    assert res["confidence"] >= 0.85
    assert res["formality"] == 4
    assert "styling_guidance" in res
    assert len(res["styling_guidance"]["color_chips"]) >= 3


def test_suggest_garment_attributes_sneakers():
    from src.garment_classifier import suggest_garment_attributes
    colors = [{"name": "white", "hex": "#FFFFFF"}]
    image_info = {"width": 300, "height": 150} # Wide
    res = suggest_garment_attributes(colors, image_info=image_info)
    assert res["category"] == "Sneakers"
    assert res["confidence"] >= 0.75
    assert "styling_guidance" in res
