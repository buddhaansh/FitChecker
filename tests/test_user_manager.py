"""
tests/test_user_manager.py — Unit Tests for Multi-User Wardrobe Isolation & Admin Hub
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pandas as pd
from src.user_manager import (
    DEFAULT_ADMIN_USER, sanitize_username, get_active_user, set_active_user,
    get_user_data_dir, get_user_wardrobe_file, get_user_profile_file,
    list_users, create_user, delete_user
)
from src.data_manager import load_wardrobe, save_wardrobe, add_garment, import_sample_data
from src.skin_tone_analyzer import load_profile, save_profile


def test_sanitize_username():
    assert sanitize_username("  Alex 123  ") == "Alex123"
    assert sanitize_username("Rohan_Kapoor-99") == "Rohan_Kapoor-99"
    assert sanitize_username("!@#$%^&*") == DEFAULT_ADMIN_USER
    assert sanitize_username("") == DEFAULT_ADMIN_USER


def test_create_and_isolate_user():
    user = create_user("Sneha", display_name="Sneha Sharma", gender="Girl")
    assert user["user_id"] == "Sneha"
    assert os.path.exists(user["user_dir"])

    # Verify isolated profile
    profile = load_profile(user_id="Sneha")
    assert profile["name"] == "Sneha Sharma"
    assert profile["gender"] == "Girl"

    # Verify isolated wardrobe
    wdf = load_wardrobe(user_id="Sneha")
    assert wdf.empty

    # Add garment to Sneha's wardrobe
    item = {
        "category": "Dresses",
        "color": "Emerald Green",
        "color_hex": "#097969",
        "pattern": "Solid",
        "formality": 4,
        "style_tags": "Party / Night Out",
        "season": "Summer",
        "weather": "Warm",
        "fit": "Fitted",
        "brand": "Zara",
        "notes": "Evening gown",
        "times_worn": 0,
        "is_sample": False,
    }
    item_id = add_garment(item, user_id="Sneha")
    assert item_id.startswith("item_")

    sneha_df = load_wardrobe(user_id="Sneha")
    assert len(sneha_df) == 1
    assert sneha_df.iloc[0]["category"] == "Dresses"

    # Verify BUDZ wardrobe was NOT touched
    budz_df = load_wardrobe(user_id=DEFAULT_ADMIN_USER)
    assert sneha_df.iloc[0]["item_id"] not in budz_df["item_id"].values


def test_list_users():
    create_user("Arjun", display_name="Arjun Roy", gender="Boy")
    users = list_users()
    user_ids = [u["user_id"] for u in users]
    assert DEFAULT_ADMIN_USER in user_ids
    assert "Arjun" in user_ids


def test_delete_user_protection():
    # Admin BUDZ cannot be deleted
    assert delete_user(DEFAULT_ADMIN_USER) is False

    # Guest user can be deleted
    create_user("TempGuest", display_name="Temp Guest")
    assert delete_user("TempGuest") is True
    user_ids = [u["user_id"] for u in list_users()]
    assert "TempGuest" not in user_ids


def test_seed_capsule_for_user():
    create_user("Priya", display_name="Priya Patel")
    assert len(load_wardrobe(user_id="Priya")) == 0
    count = import_sample_data(user_id="Priya")
    assert count == 25
    assert len(load_wardrobe(user_id="Priya")) == 25
