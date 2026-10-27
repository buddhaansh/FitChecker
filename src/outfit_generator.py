"""
outfit_generator.py — FitChecker Combination Engine
====================================================
PURPOSE:
  Given a wardrobe DataFrame, produce a list of valid outfit combinations
  for a specified occasion and optional weather condition.

ALGORITHM:
  1. Separate wardrobe items into category groups (tops, bottoms, etc.).
  2. Apply outfit templates (see OUTFIT_TEMPLATES below).
  3. For each template, enumerate valid combinations from available items.
  4. Reject combinations that violate hard constraints.
  5. Deduplicate by sorted item_id tuple.
  6. Shuffle and cap at MAX_OUTFITS_TO_SCORE to limit search time.

OUTFIT TEMPLATES:
  Each template is a list of required category groups.
  Optional groups are indicated separately and added when items exist.

BEGINNER NOTE:
  itertools.product computes the Cartesian product of multiple lists.
  For example, product([A, B], [X, Y]) = [(A,X), (A,Y), (B,X), (B,Y)].
  We use this to enumerate all possible garment combinations.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import itertools
import random
from typing import Optional

import pandas as pd

from config.settings import (
    CATEGORY_GROUP, MAX_OUTFITS_TO_SCORE, OCCASION_PROFILES
)
from src.wardrobe_manager import filter_by_group


# ─────────────────────────────────────────────
# OUTFIT TEMPLATES
# Each template specifies required groups and optional groups.
# ─────────────────────────────────────────────
OUTFIT_TEMPLATES = [
    {
        "name":     "Top + Bottom + Footwear",
        "required": ["tops", "bottoms", "footwear"],
        "optional": ["outer", "accessories"],
    },
    {
        "name":     "One-Piece + Footwear",
        "required": ["one_piece", "footwear"],
        "optional": ["outer", "accessories"],
    },
]


# ─────────────────────────────────────────────
# SEASON / WEATHER COMPATIBILITY
# ─────────────────────────────────────────────
def _weather_ok(item_weather: str, current_weather: str) -> bool:
    """Return True if an item's weather tag is compatible with current weather."""
    if not current_weather or current_weather == "Any":
        return True
    if not item_weather or item_weather == "Any":
        return True
    # "All Seasons" items work in all conditions
    if item_weather.lower() in ("any", "all seasons"):
        return True
    # Direct match or inclusive grouping
    return item_weather.lower() == current_weather.lower()


def _season_ok(item_season: str, current_season: str) -> bool:
    """Return True if an item's season tag matches the current season."""
    if not current_season or current_season == "All Seasons":
        return True
    if not item_season or item_season in ("All Seasons",):
        return True
    return item_season.lower() == current_season.lower()


# ─────────────────────────────────────────────
# OCCASION-BASED HARD CONSTRAINTS
# ─────────────────────────────────────────────
def _formality_ok(item_formality: int, occasion: str) -> bool:
    """
    Check if an item's formality is broadly compatible with the occasion.
    We allow a ±2 window around the occasion target.
    This is a soft guide, not a strict ban.
    """
    profile = OCCASION_PROFILES.get(occasion, {})
    target  = profile.get("formality", 3)
    # For formal occasions (target >= 4), reject items < target-1
    if target >= 4 and item_formality < target - 1:
        return False
    # For casual occasions (target <= 2), reject very formal items
    if target <= 2 and item_formality >= 5:
        return False
    return True


# ─────────────────────────────────────────────
# CORE GENERATOR
# ─────────────────────────────────────────────
def generate_outfits(
    wardrobe_df: pd.DataFrame,
    occasion: str = "Daily College Wear",
    current_weather: str = "Any",
    current_season: str = "All Seasons",
    include_accessories: bool = True,
) -> list[dict]:
    """
    Generate a list of valid outfit dicts from the given wardrobe.

    Each outfit dict contains:
      {
        "template":   str,            # Template name
        "item_ids":   list[str],      # IDs of garments in the outfit
        "items":      list[dict],     # Full garment dicts (for scoring/display)
        "groups":     list[str],      # Which groups are represented
      }

    Returns [] if no valid outfit can be assembled.
    """
    if wardrobe_df is None or wardrobe_df.empty:
        return []

    # Pre-filter: remove weather/season-incompatible items
    def item_fits_conditions(row):
        return (
            _weather_ok(str(row.get("weather", "Any")), current_weather) and
            _season_ok(str(row.get("season", "All Seasons")), current_season) and
            _formality_ok(int(row.get("formality", 3)), occasion)
        )

    eligible = wardrobe_df[wardrobe_df.apply(item_fits_conditions, axis=1)].copy()

    if eligible.empty:
        # Relax season/weather constraint and try again with only formality
        eligible = wardrobe_df[
            wardrobe_df.apply(lambda r: _formality_ok(int(r.get("formality", 3)), occasion), axis=1)
        ].copy()

    outfits = []
    seen    = set()   # For deduplication

    for template in OUTFIT_TEMPLATES:
        # Check if all required groups have at least one eligible item
        group_items = {}
        missing_required = False
        for group in template["required"]:
            items = filter_by_group(eligible, group)
            if items.empty:
                missing_required = True
                break
            group_items[group] = items.to_dict("records")

        if missing_required:
            continue  # Try next template

        # Gather optional group items
        for group in template["optional"]:
            if group == "accessories" and not include_accessories:
                continue
            items = filter_by_group(eligible, group)
            if not items.empty:
                group_items[group] = items.to_dict("records")

        # Build Cartesian product of required groups
        required_lists = [group_items[g] for g in template["required"]]
        combos = list(itertools.product(*required_lists))

        # Shuffle to get variety; cap to avoid huge search space
        random.shuffle(combos)
        combos = combos[:MAX_OUTFITS_TO_SCORE]

        for combo in combos:
            items = list(combo)
            item_ids = tuple(sorted(i["item_id"] for i in items))

            # Skip duplicates
            if item_ids in seen:
                continue
            seen.add(item_ids)

            groups = list(template["required"])

            # Add one optional item from each optional group (first available)
            for group in template["optional"]:
                if group not in group_items:
                    continue
                if group == "accessories" and not include_accessories:
                    continue
                # Pick the optional item not already in the outfit
                for opt_item in group_items[group]:
                    if opt_item["item_id"] not in [i["item_id"] for i in items]:
                        items.append(opt_item)
                        groups.append(group)
                        break   # One optional per group

            outfit = {
                "template": template["name"],
                "item_ids": [i["item_id"] for i in items],
                "items":    items,
                "groups":   groups,
            }
            outfits.append(outfit)

    return outfits


def format_outfit_label(outfit: dict) -> str:
    """Create a human-readable label for an outfit (for display/logging)."""
    parts = []
    for item in outfit.get("items", []):
        cat   = item.get("category", "?")
        color = item.get("color", "")
        parts.append(f"{color} {cat}".strip())
    return " + ".join(parts) if parts else "Unknown outfit"
