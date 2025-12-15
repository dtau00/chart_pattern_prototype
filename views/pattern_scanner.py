"""Pattern scanner page."""

from nicegui import ui
from utils.ui_components import create_page_header
from components.patterns.scan_patterns import render_scan_patterns_tab


def render_pattern_scanner(app_state):
    """Render the pattern scanner page."""
    create_page_header('Pattern Scanner')

    with ui.column().classes('w-full p-4'):
        render_scan_patterns_tab(app_state)
