# pages/data_manager_parent.py
import streamlit as st
# Import the functions defined in the components directory
from components.tab_download import render_download_tab
from components.tab_manage_data import render_manage_data_tab

st.title("OHLCV Data Manager")
st.caption("Download and manage historical OHLCV data from HistData.com")

# Create the internal tabs
tab_names = ["Download Data", "Manage Data"]
tab1, tab2 = st.tabs(tab_names)

with tab1:
    # CALL the imported function to render content
    render_download_tab()

with tab2:
    # CALL the imported function to render content
    render_manage_data_tab()
