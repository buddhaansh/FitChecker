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
from src.garment_classifier import (
    suggest_garment_attributes,
    suggest_category_from_colors,
    get_category_confidence_display,
    get_garment_styling_advice
)
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

tab_batch, tab_scan, tab_manual = st.tabs([
    "⚡ Batch Upload (Up to 20 Clothes at Once)",
    "📷 Single Garment Scan / Camera",
    "📝 Manual Catalogue Entry"
])


# ─────────────────────────────────────────────
# TAB 1 — BATCH UPLOAD (UP TO 20 CLOTHES AT ONCE)
# ─────────────────────────────────────────────
with tab_batch:
    st.subheader("⚡ Batch Garment Upload & AI Auto-Catalogue")
    st.caption("Drop 2 to 20 clothing photos at once. The AI automatically isolates every piece onto a clean white studio background, extracts colors, detects categories & patterns, and lets you save your entire wardrobe in 1 click.")

    batch_files = st.file_uploader(
        "Choose or drag multiple clothing photos (JPG, PNG, WEBP — up to 20 images)",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        key="batch_file_uploader"
    )

    if batch_files:
        st.markdown(f"**Loaded {len(batch_files)} photo(s).** Processing background cutouts & AI classification...")

        # Initialize session state cache for batch items
        if "batch_cache" not in st.session_state:
            st.session_state["batch_cache"] = {}

        # Progress bar during processing
        progress_bar = st.progress(0, text="Analyzing garments with Computer Vision...")

        processed_items = []
        for idx, f in enumerate(batch_files):
            progress_pct = int((idx / len(batch_files)) * 100)
            progress_bar.progress(progress_pct, text=f"Processing {idx+1}/{len(batch_files)}: {f.name}...")

            f_bytes = f.getvalue()
            cache_id = f"{f.name}_{len(f_bytes)}"

            if cache_id in st.session_state["batch_cache"]:
                processed_items.append(st.session_state["batch_cache"][cache_id])
            else:
                try:
                    cutout = remove_background(f_bytes)
                    colors = extract_dominant_colors(cutout)
                    info = {"width": cutout.width, "height": cutout.height}
                    ai_attrs = suggest_garment_attributes(colors, image_input=cutout, image_info=info)

                    top_col = colors[0]["name"] if colors else "White"
                    top_hex = colors[0]["hex"] if colors else "#FFFFFF"

                    cached_obj = {
                        "filename": f.name,
                        "file_bytes": f_bytes,
                        "cutout_image": cutout,
                        "colors": colors,
                        "ai_attrs": ai_attrs,
                        "top_color": top_col,
                        "top_hex": top_hex,
                    }
                    st.session_state["batch_cache"][cache_id] = cached_obj
                    processed_items.append(cached_obj)
                except Exception as e:
                    st.warning(f"Could not process {f.name}: {e}")

        progress_bar.progress(100, text="✨ All garments analyzed and isolated onto pure white background!")

        st.markdown(f"""
        <div style="background: #FFFFFF; border: 1.5px solid #DDD1C2; border-radius: 12px; padding: 14px 18px; margin: 16px 0; box-shadow: 0 4px 12px rgba(74, 53, 43, 0.04);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-family: 'Playfair Display', Georgia, serif; font-size: 18px; font-weight: 700; color: #241C18;">
                    Batch Review ({len(processed_items)} Garments Ready)
                </span>
                <span style="background: #2D5A27; color: #FFFFFF; font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 10px;">
                    AI CLASSIFIED
                </span>
            </div>
            <div style="font-size: 13px; color: #704E38; margin-top: 4px;">
                Review the AI predictions below. You can tweak any category, color, or formality before saving all pieces in 1 click.
            </div>
        </div>
        """, unsafe_allow_html=True)

        batch_edit_records = []

        for i, item in enumerate(processed_items):
            ai_data = item["ai_attrs"]
            c_img, c_form = st.columns([1.1, 2.5])

            with c_img:
                st.image(item["cutout_image"].convert("RGB"), caption=item["filename"], use_column_width=True)
                st.markdown(f"<div style='font-size: 12px; color: #8C3B1E; font-weight: 700; text-align: center;'>Detected: {ai_data['category']} ({int(ai_data['confidence']*100)}%)</div>", unsafe_allow_html=True)

            with c_form:
                st.markdown(f"**Garment #{i+1}: {item['filename']}**")
                bf1, bf2 = st.columns(2)
                with bf1:
                    # Category
                    cat_default_idx = CATEGORIES.index(ai_data["category"]) if ai_data["category"] in CATEGORIES else 0
                    b_cat = st.selectbox(f"Category", CATEGORIES, index=cat_default_idx, key=f"b_cat_{i}")

                    # Primary Color
                    b_col_idx = 0
                    for ci, cname in enumerate(AVAILABLE_COLORS):
                        if cname.lower() == item["top_color"].lower():
                            b_col_idx = ci
                            break
                    b_col = st.selectbox(f"Color", AVAILABLE_COLORS, index=b_col_idx, key=f"b_col_{i}")

                    # Formality
                    b_formality = st.slider(f"Formality", 1, 5, value=ai_data.get("formality", 3), key=f"b_form_{i}")

                with bf2:
                    # Pattern
                    pat_idx = PATTERNS.index(ai_data["pattern"]) if ai_data.get("pattern") in PATTERNS else 0
                    b_pat = st.selectbox(f"Pattern", PATTERNS, index=pat_idx, key=f"b_pat_{i}")

                    # Fit
                    fit_idx = FIT_OPTIONS.index(ai_data["fit"]) if ai_data.get("fit") in FIT_OPTIONS else 0
                    b_fit = st.selectbox(f"Fit", FIT_OPTIONS, index=fit_idx, key=f"b_fit_{i}")

                    # Brand
                    b_brand = st.text_input(f"Brand (optional)", placeholder="e.g. Zara, Uniqlo, H&M", key=f"b_brand_{i}")

                # Include checkbox
                b_include = st.checkbox("Include in digital wardrobe", value=True, key=f"b_inc_{i}")

                batch_edit_records.append({
                    "include": b_include,
                    "item": item,
                    "category": b_cat,
                    "color": b_col,
                    "color_hex": item["top_hex"],
                    "pattern": b_pat,
                    "formality": b_formality,
                    "fit": b_fit,
                    "brand": b_brand,
                    "style_tags": ", ".join(ai_data.get("style_tags", ["Casual"])),
                    "season": ai_data.get("season", "All Seasons")
                })

            st.markdown("<hr style='border: none; border-top: 1px dashed #DDD1C2; margin: 16px 0;'>", unsafe_allow_html=True)

        # Batch Save Button
        st.markdown("<br>", unsafe_allow_html=True)
        num_selected = sum(1 for r in batch_edit_records if r["include"])

        if st.button(f"✨ Save All {num_selected} Garment(s) to My Digital Wardrobe", type="primary", use_container_width=True, key="btn_save_batch_all"):
            saved_count = 0
            with st.spinner(f"Cataloguing {num_selected} pieces into your digital wardrobe..."):
                for rec in batch_edit_records:
                    if not rec["include"]:
                        continue

                    it = rec["item"]
                    # Save cutout image
                    saved_path, _ = save_garment_image(
                        it["file_bytes"],
                        it["filename"],
                        auto_remove_bg=True,
                        precomputed_cutout=it["cutout_image"]
                    )

                    garment_dict = {
                        "category":    rec["category"],
                        "color":       rec["color"],
                        "color_hex":   rec["color_hex"],
                        "pattern":     rec["pattern"],
                        "formality":   rec["formality"],
                        "style_tags":  rec["style_tags"],
                        "season":      rec["season"],
                        "weather":     "Any",
                        "fit":         rec["fit"],
                        "brand":       rec["brand"],
                        "notes":       "Batch catalogued via AI studio",
                        "photo_path":  saved_path,
                        "times_worn":  0,
                        "is_sample":   False,
                    }
                    add_garment(garment_dict)
                    saved_count += 1

            st.session_state.pop("batch_cache", None)
            st.success(f"🎉 Successfully saved all {saved_count} garments to your wardrobe!")
            st.balloons()

            b_c1, b_c2 = st.columns(2)
            with b_c1:
                if st.button("🧥 VIEW ALL IN MY WARDROBE", type="primary", use_container_width=True, key="btn_b_view_wardrobe"):
                    st.switch_page("pages/1_My_Wardrobe.py")
            with b_c2:
                if st.button("➕ UPLOAD MORE CLOTHES", type="secondary", use_container_width=True, key="btn_b_upload_more"):
                    st.rerun()


