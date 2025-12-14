# pages/analysis_parent.py
import streamlit as st
# Import the functions defined in the components directory
from components.tab_overview import render_overview_tab
from components.tab_metrics import render_metrics_tab


st.title("Main Analysis View")

# Create the internal tabs
tab_names = ["Overview Summary", "Detailed Metrics"]
tab1, tab2 = st.tabs(tab_names)

with tab1:
    # CALL the imported function to render content
    render_overview_tab()

with tab2:
    # CALL the imported function to render content
    render_metrics_tab()
