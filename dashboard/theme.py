# =============================================================================
# theme.py
# Design system: colour tokens, shared Plotly layout and global CSS.
# CSS variables mirror COLORS so chart colours and UI colours stay in sync.
# =============================================================================

import streamlit as st

COLORS = {
    "bg":           "#0d0f14",
    "surface":      "#161922",
    "surface2":     "#1e222d",
    "border":       "#2a2f3e",
    "accent":       "#00e5a0",
    "accent2":      "#3d9bff",
    "warning":      "#f5a623",
    "danger":       "#ff5b5b",
    "text":         "#e8ecf3",
    "text_muted":   "#6b7694",
    "arb_green":    "#00e5a0",
    "close_yellow": "#f5a623",
    "far_red":      "#ff5b5b",
}

# Shared Plotly layout applied to every chart via dict unpacking: **PLOTLY_LAYOUT
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="'IBM Plex Mono', monospace", color=COLORS["text"], size=12),
    margin=dict(l=10, r=10, t=30, b=10),
    hoverlabel=dict(
        bgcolor=COLORS["surface2"],
        bordercolor=COLORS["border"],
        font_color=COLORS["text"],
    ),
)


# All styling is injected once per run via inject_css().
CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=Syne:wght@700;800&display=swap');

/* ── ROOT & GLOBAL ── */
:root {{
    --bg:         {COLORS["bg"]};
    --surface:    {COLORS["surface"]};
    --surface2:   {COLORS["surface2"]};
    --border:     {COLORS["border"]};
    --accent:     {COLORS["accent"]};
    --accent2:    {COLORS["accent2"]};
    --warn:       {COLORS["warning"]};
    --danger:     {COLORS["danger"]};
    --text:       {COLORS["text"]};
    --muted:      {COLORS["text_muted"]};
}}

html, body, [data-testid="stAppViewContainer"],
[data-testid="stMain"], .main {{
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'IBM Plex Mono', monospace !important;
}}

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {{
    background-color: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
    width: 290px !important;
}}
/* ── SIDEBAR TOP-GAP ELIMINATION ─────────────────────────────────────────
   Streamlit's sidebar chrome (header bar, collapse button, optional nav) is
   layered across several DOM wrappers that change names between releases.
   We zero them ALL out so the app title sits flush at the top.

   Each of the test IDs / selectors below has been used by Streamlit at some
   point between 1.20 and 1.42 — keeping them all in keeps us robust across
   user installs. */

/* 1. Hide the header bar that contains the collapse button */
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"],
section[data-testid="stSidebar"] [data-testid="stSidebarNav"],
[data-testid="stSidebarCollapsedControl"] {{
    display: none !important;
}}

/* 2. Hide the collapse button itself (multiple historical test IDs) */
section[data-testid="stSidebar"] button[data-testid="stSidebarCollapseButton"],
section[data-testid="stSidebar"] button[data-testid="baseButton-headerNoPadding"],
section[data-testid="stSidebar"] button[kind="header"],
section[data-testid="stSidebar"] > div > div:first-child > button {{
    display: none !important;
}}

/* 3. Zero out padding on every wrapper between <section> and the user content */
section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] > div > div,
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {{
    padding-top: 0 !important;
    margin-top: 0 !important;
}}
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {{
    padding-top: 0.75rem !important;
    padding-bottom: 1rem !important;
    margin-top: 0 !important;
}}

