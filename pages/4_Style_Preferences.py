"""
pages/4_Style_Preferences.py — Configure personal style preferences
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from src.data_manager import load_preferences, save_preferences
from config.settings import STYLE_TAGS, FIT_OPTIONS
from src.color_compatibility import AVAILABLE_COLORS
from src.theme_helper import apply_editorial_theme

st.set_page_config(page_title="Style Preferences — FitChecker", page_icon="⚙️", layout="centered")

# Apply full editorial theme: light brown sidebar, light brown text, warm selection
apply_editorial_theme()

st.title("⚙️ Style Preferences")
st.caption(
    "Set your personal preferences. These are used to personalise outfit recommendations. "
    "All fields are optional — skip any you don't care about."
)

prefs = load_preferences()

with st.form("preferences_form"):
    st.subheader("Color Preferences")
    preferred_colors = st.multiselect(
        "Colors I like",
        AVAILABLE_COLORS,
        default=prefs.get("preferred_colors", []),
        help="Outfits containing these colors get a slight boost."
    )
    avoided_colors = st.multiselect(
        "Colors I want to avoid",
        AVAILABLE_COLORS,
        default=prefs.get("avoided_colors", []),
        help="Outfits containing these colors get a penalty."
    )

    st.subheader("Style Preferences")
    preferred_styles = st.multiselect(
        "My preferred styles",
        STYLE_TAGS,
        default=prefs.get("preferred_styles", [])
    )
    preferred_fit = st.selectbox(
        "Preferred fit",
        FIT_OPTIONS,
        index=FIT_OPTIONS.index(prefs.get("preferred_fit", "Regular"))
        if prefs.get("preferred_fit", "Regular") in FIT_OPTIONS else 0
    )

    st.subheader("Formality & Variety")
    desired_formality = st.slider(
        "My general formality preference (1=Casual, 5=Formal)",
        1, 5, int(prefs.get("desired_formality", 3))
    )
    preferred_variety = st.toggle(
        "Prefer outfit variety (avoid recent repeats)",
        value=prefs.get("preferred_variety", True)
    )

    st.subheader("Optional Budget")
    budget_raw = prefs.get("budget_limit", None)
    budget_default = float(budget_raw) if budget_raw else 0.0
    budget_limit = st.number_input(
        "Budget limit for new purchases (₹) — 0 = no limit",
        min_value=0.0, step=500.0, value=budget_default
    )

    saved = st.form_submit_button("💾 Save Preferences", use_container_width=True)

if saved:
    updated = {
        "preferred_colors":  preferred_colors,
        "avoided_colors":    avoided_colors,
        "preferred_styles":  preferred_styles,
        "preferred_fit":     preferred_fit,
        "desired_formality": desired_formality,
        "preferred_variety": preferred_variety,
        "budget_limit":      budget_limit if budget_limit > 0 else None,
    }
    if save_preferences(updated):
        st.success("✅ Preferences saved!")
    else:
        st.error("Failed to save preferences. Check file permissions.")

st.markdown("---")
st.info(
    "💡 **Note:** Preferences influence scoring but don't hard-block outfits. "
    "If a colour preference doesn't apply to any garment you own, it has no effect."
)
