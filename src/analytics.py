"""
analytics.py — FitChecker Wardrobe Analytics
=============================================
PURPOSE:
  Compute wardrobe utilization metrics and generate charts for the
  Analytics Dashboard page.

METRICS DEFINED:
  • Wardrobe Utilization:
      = (Garments worn at least once in the observation period) /
        (Total garments) × 100
      IMPORTANT: Missing wear records mean "usage unrecorded",
      NOT "confirmed never worn".

  • Cost Per Wear:
      = Purchase Price / Times Worn
      Only shown when both values are available and times_worn > 0.

  • Outfit Variety:
      = Unique outfit combinations selected / Total recommendations made

BEGINNER NOTE:
  Matplotlib is a plotting library.  We use it to create bar charts,
  pie charts and histograms.  Each chart is saved to a BytesIO buffer
  and returned as an image, which Streamlit can display directly.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")   # Non-interactive backend for server environments
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from config.settings import CATEGORY_GROUP


# ─────────────────────────────────────────────
# CORE METRICS
# ─────────────────────────────────────────────

def wardrobe_utilization(wardrobe_df: pd.DataFrame,
                         observation_days: int = 30) -> dict:
    """
    Compute utilization for the observation period.

    Returns a dict:
      {
        "total":           int,
        "worn_count":      int,
        "never_worn":      int,
        "utilization_pct": float,
        "observation_days": int,
        "note":            str,   # Disclaimer about missing data
      }
    """
    if wardrobe_df is None or wardrobe_df.empty:
        return {"total": 0, "worn_count": 0, "never_worn": 0,
                "utilization_pct": 0.0, "observation_days": observation_days,
                "note": "No wardrobe data available."}

    cutoff = datetime.now() - timedelta(days=observation_days)
    times_worn = pd.to_numeric(wardrobe_df["times_worn"], errors="coerce").fillna(0)

    worn_count  = 0
    for _, row in wardrobe_df.iterrows():
        last = str(row.get("last_worn", "")).strip()
        if last and last not in ("", "nan", "None"):
            try:
                last_date = datetime.strptime(last, "%Y-%m-%d")
                if last_date >= cutoff:
                    worn_count += 1
            except ValueError:
                pass

    total    = len(wardrobe_df)
    never    = int((times_worn == 0).sum())
    util_pct = round(worn_count / total * 100, 1) if total > 0 else 0.0

    return {
        "total":            total,
        "worn_count":       worn_count,
        "never_worn":       never,
        "utilization_pct":  util_pct,
        "observation_days": observation_days,
        "note": (
            "⚠️ Items with no wear records are shown as 'unrecorded', not 'confirmed unused'. "
            "If you wore items before adding them to FitChecker, the count will be understated."
        ),
    }


def cost_per_wear(wardrobe_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute cost-per-wear for items with both purchase_price and times_worn > 0.
    Returns a filtered DataFrame with a new 'cost_per_wear' column.
    """
    df = wardrobe_df.copy()
    df["purchase_price"] = pd.to_numeric(df["purchase_price"], errors="coerce")
    df["times_worn"]     = pd.to_numeric(df["times_worn"],     errors="coerce").fillna(0)

    valid = df[(df["purchase_price"].notna()) & (df["times_worn"] > 0)].copy()
    if valid.empty:
        return pd.DataFrame()

    valid["cost_per_wear"] = (valid["purchase_price"] / valid["times_worn"]).round(2)
    return valid[["item_id", "category", "color", "times_worn",
                  "purchase_price", "cost_per_wear"]].sort_values("cost_per_wear")


def outfit_variety_score(feedback_df: pd.DataFrame) -> dict:
    """
    Compute outfit variety from feedback records.
    Returns {"accepted": int, "unique_outfits": int, "variety_pct": float}.
    """
    if feedback_df is None or feedback_df.empty:
        return {"accepted": 0, "unique_outfits": 0, "variety_pct": 0.0}

    accepted = feedback_df[
        feedback_df["accepted"].astype(str).str.lower().isin(("true", "1"))
    ]
    total_accepted  = len(accepted)
    unique_outfits  = accepted["outfit_id"].nunique() if not accepted.empty else 0
    variety_pct     = round(unique_outfits / total_accepted * 100, 1) if total_accepted > 0 else 0.0

    return {"accepted": total_accepted, "unique_outfits": unique_outfits, "variety_pct": variety_pct}


# ─────────────────────────────────────────────
# CHART GENERATORS  (return PNG bytes)
# ─────────────────────────────────────────────

CHART_STYLE = {
    "figure.facecolor": "#0E1117",
    "axes.facecolor":   "#1E2130",
    "axes.edgecolor":   "#3D4663",
    "text.color":       "#FAFAFA",
    "axes.labelcolor":  "#FAFAFA",
    "xtick.color":      "#FAFAFA",
    "ytick.color":      "#FAFAFA",
    "grid.color":       "#3D4663",
    "axes.grid":        True,
    "grid.alpha":       0.4,
}

PALETTE = ["#4C78A8", "#F58518", "#E45756", "#72B7B2", "#54A24B",
           "#EECA3B", "#B279A2", "#FF9DA6", "#9D755D", "#BAB0AC"]


