import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

from urllib.parse import quote_plus
from datetime import datetime, timezone
from api_client import get_odds, get_sports
from arbitrage import analyze_event
from exporter import (
    analyses_to_dataframe,
    export_detailed_csv,
    export_summary_csv,
)

st.set_page_config(
    page_title="BetScan — Arbitrage Finder",
    layout="wide",
    initial_sidebar_state="expanded",
)


BOOK_LINKS = {
    "DraftKings": "https://sportsbook.draftkings.com/",
    "FanDuel": "https://sportsbook.fanduel.com/",
    "BetMGM": "https://sports.betmgm.com/",
    "Caesars": "https://sportsbook.caesars.com/",
    "BetRivers": "https://www.betrivers.com/",
    "PointsBet": "https://pointsbet.com/",
    "Barstool": "https://barstoolsportsbook.com/",
    "Hard Rock Bet": "https://www.hardrock.bet/",
    "ESPN BET": "https://espnbet.com/",
    "Fanatics": "https://sportsbook.fanatics.com/",
    "Bet365": "https://www.bet365.com/",
    "William Hill": "https://www.williamhill.com/",
    "888sport": "https://www.888sport.com/",
    "Unibet": "https://www.unibet.com/",
    "Pinnacle": "https://www.pinnacle.com/",
    "Betway": "https://www.betway.com/",
    "LeoVegas": "https://www.leovegas.com/",
    "Coral": "https://sports.coral.co.uk/",
    "Ladbrokes": "https://sports.ladbrokes.com/",
    "Bovada": "https://www.bovada.lv/",
    "MyBookie.ag": "https://www.mybookie.ag/",
    "LowVig.ag": "https://www.lowvig.ag/",
    "BetUS": "https://www.betus.com.pa/",
    "BetUS.ag": "https://www.betus.com.pa/",
    "BetOnline": "https://www.betonline.ag/",
    "BetOnline.ag": "https://www.betonline.ag/",
}


# ─── DESIGN SYSTEM ────────────────────────────────────────────────────────────
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


st.markdown(f"""
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
/* Remove top spacer so the sidebar starts directly at BetScan and doesn't scroll from hidden chrome. */
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {{
    padding-top: 0 !important;
}}
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {{
    padding-top: 0 !important;
}}
section[data-testid="stSidebar"] button[data-testid="stSidebarCollapseButton"] {{
    display: none !important;
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

/* ── EXPANDER ── */
.streamlit-expanderHeader {{
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-size: 0.8rem !important;
}}
.streamlit-expanderContent {{
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
    border-radius: 0 0 8px 8px !important;
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
""", unsafe_allow_html=True)


# ─── HELPERS ──────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def load_sports():
    sports = get_sports()
    excluded_keywords = ["winner", "outrights", "championship"]
    filtered_sports = {}
    for sport in sports:
        key = sport["key"]
        title = sport["title"]
        if any(word in key.lower() for word in excluded_keywords):
            continue
        filtered_sports[title] = key
    return filtered_sports


@st.cache_data(ttl=60)
def load_data(sport_key: str, market: str, region: str, bankroll: float):
    try:
        events = get_odds(
            sport=sport_key,
            markets=market,
            regions=region,
            odds_format="american",
            include_links=True,
            include_sids=True,
        )
    except Exception as e:
        raise Exception(f"This sport or market is not supported right now. API details: {e}") from e

    all_analyses = []
    for event in events:
        analysis = analyze_event(event, bankroll, selected_market=market)
        if analysis is not None:
            all_analyses.append(analysis)

    detail_df = analyses_to_dataframe(all_analyses)
    event_df = summarize_by_event(all_analyses)
    detail_df = add_direct_links(detail_df, all_analyses)

    return all_analyses, detail_df, event_df


def summarize_by_event(all_analyses):
    rows = []
    for analysis in all_analyses:
        rows.append({
            "Game": analysis["event"],
            "Sport": analysis["sport"],
            "Start Time": analysis["commence_time"],
            "Market Efficiency": round(analysis["implied_prob_sum"], 4),
            "Guaranteed Profit": "Yes" if analysis["arbitrage"] else "No",
            "Profit ($)": round(analysis["profit"], 2) if analysis["profit"] is not None else None,
            "Return (%)": round(analysis["roi"], 2) if analysis["roi"] is not None else None,
        })
    return pd.DataFrame(rows)


