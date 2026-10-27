# ✨ FitChecker & Muse Wardrobe — AI Editorial Wardrobe & Outfit Stylist

**FitChecker** is a private, editorial-style digital wardrobe and AI outfit stylist designed to help individuals curate their closet, discover high-harmony outfit combinations tailored to their **24-shade foundation complexion and physical silhouette**, and dress intentionally according to their **mood and daily plans**.

---

## 🌟 Key Features

### 1. 👤 Face & Complexion Analysis (24-Shade Palette System) (`src/skin_tone_analyzer.py`)
- **Direct 24-Shade Complexion Matching:** Maps real-world skin tones directly from a 24-shade foundation chart (Shades 01 to 24), completely free of seasonal jargon ("Cool Summer", "Cool Winter", "Warm Autumn", "Warm Spring").
- **7 Direct Color Palette Tiers:**
  - `Fair Porcelain & Rosy` (Shades 01, 02, 04, 07)
  - `Fair & Light Warm Peach` (Shades 03, 06, 09, 10)
  - `Light to Medium Olive & Neutral` (Shades 08, 11, 13)
  - `Medium Golden & Honey Tan` (Shades 12, 14, 15, 16)
  - `Rich Dusky & Caramel Bronze` (Shades 17, 18, 19, 20)
  - `Deep Espresso & Ebony` (Shades 21, 22, 23, 24)
  - `Vitiligo & Dual-Tone` (Shade 05)
- **Face Camera & Portrait Scanner:** Upload a photo or snap a camera portrait to isolate facial skin chrominance (YCrCb color space), measure undertone warmth, and match your exact shade number.
- **Garment Palette Badges:** Real-time badge classification for every piece:
  - `BEST MATCH`: Textbook harmonizer for your complexion palette.
  - `ADD WARMTH`: Warmth booster that adds radiance.
  - `STAPLE`: Versatile foundational neutral.
  - `OUTSIDE PALETTE`: Contrast piece recommended to balance with neutral layers.

### 2. 💭 "What Should I Wear?" — Mood & Natural Language Stylist (`src/mood_engine.py`)
- Freeform natural language prompt input:
  *(e.g., "Dinner with friends, polished but comfortable...", "Rainy day study at library", "Confident presentation, sharp and composed")*
- Instant mood, formality, weather, and intention extraction.
- Quick preset suggestion pills:
  - *Casual and comfortable*
  - *A polished work day*
  - *Dinner with friends*
  - *A special occasion*
  - *Packing for a trip*

### 3. 🖼️ Editorial Curated Outfit Cards (`src/editorial_recommender.py`)
Generates 3 distinct high-fashion curation perspectives:
- **`BEST MATCH` (89–94% Match):** Optimal balance of skin tone harmony, silhouette proportion, and occasion alignment.
- **`MORE RELAXED` (84–90% Match):** Easy, breathable silhouette prioritizing movement and laid-back comfort.
- **`MORE POLISHED` (86–92% Match):** Structured tailoring and elevated contrast for a composed presence.
- **Rich Editorial Commentary:** Styling paragraphs explaining fit synergy, color balance, and how the tones complement the wearer's skin undertones.

### 4. 🔍 Piece Details & "Pair With" Drawer
- Inspect any piece in your collection with high-resolution presentation and editorial **Colour Guidance**.
- Interactive **"Pair with"** drawer filtered by style (*ALL*, *CASUAL*, *WORK*, *DINNER*, *OCCASION*) with match percentages and fashion styling rationale.

### 5. 🧳 Packing Mode & Travel Capsules
- Enter trip destination and duration *(e.g., "Pack for 3 days in Lisbon")*.
- Automatically generates a weather-aware, mix-and-match mini capsule and day-by-day packing itinerary.

### 6. 📷 Garment Scanner & Catalogue Manager (`pages/2_Add_Clothing.py`)
- Scan pieces via camera or photo upload.
- Automated K-Means dominant color clustering.
- Immediate skin tone compatibility feedback.

---

## 📂 Project Structure

```
FitChecker/
├── app.py                         # Editorial Digital Wardrobe & Main Stylist
├── requirements.txt               # Dependencies
├── run_app.bat                    # Windows 1-click launcher
├── run_tests.bat                  # Pytest test suite runner
├── conftest.py                    # Pytest test fixtures
│
├── config/
│   ├── __init__.py
│   └── settings.py                # Paths, categories, occasions, scoring weights
│
├── data/
│   ├── sample_wardrobe.csv        # 25 curated sample garments
│   └── sample_feedback.csv        # Sample feedback records
│
├── pages/
│   ├── 1_My_Wardrobe.py           # Wardrobe inventory with palette badges
│   ├── 2_Add_Clothing.py          # Camera & photo garment scanner
│   ├── 3_Outfit_Recommendations.py# Advanced multi-weight outfit generator
│   ├── 4_Style_Preferences.py     # Personal style preferences
│   ├── 5_Wardrobe_Analytics.py    # Utilization %, Cost-Per-Wear, Variety scores
│   ├── 6_Feedback_and_History.py  # Outfit wear tracking & ratings
│   └── 7_About_the_Model.py       # Random Forest ML model transparency
│
├── src/
│   ├── skin_tone_analyzer.py      # Face analysis, undertone & seasonal palettes
│   ├── mood_engine.py             # Natural language plan & mood intent parser
│   ├── editorial_recommender.py   # 3-card curated outfits & "Pair With" engine
│   ├── analytics.py               # Utilization, Cost-Per-Wear, Variety score
│   ├── color_compatibility.py     # Color theory & HSV harmony
│   ├── data_manager.py            # Local storage & CSV/JSON CRUD
│   ├── feedback_manager.py        # Feedback logging & wear history
│   ├── garment_classifier.py      # Category prediction heuristics
│   ├── image_processor.py         # K-Means color extraction & LANCZOS resizing
│   ├── ml_model.py                # Random Forest re-ranking model
│   ├── outfit_generator.py        # Combinatorial outfit generator
│   ├── recommender.py             # Weighted scoring engine
│   └── wardrobe_manager.py        # Garment grouping & queries
│
└── tests/                         # 13 Automated Test Suites
```

---

## 🚀 How to Run

1. **Start the Web App:**
   ```powershell
   & "C:\Users\Dell\anaconda3\python.exe" -m streamlit run "D:\DATA SCIENCE\FitChecker\app.py"
   ```
   *(Or double-click `run_app.bat`)*

2. **Run All Tests:**
   ```powershell
   & "C:\Users\Dell\anaconda3\python.exe" -m pytest "D:\DATA SCIENCE\FitChecker\tests" -v
   ```
   *(Or double-click `run_tests.bat`)*

---

## 🔒 100% Private & Local Storage
- All photos, profiles, and wardrobe items are stored locally in `user_data/`.
- No cloud upload, no biometric databases, zero external tracking.
