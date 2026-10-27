# =============================================================================
# theme.py
# Design system: colour tokens and global CSS.
#
# Style: a consumer-finance app. White cards with one large radius on an
# off-white ground, Manrope throughout with the money figures large, pale
# tiles for teams and sportsbooks (each tile's ink is the dark of its own
# hue), profit in green with a plus sign, and a single cobalt for the data
# and the one primary control. No shadows at rest, no table grids.
# =============================================================================

import streamlit as st

COLORS = {
    "ground":      "#eef1f5",
    "surface":     "#ffffff",
    "raised":      "#f4f8fd",
    "border":      "#e1e5ea",
    "rule":        "#f0f1f3",
    "control":     "#d6d9dd",
    "text":        "#1b1d1f",
    "muted":       "#5c6064",
    "faint":       "#c4c8cd",   # marks only, never text
    "accent":      "#1d5fd6",
    "accent_soft": "#dcf1ff",
    "accent_ink":  "#0a3a80",
    "positive":    "#2f7a45",
    "negative":    "#c41c29",
}

# Pale tiles for teams and sportsbooks: (background, ink of the same hue)
TILE_TONES = [
    ("#dcf1ff", "#0a3a80"),   # blue
    ("#fff1d6", "#7a4a00"),   # amber
    ("#d7f3f5", "#0b4d55"),   # teal
    ("#ffe4ec", "#7d1236"),   # rose
    ("#e8ecf2", "#2b3644"),   # slate
    ("#ffe8d9", "#7c2d12"),   # orange
]

FONT = "'Manrope', Inter, system-ui, sans-serif"


# All styling is injected once per run via inject_css().
CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&display=swap');

:root {{
    --ground:  {COLORS["ground"]};
    --surface: {COLORS["surface"]};
    --raised:  {COLORS["raised"]};
    --border:  {COLORS["border"]};
    --rule:    {COLORS["rule"]};
    --control: {COLORS["control"]};
    --text:    {COLORS["text"]};
    --muted:   {COLORS["muted"]};
    --faint:   {COLORS["faint"]};
    --accent:  {COLORS["accent"]};
    --accent-soft: {COLORS["accent_soft"]};
    --accent-ink:  {COLORS["accent_ink"]};
    --positive: {COLORS["positive"]};
    --negative: {COLORS["negative"]};
    --pill-positive-bg: #dcfae5; --pill-positive-ink: #04250e;
    --pill-warning-bg:  #fffbeb; --pill-warning-ink:  #92400e;
    --pill-neutral-bg:  #eef1f4; --pill-neutral-ink:  #3a3d40;
    --radius-card: 20px;
    --radius-inner: 10px;
    --font: {FONT};
}}

/* ── Ground and type ───────────────────────────────────────────────────── */
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
    background: var(--ground) !important;
    color: var(--text);
}}
.stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp button,
.stApp [data-baseweb="select"], .stApp h1, .stApp h2, .stApp h3 {{
    font-family: var(--font) !important;
}}
.stApp p, .stApp li {{ font-size: 15px; line-height: 22px; }}
.num {{ font-variant-numeric: tabular-nums; }}

[data-testid="stDecoration"] {{ display: none !important; }}
header[data-testid="stHeader"] {{ background: transparent !important; }}
[data-testid="stHeaderActionElements"], .stApp h1 a, .stApp h2 a, .stApp h3 a {{ display: none !important; }}

.block-container, [data-testid="stMainBlockContainer"] {{
    padding: 36px 40px 72px !important;
    max-width: 1280px !important;
}}
[data-testid="stMain"] [data-testid="stVerticalBlock"] {{ gap: 24px; }}
/* Streamlit pulls markdown up by 1rem to cancel a paragraph margin; our HTML blocks have none */
[data-testid="stMarkdownContainer"]:has(> div, > svg) {{ margin-bottom: 0 !important; }}

/* ── Sidebar: on the page ground, a neutral pill on the active item ────── */
section[data-testid="stSidebar"], section[data-testid="stSidebar"] > div {{
    background: var(--surface) !important;
}}
section[data-testid="stSidebar"] {{ border-right: 1px solid var(--border) !important; }}
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {{ height: 36px; padding-bottom: 0 !important; }}
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {{ padding: 0 16px 32px !important; }}
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{ gap: 14px; }}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{
    font-size: 13px; line-height: 18px; color: var(--muted);
}}