/* 4. Kill the default top margin on the very first element (the sidebar h2 title).
   Browsers add ~0.83em margin-top to h2 by default; this zeroes it. */
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] > div:first-child,
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] > div:first-child > *:first-child,
section[data-testid="stSidebar"] h2:first-of-type {{
    margin-top: 0 !important;
    padding-top: 0 !important;
}}
section[data-testid="stSidebar"] * {{
    color: var(--text) !important;
    font-family: 'IBM Plex Mono', monospace !important;
}}
/* Keep Streamlit material icon ligatures from rendering as raw text. */
section[data-testid="stSidebar"] [data-testid="stIconMaterial"] {{
    font-family: "Material Symbols Rounded", "Material Symbols Outlined", sans-serif !important;
    font-weight: normal !important;
    font-style: normal !important;
    font-size: 1.25rem !important;
    line-height: 1 !important;
    letter-spacing: normal !important;
    text-transform: none !important;
    white-space: nowrap !important;
    direction: ltr !important;
    -webkit-font-feature-settings: "liga" !important;
    font-feature-settings: "liga" !important;
}}
section[data-testid="stSidebar"] .stSelectbox > div,
section[data-testid="stSidebar"] .stNumberInput > div,
section[data-testid="stSidebar"] .stRadio > div {{
    background-color: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
}}
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown p {{
    color: var(--muted) !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}}
section[data-testid="stSidebar"] h2 {{
    font-family: 'Syne', sans-serif !important;
    font-size: 1rem !important;
    color: var(--accent) !important;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}}

/* ── MAIN HEADING ── */
h1 {{
    font-family: 'Syne', sans-serif !important;
    font-size: 2.2rem !important;
    font-weight: 800 !important;
    color: var(--text) !important;
    letter-spacing: -0.01em;
    margin-bottom: 0 !important;
}}
h2, h3 {{
    font-family: 'Syne', sans-serif !important;
    color: var(--text) !important;
    letter-spacing: 0.02em;
}}

/* ── CAPTION / SUBTEXT ── */
.stCaption, [data-testid="stCaptionContainer"] p {{
    color: var(--muted) !important;
    font-size: 0.75rem !important;
}}

/* ── METRIC CARDS ── */
[data-testid="stMetric"] {{
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    padding: 1rem 1.2rem !important;
}}
[data-testid="stMetricLabel"] p {{
    color: var(--muted) !important;
    font-size: 0.7rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}}
[data-testid="stMetricValue"] {{
    color: var(--accent) !important;
    font-family: 'Syne', sans-serif !important;
    font-size: clamp(1.45rem, 3.2vw, 1.8rem) !important;
    font-weight: 800 !important;
}}

/* ── DATAFRAME ── */
[data-testid="stDataFrame"] {{
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    overflow: hidden;
}}

[data-testid="stMetricValue"] > div {{
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: clip !important;
    line-height: 1.1 !important;
}}

/* ── BUTTONS ── */
.stButton > button, .stDownloadButton > button {{
    background: transparent !important;
    border: 1px solid var(--accent) !important;
    color: var(--accent) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    border-radius: 6px !important;
    transition: all 0.2s ease !important;
}}
.stButton > button:hover, .stDownloadButton > button:hover {{
    background: var(--accent) !important;
    color: var(--bg) !important;
    transform: translateY(-1px);
}}
.stLinkButton a {{
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    color: var(--accent2) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.75rem !important;
    border-radius: 6px !important;
    text-decoration: none !important;
    transition: all 0.2s ease !important;
}}
.stLinkButton a:hover {{
    border-color: var(--accent2) !important;
    background: rgba(61, 155, 255, 0.12) !important;
}}

/* ── SELECT BOX & INPUTS ── */
.stSelectbox [data-baseweb="select"] > div,
.stNumberInput input {{
    background-color: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 6px !important;
    font-family: 'IBM Plex Mono', monospace !important;
}}
.stSelectbox [data-baseweb="popover"] {{
    background-color: var(--surface2) !important;
    border: 1px solid var(--border) !important;
}}

/* ── ALERTS / NOTICES ── */
.stSuccess {{
    background: rgba(0, 229, 160, 0.08) !important;
    border-left: 3px solid var(--accent) !important;
    color: var(--text) !important;
    border-radius: 0 6px 6px 0 !important;
}}
.stInfo {{
    background: rgba(61, 155, 255, 0.08) !important;
    border-left: 3px solid var(--accent2) !important;
    color: var(--text) !important;
    border-radius: 0 6px 6px 0 !important;
}}
.stWarning {{
    background: rgba(245, 166, 35, 0.08) !important;
    border-left: 3px solid var(--warn) !important;
    border-radius: 0 6px 6px 0 !important;
}}

