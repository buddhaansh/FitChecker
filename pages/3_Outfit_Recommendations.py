"""
pages/3_Outfit_Recommendations.py — Generate and rank outfit recommendations
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import streamlit as st
from PIL import Image

from src.data_manager import load_wardrobe, load_preferences
from src.outfit_generator import generate_outfits, format_outfit_label
from src.recommender import rank_outfits
from src.feedback_manager import record_outfit_selection
from src.ml_model import load_model, predict_acceptance
from src.skin_tone_analyzer import load_profile
from src.editorial_recommender import generate_eloquent_shuffle_outfit
from src.theme_helper import apply_editorial_theme
from config.settings import OCCASIONS, WEATHER_OPTIONS, SCORE_WEIGHTS

st.set_page_config(page_title="Outfit Recommendations — FitChecker", page_icon="✨", layout="wide")

# Apply full editorial theme: light brown sidebar, light brown text, warm selection
apply_editorial_theme()

st.title("✨ Outfit Recommendations")
st.caption("Generate outfit ideas from your wardrobe for any occasion with continuous color harmony and eloquent AI styling.")

prof = load_profile()
w_df_quick = load_wardrobe()
if not w_df_quick.empty:
    with st.expander("🎲 Quick Shuffle · Eloquent AI Mode (Whering Style)", expanded=False):
        st.caption("Behind the scenes, the AI models color harmony and skin radiance with creative stochastic sampling.")
        q_cols = st.columns([1, 3])
        with q_cols[0]:
            if st.button("🎲 Instant Eloquent Shuffle", key="btn_quick_shuffle", type="primary", use_container_width=True):
                st.session_state["quick_eloquent_look"] = generate_eloquent_shuffle_outfit(w_df_quick, prof, temperature=0.75)
        with q_cols[1]:
            q_look = st.session_state.get("quick_eloquent_look")
            if q_look:
                st.markdown(f"**{q_look['formula_tag']}** — `{q_look['total_score']}% Curated Match`")
                st.markdown(f"*{q_look['eloquent_desc']}*")
                q_it_cols = st.columns(len(q_look["items"]))
                for q_i, q_it in enumerate(q_look["items"]):
                    with q_it_cols[q_i]:
                        q_photo = str(q_it.get("photo_path") or "").strip()
                        if q_photo and os.path.exists(q_photo):
                            st.image(q_photo, use_column_width=True)
                        else:
                            st.markdown(f"<div style='background:{q_it.get('color_hex','#808080')};height:55px;border-radius:6px;'></div>", unsafe_allow_html=True)
                        st.caption(f"{q_it.get('color','').title()} {q_it.get('category')}")

# ─────────────────────────────────────────────
# SIDEBAR CONTROLS
# ─────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Recommendation Settings")

    occasion = st.selectbox(
        "Occasion",
        OCCASIONS,
        index=OCCASIONS.index(st.session_state.get("rec_occasion", "Daily College Wear"))
    )
    weather = st.selectbox(
        "Current Weather",
        WEATHER_OPTIONS,
        index=WEATHER_OPTIONS.index(st.session_state.get("rec_weather", "Any"))
    )
    include_acc = st.toggle("Include Accessories", value=True)
    top_n = st.slider("Number of Recommendations", 1, 10, 5)

    st.markdown("---")
    st.markdown("**Scoring Weights** *(must sum to 1.0)*")
    w_occ  = st.slider("Occasion Suitability",  0.0, 1.0, SCORE_WEIGHTS["occasion_suitability"], 0.05)
    w_col  = st.slider("Color Compatibility",   0.0, 1.0, SCORE_WEIGHTS["color_compatibility"],  0.05)
    w_sty  = st.slider("Style / Formality",     0.0, 1.0, SCORE_WEIGHTS["style_formality"],      0.05)
    w_wx   = st.slider("Weather Suitability",   0.0, 1.0, SCORE_WEIGHTS["weather_suitability"],  0.05)
    w_pref = st.slider("Personal Preference",   0.0, 1.0, SCORE_WEIGHTS["personal_preference"],  0.05)

    total_w = round(w_occ + w_col + w_sty + w_wx + w_pref, 2)
    if total_w != 1.0:
        st.warning(f"Weights sum to {total_w}. They will be auto-normalised.")

    custom_weights = {
        "occasion_suitability": w_occ / total_w if total_w else SCORE_WEIGHTS["occasion_suitability"],
        "color_compatibility":  w_col / total_w if total_w else SCORE_WEIGHTS["color_compatibility"],
        "style_formality":      w_sty / total_w if total_w else SCORE_WEIGHTS["style_formality"],
        "weather_suitability":  w_wx  / total_w if total_w else SCORE_WEIGHTS["weather_suitability"],
        "personal_preference":  w_pref / total_w if total_w else SCORE_WEIGHTS["personal_preference"],
    }

    generate_btn = st.button("🔄 Generate Recommendations", use_container_width=True)

# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
wardrobe_df = load_wardrobe()
preferences = load_preferences()
ml_model    = load_model()

# ─────────────────────────────────────────────
# GENERATE
# ─────────────────────────────────────────────
if generate_btn or st.session_state.get("rec_occasion"):
    # Clear the session trigger after first use
    st.session_state.pop("rec_occasion", None)
    st.session_state.pop("rec_weather",  None)

    if wardrobe_df.empty:
        st.warning("Your wardrobe is empty. Add some garments first!")
        st.stop()

    with st.spinner("Generating outfit combinations…"):
        candidates = generate_outfits(
            wardrobe_df,
            occasion=occasion,
            current_weather=weather,
            include_accessories=include_acc,
        )
        if not candidates:
            from src.editorial_recommender import _generate_partial_outfits
            candidates = _generate_partial_outfits(wardrobe_df)

    if not candidates:
        st.error(
            "No valid outfit combinations could be found for this occasion and weather. "
            "Tips: Add more garment categories (especially footwear), "
            "or relax the weather/formality settings."
        )
        st.stop()

    with st.spinner("Scoring and ranking outfits…"):
        ranked = rank_outfits(
            candidates,
            occasion=occasion,
            current_weather=weather,
            preferences=preferences,
            weights=custom_weights,
            top_n=top_n,
        )

    st.success(
        f"Found **{len(candidates)}** combinations → showing top **{len(ranked)}** "
        f"for **{occasion}**"
    )

    # ── Display each recommended outfit ──
    for rank_idx, outfit in enumerate(ranked, start=1):
        with st.container(border=True):
            col_rank, col_items, col_score = st.columns([1, 4, 2])

            with col_rank:
                medals = ["🥇", "🥈", "🥉"]
                badge  = medals[rank_idx - 1] if rank_idx <= 3 else f"#{rank_idx}"
                st.markdown(f"## {badge}")
                score_color = "#54A24B" if outfit["score"] >= 70 else (
                    "#EECA3B" if outfit["score"] >= 50 else "#E45756"
                )
                st.markdown(
                    f"<div style='font-size:2em;font-weight:bold;color:{score_color}'>"
                    f"{outfit['score']:.0f}</div><div style='color:#AAAAAA'>/ 100</div>",
                    unsafe_allow_html=True
                )

            with col_items:
                st.markdown(f"**Outfit #{rank_idx}** — {outfit['template']}")

                # Garment thumbnails / swatches
                item_cols = st.columns(min(len(outfit["items"]), 5))
                for i, item in enumerate(outfit["items"]):
                    with item_cols[i % len(item_cols)]:
                        photo = str(item.get("photo_path", "")).strip()
                        if photo and os.path.exists(photo):
                            try:
                                st.image(photo, use_column_width=True)
                            except Exception:
                                pass
                        else:
                            hex_color = item.get("color_hex") or "#808080"
                            st.markdown(
                                f"<div style='background:{hex_color};height:60px;"
                                f"border-radius:6px;margin-bottom:4px'></div>",
                                unsafe_allow_html=True
                            )
                        st.caption(f"{item.get('color','')} {item.get('category','')}")

                # ML prediction badge
                if ml_model:
                    ml_prob = predict_acceptance(outfit, occasion, wardrobe_df, ml_model)
                    if ml_prob is not None:
                        st.caption(
                            f"🤖 ML acceptance probability: **{ml_prob*100:.0f}%** "
                            f"*(based on trained feedback data)*"
                        )

            with col_score:
                st.markdown("**Score Breakdown**")
                comp = outfit.get("score_components", {})
                for k, v in comp.items():
                    label = k.replace("_", " ").title()
                    st.progress(int(v), text=f"{label}: {v:.0f}")

                if outfit.get("penalty", 0) > 0:
                    st.caption(f"⚠️ Repetition penalty: −{outfit['penalty']:.0f} pts")

            # Explanation
            with st.expander("📖 Why this outfit?"):
                st.markdown(outfit.get("explanation", "No explanation available."))
                items_list = ", ".join(
                    f"{i.get('color','')} {i.get('category','')}" for i in outfit["items"]
                )
                st.markdown(f"**Items:** {items_list}")

            # Action buttons
            act1, act2, act3 = st.columns(3)
            if act1.button("✅ Select This Outfit", key=f"select_{rank_idx}"):
                outfit_id, fb_id = record_outfit_selection(outfit, occasion, weather)
                st.session_state[f"selected_{rank_idx}"] = {"outfit_id": outfit_id, "fb_id": fb_id}
                st.success(f"Outfit saved! Now rate it below if you wear it.")
                st.rerun()

            # Rating (visible after selection)
            if f"selected_{rank_idx}" in st.session_state:
                selected_info = st.session_state[f"selected_{rank_idx}"]
                rating = act2.slider(
                    "Rate this outfit ⭐",
                    1, 5, 3,
                    key=f"rate_{rank_idx}"
                )
                if act3.button("💾 Save Rating", key=f"save_rate_{rank_idx}"):
                    from src.feedback_manager import save_rating
                    save_rating(selected_info["fb_id"], rating)
                    st.success("Rating saved!")

            st.markdown("---")

else:
    if wardrobe_df.empty:
        st.markdown("""
        <div style="background: #FFFFFF; border: 1.5px dashed #D5C7B8; border-radius: 14px; padding: 36px 24px; text-align: center; margin: 20px 0;">
            <div style="font-size: 36px; margin-bottom: 8px;">✨</div>
            <div style="font-family: 'Playfair Display', Georgia, serif; font-size: 20px; font-weight: 700; color: #241C18; margin-bottom: 6px;">
                Wardrobe Zero — Clean Slate
            </div>
            <div style="font-size: 14px; color: #704E38; max-width: 480px; margin: 0 auto 16px auto; line-height: 1.5;">
                Your wardrobe is currently empty (0 items). Add clothes from your almirah using <strong>Add Clothing</strong> to generate outfit combinations.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📷 Add Clothing from Almirah", type="primary"):
            st.switch_page("pages/2_Add_Clothing.py")
    else:
        # Landing state
        st.info(
            "👆 Use the **sidebar** to choose an occasion and weather, "
            "then click **Generate Recommendations**."
        )
        st.markdown("""
        **How it works:**
        1. FitChecker finds all valid combinations from your wardrobe.
        2. Each combination is scored across 5 dimensions.
        3. Outfits are ranked and the top results are shown.
        4. You can adjust the scoring weights in the sidebar.
        """)
