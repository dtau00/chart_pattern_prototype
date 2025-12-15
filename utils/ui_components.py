"""Shared UI components for NiceGUI app."""

from nicegui import ui


def create_page_header(title: str, show_back_button: bool = True):
    """Create a consistent page header with optional back button.

    Args:
        title: The page title to display
        show_back_button: Whether to show the back button (default: True)
    """
    with ui.header().classes('items-center justify-between'):
        with ui.row().classes('items-center gap-2'):
            if show_back_button:
                ui.button(
                    icon='arrow_back',
                    on_click=lambda: ui.open('/')
                ).props('flat round').classes('text-white')
            ui.label(title).classes('text-h5')


def create_metric_card(label: str, value: str, sublabel: str = None, color: str = None):
    """Create a metric card with consistent styling.

    Args:
        label: The metric label
        value: The metric value
        sublabel: Optional sublabel (e.g., percentage change)
        color: Optional color class for the value
    """
    with ui.card().classes('p-4'):
        ui.label(label).classes('text-caption text-grey-7')
        value_classes = 'text-h5'
        if color:
            value_classes += f' text-{color}'
        ui.label(value).classes(value_classes)
        if sublabel:
            ui.label(sublabel).classes('text-caption')


def create_info_section(title: str, items: dict):
    """Create an information section with key-value pairs.

    Args:
        title: Section title
        items: Dictionary of key-value pairs to display
    """
    with ui.column().classes('gap-1'):
        ui.label(title).classes('text-subtitle2 text-weight-medium')
        for key, value in items.items():
            ui.label(f"{key}: {value}").classes('text-body2')
