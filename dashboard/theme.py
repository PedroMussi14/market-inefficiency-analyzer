# =============================================================================
# theme.py
# Design system: colour tokens, shared Plotly layout and global CSS.
#
# Style: a dark "data terminal". Cards sit slightly darker than the ground,
# every figure is set in IBM Plex Mono so digits stack, colour is kept for
# data (a guaranteed margin, a live game) and every selection is marked by
# the same 1px accent line.
# =============================================================================

import streamlit as st

COLORS = {
    "ground":   "#171719",   # page and sidebar
    "surface":  "#131217",   # cards, one step darker than the ground
    "raised":   "#212023",   # nested panels, hover fills, tooltips
    "border":   "#222224",   # structural lines
    "rule":     "#1b1a1f",   # row rules inside tables
    "control":  "#3a3a3e",   # control outlines
    "text":     "#ffffff",
    "muted":    "#8a8c92",   # secondary text, 4.5:1 on the card
    "faint":    "#4a4b50",   # non-text marks only (bars that are not the story)
    "accent":   "#4a8ad6",   # selection lines and the main data series
    "positive": "#44a282",
    "positive_ink": "#5fc39c",
    "negative": "#e5566f",
    "warning":  "#d9a441",
    "grid":     "#26262a",
}

FONT_TEXT = "'Public Sans', Inter, system-ui, sans-serif"
FONT_NUM  = "'IBM Plex Mono', ui-monospace, monospace"

# Shared Plotly layout applied to every chart via dict unpacking: **PLOTLY_LAYOUT
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family=FONT_TEXT, color=COLORS["muted"], size=12),
    margin=dict(l=8, r=8, t=8, b=8),
    hoverlabel=dict(
        bgcolor=COLORS["raised"],
        bordercolor=COLORS["control"],
        font=dict(family=FONT_TEXT, color=COLORS["text"], size=12),
    ),
    showlegend=False,
)


# All styling is injected once per run via inject_css().
CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Public+Sans:wght@400;500;600;700&display=swap');

:root {{
    --ground:   {COLORS["ground"]};
    --surface:  {COLORS["surface"]};
    --raised:   {COLORS["raised"]};
    --border:   {COLORS["border"]};
    --rule:     {COLORS["rule"]};
    --control:  {COLORS["control"]};
    --text:     {COLORS["text"]};
    --muted:    {COLORS["muted"]};
    --accent:   {COLORS["accent"]};
    --positive: {COLORS["positive"]};
    --negative: {COLORS["negative"]};
    --warning:  {COLORS["warning"]};
    --pill-positive-bg: #1b2828; --pill-positive-ink: {COLORS["positive_ink"]};
    --pill-negative-bg: #2c1a20; --pill-negative-ink: {COLORS["negative"]};
    --pill-warning-bg:  #2a2416; --pill-warning-ink:  {COLORS["warning"]};
    --pill-neutral-bg:  #212023; --pill-neutral-ink:  #bdbdc0;
    --shadow: 0 12px 28px rgba(0,0,0,.2);
    --radius-card: 6px;
    --radius-field: 6px;
    --font: {FONT_TEXT};
    --font-num: {FONT_NUM};
}}

/* ── Ground and type ───────────────────────────────────────────────────── */
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
    background: var(--ground) !important;
    color: var(--text);
    font-family: var(--font);
}}
.stApp p, .stApp li, .stApp label, .stApp input, .stApp textarea, .stApp button,
.stApp [data-baseweb="select"] {{
    font-family: var(--font) !important;
}}
.stApp p, .stApp li {{ font-size: 14px; line-height: 20px; }}
.num, .stApp .num {{
    font-family: var(--font-num) !important;
    font-variant-numeric: tabular-nums;
}}

/* Streamlit chrome: no decoration bar, a transparent header */
[data-testid="stDecoration"] {{ display: none !important; }}
header[data-testid="stHeader"] {{ background: transparent !important; }}
[data-testid="stHeaderActionElements"], .stApp h1 a, .stApp h2 a, .stApp h3 a {{ display: none !important; }}

