"""Pattern scanner page for real-time pattern detection."""

import streamlit as st
from components.tab_scan_patterns import render_scan_patterns_tab

st.title("Pattern Scanner")

render_scan_patterns_tab()
