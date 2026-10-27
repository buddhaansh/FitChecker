"""
body_criteria.py — Body Build, Height, and Silhouette Rules for FitChecker
==========================================================================
PURPOSE:
  Analyzes user body criteria (build shape, height, torso-to-leg proportions)
  and calculates silhouette compatibility scores for outfits.
  Ensures outfits flatter the wearer's physical structure, not just colors.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, List, Tuple
import numpy as np

# ─────────────────────────────────────────────
# BODY BUILDS & SILHOUETTE BLUEPRINTS
# ─────────────────────────────────────────────

BODY_BUILDS = {
    "athletic_v_taper": {
        "id": "athletic_v_taper",
        "name": "Athletic / V-Taper",
        "description": "Broad shoulders and chest with a narrower waist.",
        "best_fits": ["Fitted", "Regular", "Slim"],
        "avoid_fits": ["Loose / Oversized"],
        "ideal_tops": ["Polo", "Henley", "Fitted T-Shirt", "Shirt", "Jacket"],
        "ideal_bottoms": ["Straight Jeans", "Chinos", "Trousers"],
        "styling_rules": [
            "Fitted and regular tops accentuate shoulder-to-waist taper naturally.",
            "Straight-leg or slim-straight pants balance broader upper body weight.",
            "Avoid overly baggy tops that hide the taper and look boxy.",
        ],
        "flattery_note": "Accentuates upper body taper while grounding with balanced, straight-line trousers.",
    },
    "lean_slim": {
        "id": "lean_slim",
        "name": "Lean / Slim",
        "description": "Slender frame, narrower chest, and leaner limbs.",
        "best_fits": ["Regular", "Slim", "Fitted"],
        "avoid_fits": ["Skinny", "Overly Tight"],
        "ideal_tops": ["Sweater", "Hoodie", "Checked Shirt", "Jacket", "Layered Top"],
        "ideal_bottoms": ["Regular Jeans", "Chinos", "Cargo", "Trousers"],
        "styling_rules": [
            "Structured layering (jackets over tees, hoodies, sweaters) adds visual weight and presence.",
            "Horizontal textures (checked, waffle, knit, stripes) broaden the torso.",
            "Avoid ultra-skinny pants; choose slim-straight or regular cuts to maintain balanced proportions.",
        ],
        "flattery_note": "Structured layering and textural contrast add visual presence and broadness.",
    },
    "broad_inverted_triangle": {
        "id": "broad_inverted_triangle",
        "name": "Broad / Inverted Triangle",
        "description": "Heavy/broad upper torso and shoulders with leaner lower body.",
        "best_fits": ["Regular", "Slim"],
        "avoid_fits": ["Overly Tight Tops", "Heavy Shoulder Padding"],
        "ideal_tops": ["V-Neck", "Open Collar Shirt", "Polo", "Soft Unstructured Jacket"],
        "ideal_bottoms": ["Straight Jeans", "Chinos", "Relaxed Trousers"],
        "styling_rules": [
            "V-necks and unbuttoned shirts draw the eye vertically, softening upper-body heaviness.",
            "Straight and relaxed trousers add volume below to balance broad shoulders.",
            "Unstructured, soft-shoulder jackets work better than heavily padded blazers.",
        ],
        "flattery_note": "Softens upper-body heaviness with vertical lines and balances proportions with straight trousers.",
    },
    "husky_oval": {
        "id": "husky_oval",
        "name": "Husky / Oval",
        "description": "Broader midsection with softer torso contours.",
        "best_fits": ["Regular", "Loose / Oversized"],
        "avoid_fits": ["Fitted", "Skinny", "Clingy"],
        "ideal_tops": ["Dark Shirt", "Open Overshirt", "Dark Hoodie", "Jacket", "Sweatshirt"],
        "ideal_bottoms": ["Straight Jeans", "Dark Trousers", "Chinos"],
        "styling_rules": [
            "Open layers (unbuttoned shirts, lightweight jackets) create slimming vertical columns.",
            "Monochromatic or low-contrast pairings (dark top + dark bottom) elongate the torso.",
            "Mid-to-high rise pants sit comfortably above the waist for cleaner drape.",
            "Avoid thin clingy fabrics; choose medium-weight cotton and twill.",
        ],
        "flattery_note": "Vertical column layering and structured fabrics create a streamlined, slimming silhouette.",
    },
    "regular_balanced": {
        "id": "regular_balanced",
        "name": "Regular / Balanced",
        "description": "Evenly proportioned torso and legs with standard width.",
        "best_fits": ["Regular", "Slim", "Fitted"],
        "avoid_fits": [],
        "ideal_tops": ["T-Shirt", "Shirt", "Polo", "Sweater", "Jacket"],
        "ideal_bottoms": ["Jeans", "Chinos", "Trousers", "Shorts"],
        "styling_rules": [
            "Classic proportions work effortlessly across tailored and casual looks.",
            "Maintain the 1/3 to 2/3 golden ratio: tuck tops or wear jackets that hit the hip line.",
            "Versatile canvas for both tailored and relaxed silhouettes.",
        ],
        "flattery_note": "Harmonious natural proportions with clean horizontal waist break.",
    },
}

HEIGHT_PROFILES = {
    "compact": {
        "label": "Compact / Under 5'8\" (< 172 cm)",
        "rules": [
            "Keep tops untucked hitting no lower than mid-fly to avoid shortening legs.",
            "Monochromatic or tonal colors create an unbroken vertical line.",
            "Tapered pants and low-profile shoes make legs look longer.",
        ],
    },
    "average": {
        "label": "Average / 5'8\" - 6'0\" (172 - 183 cm)",
        "rules": [
            "Balanced proportions that support standard jacket lengths and cuff breaks.",
            "Tuck or untuck tops comfortably without disrupting height balance.",
        ],
    },
    "tall": {
        "label": "Tall / Over 6'0\" (> 183 cm)",
        "rules": [
            "Contrast between tops and bottoms breaks up excessive vertical length.",
            "Can pull off longer coats, horizontal stripes, and cuff rolls with ease.",
        ],
    },
}


# ─────────────────────────────────────────────
# BODY COMPATIBILITY SCORING ENGINE
# ─────────────────────────────────────────────

def score_body_silhouette_compatibility(
    items: List[Dict[str, Any]],
    build_id: str = "athletic_v_taper",
    height_profile: str = "average",
) -> Tuple[float, str, List[str]]:
    """
    Score how well the garments fit and flatter the user's specific body criteria.
    Returns (score 0-100, flattery_rationale, styling_tips).
    """
    if not items:
        return 75.0, "Standard silhouette compatibility.", []

    build_info = BODY_BUILDS.get(build_id, BODY_BUILDS["regular_balanced"])
    best_fits = [f.lower() for f in build_info["best_fits"]]
    avoid_fits = [f.lower() for f in build_info["avoid_fits"]]

    points = []
    has_avoid = False
    has_ideal = False

    for item in items:
        fit = str(item.get("fit", "Regular")).lower()
        cat = str(item.get("category", "")).lower()

        # Fit match check
        if any(bf in fit for bf in best_fits):
            points.append(94.0)
            has_ideal = True
        elif any(af in fit for af in avoid_fits):
            points.append(55.0)
            has_avoid = True
        else:
            points.append(80.0)

        # Silhouette synergy check (tops & bottoms)
        if build_id == "lean_slim":
            # Outerwear or layering provides major bonus for lean frames
            if cat in ["jacket", "blazer", "hoodie", "sweater", "windcheater"]:
                points.append(98.0)
        elif build_id == "husky_oval":
            # Layering pieces that open vertically give bonus
            if cat in ["jacket", "windcheater", "shirt"]:
                points.append(95.0)

    avg_score = float(np.mean(points)) if points else 80.0

    # Build actionable explanation
    if has_ideal and not has_avoid:
        note = f"Cuts and proportions perfectly complement his {build_info['name']} physique. {build_info['flattery_note']}"
    elif has_avoid:
        note = f"Comfortable wear, though adjusting to a {build_info['best_fits'][0]} fit would sharpen his {build_info['name']} silhouette."
    else:
        note = f"Balanced silhouette that cleanly frames his {build_info['name']} proportions."

    return round(avg_score, 1), note, build_info["styling_rules"]