def add_direct_links(df, analyses):
    df = df.copy()
    df["Direct Link"] = None
    for idx, row in df.iterrows():
        game = row.get("event") or row.get("Game")
        book = row.get("bookmaker")
        if not game or not book:
            continue
        for analysis in analyses:
            if analysis.get("event") == game:
                for res in analysis.get("results", []):
                    if res.get("bookmaker") == book:
                        df.at[idx, "Direct Link"] = res.get("link")
                        break
                break
    return df


def format_event_detail(df: pd.DataFrame) -> pd.DataFrame:
    display_df = df.copy()
    rename_map = {
        "event": "Game", "sport": "Sport", "commence_time": "Start Time",
        "implied_prob_sum": "Market Efficiency", "arbitrage": "Guaranteed Profit",
        "profit": "Profit ($)", "roi": "Return (%)", "outcome": "Bet On",
        "bookmaker": "Sportsbook", "american_odds": "American Odds",
        "decimal_odds": "Decimal Odds", "stake": "Suggested Bet ($)",
    }
    display_df = display_df.rename(columns=rename_map)
    for col in ["Market Efficiency", "Profit ($)", "Return (%)", "Decimal Odds", "Suggested Bet ($)"]:
        if col in display_df.columns:
            rnd = 4 if col in ["Market Efficiency", "Decimal Odds"] else 2
            display_df[col] = pd.to_numeric(display_df[col], errors="coerce").round(rnd)
    return display_df


def is_live_event(commence_time_str: str) -> bool:
    if not commence_time_str:
        return False
    try:
        event_time = datetime.fromisoformat(commence_time_str.replace("Z", "+00:00"))
        return event_time <= datetime.now(timezone.utc)
    except Exception:
        return False


def format_market_label(market_key: str) -> str:
    return {"h2h": "Moneyline / Match Winner", "spreads": "Point Spread", "totals": "Game Total"}.get(market_key, market_key)


def clean_bookmaker_link(raw_link: str, book_title: str) -> str:
    if not raw_link or not str(raw_link).startswith("http"):
        return None
    link_str = str(raw_link).strip()
    if "betmgm.com" in link_str.lower():
        if "{state}" in link_str:
            link_str = link_str.replace("{state}", "www")
        if "sports.www.betmgm.com" in link_str or "{state}" in link_str:
            return None
    return link_str


def normalize_book_name(name: str) -> str:
    name_lower = name.lower()
    mapping = {
        "draftkings": "DraftKings", "fanduel": "FanDuel", "betmgm": "BetMGM",
        "caesars": "Caesars", "betrivers": "BetRivers", "pointsbet": "PointsBet",
        "barstool": "Barstool", "hard rock": "Hard Rock Bet", "espn": "ESPN BET",
        "fanatics": "Fanatics", "bet365": "Bet365", "william hill": "William Hill",
        "888": "888sport", "unibet": "Unibet", "pinnacle": "Pinnacle",
        "betway": "Betway", "leovegas": "LeoVegas", "coral": "Coral",
        "ladbrokes": "Ladbrokes", "bovada": "Bovada", "mybookie": "MyBookie.ag",
        "lowvig": "LowVig.ag", "betus": "BetUS", "betonline": "BetOnline",
    }
    for key in mapping:
        if key in name_lower:
            return mapping[key]
    return name.title()


def efficiency_badge(eff: float) -> str:
    base = (
        "display:inline-block; padding:3px 12px; border-radius:20px; "
        "font-size:0.68rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase;"
    )
    if eff < 1.0:
        style = f"{base} background:rgba(0,229,160,0.15); color:#00e5a0; border:1px solid #00e5a0;"
        return f'<span style="{style}">&#9889; Arbitrage</span>'
    elif eff < 1.015:
        style = f"{base} background:rgba(245,166,35,0.12); color:#f5a623; border:1px solid #f5a623;"
        return f'<span style="{style}">&#9670; Near Arb</span>'
    else:
        style = f"{base} background:rgba(107,118,148,0.15); color:#6b7694; border:1px solid #2a2f3e;"
        return f'<span style="{style}">&#9671; Normal</span>'


def build_game_info_link(game_name: str) -> str:
    return f"https://www.google.com/search?q={quote_plus(game_name + ' ESPN')}"


