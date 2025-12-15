"""Home page view."""

from nicegui import ui


def render_home():
    """Render the home/landing page content."""
    with ui.column().classes('w-full items-center justify-center q-pa-lg'):
        ui.label('Welcome to OHLCV Analysis Platform').classes('text-h4 q-mb-md')
        ui.label('Chart Pattern Recognition with DTW & kNN').classes('text-subtitle1 text-grey-7 q-mb-lg')

        with ui.card().classes('w-full max-w-4xl'):
            ui.label('Features').classes('text-h6 q-mb-md')
            with ui.grid(columns=2).classes('w-full gap-4'):
                with ui.card().classes('bg-blue-grey-9'):
                    ui.icon('analytics', size='lg').classes('q-mb-sm')
                    ui.label('Analysis Dashboard').classes('text-subtitle1 text-weight-medium')
                    ui.label('High-level KPIs and metrics').classes('text-caption text-grey-7')

                with ui.card().classes('bg-blue-grey-9'):
                    ui.icon('storage', size='lg').classes('q-mb-sm')
                    ui.label('Data Manager').classes('text-subtitle1 text-weight-medium')
                    ui.label('Download and manage OHLCV data').classes('text-caption text-grey-7')

                with ui.card().classes('bg-blue-grey-9'):
                    ui.icon('pattern', size='lg').classes('q-mb-sm')
                    ui.label('Pattern Manager').classes('text-subtitle1 text-weight-medium')
                    ui.label('Label and manage chart patterns').classes('text-caption text-grey-7')

                with ui.card().classes('bg-blue-grey-9'):
                    ui.icon('search', size='lg').classes('q-mb-sm')
                    ui.label('Pattern Scanner').classes('text-subtitle1 text-weight-medium')
                    ui.label('Real-time pattern detection').classes('text-caption text-grey-7')
