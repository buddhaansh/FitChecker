"""
mood_engine.py — Natural Language Plan & Mood Understanding for FitChecker
===========================================================================
PURPOSE:
  Parses user inputs like "Dinner with friends, polished but comfortable..."
  or quick preset buttons to determine:
    1. Vibe / Mood (Relaxed, Polished, Confident, Cozy, Bold)
    2. Occasion & Formality Level
    3. Weather / Temperature cues
    4. Special modes (e.g. Packing capsule mode)
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
from typing import Dict, Any, List

from config.settings import OCCASIONS, WEATHER_OPTIONS

PRESET_PLANS = [
    {
        "id": "casual_comfort",
        "label": "Casual and comfortable",
        "prompt": "Relaxed weekend outing, effortless comfort, easy movement",
        "mood": "Relaxed",
        "occasion": "Casual Outing",
        "formality": 2,
    },
    {
        "id": "polished_work",
        "label": "A polished work day",
        "prompt": "College presentation and smart work day, sharp and composed",
        "mood": "Polished",
        "occasion": "College Presentation",
        "formality": 3,
    },
    {
        "id": "dinner_friends",
        "label": "Dinner with friends",
        "prompt": "Dinner with friends, polished but comfortable, warm atmosphere",
        "mood": "Warm Social",
        "occasion": "Date",
        "formality": 3,
    },
    {
        "id": "special_occasion",
        "label": "A special occasion",
        "prompt": "Celebration evening or college fest, standout aesthetic",
        "mood": "Elevated / Bold",
        "occasion": "Party",
        "formality": 4,
    },
    {
        "id": "packing_trip",
        "label": "Packing for a trip",
        "prompt": "Pack a versatile capsule for a 3-day getaway",
        "mood": "Versatile Capsule",
        "occasion": "Casual Outing",
        "formality": 2,
        "is_packing": True,
    },
]


def parse_plan_and_mood(prompt: str) -> Dict[str, Any]:
    """
    Extract intention, mood, formality, occasion, and packing parameters.
    """
    p = (prompt or "").strip()
    low = p.lower()

    # Default baseline
    res = {
        "raw_prompt": p,
        "plan_title": p if p else "Everyday Outfits",
        "mood": "Balanced",
        "occasion": "Daily College Wear",
        "target_formality": 2,
        "weather": "Any",
        "temperature_c": None,
        "is_packing": False,
        "destination": "",
        "days": 3,
        "keywords": [],
    }

    if not p:
        return res

    # 1. Detect Packing Mode
    if any(k in low for k in ["pack", "packing", "trip", "travel", "vacation", "getaway"]):
        res["is_packing"] = True
        days_match = re.search(r'(\d+)\s*[- ]*(?:day|days|night|nights)', low)
        if days_match:
            res["days"] = max(1, min(14, int(days_match.group(1))))

        # Look for destination like "in Lisbon", "to Paris", "for Goa"
        dest_match = re.search(r'(?:in|to|for)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)', p)
        if dest_match:
            res["destination"] = dest_match.group(1)
        elif "lisbon" in low:
            res["destination"] = "Lisbon"
        elif "goa" in low:
            res["destination"] = "Goa"

    # 2. Weather & Temperature Extraction
    temp_match = re.search(r'(\d+)\s*(?:°|deg|c\b)', low)
    if temp_match:
        temp_val = int(temp_match.group(1))
        res["temperature_c"] = temp_val
        if temp_val <= 12:
            res["weather"] = "Cold"
        elif temp_val <= 19:
            res["weather"] = "Cool"
        elif temp_val <= 27:
            res["weather"] = "Warm"
        else:
            res["weather"] = "Hot"
    elif any(k in low for k in ["rain", "rainy", "monsoon", "drizzle", "umbrella"]):
        res["weather"] = "Rainy"
    elif any(k in low for k in ["cold", "winter", "chilly", "freezing", "snow"]):
        res["weather"] = "Cold"
    elif any(k in low for k in ["hot", "summer", "sunny", "humid"]):
        res["weather"] = "Hot"
    elif any(k in low for k in ["cool", "autumn", "breeze", "breezy"]):
        res["weather"] = "Cool"

    # 3. Occasion Detection
    if any(k in low for k in ["presentation", "interview", "defense", "pitch", "formal meeting"]):
        res["occasion"] = "College Presentation"
        res["target_formality"] = 3
        res["mood"] = "Sharp & Composed"
    elif any(k in low for k in ["dinner", "date", "candle", "restaurant", "evening with friends"]):
        res["occasion"] = "Date"
        res["target_formality"] = 3
        res["mood"] = "Warm & Polished"
    elif any(k in low for k in ["party", "club", "fest", "night out", "celebration", "concert"]):
        res["occasion"] = "Party"
        res["target_formality"] = 4
        res["mood"] = "Bold & Expressive"
    elif any(k in low for k in ["gym", "workout", "sports", "running", "jog"]):
        res["occasion"] = "Daily College Wear"
        res["target_formality"] = 1
        res["mood"] = "Active & Athleisure"
    elif any(k in low for k in ["formal", "wedding", "conference", "gala"]):
        res["occasion"] = "Formal Event"
        res["target_formality"] = 5
        res["mood"] = "Architectural & Formal"
    elif any(k in low for k in ["lab", "workshop"]):
        res["occasion"] = "Lab / Workshop Session"
        res["target_formality"] = 2
        res["mood"] = "Practical & Focused"
    else:
        res["occasion"] = "Casual Outing"
        res["target_formality"] = 2
        res["mood"] = "Effortless & Casual"

    # 4. Mood Adjustments
    if any(k in low for k in ["relax", "comfortable", "cozy", "easy", "chill", "soft"]):
        res["mood"] = "Relaxed & Comfortable"
    elif any(k in low for k in ["polish", "elevated", "smart", "clean", "put-together"]):
        res["mood"] = "Polished & Elevated"
    elif any(k in low for k in ["bold", "standout", "edgy", "chic"]):
        res["mood"] = "Bold & Statement"

    return res
