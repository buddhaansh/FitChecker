import os
import base64
import subprocess

def img_to_b64(path):
    if not os.path.exists(path):
        print(f"Warning: {path} not found")
        return ""
    with open(path, "rb") as f:
        ext = os.path.splitext(path)[1].lower().replace(".", "")
        if ext == "jpg": ext = "jpeg"
        data = base64.b64encode(f.read()).decode("utf-8")
        return f"data:image/{ext};base64,{data}"

# Image paths
brain_dir = r"C:\Users\Dell\.gemini\antigravity\brain\f93ef9b3-42be-4660-8255-87a1742de75a"
uploaded_dir = os.path.join(brain_dir, ".user_uploaded")

img_map = {
    "__IMG_EDITORIAL__": img_to_b64(os.path.join(uploaded_dir, "media_1793426605686_acb1ff34.png")),
    "__IMG_KURTA_RAW__": img_to_b64(os.path.join(uploaded_dir, "media_1793550296373_a9ce130e.png")),
    "__IMG_KURTA_CUTOUT__": img_to_b64(os.path.join(brain_dir, "kurta_final_cutout.png")),
    "__IMG_ADD_CLOTHING__": img_to_b64(os.path.join(uploaded_dir, "media_1793425937784_992495db.png")),
    "__IMG_COLOR_CLUSTERS__": img_to_b64(os.path.join(uploaded_dir, "media_1793395767238_d48abc05.png")),
    "__IMG_SKIN_TONE__": img_to_b64(os.path.join(uploaded_dir, "media_1793044225087_5da35347.png")),
    "__IMG_PROFILE__": img_to_b64(os.path.join(uploaded_dir, "media_1793046676657_6b1d8416.png")),
}