/* ── EXPANDER ── (uses modern data-testid; the old .streamlit-expander* classes
   were removed in Streamlit 1.18+) */
[data-testid="stExpander"] {{
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    overflow: hidden;
}}
[data-testid="stExpander"] summary {{
    color: var(--text) !important;
    font-size: 0.8rem !important;
}}
[data-testid="stExpander"] details {{
    background: var(--surface) !important;
}}
[data-testid="stExpander"] [data-testid="stExpanderDetails"] {{
    background: var(--surface) !important;
}}

/* ── SPINNER ── */
.stSpinner > div {{
    border-top-color: var(--accent) !important;
}}

/* ── SLIDER ── */
.stSlider [data-baseweb="slider"] [role="slider"] {{
    background: var(--accent) !important;
}}
.stSlider [data-baseweb="slider"] [data-testid="stSliderTrackFill"] {{
    background: var(--accent) !important;
}}

/* ── CHECKBOX ── */
.stCheckbox [data-baseweb="checkbox"] input:checked + div {{
    background: var(--accent) !important;
    border-color: var(--accent) !important;
}}

/* ── DIVIDER ── */
hr {{
    border-color: var(--border) !important;
}}

/* ── LIVE INDICATOR ── */
.live-indicator {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-weight: 700;
    color: var(--danger);
    font-size: 0.85rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin: 4px 0 8px;
}}
.live-dot {{
    width: 10px;
    height: 10px;
    background-color: var(--danger);
    border-radius: 50%;
    position: relative;
    animation: pulse 1.8s infinite ease-in-out;
}}
.live-dot::after {{
    content: '';
    position: absolute;
    width: 100%;
    height: 100%;
    border-radius: 50%;
    background-color: var(--danger);
    animation: ring 1.8s infinite ease-in-out;
}}
@keyframes pulse {{
    0%, 100% {{ transform: scale(1); box-shadow: 0 0 0 0 rgba(255,91,91,0.7); }}
    50% {{ transform: scale(1.15); box-shadow: 0 0 0 6px rgba(255,91,91,0); }}
}}
@keyframes ring {{
    0% {{ transform: scale(0.6); opacity: 1; }}
    100% {{ transform: scale(2.8); opacity: 0; }}
}}

/* ── BADGE PILL ── */
.badge {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}}
.badge-arb {{
    background: rgba(0,229,160,0.15);
    color: {COLORS["arb_green"]};
    border: 1px solid {COLORS["arb_green"]};
}}
.badge-close {{
    background: rgba(245,166,35,0.12);
    color: {COLORS["close_yellow"]};
    border: 1px solid {COLORS["close_yellow"]};
}}
.badge-normal {{
    background: rgba(107,118,148,0.15);
    color: {COLORS["text_muted"]};
    border: 1px solid {COLORS["border"]};
}}

/* ── GAME CARD ── */
.game-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.5rem;
    transition: border-color 0.2s;
}}
.game-card:hover {{
    border-color: var(--accent);
}}

/* ── SECTION LABEL ── */
.section-label {{
    font-size: 0.65rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 0.4rem;
    display: block;
}}

/* ── HEADER TICKER ── */
.header-bar {{
    display: flex;
    align-items: baseline;
    gap: 14px;
    margin-bottom: 0.25rem;
}}
.header-tag {{
    font-size: 0.7rem;
    color: var(--accent);
    background: rgba(0,229,160,0.1);
    border: 1px solid var(--accent);
    border-radius: 4px;
    padding: 2px 8px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    vertical-align: middle;
}}

.block-container {{
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 1400px !important;
}}
</style>
"""


def inject_css() -> None:
    """Inject the global stylesheet into the current Streamlit page."""
    st.markdown(CSS, unsafe_allow_html=True)
