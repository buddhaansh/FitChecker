"""
tests/test_analytics.py — Tests for wardrobe analytics calculations
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pandas as pd
from datetime import date, timedelta

from src.analytics import (
    wardrobe_utilization,
    cost_per_wear,
    outfit_variety_score,
)


def _wardrobe(rows):
    defaults = {
        "item_id": "", "category": "T-Shirt", "color": "White",
        "times_worn": 0, "last_worn": "", "purchase_price": "",
        "formality": 2,
    }
    records = []
    for i, row in enumerate(rows):
        r = dict(defaults)
        r.update(row)
        if not r["item_id"]:
            r["item_id"] = f"item_{i}"
        records.append(r)
    return pd.DataFrame(records)


def _feedback(rows):
    defaults = {
        "feedback_id": "", "outfit_id": "o1",
        "accepted": False, "worn": False,
        "user_rating": 0, "occasion": "Daily College Wear",
        "timestamp": str(date.today()), "is_sample": False,
    }
    records = []
    for i, row in enumerate(rows):
        r = dict(defaults)
        r.update(row)
        if not r["feedback_id"]:
            r["feedback_id"] = f"fb_{i}"
        records.append(r)
    return pd.DataFrame(records)


# ─────────────────────────────────────────────
# WARDROBE UTILIZATION
# ─────────────────────────────────────────────

def test_utilization_empty_wardrobe():
    result = wardrobe_utilization(pd.DataFrame(), 30)
    assert result["total"]           == 0
    assert result["utilization_pct"] == 0.0


def test_utilization_all_never_worn():
    df = _wardrobe([{"times_worn": 0}, {"times_worn": 0}])
    result = wardrobe_utilization(df, 30)
    assert result["never_worn"]      == 2
    assert result["utilization_pct"] == 0.0


def test_utilization_some_worn_recently():
    today      = date.today().strftime("%Y-%m-%d")
    df = _wardrobe([
        {"times_worn": 3, "last_worn": today},
        {"times_worn": 0, "last_worn": ""},
    ])
    result = wardrobe_utilization(df, 30)
    assert result["worn_count"] == 1
    assert result["total"]      == 2
    assert result["utilization_pct"] == 50.0


def test_utilization_old_wear_not_counted_in_window():
    """Items worn 60 days ago should NOT count in a 30-day window."""
    old_date = (date.today() - timedelta(days=60)).strftime("%Y-%m-%d")
    df = _wardrobe([{"times_worn": 5, "last_worn": old_date}])
    result = wardrobe_utilization(df, 30)
    assert result["worn_count"]      == 0
    assert result["utilization_pct"] == 0.0


def test_utilization_definition_in_result():
    """Result should contain a note about the metric definition."""
    df = _wardrobe([{"times_worn": 1}])
    result = wardrobe_utilization(df, 30)
    assert "note" in result
    assert len(result["note"]) > 0


# ─────────────────────────────────────────────
# COST PER WEAR
# ─────────────────────────────────────────────

def test_cost_per_wear_basic():
    df = _wardrobe([{"purchase_price": "1000", "times_worn": 10}])
    cpw = cost_per_wear(df)
    assert not cpw.empty
    assert float(cpw.iloc[0]["cost_per_wear"]) == pytest.approx(100.0)


def test_cost_per_wear_excludes_zero_times_worn():
    """Items never worn should not have cost-per-wear (division by zero risk)."""
    df = _wardrobe([{"purchase_price": "500", "times_worn": 0}])
    cpw = cost_per_wear(df)
    assert cpw.empty


def test_cost_per_wear_excludes_missing_price():
    df = _wardrobe([{"purchase_price": "", "times_worn": 5}])
    cpw = cost_per_wear(df)
    assert cpw.empty


def test_cost_per_wear_sorted_ascending():
    """Cheapest cost-per-wear should appear first."""
    df = _wardrobe([
        {"item_id": "a", "purchase_price": "100",  "times_worn": 1},   # ₹100/wear
        {"item_id": "b", "purchase_price": "1000", "times_worn": 100}, # ₹10/wear
    ])
    cpw = cost_per_wear(df)
    assert cpw.iloc[0]["item_id"] == "b"   # cheapest first


# ─────────────────────────────────────────────
# OUTFIT VARIETY
# ─────────────────────────────────────────────

def test_variety_empty_feedback():
    result = outfit_variety_score(pd.DataFrame())
    assert result["accepted"]      == 0
    assert result["variety_pct"]   == 0.0


def test_variety_all_unique_outfits():
    df = _feedback([
        {"outfit_id": "o1", "accepted": True},
        {"outfit_id": "o2", "accepted": True},
        {"outfit_id": "o3", "accepted": True},
    ])
    result = outfit_variety_score(df)
    assert result["accepted"]      == 3
    assert result["unique_outfits"] == 3
    assert result["variety_pct"]   == 100.0


def test_variety_repeated_outfit():
    df = _feedback([
        {"outfit_id": "o1", "accepted": True},
        {"outfit_id": "o1", "accepted": True},  # Same outfit twice
    ])
    result = outfit_variety_score(df)
    assert result["accepted"]       == 2
    assert result["unique_outfits"] == 1
    assert result["variety_pct"]    == 50.0
