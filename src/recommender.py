"""
recommender.py — FitChecker Baseline Scoring & Ranking
=======================================================
PURPOSE:
  Score and rank outfit candidates using the weighted baseline formula.
  Explain each score component so the user understands *why* an outfit
  was recommended.

FORMULA (configurable in config/settings.py):
  Outfit Score =
    0.30 × Occasion Suitability      (0-100)
  + 0.25 × Color Compatibility       (0-100)
  + 0.20 × Style / Formality Match   (0-100)
  + 0.15 × Weather Suitability       (0-100)
  + 0.10 × Personal Preference Match (0-100)

  Final score is then penalised if the outfit was worn recently.

IMPORTANT NOTE:
  These weights are engineering defaults, not scientifically established
  values.  They are stored in config/settings.py so you can change them
  and re-run tests to observe the effect.

BEGINNER NOTE:
  "Weighted scoring" means we give each dimension a different importance.
  Occasion Suitability (weight 0.30) counts three times more than
  Personal Preference (weight 0.10).
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from config.settings import (
    SCORE_WEIGHTS, OCCASION_PROFILES, RECENT_WEAR_DAYS,
    REPETITION_PENALTY, TOP_N_RECOMMENDATIONS,
)
from src.color_compatibility import outfit_color_score


# ─────────────────────────────────────────────
# COMPONENT SCORERS (each returns 0–100)
# ─────────────────────────────────────────────

def score_occasion_suitability(items: list[dict], occasion: str) -> float:
    """
    How well does the outfit's style and formality match the occasion?

    ALGORITHM:
      1. Look up occasion profile (target formality, preferred styles).
      2. For each item, measure formality distance from target.
      3. Award style tag bonus if item tags intersect preferred styles.
      4. Average across all items.
    """
    profile = OCCASION_PROFILES.get(occasion, OCCASION_PROFILES.get("Daily College Wear"))
    target_formality  = profile.get("formality", 3)
    preferred_styles  = set(profile.get("style", []))

    if not items:
        return 50.0

    item_scores = []
    for item in items:
        # Formality component: score 100 if perfect match, lose 20 per level away
        formality = int(item.get("formality", 3))
        f_diff    = abs(formality - target_formality)
        f_score   = max(0, 100 - f_diff * 20)

        # Style bonus: +15 if any style tag matches preferred styles
        tags = set(t.strip() for t in str(item.get("style_tags", "")).split(",") if t.strip())
        s_bonus = 15 if tags & preferred_styles else 0

        item_scores.append(min(100, f_score + s_bonus))

    return round(sum(item_scores) / len(item_scores), 1)


def score_color_compatibility(items: list[dict]) -> float:
    """Delegate to the color_compatibility module."""
    garment_colors = [{"color": i.get("color", ""), "color_hex": i.get("color_hex", "")}
                      for i in items]
    return outfit_color_score(garment_colors)


def score_style_formality(items: list[dict], occasion: str) -> float:
    """
    Check style coherence within the outfit itself.

    ALGORITHM:
      • Compute the average formality across items.
      • Penalize high variance (mixed very formal + very casual = incoherent).
      • Return a 0-100 score.
    """
    if not items:
        return 50.0
    formalities = [int(i.get("formality", 3)) for i in items]
    mean_f  = sum(formalities) / len(formalities)
    variance = sum((f - mean_f) ** 2 for f in formalities) / len(formalities)
    # Low variance = coherent outfit; penalize up to 40 points for high variance
    coherence = max(0, 100 - variance * 10)
    return round(coherence, 1)


def score_weather_suitability(items: list[dict], current_weather: str) -> float:
    """
    How many items are explicitly suitable for the current weather?

    Returns 100 if weather is "Any" (user didn't specify),
    otherwise proportion of items that are weather-compatible × 100.
    """
    if not current_weather or current_weather == "Any":
        return 100.0
    if not items:
        return 50.0

    compatible = 0
    for item in items:
        w = str(item.get("weather", "Any")).lower()
        if w in ("any", "all seasons") or w == current_weather.lower():
            compatible += 1

    return round((compatible / len(items)) * 100, 1)


def score_personal_preference(items: list[dict], preferences: dict) -> float:
    """
    How well does the outfit match the user's personal preferences?

    Checks:
      • Preferred colors → +20 points each (capped at 60)
      • Avoided colors   → -30 points each (capped at -60)
      • Preferred styles → +15 per match  (capped at 45)
    """
    if not preferences or not items:
        return 70.0   # Neutral score when no preferences exist

    preferred_colors = [c.lower() for c in preferences.get("preferred_colors", [])]
    avoided_colors   = [c.lower() for c in preferences.get("avoided_colors", [])]
    preferred_styles = set(preferences.get("preferred_styles", []))

    bonus = 0
    for item in items:
        color = str(item.get("color", "")).lower()
        if color in preferred_colors:
            bonus += 20
        if color in avoided_colors:
            bonus -= 30
        tags = set(t.strip() for t in str(item.get("style_tags", "")).split(",") if t.strip())
        if tags & preferred_styles:
            bonus += 15

    raw = 70.0 + max(-60, min(60, bonus))  # Clamp bonus
    return round(max(0, min(100, raw)), 1)


# ─────────────────────────────────────────────
# REPETITION PENALTY
# ─────────────────────────────────────────────

def _days_since_last_worn(item: dict) -> Optional[int]:
    """Return days since last_worn, or None if not available."""
    last = item.get("last_worn", "")
    if not last or str(last).strip() in ("", "nan", "None"):
        return None
    try:
        last_date = datetime.strptime(str(last).strip(), "%Y-%m-%d")
        return (datetime.now() - last_date).days
    except ValueError:
        return None


def repetition_penalty(items: list[dict]) -> float:
    """
    Return a penalty (0–REPETITION_PENALTY) to subtract from the final score.

    If any item was worn within RECENT_WEAR_DAYS days, apply the penalty.
    Gradually reduces as the item gets older (so penalty is 100% on day 0,
    0% on day RECENT_WEAR_DAYS).
    """
    max_pen = REPETITION_PENALTY * 100   # Convert to 0-100 scale
    penalties = []
    for item in items:
        days = _days_since_last_worn(item)
        if days is not None and days <= RECENT_WEAR_DAYS:
            # Fraction of penalty: 1.0 on day 0, approaching 0 on day N
            fraction = 1.0 - (days / RECENT_WEAR_DAYS)
            penalties.append(fraction * max_pen)
    if not penalties:
        return 0.0
    return round(max(penalties), 1)   # Use the largest individual penalty


# ─────────────────────────────────────────────
# EXPLANATION BUILDER
# ─────────────────────────────────────────────

def build_explanation(components: dict, weights: dict, penalty: float) -> str:
    """Build a human-readable explanation string for a score."""
    lines = []
    for key, score in components.items():
        label  = key.replace("_", " ").title()
        weight = weights.get(key, 0)
        contrib = round(score * weight, 1)
        lines.append(f"• {label}: {score:.0f}/100 × {int(weight*100)}% = {contrib:.1f} pts")
    if penalty > 0:
        lines.append(f"• Repetition Penalty: −{penalty:.0f} pts (worn recently)")
    return "\n".join(lines)


# ─────────────────────────────────────────────
# MAIN SCORING FUNCTION
# ─────────────────────────────────────────────

def score_outfit(
    outfit: dict,
    occasion: str,
    current_weather: str = "Any",
    preferences: dict = None,
    weights: dict = None,
) -> dict:
    """
    Compute the full score for a single outfit.

    Returns the outfit dict enriched with:
      "score":            float (0-100)
      "score_components": dict  {component: score}
      "explanation":      str
      "penalty":          float
    """
    if preferences is None:
        preferences = {}
    if weights is None:
        weights = SCORE_WEIGHTS

    items = outfit.get("items", [])

    components = {
        "occasion_suitability": score_occasion_suitability(items, occasion),
        "color_compatibility":  score_color_compatibility(items),
        "style_formality":      score_style_formality(items, occasion),
        "weather_suitability":  score_weather_suitability(items, current_weather),
        "personal_preference":  score_personal_preference(items, preferences),
    }

    # Weighted sum
    raw_score = sum(components[k] * weights.get(k, 0) for k in components)

    # Repetition penalty
    penalty = repetition_penalty(items)
    final   = max(0.0, round(raw_score - penalty, 1))

    explanation = build_explanation(components, weights, penalty)

    return {
        **outfit,
        "score":            final,
        "score_components": components,
        "explanation":      explanation,
        "penalty":          penalty,
    }


# ─────────────────────────────────────────────
# RANKER
# ─────────────────────────────────────────────

def rank_outfits(
    outfits: list[dict],
    occasion: str,
    current_weather: str = "Any",
    preferences: dict = None,
    weights: dict = None,
    top_n: int = TOP_N_RECOMMENDATIONS,
) -> list[dict]:
    """
    Score all candidate outfits and return the top-N sorted by score descending.

    If outfits list is empty, returns [].
    """
    if not outfits:
        return []

    scored = [
        score_outfit(o, occasion, current_weather, preferences, weights)
        for o in outfits
    ]
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_n]
