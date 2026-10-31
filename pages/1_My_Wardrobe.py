"""
pages/1_My_Wardrobe.py — View, Edit and Delete Garments
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from PIL import Image

from src.data_manager import load_wardrobe, delete_garment, update_garment
from src.wardrobe_manager import get_wardrobe_summary
from src.skin_tone_analyzer import load_profile, get_garment_palette_badge
from src.theme_helper import apply_editorial_theme
from src.image_processor import remove_background
from src.color_compatibility import AVAILABLE_COLORS
from config.settings import CATEGORIES, PATTERNS, SEASONS, WEATHER_OPTIONS, FIT_OPTIONS, STYLE_TAGS

st.set_page_config(page_title="Wardrobe Collection", page_icon="🧥", layout="wide")

# Apply full editorial theme: light brown sidebar, light brown text, warm selection
apply_editorial_theme()

profile = load_profile()
user_name = profile.get("name", "BUDZ")
st.title(f"🧥 {user_name}'s Wardrobe")
st.caption(f"Curated private collection for {user_name} — editorial digital closet.")

wardrobe_df = load_wardrobe()
summary = get_wardrobe_summary(wardrobe_df)
profile = load_profile()
season_curr = profile.get("palette_tier", profile.get("season", "medium_golden"))

# ── Top-level metrics ──
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Items",     summary["total"])
c2.metric("Never Worn",      summary["never_worn"])
c3.metric("Utilization",     f"{summary['utilization_pct']}%")
c4.metric("Rarely Worn",     summary["rarely_worn"])

st.markdown("---")

if wardrobe_df.empty:
    st.markdown(f"""
    <div style="background: #FFFFFF; border: 1.5px dashed #D5C7B8; border-radius: 14px; padding: 42px 32px; text-align: center; margin: 20px 0; box-shadow: 0 4px 20px rgba(74, 53, 43, 0.04);">
        <div style="font-size: 42px; margin-bottom: 12px;">🧥✨</div>
        <div style="font-family: 'Playfair Display', Georgia, serif; font-size: 24px; font-weight: 700; color: #241C18; margin-bottom: 8px;">
            Wardrobe Zero — Clean Slate
        </div>
        <div style="font-size: 15px; color: #704E38; max-width: 540px; margin: 0 auto 24px auto; line-height: 1.6; font-weight: 500;">
            Your wardrobe starts at <strong>0 items</strong> so you can curate your own personal clothes. Snap or upload pieces from your almirah to calculate skin tone harmony, silhouette fit, and personalized outfit curations calibrated for <strong>{user_name}</strong>.
        </div>
    </div>
    """, unsafe_allow_html=True)

    b_col1, b_col2 = st.columns(2)
    with b_col1:
        if st.button("📷 ADD CLOTHING FROM ALMIRAH", type="primary", use_container_width=True):
            st.switch_page("pages/2_Add_Clothing.py")
    with b_col2:
        if st.button("✨ VIEW EDITORIAL SHOWCASES", type="secondary", use_container_width=True):
            st.switch_page("app.py")
    st.stop()

# ── Batch AI Background Removal Studio ──
has_photos = any(str(p).strip() and os.path.exists(str(p).strip()) for p in wardrobe_df.get("photo_path", []))
if has_photos:
    with st.expander("✂️ AI Cutout Studio (Batch Background Cleanup)", expanded=False):
        st.markdown(
            "<div style='font-size:13.5px; color:#4A4138; margin-bottom:8px;'>"
            "Cleanly extract garments from room/bed/wall backgrounds across all pieces using the upgraded high-precision CV GrabCut model."
            "</div>",
            unsafe_allow_html=True
        )
        if st.button("✨ Reprocess All Photos to Clean Cutouts", type="secondary", key="btn_batch_cutout"):
            with st.spinner("Extracting clean cutouts..."):
                count_cleaned = 0
                for it in wardrobe_df.to_dict("records"):
                    p = str(it.get("photo_path", "")).strip()
                    if p and os.path.exists(p):
                        try:
                            cutout = remove_background(p)
                            base, _ = os.path.splitext(p)
                            clean_path = base + ("_clean.png" if not base.endswith("_clean") else ".png")
                            cutout.save(clean_path, format="PNG")
                            update_garment(it["item_id"], {"photo_path": clean_path})
                            count_cleaned += 1
                        except Exception:
                            pass
                st.success(f"Successfully cleaned backgrounds for {count_cleaned} garments!")
                st.rerun()

# ── Palette Filter Bar (Matches Luxury Editorial Closet) ──
wardrobe_df["palette_badge"] = wardrobe_df["color"].apply(lambda c: get_garment_palette_badge(str(c), season_curr)["badge"])

total_items = len(wardrobe_df)
count_best = int((wardrobe_df["palette_badge"] == "BEST MATCH").sum())
count_warmth = int((wardrobe_df["palette_badge"] == "ADD WARMTH").sum())
count_outside = int((~wardrobe_df["palette_badge"].isin(["BEST MATCH", "ADD WARMTH"])).sum())

pal_options = [
    f"ALL {total_items}",
    f"BEST MATCHES {count_best}",
    f"ADD WARMTH {count_warmth}",
    f"OUTSIDE PALETTE {count_outside}",
]

p_col1, p_col2 = st.columns([1, 4])
with p_col1:
    st.markdown("<div style='font-size: 11px; font-weight: 800; color: #704E38; letter-spacing: 0.12em; text-transform: uppercase; padding-top: 10px;'>PALETTE HARMONY</div>", unsafe_allow_html=True)
with p_col2:
    selected_pal = st.radio("Palette Filter", pal_options, horizontal=True, label_visibility="collapsed", key="wardrobe_palette_radio")

filtered = wardrobe_df.copy()
if selected_pal:
    if "BEST MATCHES" in selected_pal:
        filtered = filtered[filtered["palette_badge"] == "BEST MATCH"]
    elif "ADD WARMTH" in selected_pal:
        filtered = filtered[filtered["palette_badge"] == "ADD WARMTH"]
    elif "OUTSIDE PALETTE" in selected_pal:
        filtered = filtered[~filtered["palette_badge"].isin(["BEST MATCH", "ADD WARMTH"])]

# ── Filters ──
with st.expander("🔍 Filter by Category, Color & Wear Status", expanded=False):
    f1, f2, f3 = st.columns(3)
    filter_cat   = f1.multiselect("Category",  sorted(wardrobe_df["category"].dropna().unique()))
    filter_color = f2.multiselect("Color",     sorted(wardrobe_df["color"].dropna().unique()))
    filter_worn  = f3.selectbox("Wear Status",  ["All", "Worn", "Never Worn"])

if filter_cat:
    filtered = filtered[filtered["category"].isin(filter_cat)]
if filter_color:
    filtered = filtered[filtered["color"].isin(filter_color)]
if filter_worn == "Worn":
    filtered = filtered[pd.to_numeric(filtered["times_worn"], errors="coerce").fillna(0) > 0]
elif filter_worn == "Never Worn":
    filtered = filtered[pd.to_numeric(filtered["times_worn"], errors="coerce").fillna(0) == 0]

st.markdown(f"Showing **{len(filtered)}** of **{summary['total']}** curated pieces")

# ── Item Cards (Editorial Studio Catalog) ──
COLS_PER_ROW = 4
items = filtered.to_dict("records")

for row_start in range(0, len(items), COLS_PER_ROW):
    cols = st.columns(COLS_PER_ROW)
    for col_idx, item in enumerate(items[row_start : row_start + COLS_PER_ROW]):
        with cols[col_idx]:
            with st.container(border=True):
                # Palette Badge
                palette_b = get_garment_palette_badge(item.get("color", ""), season_curr)
                b_text = palette_b["badge"]
                if b_text == "BEST MATCH":
                    badge_bg = "#2D5A27"
                    badge_fg = "#FFFFFF"
                elif b_text == "ADD WARMTH":
                    badge_bg = "#8C4A28"
                    badge_fg = "#FFFFFF"
                else:
                    badge_bg = "#756D65"
                    badge_fg = "#FFFFFF"

                # Editorial Studio Backdrop Container
                st.markdown(f"""
                <div style="background: #FAF7F2; border: 1.5px solid #EBE4DA; border-radius: 12px; padding: 10px 8px; margin-bottom: 8px; text-align: center; box-shadow: 0 4px 12px rgba(74, 53, 43, 0.03);">
                    <div style="display: flex; justify-content: flex-start; margin-bottom: 4px;">
                        <span style="background: {badge_bg}; color: {badge_fg}; font-size: 9.5px; font-weight: 800; padding: 2px 8px; border-radius: 8px; letter-spacing: 0.04em;">{b_text}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Photo
                photo = str(item.get("photo_path", "")).strip()
                if photo and os.path.exists(photo):
                    try:
                        st.image(photo, use_column_width=True)
                    except Exception:
                        st.markdown("📷 *Image unavailable*")
                else:
                    # Color swatch placeholder
                    color_name = item.get("color", "grey").lower()
                    st.markdown(
                        f"<div style='background:{item.get('color_hex','#808080') or '#808080'};"
                        f"height:120px;border-radius:8px;margin-bottom:8px;'></div>",
                        unsafe_allow_html=True
                    )

                # Details
                st.markdown(f"<div style='font-size:15px; font-weight:700; color:#241C18; margin-bottom:3px;'>{item.get('color','')} {item.get('category','')}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:12.5px; font-weight:500; color:#8C5835; margin-bottom:2px;'>Pattern: {item.get('pattern','—')} &nbsp;|&nbsp; {'⭐' * int(item.get('formality', 3))}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:12px; font-weight:500; color:#8C5835; margin-bottom:4px;'>Worn: {item.get('times_worn', 0)}× &nbsp;|&nbsp; Last: {item.get('last_worn','—') or '—'}</div>", unsafe_allow_html=True)

                if item.get("is_sample"):
                    st.markdown("<div style='font-size:11px; font-weight:600; color:#B85D3B; margin-bottom:4px;'>🏷️ Sample data</div>", unsafe_allow_html=True)

                # Actions
                exp = st.expander("Edit / Delete / Clean")
                with exp:
                    curr_cat = item.get("category", "Shirt")
                    cat_idx = CATEGORIES.index(curr_cat) if curr_cat in CATEGORIES else 0
                    new_category = st.selectbox("Category", CATEGORIES, index=cat_idx, key=f"cat_{item['item_id']}")

                    curr_color = item.get("color", "White")
                    col_idx = AVAILABLE_COLORS.index(curr_color) if curr_color in AVAILABLE_COLORS else 0
                    new_color = st.selectbox("Color", AVAILABLE_COLORS, index=col_idx, key=f"col_{item['item_id']}")

                    curr_pat = item.get("pattern", "Solid")
                    pat_idx = PATTERNS.index(curr_pat) if curr_pat in PATTERNS else 0
                    new_pattern = st.selectbox("Pattern", PATTERNS, index=pat_idx, key=f"pat_{item['item_id']}")

                    new_formality = st.slider(
                        "Formality (1=Casual, 5=Formal)", 1, 5,
                        int(item.get("formality", 3)),
                        key=f"form_{item['item_id']}"
                    )
                    new_notes = st.text_input(
                        "Notes", value=str(item.get("notes","") or ""),
                        key=f"notes_{item['item_id']}"
                    )

                    # Background cleaner action
                    photo_file = str(item.get("photo_path", "")).strip()
                    if photo_file and os.path.exists(photo_file):
                        if st.button("✂️ Clean Background Cutout", key=f"rebg_{item['item_id']}", use_container_width=True):
                            with st.spinner("Extracting clean cutout..."):
                                try:
                                    cutout = remove_background(photo_file)
                                    base, _ = os.path.splitext(photo_file)
                                    clean_path = base + ("_clean.png" if not base.endswith("_clean") else ".png")
                                    cutout.save(clean_path, format="PNG")
                                    update_garment(item["item_id"], {"photo_path": clean_path})
                                    st.success("Background cleanly removed!")
                                    st.rerun()
                                except Exception as err:
                                    st.error(f"Failed to remove background: {err}")

                    save_col, del_col = st.columns(2)
                    if save_col.button("💾 Save", key=f"save_{item['item_id']}", type="primary"):
                        update_garment(item["item_id"], {
                            "category": new_category,
                            "color": new_color,
                            "pattern": new_pattern,
                            "formality": new_formality,
                            "notes": new_notes
                        })
                        st.success("Saved!")
                        st.rerun()
                    if del_col.button("🗑️ Delete", key=f"del_{item['item_id']}"):
                        delete_garment(item["item_id"])
                        st.warning("Deleted.")
                        st.rerun()

# ── Raw Table View ──
with st.expander("📋 View as Table"):
    display_cols = ["category", "color", "pattern", "formality",
                    "times_worn", "last_worn", "season", "style_tags", "is_sample"]
    show_cols = [c for c in display_cols if c in filtered.columns]
    st.dataframe(filtered[show_cols], use_container_width=True)
