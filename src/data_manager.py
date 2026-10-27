"""
data_manager.py — FitChecker Core Storage Layer
================================================
PURPOSE:
  Handles all reading and writing to CSV files.
  Every other module calls functions here instead of touching files directly.
  This keeps storage separate from business logic.

INPUTS / OUTPUTS:
  Input  : Python dicts or DataFrames describing garments, outfits, feedback.
  Output : DataFrames for reading; None or bool for write operations.

BEGINNER NOTE:
  A CSV (Comma-Separated Values) file is like a simple spreadsheet saved
  as plain text.  Pandas reads and writes them easily.
"""

import os
import uuid
import json
import shutil
from datetime import datetime

import pandas as pd
import numpy as np

# Add project root to path so imports work regardless of how the app is launched
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import (
    WARDROBE_FILE, FEEDBACK_FILE, PREFERENCES_FILE,
    WEAR_HISTORY_FILE, OUTFITS_FILE, USER_DATA_DIR,
    SAMPLE_WARDROBE_FILE, SAMPLE_FEEDBACK_FILE,
)

# ─────────────────────────────────────────────
# SCHEMA DEFINITIONS
# Each key is a column name; value is the default when a field is missing.
# ─────────────────────────────────────────────

WARDROBE_SCHEMA = {
    "item_id":        "",          # UUID string
    "category":       "",
    "subcategory":    "",
    "color":          "",
    "color_hex":      "",          # Hex code e.g. #3A86FF
    "secondary_color":"",
    "pattern":        "Plain",
    "formality":      3,           # 1 (very casual) – 5 (very formal)
    "style_tags":     "",          # Comma-separated
    "season":         "All Seasons",
    "weather":        "Any",
    "fit":            "Regular",
    "brand":          "",
    "purchase_price": "",
    "purchase_date":  "",
    "photo_path":     "",
    "times_worn":     0,
    "last_worn":      "",
    "notes":          "",
    "added_date":     "",
    "is_sample":      False,       # True for pre-loaded sample data
}

OUTFIT_SCHEMA = {
    "outfit_id":        "",
    "item_ids":         "",        # Semicolon-separated list of item_ids
    "occasion":         "",
    "generated_score":  0.0,
    "score_components": "",        # JSON string
    "created_at":       "",
    "is_sample":        False,
}

FEEDBACK_SCHEMA = {
    "feedback_id":  "",
    "outfit_id":    "",
    "user_rating":  0,             # 1–5 stars; 0 = not rated
    "accepted":     False,         # Did user click "Select this outfit"?
    "worn":         False,         # Did user confirm they wore it?
    "occasion":     "",
    "weather":      "",
    "notes":        "",
    "timestamp":    "",
    "is_sample":    False,
}

WEAR_HISTORY_SCHEMA = {
    "history_id":  "",
    "item_id":     "",
    "outfit_id":   "",
    "worn_date":   "",
    "occasion":    "",
}

DEFAULT_PREFERENCES = {
    "preferred_colors":   [],
    "avoided_colors":     [],
    "preferred_styles":   [],
    "preferred_fit":      "Regular",
    "desired_formality":  3,
    "budget_limit":       None,
    "preferred_variety":  True,    # Try to avoid repeat outfits
}


# ─────────────────────────────────────────────
# UTILITY HELPERS
# ─────────────────────────────────────────────

def generate_id(prefix: str = "") -> str:
    """Generate a short unique ID.  e.g.  'item_3f7a2c'"""
    return f"{prefix}{uuid.uuid4().hex[:8]}"


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_user_data_dirs():
    """Create user_data/ and user_data/images/ if they don't exist yet."""
    from config.settings import IMAGES_DIR
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)


def _enforce_schema(df: pd.DataFrame, schema: dict) -> pd.DataFrame:
    """
    Add any missing columns with their default values.
    This prevents KeyError crashes when schema evolves over time.
    """
    for col, default in schema.items():
        if col not in df.columns:
            df[col] = default
    return df[list(schema.keys())]


# ─────────────────────────────────────────────
# WARDROBE CSV OPERATIONS
# ─────────────────────────────────────────────

def load_wardrobe() -> pd.DataFrame:
    """
    Load the user's wardrobe from CSV.
    Returns an empty DataFrame (with correct columns) if no file exists yet.
    """
    ensure_user_data_dirs()
    if os.path.exists(WARDROBE_FILE):
        try:
            df = pd.read_csv(WARDROBE_FILE, dtype=str)
            df = _enforce_schema(df, WARDROBE_SCHEMA)
            # Ensure string columns never contain NaN floats
            for col in WARDROBE_SCHEMA.keys():
                if col not in ["formality", "times_worn", "is_sample"] and col in df.columns:
                    df[col] = df[col].fillna("").astype(str)
            # Convert numeric columns back from string
            df["formality"]   = pd.to_numeric(df["formality"],   errors="coerce").fillna(3).astype(int)
            df["times_worn"]  = pd.to_numeric(df["times_worn"],  errors="coerce").fillna(0).astype(int)
            df["is_sample"]   = df["is_sample"].map({"True": True, "False": False, True: True, False: False}).fillna(False)

            # Resilient path resolution across operating systems (Windows <-> Linux/Cloud)
            if "photo_path" in df.columns:
                def _normalize_photo(p):
                    if not p:
                        return ""
                    if not os.path.exists(str(p)):
                        fname = os.path.basename(str(p))
                        cand = os.path.join(IMAGES_DIR, fname)
                        if os.path.exists(cand):
                            return cand
                    return str(p)
                df["photo_path"] = df["photo_path"].apply(_normalize_photo)

            return df
        except Exception as e:
            print(f"[data_manager] Warning: could not load wardrobe — {e}")
            return _empty_wardrobe()
    return _empty_wardrobe()


