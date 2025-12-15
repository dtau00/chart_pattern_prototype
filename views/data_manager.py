"""Data manager page."""

from nicegui import ui
from pathlib import Path
from utils.ui_components import create_page_header


def render_data_manager(app_state):
    """Render the data manager page."""
    create_page_header('OHLCV Data Manager')

    with ui.column().classes('w-full p-4 gap-4'):
        # Download section
        with ui.card().classes('w-full'):
            ui.label('Download Historical Data').classes('text-h6')
            ui.label('Download OHLCV data from HistData.com').classes('text-caption text-grey-7 q-mb-md')

            with ui.row().classes('w-full items-end gap-4'):
                symbol_select = ui.select(
                    label='Symbol',
                    options=['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD'],
                    value='EURUSD'
                ).classes('flex-grow')

                timeframe_select = ui.select(
                    label='Timeframe',
                    options=['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1'],
                    value='H1'
                ).classes('w-40')

                years_input = ui.number(
                    label='Years',
                    value=10,
                    min=1,
                    max=20
                ).classes('w-32')

            def start_download():
                ui.notify('Download started (simulated)', type='info')
                # TODO: Implement actual download logic

            ui.button(
                'Start Download',
                on_click=start_download,
                color='primary',
                icon='download'
            ).classes('w-full q-mt-md')

        # Existing files section
        with ui.card().classes('w-full'):
            ui.label('Existing Data Files').classes('text-h6')

            data_dir = Path("data/parquet")
            if data_dir.exists():
                parquet_files = sorted(data_dir.glob("*.parquet"))
                if parquet_files:
                    ui.label(f'{len(parquet_files)} file(s) found').classes('text-caption text-grey-7 q-mb-md')
                    with ui.column().classes('w-full gap-2'):
                        for file in parquet_files:
                            with ui.card().classes('w-full bg-blue-grey-9'):
                                with ui.row().classes('w-full items-center justify-between'):
                                    with ui.column().classes('gap-0'):
                                        ui.label(file.name).classes('text-subtitle2')
                                        ui.label(f'Size: {file.stat().st_size / 1024 / 1024:.2f} MB').classes('text-caption text-grey-7')
                                    ui.icon('insert_drive_file', size='md').classes('text-grey-7')
                else:
                    ui.label('No data files found').classes('text-caption text-grey-7')
            else:
                ui.label('Data directory does not exist').classes('text-caption text-grey-7')