def build_general_odds_info_link(game_name: str) -> str:
    return f"https://www.google.com/search?q={quote_plus(game_name + ' odds')}"


# ─── CHARTS ──────────────────────────────────────────────────────────────────

def chart_efficiency_ranking(event_df: pd.DataFrame, top_n: int = 20) -> go.Figure:
    """Horizontal bar chart — market efficiency for top N games."""
    df = event_df.sort_values("Market Efficiency").head(top_n).copy()

    def bar_color(eff):
        if eff < 1.0:
            return COLORS["arb_green"]
        elif eff < 1.015:
            return COLORS["warning"]
        return COLORS["accent2"]

    colors = [bar_color(e) for e in df["Market Efficiency"]]

    # Shorten game names for display
    short_names = [g[:30] + "…" if len(g) > 30 else g for g in df["Game"]]

    fig = go.Figure(go.Bar(
        x=df["Market Efficiency"],
        y=short_names,
        orientation="h",
        marker_color=colors,
        marker_line_width=0,
        text=[f"{e:.4f}" for e in df["Market Efficiency"]],
        textposition="outside",
        textfont=dict(color=COLORS["text"], size=10),
        hovertemplate="<b>%{y}</b><br>Efficiency: %{x:.4f}<extra></extra>",
    ))

    fig.add_vline(
        x=1.0, line_width=1.5, line_dash="dash",
        line_color=COLORS["arb_green"],
        annotation_text=" Arbitrage threshold",
        annotation_font_color=COLORS["arb_green"],
        annotation_font_size=10,
    )

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="Market Efficiency Ranking", font_size=13, font_color=COLORS["text_muted"]),
        xaxis=dict(
            showgrid=True, gridcolor=COLORS["border"], gridwidth=0.5,
            zeroline=False, tickfont_size=10,
            range=[max(0.95, df["Market Efficiency"].min() - 0.005),
                   df["Market Efficiency"].max() + 0.008],
        ),
        yaxis=dict(showgrid=False, tickfont_size=10),
        height=max(300, len(df) * 34),
        bargap=0.35,
    )
    return fig


def chart_odds_comparison(event_rows_df: pd.DataFrame, game_name: str) -> go.Figure:
    """Grouped bar chart comparing decimal odds per outcome for a selected game."""
    df = event_rows_df[["Bet On", "Sportsbook", "Decimal Odds"]].dropna()

    outcomes = df["Bet On"].unique()
    colors_list = [COLORS["accent"], COLORS["accent2"], COLORS["warning"], COLORS["danger"]]

    fig = go.Figure()
    for i, outcome in enumerate(outcomes):
        sub = df[df["Bet On"] == outcome].sort_values("Decimal Odds", ascending=False)
        fig.add_trace(go.Bar(
            name=str(outcome),
            x=sub["Sportsbook"],
            y=sub["Decimal Odds"],
            marker_color=colors_list[i % len(colors_list)],
            marker_line_width=0,
            text=[f"{v:.3f}" for v in sub["Decimal Odds"]],
            textposition="outside",
            textfont=dict(size=9, color=COLORS["text"]),
            hovertemplate="<b>%{x}</b><br>Odds: %{y:.4f}<extra>" + str(outcome) + "</extra>",
        ))

    fig.update_layout(
        **PLOTLY_LAYOUT,
        barmode="group",
        xaxis=dict(showgrid=False, tickfont_size=10, tickangle=-30),
        yaxis=dict(showgrid=True, gridcolor=COLORS["border"], gridwidth=0.5, zeroline=False, tickfont_size=10),
        legend=dict(
            bgcolor="rgba(0,0,0,0)", bordercolor=COLORS["border"], borderwidth=1,
            font_size=10, orientation="h", yanchor="bottom", y=1.02,
        ),
        height=340,
        bargap=0.2,
        bargroupgap=0.08,
    )
    return fig


