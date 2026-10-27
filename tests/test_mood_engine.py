"""
tests/test_mood_engine.py — Tests for natural language plan and mood parsing
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src.mood_engine import parse_plan_and_mood, PRESET_PLANS


def test_presets_exist():
    assert len(PRESET_PLANS) >= 4
    labels = [p["label"] for p in PRESET_PLANS]
    assert "Casual and comfortable" in labels
    assert "Dinner with friends" in labels


def test_parse_dinner_friends():
    res = parse_plan_and_mood("Dinner with friends, polished but comfortable...")
    assert "Dinner" in res["plan_title"]
    assert res["target_formality"] >= 2
    assert "Warm" in res["mood"] or "Polished" in res["mood"] or "Relaxed" in res["mood"]


def test_parse_temperature_and_weather():
    res = parse_plan_and_mood("Casual dinner, comfortable, 18°C")
    assert res["temperature_c"] == 18
    assert res["weather"] == "Cool"

    res_rain = parse_plan_and_mood("Rainy day college walk")
    assert res_rain["weather"] == "Rainy"


def test_parse_packing_mode():
    res = parse_plan_and_mood("Pack for 3 days in Lisbon")
    assert res["is_packing"] is True
    assert res["days"] == 3
    assert res["destination"] == "Lisbon"
