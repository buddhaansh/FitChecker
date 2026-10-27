"""
tests/test_color_compatibility.py — Tests for color scoring logic
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src.color_compatibility import (
    _get_rgb_for_name,
    _hex_to_rgb,
    pair_score,
    outfit_color_score,
)


def test_hex_to_rgb_valid():
    assert _hex_to_rgb("#ffffff") == (255, 255, 255)
    assert _hex_to_rgb("000000") == (0, 0, 0)
    assert _hex_to_rgb("#fff") == (255, 255, 255)


def test_hex_to_rgb_invalid():
    assert _hex_to_rgb("invalid_hex") is None
    assert _hex_to_rgb("") is None


def test_get_rgb_for_name():
    assert _get_rgb_for_name("white") == (255, 255, 255)
    assert _get_rgb_for_name("black") == (0, 0, 0)
    assert _get_rgb_for_name("navy blue") == (31, 43, 122)
    assert _get_rgb_for_name("nonexistent_color_name") is None


def test_pair_score_identical_colors():
    # Neutrals get 85, vivid colors get 65 (monochromatic risk)
    white_score = pair_score("White", "White")
    assert white_score == 85.0

    red_score = pair_score("Red", "Red")
    assert red_score == 65.0


def test_pair_score_known_lookup():
    # White + Navy Blue should be a top pair
    score = pair_score("White", "Navy Blue")
    assert score >= 90.0

    # Symmetry: Navy Blue + White should equal White + Navy Blue
    rev_score = pair_score("Navy Blue", "White")
    assert score == rev_score


def test_pair_score_case_insensitivity():
    s1 = pair_score("black", "white")
    s2 = pair_score("Black", "WHITE")
    assert s1 == s2


def test_outfit_color_score_single_or_empty():
    assert outfit_color_score([]) == 100.0
    assert outfit_color_score([{"color": "White"}]) == 100.0


def test_outfit_color_score_multiple_items():
    garments = [
        {"color": "White"},
        {"color": "Navy Blue"},
        {"color": "Black"},
    ]
    score = outfit_color_score(garments)
    assert 0.0 <= score <= 100.0
    # All are classic neutrals/staples, so score should be high
    assert score >= 80.0
