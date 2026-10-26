# =============================================================================
# charts.py
# The market strip: every game as one dot on a single axis of "return from
# backing every outcome", around the break-even line. Drawn as inline SVG
# so it shares the page's type and colours exactly.
# =============================================================================

import math
from html import escape

import pandas as pd

from .components import locked_in_return, short_game
from .theme import COLORS

W, H = 800, 156          # viewBox; the SVG scales to its card's width
PAD_X = 28
AXIS_Y = 86


def _nice_step(span: float) -> float:
    """A round tick step (1, 2, 2.5, 5 × 10ⁿ) giving about five ticks over `span`."""
    raw = span / 5
    magnitude = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * magnitude:
            return m * magnitude
    return 10 * magnitude


def _signed(v: float, digits: int = 2) -> str:
    return f"{'+' if v > 0 else '−' if v < 0 else ''}{abs(v):.{digits}f}%"


def market_strip_svg(event_df: pd.DataFrame, selected: str | None = None) -> str:
    """One dot per game; right of break-even (shaded) is a guaranteed profit.

    Dots that would overlap are stacked above and below the axis. The selected
    game is drawn larger and labelled; every dot names its game on hover.
    """
    df = event_df.copy()
    df["ret"] = locked_in_return(df["Market Efficiency"])
    lo, hi = min(df["ret"].min(), 0.0), max(df["ret"].max(), 0.0)
    span = max(hi - lo, 1.0)
    lo, hi = lo - span * 0.08, hi + span * 0.12
    step = _nice_step(hi - lo)

    def x(v: float) -> float:
        return PAD_X + (v - lo) / (hi - lo) * (W - 2 * PAD_X)

    x0 = x(0)
    parts = [
        # The profit zone, its label, and the break-even line
        f'<rect x="{x0:.1f}" y="18" width="{W - PAD_X - x0:.1f}" height="{AXIS_Y + 28 - 18}" '
        f'rx="10" fill="#dcfae5" opacity=".55"/>',
        f'<text x="{x0 + 10:.1f}" y="36" font-size="12" font-weight="600" fill="{COLORS["positive"]}">'
        'Guaranteed profit</text>',
        f'<text x="{x0 - 10:.1f}" y="36" font-size="12" text-anchor="end" fill="{COLORS["muted"]}">'
        'Bookmakers keep a margin</text>',
        f'<line x1="{PAD_X}" x2="{W - PAD_X}" y1="{AXIS_Y}" y2="{AXIS_Y}" '
        f'stroke="{COLORS["border"]}" stroke-width="2"/>',
        f'<line x1="{x0:.1f}" x2="{x0:.1f}" y1="18" y2="{AXIS_Y + 28}" stroke="{COLORS["text"]}" '
        'stroke-width="1"/>',
    ]

    # Ticks below the axis, on round steps
    t = math.ceil(lo / step) * step
    while t <= hi + 1e-9:
        parts.append(f'<text x="{x(t):.1f}" y="{AXIS_Y + 50}" font-size="11" text-anchor="middle" '
                     f'fill="{COLORS["muted"]}">{_signed(t, 0 if step >= 1 else 1)}</text>')
        t += step

    # Dots, nudged off the axis when they would sit on top of each other
    placed: list = []
    sel_dot = None
    for _, r in df.sort_values("ret").iterrows():
        cx = x(r["ret"])
        near = sum(1 for px in placed if abs(px - cx) < 15)
        placed.append(cx)
        cy = AXIS_Y + (0 if near == 0 else (-14 if near % 2 else 14) * ((near + 1) // 2))
        arb = r["ret"] > 0
        fill = COLORS["accent"] if arb else COLORS["faint"]
        title = f'<title>{escape(r["Game"])}: {_signed(r["ret"])}</title>'
        if r["Game"] == selected:
            sel_dot = (cx, cy, r)
            continue
        parts.append(f'<circle cx="{cx:.1f}" cy="{cy}" r="7" fill="{fill}">{title}</circle>')

    if sel_dot:
        cx, cy, r = sel_dot
        fill = COLORS["accent"] if r["ret"] > 0 else "#8a9099"
        label = f'{short_game(r["Game"])}  {_signed(r["ret"])}'
        anchor = "end" if cx > W * 0.7 else "start" if cx < W * 0.3 else "middle"
        parts.append(f'<circle cx="{cx:.1f}" cy="{cy}" r="16" fill="{fill}" opacity=".18"/>')
        parts.append(f'<circle cx="{cx:.1f}" cy="{cy}" r="9" fill="{fill}" stroke="#fff" stroke-width="3">'
                     f'<title>{escape(r["Game"])}</title></circle>')
        parts.append(f'<text x="{cx:.1f}" y="{AXIS_Y - 24 if cy >= AXIS_Y else AXIS_Y + 30}" font-size="12" '
                     f'font-weight="600" text-anchor="{anchor}" fill="{COLORS["text"]}">{escape(label)}</text>')

    return (f'<div class="strip"><svg viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="Return from backing every outcome, one dot per game">{"".join(parts)}</svg></div>')
