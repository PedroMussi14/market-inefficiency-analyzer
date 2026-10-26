# =============================================================================
# charts.py
# Plotly figures used by the dashboard. Every chart shares PLOTLY_LAYOUT and
# the COLORS palette so the visuals read as one system.
# =============================================================================

import math

import pandas as pd
import plotly.graph_objects as go

from .components import short_game
from .theme import COLORS, FONT_NUM, PLOTLY_LAYOUT


def _nice_step(span: float) -> float:
    """A round tick step (0.5, 1, 2, 2.5, 5 × 10ⁿ) giving about four ticks over `span`."""
    raw = span / 4
    magnitude = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * magnitude:
            return m * magnitude
    return 10 * magnitude


def locked_in_return(implied_sum):
    """Return (%) from backing every outcome at the best prices, staked to pay the same.

    1 / implied_sum − 1: positive is a guaranteed profit (the arbitrage ROI),
    negative is the margin the bookmakers keep.
    """
    return (1 / implied_sum - 1) * 100


def chart_break_even(event_df: pd.DataFrame, top_n: int = 12, selected: str | None = None) -> go.Figure:
    """Each game's locked-in return, as one bar per game around the break-even line.

    Right of the line the best prices guarantee a profit (arbitrage) and the
    bar is drawn in the accent; left of it is the bookmakers' remaining
    margin, in grey. The game shown in the focus card is labelled in white.
    """
    df = event_df.sort_values("Market Efficiency").head(top_n).copy()
    df["margin"] = locked_in_return(df["Market Efficiency"])
    df = df.iloc[::-1]   # best at the top

    colors = [COLORS["accent"] if m > 0 else COLORS["faint"] for m in df["margin"]]
    # Short labels can collide ("United vs City" twice); zero-width spaces keep them distinct
    labels, seen = [], {}
    for g in df["Game"]:
        label = short_game(g)
        seen[label] = seen.get(label, -1) + 1
        labels.append(label + "​" * seen[label])
    text = [f"{'+' if m > 0 else '−' if m < 0 else ''}{abs(m):.2f}%" for m in df["margin"]]

    lo, hi = min(df["margin"].min(), 0), max(df["margin"].max(), 0)
    span = max(hi - lo, 0.5)
    # Room beside each bar's end for its value label, then round ticks inside the range
    x0, x1 = lo - span * 0.08, hi + span * 0.4
    step = _nice_step(span)
    ticks = [t * step for t in range(math.ceil(x0 / step), math.floor(x1 / step) + 1)]

    fig = go.Figure(go.Bar(
        x=df["margin"],
        y=labels,
        orientation="h",
        marker=dict(color=colors, line_width=0),
        text=text,
        # A profit reads beside its bar; a loss sits inside its (longer) bar, clear of the names
        textposition=["outside" if m > 0 else "inside" for m in df["margin"]],
        insidetextanchor="start",
        cliponaxis=False,
        textfont=dict(family=FONT_NUM, size=12, color=COLORS["text"]),
        customdata=df[["Game", "Market Efficiency"]],
        hovertemplate="%{customdata[0]}<br>Implied sum %{customdata[1]:.4f}<extra></extra>",
    ))

    fig.add_vline(x=0, line_width=1, line_color=COLORS["text"])
    fig.add_annotation(
        x=0, y=1, yref="paper", yanchor="bottom", showarrow=False,
        text="Break-even", font=dict(size=12, color=COLORS["muted"]), xanchor="left", xshift=4,
    )

    selected_labels = {lbl for lbl, g in zip(labels, df["Game"], strict=True) if g == selected}
    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis=dict(
            range=[x0, x1], tickvals=ticks,
            ticktext=[f"{'+' if t > 0 else '−' if t < 0 else ''}{abs(t):g}%" for t in ticks],
            showgrid=True, gridcolor=COLORS["grid"], gridwidth=1, zeroline=False,
            showline=False, tickfont=dict(size=12, color=COLORS["muted"]), fixedrange=True,
        ),
        yaxis=dict(
            showgrid=False, automargin=True, fixedrange=True, ticklabelstandoff=10,
            tickfont=dict(size=12, color=COLORS["muted"]),
            tickmode="array", tickvals=labels,
            ticktext=[f"<b style='color:#fff'>{lbl}</b>" if lbl in selected_labels else lbl for lbl in labels],
        ),
        height=max(240, len(df) * 36 + 56),
        bargap=0.36,
        uniformtext=dict(minsize=12, mode="show"),
    )
    fig.update_layout(margin=dict(l=8, r=8, t=28, b=8))
    return fig
