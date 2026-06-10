"""AI Profitability Simulator — Streamlit entry point."""

import streamlit as st

st.set_page_config(
    page_title="AI Profitability Simulator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
[data-testid="stMetricValue"] { font-size: 1.5rem; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { font-size: 0.8rem; line-height: 1.4; color: #999; }
.kpi-card { padding: 12px; border-radius: 8px; margin-bottom: 8px; }
.kpi-card.green { border-left: 4px solid #2ecc71; }
.kpi-card.red { border-left: 4px solid #e74c3c; }
</style>
""",
    unsafe_allow_html=True,
)

pg = st.navigation(
    [
        st.Page("pages/1_Simulator.py", title="Simulator", icon="📊"),
        st.Page("pages/2_Sensitivity.py", title="Sensitivity", icon="🎯"),
        st.Page("pages/3_Breakeven.py", title="Breakeven Solver", icon="🔍"),
        st.Page("pages/4_Methodology.py", title="Methodology", icon="📚"),
    ]
)

pg.run()