def _empty_wardrobe() -> pd.DataFrame:
    return pd.DataFrame(columns=list(WARDROBE_SCHEMA.keys()))


def save_wardrobe(df: pd.DataFrame) -> bool:
    """Write the wardrobe DataFrame to CSV.  Returns True on success."""
    ensure_user_data_dirs()
    try:
        df = _enforce_schema(df, WARDROBE_SCHEMA)
        df.to_csv(WARDROBE_FILE, index=False)
        return True
    except Exception as e:
        print(f"[data_manager] Error saving wardrobe — {e}")
        return False


def add_garment(garment_dict: dict) -> str:
    """
    Validate and append a single garment to the wardrobe CSV.
    Returns the new item_id on success, or raises ValueError on bad input.

    ALGORITHM:
      1. Validate required fields.
      2. Fill defaults for optional fields.
      3. Assign a unique item_id.
      4. Append to the existing CSV.
    """
    # ── Validation ──
    required = ["category", "color"]
    for field in required:
        if not garment_dict.get(field, "").strip():
            raise ValueError(f"Field '{field}' is required and cannot be empty.")

    if not (1 <= int(garment_dict.get("formality", 3)) <= 5):
        raise ValueError("Formality must be between 1 and 5.")

    # ── Defaults ──
    item_id = generate_id("item_")
    row = dict(WARDROBE_SCHEMA)   # Start with all defaults
    row.update(garment_dict)      # Overlay provided values
    row["item_id"]    = item_id
    row["added_date"] = today_str()
    if not row.get("times_worn"):
        row["times_worn"] = 0

    # ── Append ──
    df = load_wardrobe()
    new_row = pd.DataFrame([row])
    df = pd.concat([df, new_row], ignore_index=True)
    save_wardrobe(df)
    return item_id


def get_garment(item_id: str) -> dict | None:
    """Return a single garment as a dict, or None if not found."""
    df = load_wardrobe()
    row = df[df["item_id"] == item_id]
    if row.empty:
        return None
    return row.iloc[0].to_dict()


def update_garment(item_id: str, updates: dict) -> bool:
    """
    Update specific fields of a garment identified by item_id.
    Returns True on success, False if item not found.
    """
    df = load_wardrobe()
    mask = df["item_id"] == item_id
    if not mask.any():
        return False
    for col, val in updates.items():
        if col in df.columns:
            df.loc[mask, col] = val
    return save_wardrobe(df)


def delete_garment(item_id: str) -> bool:
    """
    Remove a garment from the wardrobe.
    Also deletes its photo if one is stored locally.
    Returns True on success.
    """
    df = load_wardrobe()
    row = df[df["item_id"] == item_id]
    if row.empty:
        return False

    # Delete associated photo if it exists
    photo_path = row.iloc[0].get("photo_path", "")
    if photo_path and os.path.exists(str(photo_path)):
        try:
            os.remove(photo_path)
        except Exception:
            pass  # File deletion is best-effort

    df = df[df["item_id"] != item_id]
    return save_wardrobe(df)


def increment_wear_count(item_id: str, worn_date: str | None = None) -> bool:
    """Increase times_worn by 1 and update last_worn date."""
    date = worn_date or today_str()
    df = load_wardrobe()
    mask = df["item_id"] == item_id
    if not mask.any():
        return False
    df.loc[mask, "times_worn"] = df.loc[mask, "times_worn"].astype(int) + 1
    df.loc[mask, "last_worn"]  = date
    return save_wardrobe(df)


# ─────────────────────────────────────────────
# OUTFIT CSV OPERATIONS
# ─────────────────────────────────────────────

def load_outfits() -> pd.DataFrame:
    ensure_user_data_dirs()
    if os.path.exists(OUTFITS_FILE):
        try:
            df = pd.read_csv(OUTFITS_FILE, dtype=str)
            return _enforce_schema(df, OUTFIT_SCHEMA)
        except Exception:
            return pd.DataFrame(columns=list(OUTFIT_SCHEMA.keys()))
    return pd.DataFrame(columns=list(OUTFIT_SCHEMA.keys()))


