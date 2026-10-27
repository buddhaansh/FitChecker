"""
pages/5_Wardrobe_Analytics.py — Dashboard with charts and metrics
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from src.data_manager import load_wardrobe, load_feedback
from src.analytics import (
    wardrobe_utilization, cost_per_wear, outfit_variety_score,
    chart_category_distribution, chart_color_distribution,
    chart_wear_frequency, chart_formality_distribution,
    chart_utilization_gauge, chart_feedback_ratings,
)
from src.theme_helper import apply_editorial_theme

st.set_page_config(page_title="Wardrobe Analytics — FitChecker", page_icon="📊", layout="wide")

# Apply full editorial theme: light brown sidebar, light brown text, warm selection
apply_editorial_theme()

st.title("📊 Wardrobe Analytics")
st.caption("Understand your wardrobe patterns. All metrics are precisely defined below each chart.")

wardrobe_df = load_wardrobe()
feedback_df = load_feedback()

if wardrobe_df.empty:
    st.markdown("""
    <div style="background: #FFFFFF; border: 1.5px dashed #D5C7B8; border-radius: 14px; padding: 36px 24px; text-align: center; margin: 20px 0;">
        <div style="font-size: 36px; margin-bottom: 8px;">📊✨</div>
        <div style="font-family: 'Playfair Display', Georgia, serif; font-size: 20px; font-weight: 700; color: #241C18; margin-bottom: 6px;">
            Wardrobe Zero — Clean Slate
        </div>
        <div style="font-size: 14px; color: #704E38; max-width: 480px; margin: 0 auto 16px auto; line-height: 1.5;">
            Your wardrobe starts at <strong>0 items</strong>. Once you add clothes from your almirah, your color distributions, wear analytics, and cost-per-wear charts will display here.
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("📷 Add Clothing from Almirah", type="primary"):
        st.switch_page("pages/2_Add_Clothing.py")
    st.stop()

# ─────────────────────────────────────────────
# UTILIZATION SECTION
# ─────────────────────────────────────────────
st.subheader("🎯 Wardrobe Utilization")
obs_days = st.slider("Observation Period (days)", 7, 365, 30, key="obs_slider")
util = wardrobe_utilization(wardrobe_df, obs_days)

u1, u2, u3 = st.columns(3)
u1.metric("Total Garments",   util["total"])
u2.metric("Worn (recorded)",  util["worn_count"],
          help=f"Items with a recorded wear date within the last {obs_days} days")
u3.metric("Never Worn",       util["never_worn"],
          help="Items with zero wear records (may have been worn before app usage)")

gauge_bytes = chart_utilization_gauge(util["utilization_pct"])
st.image(gauge_bytes, use_column_width=False, width=500)
st.caption(
    f"**Definition:** Wardrobe Utilization = Garments worn in last {obs_days} days "
    f"/ Total garments × 100"
)
st.info(util["note"])

st.markdown("---")

# ─────────────────────────────────────────────
# CHARTS — TWO COLUMNS
# ─────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("📦 Items by Category")
    st.image(chart_category_distribution(wardrobe_df), use_column_width=True)

with col2:
    st.subheader("🎨 Color Distribution")
    st.image(chart_color_distribution(wardrobe_df), use_column_width=True)

col3, col4 = st.columns(2)

with col3:
    st.subheader("👗 Most Worn Garments")
    st.image(chart_wear_frequency(wardrobe_df), use_column_width=True)

with col4:
    st.subheader("👔 Formality Profile")
    st.image(chart_formality_distribution(wardrobe_df), use_column_width=True)

st.markdown("---")

# ─────────────────────────────────────────────
# FEEDBACK / RATING CHART
# ─────────────────────────────────────────────
if not feedback_df.empty:
    st.subheader("⭐ Recommendation Ratings")
    variety = outfit_variety_score(feedback_df)
    v1, v2, v3 = st.columns(3)
    v1.metric("Outfits Selected",   variety["accepted"])
    v2.metric("Unique Outfits",     variety["unique_outfits"])
    v3.metric("Variety Score",      f"{variety['variety_pct']}%",
              help="Unique outfits selected / total selections × 100")

    try:
        st.image(chart_feedback_ratings(feedback_df), use_column_width=False, width=500)
    except Exception:
        st.info("Not enough rating data to display the chart yet.")

st.markdown("---")

# ─────────────────────────────────────────────
# COST-PER-WEAR TABLE
# ─────────────────────────────────────────────
st.subheader("💸 Cost Per Wear")
cpw = cost_per_wear(wardrobe_df)
if cpw.empty:
    st.info(
        "No cost-per-wear data available. "
        "Add purchase prices and wear counts to your garments to see this table."
    )
else:
    st.caption(
        "**Definition:** Cost Per Wear = Purchase Price / Times Worn. "
        "Only items with both values available are shown."
    )
    st.dataframe(
        cpw.style.format({"purchase_price": "₹{:.0f}", "cost_per_wear": "₹{:.2f}"}),
        use_container_width=True
    )

# ─────────────────────────────────────────────
# UNDERUTILISED ITEMS
# ─────────────────────────────────────────────
st.markdown("---")
st.subheader("😴 Rarely Worn Items")
import pandas as pd
times_worn = pd.to_numeric(wardrobe_df["times_worn"], errors="coerce").fillna(0)
rarely = wardrobe_df[times_worn < 2].copy()
if rarely.empty:
    st.success("All garments have been worn at least twice — great wardrobe utilization!")
else:
    st.caption(
        f"**{len(rarely)} garments** have been worn fewer than 2 times. "
        "These items might benefit from being included in more outfit combinations."
    )
    show_cols = [c for c in ["category", "color", "times_worn", "last_worn", "notes", "is_sample"]
                 if c in rarely.columns]
    st.dataframe(rarely[show_cols], use_container_width=True)
