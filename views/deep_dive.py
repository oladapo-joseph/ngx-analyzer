# pages/deep_dive.py — Stock Deep Dive page (Streamlit)

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from config import ACCENT, RED, YELLOW, MUTED, TEXT, CARD_BG, BORDER, BG
from data.loader import load_stock_list, load_stock_data, filter_by_dates
from analysis.signals import get_signals, STRATEGIES
from analysis.recommender import generate_recommendation
from charts.deep_dive import build_main_chart, build_signal_chart, empty_fig


# ── CSS ───────────────────────────────────────────────────────────────────────
_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'IBM Plex Mono', monospace !important;
}}

/* ── Control bar row ── */
.ctrl-bar {{
    display: flex;
    align-items: flex-end;
    gap: 12px;
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 10px 16px;
    margin-bottom: 12px;
    flex-wrap: wrap;
}}
.ctrl-label {{
    color: {MUTED};
    font-size: 9px;
    letter-spacing: 1.8px;
    margin-bottom: 4px;
}}

/* ── Meta stat cards ── */
.meta-bar {{
    display: flex;
    gap: 8px;
    margin-bottom: 12px;
    flex-wrap: wrap;
}}
.meta-card {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 10px 16px;
    flex: 1;
    min-width: 90px;
}}
.meta-card .mc-label {{
    color: {MUTED};
    font-size: 9px;
    letter-spacing: 1.8px;
    margin-bottom: 4px;
}}
.meta-card .mc-value {{
    color: {TEXT};
    font-size: 16px;
    font-weight: 700;
    letter-spacing: 0.5px;
}}
.meta-card .mc-delta {{
    font-size: 11px;
    font-weight: 600;
    margin-top: 2px;
}}
.mc-up   {{ color: {ACCENT}; }}
.mc-down {{ color: {RED};   }}
.mc-flat {{ color: {MUTED}; }}

/* ── Recommendation box ── */
.reco-box {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 16px 20px;
    line-height: 1.8;
    font-size: 13px;
    min-height: 80px;
}}
.reco-verdict {{
    font-size: 14px;
    font-weight: 700;
    margin-bottom: 6px;
}}

/* ── Section label ── */
.section-label {{
    color: {MUTED};
    font-size: 9px;
    letter-spacing: 2px;
    margin-bottom: 8px;
    margin-top: 4px;
}}

/* Hide default metric styling bleed */
div[data-testid="metric-container"] {{ display: none !important; }}

/* Streamlit button */
div[data-testid="stButton"] > button {{
    background: transparent !important;
    border: 1px solid {ACCENT} !important;
    color: {ACCENT} !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 11px !important;
    border-radius: 4px !important;
    padding: 6px 14px !important;
    width: 100%;
}}
div[data-testid="stButton"] > button:hover {{
    background: {ACCENT}22 !important;
}}
</style>
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _format_naira(n: float) -> str:
    if n >= 1_000_000_000:
        return f"₦{n / 1_000_000_000:.2f}B"
    if n >= 1_000_000:
        return f"₦{n / 1_000_000:.2f}M"
    return f"₦{n:,.2f}"


def _meta_bar(last: pd.Series) -> str:
    chg = float(last.get("Change", 0) or 0)
    pct = (chg / float(last.get("PrevClosingPrice", 1) or 1)) * 100

    sign       = "+" if chg > 0 else ""
    delta_cls  = "mc-up" if chg > 0 else ("mc-down" if chg < 0 else "mc-flat")
    delta_html = (
        f"<div class='mc-delta {delta_cls}'>"
        f"{sign}{chg:.2f} ({sign}{pct:.2f}%)</div>"
    )

    def card(label, value, extra=""):
        return (
            f"<div class='meta-card'>"
            f"  <div class='mc-label'>{label}</div>"
            f"  <div class='mc-value'>{value}</div>"
            f"  {extra}"
            f"</div>"
        )

    cards = "".join([
        card("CLOSE",  f"₦{float(last['ClosePrice']):.2f}", delta_html),
        card("OPEN",   f"₦{float(last.get('OpeningPrice', 0)):.2f}"),
        card("HIGH",   f"<span class='mc-up'>₦{float(last.get('HighPrice', 0)):.2f}</span>"),
        card("LOW",    f"<span class='mc-down'>₦{float(last.get('LowPrice', 0)):.2f}</span>"),
        card("VOLUME", f"{int(last.get('Volume', 0)):,}"),
        card("VALUE",  _format_naira(float(last.get("Value", 0)))),
        card("TRADES", f"{int(last.get('Trades', 0)):,}" if "Trades" in last.index else "—"),
    ])
    return f"<div class='meta-bar'>{cards}</div>"


def _reco_html(text: str) -> str:
    verdict_colors = {"BUY": ACCENT, "SELL": RED, "HOLD": YELLOW}
    verdict_html = ""
    body = text

    for v, c in verdict_colors.items():
        tag = f"Recommendation: {v}"
        if tag in text:
            verdict_html = (
                f"<div class='reco-verdict' style='color:{c}'>▶ {v}</div>"
            )
            body = text.replace(tag, "").strip()
            # Clean up "Reason:" prefix styling
            body = body.replace("Reason:", f"<span style='color:{MUTED}'>REASON —</span>")
            break

    return f"<div class='reco-box'>{verdict_html}{body}</div>"


# ── Render ────────────────────────────────────────────────────────────────────

