"""
tests/test_wardrobe_manager.py — Tests for wardrobe business logic
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pandas as pd

from src.wardrobe_manager import (
    get_group,
    filter_by_group,
    get_available_groups,
    validate_garment_dict,
    get_wardrobe_summary,
    get_items_by_ids,
    get_rarely_worn,
    get_most_worn,
)


def _make_sample_df():
    data = [
        {"item_id": "item1", "category": "T-Shirt", "times_worn": 0, "color": "Blue", "formality": 2},
        {"item_id": "item2", "category": "Jeans", "times_worn": 1, "color": "Navy Blue", "formality": 2},
        {"item_id": "item3", "category": "Sneakers", "times_worn": 5, "color": "White", "formality": 2},
        {"item_id": "item4", "category": "Jacket", "times_worn": 10, "color": "Black", "formality": 1},
    ]
    return pd.DataFrame(data)


# ─────────────────────────────────────────────
# CATEGORY / GROUP HELPERS
# ─────────────────────────────────────────────

def test_get_group_known_categories():
    assert get_group("T-Shirt") == "tops"
    assert get_group("Jeans") == "bottoms"
    assert get_group("Sneakers") == "footwear"
    assert get_group("Jacket") == "outer"
    assert get_group("Dress") in ["one_piece", "dresses"]
    assert get_group("Accessories") == "accessories"


def test_get_group_unknown_category():
    assert get_group("UnknownItem123") == "other"


def test_filter_by_group():
    df = _make_sample_df()
    tops = filter_by_group(df, "tops")
    assert len(tops) == 1
    assert tops.iloc[0]["item_id"] == "item1"

    bottoms = filter_by_group(df, "bottoms")
    assert len(bottoms) == 1
    assert bottoms.iloc[0]["item_id"] == "item2"


def test_get_available_groups():
    df = _make_sample_df()
    groups = get_available_groups(df)
    assert "tops" in groups
    assert "bottoms" in groups
    assert "footwear" in groups
    assert "outer" in groups  # Hoodie is in outer
    assert "dresses" not in groups


# ─────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────

def test_validate_garment_dict_valid():
    valid_data = {
        "category": "T-Shirt",
        "color": "White",
        "formality": 2,
    }
    errors = validate_garment_dict(valid_data)
    assert errors == []


def test_validate_garment_dict_missing_fields():
    errors = validate_garment_dict({"category": "", "color": ""})
    assert any("Category is required" in e for e in errors)
    assert any("Color is required" in e for e in errors)


def test_validate_garment_dict_invalid_formality():
    errors = validate_garment_dict({"category": "T-Shirt", "color": "White", "formality": 6})
    assert any("between 1 and 5" in e for e in errors)

    errors_str = validate_garment_dict({"category": "T-Shirt", "color": "White", "formality": "abc"})
    assert any("whole number" in e for e in errors_str)


# ─────────────────────────────────────────────
# SUMMARY & QUERIES
# ─────────────────────────────────────────────

def test_get_wardrobe_summary_empty():
    empty_df = pd.DataFrame()
    summary = get_wardrobe_summary(empty_df)
    assert summary["total"] == 0
    assert summary["never_worn"] == 0
    assert summary["rarely_worn"] == 0
    assert summary["utilization_pct"] == 0.0


def test_get_wardrobe_summary_populated():
    df = _make_sample_df()
    summary = get_wardrobe_summary(df)
    assert summary["total"] == 4
    assert summary["never_worn"] == 1  # item1 has times_worn=0
    assert summary["rarely_worn"] == 1  # item2 has times_worn=1
    # 3 out of 4 worn at least once = 75.0%
    assert summary["utilization_pct"] == 75.0


def test_get_items_by_ids():
    df = _make_sample_df()
    found = get_items_by_ids(["item1", "item3"], df)
    assert len(found) == 2
    assert set(found["item_id"]) == {"item1", "item3"}


def test_get_rarely_worn():
    df = _make_sample_df()
    rare = get_rarely_worn(df, threshold=2)
    # item1 (0) and item2 (1) are < 2
    assert len(rare) == 2
    assert set(rare["item_id"]) == {"item1", "item2"}


def test_get_most_worn():
    df = _make_sample_df()
    top = get_most_worn(df, top_n=2)
    assert len(top) == 2
    # item4 (10) and item3 (5)
    assert list(top["item_id"]) == ["item4", "item3"]
