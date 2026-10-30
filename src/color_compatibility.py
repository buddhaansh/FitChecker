"""
color_compatibility.py — FitChecker Color Scoring
==================================================
PURPOSE:
  Determine how well two or more garment colors go together.
  Returns a score from 0 to 100.

ALGORITHM:
  Two complementary approaches are combined:

  1. COMPATIBILITY TABLE  (primary)
     A human-curated lookup table of known good and bad color pairings,
     based on common fashion color theory.  Easy to inspect and edit.

  2. COLOR THEORY HEURISTIC  (fallback)
     Computes a rough compatibility score using HSV (Hue, Saturation,
     Value) color space.  Classic rules:
       • Complementary  hue difference ~180° → high score
       • Analogous      hue difference < 30° → medium-high score
       • Triadic        hue difference ~120° → medium score
       • Neutral colors (low saturation)     → always compatible

IMPORTANT NOTE:
  Color compatibility is personal and context-dependent.
  The scores below are reasonable defaults, NOT objective truths.
  Users can override results via the preferences page.

BEGINNER NOTE:
  HSV = Hue (which color), Saturation (how vivid), Value (how bright).
  Converting RGB to HSV lets us compare colors mathematically.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import colorsys
from typing import Optional


# ─────────────────────────────────────────────
# NAMED COLOR → RGB MAPPING
# ─────────────────────────────────────────────
# Maps common color names (lower-case) to their approximate RGB tuple.
COLOR_RGB: dict[str, tuple] = {
    "white":       (255, 255, 255),
    "black":       (0,   0,   0),
    "grey":        (128, 128, 128),
    "gray":        (128, 128, 128),
    "light grey":  (211, 211, 211),
    "dark grey":   (64,  64,  64),
    "navy blue":   (31,  43,  122),
    "blue":        (0,   102, 204),
    "light blue":  (173, 216, 230),
    "sky blue":    (135, 206, 235),
    "dark blue":   (0,   0,   139),
    "red":         (220, 50,  50),
    "maroon":      (128, 0,   0),
    "pink":        (255, 182, 193),
    "hot pink":    (255, 105, 180),
    "orange":      (255, 140, 0),
    "yellow":      (255, 215, 0),
    "olive green": (107, 124, 71),
    "green":       (50,  150, 50),
    "dark green":  (0,   100, 0),
    "mint green":  (152, 255, 152),
    "brown":       (139, 69,  19),
    "tan":         (210, 180, 140),
    "beige":       (245, 245, 220),
    "khaki":       (195, 163, 67),
    "cream":       (255, 253, 208),
    "off white":   (250, 250, 240),
    "purple":      (128, 0,   128),
    "lavender":    (230, 190, 255),
    "teal":        (0,   128, 128),
    "cyan":        (0,   188, 212),
    "dark brown":  (101, 50,  20),
    "light pink":  (255, 218, 224),
    "rust":        (183, 65,  14),
    "mustard":     (255, 191, 0),
    "charcoal":    (54,  69,  79),
}

# Canonical color set (lower-case) — offered in the UI dropdown
AVAILABLE_COLORS = sorted(COLOR_RGB.keys())


# ─────────────────────────────────────────────
# CURATED COMPATIBILITY TABLE
# Key: frozenset of two color names → score 0-100
# ─────────────────────────────────────────────
_PAIR_TABLE: dict[frozenset, int] = {
    # Neutrals always go with almost everything
    frozenset({"white",       "black"}):       90,
    frozenset({"white",       "navy blue"}):   90,
    frozenset({"white",       "grey"}):        88,
    frozenset({"white",       "beige"}):       85,
    frozenset({"white",       "khaki"}):       85,
    frozenset({"white",       "blue"}):        85,
    frozenset({"white",       "light blue"}):  88,
    frozenset({"white",       "olive green"}): 80,
    frozenset({"white",       "maroon"}):      82,
    frozenset({"black",       "grey"}):        90,
    frozenset({"black",       "white"}):       90,
    frozenset({"black",       "navy blue"}):   60,  # Too similar; avoid
    frozenset({"black",       "khaki"}):       80,
    frozenset({"black",       "beige"}):       82,
    frozenset({"black",       "red"}):         78,
    frozenset({"black",       "light blue"}):  80,
    frozenset({"black",       "olive green"}): 75,
    frozenset({"grey",        "navy blue"}):   88,
    frozenset({"grey",        "white"}):       88,
    frozenset({"grey",        "light blue"}):  85,
    frozenset({"grey",        "beige"}):       80,
    frozenset({"grey",        "maroon"}):      82,
    frozenset({"navy blue",   "khaki"}):       88,
    frozenset({"navy blue",   "white"}):       90,
    frozenset({"navy blue",   "beige"}):       85,
    frozenset({"navy blue",   "light blue"}):  65,  # Too close
    frozenset({"navy blue",   "grey"}):        88,
    frozenset({"light blue",  "white"}):       88,
    frozenset({"light blue",  "khaki"}):       82,
    frozenset({"light blue",  "beige"}):       80,
    frozenset({"olive green", "khaki"}):       85,
    frozenset({"olive green", "beige"}):       95,  # Earthy & Natural
    frozenset({"olive green", "black"}):       92,  # Cool & Military / Sharp & Strong
    frozenset({"olive green", "white"}):       92,  # Casual Vibes / Clean Organic
    frozenset({"olive green", "navy blue"}):   88,
    frozenset({"olive green", "brown"}):       88,  # Earthy Tonal
    frozenset({"brown",       "cream"}):       96,  # Coffee + Cream Signature
    frozenset({"brown",       "black"}):       92,  # Warm & Bold
    frozenset({"navy blue",   "cream"}):       96,  # Classic & Clean
    frozenset({"burgundy",    "beige"}):       96,  # Rich & Elegant
    frozenset({"maroon",      "cream"}):       95,  # Rich & Elegant
    frozenset({"rust",        "black"}):       94,  # Warm & Grounded
    frozenset({"rust",        "dark blue"}):   94,  # Rich & Balanced
    frozenset({"teal",        "beige"}):       94,  # Unique & Fresh
    frozenset({"sage green",  "white"}):       94,  # Fresh & Trendy
    frozenset({"charcoal",    "cream"}):       94,  # Modern & Classy
    frozenset({"light grey",  "charcoal"}):    92,  # Minimal & Modern
    frozenset({"cream",       "brown"}):       96,  # Soft & Warm
    frozenset({"khaki",       "white"}):       85,
    frozenset({"khaki",       "navy blue"}):   88,
    frozenset({"khaki",       "brown"}):       70,
    frozenset({"beige",       "white"}):       82,
    frozenset({"beige",       "brown"}):       72,
    frozenset({"maroon",      "beige"}):       80,
    frozenset({"maroon",      "khaki"}):       78,
    frozenset({"maroon",      "grey"}):        82,
    frozenset({"maroon",      "white"}):       82,
    frozenset({"brown",       "beige"}):       72,
    frozenset({"brown",       "khaki"}):       70,
    frozenset({"brown",       "white"}):       78,
    frozenset({"red",         "white"}):       78,
    frozenset({"red",         "black"}):       78,
    frozenset({"red",         "blue"}):        55,  # Risky combination
    frozenset({"blue",        "white"}):       85,
    frozenset({"purple",      "grey"}):        78,
    frozenset({"purple",      "white"}):       80,
    frozenset({"pink",        "white"}):       85,
    frozenset({"pink",        "grey"}):        80,
    frozenset({"pink",        "navy blue"}):   78,
    frozenset({"teal",        "white"}):       82,
    frozenset({"teal",        "beige"}):       80,
    frozenset({"mustard",     "navy blue"}):   82,
    frozenset({"mustard",     "white"}):       78,
    frozenset({"mustard",     "olive green"}): 70,
    frozenset({"rust",        "beige"}):       78,
    frozenset({"rust",        "white"}):       80,
    frozenset({"charcoal",    "white"}):       88,
    frozenset({"charcoal",    "beige"}):       82,
    frozenset({"charcoal",    "light blue"}):  80,
}


def _hex_to_rgb(hex_str: str) -> Optional[tuple]:
    """Convert '#RRGGBB' to (R, G, B) tuple, or None if invalid."""
    hex_str = hex_str.strip().lstrip("#")
    if len(hex_str) == 3:
        hex_str = "".join(c * 2 for c in hex_str)
    if len(hex_str) == 6:
        try:
            r = int(hex_str[0:2], 16)
            g = int(hex_str[2:4], 16)
            b = int(hex_str[4:6], 16)
            return (r, g, b)
        except ValueError:
            return None
    return None


def _rgb_to_hsv(rgb: tuple) -> tuple:
    """Convert (R, G, B) in range 0-255 to (H, S, V) in range 0-1."""
    r, g, b = rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0
    return colorsys.rgb_to_hsv(r, g, b)


def _is_neutral(rgb: tuple) -> bool:
    """
    Returns True if the color is approximately neutral (white, black, grey).
    ALGORITHM: Low saturation in HSV = neutral color.
    """
    _, s, _ = _rgb_to_hsv(rgb)
    return s < 0.15


def _hue_score(rgb1: tuple, rgb2: tuple) -> float:
    """
    Score two colors based on color-wheel distance.
    Returns 0-100.

    RULES (classical color theory):
      • Same hue (monochromatic) → 70
      • Analogous   (diff < 30°) → 75
      • Triadic     (diff ~120°) → 72
      • Complementary (diff ~180°) → 80
      • Neutral     (low saturation) → 85
    """
    if _is_neutral(rgb1) or _is_neutral(rgb2):
        return 82.0   # Neutrals pair well with almost anything

    h1, s1, v1 = _rgb_to_hsv(rgb1)
    h2, s2, v2 = _rgb_to_hsv(rgb2)

    # Both desaturated = neutral pair
    if s1 < 0.25 and s2 < 0.25:
        return 80.0

    # Hue difference in degrees (0–360)
    diff = abs(h1 - h2) * 360
    if diff > 180:
        diff = 360 - diff

    if diff < 20:
        return 70.0   # Too close — monochromatic, a bit boring but fine
    elif diff < 45:
        return 75.0   # Analogous
    elif 100 <= diff <= 140:
        return 72.0   # Triadic-ish
    elif 150 <= diff <= 210:
        return 80.0   # Complementary — classic contrast
    else:
        return 65.0   # Awkward distance


def _get_rgb_for_name(color_name: str) -> Optional[tuple]:
    """Look up RGB for a colour name (case-insensitive)."""
    return COLOR_RGB.get(color_name.lower().strip())


def pair_score(color1: str, color2: str,
               hex1: str = "", hex2: str = "") -> float:
    """
    Return a 0-100 compatibility score for two garment colors.

    Priority:
      1. Check curated lookup table (most accurate for known pairs).
      2. Try converting hex codes to RGB and use heuristic.
      3. Try named-color RGB lookup + heuristic.
      4. Return 60.0 as a safe neutral default.
    """
    # Normalize names
    c1, c2 = color1.lower().strip(), color2.lower().strip()

    # Same color → 100 only if it's a neutral; otherwise monochromatic risk
    if c1 == c2:
        rgb = _get_rgb_for_name(c1)
        if rgb and _is_neutral(rgb):
            return 85.0
        return 65.0   # Same vivid color = monochromatic (ok, not great)

    # 1. Table lookup
    key = frozenset({c1, c2})
    if key in _PAIR_TABLE:
        return float(_PAIR_TABLE[key])

    # 2. Hex-based heuristic
    rgb1 = _hex_to_rgb(hex1) if hex1 else None
    rgb2 = _hex_to_rgb(hex2) if hex2 else None
    if rgb1 and rgb2:
        return _hue_score(rgb1, rgb2)

    # 3. Name-based heuristic
    rgb1 = rgb1 or _get_rgb_for_name(c1)
    rgb2 = rgb2 or _get_rgb_for_name(c2)
    if rgb1 and rgb2:
        return _hue_score(rgb1, rgb2)

    # 4. Default — unknown pair, assume average compatibility
    return 60.0


def outfit_color_score(garment_colors: list[dict]) -> float:
    """
    Compute the overall color compatibility for an outfit (list of garments).

    Each garment dict should have keys: 'color' (str) and optionally 'color_hex'.

    ALGORITHM:
      Compute pair_score for every unique pair of garments,
      then return the average of all pair scores.
      If fewer than 2 garments are provided, return 100.0.
    """
    if len(garment_colors) < 2:
        return 100.0

    scores = []
    for i in range(len(garment_colors)):
        for j in range(i + 1, len(garment_colors)):
            g1, g2 = garment_colors[i], garment_colors[j]
            s = pair_score(
                g1.get("color", ""),
                g2.get("color", ""),
                g1.get("color_hex", ""),
                g2.get("color_hex", ""),
            )
            scores.append(s)

    return round(sum(scores) / len(scores), 1) if scores else 60.0


def describe_color_interplay(color1: str, color2: str, cat1: str = "", cat2: str = "") -> str:
    """
    Generate an insightful, high-fashion editorial description of the aesthetic interplay
    between two colors and their respective garment pieces.
    """
    c1 = (color1 or "").lower().strip()
    c2 = (color2 or "").lower().strip()
    t1 = cat1.strip() if cat1 else "upper"
    t2 = cat2.strip() if cat2 else "lower"

    pair = frozenset({c1, c2})
    sc = pair_score(c1, c2)

    # Specific signature combinations
    if pair in [frozenset({"white", "black"}), frozenset({"white", "charcoal"})]:
        return f"High-Contrast Monochrome ({int(sc)}% Match): Crisp {c1.title()} offset by deep {c2.title()} creates timeless, razor-sharp tailored definition."
    elif pair in [frozenset({"olive green", "beige"}), frozenset({"olive green", "cream"}), frozenset({"olive green", "khaki"})]:
        return f"Earthy Quiet Luxury ({int(sc)}% Match): Muted {c1.title()} paired with organic {c2.title()} delivers an understated Scandinavian aesthetic."
    elif pair in [frozenset({"brown", "cream"}), frozenset({"tan", "cream"}), frozenset({"brown", "beige"})]:
        return f"Coffee & Cream Tonal Warmth ({int(sc)}% Match): Rich {c1.title()} anchored by soft {c2.title()} produces welcoming sartorial depth."
    elif pair in [frozenset({"navy blue", "white"}), frozenset({"navy blue", "cream"}), frozenset({"navy blue", "khaki"})]:
        return f"Classic Preppy Harmony ({int(sc)}% Match): Deep {c1.title()} structured against clean {c2.title()} evokes effortless coastal refinement."
    elif pair in [frozenset({"black", "grey"}), frozenset({"charcoal", "light grey"}), frozenset({"black", "charcoal"})]:
        return f"Sleek Monochromatic Gradient ({int(sc)}% Match): Seamless urban transition between {c1.title()} and {c2.title()} with minimalist modern drape."
    elif pair in [frozenset({"maroon", "cream"}), frozenset({"burgundy", "beige"}), frozenset({"maroon", "white"})]:
        return f"Rich Regal Contrast ({int(sc)}% Match): Luxurious {c1.title()} highlighted by crisp neutral {c2.title()} for an elevated presence."
    elif pair in [frozenset({"black", "olive green"}), frozenset({"charcoal", "olive green"})]:
        return f"Tactical Modernism ({int(sc)}% Match): Strong {c1.title()} paired with utilitarian {c2.title()} offers an assertive, masculine silhouette."
    elif pair in [frozenset({"rust", "black"}), frozenset({"rust", "dark blue"})]:
        return f"Warm Autumnal Accent ({int(sc)}% Match): Vibrant {c1.title()} grounded by deep {c2.title()} for sophisticated seasonal warmth."
    elif sc >= 85:
        return f"Refined Color Harmony ({int(sc)}% Match): {c1.title()} and {c2.title()} naturally harmonize, balancing visual weight between {t1} and {t2}."
    elif sc >= 70:
        return f"Balanced Contrast ({int(sc)}% Match): {c1.title()} against {c2.title()} provides clean visual separation and modern everyday ease."
    else:
        return f"Dynamic Contrast ({int(sc)}% Match): Bold interplay between {c1.title()} and {c2.title()}; ground with clean neutral footwear."

