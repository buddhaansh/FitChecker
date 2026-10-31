"""
app.py — Muse Wardrobe & Editorial Outfit Stylist for BUDZ
===========================================================
Dual-criteria (Face & Skin Tone + Body Silhouette) digital wardrobe,
Whering-inspired interactive styling canvas, continuous correlation carousel,
eloquent AI selection (Clueless shuffle), mood-based outfit curation, and lookbooks.

Run with:
  & "C:\\Users\\Dell\\anaconda3\\python.exe" -m streamlit run app.py
"""

import sys
import os
import random
import io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image

# ─────────────────────────────────────────────
# PAGE CONFIGURATION
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Muse Wardrobe — BUDZ",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from config.settings import (
    OCCASIONS, WEATHER_OPTIONS, CATEGORY_GROUP,
    SAMPLE_WARDROBE_FILE, IMAGES_DIR,
)
from src.data_manager import load_wardrobe, save_wardrobe, import_sample_data, add_garment
from src.wardrobe_manager import get_wardrobe_summary
from src.skin_tone_analyzer import (
    load_profile, save_profile, analyze_face_image,
    SEASON_PALETTES, COMPLEXION_PALETTES, SHADES_24,
    SKIN_TONE_PRESETS, resolve_palette,
    get_garment_palette_badge, score_skin_tone_harmony,
)
from src.body_criteria import (
    BODY_BUILDS, HEIGHT_PROFILES, score_body_silhouette_compatibility
)
from src.color_compatibility import pair_score, describe_color_interplay
from src.mood_engine import parse_plan_and_mood, PRESET_PLANS
from src.editorial_recommender import (
    generate_editorial_recommendations,
    get_pairings_for_garment,
    generate_packing_capsule,
    LOOKBOOK_DROPS,
    generate_lookbook_showcase,
    generate_eloquent_shuffle_outfit,
    find_best_match_for_item,
)
from src.feedback_manager import record_outfit_selection, record_wear_confirmation, get_feedback_stats

# Curated Staple Fallbacks when closet has 0 shoes or 0 accessories
STAPLE_SHOES = [
    {"item_id": "staple_shoe_white_sneaker", "category": "Sneakers", "color": "White", "formality": 2, "fit": "Regular", "color_hex": "#F4F3EF", "brand": "Minimalist Sneaker (Staple)"},
    {"item_id": "staple_shoe_black_loafer", "category": "Formal Shoes", "color": "Black", "formality": 4, "fit": "Regular", "color_hex": "#1A1A1A", "brand": "Penny Loafer (Staple)"},
    {"item_id": "staple_shoe_chelsea_boot", "category": "Boots", "color": "Brown", "formality": 3, "fit": "Regular", "color_hex": "#5C3A21", "brand": "Chelsea Boot (Staple)"},
]

STAPLE_ACCESSORIES = [
    {"item_id": "staple_acc_tortoise_glasses", "category": "Glasses", "color": "Brown", "formality": 3, "fit": "Regular", "color_hex": "#5A3825", "brand": "Tortoiseshell Frames (Staple)"},
    {"item_id": "staple_acc_gold_aviators", "category": "Glasses", "color": "Beige", "formality": 2, "fit": "Regular", "color_hex": "#D4AF37", "brand": "Gold Wire Aviators (Staple)"},
    {"item_id": "staple_acc_black_shades", "category": "Sunglasses", "color": "Black", "formality": 2, "fit": "Regular", "color_hex": "#1E1E1E", "brand": "Matte Black Sunglasses (Staple)"},
]

# Load state
wardrobe_df = load_wardrobe()
profile     = load_profile()

# Ensure default name is BUDZ and gender is Boy (him)
if profile.get("name") in ["Pauline", ""]:
    profile["name"] = "BUDZ"
    profile["gender"] = "Boy"
    save_profile(profile)

palette_data = resolve_palette(profile.get("palette_tier", profile.get("season", "medium_golden")))
active_palette_key = profile.get("palette_tier", profile.get("season", "medium_golden"))
build_data   = BODY_BUILDS.get(profile.get("body_build", "athletic_v_taper"), BODY_BUILDS["athletic_v_taper"])

# ─────────────────────────────────────────────
# LUXURY EDITORIAL BROWN & WHITE STYLESHEET
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

/* Universal Text Selection */
::selection {
    background-color: #E8D8C8 !important;
    color: #36261E !important;
}
::-moz-selection {
    background-color: #E8D8C8 !important;
    color: #36261E !important;
}

/* Main App Background & Typography */
.stApp {
    background-color: #FAF7F2 !important;
    color: #1A1412 !important;
    font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
}

/* Sidebar styling */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div:first-child,
section[data-testid="stSidebar"],
.stSidebar,
div[data-testid="stSidebarContent"],
[data-testid="stSidebarUserContent"] {
    background-color: #EFE7DE !important;
    border-right: 1.5px solid #DDD1C2 !important;
}

[data-testid="stSidebarNav"] a,
[data-testid="stSidebarNav"] li,
[data-testid="stSidebarNav"] span,
[data-testid="stSidebarNav"] p,
[data-testid="stSidebarNavLink"],
[data-testid="stSidebar"] a,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label {
    color: #704E38 !important;
    font-size: 15px !important;
    font-weight: 600 !important;
}

/* High contrast typography */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] strong,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] div,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4,
[data-testid="stMarkdownContainer"] h5,
[data-testid="stMarkdownContainer"] h6,
label,
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] label {
    color: #1A1412 !important;
}

h1, h2, h3, h4, h5, h6, .serif-font {
    font-family: 'Playfair Display', Georgia, serif !important;
    color: #1A1412 !important;
    font-weight: 700 !important;
}

/* Tabs: Prominent, Luxury, Visible */
div[data-baseweb="tab-list"] {
    border-bottom: 2px solid #E5DED4 !important;
    gap: 12px !important;
    margin-bottom: 24px !important;
}
div[data-baseweb="tab-list"] button {
    font-size: 17px !important;
    font-weight: 700 !important;
    color: #4A4138 !important;
    padding: 12px 22px !important;
    border-radius: 8px 8px 0 0 !important;
    transition: all 0.2s ease;
}
div[data-baseweb="tab-list"] button[aria-selected="true"] {
    color: #B85D3B !important;
    border-bottom: 3.5px solid #B85D3B !important;
    background: #FAF6F3 !important;
}

/* Buttons */
div.stButton > button[kind="primary"] {
    background-color: #B85D3B !important;
    color: #FFFFFF !important;
    border: none !important;
    font-weight: 700 !important;
    border-radius: 20px !important;
    padding: 8px 24px !important;
    box-shadow: 0 4px 12px rgba(184, 93, 59, 0.25) !important;
}
div.stButton > button[kind="primary"]:hover {
    background-color: #9E4D2E !important;
}

div.stButton > button[kind="secondary"],
div.stButton > button:not([kind="primary"]) {
    background-color: #FFFFFF !important;
    border: 1.5px solid #D5CFC7 !important;
    color: #1A1412 !important;
    font-weight: 600 !important;
    border-radius: 12px !important;
}
div.stButton > button:not([kind="primary"]):hover {
    border-color: #8C3B1E !important;
    background-color: #F8F5F0 !important;
}

/* Garment Cutout Images with Floating Drop Shadow */
[data-testid="stImage"] img {
    filter: drop-shadow(0 10px 18px rgba(36, 28, 24, 0.16)) !important;
    border-radius: 8px !important;
    transition: transform 0.2s ease;
}
[data-testid="stImage"] img:hover {
    transform: translateY(-2px) scale(1.02);
}

/* Whering Slot Machine & Studio */
.whering-carousel-card {
    background: #FFFFFF !important;
    border: 1.5px solid #E5DED4 !important;
    border-radius: 14px;
    padding: 14px;
    margin-bottom: 14px;
    box-shadow: 0 4px 14px rgba(36, 28, 24, 0.04);
    text-align: center;
    transition: all 0.2s ease;
}
.whering-carousel-card:hover {
    border-color: #B85D3B !important;
}
.whering-slot-badge {
    display: inline-block;
    font-size: 11.5px;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #8C3B1E;
    background: #F7ECE7;
    border: 1px solid #E4C5BA;
    padding: 4px 12px;
    border-radius: 12px;
    margin-bottom: 8px;
}
.whering-canvas-board {
    background: linear-gradient(180deg, #FFFFFF 0%, #F9F6F0 100%) !important;
    border: 2px solid #D5CFC7 !important;
    border-radius: 18px;
    padding: 26px;
    box-shadow: 0 10px 32px rgba(36, 28, 24, 0.08);
    text-align: center;
    margin-bottom: 20px;
}
.whering-correlation-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    font-weight: 700;
    color: #2D5A27;
    background: #EBF3EA;
    border: 1px solid #BED8BC;
    padding: 6px 14px;
    border-radius: 14px;
    margin-top: 6px;
}

/* Badges */
.badge-best {
    background: #EBF3EA; color: #2D5A27; border: 1px solid #BED8BC;
    padding: 3px 8px; border-radius: 10px; font-size: 11px; font-weight: 700;
}
.badge-warmth {
    background: #F7ECE7; color: #8C3B1E; border: 1px solid #E4C5BA;
    padding: 3px 8px; border-radius: 10px; font-size: 11px; font-weight: 700;
}
.badge-staple {
    background: #F2EFEB; color: #4A453E; border: 1px solid #D5CFC7;
    padding: 3px 8px; border-radius: 10px; font-size: 11px; font-weight: 700;
}

.profile-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #FFFFFF;
    border: 1.5px solid #D5CFC7;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 13.5px;
    font-weight: 600;
}
.skin-dot {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    display: inline-block;
    border: 1px solid rgba(0,0,0,0.15);
}

