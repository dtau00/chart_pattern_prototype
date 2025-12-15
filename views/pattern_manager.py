"""Pattern management page with labeling and library management tabs."""

from nicegui import ui
from utils.ui_components import create_page_header
from components.patterns.label_patterns import render_label_patterns_tab
from components.patterns.view_library import render_view_library_tab
from components.patterns.train_model import render_train_model_tab


def render_pattern_manager(app_state):
    """Render the pattern manager page with tabs."""
    create_page_header('Pattern Manager')

    with ui.column().classes('w-full p-4'):
        with ui.tabs().classes('w-full') as tabs:
            tab1 = ui.tab('Label Patterns', icon='edit')
            tab2 = ui.tab('View Library', icon='folder')
            tab3 = ui.tab('Train & Validate', icon='model_training')

        with ui.tab_panels(tabs, value=tab1).classes('w-full q-mt-md'):
            with ui.tab_panel(tab1):
                render_label_patterns_tab(app_state)

            with ui.tab_panel(tab2):
                render_view_library_tab(app_state)

            with ui.tab_panel(tab3):
                render_train_model_tab(app_state)
