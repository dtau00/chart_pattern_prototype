"""View and manage pattern library."""

import streamlit as st
import plotly.graph_objects as go
from pathlib import Path
import yaml

from engine.preprocessor import Preprocessor
from engine.pattern_library import PatternLibrary
from engine.dtw_core import DTWCalculator


def render_view_library_tab():
    """Render the library viewer interface."""
    st.header("Pattern Library")

    # Initialize if needed
    if 'pattern_library' not in st.session_state:
        _initialize_pattern_library()

    library = st.session_state['pattern_library']

    if library.get_template_count() == 0:
        st.info("No patterns in library yet. Use the 'Label Patterns' tab to add patterns.")
        return

    # Library statistics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Patterns", library.get_template_count())

    with col2:
        unique_labels = library.get_all_labels()
        st.metric("Unique Labels", len(unique_labels))

    with col3:
        augmented_count = sum(1 for t in library.templates.values() if t.is_augmented)
        st.metric("Augmented Patterns", augmented_count)

    # Augmentation controls
    st.subheader("Library Management")

    col_aug, col_idx = st.columns(2)

    with col_aug:
        if st.button("Augment Library (Mirror Patterns)", type="secondary"):
            config = st.session_state['config']
            library.augment_library(mirror_patterns=config['augmentation']['mirror_patterns'])
            library.save()
            st.success(f"Library augmented! New total: {library.get_template_count()} patterns")
            st.rerun()

    with col_idx:
        if st.button("Build Index (LB_Keogh)", type="secondary"):
            library.build_index()
            library.save()
            st.success("Index built successfully!")

    # Filter by label
    st.subheader("Browse Patterns")

    selected_label = st.selectbox(
        "Filter by label",
        ["All"] + unique_labels,
        key="library_label_filter"
    )

    # Get templates to display
    if selected_label == "All":
        templates = list(library.templates.values())
    else:
        templates = library.get_templates_by_label(selected_label)

    templates.sort(key=lambda t: t.label)

    # Display patterns
    st.write(f"Showing {len(templates)} pattern(s)")

    for template in templates:
        with st.expander(
            f"{template.label} - {template.symbol} {template.timeframe} "
            f"({template.bars_count} bars) - Quality: {template.quality_score:.2f}"
        ):
            col_info, col_meta = st.columns(2)

            with col_info:
                st.write("**Pattern Info:**")
                st.write(f"- ID: `{template.id[:16]}...`")
                st.write(f"- Label: {template.label}")
                st.write(f"- Bars: {template.bars_count}")
                st.write(f"- Quality: {template.quality_score:.3f}")

            with col_meta:
                st.write("**Metadata:**")
                st.write(f"- Symbol: {template.symbol}")
                st.write(f"- Timeframe: {template.timeframe}")
                st.write(f"- Period: {template.start_time.strftime('%Y-%m-%d')} to {template.end_time.strftime('%Y-%m-%d')}")
                if template.is_augmented:
                    st.write(f"- Augmented: {template.augmentation_type}")

            # Chart
            fig = _create_pattern_chart(template)
            st.plotly_chart(fig, use_container_width=True)

            # Delete button
            if st.button(f"Delete Pattern", key=f"delete_{template.id}"):
                del library.templates[template.id]
                library.save()
                st.success("Pattern deleted!")
                st.rerun()


def _initialize_pattern_library():
    """Initialize pattern library and related components."""
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

    st.session_state['preprocessor'] = preprocessor
    st.session_state['dtw_calculator'] = dtw_calculator
    st.session_state['pattern_library'] = library
    st.session_state['config'] = config


def _create_pattern_chart(template):
    """Create chart showing both raw and normalized patterns."""
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Raw Pattern (OHLC)", "Normalized Pattern (DDTW)"),
        row_heights=[0.6, 0.4]
    )

    # Raw candlestick
    fig.add_trace(
        go.Candlestick(
            x=template.raw_data.index,
            open=template.raw_data['open'],
            high=template.raw_data['high'],
            low=template.raw_data['low'],
            close=template.raw_data['close'],
            name='OHLC'
        ),
        row=1, col=1
    )

    # Normalized pattern
    fig.add_trace(
        go.Scatter(
            y=template.normalized,
            mode='lines',
            name='Normalized',
            line=dict(color='blue')
        ),
        row=2, col=1
    )

    fig.update_layout(
        height=500,
        showlegend=False,
        xaxis_rangeslider_visible=False,
        xaxis2_title="Bar Index",
        yaxis2_title="Normalized Value"
    )

    return fig