def chart_stake_pie(event_rows_df: pd.DataFrame, bankroll: float) -> go.Figure | None:
    """Pie / donut chart for stake allocation in arbitrage situations."""
    df = event_rows_df[["Bet On", "Suggested Bet ($)"]].dropna(subset=["Suggested Bet ($)"])
    if df.empty:
        return None

    colors_list = [COLORS["accent"], COLORS["accent2"], COLORS["warning"], COLORS["danger"]]

    fig = go.Figure(go.Pie(
        labels=df["Bet On"],
        values=df["Suggested Bet ($)"],
        hole=0.55,
        marker=dict(colors=colors_list[:len(df)], line=dict(color=COLORS["bg"], width=2)),
        textinfo="label+percent",
        textfont=dict(size=11, color=COLORS["text"]),
        hovertemplate="<b>%{label}</b><br>Stake: $%{value:.2f}<br>(%{percent})<extra></extra>",
    ))

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text=f"Stake Split (${bankroll:.0f})", font_size=13, font_color=COLORS["text_muted"]),
        legend=dict(bgcolor="rgba(0,0,0,0)", font_size=10),
        height=280,
        annotations=[dict(
            text=f"${bankroll:.0f}", x=0.5, y=0.5, font_size=18,
            font_color=COLORS["text"], showarrow=False,
            font=dict(family="Syne", weight=700),
        )],
    )
    return fig


def chart_efficiency_gauge(efficiency: float) -> go.Figure:
    """Gauge / speedometer for a single game's market efficiency."""
    if efficiency < 1.0:
        gauge_color = COLORS["arb_green"]
        label = "ARBITRAGE"
    elif efficiency < 1.015:
        gauge_color = COLORS["warning"]
        label = "NEAR ARB"
    else:
        gauge_color = COLORS["accent2"]
        label = "NORMAL"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=efficiency,
        number=dict(
            suffix="",
            valueformat=".4f",
            font=dict(size=22, color=COLORS["text"], family="IBM Plex Mono"),
        ),
        gauge=dict(
            axis=dict(
                range=[0.96, 1.08],
                tickwidth=1,
                tickcolor=COLORS["border"],
                tickfont=dict(color=COLORS["text_muted"], size=9),
                nticks=7,
            ),
            bar=dict(color=gauge_color, thickness=0.22),
            bgcolor=COLORS["surface2"],
            borderwidth=0,
            steps=[
                dict(range=[0.96, 1.0], color="rgba(0,229,160,0.12)"),
                dict(range=[1.0, 1.015], color="rgba(245,166,35,0.10)"),
                dict(range=[1.015, 1.08], color="rgba(61,155,255,0.06)"),
            ],
            threshold=dict(
                line=dict(color=COLORS["arb_green"], width=2),
                thickness=0.8, value=1.0,
            ),
        ),
        title=dict(
            text=f"<b>{label}</b>",
            font=dict(size=11, color=gauge_color, family="Syne"),
        ),
        domain=dict(x=[0, 1], y=[0, 1]),
    ))

    layout = {**PLOTLY_LAYOUT, "margin": dict(l=20, r=20, t=40, b=10)}
    fig.update_layout(**layout, height=220)
    return fig


def chart_roi_scatter(event_df: pd.DataFrame) -> go.Figure:
    """Scatter: efficiency vs. ROI for arbitrage games."""
    df = event_df[event_df["Guaranteed Profit"] == "Yes"].dropna(subset=["Return (%)"])
    if df.empty:
        return None

    short_names = [g[:22] + "…" if len(g) > 22 else g for g in df["Game"]]

    fig = go.Figure(go.Scatter(
        x=df["Market Efficiency"],
        y=df["Return (%)"],
        mode="markers+text",
        text=short_names,
        textposition="top center",
        textfont=dict(size=9, color=COLORS["text_muted"]),
        marker=dict(
            size=12,
            color=df["Return (%)"],
            colorscale=[[0, COLORS["accent2"]], [1, COLORS["arb_green"]]],
            showscale=False,
            line=dict(color=COLORS["border"], width=1),
        ),
        hovertemplate="<b>%{text}</b><br>Efficiency: %{x:.4f}<br>ROI: %{y:.2f}%<extra></extra>",
    ))

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="Arbitrage Opportunities — Efficiency vs. ROI", font_size=13, font_color=COLORS["text_muted"]),
        xaxis=dict(showgrid=True, gridcolor=COLORS["border"], title="Market Efficiency", title_font_size=10, tickfont_size=10),
        yaxis=dict(showgrid=True, gridcolor=COLORS["border"], title="ROI (%)", title_font_size=10, tickfont_size=10),
        height=320,
    )
    return fig