.block-container, [data-testid="stMainBlockContainer"] {{
    padding: 36px 32px 64px !important;
    max-width: 1320px !important;
}}

/* ── Sidebar ───────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {{
    background: var(--ground) !important;
    border-right: 1px solid var(--border) !important;
}}
section[data-testid="stSidebar"] > div {{ background: var(--ground) !important; }}
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {{
    padding-bottom: 0 !important;
    height: 40px;
}}
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {{
    padding: 0 16px 32px !important;
}}
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{ gap: 12px; }}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{
    font-size: 12px; line-height: 17px; color: var(--muted);
}}

.brand {{
    display: flex; align-items: center; gap: 10px;
    padding: 0 0 8px; color: var(--text);
}}
.brand svg {{ flex: none; }}
.brand-name {{ font-size: 15px; font-weight: 600; line-height: 19px; }}
.brand-scope {{ font-size: 12px; color: var(--muted); line-height: 16px; }}

.nav-group {{
    font-size: 13px !important; font-weight: 600; color: var(--text) !important;
    margin: 20px 0 0 !important; padding-top: 16px; border-top: 1px solid var(--border);
}}

/* Page navigation: text items; the active one is white with a 1px accent
   line exactly as wide as its label. */
.st-key-nav {{ margin-top: 4px; }}
.st-key-nav [role="radiogroup"] {{ gap: 0 !important; }}
.st-key-nav [data-testid="stRadioOption"] {{
    margin: 0 !important; padding: 6px 0 !important; min-height: 34px; cursor: pointer;
}}
.st-key-nav [data-testid="stRadioOption"] p {{
    font-size: 14px !important; color: var(--muted) !important;
    display: inline-block; padding-bottom: 3px;
    border-bottom: 1px solid transparent;
    transition: color .15s ease;
}}
.st-key-nav [data-testid="stRadioOption"]:hover p {{ color: var(--text) !important; }}

/* Radios (the page nav and the view mode) drop their circles: the selected
   option is white with the accent line under its label. */
.st-key-nav [data-testid="stRadioOption"] > div > div:first-child,
[aria-orientation="horizontal"] [data-testid="stRadioOption"] > div > div:first-child {{
    display: none !important;
}}
[aria-orientation="horizontal"] [data-testid="stRadioOption"] {{ margin-right: 18px !important; }}
[aria-orientation="horizontal"] [data-testid="stRadioOption"] p {{
    color: var(--muted) !important; padding-bottom: 3px; border-bottom: 1px solid transparent;
}}
.st-key-nav [data-testid="stRadioOption"][data-selected="true"] p,
[aria-orientation="horizontal"] [data-testid="stRadioOption"][data-selected="true"] p {{
    color: var(--text) !important; font-weight: 500;
    border-bottom-color: var(--accent);
}}

