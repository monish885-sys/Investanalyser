"""
PersonaInvest Streamlit Dashboard.
Run: streamlit run src/personainvest/app.py
"""

import sys
from pathlib import Path

# Ensure src is on path so "personainvest" resolves
_src = Path(__file__).resolve().parent.parent  # src/
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

import streamlit as st
import pandas as pd

from personainvest.analysis import run_analysis
from personainvest.config import USE_MOCK_DATA

# Page config (dark theme via config + custom CSS)
st.set_page_config(
    page_title="PersonaInvest",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Dark theme and professional styling
st.markdown("""
<style>
    /* Dark theme base */
    .stApp { background: linear-gradient(180deg, #0e1117 0%, #1a1d24 100%); }
    [data-testid="stHeader"] { background: rgba(0,0,0,0.3); }
    [data-testid="stToolbar"] { background: #0e1117; }
    
    /* Title area */
    .main-title {
        font-family: 'JetBrains Mono', 'SF Mono', monospace;
        font-size: 2.2rem;
        font-weight: 700;
        color: #e0e0e0;
        letter-spacing: -0.02em;
        margin-bottom: 0.25rem;
    }
    .subtitle {
        color: #8892a0;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }
    
    /* Analyse button */
    .stButton > button {
        width: 100%;
        padding: 0.75rem 1.5rem;
        font-size: 1.1rem;
        font-weight: 600;
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
        border: none;
        border-radius: 8px;
        transition: transform 0.15s, box-shadow 0.15s;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.45);
    }
    
    /* Status / expander */
    [data-testid="stExpander"] {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(71, 85, 105, 0.5);
        border-radius: 8px;
    }
    
    /* Tables */
    .dataframe { font-size: 0.9rem; }
    div[data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid rgba(71, 85, 105, 0.4);
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] { color: #93c5fd; }
    [data-testid="stMetricLabel"] { color: #94a3b8; }
</style>
""", unsafe_allow_html=True)


def main():
    st.markdown('<p class="main-title">PersonaInvest</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="subtitle">Multi-Agent Portfolio Consensus · Upstox & HDFC InvestRight · Gemini 1.5 Pro</p>',
        unsafe_allow_html=True,
    )

    # Sidebar: mock toggle and info
    with st.sidebar:
        st.header("Settings")
        use_mock = st.checkbox(
            "Use mock portfolio (no broker API)",
            value=USE_MOCK_DATA,
            help="Enable to test without Upstox/HDFC credentials.",
        )
        st.divider()
        st.caption("Agents: Portfolio Scout → News Sentinel → Earnings Whisperer → Strategist (CIO)")
        st.caption("Data: Upstox v2, HDFC InvestRight, Tavily search")

    # Single prominent CTA
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        analyse_clicked = st.button("Analyse My Portfolio", type="primary", use_container_width=True)

    if not analyse_clicked:
        st.info("Click **Analyse My Portfolio** to fetch your holdings and run consensus analysis.")
        return

    # Run analysis with live status
    progress_messages: list[str] = []

    def stream_cb(msg: str):
        progress_messages.append(msg)

    with st.status("Running consensus analysis...", expanded=True) as status:
        st.write("Loading portfolio (Upstox + HDFC or mock)...")
        state, consensus = run_analysis(use_mock=use_mock, stream_callback=stream_cb)
        for m in progress_messages:
            st.write(m)
        status.update(label="Analysis complete", state="complete")

    # Portfolio snapshot
    if state.holdings:
        st.subheader("Portfolio snapshot")
        hold_df = pd.DataFrame([
            {
                "Ticker": h.ticker,
                "Company": (h.company_name or "—")[:40],
                "Qty": h.quantity,
                "Avg price": round(h.average_price, 2),
                "LTP": round(h.last_price, 2),
                "P&L (₹)": round(h.pnl, 2),
                "P&L %": round(h.pnl_percent, 2),
                "Source": h.source,
            }
            for h in state.holdings
        ])
        st.dataframe(hold_df, use_container_width=True, hide_index=True)
        st.metric("Total value (₹)", f"{state.total_value:,.2f}", state.as_of_text)

    # Results table: Ticker | Action | Persona Feedback | Confidence Score
    st.subheader("Consensus results")
    if consensus.summary:
        st.write(consensus.summary)

    if consensus.ticker_actions:
        table_df = pd.DataFrame([
            {
                "Ticker": r.ticker,
                "Action": r.action,
                "Persona Feedback": r.persona_feedback,
                "Confidence Score": round(r.confidence_score, 2),
            }
            for r in consensus.ticker_actions
        ])
        st.dataframe(table_df, use_container_width=True, hide_index=True)
    else:
        st.warning("No ticker-level actions returned. Check API keys (Gemini, Tavily) and try again.")


if __name__ == "__main__":
    main()
