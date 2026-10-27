"""
pages/6_Feedback_and_History.py — View outfit history and manage feedback
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from src.feedback_manager import (
    get_history_display, get_feedback_stats,
    record_wear_confirmation, save_rating,
)
from src.data_manager import load_wardrobe
from src.theme_helper import apply_editorial_theme

st.set_page_config(page_title="Feedback & History — FitChecker", page_icon="📝", layout="wide")

# Apply full editorial theme: light brown sidebar, light brown text, warm selection
apply_editorial_theme()

st.title("📝 Feedback & History")
st.caption(
    "View your outfit selection history, confirm what you wore, "
    "and rate past recommendations."
)

wardrobe_df = load_wardrobe()
stats = get_feedback_stats()

# ── Summary metrics ──
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Recommendations", stats["total_recommendations"])
m2.metric("Outfits Selected",      stats["total_selected"])
m3.metric("Outfits Confirmed Worn", stats["total_worn"])
m4.metric("Average Rating",         f"{stats['avg_rating']}/5" if stats["avg_rating"] > 0 else "N/A")

st.markdown("---")

history = get_history_display(limit=100)

if history.empty:
    st.info("No outfit history yet. Generate and select outfits to build your history.")
    st.stop()

# ── Filter ──
col_f1, col_f2 = st.columns(2)
filter_occ = col_f1.multiselect(
    "Filter by Occasion",
    options=history["occasion"].dropna().unique().tolist()
)
filter_worn = col_f2.selectbox("Filter by Wear Status", ["All", "Worn", "Not Worn"])

filtered = history.copy()
if filter_occ:
    filtered = filtered[filtered["occasion"].isin(filter_occ)]
if filter_worn == "Worn":
    filtered = filtered[filtered["worn"].astype(str).str.lower().isin(("true", "1"))]
elif filter_worn == "Not Worn":
    filtered = filtered[~filtered["worn"].astype(str).str.lower().isin(("true", "1"))]

st.markdown(f"**{len(filtered)}** records shown")

# ── History cards ──
for _, row in filtered.iterrows():
    with st.container(border=True):
        col_info, col_actions = st.columns([3, 2])
        with col_info:
            worn_icon = "✅" if str(row.get("worn","")).lower() in ("true","1") else "⏳"
            rating    = int(row.get("user_rating", 0))
            stars     = "⭐" * rating if rating > 0 else "Not rated"
            st.markdown(
                f"{worn_icon} **{row.get('occasion','—')}** — "
                f"{str(row.get('timestamp',''))[:16]} | {stars}"
            )

            # Show outfit items
            item_ids_str = str(row.get("item_ids","")).strip()
            if item_ids_str and item_ids_str not in ("", "nan"):
                ids = [i.strip() for i in item_ids_str.split(";") if i.strip()]
                if not wardrobe_df.empty and ids:
                    items = wardrobe_df[wardrobe_df["item_id"].isin(ids)]
                    if not items.empty:
                        outfit_label = " + ".join(
                            f"{r['color']} {r['category']}" for _, r in items.iterrows()
                        )
                        st.caption(f"👗 {outfit_label}")

            score = row.get("generated_score","")
            if score and str(score) not in ("", "nan"):
                try:
                    st.caption(f"Score: {float(score):.1f}/100")
                except ValueError:
                    pass

        with col_actions:
            fb_id    = str(row.get("feedback_id",""))
            outfit_id = str(row.get("outfit_id",""))
            is_worn  = str(row.get("worn","")).lower() in ("true","1")

            if not is_worn:
                if st.button("✅ Mark as Worn", key=f"worn_{fb_id}"):
                    ids = [i.strip() for i in str(row.get("item_ids","")).split(";") if i.strip()]
                    record_wear_confirmation(
                        feedback_id=fb_id,
                        outfit_id=outfit_id,
                        item_ids=ids,
                        occasion=str(row.get("occasion","Daily College Wear")),
                    )
                    st.success("Marked as worn!")
                    st.rerun()

            current_rating = int(row.get("user_rating", 0))
            new_rating = st.select_slider(
                "Update Rating",
                options=[1, 2, 3, 4, 5],
                value=max(1, current_rating),
                key=f"rate_{fb_id}",
            )
            if st.button("💾 Save Rating", key=f"save_{fb_id}"):
                save_rating(fb_id, new_rating)
                st.success("Rating updated!")
                st.rerun()

st.markdown("---")

# ── Raw table export ──
with st.expander("📋 View as Table / Export"):
    show_cols = [c for c in ["timestamp","occasion","accepted","worn","user_rating",
                              "notes","outfit_id","is_sample"] if c in filtered.columns]
    st.dataframe(filtered[show_cols], use_container_width=True)
    csv = filtered[show_cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download History CSV",
        data=csv,
        file_name="fitchecker_history.csv",
        mime="text/csv",
    )
