"""Navigation drawer component."""

from nicegui import ui


def render_navigation_drawer():
    """Render the left navigation drawer."""
    with ui.left_drawer(top_corner=True, bottom_corner=True).classes('bg-blue-grey-9'):
        ui.label('Navigation').classes('text-h6 q-ma-md')
        ui.separator()

        with ui.column().classes('w-full gap-2 q-pa-md'):
            ui.button(
                'Analysis Dashboard',
                on_click=lambda: ui.navigate.to('/analysis'),
                icon='analytics'
            ).props('flat align=left').classes('w-full')

            ui.button(
                'Data Manager',
                on_click=lambda: ui.navigate.to('/data_manager'),
                icon='storage'
            ).props('flat align=left').classes('w-full')

            ui.button(
                'Pattern Manager',
                on_click=lambda: ui.navigate.to('/pattern_manager'),
                icon='pattern'
            ).props('flat align=left').classes('w-full')

            ui.button(
                'Pattern Scanner',
                on_click=lambda: ui.navigate.to('/pattern_scanner'),
                icon='search'
            ).props('flat align=left').classes('w-full')