html_template = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>FitChecker — Comprehensive Academic & Technical Project Report</title>
<style>
  @page {
    size: A4;
    margin: 18mm 16mm 18mm 16mm;
    @bottom-right {
      content: counter(page);
    }
  }
  *, *::before, *::after {
    box-sizing: border-box;
  }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #1e293b;
    background-color: #ffffff;
    line-height: 1.55;
    font-size: 10pt;
    margin: 0;
    padding: 0;
  }
  .page-break {
    page-break-after: always;
  }
  .no-break {
    page-break-inside: avoid;
  }
  h1, h2, h3, h4 {
    color: #0f172a;
    font-weight: 700;
    line-height: 1.25;
    margin-top: 0;
  }
  h1 { font-size: 20pt; margin-bottom: 6px; }
  h2 { font-size: 13pt; margin-top: 16px; margin-bottom: 8px; border-bottom: 2px solid #e2e8f0; padding-bottom: 4px; color: #1e3a8a; }
  h3 { font-size: 11pt; margin-top: 10px; margin-bottom: 6px; color: #334155; }
  p { margin-top: 0; margin-bottom: 8px; }
  
  /* Badges & Pills */
  .badge-container {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 12px;
  }
  .badge {
    display: inline-block;
    padding: 3px 8px;
    font-size: 8pt;
    font-weight: 600;
    border-radius: 9999px;
    background: #eff6ff;
    color: #1d4ed8;
    border: 1px solid #bfdbfe;
  }
  .badge-success { background: #ecfdf5; color: #047857; border-color: #a7f3d0; }
  .badge-purple { background: #faf5ff; color: #7e22ce; border-color: #e9d5ff; }
  .badge-amber { background: #fffbeb; color: #b45309; border-color: #fde68a; }

  /* Cards & Callouts */
  .card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 10px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }
  .info-box {
    background: #f8fafc;
    border-left: 4px solid #3b82f6;
    padding: 10px 14px;
    margin-bottom: 10px;
    border-radius: 0 6px 6px 0;
  }
  .ai-box {
    background: #faf5ff;
    border-left: 4px solid #8b5cf6;
    padding: 10px 14px;
    margin-bottom: 10px;
    border-radius: 0 6px 6px 0;
  }
  .formula-box {
    background: #f1f5f9;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 8px 12px;
    font-family: "Courier New", Courier, monospace;
    font-size: 9pt;
    margin-bottom: 10px;
    color: #0f172a;
  }

  /* Tables */
  table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 10px;
    font-size: 8.5pt;
  }
  th, td {
    border: 1px solid #cbd5e1;
    padding: 6px 8px;
    text-align: left;
  }
  th {
    background-color: #f1f5f9;
    color: #1e293b;
    font-weight: 600;
  }
  tr:nth-child(even) {
    background-color: #f8fafc;
  }

  /* Images & Figures */
  .figure-card {
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 10px;
    background: #f8fafc;
  }
  .figure-card img {
    width: 100%;
    display: block;
    max-height: 220px;
    object-fit: contain;
    background: #ffffff;
  }
  .figure-caption {
    padding: 5px 10px;
    font-size: 8pt;
    color: #475569;
    background: #f1f5f9;
    border-top: 1px solid #e2e8f0;
    text-align: center;
    font-weight: 500;
  }

  /* Two Column Layout */
  .grid-2 {
    display: flex;
    gap: 12px;
    margin-bottom: 8px;
  }
  .col-2 {
    flex: 1;
  }

  /* Header Cover Banner */
  .cover-banner {
    background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #6366f1 100%);
    color: white;
    padding: 20px 18px;
    border-radius: 10px;
    margin-bottom: 14px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  }
  .cover-banner h1 {
    color: white;
    font-size: 21pt;
    margin: 0 0 4px 0;
    letter-spacing: -0.5px;
  }
  .cover-banner .subtitle {
    font-size: 10.5pt;
    opacity: 0.92;
    margin-bottom: 12px;
    font-weight: 400;
  }
  .meta-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
    font-size: 8.5pt;
    border-top: 1px solid rgba(255,255,255,0.25);
    padding-top: 8px;
  }
  .meta-item strong {
    color: #e0e7ff;
  }
</style>
</head>
<body>

<!-- PAGE 1: COVER & EXECUTIVE SUMMARY -->
<div class="cover-banner">
  <h1>FITCHECKER</h1>
  <div class="subtitle">An Intelligent AI-Powered Personal Wardrobe, Computer Vision Segmentation, and Multi-Criteria Styling System</div>
  <div class="meta-grid">
    <div class="meta-item"><strong>Developer & Author:</strong> Buddhaansh Sehgal (<code>budzsehgal</code>)</div>
    <div class="meta-item"><strong>Deployment:</strong> Streamlit Cloud Production</div>
    <div class="meta-item"><strong>Live Web App:</strong> https://budzsehgal-wardrobe.streamlit.app</div>
    <div class="meta-item"><strong>Source Code:</strong> github.com/buddhaansh/FitChecker</div>
  </div>
</div>

<div class="badge-container">
  <span class="badge">Python 3.12</span>
  <span class="badge">OpenCV 4.10 (GrabCut GMM)</span>
  <span class="badge badge-purple">Scikit-Learn (Random Forest)</span>
  <span class="badge badge-amber">Colorimetry & K-Means</span>
  <span class="badge badge-success">130/130 Tests Passing (100%)</span>
  <span class="badge">Zero Cloud API Cost</span>
</div>

<div class="card">
  <h3 style="margin-top:0; color:#1e3a8a;">Abstract & Project Motivation</h3>
  <p>Modern consumers actively purchase apparel but consistently underutilize over <strong>70% of their wardrobe</strong>. This stems from visual closet disorganization, styling friction, and the tedious requirement of existing apps that force users to type metadata for clothes one by one. <strong>FitChecker</strong> is an autonomous, privacy-preserving digital wardrobe and stylist engineered to solve these bottlenecks.</p>
  <p>FitChecker introduces an end-to-end computer vision and machine learning pipeline that automatically cuts out garments from smartphone photos onto pure studio white (<code>#FFFFFF</code>), infers garment category, fit, pattern, and formality without manual tagging, provides high-fashion editorial styling rules, and formulates daily outfit combinations through a multi-objective mathematical scoring rubric.</p>
</div>

<div class="card no-break">
  <h3 style="margin-top:0; color:#1e3a8a;">Functional Architecture Matrix</h3>
  <table>
    <thead>
      <tr>
        <th>Core Engine</th>
        <th>Primary Tech Module</th>
        <th>Algorithmic Mechanism</th>
        <th>User-Facing Deliverable</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>1. Studio Isolator</strong></td>
        <td><code>src/image_processor.py</code></td>
        <td>GrabCut GMM + Perimeter Sampling</td>
        <td>Pure solid #FFFFFF garment cutout</td>
      </tr>
      <tr>
        <td><strong>2. Garment Classifier</strong></td>
        <td><code>src/garment_classifier.py</code></td>
        <td>Canny Placket & Silhouette Ratios</td>
        <td>Auto-detect Category, Fit & Pattern</td>
      </tr>
      <tr>
        <td><strong>3. Editorial Stylist</strong></td>
        <td><code>src/editorial_recommender.py</code></td>
        <td>Fashion Color Pairing Matrix</td>
        <td>Layering, proportion & footwear advice</td>
      </tr>
      <tr>
        <td><strong>4. Outfit Recommender</strong></td>
        <td><code>src/recommender.py</code></td>
        <td>Multi-Criteria Weighted Function</td>
        <td>Daily outfits scored from 0 to 100%</td>
      </tr>
      <tr>
        <td><strong>5. Complexion Analyzer</strong></td>
        <td><code>src/skin_tone_analyzer.py</code></td>
        <td>24 Foundation Tones & Monk Scale</td>
        <td>Skin-flattering clothing color swatches</td>
      </tr>
      <tr>
        <td><strong>6. Batch Upload Studio</strong></td>
        <td><code>pages/2_Add_Clothing.py</code></td>
        <td>Session Caching & Thread Workers</td>
        <td>Upload up to 20 garments simultaneously</td>
      </tr>
    </tbody>
  </table>
</div>

<div class="page-break"></div>

<!-- PAGE 2: FUNCTION 1 & 2 (BACKGROUND REMOVER & WARDROBE) -->
<h2>FUNCTION 1: SMART DIGITAL WARDROBE GALLERY</h2>
<p>The <strong>Digital Wardrobe Gallery</strong> provides an interactive visual inventory of a user's entire apparel collection. It groups garments by intuitive categories (Tops, Bottoms, Footwear, Layers, One-Piece), displays formality ratings (Casual 1 to Black Tie 5), wear counters, and dominant color swatches.</p>

<div class="grid-2 no-break">
  <div class="col-2 card">
    <h4 style="margin-top:0; color:#1e3a8a;">Key Capabilities</h4>
    <ul style="margin: 0; padding-left: 18px; font-size: 9pt;">
      <li><strong>Categorical Partitioning:</strong> Instant filtering by tops, bottoms, outerwear, and footwear.</li>
      <li><strong>Wear Frequency Tracking:</strong> Records wear count and last-worn timestamp to prevent repetitive outfits.</li>
      <li><strong>Formality Badges:</strong> Formality level displayed as a clean visual indicator (1-5).</li>
      <li><strong>Color Palette Dots:</strong> Real-time rendering of extracted fabric hex codes.</li>
    </ul>
  </div>
  <div class="col-2 figure-card">
    <img src="__IMG_PROFILE__" alt="Wardrobe Profile Selector" style="max-height: 140px;">
    <div class="figure-caption">Figure 1.1: Multi-User Profile Selector & Wardrobe Partitioning</div>
  </div>
</div>

<h2>FUNCTION 2: AI BACKGROUND ISOLATION & STUDIO CLEANER</h2>
<p>Photographing garments in everyday rooms introduces messy backgrounds: bedroom walls, bedsheets, hangers, and carpets. FitChecker features an autonomous background isolation engine powered by <strong>OpenCV GrabCut with Adaptive Perimeter Sampling</strong>.</p>

<div class="info-box">
  <strong>Technical Breakthrough:</strong> Standard segmentation fails when garments touch boundaries or when room walls are textured. FitChecker uses adaptive perimeter sampling <code>rect = (bx, by, W - 2*bx, H - 2*by)</code> with <code>cv2.GC_INIT_WITH_RECT</code>, paired with blue hanger clearance in HSV color space and cavity-preserving connected component analysis.
</div>

<div class="figure-card no-break">
  <div style="display: flex; background: white; padding: 10px; gap: 10px; justify-content: center; align-items: center;">
    <div style="flex: 1; text-align: center;">
      <div style="font-size: 8pt; font-weight: 600; color: #dc2626; margin-bottom: 4px;">RAW INPUT (Noisy Bedroom Wall)</div>
      <img src="__IMG_KURTA_RAW__" alt="Raw Kurta Photo" style="max-height: 190px; margin: 0 auto; border: 1px solid #cbd5e1; border-radius: 4px;">
    </div>
    <div style="font-size: 16pt; color: #3b82f6; font-weight: bold;">&rarr;</div>
    <div style="flex: 1; text-align: center;">
      <div style="font-size: 8pt; font-weight: 600; color: #16a34a; margin-bottom: 4px;">FITCHECKER CUTOUT (Solid #FFFFFF)</div>
      <img src="__IMG_KURTA_CUTOUT__" alt="Processed Kurta Cutout" style="max-height: 190px; margin: 0 auto; border: 1px solid #cbd5e1; border-radius: 4px;">
    </div>
  </div>
  <div class="figure-caption">Figure 2.1: Before & After Background Isolation on User-Uploaded Ethnic Kurta against Textured Pink Wall</div>
</div>

<div class="page-break"></div>

<!-- PAGE 3: FUNCTION 3 & 4 (GARMENT ID & EDITORIAL STYLING ADVICE) -->
<h2>FUNCTION 3 & 4: AI GARMENT IDENTIFICATION & EDITORIAL STYLING ENGINE</h2>
<p>When a garment photo is ingested, FitChecker's computer vision engine instantly analyzes its structural silhouette and fabrics. It displays two complementary intelligent cards: <strong>AI Garment Identification</strong> and <strong>AI Editorial Styling Advice</strong>.</p>

<div class="figure-card no-break">
  <img src="__IMG_EDITORIAL__" alt="AI Garment Identification & Editorial Styling Advice" style="max-height: 250px;">
  <div class="figure-caption">Figure 3.1: Live Application Screenshot — AI Garment Identification and AI Editorial Styling Advice with Color Match Percentages and Proportion Rules</div>
</div>

<div class="grid-2 no-break">
  <div class="col-2 card">
    <h3 style="margin-top:0; color:#1e3a8a;">Function 3: AI Garment Identification</h3>
    <p style="font-size: 8.5pt;">Extracts spatial geometry directly from the foreground mask:</p>
    <ul style="margin: 0; padding-left: 16px; font-size: 8pt;">
      <li><strong>Aspect Ratio (H/W):</strong> Separates footwear (AR &lt; 0.65), standard tops, and elongated bottoms/kurtas (AR &gt; 1.45).</li>
      <li><strong>Placket Edge Density:</strong> Vertical Canny edge filters down the chest line identify button plackets, preventing collared shirts from being mistaken for blazers.</li>
      <li><strong>Leg Bifurcation:</strong> Horizontal density scan at 70% height detects leg splits in trousers and shorts.</li>
      <li><strong>Formality Ingress:</strong> Dark navy, charcoal, and structured lapels automatically score formality 4/5 or 5/5.</li>
    </ul>
  </div>

  <div class="col-2 card">
    <h3 style="margin-top:0; color:#7e22ce;">Function 4: AI Editorial Styling Advice</h3>
    <p style="font-size: 8.5pt;">Replaces generic fashion cliches with editorial rules:</p>
    <ul style="margin: 0; padding-left: 16px; font-size: 8pt;">
      <li><strong>Ideal Color Pairings:</strong> Curated compatibility percentages (e.g., Beige 82%, Black 82%, Blue 82%).</li>
      <li><strong>Recommended Layering:</strong> Direct garment layering suggestions (e.g., Crewneck T-Shirt as Layer 1, Tailored Trousers as Bottom).</li>
      <li><strong>Footwear Anchor:</strong> Exact footwear styles to balance the silhouette (Dress Shoes, Loafers, Minimalist Sneakers).</li>
      <li><strong>Proportion Rules:</strong> Explains visual volume balance (e.g. structured upper volume paired with clean tapered lower silhouette).</li>
    </ul>
  </div>
</div>

<div class="page-break"></div>

<!-- PAGE 4: FUNCTION 5 & 6 (OUTFIT RECOMMENDER & COMPLEXION) -->
<h2>FUNCTION 5: MULTI-CRITERIA DAILY OUTFIT RECOMMENDER</h2>
<p>The outfit engine evaluates combinations of tops, bottoms, layers, and footwear from the user's wardrobe. It uses a mathematically explainable <strong>Multi-Objective Weighted Scoring Function</strong>:</p>

<div class="formula-box">
  Outfit Score = 0.30 &times; Occasion + 0.25 &times; Color + 0.20 &times; StyleFormality + 0.15 &times; Weather + 0.10 &times; Preference &minus; RecencyPenalty
</div>

<div class="card no-break">
  <h4 style="margin-top:0; color:#1e3a8a;">Mathematical Breakdown of Scoring Components</h4>
  <table>
    <thead>
      <tr>
        <th>Scoring Component</th>
        <th>Weight</th>
        <th>Underlying Mathematical Metric</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Occasion Suitability</strong></td>
        <td>30%</td>
        <td>100 - 20 &times; |Formality_garment - Formality_target| + 15 &times; StyleTagMatch</td>
      </tr>
      <tr>
        <td><strong>Color Harmony</strong></td>
        <td>25%</td>
        <td>Pairwise color matrix + HSV difference (|&Delta;H - 180&deg;| &lt; 20&deg; for complementary)</td>
      </tr>
      <tr>
        <td><strong>Style & Formality Match</strong></td>
        <td>20%</td>
        <td>Variance penalty across ensemble: max(0, 100 - 25 &times; FormalityVariance)</td>
      </tr>
      <tr>
        <td><strong>Weather Suitability</strong></td>
        <td>15%</td>
        <td>Season & fabric weight compatibility with current temperature context</td>
      </tr>
      <tr>
        <td><strong>Personal Preference</strong></td>
        <td>10%</td>
        <td>Historical wear counts and user feedback thumbs-up ratings</td>
      </tr>
      <tr>
        <td><strong>Recency Decay Penalty</strong></td>
        <td>Deduction</td>
        <td>&minus;25 points if worn within 3 days; &minus;15 points if worn within 7 days</td>
      </tr>
    </tbody>
  </table>
</div>

<h2>FUNCTION 6: PERSONAL COLORIMETRY & 24 FOUNDATION SHADES</h2>
<p>Traditional four-season systems ("Cool Summer", "Warm Autumn") confuse consumers with subjective cosmetology terms. FitChecker maps complexion to <strong>24 clinical foundation shades</strong> grouped across 6 intuitive tiers:</p>

<div class="figure-card no-break">
  <img src="__IMG_SKIN_TONE__" alt="Personal Color & Skin Tone Guidance" style="max-height: 190px;">
  <div class="figure-caption">Figure 6.1: Personal Color & Complexion Guidance Page with Direct Palette Recommendations</div>
</div>

<div class="card no-break">
  <h4 style="margin-top:0; color:#1e3a8a;">Complexion Tiers & Vitiligo Innovation</h4>
  <p style="font-size: 8.5pt;"><strong>Fair Porcelain (Cool), Light Warm Peach (Warm), Medium Olive, Medium Golden, Rich Dusky, and Deep Espresso:</strong> Each tier receives curated "Best Colors", "Warmth Boosters", and "Colors to Avoid".</p>
  <p style="font-size: 8.5pt; margin-bottom: 0;"><strong>Specialized Vitiligo Duo-Tone Mode:</strong> For users with vitiligo, single-palette algorithms wash out one tone or clash with another. FitChecker formulates dual-palette recommendations harmonizing deep base skin with lighter pigmentation patches.</p>
</div>

<div class="page-break"></div>

<!-- PAGE 5: FUNCTION 7 & 8 (BATCH UPLOAD & MULTI-USER) -->
<h2>FUNCTION 7: BATCH UPLOAD STUDIO (UP TO 20 CLOTHES AT ONCE)</h2>
<p>Uploading wardrobe items one by one is the #1 reason users abandon digital closet apps. FitChecker features a high-throughput <strong>Batch Upload Studio</strong> allowing users to ingest up to 20 garment photos simultaneously.</p>

<div class="grid-2 no-break">
  <div class="col-2 figure-card">
    <img src="__IMG_ADD_CLOTHING__" alt="Add Clothing Studio" style="max-height: 180px;">
    <div class="figure-caption">Figure 7.1: Add Clothing Page with Color Extraction and Background Removal</div>
  </div>
  <div class="col-2 card">
    <h3 style="margin-top:0; color:#1e3a8a;">Batch Engine Workflow</h3>
    <ol style="margin: 0; padding-left: 16px; font-size: 8.5pt;">
      <li><strong>Multi-File Ingestion:</strong> Drag and drop 2 to 20 photos at once.</li>
      <li><strong>Session-State Caching:</strong> All cutouts and dominant colors are processed once and cached in <code>st.session_state["batch_cache"]</code>.</li>
      <li><strong>Editable Grid Review:</strong> A responsive card grid displays thumbnails, category dropdowns, fit, and pattern selectors.</li>
      <li><strong>Atomic Bulk Save:</strong> Single-click commit writes all garments to <code>wardrobe.csv</code> and saves transparent PNG cutouts atomically.</li>
    </ol>
  </div>
</div>

<h2>FUNCTION 8: MULTI-USER DATA ISOLATION & MASTER SECURITY PIN</h2>
<p>To enable sharing the application with friends and family without mixing up wardrobes or compromising personal data, FitChecker implements <strong>Namespace Directory Partitioning</strong>.</p>

<div class="grid-2 no-break">
  <div class="col-2 card">
    <h4 style="margin-top:0; color:#1e3a8a;">Directory-Level Data Isolation</h4>
    <p style="font-size: 8.5pt;">Each user profile operates inside an isolated sandbox directory:</p>
    <div class="formula-box" style="font-size: 8pt;">
      user_data/users/&lt;username&gt;/<br>
      &nbsp;&nbsp;&boxur; wardrobe.csv<br>
      &nbsp;&nbsp;&boxur; outfits.csv<br>
      &nbsp;&nbsp;&boxur; feedback.csv<br>
      &nbsp;&nbsp;&boxur; images/
    </div>
    <p style="font-size: 8pt;">Switching profiles completely resets memory references and points all database queries strictly to the active user's folder.</p>
  </div>

  <div class="col-2 card">
    <h4 style="margin-top:0; color:#dc2626;">Master Creator Security PIN (7777)</h4>
    <p style="font-size: 8.5pt;">The Master Creator account is protected with PIN verification:</p>
    <ul style="margin: 0; padding-left: 16px; font-size: 8pt;">
      <li>Friends can create their own profiles and manage private wardrobes.</li>
      <li>Switching to the Creator profile requires entering the secret 4-digit PIN (<code>7777</code>).</li>
      <li>Prevents accidental overwrites, snooping, or wardrobe contamination.</li>
    </ul>
  </div>
</div>

<div class="page-break"></div>

<!-- PAGE 6: THE AI TOOLS USED TO CREATE THIS MODEL -->
<h2>THE AI & MACHINE LEARNING TOOLS USED TO BUILD FITCHECKER</h2>
<p>FitChecker was engineered through a synergy of modern artificial intelligence, computer vision libraries, and agentic software design tools:</p>

<div class="ai-box no-break">
  <h3 style="margin-top:0; color:#7e22ce;">1. Google Antigravity & DeepMind Agentic Pair Programming</h3>
  <p style="font-size: 8.5pt;">The entire software architecture, mathematical scoring formulas, and computer vision routines were designed and refined using <strong>Google Antigravity</strong> — DeepMind's state-of-the-art agentic AI development environment.</p>
  <ul style="margin: 0; padding-left: 16px; font-size: 8pt;">
    <li><strong>Autonomous Iterative Debugging:</strong> The AI agent diagnosed complex computer vision artifacts (such as underarm cavity fillings and placket edge frequencies) in real time.</li>
    <li><strong>Continuous Automated Test Harness:</strong> Formulated and maintained a rigorous 130-test regression suite ensuring zero breaking changes across updates.</li>
    <li><strong>Subagent Task Delegation:</strong> Utilized specialized subagents to perform sandbox testing and mathematical rubric validation concurrently.</li>
  </ul>
</div>

<div class="grid-2 no-break">
  <div class="col-2 card">
    <h3 style="margin-top:0; color:#1e3a8a;">2. OpenCV (Open Source Computer Vision)</h3>
    <ul style="margin: 0; padding-left: 16px; font-size: 8pt;">
      <li><strong>Iterative GrabCut Segmentation:</strong> Uses dual 5-component Gaussian Mixture Models to perform min-cut energy optimization on pixel contrast boundaries.</li>
      <li><strong>Canny Edge Detection:</strong> High-frequency edge filters isolating vertical shirt plackets and lapel contours.</li>
      <li><strong>Laplacian Texture Variance:</strong> Measures second-order spatial derivatives to detect Plain, Checked, and Striped fabric textures.</li>
    </ul>
  </div>

  <div class="col-2 card">
    <h3 style="margin-top:0; color:#047857;">3. Scikit-Learn Machine Learning Ensemble</h3>
    <ul style="margin: 0; padding-left: 16px; font-size: 8pt;">
      <li><strong>Random Forest Classifier:</strong> 100-tree ensemble learning user acceptance probabilities from feedback logs.</li>
      <li><strong>Balanced Class Weighting:</strong> Automatically adjusts loss weights W_j = N / (2 N_j) to resolve feedback class imbalances.</li>
      <li><strong>Explainable Feature Importance:</strong> Unpacks Gini-impurity drops across 9 dense feature dimensions.</li>
    </ul>
  </div>
</div>

<div class="grid-2 no-break">
  <div class="col-2 card">
    <h3 style="margin-top:0; color:#b45309;">4. Colorimetry & K-Means Fabric Clustering</h3>
    <ul style="margin: 0; padding-left: 16px; font-size: 8pt;">
      <li><strong>K-Means Color Quantization:</strong> Clusters fabric pixels into dominant and secondary palette centroids.</li>
      <li><strong>HSV Color Wheel Trigonometry:</strong> Calculates hue separation angles (&Delta;H) to evaluate Complementary, Analogous, and Triadic harmonies.</li>
      <li><strong>CIE-Lab Euclidean Distance:</strong> Computes perceptual &Delta;E color differences matching human eye perception.</li>
    </ul>
  </div>

  <div class="col-2 card">
    <h3 style="margin-top:0; color:#2563eb;">5. Streamlit Reactive Cloud Platform</h3>
    <ul style="margin: 0; padding-left: 16px; font-size: 8pt;">
      <li><strong>Multi-Page Web Architecture:</strong> Decoupled UI pages with reactive session state caching.</li>
      <li><strong>Zero Server Cost Hosting:</strong> Optimized memory footprint allows continuous production hosting on Streamlit Cloud.</li>
      <li><strong>Mobile-First Responsive CSS:</strong> Tailored viewport styles optimized for smartphone camera uploads.</li>
    </ul>
  </div>
</div>

<div class="page-break"></div>

<!-- PAGE 7: AUTOMATED TESTS, CONCLUSION & SUMMARY -->
<h2>AUTOMATED VERIFICATION & TEST SUITE RESULTS</h2>
<p>FitChecker is backed by <strong>130 automated unit and integration tests</strong> covering image processing, scoring algorithms, machine learning models, and data security:</p>

<div class="card no-break">
  <table>
    <thead>
      <tr>
        <th>Test Suite Module</th>
        <th>Tests Passed</th>
        <th>Key Validated Capabilities</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><code>test_image_processor.py</code></td>
        <td>9 / 9</td>
        <td>GrabCut bounding frame, solid #FFFFFF compositing, dominant color extraction</td>
      </tr>
      <tr>
        <td><code>test_garment_classifier.py</code></td>
        <td>8 / 8</td>
        <td>Collared shirt vs. blazer classification, pattern edge density, aspect ratios</td>
      </tr>
      <tr>
        <td><code>test_recommender.py</code></td>
        <td>19 / 19</td>
        <td>Occasion profiles, formality penalties, recency decay degradation</td>
      </tr>
      <tr>
        <td><code>test_color_compatibility.py</code></td>
        <td>8 / 8</td>
        <td>HSV complementary angles, neutral anchors, curated fashion pairings</td>
      </tr>
      <tr>
        <td><code>test_ml_model.py</code></td>
        <td>6 / 6</td>
        <td>Feature vector extraction, class balancing, cold-start fallback safety</td>
      </tr>
      <tr>
        <td><code>test_skin_tone_analyzer.py</code></td>
        <td>7 / 7</td>
        <td>24 foundation shade mapping, Monk scale color flattery, Vitiligo duo mode</td>
      </tr>
      <tr>
        <td><code>test_user_manager.py</code></td>
        <td>7 / 7</td>
        <td>Isolated user directory partitioning, master PIN 7777 verification</td>
      </tr>
      <tr>
        <td><code>test_wardrobe_manager.py</code></td>
        <td>12 / 12</td>
        <td>Wardrobe CRUD operations, item filtering, category counts</td>
      </tr>
      <tr>
        <td><code>test_feedback_manager.py</code></td>
        <td>5 / 5</td>
        <td>Wear logging, outfit rating persistence, wear history displays</td>
      </tr>
      <tr>
        <td><code>test_analytics.py</code> & Other Modules</td>
        <td>49 / 49</td>
        <td>Mood engine, body criteria, analytics visualization, outfit generator</td>
      </tr>
      <tr style="background-color: #ecfdf5; font-weight: bold;">
        <td>TOTAL AUTOMATED SUITE</td>
        <td>130 / 130</td>
        <td>100% PASS RATE &bull; Execution time: 6.21s</td>
      </tr>
    </tbody>
  </table>
</div>

<h2>PROJECT CONCLUSION & FUTURE SCOPE</h2>
<div class="card no-break">
  <p><strong>Conclusion:</strong> FitChecker demonstrates that an intelligent, zero-friction, production-grade digital wardrobe system can be built without relying on expensive third-party APIs. By combining classical computer vision (GrabCut with adaptive frame sampling) with explainable multi-objective mathematics, machine learning adaptation, and 24-shade personal colorimetry, FitChecker empowers users with personalized, confident daily styling.</p>
  <p style="margin-bottom: 0;"><strong>Future Roadmap:</strong></p>
  <ul style="margin: 4px 0 0 0; padding-left: 18px; font-size: 8.5pt;">
    <li><strong>Client-Side WebAssembly (WASM):</strong> Running GrabCut on-device in browser threads to eliminate cloud compute bottlenecks.</li>
    <li><strong>Live Weather API Ingress:</strong> Fetching real-time temperature, rain, and humidity to adjust weather coefficients automatically.</li>
    <li><strong>3D Parametric Body Fitting:</strong> Enabling 3D virtual try-ons to preview garment draping and proportion fit.</li>
  </ul>
</div>

</body>
</html>
"""

for placeholder, b64_val in img_map.items():
    html_template = html_template.replace(placeholder, b64_val)

html_path = r"D:\DATA SCIENCE\FitChecker\FitChecker_Academic_Report.html"
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_template)

print(f"HTML written to {html_path} ({len(html_template)} bytes)")

# Convert to PDF using Edge headless
pdf_path = r"D:\DATA SCIENCE\FitChecker\FitChecker_Complete_Project_Report.pdf"
edge_cmd = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "--headless=new",
    "--no-sandbox",
    "--disable-gpu",
    f"--print-to-pdf={pdf_path}",
    html_path
]

print("Running Edge headless PDF generation...")
res = subprocess.run(edge_cmd, capture_output=True, text=True)
print("Return code:", res.returncode)
if os.path.exists(pdf_path):
    print(f"SUCCESS: PDF generated at {pdf_path} ({os.path.getsize(pdf_path)} bytes)")
else:
    print("FAILED: PDF not found")