def build_prices_table(event_rows, bankroll):
    import pandas as pd
    has_stake = (
        "Suggested Bet ($)" in event_rows.columns
        and event_rows["Suggested Bet ($)"].notna().any()
    )
    has_link = (
        "Direct Link" in event_rows.columns
        and event_rows["Direct Link"].notna().any()
    )
    outcome_colors = ["#00e5a0", "#3d9bff", "#f5a623", "#ff5b5b"]
    th = ("padding:10px 14px;text-align:left;font-size:0.62rem;text-transform:uppercase;"
          "letter-spacing:0.1em;color:#6b7694;border-bottom:1px solid #2a2f3e;white-space:nowrap;")
    td = "padding:11px 14px;font-size:0.82rem;color:#e8ecf3;border-bottom:1px solid #1e222d;white-space:nowrap;"
    tn = td + "text-align:right;font-family:'IBM Plex Mono',monospace;"
    rows_html = ""
    for i, (_, row) in enumerate(event_rows.iterrows()):
        outcome  = row.get("Bet On", "")
        book     = row.get("Sportsbook", "")
        am_odds  = row.get("American Odds", "")
        dec_odds = row.get("Decimal Odds", "")
        stake    = row.get("Suggested Bet ($)", None)
        link     = row.get("Direct Link", None)
        accent = outcome_colors[i % len(outcome_colors)]
        bg = "#161922" if i % 2 == 0 else "#13161f"
        try:
            am_int = int(am_odds)
            am_color = "#00e5a0" if am_int > 0 else "#e8ecf3"
            am_prefix = "+" if am_int > 0 else ""
        except (ValueError, TypeError):
            am_int, am_color, am_prefix = None, "#e8ecf3", ""
        try:
            dec_str = f"{float(dec_odds):.4f}"
        except (ValueError, TypeError):
            dec_str = str(dec_odds)
        try:
            stake_str = f"${float(stake):.2f}" if stake is not None and str(stake) != "nan" else "&#8212;"
        except (ValueError, TypeError):
            stake_str = "&#8212;"
        if link and str(link).startswith("http"):
            link_cell = (f'<a href="{link}" target="_blank" style="display:inline-block;padding:3px 10px;'
                         'border-radius:5px;background:rgba(61,155,255,0.1);border:1px solid #3d9bff;'
                         'color:#3d9bff;font-size:0.7rem;text-decoration:none;text-transform:uppercase;">'
                         'Bet &#8594;</a>')
        else:
            link_cell = '<span style="color:#6b7694;">&#8212;</span>'
        stake_td = f'<td style="{tn}color:#f5a623;">{stake_str}</td>' if has_stake else ""
        link_td  = f'<td style="{td}">{link_cell}</td>' if has_link else ""
        rows_html += (
            f'<tr style="background:{bg};">'
            f'<td style="{td}border-left:3px solid {accent};font-weight:600;color:{accent};">{outcome}</td>'
            f'<td style="{td}">{book}</td>'
            f'<td style="{tn}color:{am_color};">{am_prefix}{am_odds}</td>'
            f'<td style="{tn}">{dec_str}</td>'
            f'{stake_td}{link_td}'
            f'</tr>'
        )
    sh = f'<th style="{th}text-align:right;">Suggested Bet</th>' if has_stake else ""
    lh = f'<th style="{th}">Place Bet</th>' if has_link else ""
    return (
        '<div style="border:1px solid #2a2f3e;border-radius:10px;overflow:hidden;width:100%;">'
        '<table style="width:100%;border-collapse:collapse;">'
        f'<thead><tr style="background:#1e222d;">'
        f'<th style="{th}">Outcome</th><th style="{th}">Sportsbook</th>'
        f'<th style="{th}text-align:right;">Amer. Odds</th>'
        f'<th style="{th}text-align:right;">Dec. Odds</th>'
        f'{sh}{lh}</tr></thead>'
        f'<tbody>{rows_html}</tbody></table></div>'
    )



# ─── SIDEBAR ──────────────────────────────────────────────────────────────────

available_sports = load_sports()

common_sports = ["NBA", "NFL", "MLB", "NHL", "English Premier League", "NCAAB", "NCAAF"]
sport_options = [s for s in common_sports if s in available_sports]
sport_options += [s for s in available_sports if s not in sport_options]