/* ── Fields ────────────────────────────────────────────────────────────── */
.stApp label[data-testid="stWidgetLabel"] p {{
    font-size: 12px !important; color: var(--muted) !important; font-weight: 400;
}}
.stApp [data-baseweb="select"] > div,
.stApp [data-testid="stNumberInputContainer"] {{
    background: var(--surface) !important;
    border: 1px solid var(--control) !important;
    border-radius: var(--radius-field) !important;
    min-height: 34px;
}}
.stApp [data-testid="stNumberInputContainer"] > div {{
    border: 0 !important; background: transparent !important;
}}
.stApp [data-baseweb="select"] > div:hover {{ border-color: #55555a !important; }}
.stApp [data-baseweb="select"] span, .stApp [data-baseweb="select"] div {{ font-size: 13px; }}
.stApp [data-testid="stNumberInputContainer"] input {{
    background: transparent !important; font-family: var(--font-num) !important; font-size: 13px;
}}
.stApp [data-testid="stNumberInputContainer"] button {{ background: transparent !important; }}
.stApp [data-baseweb="tag"] {{
    background: var(--raised) !important; border-radius: 4px !important;
}}
.stApp [data-baseweb="tag"] span {{ color: var(--text) !important; }}
[data-baseweb="popover"] ul, [data-baseweb="menu"] {{ background: var(--raised) !important; }}

.stCheckbox p, .stToggle p {{ font-size: 13px !important; color: var(--text) !important; }}

.stSlider [data-testid="stSliderThumbValue"] {{
    font-family: var(--font-num) !important; color: var(--text) !important;
}}
.stSlider [data-testid="stSliderTickBarMin"], .stSlider [data-testid="stSliderTickBarMax"] {{
    font-family: var(--font-num) !important; color: var(--muted) !important;
}}

/* ── Buttons: one quiet outlined pill style; there is no filled primary ── */
.stButton > button, .stDownloadButton > button, .stLinkButton a {{
    background: transparent !important;
    border: 1px solid var(--control) !important;
    color: var(--text) !important;
    border-radius: 999px !important;
    min-height: 34px; padding: 0 16px !important;
    font-size: 13px !important; font-weight: 500;
    text-decoration: none !important;
    transition: border-color .15s ease, background-color .15s ease;
}}
.stButton > button:hover, .stDownloadButton > button:hover, .stLinkButton a:hover {{
    border-color: #6a6b70 !important; background: var(--raised) !important;
}}
.stButton > button:active, .stDownloadButton > button:active {{ transform: translateY(1px); }}
.stButton > button p, .stDownloadButton > button p {{ font-size: 13px !important; }}

/* ── Headings ──────────────────────────────────────────────────────────── */
.stApp h1 {{
    font-family: var(--font) !important;
    font-size: 26px !important; line-height: 32px !important; font-weight: 700 !important;
    letter-spacing: -0.01em; color: var(--text) !important;
    margin: 0 !important; padding: 0 !important;
}}
.stApp h2.section {{
    font-family: var(--font) !important;
    font-size: 20px !important; line-height: 26px !important; font-weight: 400 !important;
    color: var(--muted) !important; margin: 32px 0 0 !important; padding: 0 !important;
}}
.stApp h3.card-title {{
    font-family: var(--font) !important;
    font-size: 16px !important; line-height: 22px !important; font-weight: 600 !important;
    color: var(--text) !important; margin: 0 !important; padding: 0 !important;
}}

/* Title row: the h1, the finding under it, a freshness stamp on the right */
.title-row {{ display: flex; justify-content: space-between; align-items: flex-end; gap: 24px;
             flex-wrap: wrap; padding-bottom: 20px; border-bottom: 1px solid var(--border); }}
.title-row .finding {{ font-size: 15px; line-height: 22px; color: var(--muted); margin-top: 6px; max-width: 780px; }}
.title-row .finding b {{ color: var(--text); font-weight: 500; }}
.stamp {{ font-size: 12px; color: var(--muted); white-space: nowrap; display: flex; gap: 8px; align-items: center; }}

/* ── Cards (keyed Streamlit containers) ────────────────────────────────── */
.st-key-kpis, [class*="st-key-card"] {{
    background: var(--surface);
    border-radius: var(--radius-card);
    box-shadow: var(--shadow);
}}
[class*="st-key-card"] {{ padding: 20px 24px 24px; gap: 16px; }}
/* Cards that share a row share a bottom edge */
[data-testid="stColumn"] > [data-testid="stVerticalBlock"]
    > [data-testid="stLayoutWrapper"]:has(> [class*="st-key-card"]) {{
    flex: 1 1 auto;
}}
[data-testid="stColumn"] [class*="st-key-card"] {{ height: 100%; }}
.card-sub {{ font-size: 12px; color: var(--muted); line-height: 17px; margin-top: 2px; }}

/* KPI strip: one card split into equal columns by 1px lines */
.st-key-kpis {{ padding: 0; }}
.st-key-kpis [data-testid="stHorizontalBlock"] {{ gap: 0 !important; }}
.st-key-kpis [data-testid="stColumn"] {{ padding: 16px 24px; }}
.st-key-kpis [data-testid="stColumn"] + [data-testid="stColumn"] {{ border-left: 1px solid var(--border); }}
[data-testid="stMetric"] {{ background: transparent !important; border: 0 !important; padding: 0 !important; }}
[data-testid="stMetricLabel"] p {{ font-size: 12px !important; color: var(--muted) !important; }}
[data-testid="stMetricValue"] {{
    font-family: var(--font-num) !important; font-variant-numeric: tabular-nums;
    font-size: 22px !important; line-height: 30px; font-weight: 500 !important; color: var(--text) !important;
}}
[data-testid="stMetricValue"] > div {{ overflow: visible !important; }}

/* ── The focus card: the selected game, its stakes and where to place them ── */
.figure-row {{ display: flex; gap: 32px; flex-wrap: wrap; align-items: flex-start; margin-bottom: 4px; }}
.figure .label {{ font-size: 12px; color: var(--muted); line-height: 16px; }}
.figure .value {{ font-family: var(--font-num); font-variant-numeric: tabular-nums;
                  font-size: 20px; line-height: 28px; font-weight: 500; color: var(--text); }}
.figure.lead .value {{ font-size: 32px; line-height: 40px; }}
.figure .value.pos {{ color: var(--pill-positive-ink); }}

.game-head {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }}
.game-name {{ font-size: 18px; line-height: 24px; font-weight: 600; color: var(--text); }}
.game-meta {{ font-size: 12px; color: var(--muted); margin-top: 2px; }}

/* Stake split: one 100% bar, legs separated by 2px seams */
.split {{ display: flex; gap: 2px; height: 8px; border-radius: 999px; overflow: hidden; }}
.split span {{ display: block; height: 100%; }}
.split-legend {{
    display: flex; flex-wrap: wrap; gap: 4px 20px; margin-top: 8px; font-size: 12px; color: var(--muted);
}}
.split-legend i {{ display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }}

/* ── Tables ────────────────────────────────────────────────────────────── */
.table-frame {{ overflow-x: auto; }}   /* a table never widens the page */
table.legs {{ width: 100%; border-collapse: collapse; margin: 8px 0 0; }}
table.legs th {{
    font-size: 12px; font-weight: 400; color: var(--muted); text-align: left;
    padding: 0 12px 8px 0; white-space: nowrap; border: 0 !important; background: none !important;
}}
table.legs td {{
    font-size: 14px; color: var(--text); padding: 0 12px 0 0; height: 42px;
    border: 0 !important; border-top: 1px solid var(--rule) !important;
    white-space: nowrap; background: none !important;
}}
table.legs tr {{ background: none !important; border: 0 !important; }}
table.legs th:last-child, table.legs td:last-child {{ padding-right: 0; }}
table.legs .r {{ text-align: right; }}
table.legs td.r {{ font-family: var(--font-num); font-variant-numeric: tabular-nums; font-size: 13px; }}
table.legs td.sub {{ color: var(--muted); }}
table.legs tr.total td {{ border-top: 1px solid var(--control) !important; color: var(--muted); }}
table.legs tr.total td.r {{ color: var(--text); }}
a.go {{
    font-family: var(--font) !important;
    color: var(--text) !important; text-decoration: none !important; font-size: 13px;
    border-bottom: 1px solid var(--control); padding-bottom: 1px;
    transition: border-color .15s ease;
}}
a.go:hover {{ border-bottom-color: var(--accent); }}
.links {{ display: flex; flex-wrap: wrap; gap: 6px 20px; font-size: 13px; }}

[data-testid="stDataFrame"] {{ border-radius: var(--radius-card); overflow: hidden; }}

/* ── Pills ─────────────────────────────────────────────────────────────── */
.pill {{
    display: inline-flex; align-items: center; flex: none; white-space: nowrap;
    height: 20px; padding: 0 8px; border-radius: 999px;
    font-size: 12px; font-weight: 500; line-height: 20px;
}}
.pill.positive {{ background: var(--pill-positive-bg); color: var(--pill-positive-ink); }}
.pill.negative {{ background: var(--pill-negative-bg); color: var(--pill-negative-ink); }}
.pill.warning  {{ background: var(--pill-warning-bg);  color: var(--pill-warning-ink); }}
.pill.neutral  {{ background: var(--pill-neutral-bg);  color: var(--pill-neutral-ink); }}
.pills {{ display: flex; gap: 6px; flex-wrap: wrap; justify-content: flex-end; }}

/* ── Notices and empty states ──────────────────────────────────────────── */
.empty {{
    border: 1px dashed var(--control); border-radius: 8px;
    padding: 12px 16px; font-size: 13px; color: var(--muted);
}}
.empty b {{ color: var(--text); font-weight: 500; }}
[data-testid="stAlertContainer"] {{
    background: var(--raised) !important; color: var(--text) !important;
    border: 0 !important; border-radius: 8px !important;
}}
[data-testid="stAlertContainer"] p {{ font-size: 13px !important; }}

/* Usage bar (API quota) */
.usage .row {{ display: flex; justify-content: space-between; font-size: 12px; color: var(--muted); }}
.usage .row b {{ font-family: var(--font-num); font-weight: 500; color: var(--text); }}
.usage .track {{ height: 6px; border-radius: 999px; background: var(--raised); margin-top: 6px; overflow: hidden; }}
.usage .fill {{ height: 100%; border-radius: 999px; background: var(--text); }}
.usage .fill.low {{ background: var(--negative); }}

/* ── Expander ──────────────────────────────────────────────────────────── */
[data-testid="stExpander"] details {{
    background: var(--surface) !important; border: 0 !important;
    border-radius: var(--radius-card) !important;
}}
[data-testid="stExpander"] summary p {{ font-size: 14px !important; color: var(--text) !important; }}

hr {{ border-color: var(--border) !important; }}

/* Visible focus for keyboard users */
.stApp a:focus-visible, .stApp button:focus-visible {{
    outline: 2px solid var(--accent) !important; outline-offset: 2px;
}}

/* ── Tablet: side-by-side cards stack once either would be too narrow ──── */
@media (max-width: 1100px) {{
    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] [class*="st-key-card"]) {{
        flex-direction: column !important;
    }}
    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] [class*="st-key-card"])
        > [data-testid="stColumn"] {{
        width: 100% !important; flex: 1 1 auto !important;
    }}
}}

