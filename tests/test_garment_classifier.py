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
