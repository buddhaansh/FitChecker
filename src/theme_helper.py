"""
src/theme_helper.py — Centralized Editorial Theme & Sidebar Styling
===================================================================
Applies the warm light brown & linen palette across Streamlit:
- Left sidebar: Warm light brown background (#EFE7DE) with warm light brown text (#704E38)
- Text selection: Soft warm mocha/light brown (replaces default browser blue highlight)
- Captions, subtext & metadata: Legible warm light brown (#8C5835) instead of white
- Form controls & cards: Rich brown (#4A352B) and cream accents
"""

import streamlit as st

THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

/* Universal Text Selection (replaces browser electric blue with soft light brown) */
::selection {
    background-color: #E8D8C8 !important;
    color: #36261E !important;
}
::-moz-selection {
    background-color: #E8D8C8 !important;
    color: #36261E !important;
}

/* Base App Canvas */
.stApp {
    background-color: #FAF7F2 !important;
    background-image: none !important;
    color: #241C18 !important;
    font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
}

/* Headings */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Playfair Display', Georgia, serif !important;
    color: #241C18 !important;
    font-weight: 700 !important;
}

/* ──────────────────────────────────────────────────────────────
   LEFT SIDEBAR: LIGHT BROWN BACKGROUND (#EFE7DE) & LIGHT BROWN TEXT
   ────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div:first-child,
section[data-testid="stSidebar"],
.stSidebar,
div[data-testid="stSidebarContent"],
[data-testid="stSidebarUserContent"] {
    background-color: #EFE7DE !important;
    border-right: 1.5px solid #DDD1C2 !important;
}

/* Sidebar Header & Collapse Controls */
[data-testid="stSidebarHeader"],
[data-testid="stSidebarCollapseButton"] button,
[data-testid="collapsedControl"],
[data-testid="collapsedControl"] button {
    background-color: #EFE7DE !important;
    color: #8C5835 !important;
}
[data-testid="stSidebarCollapseButton"] svg,
[data-testid="collapsedControl"] svg {
    fill: #8C5835 !important;
    stroke: #8C5835 !important;
}

/* Sidebar Navigation Container */
[data-testid="stSidebarNav"] {
    background-color: #EFE7DE !important;
    padding-top: 1rem !important;
}

/* Sidebar Navigation Links: Warm Light Brown Text */
[data-testid="stSidebarNav"] a,
[data-testid="stSidebarNav"] li,
[data-testid="stSidebarNav"] span,
[data-testid="stSidebarNav"] p,
[data-testid="stSidebarNavLink"],
[data-testid="stSidebarNavLink"] span,
[data-testid="stSidebarNavLink"] p,
[data-testid="stSidebar"] a,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {
    color: #704E38 !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    text-decoration: none !important;
}

/* Sidebar Links Hover State */
[data-testid="stSidebarNav"] a:hover,
[data-testid="stSidebarNavLink"]:hover,
[data-testid="stSidebarNav"] li:hover {
    background-color: #E4D8CC !important;
    border-radius: 8px !important;
}
[data-testid="stSidebarNav"] a:hover span,
[data-testid="stSidebarNavLink"]:hover span {
    color: #8C3B1E !important;
}

/* Sidebar Active Page: Clean Linen Pill with Terracotta Accent */
[data-testid="stSidebarNav"] a[aria-current="page"],
[data-testid="stSidebarNavLink"][aria-current="page"],
[data-testid="stSidebarNav"] li[aria-selected="true"],
[data-testid="stSidebarNav"] [data-active="true"] {
    background-color: #FAF7F2 !important;
    border-left: 4px solid #B85D3B !important;
    border-radius: 6px !important;
    box-shadow: 0 2px 8px rgba(112, 78, 56, 0.08) !important;
}
[data-testid="stSidebarNav"] a[aria-current="page"] span,
[data-testid="stSidebarNavLink"][aria-current="page"] span,
[data-testid="stSidebarNav"] a[aria-current="page"] p,
[data-testid="stSidebarNavLink"][aria-current="page"] p {
    color: #8C3B1E !important;
    font-weight: 700 !important;
}

/* Sidebar Icons */
[data-testid="stSidebar"] svg {
    fill: #8C5835 !important;
    color: #8C5835 !important;
}

/* Sidebar Form Widgets & Selectors */
[data-testid="stSidebar"] [data-baseweb="select"] div,
[data-testid="stSidebar"] [data-baseweb="input"] div {
    background-color: #FAF7F2 !important;
    color: #4A352B !important;
    border-color: #D5CFC7 !important;
}

/* ──────────────────────────────────────────────────────────────
   TEXT COLOR: WARM LIGHT BROWN FOR CAPTIONS, METADATA & BADGES
   (Replaces washed-out white / faint text with crisp light brown)
   ────────────────────────────────────────────────────────────── */
.stCaption,
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p,
[data-testid="stCaptionContainer"] span,
small,
.caption-light-brown {
    color: #8C5835 !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    line-height: 1.5 !important;
}

/* Metrics Card Styling */
div[data-testid="stMetric"] {
    background-color: #FFFFFF !important;
    border: 1.5px solid #E5DED4 !important;
    border-radius: 12px !important;
    padding: 16px 20px !important;
    box-shadow: 0 2px 10px rgba(74, 53, 43, 0.04) !important;
}

/* Metric Labels: Bold Warm Light Brown (Never Faint or White) */
[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] *,
div[data-testid="stMetricLabel"] div,
div[data-testid="stMetric"] label,
div[data-testid="stMetric"] [data-testid="stMetricLabel"] * {
    color: #704E38 !important;
    font-weight: 700 !important;
    font-size: 13.5px !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    opacity: 1 !important;
    visibility: visible !important;
}

/* Metric Values: Rich Espresso Serif */
[data-testid="stMetricValue"],
[data-testid="stMetricValue"] *,
div[data-testid="stMetricValue"] div {
    color: #241C18 !important;
    font-family: 'Playfair Display', Georgia, serif !important;
    font-weight: 700 !important;
    font-size: 32px !important;
}

/* Alerts & Notifications (Never Faint Blue or Washed Out) */
[data-testid="stAlert"],
.stAlert,
div[data-baseweb="notification"] {
    background-color: #FAF4EE !important;
    border: 1.5px solid #E2D2C2 !important;
    border-radius: 12px !important;
    color: #36261E !important;
    padding: 16px 20px !important;
}
[data-testid="stAlert"] *,
.stAlert *,
div[data-baseweb="notification"] * {
    color: #36261E !important;
    font-weight: 600 !important;
}
[data-testid="stAlert"] svg {
    fill: #8C3B1E !important;
}

/* Expanders */
[data-testid="stExpander"] {
    background-color: #FFFFFF !important;
    border: 1.5px solid #E5DED4 !important;
    border-radius: 10px !important;
}
[data-testid="stExpander"] summary span,
[data-testid="stExpander"] summary p {
    color: #704E38 !important;
    font-weight: 600 !important;
}

/* Item Container Borders */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FFFFFF !important;
    border: 1px solid #EBE4DA !important;
    border-radius: 10px !important;
    box-shadow: 0 2px 10px rgba(74, 53, 43, 0.04) !important;
}
</style>
"""

def apply_editorial_theme():
    """Inject the centralized warm light-brown & editorial theme into Streamlit."""
    st.markdown(THEME_CSS, unsafe_allow_html=True)
