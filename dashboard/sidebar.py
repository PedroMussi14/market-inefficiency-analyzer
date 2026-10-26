# =============================================================================
# sidebar.py
# Sidebar controls. render_sidebar() draws every control and returns the
# user's choices as a Settings object that the views consume.
# =============================================================================

from dataclasses import dataclass, field

import streamlit as st
import streamlit.components.v1 as components

from analyzer.filters import UNRELIABLE_PATTERNS
from analyzer.providers import Provider, get_provider, list_configured_providers, list_providers

from .config import (
    APP_NAME,
    BET_FROM_OPTIONS,
    BOOK_LINKS,
    DEFAULT_MAX_EFFICIENCY,
    DEFAULT_TOP_N,
    MARKET_OPTIONS,
    PRIORITY_SPORTS,
    REGION_OPTIONS,
)
from .data import load_sports

PAGES = ["Market scanner", "All arbitrage", "+EV bets"]

# The product's mark: the break-even line, with one price dipping under it
BRAND_MARK = (
    '<svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true">'
    '<rect x="2" y="3" width="4" height="7" fill="#8a8c92"/>'
    '<rect x="9" y="5" width="4" height="5" fill="#8a8c92"/>'
    '<rect x="16" y="12" width="4" height="8" fill="#4a8ad6"/>'
    '<rect x="0" y="10.5" width="22" height="1" fill="#ffffff"/>'
    '</svg>'
)


@dataclass(frozen=True)
class Settings:
    """Everything the user chose in the sidebar."""

    page: str
    provider: Provider
    sport_key: str
    market: str
    region: str
    bet_from: str
    bankroll: float
    hide_american_odds: bool
    show_only_arbitrage: bool = False
    max_efficiency: float = DEFAULT_MAX_EFFICIENCY
    top_n: int = DEFAULT_TOP_N
    min_roi: float = 0.0
    excluded_books: frozenset = field(default_factory=frozenset)

    @property
    def provider_name(self) -> str:
        return self.provider.name


def _group(label: str) -> None:
    st.markdown(f'<p class="nav-group">{label}</p>', unsafe_allow_html=True)


def _select_provider() -> Provider:
    configured = list_configured_providers()
    if not configured:
        st.error("No data providers configured. Add at least one API key to `.env`.")
        for p in list_providers():
            st.markdown(f"- **{p.label}**: {p.setup_help()}")
        st.stop()

    provider_label_to_name = {p.label: p.name for p in configured}
    provider_label = st.selectbox(
        "Data provider",
        list(provider_label_to_name.keys()),
        help="Switch between odds sources. Configure additional providers in .env.",
    )
    provider = get_provider(provider_label_to_name[provider_label])
    st.caption(provider.region_hint)

    unconfigured = [p for p in list_providers() if not p.is_configured()]
    if unconfigured:
        with st.expander(f"Other providers ({len(unconfigured)})"):
            for p in unconfigured:
                st.markdown(f"**{p.label}**")
                st.caption(p.setup_help())
    return provider


def _select_sport(provider: Provider) -> str:
    try:
        available_sports = load_sports(provider.name)
    except NotImplementedError as e:
        st.error(f"The {provider.label} adapter is not finished yet. {e}")
        st.stop()
    except Exception as e:
        st.error(f"Couldn't load sports from {provider.label}. {e}")
        st.stop()

    # Prioritised sport list: common sports first, then everything else
    sport_options = (
        [s for s in PRIORITY_SPORTS if s in available_sports]
        + [s for s in available_sports if s not in PRIORITY_SPORTS]
    )
    if not sport_options:
        st.warning(f"{provider.label} returned no active sports right now.")
        st.stop()

    sport_title = st.selectbox("Sport", sport_options)
    return available_sports[sport_title]


def _select_region() -> str:
    region_display = st.multiselect(
        "Sportsbook region",
        list(REGION_OPTIONS.keys()),
        default=["Brasil"],
        help="Brasil = EU+UK books that accept Brazilian users (Bet365, Betfair, Pinnacle, Betsson).",
    )
    if not region_display:
        st.warning("Select at least one region.")
        st.stop()
    # Expand presets (e.g. "Brasil" → "eu,uk") and dedupe so combined selections
    # like "Brasil + Europe" don't double-bill API quota for "eu".
    region_keys = {key for r in region_display for key in REGION_OPTIONS[r].split(",")}
    return ",".join(sorted(region_keys))