# ─────────────────────────────────────────────
# TAB 2 — SINGLE GARMENT SCAN / CAMERA
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
            filename   = "camera_capture.jpg"
            st.session_state["active_upload_bytes"] = file_bytes
            st.session_state["active_upload_filename"] = filename
    else:
        uploaded_file = st.file_uploader(
            "Upload image (JPG, PNG, WEBP — max 10 MB)",
            type=["jpg", "jpeg", "png", "webp"]
        )
        if uploaded_file:
            file_bytes = uploaded_file.getvalue()
            filename   = uploaded_file.name
            st.session_state["active_upload_bytes"] = file_bytes
            st.session_state["active_upload_filename"] = filename

    # Fallback to session state bytes if Streamlit rerun cleared uploader pointer
    if not file_bytes and st.session_state.get("active_upload_bytes"):
        file_bytes = st.session_state["active_upload_bytes"]
        filename   = st.session_state.get("active_upload_filename", "uploaded_garment.jpg")

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
                    with st.spinner("Isolating garment onto clean white background..."):
                        try:
                            cutout_img_preview = remove_background(file_bytes)
                            st.session_state["cached_cutout_preview"] = cutout_img_preview
                            st.markdown("""
                            <div style="background: #FFFFFF; border: 1.5px solid #E5E0D8; border-radius: 12px; padding: 10px 8px 4px 8px; margin-bottom: 8px; text-align: center; box-shadow: 0 4px 12px rgba(74, 53, 43, 0.04);">
                                <div style="font-size: 11px; font-weight: 800; color: #8C3B1E; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 4px;">✨ Clean White Cutout</div>
                            </div>
                            """, unsafe_allow_html=True)
                            st.image(cutout_img_preview.convert("RGB"), use_column_width=True)
                        except Exception as e:
                            st.error(f"Cutout error: {e}")
                            st.image(file_bytes, caption="Scanned Garment", use_column_width=True)
                else:
                    st.image(file_bytes, caption="Scanned Garment", use_column_width=True)

            with col_info:
                with st.spinner("Analyzing colors, silhouette proportions, and styling rules..."):
                    img_for_colors = cutout_img_preview if (auto_bg and cutout_img_preview) else Image.open(io.BytesIO(file_bytes))
                    colors = extract_dominant_colors(img_for_colors)
                    info = {"width": img_for_colors.width, "height": img_for_colors.height}
                    ai_attrs = suggest_garment_attributes(colors, image_input=cutout_img_preview or file_bytes, image_info=info)

                top_color = colors[0]["name"] if colors else "White"
                badge = get_garment_palette_badge(top_color, season_curr)
                badge_class = "badge-best" if badge["badge"] == "BEST MATCH" else "badge-warmth" if badge["badge"] == "ADD WARMTH" else "badge-staple"

                # 1. Complexion & Skin Guidance Card
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

                # 2. Executive AI Silhouette & Category Identification Card
                conf_badge_color = "#2D5A27" if ai_attrs["confidence_label"] == "High" else "#8C3B1E"
                conf_badge_bg = "#EBF3EA" if ai_attrs["confidence_label"] == "High" else "#F7ECE7"
                st.markdown(f"""
                <div style="background:#FFFFFF; border:1px solid #EBE4DA; border-radius:8px; padding:12px 14px; margin-top:10px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:13px; font-weight:700; color:#1A1412;">🎯 AI Garment Identification:</span>
                        <span style="background:{conf_badge_bg}; color:{conf_badge_color}; font-size:11px; font-weight:700; padding:2px 8px; border-radius:10px;">
                            {ai_attrs['confidence_label']} ({int(ai_attrs['confidence']*100)}%)
                        </span>
                    </div>
                    <div style="font-size:15px; font-weight:700; color:#8C3B1E; margin-top:4px;">
                        {ai_attrs['category']} <span style="font-size:12px; font-weight:500; color:#6B6055;">— Formality {ai_attrs['formality']}/5 · {ai_attrs['fit']} Fit</span>
                    </div>
                    <div style="font-size:12.5px; color:#4A4138; margin-top:4px; line-height:1.45;">
                        {ai_attrs['reason']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 3. Editorial Styling & Pairing Guidance Box
                styling = ai_attrs.get("styling_guidance", {})
                chips = styling.get("color_chips", [])
                chips_html = "".join([
                    f"<span style='display:inline-flex; align-items:center; gap:5px; background:#F5F0EA; border:1px solid #D5CFC7; border-radius:12px; padding:2px 8px; margin:2px 4px 2px 0; font-size:11.5px; font-weight:600; color:#241C18;'>"
                    f"<span style='width:10px; height:10px; border-radius:50%; background:{c['hex']}; display:inline-block; border:1px solid #999;'></span>"
                    f"{c['name']} ({c['score']}%)</span>"
                    for c in chips[:4]
                ])

                st.markdown(f"""
                <div style="background:#FAF6F3; border:1px solid #E4D8CB; border-radius:8px; padding:12px 14px; margin-top:10px;">
                    <div style="font-size:12px; font-weight:800; color:#8C3B1E; text-transform:uppercase; letter-spacing:0.05em;">✨ AI Editorial Styling Advice</div>
                    <div style="font-size:12.5px; color:#2E2722; margin-top:6px; line-height:1.5;">
                        <strong>Ideal Color Pairings:</strong><br>{chips_html}<br>
                        <div style="margin-top:6px;"><strong>Recommended Pieces:</strong> {', '.join(styling.get('recommended_pairings', []))}</div>
                        <div style="margin-top:4px;"><strong>Footwear Anchor:</strong> {styling.get('recommended_footwear', '')}</div>
                        <div style="margin-top:4px;"><strong>Proportion Rule:</strong> {styling.get('proportion_rule', '')}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("#### Confirm Details & Save to Digital Wardrobe")

            # Determine best index in AVAILABLE_COLORS
            av_idx = 0
            for i, ac in enumerate(AVAILABLE_COLORS):
                if ac.lower() == top_color.lower():
                    av_idx = i
                    break

            with st.form("scanned_save_form", clear_on_submit=False):
                p1, p2 = st.columns(2)
                with p1:
                    p_brand     = st.text_input("Brand (e.g. Zara, Levi's, Uniqlo)")
                    p_category  = st.selectbox("Category *", CATEGORIES,
                                                index=CATEGORIES.index(ai_attrs["category"]) if ai_attrs["category"] in CATEGORIES else 0)
                    p_color     = st.selectbox("Primary Color *", AVAILABLE_COLORS, index=av_idx)
                    p_color_hex = st.color_picker("Color Hex", value=colors[0]["hex"] if colors else "#808080")
                    p_formality = st.slider("Formality (1=Casual, 5=Formal)", 1, 5, value=ai_attrs["formality"])

                with p2:
                    p_pat_idx   = PATTERNS.index(ai_attrs["pattern"]) if ai_attrs.get("pattern") in PATTERNS else 0
                    p_pattern   = st.selectbox("Pattern", PATTERNS, index=p_pat_idx)
                    p_fit       = st.selectbox("Fit", FIT_OPTIONS,
                                               index=FIT_OPTIONS.index(ai_attrs["fit"]) if ai_attrs["fit"] in FIT_OPTIONS else 0)
                    default_styles = [s for s in ai_attrs.get("style_tags", ["Casual"]) if s in STYLE_TAGS]
                    p_style     = st.multiselect("Style Tags", STYLE_TAGS, default=default_styles if default_styles else ["Casual"])
                    p_season    = st.selectbox("Season", SEASONS,
                                               index=SEASONS.index(ai_attrs["season"]) if ai_attrs["season"] in SEASONS else 0)
                    p_notes     = st.text_area("Notes", placeholder="e.g. Favorite oversized fit, soft fabric")

                save_btn = st.form_submit_button("✨ Save to Digital Wardrobe", type="primary", use_container_width=True)

            if save_btn:
                cached_cutout = st.session_state.get("cached_cutout_preview")
                saved_path, img_err = save_garment_image(
                    file_bytes, filename,
                    auto_remove_bg=auto_bg,
                    precomputed_cutout=cached_cutout
                )
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

                    # Instant navigation actions
                    nav_c1, nav_c2 = st.columns(2)
                    with nav_c1:
                        if st.button("🧥 VIEW IN MY WARDROBE", type="primary", use_container_width=True, key="btn_go_wardrobe"):
                            st.switch_page("pages/1_My_Wardrobe.py")
                    with nav_c2:
                        if st.button("➕ SCAN ANOTHER GARMENT", type="secondary", use_container_width=True, key="btn_scan_another"):
                            st.session_state.pop("active_upload_bytes", None)
                            st.session_state.pop("active_upload_filename", None)
                            st.session_state.pop("cached_cutout_preview", None)
                            st.rerun()


# ─────────────────────────────────────────────
# TAB 2 — MANUAL ENTRY
# ─────────────────────────────────────────────
with tab_manual:
    st.subheader("Manual Garment Entry")
    with st.form("manual_add_form", clear_on_submit=False):
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
            m_nav1, m_nav2 = st.columns(2)
            with m_nav1:
                if st.button("🧥 VIEW IN MY WARDROBE", type="primary", use_container_width=True, key="btn_m_go_wardrobe"):
                    st.switch_page("pages/1_My_Wardrobe.py")
            with m_nav2:
                if st.button("➕ ADD ANOTHER PIECE", type="secondary", use_container_width=True, key="btn_m_add_another"):
                    st.rerun()