.diagnostic-box {
    background-color: #FFFFFF !important;
    border: 1.5px solid #D5CFC7 !important;
    border-left: 5px solid #8C3B1E !important;
    border-radius: 10px !important;
    padding: 20px !important;
    margin-top: 14px !important;
    box-shadow: 0 4px 14px rgba(36, 28, 24, 0.05) !important;
}

.garment-tile {
    background-color: #FFFFFF !important;
    border: 1.5px solid #E5DED4 !important;
    border-radius: 12px !important;
    padding: 14px !important;
    margin-bottom: 14px !important;
    box-shadow: 0 4px 12px rgba(36, 28, 24, 0.04) !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TOP NAVIGATION & USER PROFILE BAR
# ─────────────────────────────────────────────
user_name   = profile.get("name", "BUDZ")
user_gender = profile.get("gender", "Boy")
gender_label = "Him" if user_gender in ["Boy", "Him", "Male"] else "Her" if user_gender in ["Girl", "Her", "Female"] else "Them"
pronoun_subject = "he" if user_gender in ["Boy", "Him", "Male"] else "she" if user_gender in ["Girl", "Her", "Female"] else "they"
pronoun_possessive = "his" if user_gender in ["Boy", "Him", "Male"] else "her" if user_gender in ["Girl", "Her", "Female"] else "their"
pronoun_object = "him" if user_gender in ["Boy", "Him", "Male"] else "her" if user_gender in ["Girl", "Her", "Female"] else "them"

palette_info = resolve_palette(profile.get("palette_tier", profile.get("season", "medium_golden")))
palette_name = palette_info.get("name", "Medium Golden")
skin_hex    = profile.get("skin_hex", "#A7714C")
build_label = build_data.get("name", "Athletic")
shade_label = profile.get("skin_tone_label", "Shade 15")
short_shade = shade_label.split("—")[0].strip() if "—" in shade_label else shade_label

top_col1, top_col2, top_col3 = st.columns([3.5, 1, 2.8])

with top_col1:
    st.markdown(f"<h2 style='margin:0; font-family:Playfair Display, Georgia, serif; font-size:32px; font-weight:700; color:#1A1412 !important;'>{user_name.upper()}'S WARDROBE</h2>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:#2E2722 !important; font-size:14.5px; font-weight:600; margin-top:2px;'>Whering Digital Wardrobe & Editorial Outfit Studio</div>", unsafe_allow_html=True)

with top_col2:
    if st.button("+ ADD A PIECE", type="primary", use_container_width=True):
        st.switch_page("pages/2_Add_Clothing.py")

with top_col3:
    st.markdown(f"""
    <div style='text-align:right;'>
        <div class="profile-pill">
            <span class="skin-dot" style="background-color: {skin_hex};"></span>
            <span>{user_name} ({gender_label})</span>
            <span style="color:#8C3B1E; font-size:11px; background:#F7ECE7; padding:2px 8px; border-radius:10px;">{short_shade} · {palette_name}</span>
            <span style="color:#2D5A27; font-size:11px; background:#EBF3EA; padding:2px 8px; border-radius:10px;">{build_label}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Partition Wardrobe categories
w_tops = wardrobe_df[wardrobe_df["category"].isin(CATEGORY_GROUP.get("tops", []))]
w_bots = wardrobe_df[wardrobe_df["category"].isin(CATEGORY_GROUP.get("bottoms", []))]
w_outers = wardrobe_df[wardrobe_df["category"].isin(CATEGORY_GROUP.get("outer", []))]
w_shoes = wardrobe_df[wardrobe_df["category"].isin(CATEGORY_GROUP.get("footwear", []))]
w_accs = wardrobe_df[wardrobe_df["category"].isin(CATEGORY_GROUP.get("accessories", []) + ["Other"])]

# Initialize session state for carousels
if "carousel_top_idx" not in st.session_state:
    st.session_state["carousel_top_idx"] = 0
if "carousel_bot_idx" not in st.session_state:
    st.session_state["carousel_bot_idx"] = 0
if "carousel_outer_idx" not in st.session_state:
    st.session_state["carousel_outer_idx"] = 0
if "carousel_shoe_idx" not in st.session_state:
    st.session_state["carousel_shoe_idx"] = 0

if "lock_top" not in st.session_state:
    st.session_state["lock_top"] = False
if "lock_bot" not in st.session_state:
    st.session_state["lock_bot"] = False
if "lock_outer" not in st.session_state:
    st.session_state["lock_outer"] = False
if "lock_shoe" not in st.session_state:
    st.session_state["lock_shoe"] = False

if "eloquent_look" not in st.session_state:
    st.session_state["eloquent_look"] = None

# ─────────────────────────────────────────────
# 6 PRIMARY TABS (FRONT & CENTER LIKE WHERING)
# ─────────────────────────────────────────────
tab_dress_me, tab_canvas, tab_eloquent, tab_inventory, tab_planner, tab_profile = st.tabs([
    "👗 Dress Me",
    "🎨 Interactive Styling Canvas",
    "🎲 Eloquent AI Selection",
    "🧥 Wardrobe & Cutouts",
    "📅 Mood & Outfit Planner",
    "👤 Profile Calibration",
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: 👗 DRESS ME (SLOT MACHINE / CONTINUOUS CORRELATION / FLATLAY)
# ─────────────────────────────────────────────────────────────────────────────
with tab_dress_me:
    st.markdown("""
    <div style="background:#FAF6F3; border:1px solid #EBE4DA; border-radius:10px; padding:14px 18px; margin-bottom:18px;">
        <div style="font-size:11.5px; font-weight:800; color:#8C3B1E; text-transform:uppercase; letter-spacing:0.12em;">Whering Dress Me Carousel</div>
        <div style="font-size:20px; font-weight:700; color:#1A1412; font-family:'Playfair Display', Georgia, serif; margin:2px 0 4px 0;">4-Tier Slot Machine & Live Continuous Correlation</div>
        <div style="font-size:14px; color:#2E2722;">Cycle through your clothes using ◀ and ▶. Pin pieces you want to keep. As you scroll, the AI continuously computes the best matching bottom and harmonizes the complete flatlay in real time.</div>
    </div>
    """, unsafe_allow_html=True)

    if wardrobe_df.empty:
        st.markdown(f"""
        <div style="background: #FFFFFF; border: 1.5px dashed #D5C7B8; border-radius: 14px; padding: 40px 24px; text-align: center; margin: 20px 0;">
            <div style="font-size: 42px; margin-bottom: 10px;">✨</div>
            <div style="font-family: 'Playfair Display', Georgia, serif; font-size: 22px; font-weight: 700; color: #241C18; margin-bottom: 8px;">
                Wardrobe Zero — Clean Slate
            </div>
            <div style="font-size: 14.5px; color: #704E38; max-width: 520px; margin: 0 auto 20px auto; line-height: 1.6;">
                Your wardrobe is currently empty. Click <strong>+ ADD A PIECE</strong> above to scan your clothes with automatic background cutout and begin styling!
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        d_col1, d_col2 = st.columns([1.15, 1.35])

        with d_col1:
            # ── Tier 1: Tops / Upper ──
            st.markdown("<div class='whering-slot-badge'>1. Upper (Tops / Tees / Shirts)</div>", unsafe_allow_html=True)
            active_top_dict = None
            if not w_tops.empty:
                top_len = len(w_tops)
                st.session_state["carousel_top_idx"] = st.session_state["carousel_top_idx"] % top_len
                curr_top = w_tops.iloc[st.session_state["carousel_top_idx"]].to_dict()
                active_top_dict = curr_top

                st.markdown("<div class='whering-carousel-card'>", unsafe_allow_html=True)
                tc_prev, tc_card, tc_next = st.columns([1, 4, 1])
                with tc_prev:
                    if st.button("◀", key="prev_top_btn", use_container_width=True):
                        st.session_state["carousel_top_idx"] = (st.session_state["carousel_top_idx"] - 1) % top_len
                        st.rerun()
                with tc_next:
                    if st.button("▶", key="next_top_btn", use_container_width=True):
                        st.session_state["carousel_top_idx"] = (st.session_state["carousel_top_idx"] + 1) % top_len
                        st.rerun()
                with tc_card:
                    p_photo = curr_top.get("photo_path")
                    if p_photo and os.path.exists(str(p_photo)):
                        st.image(str(p_photo), use_column_width=True)
                    else:
                        st.markdown(f"<div style='background:{curr_top.get('color_hex','#808080')};height:70px;border-radius:8px;'></div>", unsafe_allow_html=True)
                    st.markdown(f"<strong>{curr_top.get('color','').title()} {curr_top.get('category')}</strong> <br><small style='color:#704E38;'>{curr_top.get('fit','Regular')} · Formality {curr_top.get('formality',2)}/5</small>", unsafe_allow_html=True)
                    lock_t = st.checkbox("📌 Lock Top", value=st.session_state.get("lock_top", False), key="lock_top_chk")
                    st.session_state["lock_top"] = lock_t
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("No tops found in wardrobe. Add a top piece!")

            # ── Continuous Correlation between Top & Bottom ──
            if active_top_dict and not w_bots.empty:
                best_bottoms = find_best_match_for_item(wardrobe_df, active_top_dict, profile)
                best_bottoms = [bm for bm in best_bottoms if bm["item"]["category"] in CATEGORY_GROUP.get("bottoms", [])]
                if best_bottoms:
                    top_bm = best_bottoms[0]
                    st.markdown(f"""
                    <div class="whering-correlation-pill" style="margin-bottom:12px; width:100%; box-sizing:border-box;">
                        ⚡ <strong>Continuous Correlation:</strong> Best bottom for this top is <strong>{top_bm['summary']}</strong> ({top_bm['total_score']}% Match)
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("⚡ Snap Carousel to Best Matching Bottom", key="snap_best_bot_btn", use_container_width=True):
                        match_id = top_bm["item"]["item_id"]
                        for bi, (_, brow) in enumerate(w_bots.iterrows()):
                            if brow["item_id"] == match_id:
                                st.session_state["carousel_bot_idx"] = bi
                                break
                        st.rerun()

            # ── Tier 2: Bottoms ──
            st.markdown("<div class='whering-slot-badge'>2. Bottom (Trousers / Denim / Cargos)</div>", unsafe_allow_html=True)
            active_bot_dict = None
            if not w_bots.empty:
                bot_len = len(w_bots)
                st.session_state["carousel_bot_idx"] = st.session_state["carousel_bot_idx"] % bot_len
                curr_bot = w_bots.iloc[st.session_state["carousel_bot_idx"]].to_dict()
                active_bot_dict = curr_bot

                st.markdown("<div class='whering-carousel-card'>", unsafe_allow_html=True)
                bc_prev, bc_card, bc_next = st.columns([1, 4, 1])
                with bc_prev:
                    if st.button("◀", key="prev_bot_btn", use_container_width=True):
                        st.session_state["carousel_bot_idx"] = (st.session_state["carousel_bot_idx"] - 1) % bot_len
                        st.rerun()
                with bc_next:
                    if st.button("▶", key="next_bot_btn", use_container_width=True):
                        st.session_state["carousel_bot_idx"] = (st.session_state["carousel_bot_idx"] + 1) % bot_len
                        st.rerun()
                with bc_card:
                    p_photo = curr_bot.get("photo_path")
                    if p_photo and os.path.exists(str(p_photo)):
                        st.image(str(p_photo), use_column_width=True)
                    else:
                        st.markdown(f"<div style='background:{curr_bot.get('color_hex','#808080')};height:70px;border-radius:8px;'></div>", unsafe_allow_html=True)
                    st.markdown(f"<strong>{curr_bot.get('color','').title()} {curr_bot.get('category')}</strong> <br><small style='color:#704E38;'>{curr_bot.get('fit','Regular')} · Formality {curr_bot.get('formality',2)}/5</small>", unsafe_allow_html=True)
                    lock_b = st.checkbox("📌 Lock Bottom", value=st.session_state.get("lock_bot", False), key="lock_bot_chk")
                    st.session_state["lock_bot"] = lock_b
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("No bottoms found in wardrobe. Add trousers or jeans!")

            # ── Tier 3: Jacket / Layer (Optional) ──
            active_outer_dict = None
            if not w_outers.empty:
                st.markdown("<div class='whering-slot-badge'>3. Layer (Jacket / Blazer / Overshirt)</div>", unsafe_allow_html=True)
                outer_len = len(w_outers)
                st.session_state["carousel_outer_idx"] = st.session_state["carousel_outer_idx"] % outer_len
                curr_outer = w_outers.iloc[st.session_state["carousel_outer_idx"]].to_dict()
                active_outer_dict = curr_outer

                st.markdown("<div class='whering-carousel-card'>", unsafe_allow_html=True)
                oc_prev, oc_card, oc_next = st.columns([1, 4, 1])
                with oc_prev:
                    if st.button("◀", key="prev_outer_btn", use_container_width=True):
                        st.session_state["carousel_outer_idx"] = (st.session_state["carousel_outer_idx"] - 1) % outer_len
                        st.rerun()
                with oc_next:
                    if st.button("▶", key="next_outer_btn", use_container_width=True):
                        st.session_state["carousel_outer_idx"] = (st.session_state["carousel_outer_idx"] + 1) % outer_len
                        st.rerun()
                with oc_card:
                    p_photo = curr_outer.get("photo_path")
                    if p_photo and os.path.exists(str(p_photo)):
                        st.image(str(p_photo), use_column_width=True)
                    else:
                        st.markdown(f"<div style='background:{curr_outer.get('color_hex','#808080')};height:70px;border-radius:8px;'></div>", unsafe_allow_html=True)
                    st.markdown(f"<strong>{curr_outer.get('color','').title()} {curr_outer.get('category')}</strong>", unsafe_allow_html=True)
                    lock_o = st.checkbox("📌 Lock Layer", value=st.session_state.get("lock_outer", False), key="lock_outer_chk")
                    st.session_state["lock_outer"] = lock_o
                st.markdown("</div>", unsafe_allow_html=True)

            # ── Tier 4: Footwear (User or Curated Staples) ──
            active_shoe_dict = None
            available_shoes = w_shoes.to_dict("records") if not w_shoes.empty else STAPLE_SHOES
            if available_shoes:
                st.markdown("<div class='whering-slot-badge'>4. Footwear</div>", unsafe_allow_html=True)
                shoe_len = len(available_shoes)
                st.session_state["carousel_shoe_idx"] = st.session_state["carousel_shoe_idx"] % shoe_len
                curr_shoe = available_shoes[st.session_state["carousel_shoe_idx"]]
                active_shoe_dict = curr_shoe

                st.markdown("<div class='whering-carousel-card'>", unsafe_allow_html=True)
                sc_prev, sc_card, sc_next = st.columns([1, 4, 1])
                with sc_prev:
                    if st.button("◀", key="prev_shoe_btn", use_container_width=True):
                        st.session_state["carousel_shoe_idx"] = (st.session_state["carousel_shoe_idx"] - 1) % shoe_len
                        st.rerun()
                with sc_next:
                    if st.button("▶", key="next_shoe_btn", use_container_width=True):
                        st.session_state["carousel_shoe_idx"] = (st.session_state["carousel_shoe_idx"] + 1) % shoe_len
                        st.rerun()
                with sc_card:
                    p_photo = curr_shoe.get("photo_path")
                    if p_photo and os.path.exists(str(p_photo)):
                        st.image(str(p_photo), use_column_width=True)
                    else:
                        st.markdown(f"<div style='background:{curr_shoe.get('color_hex','#F4F3EF')};height:70px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:26px;'>👟</div>", unsafe_allow_html=True)
                    st.markdown(f"<strong>{curr_shoe.get('brand', curr_shoe.get('color','').title() + ' ' + curr_shoe.get('category'))}</strong>", unsafe_allow_html=True)
                    lock_s = st.checkbox("📌 Lock Shoes", value=st.session_state.get("lock_shoe", False), key="lock_shoe_chk")
                    st.session_state["lock_shoe"] = lock_s
                st.markdown("</div>", unsafe_allow_html=True)

            # ── Carousel Controls ──
            shuf_c1, shuf_c2 = st.columns(2)
            with shuf_c1:
                if st.button("🎲 Spin Unpinned Rows", key="btn_spin_unpinned", type="primary", use_container_width=True):
                    if not st.session_state.get("lock_top") and not w_tops.empty:
                        st.session_state["carousel_top_idx"] = random.randint(0, len(w_tops) - 1)
                    if not st.session_state.get("lock_bot") and not w_bots.empty:
                        st.session_state["carousel_bot_idx"] = random.randint(0, len(w_bots) - 1)
                    if not st.session_state.get("lock_outer") and not w_outers.empty:
                        st.session_state["carousel_outer_idx"] = random.randint(0, len(w_outers) - 1)
                    if not st.session_state.get("lock_shoe") and available_shoes:
                        st.session_state["carousel_shoe_idx"] = random.randint(0, len(available_shoes) - 1)
                    st.rerun()
            with shuf_c2:
                if st.button("🔓 Unlock All Rows", key="btn_unlock_all", use_container_width=True):
                    st.session_state["lock_top"] = False
                    st.session_state["lock_bot"] = False
                    st.session_state["lock_outer"] = False
                    st.session_state["lock_shoe"] = False
                    st.rerun()

        with d_col2:
            st.markdown("<h4 style='font-family:Playfair Display, serif; color:#1A1412;'>Assembled Flatlay Showcase</h4>", unsafe_allow_html=True)

            active_carousel_items = []
            if active_top_dict:
                active_carousel_items.append(active_top_dict)
            if active_bot_dict:
                active_carousel_items.append(active_bot_dict)
            if active_outer_dict:
                active_carousel_items.append(active_outer_dict)
            if active_shoe_dict:
                active_carousel_items.append(active_shoe_dict)

            if active_carousel_items:
                k_season = profile.get("palette_tier", profile.get("season", "medium_golden"))
                k_skin_score, k_skin_note = score_skin_tone_harmony(active_carousel_items, k_season)
                k_body_score, k_body_note, _ = score_body_silhouette_compatibility(active_carousel_items, profile.get("body_build", "athletic_v_taper"), profile.get("height_profile", "average"))
                c_pair_sc = 80.0
                if active_top_dict and active_bot_dict:
                    c_pair_sc = pair_score(active_top_dict.get("color", ""), active_bot_dict.get("color", ""))
                d_overall = round(c_pair_sc * 0.40 + k_skin_score * 0.35 + k_body_score * 0.25, 1)

                st.markdown(f"""
                <div class="whering-canvas-board">
                    <div style="font-size:12px; font-weight:800; color:#8C3B1E; letter-spacing:0.12em; text-transform:uppercase; margin-bottom:4px;">Assembled Outfit</div>
                    <div style="font-size:32px; font-weight:800; color:#1A1412; font-family:'Playfair Display', serif; margin-bottom:8px;">{int(d_overall)}% HARMONY</div>
                    <div style="display:flex; justify-content:center; gap:10px; margin-bottom:16px;">
                        <span style="font-size:12px; background:#EBF3EA; color:#2D5A27; padding:4px 10px; border-radius:12px; font-weight:700;">Face Radiance: {int(k_skin_score)}%</span>
                        <span style="font-size:12px; background:#F2EFEB; color:#4A453E; padding:4px 10px; border-radius:12px; font-weight:700;">Silhouette: {int(k_body_score)}%</span>
                    </div>
                """, unsafe_allow_html=True)

                # Flatlay garment cutout display
                f_cols = st.columns(len(active_carousel_items))
                for f_idx, fitm in enumerate(active_carousel_items):
                    with f_cols[f_idx]:
                        fp_photo = fitm.get("photo_path")
                        if fp_photo and os.path.exists(str(fp_photo)):
                            st.image(str(fp_photo), use_column_width=True)
                        else:
                            st.markdown(f"<div style='background:{fitm.get('color_hex','#808080')};height:80px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:26px;'>✨</div>", unsafe_allow_html=True)
                        st.markdown(f"<div style='font-size:12.5px; font-weight:700; color:#1A1412; margin-top:6px;'>{fitm.get('color','').title()} {fitm.get('category')}</div>", unsafe_allow_html=True)

                top_name = f"{active_top_dict.get('color','').title()} {active_top_dict.get('category','top')}" if active_top_dict else "Top piece"
                bot_name = f"{active_bot_dict.get('color','').title()} {active_bot_dict.get('category','bottom')}" if active_bot_dict else "Bottom piece"
                if active_top_dict and active_bot_dict:
                    interplay_desc = describe_color_interplay(
                        active_top_dict.get("color", ""),
                        active_bot_dict.get("color", ""),
                        active_top_dict.get("category", "top"),
                        active_bot_dict.get("category", "bottom")
                    )
                elif active_top_dict:
                    interplay_desc = f"Showcasing {top_name}. (Add a bottom piece to analyze pair harmony.)"
                elif active_bot_dict:
                    interplay_desc = f"Showcasing {bot_name}. (Add an upper piece to analyze pair harmony.)"
                else:
                    interplay_desc = "Layer pieces assembled."

                st.markdown(f"""
                    <div style="font-size:13.5px; color:#2E2722; text-align:left; background:#FAF6F3; border-radius:10px; padding:14px; margin-top:16px; line-height:1.55;">
                        🎨 <strong>Color Interplay:</strong> {interplay_desc}<br>
                        💡 <strong>Complexion Note:</strong> {k_skin_note}<br>
                        📐 <strong>Silhouette Proportion:</strong> {k_body_note}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("✨ WEAR THIS ASSEMBLED LOOK", key="btn_wear_dressme_look", type="primary", use_container_width=True):
                    record_wear_confirmation(
                        feedback_id="dress_me_carousel",
                        outfit_id="dress_me_" + str(int(d_overall)),
                        item_ids=[it.get("item_id") for it in active_carousel_items if not str(it.get("item_id")).startswith("staple_")],
                        occasion="Dress Me Custom Pairing",
                        rating=5,
                        notes=f"Selected from Dress Me Studio for {user_name}"
                    )
                    st.success("✨ Saved to wear history! Wardrobe wear counts updated.")
            else:
                st.info("Assemble pieces using the carousels on the left.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: 🎨 INTERACTIVE STYLING CANVAS (ADD UPPER, BOTTOM, JACKET, SHOES, GLASSES)
# ─────────────────────────────────────────────────────────────────────────────
with tab_canvas:
    st.markdown("""
    <div style="background:#FAF6F3; border:1px solid #EBE4DA; border-radius:10px; padding:14px 18px; margin-bottom:18px;">
        <div style="font-size:11.5px; font-weight:800; color:#8C3B1E; text-transform:uppercase; letter-spacing:0.12em;">Interactive Styling Canvas</div>
        <div style="font-size:20px; font-weight:700; color:#1A1412; font-family:'Playfair Display', Georgia, serif; margin:2px 0 4px 0;">Build Your Outfit & See If It Seems Okay</div>
        <div style="font-size:14px; color:#2E2722;">A freeform space where you can add Upper, Bottom, Jacket, Shoes, and Glasses yourself. The board arranges them in a curated flatlay and runs instant compatibility diagnostics to check if the look is balanced before stepping out.</div>
    </div>
    """, unsafe_allow_html=True)

    c_left, c_right = st.columns([1.1, 1.4])

    with c_left:
        st.markdown("<h4 style='font-family:Playfair Display, serif; color:#1A1412;'>Select Outfit Layers</h4>", unsafe_allow_html=True)

        # 1. Upper Slot
        c_top_opts = [None] + w_tops["item_id"].tolist()
        c_sel_top_id = st.selectbox(
            "1. Upper (T-Shirts / Shirts / Sweaters)",
            options=c_top_opts,
            format_func=lambda x: "— None selected —" if not x else f"{w_tops[w_tops['item_id']==x].iloc[0]['color'].title()} {w_tops[w_tops['item_id']==x].iloc[0]['category']} ({w_tops[w_tops['item_id']==x].iloc[0].get('fit', 'Regular')})",
            key="canvas_sel_top"
        )

        # 2. Bottom Slot
        c_bot_opts = [None] + w_bots["item_id"].tolist()
        c_sel_bot_id = st.selectbox(
            "2. Bottom (Trousers / Jeans / Shorts)",
            options=c_bot_opts,
            format_func=lambda x: "— None selected —" if not x else f"{w_bots[w_bots['item_id']==x].iloc[0]['color'].title()} {w_bots[w_bots['item_id']==x].iloc[0]['category']} ({w_bots[w_bots['item_id']==x].iloc[0].get('fit', 'Regular')})",
            key="canvas_sel_bot"
        )

        # 3. Jacket / Layer Slot
        c_outer_opts = [None] + w_outers["item_id"].tolist()
        c_sel_outer_id = st.selectbox(
            "3. Jacket / Layer (Optional)",
            options=c_outer_opts,
            format_func=lambda x: "— None (No Outerwear) —" if not x else f"{w_outers[w_outers['item_id']==x].iloc[0]['color'].title()} {w_outers[w_outers['item_id']==x].iloc[0]['category']}",
            key="canvas_sel_outer"
        )

        # 4. Shoes Slot (Wardrobe shoes + Curated staples)
        c_shoe_items = w_shoes.to_dict("records") + STAPLE_SHOES
        c_shoe_lookup = {it["item_id"]: it for it in c_shoe_items}
        c_shoe_opts = [None] + [it["item_id"] for it in c_shoe_items]
        c_sel_shoe_id = st.selectbox(
            "4. Shoes / Footwear",
            options=c_shoe_opts,
            format_func=lambda x: "— None selected —" if not x else f"{c_shoe_lookup[x].get('brand', c_shoe_lookup[x]['color'].title() + ' ' + c_shoe_lookup[x]['category'])}",
            key="canvas_sel_shoe"
        )

        # 5. Glasses & Accessories Slot (Wardrobe accessories + Curated staples)
        c_acc_items = w_accs.to_dict("records") + STAPLE_ACCESSORIES
        c_acc_lookup = {it["item_id"]: it for it in c_acc_items}
        c_acc_opts = [None] + [it["item_id"] for it in c_acc_items]
        c_sel_acc_id = st.selectbox(
            "5. Glasses & Accessories",
            options=c_acc_opts,
            format_func=lambda x: "— None selected —" if not x else f"{c_acc_lookup[x].get('brand', c_acc_lookup[x]['color'].title() + ' ' + c_acc_lookup[x]['category'])}",
            key="canvas_sel_acc"
        )

    with c_right:
        st.markdown("<h4 style='font-family:Playfair Display, serif; color:#1A1412;'>Styling Canvas Flatlay</h4>", unsafe_allow_html=True)

        canvas_items = []
        if c_sel_top_id:
            canvas_items.append(wardrobe_df[wardrobe_df["item_id"] == c_sel_top_id].iloc[0].to_dict())
        if c_sel_bot_id:
            canvas_items.append(wardrobe_df[wardrobe_df["item_id"] == c_sel_bot_id].iloc[0].to_dict())
        if c_sel_outer_id:
            canvas_items.append(wardrobe_df[wardrobe_df["item_id"] == c_sel_outer_id].iloc[0].to_dict())
        if c_sel_shoe_id:
            canvas_items.append(c_shoe_lookup[c_sel_shoe_id])
        if c_sel_acc_id:
            canvas_items.append(c_acc_lookup[c_sel_acc_id])

        if canvas_items:
            k_season = profile.get("palette_tier", profile.get("season", "medium_golden"))
            c_skin_sc, c_skin_nt = score_skin_tone_harmony(canvas_items, k_season)
            c_body_sc, c_body_nt, _ = score_body_silhouette_compatibility(canvas_items, profile.get("body_build", "athletic_v_taper"), profile.get("height_profile", "average"))

            c_c_score = 80.0
            if len(canvas_items) >= 2:
                p_scores = [pair_score(canvas_items[i].get("color",""), canvas_items[j].get("color",""))
                            for i in range(len(canvas_items)) for j in range(i+1, len(canvas_items))]
                c_c_score = sum(p_scores) / max(len(p_scores), 1)

            c_total = round(c_c_score * 0.40 + c_skin_sc * 0.35 + c_body_sc * 0.25, 1)

            st.markdown(f"""
            <div class="whering-canvas-board">
                <div style="font-size:12px; font-weight:800; color:#8C3B1E; letter-spacing:0.12em; text-transform:uppercase; margin-bottom:4px;">Assembled Canvas</div>
                <div style="font-size:32px; font-weight:800; color:#1A1412; font-family:'Playfair Display', serif; margin-bottom:8px;">{int(c_total)}% HARMONY</div>
                <div style="display:flex; justify-content:center; gap:10px; margin-bottom:18px;">
                    <span style="font-size:12px; background:#EBF3EA; color:#2D5A27; padding:4px 10px; border-radius:12px; font-weight:700;">Face Harmony: {int(c_skin_sc)}%</span>
                    <span style="font-size:12px; background:#F2EFEB; color:#4A453E; padding:4px 10px; border-radius:12px; font-weight:700;">Silhouette: {int(c_body_sc)}%</span>
                </div>
            """, unsafe_allow_html=True)

            # Display apparel flatlay arranged cleanly
            can_cols = st.columns(len(canvas_items))
            for c_i, c_itm in enumerate(canvas_items):
                with can_cols[c_i]:
                    cp_p = c_itm.get("photo_path")
                    if cp_p and os.path.exists(str(cp_p)):
                        st.image(str(cp_p), use_column_width=True)
                    else:
                        st.markdown(f"<div style='background:{c_itm.get('color_hex','#808080')};height:80px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:24px;'>✨</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size:12px; font-weight:700; color:#1A1412; margin-top:6px;'>{c_itm.get('color','').title()} {c_itm.get('category')}</div>", unsafe_allow_html=True)

            # Diagnostic evaluation: "See if it seems okay"
            verdict_text = "✨ EXCELLENT BALANCE — Colors and silhouette flatter your frame." if c_total >= 85 else "👍 GOOD CASUAL HARMONY — Comfortable and cohesive everyday look." if c_total >= 70 else "💡 CONTRAST ADJUSTMENT SUGGESTED — Consider balancing the color contrast between layers."
            st.markdown(f"""
                <div style="font-size:13.5px; color:#2E2722; text-align:left; background:#FAF6F3; border-radius:10px; padding:14px; margin-top:16px; line-height:1.55;">
                    <strong>Evaluation:</strong> {verdict_text}<br><br>
                    💡 <strong>Complexion Radiance:</strong> {c_skin_nt}<br>
                    📐 <strong>Body Silhouette:</strong> {c_body_nt}
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("✨ WEAR THIS CANVAS LOOK", key="btn_wear_canvas_look", type="primary", use_container_width=True):
                real_ids = [it.get("item_id") for it in canvas_items if not str(it.get("item_id")).startswith("staple_")]
                record_wear_confirmation(
                    feedback_id="canvas_custom",
                    outfit_id="canvas_" + str(int(c_total)),
                    item_ids=real_ids,
                    occasion="Custom Canvas Look",
                    rating=5,
                    notes=f"Created on Styling Canvas for {user_name}"
                )
                st.success("✨ Look logged into wear history!")
        else:
            st.markdown("""
            <div class="whering-canvas-board">
                <div style="font-size:42px; margin-bottom:10px;">🎨</div>
                <div style="font-size:18px; font-weight:700; color:#1A1412;">Canvas Empty</div>
                <div style="font-size:13.5px; color:#5A524A; margin-top:6px;">Select pieces on the left (Upper, Bottom, Jacket, Shoes, Glasses) to assemble your outfit on this flatlay board.</div>
            </div>
            """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: 🎲 ELOQUENT AI SELECTION (CLUELESS SHUFFLE)
# ─────────────────────────────────────────────────────────────────────────────
with tab_eloquent:
    st.markdown("""
    <div style="background:#FAF6F3; border:1px solid #EBE4DA; border-radius:10px; padding:14px 18px; margin-bottom:18px;">
        <div style="font-size:11.5px; font-weight:800; color:#8C3B1E; text-transform:uppercase; letter-spacing:0.12em;">Eloquent AI Stylist</div>
        <div style="font-size:20px; font-weight:700; color:#1A1412; font-family:'Playfair Display', Georgia, serif; margin:2px 0 4px 0;">Random but Eloquent Outfit Curation</div>
        <div style="font-size:14px; color:#2E2722;">Behind the scenes, the AI uses temperature-weighted sampling over color harmony, skin tone radiance, and body proportions. It is not rigidly locked to data, giving you fresh, aesthetic, and eloquent outfit formulas.</div>
    </div>
    """, unsafe_allow_html=True)

    eq_col1, eq_col2 = st.columns([1, 1.4])

    with eq_col1:
        st.markdown("<h4 style='font-family:Playfair Display, serif; color:#1A1412;'>AI Styling Controls</h4>", unsafe_allow_html=True)
        eq_temp = st.slider("Styling Creativity (Temperature)", 0.4, 1.0, 0.75, 0.05,
                            help="Lower values favor traditional classic harmony; higher values introduce artistic, fashion-forward contrast.")
        eq_occ = st.selectbox("Occasion Target", OCCASIONS, index=0, key="eq_occasion_sel")

        # Check if user has locked items from carousel
        locked_dict = {}
        if st.session_state.get("lock_top") and not w_tops.empty:
            locked_dict["tops"] = w_tops.iloc[st.session_state["carousel_top_idx"]]["item_id"]
        if st.session_state.get("lock_bot") and not w_bots.empty:
            locked_dict["bottoms"] = w_bots.iloc[st.session_state["carousel_bot_idx"]]["item_id"]

        if locked_dict:
            st.caption("📌 Active Locks from Dress Me carousel will be respected during shuffle.")

        if st.button("🎲 SHUFFLE OUTFIT (Eloquent AI Mode)", key="btn_eloquent_shuffle", type="primary", use_container_width=True):
            generated_look = generate_eloquent_shuffle_outfit(
                wardrobe_df,
                profile,
                locked_items=locked_dict,
                occasion=eq_occ,
                temperature=eq_temp
            )
            st.session_state["eloquent_look"] = generated_look

    with eq_col2:
        st.markdown("<h4 style='font-family:Playfair Display, serif; color:#1A1412;'>AI Curation Flatlay</h4>", unsafe_allow_html=True)
        curated_look = st.session_state.get("eloquent_look")

        if curated_look:
            c_items = curated_look["items"]
            st.markdown(f"""
            <div class="whering-canvas-board">
                <div style="font-size:12px; font-weight:800; color:#8C3B1E; letter-spacing:0.12em; text-transform:uppercase; margin-bottom:4px;">Eloquent AI Selection</div>
                <div style="font-size:32px; font-weight:800; color:#1A1412; font-family:'Playfair Display', serif; margin-bottom:6px;">{curated_look['total_score']}% HARMONY</div>
                <div style="font-size:16px; font-weight:700; color:#4A352B; margin-bottom:14px;">{curated_look['formula_tag']}</div>
                <div style="display:flex; justify-content:center; gap:10px; margin-bottom:18px;">
                    <span style="font-size:12px; background:#EBF3EA; color:#2D5A27; padding:4px 10px; border-radius:12px; font-weight:700;">Face Radiance: {curated_look['skin_score']}%</span>
                    <span style="font-size:12px; background:#F2EFEB; color:#4A453E; padding:4px 10px; border-radius:12px; font-weight:700;">Silhouette: {curated_look['body_score']}%</span>
                </div>
            """, unsafe_allow_html=True)

            c_cols = st.columns(len(c_items))
            for ci_idx, ci_itm in enumerate(c_items):
                with c_cols[ci_idx]:
                    cp = ci_itm.get("photo_path")
                    if cp and os.path.exists(str(cp)):
                        st.image(str(cp), use_column_width=True)
                    else:
                        st.markdown(f"<div style='background:{ci_itm.get('color_hex','#808080')};height:80px;border-radius:8px;'></div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size:12.5px; font-weight:700; color:#1A1412; margin-top:6px;'>{ci_itm.get('color','').title()} {ci_itm.get('category')}</div>", unsafe_allow_html=True)

            st.markdown(f"""
                <div style="font-size:14px; color:#2E2722; text-align:left; background:#FAF6F3; border-radius:10px; padding:16px; margin-top:16px; line-height:1.6;">
                    🖋️ <strong>Editorial Rationale:</strong> {curated_look['eloquent_desc']}<br><br>
                    📐 <strong>Proportions:</strong> {curated_look['body_note']}
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("✨ WEAR THIS ELOQUENT LOOK", key="btn_wear_eloquent_look", type="primary", use_container_width=True):
                record_wear_confirmation(
                    feedback_id="eloquent_ai",
                    outfit_id="eloquent_" + str(int(curated_look['total_score'])),
                    item_ids=[it.get("item_id") for it in c_items],
                    occasion=eq_occ,
                    rating=5,
                    notes=f"Generated by Eloquent AI for {user_name}"
                )
                st.success("✨ Saved to wear history! Wardrobe wear counts updated.")
        else:
            st.markdown("""
            <div class="whering-canvas-board">
                <div style="font-size:42px; margin-bottom:10px;">🎲</div>
                <div style="font-size:18px; font-weight:700; color:#1A1412;">Ready to Shuffle</div>
                <div style="font-size:13.5px; color:#5A524A; margin-top:6px;">Click <strong>🎲 SHUFFLE OUTFIT</strong> to let the AI curate an aesthetic, harmonious combination behind the scenes.</div>
            </div>
            """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4: 🧥 WARDROBE & CUTOUTS (INVENTORY GALLERY & PIECE PAIRING)
# ─────────────────────────────────────────────────────────────────────────────
with tab_inventory:
    f_col1, f_col2 = st.columns([3, 2])

    with f_col1:
        type_options = ["ALL", "TOPS", "BOTTOMS", "LAYERS", "SHOES"]
        selected_type = st.radio(
            "Garment Type",
            type_options,
            horizontal=True,
            label_visibility="collapsed",
            key="type_filter"
        )

    with f_col2:
        palette_options = ["ALL PALETTE", "BEST MATCHES", "ADD WARMTH", "STAPLES"]
        selected_palette = st.radio(
            "Color Guidance",
            palette_options,
            horizontal=True,
            label_visibility="collapsed",
            key="palette_filter"
        )

    filtered_df = wardrobe_df.copy()

    if selected_type == "TOPS":
        filtered_df = filtered_df[filtered_df["category"].isin(CATEGORY_GROUP.get("tops", []))]
    elif selected_type == "BOTTOMS":
        filtered_df = filtered_df[filtered_df["category"].isin(CATEGORY_GROUP.get("bottoms", []))]
    elif selected_type == "LAYERS":
        filtered_df = filtered_df[filtered_df["category"].isin(CATEGORY_GROUP.get("outer", []))]
    elif selected_type == "SHOES":
        filtered_df = filtered_df[filtered_df["category"].isin(CATEGORY_GROUP.get("footwear", []))]

    if selected_palette != "ALL PALETTE" and not filtered_df.empty:
        keep_indices = []
        target_badge = "BEST MATCH" if selected_palette == "BEST MATCHES" else "ADD WARMTH" if selected_palette == "ADD WARMTH" else "STAPLE"
        for idx, row in filtered_df.iterrows():
            b = get_garment_palette_badge(row.get("color", ""), active_palette_key)
            if b["badge"] == target_badge:
                keep_indices.append(idx)
        filtered_df = filtered_df.loc[keep_indices]

    st.markdown("<br>", unsafe_allow_html=True)

    if filtered_df.empty:
        if wardrobe_df.empty:
            st.markdown(f"""
            <div style="background: #FFFFFF; border: 1.5px dashed #D5C7B8; border-radius: 14px; padding: 36px 24px; text-align: center; margin: 16px 0;">
                <div style="font-size: 36px; margin-bottom: 8px;">🧥✨</div>
                <div style="font-family: 'Playfair Display', Georgia, serif; font-size: 20px; font-weight: 700; color: #241C18; margin-bottom: 6px;">
                    Wardrobe Zero — Clean Slate
                </div>
                <div style="font-size: 14px; color: #704E38; max-width: 480px; margin: 0 auto 16px auto; line-height: 1.5;">
                    Your collection starts empty at 0 items. Click <strong>+ ADD A PIECE</strong> above to scan clothes with automatic transparent background cutout.
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No garments match the active filter.")
    else:
        cols = st.columns(4)
        for i, (_, row) in enumerate(filtered_df.iterrows()):
            col = cols[i % 4]
            with col:
                color = row.get("color", "")
                cat   = row.get("category", "")
                badge = get_garment_palette_badge(color, active_palette_key)
                badge_class = "badge-best" if badge["badge"] == "BEST MATCH" else "badge-warmth" if badge["badge"] == "ADD WARMTH" else "badge-staple"

                photo = row.get("photo_path")
                has_photo = photo and os.path.exists(str(photo))

                st.markdown(f"""
                <div class="garment-tile">
                    <span class="{badge_class}">{badge['badge']}</span>
                    <div style="font-size:16px; font-weight:700; margin-top:8px; color:#1A1412 !important;">{row.get('brand', '')} {cat}</div>
                    <div style="font-size:13.5px; color:#2E2722 !important;">Color: <strong style="color:#1A1412 !important;">{color}</strong> · Fit: {row.get('fit', 'Regular')}</div>
                    <div style="font-size:12px; color:#8C3B1E !important; font-weight:600; margin-top:4px;">Worn: {row.get('times_worn', 0)} times</div>
                </div>
                """, unsafe_allow_html=True)

                if has_photo:
                    st.image(photo, use_column_width=True)

                if st.button(f"🔍 Inspect & Pair", key=f"pair_btn_{row['item_id']}", use_container_width=True):
                    st.session_state["selected_piece_id"] = row["item_id"]
                    st.rerun()

    # Inspect & Pair Drawer
    if "selected_piece_id" in st.session_state and st.session_state["selected_piece_id"]:
        target_id = st.session_state["selected_piece_id"]
        target_rows = wardrobe_df[wardrobe_df["item_id"] == target_id]

        if not target_rows.empty:
            target = target_rows.iloc[0].to_dict()
            season_curr = profile.get("season", "Autumn")
            p_badge = get_garment_palette_badge(target.get("color", ""), season_curr)

            st.markdown("---")
            st.markdown(f"<h3 style='font-family:Playfair Display, serif;'>Piece Details · {target.get('color')} {target.get('category')}</h3>", unsafe_allow_html=True)

            d_col1, d_col2 = st.columns([1, 1])

            with d_col1:
                photo = target.get("photo_path")
                if photo and os.path.exists(str(photo)):
                    st.image(photo, width=380)
                else:
                    st.markdown(f"""
                    <div style="background:#F6F1EA; border:1px solid #E5DED4; border-radius:10px; padding:40px; text-align:center;">
                        <div style="font-size:48px;">👕</div>
                        <div style="font-size:22px; font-weight:700; margin-top:10px; color:#1A1412 !important;">{target.get('category')}</div>
                        <div style="font-size:14.5px; color:#2E2722 !important; font-weight:500;">{target.get('color')} · Fit: {target.get('fit', 'Regular')}</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown(f"""
                <div style="margin-top:16px; background:#FFFFFF; border:1px solid #EBE4DA; border-left:4px solid #8C3B1E; border-radius:6px; padding:16px;">
                    <div style="font-size:12px; font-weight:700; color:#8C3B1E !important; text-transform:uppercase; letter-spacing:0.05em;">Colour Guidance for Him</div>
                    <div style="font-size:15px; color:#1A1412 !important; font-weight:700; margin-top:6px;">
                        {p_badge['badge']} for his {palette_data['name']} profile.
                    </div>
                    <div style="font-size:14px; color:#2E2722 !important; margin-top:6px; line-height:1.5;">
                        {p_badge['text']} {palette_data.get('complementary_suggestions', '')}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with d_col2:
                st.markdown("""
                <div style="font-size: 20px; font-weight: 700; color: #1A1412 !important; margin-bottom: 4px;">
                    Pair with
                </div>
                <div style="font-size: 14px; color: #2E2722 !important; margin-bottom: 10px;">
                    Ranked by color harmony, silhouette balance, and seasonal palette.
                </div>
                """, unsafe_allow_html=True)

                style_filter = st.selectbox(
                    "Style for",
                    ["ALL", "CASUAL", "WORK", "DINNER", "OCCASION"],
                    key="pair_style_filter"
                )

                pairings = get_pairings_for_garment(
                    garment=target,
                    wardrobe_df=wardrobe_df,
                    style_filter=style_filter,
                    season=season_curr,
                    limit=4
                )

                if pairings:
                    for pair in pairings:
                        it = pair["item"]
                        st.markdown(f"""
                        <div style="background:#FFFFFF; border:1px solid #EBE4DA; border-radius:8px; padding:14px; margin-bottom:10px;">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <strong style="font-size:14px; color:#241C18;">{it.get('color')} {it.get('category')}</strong>
                                <span style="font-size:12px; font-weight:700; color:#2D5A27;">{pair['match_percentage']}% MATCH</span>
                            </div>
                            <div style="font-size:13px; color:#5A5148; margin-top:6px; line-height:1.4;">
                                {pair['explanation']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("Add more garments to see pairing suggestions.")

            if st.button("Close Piece Details"):
                st.session_state["selected_piece_id"] = None
                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# TAB 5: 📅 MOOD & OUTFIT PLANNER (PROMPT STYLIST, PACKING CAPSULES & LOOKBOOKS)
# ─────────────────────────────────────────────────────────────────────────────
with tab_planner:
    # Hero Banner
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #4A352B 0%, #36261E 100%) !important; border: 1px solid #5C4336 !important; border-radius: 14px; padding: 36px 42px; margin-bottom: 26px; box-shadow: 0 8px 30px rgba(74, 53, 43, 0.18);">
        <div style="color: #EBDCCE !important; font-size: 12.5px; font-weight: 700; letter-spacing: 0.16em; text-transform: uppercase; margin-bottom: 8px;">
            Ask {user_name}'s Wardrobe
        </div>
        <div style="font-family: 'Playfair Display', Georgia, serif; font-size: 38px; font-weight: 700; color: #FFFFFF !important; line-height: 1.15; margin: 0 0 10px 0; text-shadow: 0 2px 10px rgba(0,0,0,0.35);">
            What should {pronoun_subject} wear?
        </div>
        <div style="font-size: 15.5px; color: #F7EFE9 !important; font-weight: 500; line-height: 1.5; margin: 0;">
            Describe the plan and the mood. I'll use only pieces you own, tailored to {pronoun_possessive} complexion and silhouette.
        </div>
    </div>
    """, unsafe_allow_html=True)

    input_col, btn_col = st.columns([5, 1])

    if "user_plan_prompt" not in st.session_state:
        st.session_state["user_plan_prompt"] = ""

    with input_col:
        user_prompt = st.text_input(
            f"{pronoun_possessive.title()} Plans",
            placeholder=f"Dinner with friends, polished but comfortable for {user_name}...",
            value=st.session_state.get("user_plan_prompt", ""),
            label_visibility="collapsed",
            key="main_plan_input"
        )

    with btn_col:
        show_me_btn = st.button("SHOW ME", type="primary", use_container_width=True)

    # Quick suggestions
    st.markdown("<div style='font-size:12px; color:#786F66; margin-bottom:8px;'><strong>Quick suggestions:</strong></div>", unsafe_allow_html=True)
    pill_cols = st.columns(len(PRESET_PLANS))
    for i, plan in enumerate(PRESET_PLANS):
        with pill_cols[i]:
            if st.button(plan["label"], key=f"pill_{plan['id']}", use_container_width=True):
                st.session_state["user_plan_prompt"] = plan["prompt"]
                st.rerun()

    active_prompt = user_prompt.strip()

    if show_me_btn or active_prompt:
        plan_info = parse_plan_and_mood(active_prompt)

        # Check if packing mode requested
        if plan_info.get("is_packing"):
            st.subheader(f"🧳 Packing Mode · {plan_info.get('days', 3)} Days")
            st.caption(f"Where and when? Checking weather for **{plan_info.get('destination', 'His Trip')}**, reusing a compact capsule.")

            capsule = generate_packing_capsule(
                destination=plan_info.get("destination", "Trip"),
                days=plan_info.get("days", 3),
                wardrobe_df=wardrobe_df,
                season=active_palette_key
            )

            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown("#### 🧥 Reusable Capsule Pieces")
                for it in capsule["capsule_items"]:
                    badge = get_garment_palette_badge(it.get("color", ""), active_palette_key)
                    st.markdown(f"""
                    <div class="garment-tile">
                        <strong>{it.get('category')}</strong> · {it.get('color')}<br>
                        <span class="{'badge-best' if badge['badge']=='BEST MATCH' else 'badge-warmth'}">{badge['badge']}</span>
                    </div>
                    """, unsafe_allow_html=True)

            with c2:
                st.markdown("#### 📅 Day-by-Day Itinerary Combinations")
                for day_plan in capsule["itinerary"]:
                    with st.container():
                        st.markdown(f"**{day_plan['title']}**")
                        st.caption(day_plan["note"])
                        d_cols = st.columns(3)
                        if day_plan.get("top"):
                            d_cols[0].markdown(f"👕 **Top:** {day_plan['top'].get('color')} {day_plan['top'].get('category')}")
                        if day_plan.get("bottom"):
                            d_cols[1].markdown(f"👖 **Bottom:** {day_plan['bottom'].get('color')} {day_plan['bottom'].get('category')}")
                        if day_plan.get("shoe"):
                            d_cols[2].markdown(f"👟 **Footwear:** {day_plan['shoe'].get('color')} {day_plan['shoe'].get('category')}")
                        st.divider()
        else:
            editorial_cards = generate_editorial_recommendations(
                wardrobe_df=wardrobe_df,
                plan_info=plan_info,
                profile=profile,
            )

            st.markdown(f"<h3 style='font-family:Playfair Display, serif; font-size:24px; font-weight:700; color:#1A1412 !important;'>3 INVENTORY-ONLY IDEAS FOR {plan_info.get('plan_title', 'HIS PLANS').upper()}</h3>", unsafe_allow_html=True)
            st.markdown(
                f"<div style='font-size:14.5px; color:#2E2722 !important; font-weight:500; margin-bottom:14px;'>"
                f"Curated for <strong style='color:#1A1412;'>{user_name}</strong> · "
                f"<strong>Face Criteria:</strong> {palette_info['name']} ({profile.get('undertone', 'Golden Amber')} undertone) · "
                f"<strong>Body Criteria:</strong> {build_data['name']} Silhouette"
                f"</div>",
                unsafe_allow_html=True
            )

            if editorial_cards:
                card_cols = st.columns(3)
                for idx, card in enumerate(editorial_cards):
                    with card_cols[idx]:
                        face_s = card.get("face_score", 90)
                        body_s = card.get("body_score", 90)

                        st.markdown(f"""
                        <div class="garment-tile" style="border: 2px solid #D5CFC7; border-radius: 14px; padding: 18px;">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                                <span style="font-size:11px; font-weight:800; color:#8C3B1E; letter-spacing:0.1em; text-transform:uppercase;">{card['card_type']}</span>
                                <span style="font-size:15px; font-weight:800; color:#1A1412;">{card['match_percentage']}% MATCH</span>
                            </div>
                            <div style="display:flex; gap:8px; margin-bottom:12px;">
                                <span class="badge-best">Face: {face_s}%</span>
                                <span class="badge-staple">Silhouette: {body_s}%</span>
                            </div>
                        """, unsafe_allow_html=True)

                        g_cols = st.columns(len(card["items"]))
                        for g_idx, g_item in enumerate(card["items"]):
                            with g_cols[g_idx]:
                                photo = g_item.get("photo_path")
                                if photo and os.path.exists(photo):
                                    st.image(photo, use_column_width=True)
                                else:
                                    st.markdown(f"<div style='background:{g_item.get('color_hex','#808080')};height:60px;border-radius:6px;'></div>", unsafe_allow_html=True)
                                st.markdown(f"<div style='font-size:11px; font-weight:600; text-align:center; color:#1A1412;'>{g_item.get('color')} {g_item.get('category')}</div>", unsafe_allow_html=True)

                        st.markdown(f"""
                            <div style="font-size:13px; color:#2E2722; margin-top:12px; line-height:1.5;">
                                {card.get('explanation', '')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        if st.button("✨ Wear This Look", key=f"wear_planner_{idx}", use_container_width=True):
                            record_wear_confirmation(
                                feedback_id=f"plan_{idx}",
                                outfit_id=f"plan_outfit_{idx}",
                                item_ids=card["raw_outfit"].get("item_ids", []),
                                occasion=plan_info.get("occasion", "Casual"),
                                rating=5,
                                notes=f"Selected from Outfit Planner for {user_name}"
                            )
                            st.success("✨ Saved to wear history!")
            else:
                st.info("No outfits match your closet criteria yet. Add more pieces!")

    st.markdown("---")

    # MadWitch Lookbooks Section
    st.markdown("<h3 style='font-family:Playfair Display, serif; color:#1A1412;'>✨ MadWitch Style Lookbook Collections</h3>", unsafe_allow_html=True)
    drop_labels = [d["name"] for d in LOOKBOOK_DROPS]
    selected_drop_name = st.radio(
        "Select Lookbook Drop",
        drop_labels,
        horizontal=True,
        label_visibility="collapsed",
        key="selected_lookbook_drop"
    )
    active_drop_id = next(d["id"] for d in LOOKBOOK_DROPS if d["name"] == selected_drop_name)
    showcase_data = generate_lookbook_showcase(wardrobe_df, profile, drop_id=active_drop_id)
    drop_meta = showcase_data["active_drop"]
    hero_look = showcase_data.get("hero_look")

    st.markdown(f"""
    <div style="background:#FAF6F3; border:1px solid #EBE4DA; border-left:4px solid #8C3B1E; border-radius:8px; padding:16px 20px; margin:16px 0 22px 0;">
        <div style="font-size:12px; font-weight:700; color:#8C3B1E; text-transform:uppercase; letter-spacing:0.12em;">{drop_meta['badge']}</div>
        <div style="font-size:22px; font-weight:700; color:#1A1412; font-family:'Playfair Display', Georgia, serif; margin:4px 0 4px 0;">{drop_meta['name']}</div>
        <div style="font-size:14.5px; color:#2E2722; font-weight:500;">{drop_meta['tagline']}</div>
    </div>
    """, unsafe_allow_html=True)

    if hero_look:
        h_c1, h_c2 = st.columns([1.5, 1])
        with h_c1:
            st.markdown(f"""
            <div style="background:#FFFFFF; border:1.5px solid #D5CFC7; border-radius:14px; padding:20px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; border-bottom:1px solid #F0EAE1; padding-bottom:10px;">
                    <span style="font-size:12px; font-weight:800; color:#8C3B1E; text-transform:uppercase;">HERO LOOK</span>
                    <span style="font-size:16px; font-weight:800; color:#8C3B1E;">{hero_look['match_score']}% CURATED MATCH</span>
                </div>
            """, unsafe_allow_html=True)

            p_cols = st.columns(len(hero_look["items"]))
            for p_idx, itm in enumerate(hero_look["items"]):
                with p_cols[p_idx]:
                    p_photo = itm.get("photo_path")
                    if p_photo and os.path.exists(str(p_photo)):
                        st.image(p_photo, use_column_width=True)
                    else:
                        st.markdown(f"<div style='background:{itm.get('color_hex','#808080')};height:70px;border-radius:8px;'></div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size:12px; font-weight:700; text-align:center;'>{itm.get('color')} {itm.get('category')}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with h_c2:
            st.markdown(f"""
            <div style="background:#FFFFFF; border:1.5px solid #D5CFC7; border-radius:14px; padding:22px; height:100%;">
                <div style="font-size:13px; font-weight:700; color:#8C3B1E; text-transform:uppercase; margin-bottom:6px;">Formula Analysis</div>
                <div style="font-size:18px; font-weight:700; color:#1A1412; margin-bottom:8px;">{hero_look['formula_tag']}</div>
                <div style="font-size:14px; color:#2E2722; line-height:1.6; margin-bottom:14px;">
                    {hero_look['skin_note']}<br><br>
                    <strong>Proportions:</strong> {hero_look['body_note']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("✨ Wear This Hero Look", key=f"wear_hero_{active_drop_id}", type="primary", use_container_width=True):
                record_wear_confirmation(
                    feedback_id="lookbook_hero",
                    outfit_id="hero_" + active_drop_id,
                    item_ids=hero_look["raw_outfit"].get("item_ids", []),
                    occasion=drop_meta["name"],
                    rating=5,
                    notes=f"Selected from {drop_meta['name']}"
                )
                st.success("✨ Saved to wear history!")
    else:
        st.info(f"No complete outfits in your closet match {drop_meta['name']} yet.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 6: 👤 PROFILE CALIBRATION (WEARER SWITCHER, 24 SHADES & BODY BLUEPRINT)
# ─────────────────────────────────────────────────────────────────────────────
with tab_profile:
    st.markdown("""
    <div style="background:#FFFFFF; border:1.5px solid #D5CFC7; border-radius:10px; padding:16px 20px; margin-bottom:20px;">
        <div style="font-size:16px; font-weight:700; color:#1A1412 !important; margin-bottom:6px;">
            👤 Change Wearer Name & Pronouns (For You or Anyone Beside You):
        </div>
        <div style="font-size:13.5px; color:#3A322D !important; margin-bottom:10px;">
            Type any name below to personalize the wardrobe title, outfit recommendations, and pronouns instantly.
        </div>
    """, unsafe_allow_html=True)

    w_c1, w_c2, w_c3 = st.columns([3, 2, 1.2])
    with w_c1:
        inp_name = st.text_input("Wearer / Person Name", value=user_name, key="profile_wearer_name_input")
    with w_c2:
        curr_g_idx = 0 if user_gender in ["Boy", "Him", "Male"] else 1 if user_gender in ["Girl", "Her", "Female"] else 2
        inp_gender = st.selectbox("Pronouns / Gender", ["Boy (He/Him)", "Girl (She/Her)", "Non-binary (They/Them)"], index=curr_g_idx, key="profile_wearer_gender_input")
    with w_c3:
        st.write("")
        st.write("")
        save_name_btn = st.button("💾 UPDATE", type="primary", key="save_wearer_name_btn", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    res_gender = "Boy" if "Boy" in inp_gender else "Girl" if "Girl" in inp_gender else "Non-binary"
    if save_name_btn or (inp_name.strip() and inp_name.strip() != user_name) or (res_gender != user_gender):
        profile["name"] = inp_name.strip() if inp_name.strip() else "BUDZ"
        profile["gender"] = res_gender
        save_profile(profile)
        st.rerun()

    t_face, t_body = st.tabs(["🎨 24-Shade Complexion & Color Palette", "🏋️ Body Build & Silhouette Blueprint"])

    with t_face:
        f_left, f_right = st.columns([1, 1])

        with f_left:
            st.markdown("""
            <div style="font-size: 19px; font-weight: 700; color: #1A1412 !important; margin-bottom: 4px;">
                1. Scan Face for Automatic Shade Detection
            </div>
            <div style="font-size: 14.5px; color: #2E2722 !important; font-weight: 500; margin-bottom: 12px; line-height: 1.5;">
                Upload a face photo or take a portrait. The diagnostic engine isolates skin chrominance and matches your exact shade among the 24 foundation tones.
            </div>
            """, unsafe_allow_html=True)

            face_file = st.file_uploader("Upload Face Photo / Portrait", type=["jpg", "jpeg", "png", "webp"], key="face_uploader_diag")
            camera_face = st.camera_input("Or take a quick portrait with camera", key="camera_selfie_diag")

            active_photo = face_file or camera_face
            if active_photo:
                try:
                    img_bytes = active_photo.getvalue()
                    analysis = analyze_face_image(img_bytes)

                    st.session_state["last_face_analysis"] = analysis
                    profile["skin_hex"]          = analysis["skin_hex"]
                    profile["skin_tone_id"]      = analysis.get("shade_id", "shade_15")
                    profile["skin_tone_label"]   = analysis["skin_tone_label"]
                    profile["palette_tier"]      = analysis["palette_tier"]
                    profile["palette_tier_label"]= analysis["palette_tier_label"]
                    profile["season"]            = analysis["season"]
                    profile["undertone"]         = analysis["undertone"]
                    profile["contrast_level"]    = analysis.get("contrast_level", "Medium Contrast")
                    save_profile(profile)
                    st.success(f"Matched to {analysis['skin_tone_label']} ({analysis['palette_tier_label']})!")
                except Exception as e:
                    st.warning(f"Could not analyze image: {e}")

            st.markdown("""
            <div style="font-size: 19px; font-weight: 700; color: #1A1412 !important; margin-top: 18px; margin-bottom: 4px;">
                2. Or Pick Your Exact Shade from the 24 Foundation Swatches
            </div>
            <div style="font-size: 14.5px; color: #2E2722 !important; font-weight: 500; margin-bottom: 8px;">
                Matches the 24-shade foundation chart ranging from Fair Porcelain (Shade 01) to Deep Obsidian Ebony (Shade 24).
            </div>
            """, unsafe_allow_html=True)

            all_shade_keys = sorted(list(SHADES_24.keys()), key=lambda k: SHADES_24[k]["shade_num"])
            curr_shade_id = profile.get("skin_tone_id", "shade_15")
            if curr_shade_id not in all_shade_keys:
                curr_shade_id = "shade_15"
            curr_shade_idx = all_shade_keys.index(curr_shade_id)

            selected_shade_id = st.selectbox(
                "24 Foundation Shades",
                all_shade_keys,
                index=curr_shade_idx,
                format_func=lambda k: f"{SHADES_24[k]['name']} ({SHADES_24[k]['undertone']})",
                key="shade_24_selector"
            )

            if selected_shade_id != profile.get("skin_tone_id"):
                s_info = SHADES_24[selected_shade_id]
                p_tier = COMPLEXION_PALETTES[s_info["tier"]]
                profile["skin_tone_id"]      = selected_shade_id
                profile["skin_tone_label"]   = s_info["name"]
                profile["skin_hex"]          = s_info["hex"]
                profile["palette_tier"]      = s_info["tier"]
                profile["palette_tier_label"]= p_tier["name"]
                profile["season"]            = s_info["tier"]
                profile["undertone"]         = s_info["undertone"]
                save_profile(profile)
                if "last_face_analysis" in st.session_state:
                    del st.session_state["last_face_analysis"]
                st.rerun()

        with f_right:
            st.markdown("""
            <div style="font-size: 19px; font-weight: 700; color: #1A1412 !important; margin-bottom: 8px;">
                Active Face Palette Diagnostic
            </div>
            """, unsafe_allow_html=True)

            p_info = resolve_palette(profile.get("palette_tier", "medium_golden"))
            st.markdown(f"""
            <div class="diagnostic-box">
                <div style="display:flex; align-items:center; gap:12px; margin-bottom:12px;">
                    <div style="width:38px; height:38px; border-radius:50%; background-color:{profile.get('skin_hex', '#A7714C')}; border:2.5px solid #1A1412;"></div>
                    <div>
                        <strong style="font-size:18px; color:#1A1412 !important; display:block;">{profile.get('skin_tone_label', 'Shade 15')}</strong>
                        <span style="font-size:14px; font-weight:600; color:#2E2722 !important;">Palette: <strong style="color:#1A1412;">{p_info.get('name', 'Medium Golden')}</strong> · {profile.get('undertone', 'Golden Amber')}</span>
                    </div>
                </div>
                <div style="font-size:14px; line-height:1.8;">
                    <strong style="color:#164E12 !important;">✨ Power Colors for Face:</strong> <span style="color:#1A1412 !important;">{', '.join(p_info.get('power_colors', []))}</span><br>
                    <strong style="color:#1A1412 !important;">⚓ Staple Neutrals:</strong> <span style="color:#1A1412 !important;">{', '.join(p_info.get('neutrals', []))}</span><br>
                    <strong style="color:#8A1E0B !important;">🚫 Washout Colors (Avoid):</strong> <span style="color:#1A1412 !important;">{', '.join(p_info.get('avoid_near_face', []))}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with t_body:
        b_left, b_right = st.columns([1, 1])

        with b_left:
            st.markdown("""
            <div style="font-size: 19px; font-weight: 700; color: #1A1412 !important; margin-bottom: 4px;">
                1. Select Body Build & Silhouette Shape
            </div>
            """, unsafe_allow_html=True)

            build_options = list(BODY_BUILDS.keys())
            curr_build_idx = build_options.index(profile.get("body_build", "athletic_v_taper")) if profile.get("body_build") in build_options else 0

            selected_build_id = st.selectbox(
                "Body Build Shape",
                build_options,
                index=curr_build_idx,
                format_func=lambda x: f"{BODY_BUILDS[x]['name']} — {BODY_BUILDS[x]['description']}",
                key="body_build_select"
            )

            h_options = list(HEIGHT_PROFILES.keys())
            curr_h_idx = h_options.index(profile.get("height_profile", "average")) if profile.get("height_profile") in h_options else 1

            selected_height = st.selectbox(
                "Height Profile",
                h_options,
                index=curr_h_idx,
                format_func=lambda x: HEIGHT_PROFILES[x]["label"],
                key="height_profile_select"
            )

            if st.button("💾 Save Body Criteria", type="primary"):
                profile["body_build"] = selected_build_id
                profile["height_profile"] = selected_height
                save_profile(profile)
                st.success("Body criteria saved!")
                st.rerun()

        with b_right:
            b_info = BODY_BUILDS[selected_build_id]
            st.markdown(f"""
            <div style="font-size: 19px; font-weight: 700; color: #1A1412 !important; margin-bottom: 10px;">
                Silhouette Blueprint: {b_info['name']}
            </div>
            <div class="diagnostic-box">
                <div style="font-size:14.5px; color:#1A1412 !important; line-height:1.6; margin-bottom:12px;">
                    {b_info['flattery_note']}
                </div>
                <div style="font-size:14px; line-height:1.8;">
                    <strong style="color:#164E12 !important;">Recommended Fits:</strong> <span style="color:#1A1412 !important;">{', '.join(b_info['best_fits'])}</span><br>
                    <strong style="color:#8A1E0B !important;">Avoid Cuts:</strong> <span style="color:#1A1412 !important;">{', '.join(b_info['avoid_fits']) if b_info['avoid_fits'] else 'None (Versatile)'}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")
st.caption("Muse Wardrobe — Private digital wardrobe stored locally on your device. Zero external cloud tracking.")