with st.sidebar:
    st.markdown("## ⚡ BetScan")
    st.markdown("---")

    sport_title = st.selectbox("Sport", sport_options)
    sport_key = available_sports[sport_title]

    market_display = st.selectbox(
        "Market type",
        ["Moneyline / Match Winner", "Point Spread", "Game Total"],
    )
    market_map = {
        "Moneyline / Match Winner": "h2h",
        "Point Spread": "spreads",
        "Game Total": "totals",
    }
    market = market_map[market_display]

    region_display = st.selectbox(
        "Sportsbook region",
        ["United States", "United Kingdom", "Europe", "Australia"],
    )
    region_map = {"United States": "us", "United Kingdom": "uk", "Europe": "eu", "Australia": "au"}
    region = region_map[region_display]

    bankroll = st.number_input("Budget per game ($)", min_value=1.0, value=100.0, step=10.0)

    st.markdown("---")

    view_mode = st.radio("View mode", ["Simple", "Advanced"], horizontal=True)
    show_only_arbitrage = st.checkbox("Show only arbitrage opportunities", value=False)

    if view_mode == "Advanced":
        max_efficiency = st.slider("Max market efficiency", 1.00, 1.10, 1.03, 0.001,
                                   help="Lower = better value. Arbitrage < 1.000")
        top_n = st.slider("Games to show", 5, 100, 15, 5)
    else:
        max_efficiency = 1.03
        top_n = 10

    st.markdown("---")
    refresh = st.button("↻ Refresh data", use_container_width=True)

if refresh:
    st.cache_data.clear()


# ─── LOAD DATA ────────────────────────────────────────────────────────────────

with st.spinner("Scanning sportsbooks for value…"):
    try:
        all_analyses, detail_df, event_df = load_data(sport_key, market, region, bankroll)
    except Exception as e:
        st.error(f"Error loading API data: {e}")
        st.stop()

if event_df.empty:
    st.warning("No games were returned for these settings.")
    st.stop()

filtered_event_df = event_df[event_df["Market Efficiency"] <= max_efficiency].copy()
if show_only_arbitrage:
    filtered_event_df = filtered_event_df[filtered_event_df["Guaranteed Profit"] == "Yes"]

matching_games = filtered_event_df["Game"].tolist()
filtered_detail_df = detail_df[detail_df["event"].isin(matching_games)].copy()
display_detail_df = format_event_detail(filtered_detail_df)

filtered_analyses = [a for a in all_analyses if a["event"] in matching_games]
summary_export_df = export_summary_csv("betting_opportunities_summary.csv", filtered_analyses)
detailed_export_df = export_detailed_csv("betting_opportunities_detailed.csv", filtered_analyses)

best_efficiency = float(filtered_event_df["Market Efficiency"].min()) if not filtered_event_df.empty else None
arb_count = int((filtered_event_df["Guaranteed Profit"] == "Yes").sum())
best_roi_row = filtered_event_df[filtered_event_df["Return (%)"].notna()].sort_values("Return (%)", ascending=False)
best_roi = float(best_roi_row.iloc[0]["Return (%)"]) if not best_roi_row.empty else None


# ─── HEADER ───────────────────────────────────────────────────────────────────

st.markdown("""
<div class="header-bar">
  <h1>BetScan</h1>
  <span class="header-tag">Live Odds</span>
</div>
""", unsafe_allow_html=True)
st.caption("Real-time arbitrage detection across major sportsbooks. Data refreshes every 60 seconds.")

st.markdown("---")

# ── KPI ROW ──
c1, c2, c3, c4 = st.columns(4)
c1.metric("Games Scanned", len(event_df))
c2.metric("Arbitrage Found", arb_count, delta="guaranteed" if arb_count > 0 else None)
c3.metric("Best Efficiency", f"{best_efficiency:.4f}" if best_efficiency else "—")
c4.metric("Best ROI", f"{best_roi:.2f}%" if best_roi else "—")

st.markdown("")


# ─── MARKET EFFICIENCY CHART ──────────────────────────────────────────────────

with st.expander("📊 Market Efficiency Ranking — all games", expanded=True):
    fig_rank = chart_efficiency_ranking(event_df, top_n=min(top_n, len(event_df)))
    st.plotly_chart(fig_rank, use_container_width=True, config={"displayModeBar": False})

    if arb_count > 0:
        scatter_fig = chart_roi_scatter(event_df)
        if scatter_fig:
            st.plotly_chart(scatter_fig, use_container_width=True, config={"displayModeBar": False})


