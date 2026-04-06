# app.py — entry point and page router

import streamlit as st

st.set_page_config(
    page_title="NGX Analyser",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

from config import ACCENT, MUTED, CARD_BG, BORDER, TEXT, BG
from views.deep_dive import render as deep_dive_page
from views.market_overview import render as market_overview_page

PAGES = {
    "Market Overview": market_overview_page,
    "Stock Deep Dive": deep_dive_page,
}

PAGE_ICONS = {
    "Market Overview": "🌍",
    "Stock Deep Dive": "📈",
}

# ── Global CSS (sidebar + app shell) ─────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'IBM Plex Mono', monospace !important;
    background: {BG} !important;
}}

/* ── Sidebar shell ── */
section[data-testid="stSidebar"] {{
    background: {CARD_BG} !important;
    border-right: 1px solid {BORDER} !important;
    min-width: 210px !important;
    max-width: 210px !important;
}}

section[data-testid="stSidebar"] > div:first-child {{
    padding: 0 !important;
}}

/* ── Radio widget container ── */
section[data-testid="stSidebar"] div[data-testid="stRadio"] {{
    width: 100%;
}}

section[data-testid="stSidebar"] div[data-testid="stRadio"] > div {{
    gap: 0 !important;
    flex-direction: column !important;
}}

/* ── Each nav item ── */
section[data-testid="stSidebar"] div[data-testid="stRadio"] label {{
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    padding: 11px 20px !important;
    margin: 0 !important;
    cursor: pointer !important;
    border-left: 3px solid transparent !important;
    border-radius: 0 !important;
    color: {MUTED} !important;
    font-size: 12px !important;
    letter-spacing: 0.5px !important;
    transition: color 0.15s ease, background 0.15s ease, border-color 0.15s ease !important;
    width: 100% !important;
}}

section[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {{
    color: {TEXT} !important;
    background: {BORDER}70 !important;
    border-left-color: {BORDER} !important;
}}

/* Hide radio circles */
section[data-testid="stSidebar"] div[data-testid="stRadio"] label > div:first-child {{
    display: none !important;
}}

/* Active nav item */
section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) {{
    color: {ACCENT} !important;
    background: {ACCENT}14 !important;
    border-left-color: {ACCENT} !important;
    font-weight: 500 !important;
}}

/* ── Hide collapse button ── */
button[data-testid="collapsedControl"] {{
    display: none;
}}

/* ── Sidebar scrollbar ── */
section[data-testid="stSidebar"] ::-webkit-scrollbar {{ width: 3px; }}
section[data-testid="stSidebar"] ::-webkit-scrollbar-track {{ background: transparent; }}
section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {{
    background: {BORDER};
    border-radius: 2px;
}}

/* ── Main content padding ── */
.main .block-container {{
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
    max-width: 100% !important;
}}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Branding
    st.markdown(f"""
        <div style='padding:28px 20px 16px 20px'>
            <div style='color:{ACCENT};font-weight:800;font-size:24px;
                        letter-spacing:4px;line-height:1'>NGX</div>
            <div style='color:{MUTED};font-size:8px;letter-spacing:5px;
                        margin-top:3px;font-weight:400'>ANALYSER</div>
        </div>
        <div style='height:1px;background:{BORDER};margin:0 0 8px 0'></div>
        <div style='color:{MUTED};font-size:8px;letter-spacing:2.5px;
                    padding:6px 20px 4px 20px'>NAVIGATION</div>
    """, unsafe_allow_html=True)

    selected = st.radio(
        "nav",
        list(PAGES.keys()),
        format_func=lambda x: f"{PAGE_ICONS[x]}  {x}",
        label_visibility="collapsed",
    )

    # Footer pinned to bottom
    st.markdown(f"""
        <div style='position:fixed;bottom:0;width:209px;
                    border-top:1px solid {BORDER};background:{CARD_BG};
                    padding:14px 20px 16px 20px;'>
            <div style='display:flex;align-items:center;gap:7px;margin-bottom:5px'>
                <div style='width:6px;height:6px;border-radius:50%;
                            background:{ACCENT};box-shadow:0 0 6px {ACCENT}99'></div>
                <span style='color:{MUTED};font-size:9px;letter-spacing:1.5px'>NGX LIVE</span>
            </div>
            <div style='color:{MUTED};font-size:8px;letter-spacing:2px;opacity:0.6'>
                v1.0 · Nigerian Exchange
            </div>
        </div>
    """, unsafe_allow_html=True)

# ── Render page ───────────────────────────────────────────────────────────────
PAGES[selected]()
