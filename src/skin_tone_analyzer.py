"""
skin_tone_analyzer.py — Personal Color & Skin Tone Analysis for FitChecker
==========================================================================
PURPOSE:
  Detects or allows user selection of skin tone and direct color palettes
  derived from the 24 foundation shades (Fair Porcelain, Light Warm Peach,
  Medium Olive, Medium Golden, Rich Dusky, Deep Espresso, and Vitiligo).
  Completely removes seasonal jargon ("Cool Summer", "Cool Winter", "Warm Autumn",
  "Warm Spring") in favor of direct, intuitive clothing color flattery.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import io
import math
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
import numpy as np
from PIL import Image

from config.settings import PROFILE_FILE, USER_DATA_DIR, IMAGES_DIR

# ─────────────────────────────────────────────
# 6 DIRECT COMPLEXION PALETTES (+ VITILIGO DUO)
# ─────────────────────────────────────────────

COMPLEXION_PALETTES = {
    "fair_porcelain": {
        "tier_id": "fair_porcelain",
        "name": "Fair Porcelain & Rosy (Cool)",
        "season_name": "Fair Porcelain & Rosy",  # Backward compatibility
        "shades_covered": "Shades 01, 02, 04, 07",
        "description": "Very fair to light complexions with delicate alabaster, ivory, or cool rosy undertones.",
        "best_colors": ["Sky Blue", "Navy Blue", "Sage Green", "Lavender", "Dusty Pink", "Off White", "Pure White", "Emerald Green", "Burgundy", "Slate Grey", "Charcoal", "Black"],
        "warmth_boosters": ["Dusty Pink", "Lavender", "Rose Quartz", "Soft Berry", "Mint Green"],
        "neutrals": ["Navy Blue", "Slate Grey", "Pure White", "Charcoal", "Off White", "Black"],
        "avoid_colors": ["Mustard", "Orange", "Rust", "Dark Brown", "Neon Shades", "Sickly Pale Beige"],
        "old_money_pick": "Powder Blue / Sky Blue",
        "quote": "Crisp, refined and architectural. Cool pastels, navy, and jewel tones illuminate porcelain features without washing them out.",
        "complementary_suggestions": "Pair sky blue shirts with navy trousers or off-white chinos for a clean Riviera aesthetic.",
    },
    "light_warm_peach": {
        "tier_id": "light_warm_peach",
        "name": "Fair & Light Warm Peach (Neutral-Warm)",
        "season_name": "Fair & Light Warm Peach",
        "shades_covered": "Shades 03, 06, 09, 10",
        "description": "Fair to light-medium complexions with golden peach, strawberry blonde, or sun-freckled warm undertones.",
        "best_colors": ["Royal Blue", "Teal", "Blush Pink", "Sage Green", "Beige", "Olive Green", "Pure White", "Coral", "French Navy", "Light Camel", "Sky Blue"],
        "warmth_boosters": ["Coral", "Peach", "Blush Pink", "Warm Cream", "Honey Gold"],
        "neutrals": ["Warm Cream", "Beige", "Light Camel", "French Navy", "Pure White"],
        "avoid_colors": ["Too Dark Brown", "Neon Green", "Neon Yellow", "Orange", "Very Dark Purple", "Bright Red"],
        "old_money_pick": "Powder Blue / Sage Green",
        "quote": "Luminous, fresh and vibrant. Soft earthy sages, blush pinks, and warm creams bring out natural peach vitality.",
        "complementary_suggestions": "Pair blush pink or sage green shirts with tailored beige trousers and white sneakers.",
    },
    "medium_olive": {
        "tier_id": "medium_olive",
        "name": "Light to Medium Olive (Warm/Olive)",
        "season_name": "Light to Medium Olive & Neutral",
        "shades_covered": "Shades 08, 11, 13",
        "description": "Light-medium to medium skin with distinct neutral or golden-olive greenish undertones.",
        "best_colors": ["Olive Green", "Teal", "Camel", "Navy Blue", "Burnt Orange", "Off White", "Sage Green", "Emerald Green", "Warm Taupe", "Burgundy", "Charcoal", "Black"],
        "warmth_boosters": ["Burnt Orange", "Terracotta", "Warm Taupe", "Deep Wine", "Mustard"],
        "neutrals": ["Navy Blue", "Off White", "Camel", "Charcoal", "Warm Taupe"],
        "avoid_colors": ["Icy Blue", "Bright Yellow", "Lavender", "Neon Lime Green", "Sickly Yellow-Green"],
        "old_money_pick": "Olive Green / Camel",
        "quote": "Balanced, earthy and modern. Deep jewel greens, warm camels, and navy counteract olive cast and give radiant depth.",
        "complementary_suggestions": "Pair olive green overshirts with camel trousers and off-white tees.",
    },
    "medium_golden": {
        "tier_id": "medium_golden",
        "name": "Medium Golden & Wheatish (Warm Amber)",
        "season_name": "Medium Golden & Honey Tan",
        "shades_covered": "Shades 12, 14, 15, 16",
        "description": "Medium wheatish complexions with prominent warm honey, golden amber, or bronze undertones (BUDZ).",
        "best_colors": ["Olive Green", "Navy Blue", "Cream", "Rust", "Rust Orange", "Wine", "Mustard", "Chocolate Brown", "Teal", "Beige", "Emerald Green", "Terracotta", "Dark Blue", "Black", "White", "Crisp White", "Pure White", "Khaki"],
        "warmth_boosters": ["Rust", "Rust Orange", "Terracotta", "Mustard", "Wine", "Rich Burgundy", "Chocolate Brown", "Warm Ochre"],
        "neutrals": ["Cream", "Beige", "Navy Blue", "Chocolate Brown", "Black", "White", "Crisp White", "Pure White", "Khaki", "Camel"],
        "avoid_colors": ["Pastel Pink", "Neon Green", "Neon Yellow", "Neon Pink", "Silver Grey", "Icy Blue"],
        "old_money_pick": "Olive Green (Ranked #1 Best Pick)",
        "quote": "Rich, grounded and magnetic. Olive green (#1 Best Pick), warm rust, cream, and deep navy illuminate your natural golden wheatish glow.",
        "complementary_suggestions": "Pair olive green shirts with pleated cream trousers, or rust sweaters with black trousers.",
    },
    "rich_dusky": {
        "tier_id": "rich_dusky",
        "name": "Tan & Dusky Bronze (Warm/Neutral)",
        "season_name": "Rich Dusky & Caramel Bronze",
        "shades_covered": "Shades 17, 18, 19, 20",
        "description": "Rich dusky, golden bronze, and warm caramel complexions with deep luminous undertones.",
        "best_colors": ["Beige", "Mocha Brown", "Caramel", "Olive Green", "Cream", "Rust", "Chocolate Brown", "Sand", "Khaki", "Royal Blue", "Forest Green", "Mustard", "Pure White", "Black"],
        "warmth_boosters": ["Caramel", "Rust", "Mocha Brown", "Mustard", "Burnt Orange"],
        "neutrals": ["Cream", "Sand", "Beige", "Khaki", "Chocolate Brown", "Pure White", "Black"],
        "avoid_colors": ["Pastel Shades", "Light Grey", "Lavender", "Neon Pink", "Icy Blue", "Bright Yellow"],
        "old_money_pick": "Chocolate Brown / Khaki",
        "quote": "Warm, striking and opulent. Earthy mocha, caramel, and olive glow effortlessly against dusky skin without washout.",
        "complementary_suggestions": "Try tan/khaki linen shirts tucked into chocolate brown trousers with brown leather loafers.",
    },
    "deep_espresso": {
        "tier_id": "deep_espresso",
        "name": "Deep Espresso & Ebony (Rich Contrast)",
        "season_name": "Deep Espresso & Ebony",
        "shades_covered": "Shades 21, 22, 23, 24",
        "description": "Deep dark chocolate, rich mahogany, espresso, and luminous obsidian midnight ebony tones.",
        "best_colors": ["Pure White", "Chocolate Brown", "Cobalt Blue", "Royal Blue", "Emerald Green", "Bright Yellow", "Burgundy", "Gold", "Charcoal", "Black", "Fuchsia", "Ivory"],
        "warmth_boosters": ["Bright Yellow", "Cobalt Blue", "Emerald Green", "Gold", "Burgundy"],
        "neutrals": ["Pure White", "Ivory", "Black", "Charcoal", "Chocolate Brown"],
        "avoid_colors": ["Light Pastels", "Light Beige", "Cool Grey", "Neon Green", "Neon Orange", "Baby Pink"],
        "old_money_pick": "Chocolate Brown / Stark White",
        "quote": "Architectural, iconic and high-contrast. Bold jewel tones, stark white, and deep chocolate brown radiate unmatched presence.",
        "complementary_suggestions": "Stark white or cobalt blue shirts with chocolate brown trousers create a stunning high-contrast statement.",
    },
    "vitiligo_duo": {
        "tier_id": "vitiligo_duo",
        "name": "Vitiligo & Dual-Tone (Sculptural Contrast)",
        "season_name": "Vitiligo & Dual-Tone",
        "shades_covered": "Shade 05",
        "description": "Unique multi-tonal complexion featuring high natural contrast between porcelain alabaster and rich cocoa.",
        "best_colors": ["Pure White", "Royal Blue", "Forest Green", "Camel", "Burgundy", "Navy Blue", "Emerald Green", "Charcoal", "Black"],
        "warmth_boosters": ["Burgundy", "Royal Blue", "Warm Ochre", "Emerald Green"],
        "neutrals": ["Pure White", "Navy Blue", "Camel", "Charcoal", "Black"],
        "avoid_colors": ["Low-contrast faded pastels", "Murky muddy grey", "Dull washed-out taupe"],
        "old_money_pick": "Camel / Navy Blue",
        "quote": "Sculptural, artistic and unique. High-contrast foundational neutrals celebrate your natural skin dimension with poise.",
        "complementary_suggestions": "Pair stark white shirts with deep navy or rich burgundy outerwear.",
    },
}

# Backward compatibility alias
SEASON_PALETTES = {
    "Autumn": COMPLEXION_PALETTES["medium_golden"],
    "Spring": COMPLEXION_PALETTES["light_warm_peach"],
    "Winter": COMPLEXION_PALETTES["deep_espresso"],
    "Summer": COMPLEXION_PALETTES["fair_porcelain"],
    **COMPLEXION_PALETTES,
}


# ─────────────────────────────────────────────
# 24 FOUNDATION SHADES (FROM USER IMAGE)
# ─────────────────────────────────────────────

SHADES_24 = {
    "shade_01": {
        "shade_id": "shade_01",
        "shade_num": 1,
        "name": "Shade 01 — Very Fair Porcelain",
        "tier": "fair_porcelain",
        "hex": "#F6ECE6",
        "rgb": (246, 236, 230),
        "undertone": "Cool Alabaster",
        "notes": "Snowy porcelain with delicate cool translucence.",
    },
    "shade_02": {
        "shade_id": "shade_02",
        "shade_num": 2,
        "name": "Shade 02 — Fair Neutral Ivory",
        "tier": "fair_porcelain",
        "hex": "#F0DCD2",
        "rgb": (240, 220, 210),
        "undertone": "Neutral Ivory",
        "notes": "Delicate fair ivory with balanced undertone.",
    },
    "shade_03": {
        "shade_id": "shade_03",
        "shade_num": 3,
        "name": "Shade 03 — Fair Warm Peach",
        "tier": "light_warm_peach",
        "hex": "#EFCDBE",
        "rgb": (239, 205, 190),
        "undertone": "Warm Peach",
        "notes": "Fair porcelain kissed with warm peach glow.",
    },
    "shade_04": {
        "shade_id": "shade_04",
        "shade_num": 4,
        "name": "Shade 04 — Fair Cool Rosy",
        "tier": "fair_porcelain",
        "hex": "#E8C8BE",
        "rgb": (232, 200, 190),
        "undertone": "Cool Rosy",
        "notes": "Light skin with gentle pink / rose undertones.",
    },
    "shade_05": {
        "shade_id": "shade_05",
        "shade_num": 5,
        "name": "Shade 05 — Vitiligo Duo-Tone",
        "tier": "vitiligo_duo",
        "hex": "#BD8564",
        "rgb": (189, 133, 100),
        "undertone": "Dual Contrast (Ivory + Cocoa)",
        "notes": "Striking dual-toned pigment with high natural contrast.",
    },
    "shade_06": {
        "shade_id": "shade_06",
        "shade_num": 6,
        "name": "Shade 06 — Light Warm Freckled Peach",
        "tier": "light_warm_peach",
        "hex": "#E2B99C",
        "rgb": (226, 185, 156),
        "undertone": "Warm Golden Peach",
        "notes": "Sun-kissed fair-to-light with delicate freckles.",
    },
    "shade_07": {
        "shade_id": "shade_07",
        "shade_num": 7,
        "name": "Shade 07 — Light Cool Beige",
        "tier": "fair_porcelain",
        "hex": "#DCBCAB",
        "rgb": (220, 188, 171),
        "undertone": "Cool Beige",
        "notes": "Soft muted beige with delicate cool undertone.",
    },
    "shade_08": {
        "shade_id": "shade_08",
        "shade_num": 8,
        "name": "Shade 08 — Light Golden Ivory & Olive",
        "tier": "medium_olive",
        "hex": "#DDBA97",
        "rgb": (221, 186, 151),
        "undertone": "Light Olive / Golden Ivory",
        "notes": "Light skin with clear golden-olive undertones.",
    },
    "shade_09": {
        "shade_id": "shade_09",
        "shade_num": 9,
        "name": "Shade 09 — Light Neutral Sand",
        "tier": "light_warm_peach",
        "hex": "#DBB198",
        "rgb": (219, 177, 152),
        "undertone": "Warm Neutral Sand",
        "notes": "Light neutral with gentle warm sand undertone.",
    },
    "shade_10": {
        "shade_id": "shade_10",
        "shade_num": 10,
        "name": "Shade 10 — Light-Medium Warm Freckled Honey",
        "tier": "light_warm_peach",
        "hex": "#C69674",
        "rgb": (198, 150, 116),
        "undertone": "Warm Honey Freckled",
        "notes": "Light-medium golden tan with prominent warm freckles.",
    },
    "shade_11": {
        "shade_id": "shade_11",
        "shade_num": 11,
        "name": "Shade 11 — Light-Medium Neutral Olive Tan",
        "tier": "medium_olive",
        "hex": "#C4967A",
        "rgb": (196, 150, 122),
        "undertone": "Neutral Olive Tan",
        "notes": "Balanced light-medium tan with neutral-olive undertone.",
    },
    "shade_12": {
        "shade_id": "shade_12",
        "shade_num": 12,
        "name": "Shade 12 — Medium Warm Golden Glow",
        "tier": "medium_golden",
        "hex": "#BD8965",
        "rgb": (189, 137, 101),
        "undertone": "Warm Golden Honey",
        "notes": "Radiant golden glow with warm yellow-amber depth.",
    },
    "shade_13": {
        "shade_id": "shade_13",
        "shade_num": 13,
        "name": "Shade 13 — Medium Warm Olive Tan",
        "tier": "medium_olive",
        "hex": "#B88161",
        "rgb": (184, 129, 97),
        "undertone": "Warm Olive",
        "notes": "Medium skin with natural golden-green olive warmth.",
    },
    "shade_14": {
        "shade_id": "shade_14",
        "shade_num": 14,
        "name": "Shade 14 — Medium Honey Caramel",
        "tier": "medium_golden",
        "hex": "#AD7A55",
        "rgb": (173, 122, 85),
        "undertone": "Warm Caramel",
        "notes": "Medium honey-caramel with golden undertones.",
    },
    "shade_15": {
        "shade_id": "shade_15",
        "shade_num": 15,
        "name": "Shade 15 — Medium Golden Amber",
        "tier": "medium_golden",
        "hex": "#A7714C",
        "rgb": (167, 113, 76),
        "undertone": "Golden Amber",
        "notes": "Rich golden amber with radiant warm reflectance.",
    },
    "shade_16": {
        "shade_id": "shade_16",
        "shade_num": 16,
        "name": "Shade 16 — Medium-Deep Olive Bronze",
        "tier": "medium_golden",
        "hex": "#996643",
        "rgb": (153, 102, 67),
        "undertone": "Warm Olive Bronze",
        "notes": "Deep golden-olive bronze with grounded warmth.",
    },
    "shade_17": {
        "shade_id": "shade_17",
        "shade_num": 17,
        "name": "Shade 17 — Rich Caramel Warm Freckled",
        "tier": "rich_dusky",
        "hex": "#915E3B",
        "rgb": (145, 94, 59),
        "undertone": "Warm Caramel Freckled",
        "notes": "Rich caramel skin with warm sun-drenched freckles.",
    },
    "shade_18": {
        "shade_id": "shade_18",
        "shade_num": 18,
        "name": "Shade 18 — Rich Dusky Golden Brown",
        "tier": "rich_dusky",
        "hex": "#855232",
        "rgb": (133, 82, 50),
        "undertone": "Rich Dusky Copper",
        "notes": "Luminous dusky golden brown with copper undertones.",
    },
    "shade_19": {
        "shade_id": "shade_19",
        "shade_num": 19,
        "name": "Shade 19 — Rich Chestnut Terracotta",
        "tier": "rich_dusky",
        "hex": "#7A4528",
        "rgb": (122, 69, 40),
        "undertone": "Warm Chestnut",
        "notes": "Deep warm chestnut with terracotta richness.",
    },
    "shade_20": {
        "shade_id": "shade_20",
        "shade_num": 20,
        "name": "Shade 20 — Rich Dark Bronze Glow",
        "tier": "rich_dusky",
        "hex": "#6C3C20",
        "rgb": (108, 60, 32),
        "undertone": "Deep Golden Bronze",
        "notes": "Deep bronze skin with glowing warm undertones.",
    },
    "shade_21": {
        "shade_id": "shade_21",
        "shade_num": 21,
        "name": "Shade 21 — Deep Neutral Espresso",
        "tier": "deep_espresso",
        "hex": "#50301F",
        "rgb": (80, 48, 31),
        "undertone": "Neutral-Cool Espresso",
        "notes": "Deep dark chocolate with cool neutral depth.",
    },
    "shade_22": {
        "shade_id": "shade_22",
        "shade_num": 22,
        "name": "Shade 22 — Deep Mahogany Dark Cocoa",
        "tier": "deep_espresso",
        "hex": "#4A2A1B",
        "rgb": (74, 42, 27),
        "undertone": "Warm Mahogany",
        "notes": "Rich dark cocoa with warm reddish-brown undertone.",
    },
    "shade_23": {
        "shade_id": "shade_23",
        "shade_num": 23,
        "name": "Shade 23 — Deep Ebony Dark Espresso",
        "tier": "deep_espresso",
        "hex": "#3A1F14",
        "rgb": (58, 31, 20),
        "undertone": "Deep Ebony",
        "notes": "Intense dark espresso with architectural depth.",
    },
    "shade_24": {
        "shade_id": "shade_24",
        "shade_num": 24,
        "name": "Shade 24 — Deepest Midnight Ebony",
        "tier": "deep_espresso",
        "hex": "#28150D",
        "rgb": (40, 21, 13),
        "undertone": "Cool Midnight Ebony",
        "notes": "Deepest obsidian ebony with sleek luminous sheen.",
    },
}

# Quick presets for manual selector
SKIN_TONE_PRESETS = [
    {"id": "shade_01", "label": "Shade 01 — Very Fair Porcelain", "season": "fair_porcelain", "hex": "#F6ECE6", "gender_neutral": True},
    {"id": "shade_03", "label": "Shade 03 — Fair Warm Peach", "season": "light_warm_peach", "hex": "#EFCDBE", "gender_neutral": True},
    {"id": "shade_06", "label": "Shade 06 — Light Warm Freckled Peach", "season": "light_warm_peach", "hex": "#E2B99C", "gender_neutral": True},
    {"id": "shade_08", "label": "Shade 08 — Light Golden Olive", "season": "medium_olive", "hex": "#DDBA97", "gender_neutral": True},
    {"id": "shade_12", "label": "Shade 12 — Medium Warm Golden Glow", "season": "medium_golden", "hex": "#BD8965", "gender_neutral": True},
    {"id": "shade_15", "label": "Shade 15 — Medium Golden Amber", "season": "medium_golden", "hex": "#A7714C", "gender_neutral": True},
    {"id": "shade_18", "label": "Shade 18 — Rich Dusky Golden Brown", "season": "rich_dusky", "hex": "#855232", "gender_neutral": True},
    {"id": "shade_20", "label": "Shade 20 — Rich Dark Bronze Glow", "season": "rich_dusky", "hex": "#6C3C20", "gender_neutral": True},
    {"id": "shade_22", "label": "Shade 22 — Deep Mahogany Dark Cocoa", "season": "deep_espresso", "hex": "#4A2A1B", "gender_neutral": True},
    {"id": "shade_24", "label": "Shade 24 — Deepest Midnight Ebony", "season": "deep_espresso", "hex": "#28150D", "gender_neutral": True},
    {"id": "shade_05", "label": "Shade 05 — Vitiligo Duo-Tone", "season": "vitiligo_duo", "hex": "#BD8564", "gender_neutral": True},
]


# ─────────────────────────────────────────────
# RESOLUTION UTILITY
# ─────────────────────────────────────────────

def resolve_palette(key: str) -> Dict[str, Any]:
    """Resolves any shade ID, tier ID, or legacy seasonal name to its palette dictionary."""
    if not key:
        return COMPLEXION_PALETTES["medium_golden"]

    # Direct tier match
    if key in COMPLEXION_PALETTES:
        return COMPLEXION_PALETTES[key]

    # Shade match: "shade_15"
    if key in SHADES_24:
        tier_id = SHADES_24[key]["tier"]
        return COMPLEXION_PALETTES.get(tier_id, COMPLEXION_PALETTES["medium_golden"])

    # Number match: "15" or "shade 15"
    k_clean = str(key).strip().lower().replace(" ", "_")
    if k_clean in SHADES_24:
        return COMPLEXION_PALETTES.get(SHADES_24[k_clean]["tier"], COMPLEXION_PALETTES["medium_golden"])
    for sid, sdata in SHADES_24.items():
        if str(sdata["shade_num"]) == str(key).strip():
            return COMPLEXION_PALETTES.get(sdata["tier"], COMPLEXION_PALETTES["medium_golden"])

    # Legacy seasonal name mapping
    k_low = str(key).lower().strip()
    legacy_map = {
        "autumn": "medium_golden",
        "warm autumn": "medium_golden",
        "spring": "light_warm_peach",
        "warm spring": "light_warm_peach",
        "summer": "fair_porcelain",
        "cool summer": "fair_porcelain",
        "winter": "deep_espresso",
        "cool winter": "deep_espresso",
    }
    target_tier = legacy_map.get(k_low, "medium_golden")
    return COMPLEXION_PALETTES.get(target_tier, COMPLEXION_PALETTES["medium_golden"])


# ─────────────────────────────────────────────
# PROFILE PERSISTENCE
# ─────────────────────────────────────────────

def get_default_profile() -> Dict[str, Any]:
    return {
        "name": "BUDZ",
        "gender": "Boy",  # "Boy", "Girl", "Non-binary"
        "skin_tone_id": "shade_15",
        "skin_tone_label": "Shade 15 — Medium Golden Amber",
        "palette_tier": "medium_golden",
        "palette_tier_label": "Medium Golden & Honey Tan",
        "skin_hex": "#A7714C",
        "season": "medium_golden",  # Backward compatibility
        "undertone": "Golden Amber",
        "contrast_level": "Medium Contrast",
        "body_build": "athletic_v_taper",
        "height_profile": "average",
        "torso_balance": "balanced",
        "avatar_path": "",
        "notes": "Curated bespoke wardrobe with a cool, rich, quiet luxury aesthetic.",
    }


def load_profile(user_id: Optional[str] = None) -> Dict[str, Any]:
    """Load user profile from JSON or return default."""
    from src.user_manager import get_user_profile_file, get_active_user
    target_file = get_user_profile_file(user_id)
    uid = user_id or get_active_user()
    defaults = get_default_profile()
    defaults["name"] = uid
    if os.path.exists(target_file):
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                defaults.update(data)
                return defaults
        except Exception:
            pass
    return defaults


def save_profile(profile_data: Dict[str, Any], user_id: Optional[str] = None) -> bool:
    """Save user profile to JSON."""
    from src.user_manager import get_user_profile_file
    target_file = get_user_profile_file(user_id)
    os.makedirs(os.path.dirname(target_file), exist_ok=True)
    try:
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=2)
        return True
    except Exception:
        return False


# ─────────────────────────────────────────────
# FACE & SKIN TONE EXTRACTION (24-SHADE MATCHING)
# ─────────────────────────────────────────────

def analyze_face_image(image_bytes: bytes) -> Dict[str, Any]:
    """
    Extract facial skin reflectance and map it directly into the 24-shade system
    and its flattering color palette, completely eliminating seasonal jargon.
    """
    try:
        pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_np = np.array(pil_img)

        # Subsample if large for responsive analysis
        h, w, _ = img_np.shape
        if max(h, w) > 800:
            pil_img.thumbnail((800, 800), Image.LANCZOS)
            img_np = np.array(pil_img)
            h, w, _ = img_np.shape

        # Face detection using OpenCV Haar Cascade if available
        try:
            import cv2
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(60, 60))
            if len(faces) > 0:
                # Pick largest face
                faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
                fx, fy, fw, fh = faces[0]
                # Center cheeks and forehead (avoids background and phone bezels)
                face_roi = img_np[fy + int(fh*0.25): fy + int(fh*0.70), fx + int(fw*0.20): fx + int(fw*0.80)]
                hair_roi = img_np[max(0, fy - int(fh*0.08)): fy + int(fh*0.18), fx + int(fw*0.25): fx + int(fw*0.75)]
            else:
                y1, y2 = int(h * 0.25), int(h * 0.75)
                x1, x2 = int(w * 0.25), int(w * 0.75)
                face_roi = img_np[y1:y2, x1:x2]
                hair_roi = img_np[0:int(h * 0.2), :]
        except Exception:
            y1, y2 = int(h * 0.25), int(h * 0.75)
            x1, x2 = int(w * 0.25), int(w * 0.75)
            face_roi = img_np[y1:y2, x1:x2]
            hair_roi = img_np[0:int(h * 0.2), :]

        # Segment skin in YCrCb color space
        r = face_roi[:, :, 0].astype(float)
        g = face_roi[:, :, 1].astype(float)
        b = face_roi[:, :, 2].astype(float)

        y_channel  = 0.299 * r + 0.587 * g + 0.114 * b
        cr_channel = 128 + 0.5 * r - 0.418688 * g - 0.081312 * b
        cb_channel = 128 - 0.168736 * r - 0.331264 * g + 0.5 * b

        skin_mask = (
            (cr_channel >= 130) & (cr_channel <= 175) &
            (cb_channel >= 75) & (cb_channel <= 130) &
            (y_channel >= 40) & (y_channel <= 235)
        )

        if np.sum(skin_mask) > 100:
            skin_r = np.median(r[skin_mask])
            skin_g = np.median(g[skin_mask])
            skin_b = np.median(b[skin_mask])
        else:
            skin_r = np.median(r)
            skin_g = np.median(g)
            skin_b = np.median(b)

        r_int = int(np.clip(skin_r, 0, 255))
        g_int = int(np.clip(skin_g, 0, 255))
        b_int = int(np.clip(skin_b, 0, 255))
        hex_code = f"#{r_int:02X}{g_int:02X}{b_int:02X}"

        # Contrast estimation (hair/background vs skin)
        brightness = (r_int + g_int + b_int) / 3.0
        hair_brightness = np.median(hair_roi) if (isinstance(hair_roi, np.ndarray) and hair_roi.size > 0) else 50.0
        contrast_diff = abs(brightness - hair_brightness)

        if contrast_diff > 65:
            contrast_level = "High Contrast"
        elif contrast_diff > 35:
            contrast_level = "Medium Contrast"
        else:
            contrast_level = "Soft Contrast"

        # Find closest shade among the 24 foundation shades (excluding vitiligo duo unless manual)
        best_dist = float("inf")
        best_shade_id = "shade_15"

        for s_id, s_data in SHADES_24.items():
            if s_id == "shade_05":
                continue  # vitiligo is distinctive
            ref_r, ref_g, ref_b = s_data["rgb"]
            # Weighted colorimetric Euclidean distance
            # Human eye is more sensitive to red-green skin shifts
            dist = math.sqrt(
                0.30 * (r_int - ref_r) ** 2 +
                0.50 * (g_int - ref_g) ** 2 +
                0.20 * (b_int - ref_b) ** 2
            )
            if dist < best_dist:
                best_dist = dist
                best_shade_id = s_id

        matched_shade = SHADES_24[best_shade_id]
        palette_info = COMPLEXION_PALETTES[matched_shade["tier"]]

        # Build clear, jargon-free diagnostic explanation
        diagnostic_reason = (
            f"Skin Colorimetry Diagnostic: Facial reflectance identifies your complexion as "
            f"'{matched_shade['name']}' with a {matched_shade['undertone'].lower()} undertone and {contrast_level.lower()}. "
            f"Your complexion is naturally flattered by {', '.join(palette_info['best_colors'][:4])}, which illuminate your natural skin depth, "
            f"while {', '.join(palette_info['avoid_colors'][:2])} cause facial washout."
        )

        return {
            "status": "success",
            "skin_hex": hex_code,
            "shade_id": best_shade_id,
            "shade_number": matched_shade["shade_num"],
            "skin_tone_label": matched_shade["name"],
            "palette_tier": matched_shade["tier"],
            "palette_tier_label": palette_info["name"],
            "season": matched_shade["tier"],  # Backward compatibility
            "undertone": matched_shade["undertone"],
            "contrast_level": contrast_level,
            "palette": palette_info,
            "diagnostic_reason": diagnostic_reason,
            "flattering_colors": palette_info["best_colors"][:6],
            "washout_colors": palette_info["avoid_colors"][:4],
            "neutrals": palette_info["neutrals"][:4],
            "advice": palette_info["description"],
        }
    except Exception as e:
        # Fallback default (Medium Golden Amber)
        matched_shade = SHADES_24["shade_15"]
        palette_info = COMPLEXION_PALETTES["medium_golden"]
        return {
            "status": "fallback",
            "skin_hex": "#A7714C",
            "shade_id": "shade_15",
            "shade_number": 15,
            "skin_tone_label": matched_shade["name"],
            "palette_tier": "medium_golden",
            "palette_tier_label": palette_info["name"],
            "season": "medium_golden",
            "undertone": "Golden Amber",
            "contrast_level": "Medium Contrast",
            "palette": palette_info,
            "diagnostic_reason": (
                "Standard Calibration: Calibrated to Shade 15 (Medium Golden Amber). "
                "Earthy olive greens, rich burgundy, rust, and navy blue provide maximum facial harmony."
            ),
            "flattering_colors": palette_info["best_colors"][:6],
            "washout_colors": palette_info["avoid_colors"][:4],
            "neutrals": palette_info["neutrals"][:4],
            "advice": palette_info["description"],
        }


# ─────────────────────────────────────────────
# PALETTE COMPATIBILITY & BADGES
# ─────────────────────────────────────────────

def get_garment_palette_badge(color: str, palette_key: str) -> Dict[str, str]:
    """
    Returns badge label, pill CSS color, and editorial note for a garment color.
    Accepts tier ID, shade ID, or legacy season string.
    """
    palette = resolve_palette(palette_key)
    c = color.strip().title()

    best_normalized = [b.lower() for b in palette.get("best_colors", [])]
    warmth_normalized = [w.lower() for w in palette.get("warmth_boosters", [])]
    neutral_normalized = [n.lower() for n in palette.get("neutrals", [])]

    c_low = c.lower()

    if any(k in c_low for k in warmth_normalized):
        return {
            "badge": "ADD WARMTH",
            "bg": "#EFE0DA",
            "color": "#8C3B1E",
            "border": "#D8B4A6",
            "text": "Adds vibrant warmth that illuminates your natural undertones.",
        }
    elif any(k in c_low for k in best_normalized):
        return {
            "badge": "BEST MATCH",
            "bg": "#E8EFE8",
            "color": "#2D5A27",
            "border": "#B9D7B5",
            "text": "A textbook harmonizer for your complexion palette.",
        }
    elif any(k in c_low for k in neutral_normalized):
        return {
            "badge": "STAPLE",
            "bg": "#F0EDE8",
            "color": "#4A453E",
            "border": "#D5CFC7",
            "text": "Versatile foundational neutral.",
        }
    else:
        return {
            "badge": "OUTSIDE PALETTE",
            "bg": "#F5F3EF",
            "color": "#766F66",
            "border": "#E0DCD6",
            "text": "Wear balanced with your best neutral accessories or layers.",
        }


def score_skin_tone_harmony(garment_colors: list, palette_key: str) -> Tuple[float, str]:
    """
    Calculate skin tone harmony score (0-100) for a list of garment colors.
    """
    if not garment_colors:
        return 75.0, "Neutral palette compatibility."

    palette = resolve_palette(palette_key)
    best_set = {b.lower() for b in palette.get("best_colors", [])}
    warmth_set = {w.lower() for w in palette.get("warmth_boosters", [])}
    avoid_set = {a.lower() for a in palette.get("avoid_colors", [])}

    points = []
    has_warmth = False
    has_avoid = False

    for item in garment_colors:
        col = (item.get("color") if isinstance(item, dict) else str(item)).lower()
        if any(b in col for b in best_set):
            points.append(95.0)
        elif any(w in col for w in warmth_set):
            points.append(98.0)
            has_warmth = True
        elif any(a in col for a in avoid_set):
            points.append(50.0)
            has_avoid = True
        else:
            points.append(78.0)

    avg_score = float(np.mean(points)) if points else 80.0

    palette_display = palette.get("name", "complexion")
    if has_warmth and not has_avoid:
        note = f"Warm, complementary tones connect beautifully with your {palette_display} tone."
    elif has_avoid:
        note = "High contrast blend; recommended to ground with a flattering neutral layer."
    else:
        note = f"Balanced palette that harmonizes with your {palette_display} profile."

    return round(avg_score, 1), note
