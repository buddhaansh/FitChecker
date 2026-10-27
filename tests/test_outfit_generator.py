"""
tests/test_outfit_generator.py — Tests for outfit combination engine
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pandas as pd
from src.outfit_generator import generate_outfits, format_outfit_label


def _make_wardrobe(rows):
    """Build a minimal wardrobe DataFrame from a list of dicts."""
    defaults = {
        "item_id": "", "category": "", "subcategory": "", "color": "White",
        "color_hex": "", "secondary_color": "", "pattern": "Plain",
        "formality": 2, "style_tags": "Casual", "season": "All Seasons",
        "weather": "Any", "fit": "Regular", "brand": "", "purchase_price": "",
        "purchase_date": "", "photo_path": "", "times_worn": 0, "last_worn": "",
        "notes": "", "added_date": "", "is_sample": False,
    }
    records = []
    for i, row in enumerate(rows):
        r = dict(defaults)
        r.update(row)
        if not r["item_id"]:
            r["item_id"] = f"test_{i:03d}"
        records.append(r)
    return pd.DataFrame(records)


# ─────────────────────────────────────────────
# BASIC GENERATION
# ─────────────────────────────────────────────

def test_generates_from_minimal_wardrobe():
    """Top + Bottom + Footwear should produce at least one outfit."""
    df = _make_wardrobe([
        {"item_id": "t1", "category": "T-Shirt",  "color": "White"},
        {"item_id": "b1", "category": "Jeans",    "color": "Navy Blue"},
        {"item_id": "f1", "category": "Sneakers", "color": "White"},
    ])
    outfits = generate_outfits(df, occasion="Daily College Wear")
    assert len(outfits) >= 1


def test_uses_only_available_garments():
    """No outfit should reference an item not in the wardrobe."""
    df = _make_wardrobe([
        {"item_id": "t1", "category": "T-Shirt",  "color": "White"},
        {"item_id": "b1", "category": "Jeans",    "color": "Navy Blue"},
        {"item_id": "f1", "category": "Sneakers", "color": "White"},
    ])
    valid_ids = set(df["item_id"].tolist())
    outfits = generate_outfits(df)
    for outfit in outfits:
        for iid in outfit["item_ids"]:
            assert iid in valid_ids, f"Outfit contains unknown item_id: {iid}"


def test_no_duplicate_outfits():
    """Each outfit combination should appear only once."""
    df = _make_wardrobe([
        {"item_id": "t1", "category": "T-Shirt",  "color": "White"},
        {"item_id": "t2", "category": "T-Shirt",  "color": "Black"},
        {"item_id": "b1", "category": "Jeans",    "color": "Navy Blue"},
        {"item_id": "b2", "category": "Jeans",    "color": "Black"},
        {"item_id": "f1", "category": "Sneakers", "color": "White"},
    ])
    outfits = generate_outfits(df, include_accessories=False)
    # Build sorted id-tuples for all outfits
    id_tuples = [tuple(sorted(o["item_ids"])) for o in outfits]
    assert len(id_tuples) == len(set(id_tuples)), "Duplicate outfits found"


def test_empty_wardrobe_returns_empty():
    """Empty wardrobe should return no outfits (not crash)."""
    df = pd.DataFrame()
    outfits = generate_outfits(df)
    assert outfits == []


def test_missing_footwear_returns_empty():
    """Without any footwear, the Top+Bottom+Footwear template cannot be satisfied."""
    df = _make_wardrobe([
        {"item_id": "t1", "category": "T-Shirt", "color": "White"},
        {"item_id": "b1", "category": "Jeans",   "color": "Navy Blue"},
        # No footwear items
    ])
    outfits = generate_outfits(df, include_accessories=False)
    # Dress template also requires footwear, so result should be empty
    assert outfits == []


def test_dress_template_works():
    """Dress + Footwear should be a valid outfit."""
    df = _make_wardrobe([
        {"item_id": "d1", "category": "Dress",   "color": "Red"},
        {"item_id": "f1", "category": "Sandals", "color": "Brown"},
    ])
    outfits = generate_outfits(df, include_accessories=False)
    assert len(outfits) >= 1
    # Should contain the dress
    dress_found = any("d1" in o["item_ids"] for o in outfits)
    assert dress_found


def test_multiple_tops_and_bottoms():
    """3 tops × 2 bottoms × 1 shoe = 6 combinations; we should get at least 5."""
    df = _make_wardrobe([
        {"item_id": "t1", "category": "T-Shirt", "color": "White"},
        {"item_id": "t2", "category": "T-Shirt", "color": "Black"},
        {"item_id": "t3", "category": "Shirt",   "color": "Blue"},
        {"item_id": "b1", "category": "Jeans",   "color": "Navy Blue"},
        {"item_id": "b2", "category": "Chinos",  "color": "Khaki"},
        {"item_id": "f1", "category": "Sneakers","color": "White"},
    ])
    outfits = generate_outfits(df, include_accessories=False)
    assert len(outfits) >= 5


def test_format_outfit_label():
    outfit = {
        "items": [
            {"category": "T-Shirt", "color": "White"},
            {"category": "Jeans",   "color": "Navy Blue"},
        ]
    }
    label = format_outfit_label(outfit)
    assert "T-Shirt" in label
    assert "Jeans"   in label
    assert "+"       in label
