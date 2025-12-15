"""Pattern management page with labeling and library management tabs."""

import streamlit as st
from components.tab_label_patterns import render_label_patterns_tab
from components.tab_view_library import render_view_library_tab
from components.tab_train_model import render_train_model_tab

st.title("Pattern Manager")

tab1, tab2, tab3 = st.tabs(["Label Patterns", "View Library", "Train & Validate"])

with tab1:
    render_label_patterns_tab()

with tab2:
    render_view_library_tab()

with tab3:
    render_train_model_tab()
