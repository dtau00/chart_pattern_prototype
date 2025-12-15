"""Pattern scanning tab - real-time pattern detection."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import yaml

from engine.preprocessor import Preprocessor
from engine.pattern_library import PatternLibrary
from engine.dtw_core import DTWCalculator
from engine.pattern_matcher import PatternMatcher
from engine.confidence import ConfidenceScorer
from engine.backtester import Backtester


def render_scan_patterns_tab():
    """Render the pattern scanning interface."""
    st.header("Pattern Scanner")

    # Initialize if needed
    if 'backtester' not in st.session_state:
        _initialize_components()

    library = st.session_state['pattern_library']

    if library.get_template_count() == 0:
        st.warning("No patterns in library. Please label some patterns first.")
        return

    if library.index_dirty:
        st.info("Index not built. Building index for faster scanning...")
        library.build_index()
        library.save()

    # Scanner configuration
    st.subheader("Scanner Configuration")

    col1, col2, col3 = st.columns(3)

    with col1:
        # File selection
        data_dir = Path("data/parquet")
        if not data_dir.exists():
            st.error("No data directory found.")
            return

        parquet_files = list(data_dir.glob("*.parquet"))
        if not parquet_files:
            st.error("No parquet files found.")
            return

        selected_file = st.selectbox(
            "Select data file",
            parquet_files,
            format_func=lambda x: x.name,
            index=st.session_state.get('scanner_file_index', 0),
            key="scanner_file_select_widget"
        )
        # Save file index for persistence
        if selected_file in parquet_files:
            st.session_state['scanner_file_index'] = parquet_files.index(selected_file)

    with col2:
        window_size = st.number_input(
            "Pattern Window Size (bars)",
            min_value=10,
            max_value=200,
            value=st.session_state.get('scanner_window_size', 50),
            key="scanner_window_size_widget"
        )
        st.session_state['scanner_window_size'] = window_size

    with col3:
        min_confidence = st.slider(
            "Minimum Confidence",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.get('scanner_min_confidence', 0.7),
            step=0.05,
            key="scanner_min_confidence_widget"
        )
        st.session_state['scanner_min_confidence'] = min_confidence

    # Advanced options
    with st.expander("Advanced Options"):
        col_adv1, col_adv2 = st.columns(2)

        with col_adv1:
            step_size = st.number_input(
                "Step Size (bars)",
                min_value=1,
                max_value=50,
                value=st.session_state.get('scanner_step_size', 5),
                help="Number of bars to skip between scans. Lower = more thorough but slower.",
                key="scanner_step_size_widget"
            )
            st.session_state['scanner_step_size'] = step_size

        with col_adv2:
            filter_labels = st.multiselect(
                "Filter by Pattern Labels",
                options=library.get_all_labels(),
                default=st.session_state.get('scanner_filter_labels', []),
                help="Only show specific pattern types (empty = show all)",
                key="scanner_filter_labels_widget"
            )
            st.session_state['scanner_filter_labels'] = filter_labels

    # Scan button
    if st.button("🔍 Scan for Patterns", type="primary"):
        with st.spinner("Scanning for patterns..."):
            # Load data
            df = pd.read_parquet(selected_file)
            df.index = pd.to_datetime(df.index)

            # Extract symbol and timeframe
            filename_parts = selected_file.stem.split('_')
            symbol = filename_parts[0] if len(filename_parts) > 0 else "UNKNOWN"
            timeframe = filename_parts[1] if len(filename_parts) > 1 else "UNKNOWN"

            # Run backtest
            backtester = st.session_state['backtester']
            detections = backtester.backtest_on_data(
                ohlc_data=df,
                window_size=window_size,
                step=step_size,
                min_confidence=min_confidence
            )

            # Filter by labels if specified
            if filter_labels:
                detections = [d for d in detections if d['label'] in filter_labels]

            # Store in session state
            st.session_state['scan_detections'] = detections
            st.session_state['scan_symbol'] = symbol
            st.session_state['scan_timeframe'] = timeframe
            st.session_state['scan_data'] = df

            st.success(f"Scan complete! Found {len(detections)} pattern(s).")

    # Display results
    if 'scan_detections' in st.session_state:
        detections = st.session_state['scan_detections']
        symbol = st.session_state['scan_symbol']
        timeframe = st.session_state['scan_timeframe']
        df = st.session_state['scan_data']

        if not detections:
            st.info("No patterns detected at this confidence level. Try lowering the threshold.")
            return

        st.subheader(f"Detected Patterns ({len(detections)})")

        # Summary statistics
        col_s1, col_s2, col_s3 = st.columns(3)

        with col_s1:
            unique_patterns = len(set(d['label'] for d in detections))
            st.metric("Unique Patterns", unique_patterns)

        with col_s2:
            avg_confidence = sum(d['confidence'] for d in detections) / len(detections)
            st.metric("Avg Confidence", f"{avg_confidence:.2%}")

        with col_s3:
            max_confidence = max(d['confidence'] for d in detections)
            st.metric("Max Confidence", f"{max_confidence:.2%}")

        # Pattern distribution
        pattern_counts = {}
        for d in detections:
            pattern_counts[d['label']] = pattern_counts.get(d['label'], 0) + 1

        st.write("**Pattern Distribution:**")
        for label, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
            st.write(f"- {label}: {count}")

        # Display each detection
        st.subheader("Detection Details")

        for i, detection in enumerate(detections):
            with st.expander(
                f"#{i+1}: {detection['label']} - "
                f"Confidence: {detection['confidence']:.2%} - "
                f"{detection['start_time'].strftime('%Y-%m-%d %H:%M')}"
            ):
                col_det1, col_det2 = st.columns(2)

                with col_det1:
                    st.write("**Detection Info:**")
                    st.write(f"- Pattern: {detection['label']}")
                    st.write(f"- Confidence: {detection['confidence']:.2%}")
                    st.write(f"- Start: {detection['start_time'].strftime('%Y-%m-%d %H:%M')}")
                    st.write(f"- End: {detection['end_time'].strftime('%Y-%m-%d %H:%M')}")
                    st.write(f"- Bars: {detection['end_index'] - detection['start_index']}")

                with col_det2:
                    st.write("**Price Action:**")
                    window_data = detection['window_data']
                    price_change = (
                        (window_data['close'].iloc[-1] - window_data['close'].iloc[0])
                        / window_data['close'].iloc[0]
                    )
                    st.write(f"- Start Price: {window_data['close'].iloc[0]:.5f}")
                    st.write(f"- End Price: {window_data['close'].iloc[-1]:.5f}")
                    st.write(f"- Change: {price_change:.2%}")
                    st.write(f"- High: {window_data['high'].max():.5f}")
                    st.write(f"- Low: {window_data['low'].min():.5f}")

                # Chart
                fig = _create_detection_chart(
                    detection,
                    df,
                    symbol,
                    timeframe
                )
                st.plotly_chart(fig, use_container_width=True)


def _create_detection_chart(detection, full_data, symbol, timeframe):
    """Create chart showing detected pattern in context."""
    # Get detection window
    start_idx = detection['start_index']
    end_idx = detection['end_index']

    # Get context (20 bars before and after)
    context_start = max(0, start_idx - 20)
    context_end = min(len(full_data), end_idx + 20)

    context_data = full_data.iloc[context_start:context_end]
    pattern_data = detection['window_data']

    # Create figure
    fig = go.Figure()

    # Context candlesticks (gray)
    fig.add_trace(go.Candlestick(
        x=context_data.index,
        open=context_data['open'],
        high=context_data['high'],
        low=context_data['low'],
        close=context_data['close'],
        name='Context',
        increasing_line_color='lightgray',
        decreasing_line_color='darkgray',
        opacity=0.5
    ))

    # Pattern candlesticks (highlighted)
    fig.add_trace(go.Candlestick(
        x=pattern_data.index,
        open=pattern_data['open'],
        high=pattern_data['high'],
        low=pattern_data['low'],
        close=pattern_data['close'],
        name='Detected Pattern',
        increasing_line_color='green',
        decreasing_line_color='red'
    ))

    # Add vertical lines to mark pattern boundaries
    y_min = context_data['low'].min()
    y_max = context_data['high'].max()

    fig.add_shape(
        type="line",
        x0=pattern_data.index[0],
        y0=y_min,
        x1=pattern_data.index[0],
        y1=y_max,
        line=dict(color="blue", width=2, dash="dash")
    )

    fig.add_shape(
        type="line",
        x0=pattern_data.index[-1],
        y0=y_min,
        x1=pattern_data.index[-1],
        y1=y_max,
        line=dict(color="blue", width=2, dash="dash")
    )

    fig.update_layout(
        title=f"{symbol} - {timeframe} | {detection['label']} (Confidence: {detection['confidence']:.2%})",
        xaxis_title="Time",
        yaxis_title="Price",
        height=500,
        xaxis_rangeslider_visible=False,
        showlegend=False
    )

    return fig


def _initialize_components():
    """Initialize components if not already done."""
    config_path = Path("config/pattern_config.yaml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

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

    library.load()

    confidence_scorer = ConfidenceScorer(
        closeness_weight=config['confidence']['weights']['closeness'],
        consensus_weight=config['confidence']['weights']['consensus'],
        separation_weight=config['confidence']['weights']['separation'],
        quality_weight=config['confidence']['weights']['quality']
    )

    matcher = PatternMatcher(
        library=library,
        dtw_calculator=dtw_calculator,
        confidence_scorer=confidence_scorer,
        k=config['knn']['k']
    )

    backtester = Backtester(library=library, matcher=matcher)

    st.session_state['preprocessor'] = preprocessor
    st.session_state['dtw_calculator'] = dtw_calculator
    st.session_state['pattern_library'] = library
    st.session_state['config'] = config
    st.session_state['confidence_scorer'] = confidence_scorer
    st.session_state['matcher'] = matcher
    st.session_state['backtester'] = backtester
