"""Analysis dashboard page."""

from nicegui import ui
from utils.ui_components import create_page_header, create_metric_card
from utils.app_init import initialize_pattern_library


def render_analysis_dashboard(app_state):
    """Render the analysis dashboard page."""
    create_page_header('Analysis Dashboard')

    initialize_pattern_library(app_state)

    with ui.column().classes('w-full p-4 gap-4'):
        # KPI Cards
        with ui.row().classes('w-full gap-4'):
            library = app_state.get('pattern_library')
            pattern_count = library.get_template_count() if library else 0

            create_metric_card(
                label='Active Patterns',
                value=str(pattern_count),
                color='primary'
            )

            create_metric_card(
                label='Unique Labels',
                value=str(len(library.get_all_labels())) if library and pattern_count > 0 else '0',
                color='secondary'
            )

            create_metric_card(
                label='Total Revenue',
                value='$150K',
                sublabel='+3%',
                color='positive'
            )

        # Additional insights
        with ui.card().classes('w-full'):
            ui.label('Quick Insights').classes('text-h6 q-mb-md')
            ui.label('Welcome to the analysis dashboard. This is where high-level metrics and KPIs will be displayed.').classes('text-body2 text-grey-7')
