"""
pages/2_Add_Clothing.py — Scan & Add Garments with Skin Tone Color Guidance
==========================================================================
Scan clothes via photo or camera, auto-extract dominant colors, receive instant
seasonal palette matching for your skin tone, and store in your digital wardrobe.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from PIL import Image
import io

from src.data_manager import add_garment
from src.wardrobe_manager import validate_garment_dict
from src.image_processor import (
    validate_image_bytes, save_garment_image,
    extract_dominant_colors, get_image_info,
    remove_background
)
from src.garment_classifier import suggest_category_from_colors, get_category_confidence_display
from src.skin_tone_analyzer import load_profile, get_garment_palette_badge, resolve_palette
from src.theme_helper import apply_editorial_theme
from config.settings import (
    CATEGORIES, PATTERNS, SEASONS, WEATHER_OPTIONS,
    FIT_OPTIONS, STYLE_TAGS
)
from src.color_compatibility import AVAILABLE_COLORS

st.set_page_config(page_title="Scan & Add Clothing", page_icon="📷", layout="wide")

# Apply full editorial theme: light brown sidebar, light brown text, warm selection
apply_editorial_theme()

# Editorial Brown & White Stylesheet
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
.stApp {
    background-color: #FAF7F2 !important;
    background-image: none !important;
    color: #241C18 !important;
    font-family: 'Plus Jakarta Sans', sans-serif;
}
h1, h2, h3 {
    font-family: 'Playfair Display', Georgia, serif !important;
    color: #241C18 !important;
}
.palette-card {
    background-color: #FFFFFF !important;
    border: 1px solid #EBE4DA !important;
    border-radius: 8px;
    padding: 14px;
    margin-top: 10px;
}
.badge-warmth {
    background-color: #F7ECE7 !important; color: #8C3B1E !important; border: 1px solid #E4C5BA !important;
    padding: 3px 8px; border-radius: 10px; font-size: 10px; font-weight: 700;
}
.badge-best {
    background-color: #EBF3EA !important; color: #2D5A27 !important; border: 1px solid #BED8BC !important;
    padding: 3px 8px; border-radius: 10px; font-size: 10px; font-weight: 700;
}
.badge-staple {
    background-color: #F2EFEB !important; color: #4A453E !important; border: 1px solid #D5CFC7 !important;
    padding: 3px 8px; border-radius: 10px; font-size: 10px; font-weight: 700;
}
div.stButton > button[kind="primary"] {
    background-color: #B85D3B !important;
    color: #FFFFFF !important;
    border: none !important;
    font-weight: 600 !important;
    border-radius: 20px !important;
}
div.stButton > button[kind="primary"]:hover {
    background-color: #9E4D2E !important;
}

/* Camera Input: "Take Photo" & Camera Action Buttons in Pure White */
[data-testid="stCameraInput"] button,
.stCameraInput button,
div[data-testid="stCameraInput"] button,
[data-testid="stCameraInputButton"],
div[data-testid="stCameraInput"] [data-baseweb="button"] {
    background-color: #241C18 !important;
    border: 1.5px solid #8C3B1E !important;
    color: #FFFFFF !important;
}

[data-testid="stCameraInput"] button:hover,
.stCameraInput button:hover,
div[data-testid="stCameraInput"] button:hover,
[data-testid="stCameraInputButton"]:hover {
    background-color: #3E2B22 !important;
    border-color: #B85D3B !important;
    color: #FFFFFF !important;
}

[data-testid="stCameraInput"] button *,
[data-testid="stCameraInput"] button div,
[data-testid="stCameraInput"] button p,
[data-testid="stCameraInput"] button span,
.stCameraInput button *,
.stCameraInput button div,
.stCameraInput button p,
.stCameraInput button span,
[data-testid="stCameraInputButton"] *,
div[data-testid="stCameraInput"] [data-baseweb="button"] * {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    font-weight: 600 !important;
    font-size: 13.5px !important;
    letter-spacing: 0.02em !important;
}

[data-testid="stCameraInput"] button svg,
.stCameraInput button svg {
    fill: #FFFFFF !important;
    stroke: #FFFFFF !important;
}
</style>
""", unsafe_allow_html=True)

