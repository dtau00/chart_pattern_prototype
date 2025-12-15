"""Pattern scanning tab - real-time pattern detection."""

from nicegui import ui
import pandas as pd
from pathlib import Path

from utils.app_init import initialize_scanner_components


def render_scan_patterns_tab(app_state):
    """Render the pattern scanning interface."""
    initialize_scanner_components(app_state)

    library = app_state['pattern_library']

    if library.get_template_count() == 0:
        ui.notify("No patterns in library. Please label some patterns first.", type='warning')
        return

    if library.index_dirty:
        ui.notify("Building index for faster scanning...", type='info')
        library.build_index()
        library.save()

    # File selection
    data_dir = Path("data/parquet")
    if not data_dir.exists():
        ui.notify("No data directory found.", type='negative')
        return

    parquet_files = list(data_dir.glob("*.parquet"))
    if not parquet_files:
        ui.notify("No parquet files found.", type='negative')
        return

    with ui.column().classes('w-full gap-4'):
        with ui.card().classes('w-full'):
            ui.label('Scanner Configuration').classes('text-h6 q-mb-md')

            with ui.row().classes('w-full items-end gap-4'):
                file_names = [f.name for f in parquet_files]
                selected_file_idx = app_state.get('scanner_file_index', 0)

                file_select = ui.select(
                    label='Data File',
                    options=file_names,
                    value=file_names[selected_file_idx]
                ).classes('flex-grow')

                def on_file_change(e):
                    app_state['scanner_file_index'] = file_names.index(e.value)

                file_select.on('update:model-value', on_file_change)

                window_size_input = ui.number(
                    label='Window Size (bars)',
                    value=app_state.get('scanner_window_size', 50),
                    min=10,
                    max=200
                ).classes('w-48')

                def update_window_size(e):
                    app_state['scanner_window_size'] = int(e.value)

                window_size_input.on('update:model-value', update_window_size)

            with ui.row().classes('w-full items-center gap-4'):
                ui.label('Min Confidence:').classes('text-subtitle2')
                min_confidence_slider = ui.slider(
                    min=0.0,
                    max=1.0,
                    step=0.05,
                    value=app_state.get('scanner_min_confidence', 0.7)
                ).props('label-always').classes('flex-grow')

                def update_min_confidence(e):
                    app_state['scanner_min_confidence'] = e.value

                min_confidence_slider.on('update:model-value', update_min_confidence)

            def scan_for_patterns():
                selected_file = parquet_files[app_state.get('scanner_file_index', 0)]
                window_size = app_state.get('scanner_window_size', 50)
                min_confidence = app_state.get('scanner_min_confidence', 0.7)

                # Load data
                df = pd.read_parquet(selected_file)
                df.index = pd.to_datetime(df.index)

                # Run backtest
                backtester = app_state['backtester']
                detections = backtester.backtest_on_data(
                    ohlc_data=df,
                    window_size=window_size,
                    step=5,
                    min_confidence=min_confidence
                )

                app_state['scan_detections'] = detections
                app_state['scan_data'] = df

                ui.notify(f'Scan complete! Found {len(detections)} pattern(s).', type='positive')
                ui.navigate.reload()

            ui.button(
                'Scan for Patterns',
                on_click=scan_for_patterns,
                color='primary',
                icon='search'
            ).classes('w-full q-mt-md')

        # Display results
        if 'scan_detections' in app_state:
            detections = app_state['scan_detections']

            if not detections:
                with ui.card().classes('w-full'):
                    ui.label('No patterns detected at this confidence level.').classes('text-caption text-grey-7')
            else:
                with ui.card().classes('w-full'):
                    ui.label(f'Detected Patterns ({len(detections)})').classes('text-h6 q-mb-md')

                    with ui.row().classes('w-full gap-4 q-mb-md'):
                        with ui.card().classes('bg-blue-grey-9'):
                            ui.label('Total Detections').classes('text-caption text-grey-7')
                            ui.label(str(len(detections))).classes('text-h6')

                        with ui.card().classes('bg-blue-grey-9'):
                            unique_patterns = len(set(d['label'] for d in detections))
                            ui.label('Unique Patterns').classes('text-caption text-grey-7')
                            ui.label(str(unique_patterns)).classes('text-h6')

                        with ui.card().classes('bg-blue-grey-9'):
                            avg_confidence = sum(d['confidence'] for d in detections) / len(detections)
                            ui.label('Avg Confidence').classes('text-caption text-grey-7')
                            ui.label(f'{avg_confidence:.0%}').classes('text-h6')

                    # Display each detection
                    ui.label(f'Showing first {min(10, len(detections))} detections').classes('text-caption text-grey-7 q-mb-sm')
                    for i, detection in enumerate(detections[:10]):  # Limit to first 10
                        with ui.expansion(
                            f"#{i+1}: {detection['label']} - Confidence: {detection['confidence']:.2%}",
                            icon='analytics'
                        ).classes('w-full'):
                            with ui.row().classes('w-full gap-4'):
                                with ui.column():
                                    ui.label(f"Pattern: {detection['label']}").classes('text-weight-medium')
                                    ui.label(f"Confidence: {detection['confidence']:.2%}")
                                    ui.label(f"Start: {detection['start_time']}")
                                    ui.label(f"End: {detection['end_time']}")

                                with ui.column():
                                    window_data = detection['window_data']
                                    price_change = ((window_data['close'].iloc[-1] - window_data['close'].iloc[0])
                                                  / window_data['close'].iloc[0])
                                    ui.label(f"Start Price: {window_data['close'].iloc[0]:.5f}")
                                    ui.label(f"End Price: {window_data['close'].iloc[-1]:.5f}")
                                    change_color = 'positive' if price_change > 0 else 'negative'
                                    ui.label(f"Change: {price_change:.2%}").classes(f'text-{change_color}')
