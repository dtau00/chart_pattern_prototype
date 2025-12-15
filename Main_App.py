# Main_App.py
import streamlit as st

st.set_page_config(
    page_title="OHLCV Analysis Platform",
    layout="wide",
    page_icon=":material/candlestick_chart:",
)

# Define all top-level pages
app_pages = [
    # Analysis dashboard with internal tabs
    st.Page("pages/analysis_parent.py",
            title="Analysis Dashboard",
            icon=":material/analytics:"),

    # Data Manager for downloading and managing OHLCV data
    st.Page("pages/data_manager_parent.py",
            title="Data Manager",
            icon=":material/download:"),

    # Pattern Manager for labeling and managing patterns
    st.Page("pages/pattern_manager_parent.py",
            title="Pattern Manager",
            icon=":material/pattern:"),

    # Pattern Scanner for real-time pattern detection
    st.Page("pages/pattern_scanner_parent.py",
            title="Pattern Scanner",
            icon=":material/search:"),
]

# Create and run the navigation menu
pg = st.navigation(app_pages)
pg.run()