.brand {{ display: flex; align-items: center; gap: 12px; padding: 0 4px 16px; }}
.brand-mark {{
    width: 36px; height: 36px; border-radius: 10px; flex: none;
    background: var(--accent); display: grid; place-items: center;
}}
.brand-name {{ font-size: 15px; font-weight: 700; line-height: 19px; color: var(--text); }}
.brand-scope {{ font-size: 13px; color: var(--muted); line-height: 17px; }}

.nav-group {{
    font-size: 12px !important; font-weight: 700; color: var(--muted) !important;
    margin: 10px 0 -2px !important; padding-top: 18px; border-top: 1px solid var(--border);
}}

.st-key-nav, .st-key-nav .stRadio, .st-key-nav [role="radiogroup"],
.st-key-nav [role="radiogroup"] > div {{ width: 100% !important; }}
.st-key-nav [role="radiogroup"] {{ gap: 2px !important; }}
.st-key-nav [data-testid="stRadioOption"] {{
    display: flex !important; align-items: center !important;
    margin: 0 !important; padding: 0 12px !important; height: 40px;
    border-radius: 10px; cursor: pointer; width: 100%;
    transition: background-color .15s ease;
}}
.st-key-nav [data-testid="stRadioOption"]:hover {{ background: #f2f4f7; }}
.st-key-nav [data-testid="stRadioOption"][data-selected="true"] {{ background: var(--accent-soft); }}
.st-key-nav [data-testid="stRadioOption"] > div,
.st-key-nav [data-testid="stRadioOption"] [data-testid="stMarkdownContainer"] {{ display: flex; align-items: center; }}
.st-key-nav [data-testid="stRadioOption"] p {{
    display: flex; align-items: center; gap: 12px; margin: 0 !important;
    font-size: 15px !important; line-height: 20px !important; color: var(--muted) !important;
}}
.st-key-nav [data-testid="stIconMaterial"] {{ font-size: 19px !important; color: var(--muted); }}

/* Sidebar fields: a light grey fill so they stand out on the white panel */
section[data-testid="stSidebar"] [data-baseweb="select"] > div,
section[data-testid="stSidebar"] [data-testid="stNumberInputContainer"],
section[data-testid="stSidebar"] [data-testid="stExpander"] details {{
    background: #f3f5f8 !important; border: 1px solid var(--border) !important;
}}
.st-key-nav [data-testid="stRadioOption"][data-selected="true"] p,
.st-key-nav [data-testid="stRadioOption"][data-selected="true"] [data-testid="stIconMaterial"] {{
    color: var(--accent-ink) !important; font-weight: 700;
}}

/* Radios lose their circles: the page nav, the view mode and the watchlist */
.st-key-nav [data-testid="stRadioOption"] > div > div:first-child,
.st-key-watch [data-testid="stRadioOption"] > div > div:first-child,
[aria-orientation="horizontal"] [data-testid="stRadioOption"] > div > div:first-child {{
    display: none !important;
}}

/* Horizontal radios read as a segmented control: a grey track, the choice in white */
.stRadio [aria-orientation="horizontal"][role="radiogroup"] {{
    background: #e7eaee; border-radius: 10px; padding: 3px; gap: 0 !important; width: fit-content;
}}
[aria-orientation="horizontal"] [data-testid="stRadioOption"] {{
    margin: 0 !important; padding: 5px 14px !important; border-radius: 8px;
}}
[aria-orientation="horizontal"] [data-testid="stRadioOption"] p {{ font-size: 14px !important; color: var(--muted) !important; }}
[aria-orientation="horizontal"] [data-testid="stRadioOption"][data-selected="true"] {{ background: var(--surface); }}
[aria-orientation="horizontal"] [data-testid="stRadioOption"][data-selected="true"] p {{
    color: var(--text) !important; font-weight: 600;
}}

/* ── Fields ────────────────────────────────────────────────────────────── */
.stApp label[data-testid="stWidgetLabel"] p {{
    font-size: 13px !important; color: var(--muted) !important; font-weight: 500;
}}
.stApp [data-baseweb="select"] > div, .stApp [data-testid="stNumberInputContainer"] {{
    background: var(--surface) !important;
    border: 1px solid var(--control) !important;
    border-radius: var(--radius-inner) !important;
    min-height: 40px;
}}
.stApp [data-testid="stNumberInputContainer"] > div {{ border: 0 !important; background: transparent !important; }}
.stApp [data-baseweb="select"] > div:hover {{ border-color: #b9bec4 !important; }}
.stApp [data-baseweb="select"] span, .stApp [data-baseweb="select"] div {{ font-size: 15px; }}
.stApp [data-testid="stNumberInputContainer"] input {{ background: transparent !important; font-size: 15px; }}
.stApp [data-testid="stNumberInputContainer"] button {{ background: transparent !important; }}
.stApp [data-baseweb="tag"] {{ background: var(--accent-soft) !important; border-radius: 6px !important; }}
.stApp [data-baseweb="tag"] span {{ color: var(--accent-ink) !important; }}
.stCheckbox p, .stToggle p {{ font-size: 14px !important; color: var(--text) !important; }}
.stApp [data-testid="stCaptionContainer"] p {{ font-size: 13px !important; line-height: 18px; color: var(--muted); }}

/* Pills (sport filter): white chips, the chosen ones in the pale accent */
.stApp button[data-variant="pills"] {{
    border: 0 !important; border-radius: 999px !important; min-height: 36px; padding: 0 16px !important;
    background: var(--surface) !important; color: var(--muted) !important;
}}
.stApp button[data-variant="pills"][aria-checked="true"], .stApp button[data-variant="pills"][aria-pressed="true"],
.stApp button[data-variant="pills"][data-selected="true"] {{
    background: var(--accent-soft) !important; color: var(--accent-ink) !important;
}}

/* Segmented control: a grey track, the choice in white */
.stApp [role="radiogroup"]:has(> button[data-variant="segmented_control"]) {{
    background: #e7eaee; border-radius: 12px; padding: 3px; gap: 0; width: fit-content;
}}
.stApp button[data-variant="segmented_control"] {{
    border: 0 !important; border-radius: 9px !important; background: transparent !important;
    min-height: 34px; padding: 0 14px !important; color: var(--muted) !important;
}}
.stApp button[data-variant="segmented_control"][aria-checked="true"] {{
    background: var(--surface) !important; color: var(--text) !important;
}}
.stApp button[data-variant="pills"] p, .stApp button[data-variant="segmented_control"] p {{
    font-size: 14px !important; font-weight: 600; color: inherit !important;
}}

/* ── Buttons: quiet grey pills; Open links are the same shape ──────────── */
.stButton > button, .stDownloadButton > button {{
    background: #e7eaee !important; border: 0 !important; color: var(--text) !important;
    border-radius: 999px !important; min-height: 40px; padding: 0 18px !important;
    transition: background-color .15s ease, transform .1s ease;
}}
.stButton > button:hover, .stDownloadButton > button:hover {{ background: #dce0e5 !important; }}
.stButton > button:active, .stDownloadButton > button:active {{ transform: scale(.98); }}
.stButton > button p, .stDownloadButton > button p {{ font-size: 14px !important; font-weight: 600; }}

/* ── Header ────────────────────────────────────────────────────────────── */
.stApp h1 {{
    font-size: 28px !important; line-height: 34px !important; font-weight: 700 !important;
    letter-spacing: -0.02em; color: var(--text) !important; margin: 0 !important; padding: 0 !important;
}}
.page-head {{ display: flex; justify-content: space-between; align-items: flex-end; gap: 16px; flex-wrap: wrap; }}
.page-sub {{ font-size: 15px; color: var(--muted); margin-top: 4px; }}
.source {{ display: flex; gap: 8px; align-items: center; font-size: 13px; color: var(--muted); }}
.dot {{ width: 8px; height: 8px; border-radius: 50%; background: var(--positive); display: inline-block; }}
.dot.live {{ background: var(--accent); }}

/* ── Cards: white, one large radius, no shadow ─────────────────────────── */
[class*="st-key-card"] {{
    background: var(--surface); border-radius: var(--radius-card); border: 1px solid var(--border);
    padding: 22px 24px 24px; gap: 18px !important;
}}
[data-testid="stColumn"] > [data-testid="stVerticalBlock"]
    > [data-testid="stLayoutWrapper"]:has(> [class*="st-key-card"]) {{
    flex: 1 1 auto;
}}
[data-testid="stColumn"] [class*="st-key-card"] {{ height: 100%; }}
.card-head {{ display: flex; justify-content: space-between; align-items: baseline; gap: 8px 12px; flex-wrap: wrap; }}
.links {{ display: flex; gap: 8px; flex-wrap: wrap; }}
.links a.open {{ background: #eef1f4; }}
.card-title {{
    font-size: 17px; font-weight: 700; color: var(--text); display: inline-flex; align-items: center; gap: 12px;
}}
.card-head.ruled {{ padding-bottom: 16px; border-bottom: 1px solid var(--rule); align-items: center; }}
.ico {{
    width: 34px; height: 34px; border-radius: 10px; display: inline-grid; place-items: center; flex: none;
    background: #f2f4f7; color: #3a3d40;
}}
.ico svg {{ width: 18px; height: 18px; display: block; }}

/* The headline panel: a tinted block, the figure on the left and its facts on the right */
.hero-panel {{
    background: var(--raised); border: 1px solid #e1eaf6; border-radius: 16px; padding: 20px 24px;
    display: flex; justify-content: space-between; align-items: center; gap: 20px 32px; flex-wrap: wrap;
}}
.hero-panel .facts {{ display: flex; gap: 0; }}
.hero-panel .fact {{ padding: 4px 22px; border-left: 1px solid #d8e3f1; min-width: 96px; }}

/* A worked example: how the headline figure is computed */
.steps {{ display: flex; align-items: stretch; gap: 8px; flex-wrap: wrap; }}
.step {{ flex: 1 1 170px; border: 1px solid var(--border); border-radius: 14px; padding: 14px 16px; }}
.step .label {{ font-size: 13px; color: var(--muted); }}
.step .value {{ font-size: 18px; font-weight: 700; margin-top: 2px; font-variant-numeric: tabular-nums; }}
.step .value.pos {{ color: var(--positive); }}
.step .note {{ font-size: 13px; color: var(--muted); margin-top: 2px; }}
.step-arrow {{ display: grid; place-items: center; color: #9aa1a9; font-size: 18px; }}

/* Key under a chart: each swatch is the mark it explains */
.key {{ display: flex; flex-wrap: wrap; gap: 6px 22px; font-size: 13px; color: var(--muted); }}
.key span {{ display: inline-flex; align-items: center; gap: 8px; }}
.key i {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}
.key i.ring {{ background: var(--accent); box-shadow: 0 0 0 2px #fff, 0 0 0 5px #d3e2f8; }}
.card-note {{ font-size: 13px; color: var(--muted); }}

/* The headline figure: dollars large, cents smaller and grey */
.hero-label {{ font-size: 15px; color: var(--muted); }}
.money {{ font-size: 40px; line-height: 46px; font-weight: 600; letter-spacing: -0.02em;
         font-variant-numeric: tabular-nums; color: var(--text); }}
.money .cents {{ font-size: 26px; color: var(--muted); }}
.money.pos {{ color: var(--positive); }}
.money.pos .cents {{ color: var(--positive); opacity: .7; }}
.hero-sub {{ font-size: 15px; color: var(--muted); margin-top: 4px; }}
.hero-sub b {{ color: var(--text); font-weight: 600; }}

/* Tiles: teams and sportsbooks */
.tile {{
    width: 40px; height: 40px; border-radius: 12px; flex: none;
    display: grid; place-items: center; font-size: 13px; font-weight: 700; letter-spacing: .01em;
}}
.tile.sm {{ width: 32px; height: 32px; border-radius: 10px; font-size: 12px; }}
.pair {{ display: flex; flex: none; }}
.pair .tile + .tile {{ margin-left: -10px; box-shadow: 0 0 0 3px var(--surface); }}
.matchup {{ display: flex; align-items: center; gap: 14px; }}
.matchup-name {{ font-size: 17px; font-weight: 600; line-height: 22px; }}
.matchup-meta {{ font-size: 13px; color: var(--muted); line-height: 18px; }}

/* The order ticket: one row per leg */
.ticket {{ background: #f7f9fb; border: 1px solid var(--border); border-radius: 14px; padding: 0 16px 2px; }}
.ticket-head {{
    display: grid; grid-template-columns: 40px 1fr auto auto; gap: 14px; padding: 12px 0 10px;
    font-size: 12px; font-weight: 700; color: var(--muted); border-bottom: 1px solid #e4e7ea;
}}
.ticket-head .r {{ text-align: right; }}
/* Fixed widths so every row's figures line up under the column labels */
.ticket-head .spacer, .leg-open {{ width: 176px; display: flex; justify-content: flex-end; }}
.ticket-head .r, .leg-money {{ min-width: 120px; }}
.leg {{ display: grid; grid-template-columns: 40px 1fr auto auto; gap: 14px; align-items: center;
        min-height: 72px; }}
.leg + .leg {{ border-top: 1px solid #e4e7ea; }}
.leg a.open {{ border: 1px solid var(--border); }}
.leg-main {{ font-size: 15px; font-weight: 600; line-height: 20px; }}
.leg-sub {{ font-size: 13px; color: var(--muted); line-height: 18px; font-variant-numeric: tabular-nums; }}
.leg-money {{ text-align: right; font-variant-numeric: tabular-nums; }}
.leg-money .leg-main {{ font-weight: 600; }}
a.open {{
    display: inline-flex; align-items: center; gap: 4px; height: 34px; padding: 0 14px;
    border-radius: 999px; background: var(--surface); color: var(--text) !important;
    font-size: 14px; font-weight: 600; text-decoration: none !important; white-space: nowrap;
    transition: background-color .15s ease;
}}
a.open:hover {{ background: var(--accent-soft); color: var(--accent-ink) !important; }}
a.open.primary {{ background: var(--accent); color: #fff !important; }}
a.open.primary:hover {{ background: #174fb5; color: #fff !important; }}
.ticket-total {{ display: flex; justify-content: space-between; padding: 0 4px; font-size: 15px;
                 font-variant-numeric: tabular-nums; }}
.ticket-total span:first-child {{ color: var(--muted); }}
.ticket-total b {{ font-weight: 600; }}

/* Stake split: one 100% bar, one hue at falling strengths */
.split {{ display: flex; gap: 3px; height: 10px; }}
.split span {{ display: block; height: 100%; border-radius: 999px; }}
.split-legend {{ display: flex; flex-wrap: wrap; gap: 4px 18px; margin-top: 10px; font-size: 13px; color: var(--muted); }}
.split-legend i {{ display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }}

/* Facts: small label over value, inside a card */
.facts {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 16px; }}
.facts.boxed {{ gap: 0; border: 1px solid var(--border); border-radius: 14px; }}
.facts.boxed .fact {{ padding: 14px 18px; }}
.facts.boxed .fact + .fact {{ border-left: 1px solid var(--border); }}
.fact .label {{ font-size: 13px; color: var(--muted); }}
.fact .value {{ font-size: 20px; font-weight: 600; font-variant-numeric: tabular-nums; margin-top: 2px; }}

/* Pills */
.pill {{
    display: inline-flex; align-items: center; flex: none; white-space: nowrap;
    height: 24px; padding: 0 10px; border-radius: 999px; font-size: 13px; font-weight: 600;
    font-variant-numeric: tabular-nums;
}}
.pill.positive {{ background: var(--pill-positive-bg); color: var(--pill-positive-ink); }}
.pill.warning  {{ background: var(--pill-warning-bg);  color: var(--pill-warning-ink); }}
.pill.neutral  {{ background: var(--pill-neutral-bg);  color: var(--pill-neutral-ink); }}
.pill.accent   {{ background: var(--accent-soft);       color: var(--accent-ink); }}

/* ── Watchlist: a radio whose options are list rows ────────────────────── */
.st-key-watch, .st-key-watch .stRadio, .st-key-watch [role="radiogroup"] {{ width: 100% !important; }}
.st-key-watch [role="radiogroup"] {{ gap: 2px !important; max-height: 620px; overflow-y: auto; }}
.st-key-watch [role="radiogroup"] > div {{
    padding: 12px 14px; border-radius: 14px; cursor: pointer; width: 100%;
    transition: background-color .15s ease;
}}
.st-key-watch [role="radiogroup"] > div:hover {{ background: #f6f7f9; }}
.st-key-watch [role="radiogroup"] > div[data-selected="true"] {{ background: var(--raised); }}
.st-key-watch [data-testid="stRadioOption"] {{ margin: 0 !important; padding: 0 !important; width: 100%; }}
.st-key-watch [data-testid="stRadioOption"] > div,
.st-key-watch [data-testid="stRadioOption"] [data-testid="stMarkdownContainer"] {{ width: 100%; }}
.st-key-watch [data-testid="stRadioOption"] p {{
    display: flex; justify-content: space-between; align-items: center; gap: 12px;
    font-size: 15px !important; line-height: 20px !important; font-weight: 600;
    color: var(--text) !important; margin: 0 !important;
}}
.st-key-watch .stMarkdownBadge {{
    flex: none; white-space: nowrap; border-radius: 999px !important; padding: 2px 10px !important;
    font-size: 13px !important; font-weight: 600; font-variant-numeric: tabular-nums;
    background: var(--pill-neutral-bg) !important; color: var(--pill-neutral-ink) !important;
}}
.st-key-watch .stMarkdownBadge[style*="33, 195, 84"] {{
    background: var(--pill-positive-bg) !important; color: var(--pill-positive-ink) !important;
}}
.st-key-watch [data-testid="stRadioCaption"] {{ margin: 2px 0 0 !important; padding: 0 !important; }}
.st-key-watch [data-testid="stRadioCaption"] p {{
    font-size: 13px !important; line-height: 18px !important; color: var(--muted) !important; margin: 0 !important;
}}

/* ── Market strip (SVG) ────────────────────────────────────────────────── */
.strip svg {{ display: block; width: 100%; height: auto; overflow: visible; }}
.strip text {{ font-family: var(--font); }}

/* ── Rows (EV bets, opportunities) ─────────────────────────────────────── */
.rows {{ display: flex; flex-direction: column; border: 1px solid var(--border); border-radius: 14px; padding: 0 16px; }}
.row {{ display: grid; grid-template-columns: 40px 1fr auto auto; gap: 14px; align-items: center; min-height: 76px; }}
.row + .row {{ border-top: 1px solid var(--rule); }}
.row-main {{ font-size: 15px; font-weight: 600; line-height: 20px; }}
.row-sub {{ font-size: 13px; color: var(--muted); line-height: 18px; }}
.row-end {{ text-align: right; }}
.row-value {{ font-size: 16px; font-weight: 600; font-variant-numeric: tabular-nums; }}
.row-value.pos {{ color: var(--positive); }}
.rows a.open {{ background: #eef1f4; }}
.rows a.open:hover {{ background: var(--accent-soft); }}

.empty {{
    border: 1px dashed var(--control); border-radius: 14px; padding: 16px 18px;
    font-size: 15px; color: var(--muted); background: var(--surface);
}}
.empty b {{ color: var(--text); font-weight: 600; }}
[data-testid="stAlertContainer"] {{ border-radius: 14px !important; }}

/* Usage bar (API quota) */
.usage {{ padding: 0 8px; }}
.usage .row-u {{ display: flex; justify-content: space-between; font-size: 13px; color: var(--muted); }}
.usage .row-u b {{ font-weight: 600; color: var(--text); font-variant-numeric: tabular-nums; }}
.usage .track {{ height: 6px; border-radius: 999px; background: #e3e7eb; margin-top: 8px; overflow: hidden; }}
.usage .fill {{ height: 100%; border-radius: 999px; background: var(--accent); }}
.usage .fill.low {{ background: var(--negative); }}

[data-testid="stExpander"] details {{ background: var(--surface) !important; border: 0 !important; border-radius: 14px !important; }}

.stApp a:focus-visible, .stApp button:focus-visible {{ outline: 2px solid var(--accent) !important; outline-offset: 2px; }}

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
    .stApp h1 {{ font-size: 24px !important; line-height: 30px !important; }}
    [class*="st-key-card"] {{ padding: 18px; }}
    .money {{ font-size: 34px; line-height: 40px; }}
    .ticket {{ padding: 4px 12px; }}
    .leg {{ grid-template-columns: 32px 1fr auto; gap: 10px; }}
    .leg .tile {{ width: 32px; height: 32px; border-radius: 10px; font-size: 12px; }}
    .leg .leg-open {{ grid-column: 2 / -1; padding-bottom: 12px; width: auto; justify-content: flex-start; }}
    .leg-money {{ min-width: 0; }}
    .row {{ grid-template-columns: 32px 1fr auto; gap: 10px; }}
    .row .tile {{ width: 32px; height: 32px; border-radius: 10px; font-size: 12px; }}
    .row .row-open {{ display: none; }}
    .hero-panel {{ padding: 16px; }}
    .hero-panel .facts {{ width: 100%; }}
    .hero-panel .fact {{ flex: 1; padding: 4px 10px; }}
    .hero-panel .fact:first-child {{ border-left: 0; padding-left: 0; }}
    .ticket-head {{ display: none; }}
    .facts.boxed {{ grid-template-columns: 1fr 1fr; }}
    .facts.boxed .fact:nth-child(3) {{ border-left: 0; }}
    .facts.boxed .fact:nth-child(n+3) {{ border-top: 1px solid var(--border); }}
    .step-arrow {{ display: none; }}
}}

@media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; }} }}
</style>
"""


def inject_css() -> None:
    """Inject the global stylesheet into the current Streamlit page."""
    st.markdown(CSS, unsafe_allow_html=True)