def _fig_to_bytes(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=110)
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def chart_category_distribution(wardrobe_df: pd.DataFrame) -> bytes:
    """Horizontal bar chart: number of items per category."""
    with plt.rc_context(CHART_STYLE):
        counts = wardrobe_df["category"].value_counts().sort_values()
        fig, ax = plt.subplots(figsize=(7, max(3, len(counts) * 0.4)))
        colors  = [PALETTE[i % len(PALETTE)] for i in range(len(counts))]
        ax.barh(counts.index, counts.values, color=colors)
        ax.set_xlabel("Number of Garments")
        ax.set_title("Wardrobe by Category", fontsize=13, fontweight="bold")
        for i, v in enumerate(counts.values):
            ax.text(v + 0.05, i, str(v), va="center", fontsize=9)
        fig.tight_layout()
        return _fig_to_bytes(fig)


def chart_color_distribution(wardrobe_df: pd.DataFrame) -> bytes:
    """Pie chart: garment color distribution."""
    with plt.rc_context(CHART_STYLE):
        counts = wardrobe_df["color"].value_counts().head(10)
        fig, ax = plt.subplots(figsize=(6, 6))
        wedge_props = {"linewidth": 1, "edgecolor": "#0E1117"}
        ax.pie(
            counts.values,
            labels=counts.index,
            colors=[PALETTE[i % len(PALETTE)] for i in range(len(counts))],
            autopct="%1.0f%%",
            startangle=140,
            wedgeprops=wedge_props,
            textprops={"color": "#FAFAFA", "fontsize": 9},
        )
        ax.set_title("Color Distribution (Top 10)", fontsize=13, fontweight="bold")
        return _fig_to_bytes(fig)


def chart_wear_frequency(wardrobe_df: pd.DataFrame, top_n: int = 10) -> bytes:
    """Bar chart: most-worn garments."""
    with plt.rc_context(CHART_STYLE):
        df = wardrobe_df.copy()
        df["times_worn"] = pd.to_numeric(df["times_worn"], errors="coerce").fillna(0)
        df["label"] = df["color"].fillna("") + " " + df["category"].fillna("")
        top = df.nlargest(top_n, "times_worn")

        fig, ax = plt.subplots(figsize=(8, 4))
        colors = [PALETTE[i % len(PALETTE)] for i in range(len(top))]
        bars = ax.bar(top["label"], top["times_worn"], color=colors)
        ax.set_xlabel("Garment")
        ax.set_ylabel("Times Worn")
        ax.set_title("Most Worn Garments", fontsize=13, fontweight="bold")
        plt.xticks(rotation=35, ha="right", fontsize=8)
        for bar, val in zip(bars, top["times_worn"]):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.05, str(int(val)),
                    ha="center", va="bottom", fontsize=8)
        fig.tight_layout()
        return _fig_to_bytes(fig)


def chart_formality_distribution(wardrobe_df: pd.DataFrame) -> bytes:
    """Histogram: distribution of formality scores."""
    with plt.rc_context(CHART_STYLE):
        formalities = pd.to_numeric(wardrobe_df["formality"], errors="coerce").dropna()
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.hist(formalities, bins=[0.5, 1.5, 2.5, 3.5, 4.5, 5.5],
                color=PALETTE[0], edgecolor="#0E1117", alpha=0.85)
        ax.set_xlabel("Formality Score (1=Casual, 5=Formal)")
        ax.set_ylabel("Number of Items")
        ax.set_title("Wardrobe Formality Profile", fontsize=13, fontweight="bold")
        ax.set_xticks([1, 2, 3, 4, 5])
        ax.set_xticklabels(["1\nVery Casual", "2\nCasual", "3\nSmart Casual", "4\nFormal", "5\nVery Formal"])
        fig.tight_layout()
        return _fig_to_bytes(fig)


def chart_utilization_gauge(util_pct: float) -> bytes:
    """Simple gauge-style chart for utilization percentage."""
    with plt.rc_context(CHART_STYLE):
        fig, ax = plt.subplots(figsize=(5, 3))
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 1)
        ax.set_yticks([])

        # Background bar
        ax.barh([0.5], [100], height=0.4, color="#3D4663", left=0)
        # Filled bar
        color = "#54A24B" if util_pct >= 60 else ("#EECA3B" if util_pct >= 30 else "#E45756")
        ax.barh([0.5], [util_pct], height=0.4, color=color, left=0)
        ax.text(50, 0.5, f"{util_pct:.1f}%", ha="center", va="center",
                fontsize=20, fontweight="bold", color="#FAFAFA")
        ax.set_title("Wardrobe Utilization (Last 30 days)", fontsize=12, fontweight="bold")
        ax.set_xlabel("Percentage of Garments Worn")
        fig.tight_layout()
        return _fig_to_bytes(fig)


def chart_feedback_ratings(feedback_df: pd.DataFrame) -> bytes:
    """Bar chart: distribution of user ratings."""
    with plt.rc_context(CHART_STYLE):
        ratings = pd.to_numeric(feedback_df["user_rating"], errors="coerce")
        ratings = ratings[ratings > 0]
        counts  = ratings.value_counts().sort_index()

        fig, ax = plt.subplots(figsize=(5, 3))
        ax.bar(counts.index.astype(str), counts.values, color=PALETTE[1])
        ax.set_xlabel("Rating (Stars)")
        ax.set_ylabel("Number of Feedbacks")
        ax.set_title("User Rating Distribution", fontsize=13, fontweight="bold")
        fig.tight_layout()
        return _fig_to_bytes(fig)