/* ── Phone ─────────────────────────────────────────────────────────────── */
@media (max-width: 640px) {{
    .block-container, [data-testid="stMainBlockContainer"] {{ padding: 56px 16px 48px !important; }}
    .stApp h1 {{ font-size: 22px !important; line-height: 28px !important; }}
    .title-row {{ flex-direction: column; align-items: flex-start; gap: 8px; }}
    .st-key-kpis [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap !important; }}
    .st-key-kpis [data-testid="stColumn"] {{
        flex: 1 1 50% !important; min-width: 50% !important; width: 50% !important; padding: 14px 16px;
        border-left: 0 !important;
    }}
    .st-key-kpis [data-testid="stColumn"]:nth-child(even) {{ border-left: 1px solid var(--border) !important; }}
    .st-key-kpis [data-testid="stColumn"]:nth-child(n+3) {{ border-top: 1px solid var(--border); }}
    [class*="st-key-card"] {{ padding: 16px; }}
    .figure.lead .value {{ font-size: 28px; line-height: 34px; }}
    table.legs .hide-sm {{ display: none; }}
    table.legs th, table.legs td {{ padding-right: 8px; }}
    table.legs td:first-child {{ white-space: normal; line-height: 18px; }}
}}

@media (prefers-reduced-motion: reduce) {{
    * {{ transition: none !important; }}
}}
</style>
"""


def inject_css() -> None:
    """Inject the global stylesheet into the current Streamlit page."""
    st.markdown(CSS, unsafe_allow_html=True)
