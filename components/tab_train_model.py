"""Model training and validation tab."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import yaml
import numpy as np

from engine.preprocessor import Preprocessor
from engine.pattern_library import PatternLibrary
from engine.dtw_core import DTWCalculator
from engine.pattern_matcher import PatternMatcher
from engine.confidence import ConfidenceScorer
from engine.backtester import Backtester


def render_train_model_tab():
    """Render the training and validation interface."""
    st.header("Model Training & Validation")

    # Initialize if needed
    if 'backtester' not in st.session_state:
        _initialize_components()

    library = st.session_state['pattern_library']

    if library.get_template_count() == 0:
        st.warning("No patterns in library. Please label some patterns first.")
        return

    # Display library stats
    st.subheader("Library Statistics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Patterns", library.get_template_count())

    with col2:
        unique_labels = library.get_all_labels()
        st.metric("Unique Labels", len(unique_labels))

    with col3:
        original_count = sum(1 for t in library.templates.values() if not t.is_augmented)
        st.metric("Original Patterns", original_count)

    with col4:
        augmented_count = sum(1 for t in library.templates.values() if t.is_augmented)
        st.metric("Augmented Patterns", augmented_count)

    # Show pattern distribution
    if unique_labels:
        st.subheader("Pattern Distribution")
        label_counts = {}
        for label in unique_labels:
            label_counts[label] = len(library.get_templates_by_label(label))

        fig = px.bar(
            x=list(label_counts.keys()),
            y=list(label_counts.values()),
            labels={'x': 'Pattern Label', 'y': 'Count'},
            title='Patterns per Label'
        )
        st.plotly_chart(fig, use_container_width=True)

    # Cross-validation section
    st.subheader("Cross-Validation")

    col_cv1, col_cv2 = st.columns(2)

    with col_cv1:
        min_confidence = st.slider(
            "Minimum Confidence",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.05,
            key="cv_min_confidence"
        )

    with col_cv2:
        exclude_augmented = st.checkbox(
            "Exclude Augmented Patterns",
            value=True,
            help="Only use original patterns for validation",
            key="cv_exclude_augmented"
        )

    if st.button("Run Cross-Validation", type="primary"):
        with st.spinner("Running cross-validation..."):
            backtester = st.session_state['backtester']
            results = backtester.cross_validate(
                min_confidence=min_confidence,
                exclude_augmented=exclude_augmented
            )

            if 'error' in results:
                st.error(results['error'])
            else:
                st.success(f"Cross-validation complete! ({results['cv_strategy']})")

                # Display metrics
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)

                with col_m1:
                    st.metric("Accuracy", f"{results['accuracy']:.2%}")

                with col_m2:
                    st.metric("Precision", f"{results['macro_precision']:.2%}")

                with col_m3:
                    st.metric("Recall", f"{results['macro_recall']:.2%}")

                with col_m4:
                    st.metric("F1 Score", f"{results['macro_f1']:.2%}")

                # Additional metrics
                st.write("**Additional Metrics:**")
                col_a1, col_a2, col_a3 = st.columns(3)

                with col_a1:
                    st.metric("Matched Rate", f"{results['matched_rate']:.2%}")

                with col_a2:
                    st.metric("Avg Confidence", f"{results['avg_confidence']:.2%}")

                with col_a3:
                    st.metric("Total Samples", results['total_samples'])

                # Store results in session state
                st.session_state['cv_results'] = results

    # Confusion matrix
    st.subheader("Confusion Matrix")

    if st.button("Generate Confusion Matrix"):
        with st.spinner("Generating confusion matrix..."):
            backtester = st.session_state['backtester']
            cm, labels = backtester.get_confusion_matrix(
                min_confidence=min_confidence,
                exclude_augmented=exclude_augmented
            )

            # Display confusion matrix as heatmap
            fig = go.Figure(data=go.Heatmap(
                z=cm,
                x=labels,
                y=labels,
                colorscale='Blues',
                text=cm,
                texttemplate='%{text}',
                textfont={"size": 12}
            ))

            fig.update_layout(
                title='Confusion Matrix',
                xaxis_title='Predicted Label',
                yaxis_title='True Label',
                height=500
            )

            st.plotly_chart(fig, use_container_width=True)

    # Threshold tuning
    st.subheader("Confidence Threshold Tuning")

    if st.button("Test Multiple Thresholds"):
        with st.spinner("Testing confidence thresholds..."):
            backtester = st.session_state['backtester']
            threshold_results = backtester.test_confidence_thresholds(
                thresholds=[0.5, 0.6, 0.7, 0.8, 0.9],
                exclude_augmented=exclude_augmented
            )

            if not threshold_results.empty:
                st.write("**Metrics by Threshold:**")
                st.dataframe(threshold_results.style.format({
                    'threshold': '{:.1f}',
                    'accuracy': '{:.2%}',
                    'precision': '{:.2%}',
                    'recall': '{:.2%}',
                    'f1': '{:.2%}',
                    'matched_rate': '{:.2%}'
                }))

                # Plot precision-recall tradeoff
                fig = go.Figure()

                fig.add_trace(go.Scatter(
                    x=threshold_results['threshold'],
                    y=threshold_results['precision'],
                    mode='lines+markers',
                    name='Precision',
                    line=dict(color='blue')
                ))

                fig.add_trace(go.Scatter(
                    x=threshold_results['threshold'],
                    y=threshold_results['recall'],
                    mode='lines+markers',
                    name='Recall',
                    line=dict(color='red')
                ))

                fig.add_trace(go.Scatter(
                    x=threshold_results['threshold'],
                    y=threshold_results['f1'],
                    mode='lines+markers',
                    name='F1 Score',
                    line=dict(color='green')
                ))

                fig.update_layout(
                    title='Precision-Recall Tradeoff by Confidence Threshold',
                    xaxis_title='Confidence Threshold',
                    yaxis_title='Score',
                    yaxis_range=[0, 1],
                    height=400
                )

                st.plotly_chart(fig, use_container_width=True)

                # Recommendations
                best_f1_idx = threshold_results['f1'].idxmax()
                best_threshold = threshold_results.loc[best_f1_idx, 'threshold']
                best_f1 = threshold_results.loc[best_f1_idx, 'f1']

                st.info(f"**Recommendation:** Best F1 score ({best_f1:.2%}) at threshold {best_threshold:.1f}")


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
