"""Shared initialization utilities for NiceGUI app."""

from pathlib import Path
import yaml

from engine.preprocessor import Preprocessor
from engine.pattern_library import PatternLibrary
from engine.dtw_core import DTWCalculator
from engine.pattern_matcher import PatternMatcher
from engine.confidence import ConfidenceScorer
from engine.backtester import Backtester


def initialize_pattern_library(app_state):
    """Initialize pattern library and related components.

    This is a centralized initialization function to avoid code duplication
    across multiple components.
    """
    if 'pattern_library' in app_state:
        return  # Already initialized

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

    app_state['preprocessor'] = preprocessor
    app_state['dtw_calculator'] = dtw_calculator
    app_state['pattern_library'] = library
    app_state['config'] = config


def initialize_scanner_components(app_state):
    """Initialize pattern matcher and backtester for scanning operations."""
    # First ensure pattern library is initialized
    initialize_pattern_library(app_state)

    if 'backtester' in app_state:
        return  # Already initialized

    config = app_state['config']

    confidence_scorer = ConfidenceScorer(
        closeness_weight=config['confidence']['weights']['closeness'],
        consensus_weight=config['confidence']['weights']['consensus'],
        separation_weight=config['confidence']['weights']['separation'],
        quality_weight=config['confidence']['weights']['quality']
    )

    matcher = PatternMatcher(
        library=app_state['pattern_library'],
        dtw_calculator=app_state['dtw_calculator'],
        confidence_scorer=confidence_scorer,
        k=config['knn']['k']
    )

    backtester = Backtester(
        library=app_state['pattern_library'],
        matcher=matcher
    )

    app_state['confidence_scorer'] = confidence_scorer
    app_state['matcher'] = matcher
    app_state['backtester'] = backtester
