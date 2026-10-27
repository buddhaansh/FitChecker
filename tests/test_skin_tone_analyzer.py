"""
tests/test_skin_tone_analyzer.py — Tests for skin tone and direct 24-shade color palette logic
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src.skin_tone_analyzer import (
    COMPLEXION_PALETTES,
    SHADES_24,
    SEASON_PALETTES,
    SKIN_TONE_PRESETS,
    resolve_palette,
    load_profile,
    save_profile,
    get_garment_palette_badge,
    score_skin_tone_harmony,
    analyze_face_image,
)


def test_complexion_palettes_structure():
    expected_tiers = [
        "fair_porcelain",
        "light_warm_peach",
        "medium_olive",
        "medium_golden",
        "rich_dusky",
        "deep_espresso",
        "vitiligo_duo",
    ]
    for tier in expected_tiers:
        assert tier in COMPLEXION_PALETTES
        data = COMPLEXION_PALETTES[tier]
        assert len(data["best_colors"]) > 0
        assert len(data["neutrals"]) > 0
        assert len(data["avoid_colors"]) > 0
        assert "description" in data


def test_24_shades_coverage():
    assert len(SHADES_24) == 24
    for i in range(1, 25):
        shade_key = f"shade_{i:02d}"
        assert shade_key in SHADES_24
        shade = SHADES_24[shade_key]
        assert shade["shade_num"] == i
        assert shade["tier"] in COMPLEXION_PALETTES
        assert shade["hex"].startswith("#")
        assert len(shade["rgb"]) == 3


def test_resolve_palette_backward_and_forward_compatibility():
    # Direct tier
    p_gold = resolve_palette("medium_golden")
    assert p_gold["tier_id"] == "medium_golden"

    # Direct shade
    p_s15 = resolve_palette("shade_15")
    assert p_s15["tier_id"] == "medium_golden"

    # Shade number
    p_num = resolve_palette("15")
    assert p_num["tier_id"] == "medium_golden"

    # Legacy season names
    p_aut = resolve_palette("Autumn")
    assert p_aut["tier_id"] == "medium_golden"

    p_win = resolve_palette("Winter")
    assert p_win["tier_id"] == "deep_espresso"


def test_profile_persistence():
    prof = load_profile()
    assert isinstance(prof, dict)
    assert "name" in prof
    assert "gender" in prof

    # Save update
    prof["name"] = "BUDZ"
    prof["gender"] = "Boy"
    prof["skin_tone_id"] = "shade_15"
    prof["palette_tier"] = "medium_golden"
    save_profile(prof)

    loaded = load_profile()
    assert loaded["name"] == "BUDZ"
    assert loaded["gender"] == "Boy"
    assert loaded["skin_tone_id"] == "shade_15"


def test_garment_palette_badge():
    # Olive Green for medium_golden is a best match or warmth booster
    b_olive = get_garment_palette_badge("Olive Green", "medium_golden")
    assert b_olive["badge"] in ["BEST MATCH", "ADD WARMTH"]

    # Rust Orange for medium_golden is a warmth booster
    b_rust = get_garment_palette_badge("Rust Orange", "shade_15")
    assert b_rust["badge"] == "ADD WARMTH"

    # Crisp White for medium_golden is neutral/best
    b_white = get_garment_palette_badge("Crisp White", "medium_golden")
    assert b_white["badge"] in ["STAPLE", "BEST MATCH"]

    # Icy Pale Silver for medium_golden is outside palette
    b_silver = get_garment_palette_badge("Icy Pale Silver", "medium_golden")
    assert b_silver["badge"] == "OUTSIDE PALETTE"


def test_score_skin_tone_harmony():
    items = [{"color": "Olive Green"}, {"color": "Rust Orange"}, {"color": "Navy Blue"}]
    score, note = score_skin_tone_harmony(items, "medium_golden")
    assert 85.0 <= score <= 100.0
    assert "complementary" in note or "Medium Golden" in note


def test_analyze_face_fallback():
    dummy_bytes = b"not_an_image"
    res = analyze_face_image(dummy_bytes)
    assert "shade_number" in res
    assert "skin_hex" in res
    assert "flattering_colors" in res
    assert "washout_colors" in res
    assert "diagnostic_reason" in res
    # Ensure no confusing seasonal words in diagnostic output
    diag = res["diagnostic_reason"].lower()
    assert "cool summer" not in diag
    assert "cool winter" not in diag
    assert "warm autumn" not in diag
    assert "warm spring" not in diag
