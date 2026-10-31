"""
FitChecker — Central Configuration
===================================
All tunable constants live here so you can change them in one place
without hunting through multiple files.

BEGINNER NOTE:
  A "constant" is a variable you set once and never change while the
  program runs.  Putting them all here makes the project easy to
  understand and adjust.
"""

import os

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR       = os.path.join(BASE_DIR, "data")
USER_DATA_DIR  = os.path.join(BASE_DIR, "user_data")
IMAGES_DIR     = os.path.join(USER_DATA_DIR, "images")
MODELS_DIR     = os.path.join(BASE_DIR, "models")

WARDROBE_FILE       = os.path.join(USER_DATA_DIR, "wardrobe.csv")
FEEDBACK_FILE       = os.path.join(USER_DATA_DIR, "feedback.csv")
PREFERENCES_FILE    = os.path.join(USER_DATA_DIR, "preferences.json")
PROFILE_FILE        = os.path.join(USER_DATA_DIR, "profile.json")
WEAR_HISTORY_FILE   = os.path.join(USER_DATA_DIR, "wear_history.csv")
OUTFITS_FILE        = os.path.join(USER_DATA_DIR, "outfits.csv")

SAMPLE_WARDROBE_FILE = os.path.join(DATA_DIR, "sample_wardrobe.csv")
SAMPLE_FEEDBACK_FILE = os.path.join(DATA_DIR, "sample_feedback.csv")
OCCASIONS_FILE       = os.path.join(DATA_DIR, "occasions.json")

ML_MODEL_FILE = os.path.join(MODELS_DIR, "rf_recommender.pkl")

# ─────────────────────────────────────────────
# GARMENT CATEGORIES
# ─────────────────────────────────────────────
CATEGORIES = [
    "T-Shirt",
    "Shirt",
    "Polo",
    "Henley",
    "Top",
    "Blouse",
    "Sweater",
    "Hoodie",
    "Sweatshirt",
    "Jeans",
    "Trousers",
    "Chinos",
    "Shorts",
    "Skirt",
    "Dress",
    "Ethnic / Traditional Wear",
    "Blazer",
    "Jacket",
    "Windcheater",
    "Coat",
    "Sneakers",
    "Formal Shoes",
    "Sandals",
    "Boots",
    "Accessories",
    "Other",
]

# High-level groups used by the outfit-generation engine
CATEGORY_GROUP = {
    "tops":    ["T-Shirt", "Shirt", "Polo", "Henley", "Top", "Blouse",
                "Sweater", "Hoodie", "Sweatshirt"],
    "bottoms": ["Jeans", "Trousers", "Chinos", "Shorts", "Skirt"],
    "one_piece": ["Dress", "Ethnic / Traditional Wear"],
    "outer":   ["Blazer", "Jacket", "Windcheater", "Coat"],
    "footwear": ["Sneakers", "Formal Shoes", "Sandals", "Boots"],
    "accessories": ["Accessories"],
}

PATTERNS = ["Plain", "Striped", "Checked", "Printed", "Floral", "Other"]

SEASONS = ["All Seasons", "Summer", "Winter", "Monsoon / Rainy", "Spring / Autumn"]

WEATHER_OPTIONS = ["Any", "Hot", "Warm", "Cool", "Cold", "Rainy"]

FIT_OPTIONS = ["Regular", "Slim", "Loose / Oversized", "Fitted", "Other"]

STYLE_TAGS = [
    "Casual", "Formal", "Smart Casual", "Streetwear", "Ethnic",
    "Sporty", "Bohemian", "Minimalist", "Preppy", "Party",
]

# Color options (derived from color compatibility engine)
try:
    from src.color_compatibility import AVAILABLE_COLORS
except Exception:
    AVAILABLE_COLORS = [
        "beige", "black", "blue", "brown", "charcoal", "cream", "cyan",
        "dark blue", "dark brown", "dark green", "dark grey", "gray", "green",
        "grey", "hot pink", "khaki", "lavender", "light blue", "light grey",
        "light pink", "maroon", "mint green", "mustard", "navy blue",
        "off white", "olive green", "orange", "pink", "purple", "red",
        "rust", "sky blue", "tan", "teal", "white", "yellow"
    ]

# ─────────────────────────────────────────────
# OCCASIONS
# ─────────────────────────────────────────────
OCCASIONS = [
    "Daily College Wear",
    "College Presentation",
    "Lab / Workshop Session",
    "College Fest",
    "Casual Outing",
    "Date",
    "Party",
    "Interview",
    "Formal Event",
    "Custom",
]

# For each occasion: target formality (1–5) and allowed weather tags
OCCASION_PROFILES = {
    "Daily College Wear":       {"formality": 2, "style": ["Casual", "Smart Casual", "Sporty"], "weather": ["Any", "Hot", "Warm", "Cool"]},
    "College Presentation":     {"formality": 3, "style": ["Smart Casual", "Formal"], "weather": ["Any"]},
    "Lab / Workshop Session":   {"formality": 2, "style": ["Casual", "Sporty"], "weather": ["Any"]},
    "College Fest":             {"formality": 2, "style": ["Casual", "Streetwear", "Bohemian", "Party"], "weather": ["Any"]},
    "Casual Outing":            {"formality": 2, "style": ["Casual", "Streetwear", "Minimalist"], "weather": ["Any"]},
    "Date":                     {"formality": 3, "style": ["Smart Casual", "Casual", "Minimalist"], "weather": ["Any"]},
    "Party":                    {"formality": 3, "style": ["Party", "Streetwear", "Casual"], "weather": ["Any"]},
    "Interview":                {"formality": 4, "style": ["Formal", "Smart Casual"], "weather": ["Any"]},
    "Formal Event":             {"formality": 5, "style": ["Formal", "Ethnic"], "weather": ["Any"]},
    "Custom":                   {"formality": 3, "style": [], "weather": ["Any"]},
}

# ─────────────────────────────────────────────
# SCORING WEIGHTS  (must sum to 1.0)
# These are engineering defaults, not scientific facts.
# Change them and re-run tests to see the effect.
# ─────────────────────────────────────────────
SCORE_WEIGHTS = {
    "occasion_suitability":      0.30,
    "color_compatibility":       0.25,
    "style_formality":           0.20,
    "weather_suitability":       0.15,
    "personal_preference":       0.10,
}

# ─────────────────────────────────────────────
# REPETITION PENALTY
# Applied when the same outfit was worn recently
# ─────────────────────────────────────────────
RECENT_WEAR_DAYS = 7          # How many days counts as "recent"
REPETITION_PENALTY = 0.20     # Fraction to subtract (0.20 = 20 points out of 100)

# ─────────────────────────────────────────────
# IMAGE SETTINGS
# ─────────────────────────────────────────────
MAX_IMAGE_SIZE_MB  = 10
ALLOWED_IMAGE_TYPES = [".jpg", ".jpeg", ".png", ".webp"]
THUMBNAIL_SIZE      = (400, 400)   # Resize uploaded images to this max
NUM_DOMINANT_COLORS = 3            # Colors to extract per image

# ─────────────────────────────────────────────
# OUTFIT GENERATION LIMITS
# ─────────────────────────────────────────────
MAX_OUTFITS_TO_SCORE  = 200   # Search limit for large wardrobes
TOP_N_RECOMMENDATIONS = 5     # Maximum outfits shown to user

# ─────────────────────────────────────────────
# ML SAFEGUARDS
# ─────────────────────────────────────────────
MIN_SAMPLES_FOR_TRAINING = 20   # Below this, refuse to train
MIN_CLASSES_FOR_TRAINING = 2    # Need at least two rating labels
