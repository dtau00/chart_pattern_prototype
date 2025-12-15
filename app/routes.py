"""Application routes."""

from nicegui import ui
from app.state import app_state
from app.layout.header import render_header
from app.layout.drawer import render_navigation_drawer
from views.home import render_home
from views.pattern_manager import render_pattern_manager
from views.pattern_scanner import render_pattern_scanner
from views.data_manager import render_data_manager
from views.analysis import render_analysis_dashboard


@ui.page('/')
def main_page():
    """Main page with navigation."""
    ui.dark_mode().enable()
    render_header()
    render_navigation_drawer()
    render_home()


@ui.page('/analysis')
def analysis_page():
    """Analysis dashboard page."""
    ui.dark_mode().enable()
    render_header()
    render_navigation_drawer()
    render_analysis_dashboard(app_state)


@ui.page('/data_manager')
def data_manager_page():
    """Data manager page."""
    ui.dark_mode().enable()
    render_header()
    render_navigation_drawer()
    render_data_manager(app_state)


@ui.page('/pattern_manager')
def pattern_manager_page():
    """Pattern manager page."""
    ui.dark_mode().enable()
    render_header()
    render_navigation_drawer()
    render_pattern_manager(app_state)


@ui.page('/pattern_scanner')
def pattern_scanner_page():
    """Pattern scanner page."""
    ui.dark_mode().enable()
    render_header()
    render_navigation_drawer()
    render_pattern_scanner(app_state)
