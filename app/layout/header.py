"""Header component."""

from nicegui import ui


def render_header(title='OHLCV Analysis Platform'):
    """Render the application header."""
    with ui.header().classes('items-center justify-between'):
        ui.label(title).classes('text-h5')