# ─── TOP GAMES TABLE ──────────────────────────────────────────────────────────

arb_df = filtered_event_df[filtered_event_df["Guaranteed Profit"] == "Yes"].sort_values("Return (%)", ascending=False)

st.subheader("Top Games Right Now")

if arb_df.empty:
    closest_df = filtered_event_df.sort_values("Market Efficiency").head(top_n)
    if closest_df.empty:
        st.info("No games match your current filters.")
    else:
        st.info("No guaranteed-profit games found. Showing closest opportunities.")
        st.dataframe(closest_df, use_container_width=True, hide_index=True)
else:
    top_display_df = arb_df.head(top_n)
    st.dataframe(top_display_df, use_container_width=True, hide_index=True)

    best = top_display_df.iloc[0]
    if pd.notna(best["Return (%)"]) and pd.notna(best["Profit ($)"]):
        st.success(
            f"⚡ Best right now: **{best['Game']}** · "
            f"Return: **{best['Return (%)']:.2f}%** · "
            f"Profit: **${best['Profit ($)']:.2f}**"
        )

st.markdown("---")


# ─── SUMMARY VIEW ─────────────────────────────────────────────────────────────

with st.expander("📋 Summary View — all filtered games"):
    summary_display_df = summary_export_df.rename(columns={
        "event": "Game", "sport": "Sport", "commence_time": "Start Time",
        "implied_prob_sum": "Market Efficiency", "arbitrage": "Guaranteed Profit",
        "profit": "Profit ($)", "roi": "Return (%)", "best_outcome": "Best Team / Side",
        "best_bookmaker": "Best Sportsbook", "best_american_odds": "Best American Odds",
        "best_decimal_odds": "Best Decimal Odds",
    })
    st.dataframe(summary_display_df, use_container_width=True, hide_index=True)


# ─── GAME BREAKDOWN ───────────────────────────────────────────────────────────

st.subheader("Game Breakdown")

