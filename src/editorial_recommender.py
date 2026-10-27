"""
editorial_recommender.py — Editorial Curation & Fashion Styling Engine
======================================================================
PURPOSE:
  Generates the 3-card curated editorial outfits seen in the reference pictures:
    - Card 1: "BEST MATCH"
    - Card 2: "MORE RELAXED"
    - Card 3: "MORE POLISHED"
  Generates garment pairing rankings ("Pair With") and packing capsules.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from config.settings import CATEGORY_GROUP
from src.outfit_generator import generate_outfits, format_outfit_label
from src.recommender import score_outfit
from src.skin_tone_analyzer import (
    score_skin_tone_harmony,
    get_garment_palette_badge,
    SEASON_PALETTES,
    COMPLEXION_PALETTES,
    resolve_palette,
)
from src.color_compatibility import pair_score
from src.body_criteria import score_body_silhouette_compatibility, BODY_BUILDS


def _generate_partial_outfits(wardrobe_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Assemble top + bottom combinations when footwear is not yet in the wardrobe."""
    if wardrobe_df.empty:
        return []
    tops = wardrobe_df[wardrobe_df["category"].isin(CATEGORY_GROUP.get("tops", []))]
    bottoms = wardrobe_df[wardrobe_df["category"].isin(CATEGORY_GROUP.get("bottoms", []))]
    if tops.empty or bottoms.empty:
        return []
    combos = []
    for _, t in tops.iterrows():
        for _, b in bottoms.iterrows():
            combos.append({
                "template": "Top + Bottom",
                "item_ids": [t["item_id"], b["item_id"]],
                "items": [t.to_dict(), b.to_dict()],
                "groups": ["tops", "bottoms"],
            })
    return combos


