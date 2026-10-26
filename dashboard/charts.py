# =============================================================================
# charts.py
# Plotly figures used by the dashboard. Every chart shares PLOTLY_LAYOUT and
# the COLORS palette so the visuals read as one system.
# =============================================================================

import pandas as pd
import plotly.graph_objects as go

from .config import NEAR_ARB_THRESHOLD
from .theme import COLORS, PLOTLY_LAYOUT


def chart_efficiency_ranking(event_df: pd.DataFrame, top_n: int = 20) -> go.Figure:
    """Horizontal bar chart showing market efficiency for the top N games.

    Bars are colour-coded: green = arbitrage, yellow = near arb, blue = normal.
    A dashed vertical line marks the arbitrage threshold at 1.0.
    """
    df = event_df.sort_values("Market Efficiency").head(top_n).copy()

    def bar_color(eff: float) -> str:
        if eff < 1.0:
            return COLORS["arb_green"]
        elif eff < NEAR_ARB_THRESHOLD:
            return COLORS["warning"]
        return COLORS["accent2"]

    colors     = [bar_color(e) for e in df["Market Efficiency"]]
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
            range=[
                max(0.95, df["Market Efficiency"].min() - 0.005),
                df["Market Efficiency"].max() + 0.008,
            ],
        ),
        yaxis=dict(showgrid=False, tickfont_size=10, automargin=True),
        height=max(300, len(df) * 34),
        bargap=0.35,
    )
    return fig


def chart_odds_comparison(event_rows_df: pd.DataFrame, game_name: str) -> go.Figure:
    """Grouped bar chart comparing decimal odds per outcome across bookmakers for a game."""
    df = event_rows_df[["Bet On", "Sportsbook", "Decimal Odds"]].dropna()
    outcomes     = df["Bet On"].unique()
    colors_list  = [COLORS["accent"], COLORS["accent2"], COLORS["warning"], COLORS["danger"]]

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


def chart_stake_pie(event_rows_df: pd.DataFrame, bankroll: float):
    """Donut chart showing optimal stake allocation per outcome for an arbitrage game.

    Returns None (no chart) when there are no suggested stakes — i.e. no arbitrage.
    """
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
    """Gauge / speedometer showing a single game's market efficiency.

    The needle colour mirrors the same green / yellow / blue logic used in badges.
    """
    if efficiency < 1.0:
        gauge_color = COLORS["arb_green"]
        label       = "ARBITRAGE"
    elif efficiency < NEAR_ARB_THRESHOLD:
        gauge_color = COLORS["warning"]
        label       = "NEAR ARB"
    else:
        gauge_color = COLORS["accent2"]
        label       = "NORMAL"

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
                dict(range=[0.96, 1.0],   color="rgba(0,229,160,0.12)"),
                dict(range=[1.0, 1.015],  color="rgba(245,166,35,0.10)"),
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


def chart_roi_scatter(event_df: pd.DataFrame):
    """Scatter plot of market efficiency vs. ROI for all arbitrage-positive games.

    Each point represents one game; position reflects how much profit is available
    relative to how close the market is to true efficiency.
    Returns None if there are no arbitrage games to plot.
    """
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
        title=dict(
            text="Arbitrage Opportunities — Efficiency vs. ROI",
            font_size=13, font_color=COLORS["text_muted"],
        ),
        xaxis=dict(
            showgrid=True, gridcolor=COLORS["border"],
            title="Market Efficiency", title_font_size=10, tickfont_size=10,
        ),
        yaxis=dict(
            showgrid=True, gridcolor=COLORS["border"],
            title="ROI (%)", title_font_size=10, tickfont_size=10,
        ),
        height=320,
    )
    return fig