def _render_quota(provider: Provider) -> None:
    """API credits as a bar at the true ratio, both ends labelled."""
    quota = provider.get_quota_info()
    if quota["remaining"] is None:
        return
    try:
        remaining = int(quota["remaining"])
        used      = int(quota["used"]) if quota["used"] is not None else None
    except (ValueError, TypeError):
        return

    total = (remaining + used) if used is not None else None
    if not total:
        st.caption(f"API credits left: {remaining:,}")
        return
    share = remaining / total
    st.markdown(
        '<div class="usage">'
        f'<div class="row"><span>API credits left</span><span><b>{remaining:,}</b> of {total:,}</span></div>'
        f'<div class="track"><div class="fill{" low" if share < 0.1 else ""}" '
        f'style="width:{share * 100:.1f}%"></div></div></div>',
        unsafe_allow_html=True,
    )


def render_sidebar() -> Settings:
    """Draw the sidebar and return the user's settings."""
    with st.sidebar:
        st.markdown(
            f'<div class="brand">{BRAND_MARK}<div><div class="brand-name">{APP_NAME}</div>'
            '<div class="brand-scope">Arbitrage and +EV scanner</div></div></div>',
            unsafe_allow_html=True,
        )

        page = st.radio("Page", PAGES, label_visibility="collapsed", key="nav")

        _group("Market")
        provider = _select_provider()
        sport_key = _select_sport(provider)
        market    = MARKET_OPTIONS[st.selectbox("Market type", list(MARKET_OPTIONS.keys()))]
        region    = _select_region()

        # "I bet from": restrict analysis to books accessible from one location,
        # so every arbitrage found can actually be executed without a VPN.
        bet_from_label = st.selectbox(
            "I bet from",
            list(BET_FROM_OPTIONS.keys()),
            index=1,   # "Brasil", matching the default region
            help=("Restricts arbs to books you can access from this location. "
                  "Without this, you'll see 'arbs' that span US + BR books which "
                  "require a VPN to execute."),
        )
        bet_from = BET_FROM_OPTIONS[bet_from_label]

        # Brazilian books only display decimal odds, so hide American odds there.
        hide_american_odds = bet_from == "brazil"

        bankroll = st.number_input("Budget per game ($)", min_value=1.0, value=100.0, step=10.0)

        _group("Filters")
        view_mode           = st.radio("View mode", ["Simple", "Advanced"], horizontal=True)
        show_only_arbitrage = st.checkbox("Show only arbitrage opportunities", value=False)

        advanced = {}
        if view_mode == "Advanced":
            advanced = dict(
                max_efficiency=st.slider(
                    "Max market efficiency", 1.00, 1.10, DEFAULT_MAX_EFFICIENCY, 0.001,
                    help="Lower = better value. Arbitrage < 1.000",
                ),
                top_n=st.slider("Games in the chart", 5, 100, 15, 5),
                min_roi=st.slider(
                    "Min ROI % (arb only)", 0.0, 5.0, 0.0, 0.1,
                    help="Hide arbitrage opportunities below this return threshold.",
                ),
                excluded_books=frozenset(st.multiselect(
                    "Exclude sportsbooks (additional)",
                    sorted(BOOK_LINKS.keys()),
                    default=[],
                    help="Additional books to exclude beyond the always-on unreliable "
                         "filter (1xBet/Unibet variants are already removed).",
                )),
            )

        # Permanent notice: the reliability filter always runs.
        st.caption(
            "Always excluded for unreliable feed prices: "
            f"{', '.join(sorted(p.title() for p in UNRELIABLE_PATTERNS))}."
        )

        _group("Data")
        if st.button("Refresh odds", width="stretch"):
            st.cache_data.clear()
        auto_refresh = st.toggle(
            "Auto-refresh every 60 s", value=False,
            help="Reload the page every 60 seconds to keep odds fresh.",
        )
        if auto_refresh:
            components.html(
                '<script>setTimeout(function(){window.parent.location.reload();},60000);</script>',
                height=0,
            )

        _render_quota(provider)

    return Settings(
        page=page,
        provider=provider,
        sport_key=sport_key,
        market=market,
        region=region,
        bet_from=bet_from,
        bankroll=bankroll,
        hide_american_odds=hide_american_odds,
        show_only_arbitrage=show_only_arbitrage,
        **advanced,
    )