def generate_editorial_recommendations(
    wardrobe_df: pd.DataFrame,
    plan_info: Dict[str, Any],
    profile: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Generate 3 distinct editorial recommendations:
      1. BEST MATCH: Highest overall score balancing mood, skin tone & occasion
      2. MORE RELAXED: Easy silhouette, laid-back comfort
      3. MORE POLISHED: Crisp tailoring, elevated silhouette
    """
    if wardrobe_df.empty:
        return []

    occasion = plan_info.get("occasion", "Casual Outing")
    weather  = plan_info.get("weather", "Any")
    target_formality = plan_info.get("target_formality", 2)
    season   = profile.get("season", "Autumn")
    plan_title = plan_info.get("plan_title", "Everyday Wear")
    gender = profile.get("gender", "Girl")

    # Generate all candidate combinations
    candidates = generate_outfits(
        wardrobe_df,
        occasion=occasion,
        include_accessories=True,
    )

    if not candidates:
        # Fallback with minimal filters
        candidates = generate_outfits(
            wardrobe_df,
            occasion="Daily College Wear",
            include_accessories=False,
        )

    if not candidates:
        # Fallback when wardrobe does not yet contain footwear
        candidates = _generate_partial_outfits(wardrobe_df)

    if not candidates:
        return []

    build_id = profile.get("body_build", "athletic_v_taper")
    height_profile = profile.get("height_profile", "average")

    scored_list = []
    for cand in candidates:
        items = cand["items"]
        # Baseline score (0-100)
        scored_cand = score_outfit(cand, occasion=occasion, current_weather=weather)
        base_score = float(scored_cand.get("total_score", 75.0))

        # 1. Face & Skin Tone Compatibility Score
        skin_score, skin_note = score_skin_tone_harmony(items, season)

        # 2. Body Silhouette & Fit Compatibility Score
        body_score, body_note, body_rules = score_body_silhouette_compatibility(items, build_id, height_profile)

        # Formality analysis
        formalities = [int(it.get("formality", 2)) for it in items if "formality" in it]
        mean_formality = float(np.mean(formalities)) if formalities else 2.0

        # Formality alignment to plan
        formality_penalty = abs(mean_formality - target_formality) * 8.0

        # Combined composite score: 35% Face Harmony, 35% Body Silhouette, 30% Base Occasion
        total_score = (base_score * 0.30) + (skin_score * 0.35) + (body_score * 0.35) - formality_penalty
        total_score = max(58.0, min(97.0, total_score))

        cand["composite_score"] = round(total_score, 1)
        cand["mean_formality"]  = mean_formality
        cand["skin_note"]       = skin_note
        cand["skin_score"]      = skin_score
        cand["body_score"]      = body_score
        cand["body_note"]       = body_note
        cand["base_score"]      = base_score
        scored_list.append(cand)

    # Sort descending by composite score
    scored_list.sort(key=lambda x: x["composite_score"], reverse=True)

    results = []

    # ── 1. BEST MATCH ──
    best_cand = scored_list[0]
    results.append(_package_editorial_card(
        card_type="BEST MATCH",
        match_pct=int(np.clip(best_cand["composite_score"], 86, 94)),
        outfit=best_cand,
        plan_info=plan_info,
        profile=profile,
        flair="Effortlessly balanced proportion and color harmony.",
    ))

    # ── 2. MORE RELAXED ──
    # Pick candidate with lower mean formality or casual silhouette
    relaxed_candidates = [
        c for c in scored_list[1:]
        if c["mean_formality"] <= best_cand["mean_formality"]
    ]
    if not relaxed_candidates:
        relaxed_candidates = scored_list[1:2] if len(scored_list) > 1 else scored_list[:1]

    relaxed_cand = relaxed_candidates[0] if relaxed_candidates else best_cand
    results.append(_package_editorial_card(
        card_type="MORE RELAXED",
        match_pct=int(np.clip(relaxed_cand["composite_score"] - 2, 83, 91)),
        outfit=relaxed_cand,
        plan_info=plan_info,
        profile=profile,
        flair="Relaxed silhouette prioritizing movement, comfort and softness.",
    ))

    # ── 3. MORE POLISHED ──
    # Pick candidate with equal or higher formality or structured tailoring
    polished_candidates = [
        c for c in scored_list[1:]
        if c.get("mean_formality", 3) >= target_formality and c.get("item_ids") != relaxed_cand.get("item_ids")
    ]
    if not polished_candidates:
        # Fallback to any remaining top candidate
        remaining = [c for c in scored_list if c not in [best_cand, relaxed_cand]]
        polished_candidates = remaining if remaining else scored_list[:1]

    polished_cand = polished_candidates[0] if polished_candidates else best_cand
    results.append(_package_editorial_card(
        card_type="MORE POLISHED",
        match_pct=int(np.clip(polished_cand["composite_score"] - 1, 85, 92)),
        outfit=polished_cand,
        plan_info=plan_info,
        profile=profile,
        flair="Structured lines with crisp tailoring for an elevated presence.",
    ))

    return results


def _package_editorial_card(
    card_type: str,
    match_pct: int,
    outfit: Dict[str, Any],
    plan_info: Dict[str, Any],
    profile: Dict[str, Any],
    flair: str,
) -> Dict[str, Any]:
    """Helper to structure an editorial outfit card."""
    items = outfit["items"]
    season = profile.get("season", "Autumn")
    plan_title = plan_info.get("plan_title", "your plans")

    # Item label combination: e.g. "Oatmeal pointelle crop tee + Levi's medium-blue mom jeans + Mushroom VIVAIA Mary Janes"
    names = []
    for it in items:
        color = str(it.get("color", "") or "").strip()
        cat   = str(it.get("category", "") or "").strip()
        brand = str(it.get("brand", "") or "").strip()
        subcat = str(it.get("subcategory", "") or "").strip()

        label_parts = [p for p in [brand, color, subcat, cat] if p and p != "nan"]
        names.append(" ".join(label_parts) if label_parts else "Garment")

    title_str = " + ".join(names)

    # Generate editorial styling critique paragraph
    critique = _generate_editorial_critique(items, card_type, plan_title, season, profile, outfit)

    # Attach palette badges for each item
    enhanced_items = []
    for it in items:
        it_copy = dict(it)
        it_copy["palette_badge"] = get_garment_palette_badge(it.get("color", ""), season)
        enhanced_items.append(it_copy)

    return {
        "card_type": card_type,
        "match_percentage": match_pct,
        "title": title_str,
        "critique": critique,
        "face_score": int(outfit.get("skin_score", 90)),
        "body_score": int(outfit.get("body_score", 90)),
        "face_note": outfit.get("skin_note", ""),
        "body_note": outfit.get("body_note", ""),
        "items": enhanced_items,
        "raw_outfit": outfit,
    }


def _generate_editorial_critique(
    items: List[Dict[str, Any]],
    card_type: str,
    plan_title: str,
    season: str,
    profile: Dict[str, Any],
    outfit: Dict[str, Any] = None,
) -> str:
    """Generate high-fashion editorial critique paragraph reflecting both Face & Body criteria."""
    palette = resolve_palette(season)
    complexion_label = profile.get("skin_tone_label", palette.get("name", "complexion"))
    colors = [it.get("color", "neutral") for it in items]
    unique_colors = list(dict.fromkeys(colors))
    gender = profile.get("gender", "Boy")
    pronoun_possessive = "his" if gender in ["Boy", "Him", "Male"] else "her" if gender in ["Girl", "Her", "Female"] else "their"
    pronoun_object = "him" if gender in ["Boy", "Him", "Male"] else "her" if gender in ["Girl", "Her", "Female"] else "them"

    build_id = profile.get("body_build", "athletic_v_taper")
    build_info = BODY_BUILDS.get(build_id, BODY_BUILDS["athletic_v_taper"])

    color_lead = f"{' and '.join(unique_colors[:2])} complementary tones"
    if len(unique_colors) >= 3:
        color_lead = f"Palette of {unique_colors[0]}, {unique_colors[1]}, and {unique_colors[2]}"

    if card_type == "BEST MATCH":
        critique = (
            f"**Face & Complexion:** {color_lead} naturally flatter {pronoun_possessive} {complexion_label} without washout. "
            f"**Body & Silhouette:** {build_info['flattery_note']} "
            f"Exudes an effortless, tailored presence for {plan_title.lower()}."
        )
    elif card_type == "MORE RELAXED":
        critique = (
            f"**Face & Complexion:** Softer, tonal blend pairing {items[0].get('color', '')} with {items[1].get('color', '') if len(items)>1 else 'neutrals'}. "
            f"**Body & Silhouette:** Relaxed, easy lines prioritizing mobility and breathable comfort on {pronoun_possessive} {build_info['name'].lower()} frame for {plan_title.lower()}."
        )
    else:  # MORE POLISHED
        critique = (
            f"**Face & Complexion:** High-contrast crisp tones that make {pronoun_possessive} facial contours stand out with clarity. "
            f"**Body & Silhouette:** Structured upper layering and clean lower drape that frame {pronoun_possessive} physique with commanding polish for {plan_title.lower()}."
        )

    return critique


# ─────────────────────────────────────────────
# PIECE PAIRING ENGINE ("PAIR WITH")
# ─────────────────────────────────────────────

def get_pairings_for_garment(
    garment: Dict[str, Any],
    wardrobe_df: pd.DataFrame,
    style_filter: str = "ALL",
    season: str = "Autumn",
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    Find pieces in the wardrobe that pair best with `garment`.
    Matches the 'Pair with' drawer seen in Screenshot 3.
    """
    if wardrobe_df.empty:
        return []

    target_id = garment.get("item_id")
    target_group = _get_item_group(garment.get("category", ""))
    target_color = garment.get("color", "")
    target_formality = int(garment.get("formality", 2))

    # We want garments from complementary groups (e.g., if target is dress -> shoes or outerwear;
    # if target is top -> bottoms or shoes)
    results = []

    for _, row in wardrobe_df.iterrows():
        if row.get("item_id") == target_id:
            continue

        item_cat = row.get("category", "")
        item_group = _get_item_group(item_cat)

        # Do not pair top with top unless outer
        if target_group == "tops" and item_group == "tops":
            continue
        if target_group == "bottoms" and item_group == "bottoms":
            continue
        if target_group == "one_piece" and item_group in ["tops", "bottoms"]:
            continue

        # Filter by style/occasion if requested
        item_styles = str(row.get("style_tags", "")).lower()
        if style_filter != "ALL":
            sf = style_filter.lower()
            if sf not in item_styles and sf not in str(row.get("occasion", "")).lower():
                continue

        # Score compatibility
        col_score = pair_score(target_color, row.get("color", ""))
        form_diff = abs(target_formality - int(row.get("formality", 2)))
        form_score = max(50.0, 100.0 - (form_diff * 15.0))

        match_pct = int(np.clip((col_score * 0.65) + (form_score * 0.35), 72, 96))

        # Generate pairing explanation
        explanation = _generate_pairing_note(garment, row.to_dict(), match_pct, season)

        results.append({
            "item": row.to_dict(),
            "match_percentage": match_pct,
            "explanation": explanation,
            "palette_badge": get_garment_palette_badge(row.get("color", ""), season),
        })

    # Sort descending by match percentage
    results.sort(key=lambda x: x["match_percentage"], reverse=True)
    return results[:limit]


def _get_item_group(category: str) -> str:
    for group, cats in CATEGORY_GROUP.items():
        if category in cats:
            return group
    return "other"


def _generate_pairing_note(target: dict, companion: dict, match_pct: int, season: str) -> str:
    t_col = target.get("color", "").lower()
    c_col = companion.get("color", "").lower()
    c_cat = companion.get("category", "")

    if "shoe" in c_cat.lower() or "sneaker" in c_cat.lower() or "boot" in c_cat.lower() or "sandal" in c_cat.lower():
        return f"{c_col.title()} grounds the {t_col} silhouette naturally; versatile and easy for casual and evening plans."
    elif "jean" in c_cat.lower() or "trouser" in c_cat.lower() or "chino" in c_cat.lower():
        return f"Classic {c_col} proportion balances the {target.get('category', 'piece')} cleanly without clashing."
    else:
        return f"Connects seamlessly with the {t_col} undertones, adding depth to your complexion palette."


# ─────────────────────────────────────────────
# PACKING CAPSULE PLANNER ("PACKING MODE")
# ─────────────────────────────────────────────

def generate_packing_capsule(
    destination: str,
    days: int,
    wardrobe_df: pd.DataFrame,
    season: str = "Autumn",
) -> Dict[str, Any]:
    """
    Build a minimal, highly-cohesive travel capsule that mixes and matches.
    Matches Screenshot 5.
    """
    if wardrobe_df.empty:
        return {"destination": destination, "days": days, "capsule_items": [], "itinerary": [], "message": "Wardrobe is empty."}

    # Recommended capsule size:
    # 3-4 Tops, 2 Bottoms, 1 Layer/Outer, 2 Shoes
    capsule_items = []

    tops = wardrobe_df[wardrobe_df["category"].isin(CATEGORY_GROUP["tops"])].head(3)
    bottoms = wardrobe_df[wardrobe_df["category"].isin(CATEGORY_GROUP["bottoms"])].head(2)
    outer = wardrobe_df[wardrobe_df["category"].isin(CATEGORY_GROUP["outer"])].head(1)
    shoes = wardrobe_df[wardrobe_df["category"].isin(CATEGORY_GROUP["footwear"])].head(2)

    selected_df = pd.concat([tops, bottoms, outer, shoes]).drop_duplicates(subset=["item_id"])

    # Build day-by-day combinations
    top_list = tops.to_dict("records") if not tops.empty else []
    bot_list = bottoms.to_dict("records") if not bottoms.empty else []
    shoe_list = shoes.to_dict("records") if not shoes.empty else []

    itinerary = []
    for day in range(1, days + 1):
        day_top = top_list[(day - 1) % len(top_list)] if top_list else None
        day_bot = bot_list[(day - 1) % len(bot_list)] if bot_list else None
        day_shoe = shoe_list[(day - 1) % len(shoe_list)] if shoe_list else None

        itinerary.append({
            "day": day,
            "title": f"Day {day} in {destination or 'Your Trip'}",
            "top": day_top,
            "bottom": day_bot,
            "shoe": day_shoe,
            "note": f"Weather-ready mix: {day_top.get('color', '')} {day_top.get('category', '')} + {day_bot.get('color', '')} {day_bot.get('category', '')}" if day_top and day_bot else "Versatile combination",
        })

    return {
        "destination": destination or "City Getaway",
        "days": days,
        "capsule_items": selected_df.to_dict("records"),
        "itinerary": itinerary,
    }


# ─────────────────────────────────────────────
# EDITORIAL LOOKBOOK DROPS & SHOWCASES (KHY & MADWITCH)
# ─────────────────────────────────────────────

LOOKBOOK_DROPS = [
    {
        "id": "drop_01",
        "name": "Drop 01 · Cream & Coffee Minimal",
        "tagline": "Tonal espresso knits & rich earth tones balanced against pleated cream / ivory bottoms.",
        "badge": "TONAL MINIMALIST",
        "aesthetic": "Quiet luxury espresso & ivory interplay inspired by European streetstyle.",
        "preferred_top_colors": ["brown", "coffee", "chocolate", "mocha", "taupe", "maroon", "rust"],
        "preferred_bot_colors": ["cream", "beige", "white", "khaki"],
        "preferred_outer_colors": ["brown", "camel", "chocolate", "khaki"],
        "preferred_shoe_colors": ["brown", "black", "white"],
    },
    {
        "id": "drop_02",
        "name": "Drop 02 · Korean & Japanese Baggy Street",
        "tagline": "Boxy dropped-shoulder silhouettes, utility overshirts, and relaxed puddle cargos.",
        "badge": "STREETWEAR DROP",
        "aesthetic": "Relaxed skater proportions & high-contrast street layers.",
        "preferred_top_colors": ["black", "navy blue", "grey", "olive green", "white"],
        "preferred_bot_colors": ["black", "charcoal", "olive green", "light blue", "dark blue", "grey"],
        "preferred_outer_colors": ["black", "olive green", "grey"],
        "preferred_shoe_colors": ["white", "black"],
    },
    {
        "id": "drop_03",
        "name": "Drop 03 · Old Money Riviera & Ivy Preppy",
        "tagline": "Unbuttoned linen collars, knit polos, collegiate V-necks, and tailored pleats.",
        "badge": "OLD MONEY #1",
        "aesthetic": "Classic European tailoring & collegiate Ivy League poise.",
        "preferred_top_colors": ["olive green", "navy blue", "white", "light blue", "cream", "maroon"],
        "preferred_bot_colors": ["beige", "white", "cream", "khaki", "navy blue"],
        "preferred_outer_colors": ["navy blue", "camel", "olive green"],
        "preferred_shoe_colors": ["brown", "black", "white"],
    },
    {
        "id": "drop_04",
        "name": "Drop 04 · 90s Distressed Leather & Denim",
        "tagline": "Vintage leather outerwear, ribbed white tanks, stacked raw denim, and rugged boots.",
        "badge": "GRUNGE LEATHER",
        "aesthetic": "Rugged moto outerwear grounded with crisp inner layers.",
        "preferred_top_colors": ["white", "grey", "black"],
        "preferred_bot_colors": ["dark blue", "black", "light blue", "charcoal"],
        "preferred_outer_colors": ["brown", "black", "olive green"],
        "preferred_shoe_colors": ["black", "brown", "white"],
    },
    {
        "id": "drop_05",
        "name": "Drop 05 · Earth-Tone Utilitarian Glow",
        "tagline": "Rich olive, rust, camel, mocha, and chocolate brown multi-layer tonal interplay.",
        "badge": "EARTH GLOW",
        "aesthetic": "Rich spice & foliage tones calibrated for golden wheatish radiance.",
        "preferred_top_colors": ["olive green", "rust", "mustard", "orange", "maroon"],
        "preferred_bot_colors": ["beige", "black", "khaki", "brown"],
        "preferred_outer_colors": ["olive green", "khaki", "brown"],
        "preferred_shoe_colors": ["brown", "black", "white"],
    },
]


def generate_lookbook_showcase(
    wardrobe_df: pd.DataFrame,
    profile: Dict[str, Any],
    drop_id: Optional[str] = "drop_01",
) -> Dict[str, Any]:
    """
    Generates high-fashion lookbook presentations matching MadWitch and KHY formats.
    Returns:
      - active_drop: drop metadata
      - hero_look: premier full outfit
      - variations: list of alternative looks in this drop
    """
    drop = next((d for d in LOOKBOOK_DROPS if d["id"] == drop_id), LOOKBOOK_DROPS[0])
    if wardrobe_df.empty:
        return {"active_drop": drop, "hero_look": None, "variations": [], "error": "Wardrobe is empty."}

    season = profile.get("palette_tier", profile.get("season", "medium_golden"))
    build_id = profile.get("body_build", "athletic_v_taper")
    height_profile = profile.get("height_profile", "average")
    user_name = profile.get("name", "BUDZ")

    # Generate all candidate combinations
    candidates = generate_outfits(wardrobe_df, occasion="Daily College Wear", include_accessories=True)
    if not candidates:
        candidates = generate_outfits(wardrobe_df, occasion="Casual Outing", include_accessories=False)
    if not candidates:
        candidates = _generate_partial_outfits(wardrobe_df)
    if not candidates:
        return {"active_drop": drop, "hero_look": None, "variations": []}

    scored_looks = []
    pref_tops = [c.lower() for c in drop["preferred_top_colors"]]
    pref_bots = [c.lower() for c in drop["preferred_bot_colors"]]
    pref_outers = [c.lower() for c in drop["preferred_outer_colors"]]

    for cand in candidates:
        items = cand.get("items", [])
        top_item = next((it for it in items if it.get("category") in CATEGORY_GROUP.get("tops", [])), None)
        bot_item = next((it for it in items if it.get("category") in CATEGORY_GROUP.get("bottoms", [])), None)
        outer_item = next((it for it in items if it.get("category") in CATEGORY_GROUP.get("outer", [])), None)
        shoe_item = next((it for it in items if it.get("category") in CATEGORY_GROUP.get("footwear", [])), None)

        if not top_item or not bot_item:
            continue

        top_col = top_item.get("color", "").lower()
        bot_col = bot_item.get("color", "").lower()

        # Score alignment with this specific drop's aesthetic
        drop_affinity = 0
        if any(pt in top_col for pt in pref_tops):
            drop_affinity += 30
        if any(pb in bot_col for pb in pref_bots):
            drop_affinity += 30
        if outer_item and any(po in outer_item.get("color", "").lower() for po in pref_outers):
            drop_affinity += 20

        skin_score, skin_note = score_skin_tone_harmony(items, season)
        body_score, body_note, _ = score_body_silhouette_compatibility(items, build_id, height_profile)

        total_score = round(drop_affinity * 0.40 + skin_score * 0.30 + body_score * 0.30, 1)

        formula_tag = f"{top_item.get('color')} + {bot_item.get('color')}"

        scored_looks.append({
            "items": items,
            "top": top_item,
            "bottom": bot_item,
            "outer": outer_item,
            "shoe": shoe_item,
            "match_score": min(98, max(68, int(total_score))),
            "face_score": int(skin_score),
            "body_score": int(body_score),
            "formula_tag": formula_tag,
            "skin_note": skin_note,
            "body_note": body_note,
            "raw_outfit": cand,
        })

    # Sort descending by match_score
    scored_looks.sort(key=lambda x: x["match_score"], reverse=True)

    if not scored_looks:
        return {"active_drop": drop, "hero_look": None, "variations": []}

    hero_look = scored_looks[0]
    variations = scored_looks[1:7]  # Up to 6 variations for MadWitch polaroid cards

    return {
        "active_drop": drop,
        "hero_look": hero_look,
        "variations": variations,
    }


def generate_eloquent_shuffle_outfit(
    wardrobe_df: pd.DataFrame,
    profile: Dict[str, Any],
    locked_items: Optional[Dict[str, str]] = None,
    occasion: str = "Casual Outing",
    temperature: float = 0.75,
) -> Optional[Dict[str, Any]]:
    """
    Random but Eloquent AI outfit selection:
    Evaluates wardrobe combinations using color harmony, skin tone radiance,
    and silhouette proportions, then performs temperature-weighted stochastic
    sampling so combinations are stylish, aesthetic, and pleasantly varied (never rigid).
    """
    if wardrobe_df.empty:
        return None

    locked = locked_items or {}
    season = profile.get("palette_tier", profile.get("season", "medium_golden"))
    build_id = profile.get("body_build", "athletic_v_taper")
    height_profile = profile.get("height_profile", "average")

    tops = wardrobe_df[wardrobe_df["category"].isin(CATEGORY_GROUP.get("tops", []))]
    bottoms = wardrobe_df[wardrobe_df["category"].isin(CATEGORY_GROUP.get("bottoms", []))]
    outers = wardrobe_df[wardrobe_df["category"].isin(CATEGORY_GROUP.get("outer", []))]
    shoes = wardrobe_df[wardrobe_df["category"].isin(CATEGORY_GROUP.get("footwear", []))]
    accessories = wardrobe_df[wardrobe_df["category"].isin(CATEGORY_GROUP.get("accessories", []) + ["Other"])]

    if locked.get("tops"):
        tops = tops[tops["item_id"] == locked["tops"]]
    if locked.get("bottoms"):
        bottoms = bottoms[bottoms["item_id"] == locked["bottoms"]]
    if locked.get("outer"):
        outers = outers[outers["item_id"] == locked["outer"]]
    if locked.get("footwear"):
        shoes = shoes[shoes["item_id"] == locked["footwear"]]
    if locked.get("accessories"):
        accessories = accessories[accessories["item_id"] == locked["accessories"]]

    if tops.empty or bottoms.empty:
        return None

    candidates = []
    for _, t in tops.iterrows():
        for _, b in bottoms.iterrows():
            item_list = [t.to_dict(), b.to_dict()]
            if not outers.empty and (locked.get("outer") or random.random() < 0.4):
                cand_outer = outers.iloc[random.randint(0, len(outers) - 1)].to_dict()
                item_list.append(cand_outer)
            if not shoes.empty:
                cand_shoe = shoes.iloc[random.randint(0, len(shoes) - 1)].to_dict()
                item_list.append(cand_shoe)
            if not accessories.empty and (locked.get("accessories") or random.random() < 0.3):
                cand_acc = accessories.iloc[random.randint(0, len(accessories) - 1)].to_dict()
                item_list.append(cand_acc)
            candidates.append(item_list)

    if not candidates:
        return None

    scored_candidates = []
    scores = []
    for items in candidates:
        c_score = 75.0
        if len(items) >= 2:
            pair_scores = []
            for i in range(len(items)):
                for j in range(i + 1, len(items)):
                    c1 = items[i].get("color", "")
                    c2 = items[j].get("color", "")
                    pair_scores.append(pair_score(c1, c2))
            c_score = sum(pair_scores) / max(len(pair_scores), 1)

        skin_score, skin_note = score_skin_tone_harmony(items, season)
        body_score, body_note, _ = score_body_silhouette_compatibility(items, build_id, height_profile)

        total = (c_score * 0.4) + (skin_score * 0.35) + (body_score * 0.25)
        scores.append(total)
        scored_candidates.append({
            "items": items,
            "color_score": int(c_score),
            "skin_score": int(skin_score),
            "body_score": int(body_score),
            "total_score": round(total, 1),
            "skin_note": skin_note,
            "body_note": body_note,
        })

    scores_arr = np.array(scores)
    scaled = (scores_arr - np.mean(scores_arr)) / max(temperature * 10, 1.0)
    exp_scores = np.exp(np.clip(scaled, -10, 10))
    probs = exp_scores / exp_scores.sum()

    chosen_idx = np.random.choice(len(scored_candidates), p=probs)
    chosen = scored_candidates[chosen_idx]

    top_c = next((it.get("color") for it in chosen["items"] if it.get("category") in CATEGORY_GROUP.get("tops", [])), "")
    bot_c = next((it.get("color") for it in chosen["items"] if it.get("category") in CATEGORY_GROUP.get("bottoms", [])), "")
    outer_it = next((it for it in chosen["items"] if it.get("category") in CATEGORY_GROUP.get("outer", [])), None)

    tag = f"{top_c} + {bot_c}"
    if outer_it:
        tag += f" + {outer_it.get('color')} {outer_it.get('category')}"

    eloquent_desc = f"Subtle {top_c.title()} balanced with {bot_c.title()}. "
    if chosen["color_score"] >= 85:
        eloquent_desc += "A high-cohesion tonal pairing that exudes quiet luxury. "
    else:
        eloquent_desc += "Effortless casual contrast grounded in neutral sophistication. "
    eloquent_desc += chosen["skin_note"]

    chosen["formula_tag"] = tag
    chosen["eloquent_desc"] = eloquent_desc
    return chosen


def find_best_match_for_item(
    wardrobe_df: pd.DataFrame,
    target_item: Dict[str, Any],
    profile: Dict[str, Any],
    category_target: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Find pieces in the wardrobe that correlate best with a specific garment.
    Returns ranked list of matches with match percentage and harmony rationale.
    """
    if wardrobe_df.empty or not target_item:
        return []

    target_id = target_item.get("item_id")
    target_col = target_item.get("color", "")
    season = profile.get("palette_tier", profile.get("season", "medium_golden"))
    build_id = profile.get("body_build", "athletic_v_taper")
    height_profile = profile.get("height_profile", "average")

    matches = []
    for _, row in wardrobe_df.iterrows():
        if row["item_id"] == target_id:
            continue
        if category_target and row["category"] != category_target:
            continue

        item_dict = row.to_dict()
        pair_sc = pair_score(target_col, item_dict.get("color", ""))
        skin_sc, _ = score_skin_tone_harmony([target_item, item_dict], season)
        body_sc, _, _ = score_body_silhouette_compatibility([target_item, item_dict], build_id, height_profile)

        total_sc = round((pair_sc * 0.45) + (skin_sc * 0.35) + (body_sc * 0.20), 1)

        matches.append({
            "item": item_dict,
            "pair_score": pair_sc,
            "skin_score": skin_sc,
            "total_score": min(99, max(60, int(total_sc))),
            "summary": f"{item_dict.get('color')} {item_dict.get('category')} ({item_dict.get('fit', 'Regular')})",
        })

    matches.sort(key=lambda x: x["total_score"], reverse=True)
    return matches