def save_outfit(outfit_dict: dict) -> str:
    """Persist a generated outfit and return its outfit_id."""
    outfit_id = generate_id("outfit_")
    outfit_dict["outfit_id"]   = outfit_id
    outfit_dict["created_at"]  = now_str()
    df = load_outfits()
    new_row = pd.DataFrame([outfit_dict])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(OUTFITS_FILE, index=False)
    return outfit_id


# ─────────────────────────────────────────────
# FEEDBACK CSV OPERATIONS
# ─────────────────────────────────────────────

def load_feedback() -> pd.DataFrame:
    ensure_user_data_dirs()
    if os.path.exists(FEEDBACK_FILE):
        try:
            df = pd.read_csv(FEEDBACK_FILE, dtype=str)
            df = _enforce_schema(df, FEEDBACK_SCHEMA)
            df["user_rating"] = pd.to_numeric(df["user_rating"], errors="coerce").fillna(0).astype(int)
            df["accepted"] = df["accepted"].map({"True": True, "False": False, True: True, False: False}).fillna(False)
            df["worn"]     = df["worn"].map({"True": True, "False": False, True: True, False: False}).fillna(False)
            return df
        except Exception:
            return pd.DataFrame(columns=list(FEEDBACK_SCHEMA.keys()))
    return pd.DataFrame(columns=list(FEEDBACK_SCHEMA.keys()))


def save_feedback_record(feedback_dict: dict) -> str:
    """Append a feedback record and return feedback_id."""
    feedback_id = generate_id("fb_")
    feedback_dict["feedback_id"] = feedback_id
    feedback_dict["timestamp"]   = now_str()
    df = load_feedback()
    new_row = pd.DataFrame([feedback_dict])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(FEEDBACK_FILE, index=False)
    return feedback_id


# ─────────────────────────────────────────────
# WEAR HISTORY OPERATIONS
# ─────────────────────────────────────────────

def load_wear_history() -> pd.DataFrame:
    ensure_user_data_dirs()
    if os.path.exists(WEAR_HISTORY_FILE):
        try:
            return pd.read_csv(WEAR_HISTORY_FILE, dtype=str)
        except Exception:
            return pd.DataFrame(columns=list(WEAR_HISTORY_SCHEMA.keys()))
    return pd.DataFrame(columns=list(WEAR_HISTORY_SCHEMA.keys()))


def record_wear_event(item_ids: list, outfit_id: str, occasion: str, worn_date: str | None = None) -> None:
    """Save a wear event for each item in the outfit."""
    date = worn_date or today_str()
    df = load_wear_history()
    rows = []
    for iid in item_ids:
        rows.append({
            "history_id": generate_id("wh_"),
            "item_id":    iid,
            "outfit_id":  outfit_id,
            "worn_date":  date,
            "occasion":   occasion,
        })
        increment_wear_count(iid, date)
    df = pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
    df.to_csv(WEAR_HISTORY_FILE, index=False)


# ─────────────────────────────────────────────
# USER PREFERENCES
# ─────────────────────────────────────────────

def load_preferences() -> dict:
    """Load user preferences JSON, returning defaults if file missing."""
    ensure_user_data_dirs()
    if os.path.exists(PREFERENCES_FILE):
        try:
            with open(PREFERENCES_FILE, "r", encoding="utf-8") as f:
                prefs = json.load(f)
            # Merge with defaults so new fields are always present
            merged = dict(DEFAULT_PREFERENCES)
            merged.update(prefs)
            return merged
        except Exception:
            return dict(DEFAULT_PREFERENCES)
    return dict(DEFAULT_PREFERENCES)


def save_preferences(prefs: dict) -> bool:
    """Write user preferences to JSON."""
    ensure_user_data_dirs()
    try:
        with open(PREFERENCES_FILE, "w", encoding="utf-8") as f:
            json.dump(prefs, f, indent=2)
        return True
    except Exception as e:
        print(f"[data_manager] Error saving preferences — {e}")
        return False


# ─────────────────────────────────────────────
# SAMPLE DATA LOADER
# ─────────────────────────────────────────────

def load_sample_wardrobe() -> pd.DataFrame:
    """Return the read-only sample wardrobe CSV (labeled is_sample=True)."""
    if os.path.exists(SAMPLE_WARDROBE_FILE):
        df = pd.read_csv(SAMPLE_WARDROBE_FILE, dtype=str)
        df = _enforce_schema(df, WARDROBE_SCHEMA)
        df["formality"]  = pd.to_numeric(df["formality"], errors="coerce").fillna(3).astype(int)
        df["times_worn"] = pd.to_numeric(df["times_worn"], errors="coerce").fillna(0).astype(int)
        df["is_sample"]  = True
        return df
    return _empty_wardrobe()


def import_sample_data() -> int:
    """
    Copy sample wardrobe records into the live wardrobe,
    but only if the wardrobe is currently empty.
    Returns the number of items imported.
    """
    df = load_wardrobe()
    if not df.empty:
        return 0   # Don't overwrite existing data
    sample = load_sample_wardrobe()
    if sample.empty:
        return 0
    save_wardrobe(sample)
    return len(sample)
