"""
pages/7_About_the_Model.py — ML Training, Evaluation and Transparency
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from src.data_manager import load_feedback, load_wardrobe, load_outfits
from src.ml_model import train_model, load_model, FEATURE_NAMES
from config.settings import SCORE_WEIGHTS, ML_MODEL_FILE
from src.theme_helper import apply_editorial_theme

st.set_page_config(page_title="About the Model — FitChecker", page_icon="🤖", layout="wide")

# Apply full editorial theme: light brown sidebar, light brown text, warm selection
apply_editorial_theme()

st.title("🤖 About the Recommendation Model")
st.caption("Transparency report: how the scoring works and how the ML model is trained.")

tab1, tab2, tab3 = st.tabs(["📐 Baseline Scorer", "🌲 ML Model", "📊 Evaluation"])

# ─────────────────────────────────────────────
# TAB 1 — BASELINE SCORER
# ─────────────────────────────────────────────
with tab1:
    st.subheader("Baseline Weighted Scoring Formula")
    st.markdown("""
    Before any machine learning is involved, FitChecker uses a transparent,
    rule-based scoring system to rank outfit candidates.

    ### Formula

    ```
    Outfit Score =
        w₁ × Occasion Suitability      (0-100)
      + w₂ × Color Compatibility       (0-100)
      + w₃ × Style / Formality Match   (0-100)
      + w₄ × Weather Suitability       (0-100)
      + w₅ × Personal Preference       (0-100)
      − Repetition Penalty             (0-20 points)
    ```

    ### Current Default Weights
    """)

    weight_data = {
        "Component":   [k.replace("_", " ").title() for k in SCORE_WEIGHTS],
        "Weight":      [f"{v*100:.0f}%" for v in SCORE_WEIGHTS.values()],
        "Meaning":     [
            "How well the outfit's formality and style match the selected occasion",
            "How harmonious the garment colors are together",
            "How consistent the formality levels are within the outfit",
            "How suitable the garments are for the current weather",
            "How well the outfit matches the user's saved color and style preferences",
        ]
    }
    st.dataframe(pd.DataFrame(weight_data), use_container_width=True, hide_index=True)

    st.warning(
        "**⚠️ These weights are engineering defaults, not scientifically established values.** "
        "You can change them on the Recommendations page sidebar and observe the effect."
    )

    st.subheader("Color Compatibility Method")
    st.markdown("""
    Color compatibility is determined by two approaches (in priority order):

    1. **Curated Pair Table:** A manually verified lookup table of ~60 common color
       pairs with assigned compatibility scores. Based on common fashion color principles.

    2. **HSV Heuristic (fallback):** Converts colors to HSV color space and scores
       based on hue distance:
       - Complementary colors (~180° apart): Score 80
       - Analogous colors (<30° apart): Score 75
       - Neutral colors (low saturation): Score 82

    **Important:** Color compatibility is subjective and context-dependent.
    These scores represent common conventions, not objective truths.
    """)

    st.subheader("Repetition Penalty")
    st.markdown("""
    If any garment in an outfit was worn within the last 7 days, a penalty of up to
    **20 points** is applied (proportional to recency — 100% on day 0, 0% on day 7).

    **This penalty only applies when wear history is recorded.** If you haven't
    marked any outfits as worn, no penalty is applied.
    """)

# ─────────────────────────────────────────────
# TAB 2 — ML MODEL
# ─────────────────────────────────────────────
with tab2:
    st.subheader("Random Forest Classifier")
    st.markdown("""
    ### Why Random Forest?

    | Property | Reason it suits this project |
    |---|---|
    | Works on small datasets | We start with limited feedback data |
    | No GPU required | Trains in seconds on CPU |
    | Handles mixed features | Numbers + categories together |
    | Feature importance | Tells us what matters most |
    | Resistant to overfitting | Better than a single decision tree |

    ### What the Model Learns
    The model learns to predict whether a user will **accept** a recommended outfit
    (click "Select This Outfit") based on features of the outfit and occasion.

    ### Features Used
    """)

    feat_table = pd.DataFrame({
        "Feature":     FEATURE_NAMES,
        "Description": [
            "Occasion encoded as a number (e.g. 0=Daily, 1=Presentation…)",
            "Number of garments in the outfit",
            "Average formality across garments (1-5)",
            "Variance in formality (measures how mixed the outfit is)",
            "Whether footwear is included (0/1)",
            "Whether an outer layer (jacket/blazer) is included (0/1)",
            "Number of top garments in the outfit",
            "Total times-worn across all garments",
            "Whether any garment was worn in the last 7 days (0/1)",
        ]
    })
    st.dataframe(feat_table, use_container_width=True, hide_index=True)

    st.subheader("⚠️ Data Integrity Rules")
    st.markdown("""
    The model is only trained when:
    - ≥ 20 labelled feedback records exist
    - At least 2 distinct acceptance labels (accepted / not accepted)
    - Data is split into train/test BEFORE feature extraction (no leakage)
    - Class imbalance is addressed via `class_weight='balanced'`

    **Sample Data Disclaimer:**
    If training on sample data only, results are reported as **illustrative only**
    and cannot be used as evidence of real user preference learning.
    """)

    st.subheader("Train the Model")
    feedback_df = load_feedback()
    wardrobe_df = load_wardrobe()
    outfits_df  = load_outfits()

    n_feedback = len(feedback_df)
    st.metric("Available Feedback Records", n_feedback, help="Need at least 20 to train")

    if st.button("🚀 Train / Retrain Model", disabled=(n_feedback == 0)):
        with st.spinner("Training Random Forest…"):
            result = train_model(feedback_df, outfits_df, wardrobe_df)

        if result["status"] == "success":
            st.success(result["message"])
            m = result["metrics"]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Accuracy",  f"{m['accuracy']*100:.1f}%")
            c2.metric("Precision", f"{m['precision']*100:.1f}%")
            c3.metric("Recall",    f"{m['recall']*100:.1f}%")
            c4.metric("F1 Score",  f"{m['f1']*100:.1f}%")
            st.caption(f"Train: {m['n_train']} | Test: {m['n_test']} | Samples: {result['n_samples']}")

            if result.get("is_sample_only"):
                st.error(
                    "🔴 All training data is labeled sample data. "
                    "The numbers above are illustrative and do NOT reflect real user accuracy."
                )
        else:
            st.warning(f"**Could not train model:** {result['message']}")

    model_exists = os.path.exists(ML_MODEL_FILE)
    if model_exists:
        st.success(f"✅ A trained model is saved at `{ML_MODEL_FILE}`.")
    else:
        st.info("No trained model saved yet. Use the button above after collecting feedback.")

# ─────────────────────────────────────────────
# TAB 3 — EVALUATION
# ─────────────────────────────────────────────
with tab3:
    st.subheader("Evaluation Methodology")
    st.markdown("""
    ### Metrics Used

    | Metric | What it measures |
    |---|---|
    | **Accuracy** | Overall fraction of correct predictions |
    | **Precision** | Of outfits predicted as "accepted", what fraction were actually accepted |
    | **Recall** | Of outfits actually accepted, what fraction did the model identify |
    | **F1 Score** | Harmonic mean of precision and recall (balanced measure) |

    ### Why Not Just Use Accuracy?
    If 80% of outfits are "not accepted", a model that always predicts "not accepted"
    would score 80% accuracy but be useless. We use F1 and recall to catch this.

    ### Train / Test Split
    25% of data is held out for testing. The split is **stratified** — meaning both
    training and test sets have similar proportions of accepted/not-accepted outfits.

    ### Baseline Comparison
    | Method | Scoring approach |
    |---|---|
    | Baseline | Weighted formula (configurable rules) |
    | ML Model | Random Forest trained on feedback |

    The ML model is considered better when its acceptance rate on held-out data
    exceeds what would be achieved by always selecting the highest-baseline-scored outfit.

    ### Current Limitations
    - Small dataset: With fewer than 50 real feedback records, results have high variance.
    - Single user: The model cannot be personalised to multiple users without separate training.
    - No temporal validation: We do not yet test whether the model improves over time.
    - Sample data: Pre-loaded sample feedback cannot substitute for real user preferences.
    """)
