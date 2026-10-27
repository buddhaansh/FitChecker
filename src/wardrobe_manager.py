"""
wardrobe_manager.py — FitChecker Wardrobe Business Logic
=========================================================
PURPOSE:
  Sits on top of data_manager.py and provides higher-level wardrobe
  operations: validation helpers, category filtering, and convenience
  functions used by both the Streamlit UI and the outfit engine.

BEGINNER NOTE:
  Think of data_manager as the "filing cabinet" and wardrobe_manager
  as the "librarian" who knows how to use it intelligently.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from config.settings import CATEGORY_GROUP, CATEGORIES, PATTERNS, SEASONS
from src.data_manager import (
    load_wardrobe, save_wardrobe, add_garment,
    get_garment, update_garment, delete_garment,
)


# ─────────────────────────────────────────────
# CATEGORY HELPERS
# ─────────────────────────────────────────────

def get_group(category: str) -> str:
    """Return the high-level group ('tops', 'bottoms', etc.) for a category."""
    for group, cats in CATEGORY_GROUP.items():
        if category in cats:
            return group
    return "other"


def filter_by_group(df: pd.DataFrame, group: str) -> pd.DataFrame:
    """Return only rows whose category belongs to the specified group."""
    cats = CATEGORY_GROUP.get(group, [])
    return df[df["category"].isin(cats)]


def get_available_groups(df: pd.DataFrame) -> list:
    """Return which category groups have at least one item in the wardrobe."""
    available = []
    for group in CATEGORY_GROUP:
        if not filter_by_group(df, group).empty:
            available.append(group)
    return available


# ─────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────

def validate_garment_dict(data: dict) -> list:
    """
    Check a garment dict for errors.
    Returns a list of error strings (empty list = valid).
    """
    errors = []
    if not data.get("category", "").strip():
        errors.append("Category is required.")
    if data.get("category") and data["category"] not in CATEGORIES:
        pass   # Custom categories are allowed; no error needed
    if not data.get("color", "").strip():
        errors.append("Color is required.")
    formality = data.get("formality", 3)
    try:
        f = int(formality)
        if not (1 <= f <= 5):
            errors.append("Formality must be between 1 and 5.")
    except (ValueError, TypeError):
        errors.append("Formality must be a whole number between 1 and 5.")
    return errors


# ─────────────────────────────────────────────
# CONVENIENCE QUERIES
# ─────────────────────────────────────────────

def get_wardrobe_summary(df: pd.DataFrame | None = None) -> dict:
    """
    Return simple statistics about the wardrobe.
    Useful for the dashboard widget.
    """
    if df is None:
        df = load_wardrobe()
    if df.empty:
        return {
            "total": 0, "categories": {}, "never_worn": 0,
            "rarely_worn": 0, "utilization_pct": 0.0,
        }

    times_worn = pd.to_numeric(df["times_worn"], errors="coerce").fillna(0)
    total = len(df)
    never_worn  = int((times_worn == 0).sum())
    rarely_worn = int((times_worn == 1).sum())

    # Utilization: fraction worn at least once
    utilization = round((total - never_worn) / total * 100, 1) if total > 0 else 0.0

    categories = df["category"].value_counts().to_dict()

    return {
        "total":           total,
        "categories":      categories,
        "never_worn":      never_worn,
        "rarely_worn":     rarely_worn,
        "utilization_pct": utilization,
    }


def get_items_by_ids(item_ids: list, df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Return wardrobe rows matching the given list of item_ids."""
    if df is None:
        df = load_wardrobe()
    return df[df["item_id"].isin(item_ids)]


def get_rarely_worn(df: pd.DataFrame | None = None, threshold: int = 2) -> pd.DataFrame:
    """Return items worn fewer than `threshold` times."""
    if df is None:
        df = load_wardrobe()
    times_worn = pd.to_numeric(df["times_worn"], errors="coerce").fillna(0)
    return df[times_worn < threshold]


def get_most_worn(df: pd.DataFrame | None = None, top_n: int = 5) -> pd.DataFrame:
    """Return the top-N most-worn items."""
    if df is None:
        df = load_wardrobe()
    df = df.copy()
    df["times_worn"] = pd.to_numeric(df["times_worn"], errors="coerce").fillna(0)
    return df.nlargest(top_n, "times_worn")