profile = load_profile()
season_curr = profile.get("palette_tier", profile.get("season", "medium_golden"))
palette_info = resolve_palette(season_curr)

st.title("📷 Scan & Catalogue Piece")
st.caption(f"Catalogue pieces into {profile.get('name', 'BUDZ')}'s private digital wardrobe with quiet luxury color guidance for his **{palette_info['name']}** complexion.")

tab_scan, tab_manual = st.tabs(["📷 Scan with Camera / Upload Photo", "📝 Manual Catalogue Entry"])


# ─────────────────────────────────────────────
# TAB 1 — SCAN WITH CAMERA OR PHOTO UPLOAD
# ─────────────────────────────────────────────
with tab_scan:
    st.subheader("Scan Garment")
    st.caption("Upload a photo or capture with your webcam. Dominant colors are extracted with K-Means clustering.")

    scan_mode = st.radio("Input Method", ["📁 Upload Image File", "📸 Use Camera"], horizontal=True)

    file_bytes = None
    filename   = "scanned_garment.jpg"

    if scan_mode == "📸 Use Camera":
        cam_pic = st.camera_input("Take a photo of the piece lying flat or hung")
        if cam_pic:
            file_bytes = cam_pic.getvalue()
    else:
        uploaded_file = st.file_uploader(
            "Upload image (JPG, PNG, WEBP — max 10 MB)",
            type=["jpg", "jpeg", "png", "webp"]
        )
        if uploaded_file:
            file_bytes = uploaded_file.read()
            filename   = uploaded_file.name

    if file_bytes:
        is_valid, err_msg = validate_image_bytes(file_bytes, filename)
        if not is_valid:
            st.error(f"❌ {err_msg}")
        else:
            auto_bg = st.checkbox("✨ Automatically remove background (Clean Cutout)", value=True, key="chk_auto_bg")

            col_img, col_info = st.columns([1.1, 1.9])
            cutout_img_preview = None

            with col_img:
                if auto_bg:
                    with st.spinner("Removing background..."):
                        try:
                            cutout_img_preview = remove_background(file_bytes)
                            st.image(cutout_img_preview, caption="✨ Clean Garment Cutout", use_column_width=True)
                        except Exception:
                            st.image(file_bytes, caption="Scanned Garment", use_column_width=True)
                else:
                    st.image(file_bytes, caption="Scanned Garment", use_column_width=True)

            with col_info:
                with st.spinner("Analyzing colors and proportions..."):
                    img_for_colors = cutout_img_preview if (auto_bg and cutout_img_preview) else Image.open(io.BytesIO(file_bytes))
                    colors = extract_dominant_colors(img_for_colors)
                    info = {"width": img_for_colors.width, "height": img_for_colors.height}

                top_color = colors[0]["name"] if colors else "White"
                badge = get_garment_palette_badge(top_color, season_curr)
                badge_class = "badge-best" if badge["badge"] == "BEST MATCH" else "badge-warmth" if badge["badge"] == "ADD WARMTH" else "badge-staple"

                st.markdown(f"""
                <div class="palette-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <strong>Skin Tone Color Guidance:</strong>
                        <span class="{badge_class}">{badge['badge']}</span>
                    </div>
                    <div style="font-size:13px; color:#4A4138; margin-top:6px;">
                        {badge['text']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("<br><strong>Extracted Dominant Colors:</strong>", unsafe_allow_html=True)
                for c in colors:
                    st.markdown(
                        f"<div style='display:flex;align-items:center;gap:10px;margin:3px 0;'>"
                        f"<div style='width:20px;height:20px;background:{c['hex']};border-radius:4px;border:1px solid #CCC;'></div>"
                        f"<span style='font-size:13px;'>{c['name'].title()} ({c['hex']}) — {c['percentage']:.0f}%</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                suggested_cat, conf, reason = suggest_category_from_colors(colors, info)
                st.caption(f"Suggested category: **{suggested_cat}** ({get_category_confidence_display(conf)} confidence)")

            st.markdown("---")
            st.markdown("#### Confirm Details & Save to Digital Wardrobe")

            # Determine best index in AVAILABLE_COLORS
            av_idx = 0
            for i, ac in enumerate(AVAILABLE_COLORS):
                if ac.lower() == top_color.lower():
                    av_idx = i
                    break

            with st.form("scanned_save_form", clear_on_submit=True):
                p1, p2 = st.columns(2)
                with p1:
                    p_brand     = st.text_input("Brand (e.g. Zara, Levi's, Uniqlo)")
                    p_category  = st.selectbox("Category *", CATEGORIES,
                                                index=CATEGORIES.index(suggested_cat) if suggested_cat in CATEGORIES else 0)
                    p_color     = st.selectbox("Primary Color *", AVAILABLE_COLORS, index=av_idx)
                    p_color_hex = st.color_picker("Color Hex", value=colors[0]["hex"] if colors else "#808080")
                    p_formality = st.slider("Formality (1=Casual, 5=Formal)", 1, 5, 2)

                with p2:
                    p_pattern   = st.selectbox("Pattern", PATTERNS)
                    p_fit       = st.selectbox("Fit", FIT_OPTIONS)
                    p_style     = st.multiselect("Style Tags", STYLE_TAGS, default=["Casual"])
                    p_season    = st.selectbox("Season", SEASONS)
                    p_notes     = st.text_area("Notes", placeholder="e.g. Favorite oversized fit, soft fabric")

                save_btn = st.form_submit_button("✨ Save to Digital Wardrobe", type="primary", use_container_width=True)

            if save_btn:
                saved_path, img_err = save_garment_image(file_bytes, filename, auto_remove_bg=auto_bg)
                garment = {
                    "category":    p_category,
                    "color":       p_color,
                    "color_hex":   p_color_hex,
                    "pattern":     p_pattern,
                    "formality":   p_formality,
                    "style_tags":  ", ".join(p_style),
                    "season":      p_season,
                    "weather":     "Any",
                    "fit":         p_fit,
                    "brand":       p_brand,
                    "notes":       p_notes,
                    "photo_path":  saved_path,
                    "times_worn":  0,
                    "is_sample":   False,
                }
                errs = validate_garment_dict(garment)
                if errs:
                    for e in errs:
                        st.error(e)
                else:
                    new_id = add_garment(garment)
                    st.success(f"🎉 Successfully catalogued piece into your digital wardrobe! (ID: `{new_id}`)")
                    st.balloons()


# ─────────────────────────────────────────────
# TAB 2 — MANUAL ENTRY
# ─────────────────────────────────────────────
with tab_manual:
    st.subheader("Manual Garment Entry")
    with st.form("manual_add_form", clear_on_submit=True):
        m1, m2 = st.columns(2)
        with m1:
            m_brand       = st.text_input("Brand", placeholder="e.g. H&M, Nike, FabIndia")
            m_category    = st.selectbox("Category *", CATEGORIES)
            m_color       = st.selectbox("Primary Color *", AVAILABLE_COLORS)
            m_formality   = st.slider("Formality (1=Casual, 5=Formal)", 1, 5, 2)

        with m2:
            m_pattern     = st.selectbox("Pattern", PATTERNS)
            m_fit         = st.selectbox("Fit", FIT_OPTIONS)
            m_style       = st.multiselect("Style Tags", STYLE_TAGS, default=["Casual"])
            m_notes       = st.text_area("Notes")

        m_submit = st.form_submit_button("💾 Save to Wardrobe", type="primary", use_container_width=True)

    if m_submit:
        garment = {
            "category":    m_category,
            "color":       m_color,
            "formality":   m_formality,
            "pattern":     m_pattern,
            "fit":         m_fit,
            "brand":       m_brand,
            "style_tags":  ", ".join(m_style),
            "season":      "All Seasons",
            "weather":     "Any",
            "notes":       m_notes,
            "times_worn":  0,
            "is_sample":   False,
        }
        errs = validate_garment_dict(garment)
        if errs:
            for e in errs:
                st.error(e)
        else:
            new_id = add_garment(garment)
            st.success(f"✅ Added {m_color} {m_category} to your wardrobe! (ID: `{new_id}`)")
