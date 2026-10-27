"""
tests/test_data_manager.py — Tests for the core storage layer
=============================================================
Run with:
  & "C:\\Users\\Dell\\anaconda3\\python.exe" -m pytest tests/ -v
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import tempfile
import shutil

# Note: temp_user_data fixture is centrally configured in conftest.py


def _sample_garment(**overrides):
    base = {
        "category":   "T-Shirt",
        "color":      "White",
        "formality":  2,
        "pattern":    "Plain",
        "season":     "All Seasons",
        "style_tags": "Casual",
    }
    base.update(overrides)
    return base


# ─────────────────────────────────────────────
# ADD / RETRIEVE
# ─────────────────────────────────────────────

def test_add_garment_returns_id():
    from src.data_manager import add_garment
    item_id = add_garment(_sample_garment())
    assert isinstance(item_id, str)
    assert item_id.startswith("item_")


def test_get_garment_after_add():
    from src.data_manager import add_garment, get_garment
    item_id = add_garment(_sample_garment(color="Navy Blue", category="Shirt"))
    result  = get_garment(item_id)
    assert result is not None
    assert result["color"]    == "Navy Blue"
    assert result["category"] == "Shirt"


def test_wardrobe_persists_multiple_items():
    from src.data_manager import add_garment, load_wardrobe
    for color in ["White", "Black", "Grey", "Navy Blue"]:
        add_garment(_sample_garment(color=color))
    df = load_wardrobe()
    assert len(df) == 4


def test_load_wardrobe_empty_returns_dataframe():
    from src.data_manager import load_wardrobe
    df = load_wardrobe()
    assert hasattr(df, "columns")
    assert "item_id" in df.columns


# ─────────────────────────────────────────────
# EDIT
# ─────────────────────────────────────────────

def test_update_garment_changes_field():
    from src.data_manager import add_garment, update_garment, get_garment
    item_id = add_garment(_sample_garment())
    update_garment(item_id, {"formality": 5, "notes": "Updated"})
    result = get_garment(item_id)
    assert int(result["formality"]) == 5
    assert result["notes"] == "Updated"


def test_update_nonexistent_returns_false():
    from src.data_manager import update_garment
    result = update_garment("item_doesnotexist", {"formality": 3})
    assert result is False


# ─────────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────────

def test_delete_garment_removes_item():
    from src.data_manager import add_garment, delete_garment, load_wardrobe
    item_id = add_garment(_sample_garment())
    delete_garment(item_id)
    df = load_wardrobe()
    assert item_id not in df["item_id"].values


def test_delete_nonexistent_returns_false():
    from src.data_manager import delete_garment
    result = delete_garment("item_xyz_fake")
    assert result is False


# ─────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────

def test_add_garment_missing_category_raises():
    from src.data_manager import add_garment
    with pytest.raises(ValueError, match="category"):
        add_garment({"category": "", "color": "White", "formality": 2})


def test_add_garment_missing_color_raises():
    from src.data_manager import add_garment
    with pytest.raises(ValueError, match="color"):
        add_garment({"category": "T-Shirt", "color": "", "formality": 2})


def test_add_garment_invalid_formality_raises():
    from src.data_manager import add_garment
    with pytest.raises(ValueError):
        add_garment({"category": "T-Shirt", "color": "White", "formality": 9})


# ─────────────────────────────────────────────
# PREFERENCES
# ─────────────────────────────────────────────

def test_save_and_load_preferences():
    from src.data_manager import save_preferences, load_preferences
    prefs = {"preferred_colors": ["White", "Navy Blue"], "avoided_colors": ["Red"]}
    save_preferences(prefs)
    loaded = load_preferences()
    assert "White" in loaded["preferred_colors"]
    assert "Red"   in loaded["avoided_colors"]


def test_load_preferences_returns_defaults_when_missing():
    from src.data_manager import load_preferences
    prefs = load_preferences()
    assert isinstance(prefs, dict)
    assert "preferred_colors" in prefs


# ─────────────────────────────────────────────
# WEAR COUNT
# ─────────────────────────────────────────────

def test_increment_wear_count():
    from src.data_manager import add_garment, increment_wear_count, get_garment
    item_id = add_garment(_sample_garment())
    increment_wear_count(item_id)
    increment_wear_count(item_id)
    result = get_garment(item_id)
    assert int(result["times_worn"]) == 2


# ─────────────────────────────────────────────
# SAMPLE DATA IMPORT
# ─────────────────────────────────────────────

def test_load_sample_wardrobe():
    from src.data_manager import load_sample_wardrobe
    sample_df = load_sample_wardrobe()
    assert not sample_df.empty
    assert len(sample_df) == 25
    assert "category" in sample_df.columns
    assert "formality" in sample_df.columns
    assert all(sample_df["is_sample"] == True)


def test_import_sample_data():
    from src.data_manager import import_sample_data, load_wardrobe
    # Initially empty in tmp_path
    assert load_wardrobe().empty

    imported = import_sample_data()
    assert imported == 25
    assert len(load_wardrobe()) == 25

    # Second call should not re-import if wardrobe is not empty
    imported_again = import_sample_data()
    assert imported_again == 0