if matching_games:
    preferred_games = (
        arb_df["Game"].tolist() if not arb_df.empty
        else filtered_event_df.sort_values("Market Efficiency")["Game"].tolist()
    )

    selected_game = st.selectbox("Select a game", preferred_games)

    event_rows = display_detail_df[display_detail_df["Game"] == selected_game].copy()
    event_summary = filtered_event_df[filtered_event_df["Game"] == selected_game].iloc[0]

    efficiency_val = float(event_summary["Market Efficiency"])
    commence_time = event_summary.get("Start Time") or ""
    is_live = is_live_event(str(commence_time))
    profit_val = event_summary["Profit ($)"]
    roi_val = event_summary["Return (%)"]

    # ── Top info bar ──
    badge_html = efficiency_badge(efficiency_val)
    live_html = (
        '<div style="display:inline-flex;align-items:center;gap:7px;font-weight:700;'
        'color:#ff5b5b;font-size:0.8rem;letter-spacing:0.1em;text-transform:uppercase;">'
        '<span style="width:9px;height:9px;background:#ff5b5b;border-radius:50%;display:inline-block;"></span>'
        'LIVE</div>'
        if is_live else ""
    )
    game_card_html = (
        '<div style="background:#161922;border:1px solid #2a2f3e;border-radius:10px;'
        'padding:1rem 1.2rem;margin-bottom:0.75rem;">'
        '<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">'
        '<div>'
        '<span style="font-size:0.62rem;color:#6b7694;text-transform:uppercase;'
        'letter-spacing:0.12em;display:block;margin-bottom:4px;">Selected Game</span>'
        f'<div style="font-family:Syne,sans-serif;font-size:1.1rem;font-weight:700;color:#e8ecf3;">{selected_game}</div>'
        f'<div style="font-size:0.75rem;color:#6b7694;margin-top:4px;">{event_summary["Sport"]} &middot; {format_market_label(market)}</div>'
        '</div>'
        f'<div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px;">{live_html}{badge_html}</div>'
        '</div>'
        '</div>'
    )
    st.markdown(game_card_html, unsafe_allow_html=True)

    # ── Charts row ──
    ch1, ch2, ch3 = st.columns([2.2, 2.2, 1.6])

    with ch1:
        fig_odds = chart_odds_comparison(event_rows, selected_game)
        st.plotly_chart(fig_odds, use_container_width=True, config={"displayModeBar": False})

    with ch2:
        pie_fig = chart_stake_pie(event_rows, bankroll)
        if pie_fig:
            st.plotly_chart(pie_fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Stake split only shown for arbitrage games.")

    with ch3:
        gauge_fig = chart_efficiency_gauge(efficiency_val)
        st.plotly_chart(gauge_fig, use_container_width=True, config={"displayModeBar": False})

    # ── Detail table + sidebar panel ──
    left, right = st.columns([1.5, 1])

    simple_cols = ["Bet On", "Sportsbook", "American Odds", "Decimal Odds"]
    if "Suggested Bet ($)" in event_rows.columns and event_rows["Suggested Bet ($)"].notna().any():
        simple_cols.append("Suggested Bet ($)")
    if "Direct Link" in event_rows.columns:
        simple_cols.append("Direct Link")

    with left:
        st.markdown("##### Best Prices")
        st.markdown(build_prices_table(event_rows, bankroll), unsafe_allow_html=True)

        st.markdown("")
        if pd.notna(roi_val):
            st.success(f"Expected return: **{roi_val:.2f}%** · Estimated profit: **${profit_val:.2f}**")
        else:
            st.info("No guaranteed arbitrage opportunity for this game.")

    with right:
        st.markdown("##### Links & Info")
        m1, m2 = st.columns(2)
        with m1:
            st.metric(f"Profit (${bankroll:.0f})", f"${profit_val:.2f}" if pd.notna(profit_val) else "N/A")
        with m2:
            st.metric("Return", f"{roi_val:.2f}%" if pd.notna(roi_val) else "N/A")

        st.markdown("")
        st.link_button("Open matchup news", build_game_info_link(selected_game), use_container_width=True)
        st.link_button("Search odds info", build_general_odds_info_link(selected_game), use_container_width=True)

        st.markdown("")
        st.markdown('<span class="section-label">Sportsbooks</span>', unsafe_allow_html=True)
        sportsbooks_used = event_rows["Sportsbook"].dropna().unique().tolist()
        for book in sportsbooks_used:
            normalized = normalize_book_name(book)
            direct_link = None
            for analysis in filtered_analyses:
                if analysis.get("event") == selected_game:
                    for res in analysis.get("results", []):
                        if res.get("bookmaker") == book:
                            direct_link = res.get("link")
                            break
                    if direct_link:
                        break
            cleaned_link = clean_bookmaker_link(direct_link, normalized)
            if cleaned_link and cleaned_link.startswith("http"):
                st.link_button(f"→ {normalized}", cleaned_link, use_container_width=True)
            else:
                homepage = BOOK_LINKS.get(normalized)
                if homepage:
                    st.link_button(f"{normalized} (Home)", homepage, use_container_width=True)
                else:
                    st.write(normalized)

    st.caption("Direct links are provided by the bookmaker when available.")

else:
    st.info("No games match the current filters.")

st.markdown("---")


# ─── ALL RESULTS EXPANDER ────────────────────────────────────────────────────

with st.expander("🗂 Show all filtered results"):
    if display_detail_df.empty:
        st.info("No results to show.")
    else:
        useful_cols = [
            "Game", "Sport", "Bet On", "Sportsbook", "American Odds", "Decimal Odds",
            "Suggested Bet ($)", "Profit ($)", "Return (%)", "Guaranteed Profit",
        ]
        existing_cols = [c for c in useful_cols if c in display_detail_df.columns]
        st.dataframe(
            display_detail_df[existing_cols].sort_values(
                ["Game", "Decimal Odds"], ascending=[True, False]
            ),
            use_container_width=True, hide_index=True,
        )


# ─── DOWNLOAD ────────────────────────────────────────────────────────────────

st.subheader("Download Data")
col1, col2 = st.columns(2)
with col1:
    st.download_button(
        "↓ Summary CSV",
        summary_export_df.to_csv(index=False).encode("utf-8"),
        "betting_opportunities_summary.csv",
        "text/csv",
        use_container_width=True,
    )
with col2:
    st.download_button(
        "↓ Detailed CSV",
        detailed_export_df.to_csv(index=False).encode("utf-8"),
        "betting_opportunities_detailed.csv",
        "text/csv",
        use_container_width=True,
    )