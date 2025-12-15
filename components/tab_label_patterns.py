"""Pattern labeling tab - interactive chart with pattern annotation."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import yaml

from engine.preprocessor import Preprocessor
from engine.pattern_library import PatternLibrary
from engine.dtw_core import DTWCalculator


def render_label_patterns_tab():
    """Render the pattern labeling interface."""
    st.header("Label Patterns")

    # Initialize session state
    if 'pattern_library' not in st.session_state:
        _initialize_pattern_library()

    # File selection
    data_dir = Path("data/parquet")
    if not data_dir.exists():
        st.warning("No data directory found. Please download data first.")
        return

    parquet_files = list(data_dir.glob("*.parquet"))
    if not parquet_files:
        st.warning("No parquet files found. Please download data first.")
        return

    selected_file = st.selectbox(
        "Select data file",
        parquet_files,
        format_func=lambda x: x.name,
        key="label_file_select"
    )

    # Load data
    df = pd.read_parquet(selected_file)
    df.index = pd.to_datetime(df.index)

    # Extract symbol and timeframe from filename
    filename_parts = selected_file.stem.split('_')
    symbol = filename_parts[0] if len(filename_parts) > 0 else "UNKNOWN"
    timeframe = filename_parts[1] if len(filename_parts) > 1 else "UNKNOWN"

    # Pattern selection controls
    col1, col2, col3 = st.columns(3)

    with col1:
        pattern_length = st.number_input(
            "Pattern Length (bars)",
            min_value=10,
            max_value=200,
            value=st.session_state.get('pattern_length', 50),
            key="pattern_length_input"
        )
        st.session_state['pattern_length'] = pattern_length

    with col2:
        start_index = st.number_input(
            "Start Index",
            min_value=0,
            max_value=max(0, len(df) - pattern_length),
            value=st.session_state.get('start_index', 0),
            key="start_index_input"
        )
        st.session_state['start_index'] = start_index

    with col3:
        pattern_label = st.text_input(
            "Pattern Label",
            value=st.session_state.get('pattern_label', ''),
            placeholder="e.g., head_and_shoulders",
            key="pattern_label_input"
        )
        st.session_state['pattern_label'] = pattern_label

    # Extract pattern
    end_index = min(start_index + pattern_length, len(df))
    pattern_data = df.iloc[start_index:end_index].copy()

    # Display chart
    st.subheader("Pattern Preview")
    fig = _create_candlestick_chart(pattern_data, f"{symbol} - {timeframe}")
    st.plotly_chart(fig, use_container_width=True)

    # Show normalized pattern
    if st.checkbox("Show Normalized Pattern", value=False):
        preprocessor = st.session_state['preprocessor']
        normalized = preprocessor.normalize_pattern(pattern_data)

        fig_norm = go.Figure()
        fig_norm.add_trace(go.Scatter(
            y=normalized,
            mode='lines',
            name='Normalized Pattern'
        ))
        fig_norm.update_layout(
            title="Normalized Pattern (DDTW)",
            xaxis_title="Bar Index",
            yaxis_title="Normalized Value",
            height=300
        )
        st.plotly_chart(fig_norm, use_container_width=True)

    # Save button
    col_save, col_stats = st.columns([1, 2])

    with col_save:
        if st.button("Save Pattern", type="primary", disabled=not pattern_label):
            _save_pattern(pattern_data, pattern_label, symbol, timeframe)

    with col_stats:
        library = st.session_state['pattern_library']
        st.metric("Total Patterns", library.get_template_count())
        if library.get_template_count() > 0:
            st.write(f"Labels: {', '.join(library.get_all_labels())}")


def _initialize_pattern_library():
    """Initialize pattern library and related components."""
    # Load config
    config_path = Path("config/pattern_config.yaml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Initialize components
    preprocessor = Preprocessor(normalization=config['preprocessing']['normalization'])
    dtw_calculator = DTWCalculator(
        variant=config['dtw']['variant'],
        constraint=config['dtw']['constraint'],
        sakoe_chiba_window=config['dtw']['sakoe_chiba_window'],
        amercing_penalty=config['dtw']['amercing_penalty']
    )

    library = PatternLibrary(
        storage_path=Path("data/patterns"),
        preprocessor=preprocessor,
        dtw_calculator=dtw_calculator
    )

    # Try to load existing library
    library.load()

    st.session_state['preprocessor'] = preprocessor
    st.session_state['dtw_calculator'] = dtw_calculator
    st.session_state['pattern_library'] = library
    st.session_state['config'] = config


def _create_candlestick_chart(df: pd.DataFrame, title: str):
    """Create candlestick chart with plotly."""
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='OHLC'
    )])

    fig.update_layout(
        title=title,
        xaxis_title="Time",
        yaxis_title="Price",
        height=500,
        xaxis_rangeslider_visible=False
    )

    return fig


def _save_pattern(pattern_data: pd.DataFrame, label: str, symbol: str, timeframe: str):
    """Save pattern to library."""
    library = st.session_state['pattern_library']

    metadata = {
        'symbol': symbol,
        'timeframe': timeframe,
        'start_time': pattern_data.index[0],
        'end_time': pattern_data.index[-1]
    }

    template = library.add_pattern(label, pattern_data, metadata)
    library.save()

    st.success(f"Pattern '{label}' saved successfully! (ID: {template.id[:8]}...)")
    st.session_state['pattern_label'] = ''