def render():
    st.markdown(_CSS, unsafe_allow_html=True)

    symbols = load_stock_list()
    today   = datetime.today().date()

    # ── Control bar (inline, above chart) ────────────────────────────────────
    c1, c2, c3, c4, c5, c6 = st.columns([2, 1.4, 1.2, 2, 2, 1.8])

    with c1:
        symbol = st.selectbox(
            "STOCK", options=symbols,
            index=None, placeholder="Select symbol…",
            label_visibility="visible",
        )
    with c2:
        quick = st.radio(
            "RANGE", ["1M", "3M", "6M", "1Y", "ALL"],
            horizontal=True, index=1,
        )
    with c3:
        chart_type = st.radio(
            "TYPE", ["Candle", "Line"],
            horizontal=True, index=0,
        )
        chart_type = "candle" if chart_type == "Candle" else "line"
    with c4:
        overlays = st.multiselect(
            "OVERLAYS",
            ["SMA_50", "SMA_200", "EMA_12", "EMA_26"],
            default=[],
            format_func=lambda x: x.replace("_", " "),
        )
    with c5:
        panels = st.multiselect(
            "PANELS", ["volume", "macd", "rsi"],
            default=["volume", "macd", "rsi"],
            format_func=str.upper,
        )
    with c6:
        strategy = st.selectbox(
            "STRATEGY", list(STRATEGIES.keys()),
            index=0,
        )

    # Resolve date range
    quick_map = {"1M": 30, "3M": 90, "6M": 180, "1Y": 365}
    if quick == "ALL":
        start_date, end_date = None, None
    else:
        end_date   = today
        start_date = today - timedelta(days=quick_map[quick])

    # ── Guard: no stock selected ──────────────────────────────────────────────
    if not symbol:
        st.plotly_chart(
            empty_fig("↑ Select a stock to begin"),
            use_container_width=True,
        )
        return

    # ── Load & filter data ────────────────────────────────────────────────────
    with st.spinner(""):
        price_df, full_df = load_stock_data(symbol)

    price_df = filter_by_dates(price_df, start_date, end_date)
    full_df  = filter_by_dates(full_df,  start_date, end_date)

    if price_df.empty:
        st.warning("No data for selected range.")
        return

    # ── Meta bar ──────────────────────────────────────────────────────────────
    st.markdown(_meta_bar(full_df.iloc[-1]), unsafe_allow_html=True)

    # ── Main chart ────────────────────────────────────────────────────────────
    fig = build_main_chart(
        price_df=price_df,
        full_df=full_df,
        overlays=overlays,
        panels=panels,
        chart_type=chart_type,
        symbol=symbol,
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Signals + Recommendation ──────────────────────────────────────────────
    buy_df, sell_df = get_signals(strategy, price_df)

    sig_col, reco_col = st.columns([1, 1], gap="large")

    with sig_col:
        st.markdown("<div class='section-label'>SIGNAL SUMMARY</div>",
                    unsafe_allow_html=True)

        # Signal count cards
        b_color = ACCENT if len(buy_df) else MUTED
        s_color = RED    if len(sell_df) else MUTED
        st.markdown(
            f"<div class='meta-bar'>"
            f"  <div class='meta-card'>"
            f"    <div class='mc-label'>BUY SIGNALS</div>"
            f"    <div class='mc-value' style='color:{b_color}'>{len(buy_df)}</div>"
            f"  </div>"
            f"  <div class='meta-card'>"
            f"    <div class='mc-label'>SELL SIGNALS</div>"
            f"    <div class='mc-value' style='color:{s_color}'>{len(sell_df)}</div>"
            f"  </div>"
            f"  <div class='meta-card'>"
            f"    <div class='mc-label'>STRATEGY</div>"
            f"    <div class='mc-value' style='font-size:12px'>{strategy}</div>"
            f"  </div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        if not buy_df.empty or not sell_df.empty:
            st.plotly_chart(
                build_signal_chart(price_df, buy_df, sell_df, symbol),
                use_container_width=True,
            )
        else:
            st.info("No signals fired in this range.")

    with reco_col:
        st.markdown("<div class='section-label'>💡 RECOMMENDATION</div>",
                    unsafe_allow_html=True)

        if st.button("Generate / Refresh"):
            if buy_df.empty and sell_df.empty:
                st.warning("No signals to analyse.")
            else:
                with st.spinner("Consulting Claude…"):
                    try:
                        reco = generate_recommendation(
                            buy_signal=buy_df.to_dict(),
                            sell_signal=sell_df.to_dict(),
                            stock_details={"Stock Name": symbol,
                                           "Strategy": strategy},
                        )
                        st.session_state[f"reco_{symbol}"] = reco
                    except Exception as e:
                        st.error(f"Claude error: {e}")

        reco_text = st.session_state.get(f"reco_{symbol}", "")
        if reco_text:
            st.markdown(_reco_html(reco_text), unsafe_allow_html=True)
        else:
            st.markdown(
                f"<div class='reco-box' style='color:{MUTED}'>"
                f"Click Generate to get an AI recommendation.</div>",
                unsafe_allow_html=True,
            )

    # ── Raw data ──────────────────────────────────────────────────────────────
    with st.expander("📋 Raw Data"):
        rawdf = full_df.copy()
        rawdf.sort_index(inplace=True, ascending=False)
        float_cols = rawdf.select_dtypes("float").columns
        st.dataframe(
            rawdf.style.format({c: "{:.2f}" for c in float_cols}),
            use_container_width=True,
        )
