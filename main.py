"""Main NiceGUI application entry point."""

from nicegui import ui
from app.routes import *  # Import all route definitions


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title='OHLCV Analysis Platform',
        port=8080,
        reload=True,
        show=False,
        dark=True
    )
