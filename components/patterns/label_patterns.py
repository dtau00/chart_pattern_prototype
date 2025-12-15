"""Pattern labeling tab - interactive chart with pattern annotation."""

from nicegui import ui
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

from utils.app_init import initialize_pattern_library


def render_label_patterns_tab(app_state):
    """Render the pattern labeling interface."""
    initialize_pattern_library(app_state)

    # File selection
    data_dir = Path("data/parquet")
    if not data_dir.exists():
        ui.notify("No data directory found. Please download data first.", type='warning')
        return

    parquet_files = list(data_dir.glob("*.parquet"))
    if not parquet_files:
        ui.notify("No parquet files found. Please download data first.", type='warning')
        return

    # Initialize state defaults
    if 'pattern_length' not in app_state:
        app_state['pattern_length'] = 50
    if 'start_index' not in app_state:
        app_state['start_index'] = 0
    if 'pattern_label' not in app_state:
        app_state['pattern_label'] = ''
    if 'selected_file_idx' not in app_state:
        app_state['selected_file_idx'] = 0

    selected_file_idx = app_state.get('selected_file_idx', 0)
    selected_file = parquet_files[selected_file_idx]

    # Load data
    df = pd.read_parquet(selected_file)
    df.index = pd.to_datetime(df.index)

    # Extract symbol and timeframe from filename
    filename_parts = selected_file.stem.split('_')
    symbol = filename_parts[0] if len(filename_parts) > 0 else "UNKNOWN"
    timeframe = filename_parts[1] if len(filename_parts) > 1 else "UNKNOWN"

    # Create UI
    with ui.column().classes('w-full gap-4'):
        # Controls card
        with ui.card().classes('w-full'):
            ui.label('Pattern Selection').classes('text-h6')

            # File selection row
            with ui.row().classes('w-full items-end gap-4'):
                file_names = [f.name for f in parquet_files]
                file_select = ui.select(
                    label='Data File',
                    options=file_names,
                    value=file_names[selected_file_idx]
                ).classes('flex-grow')

                def on_file_change(e):
                    app_state['selected_file_idx'] = file_names.index(e.value)
                    ui.navigate.reload()

                file_select.on('update:model-value', on_file_change)

            # Pattern parameters row
            with ui.row().classes('w-full items-end gap-4'):
                # Pattern length
                pattern_length_input = ui.number(
                    label='Pattern Length (bars)',
                    value=app_state.get('pattern_length', 50),
                    min=10,
                    max=200
                ).classes('w-48')

                def update_pattern_length(e):
                    app_state['pattern_length'] = int(e.value)
                    ui.navigate.reload()

                pattern_length_input.on('update:model-value', update_pattern_length)

                # Start index
                start_index_input = ui.number(
                    label='Start Index',
                    value=app_state.get('start_index', 0),
                    min=0,
                    max=max(0, len(df) - app_state.get('pattern_length', 50))
                ).classes('w-48')

                def update_start_index(e):
                    app_state['start_index'] = int(e.value)
                    ui.navigate.reload()

                start_index_input.on('update:model-value', update_start_index)

                # Pattern label
                pattern_label_input = ui.input(
                    label='Pattern Label',
                    placeholder='e.g., head_and_shoulders',
                    value=app_state.get('pattern_label', '')
                ).classes('flex-grow')

                def update_pattern_label(e):
                    app_state['pattern_label'] = e.value

                pattern_label_input.on('update:model-value', update_pattern_label)

        # Get pattern data
        pattern_length = app_state.get('pattern_length', 50)
        start_index = app_state.get('start_index', 0)
        end_index = min(start_index + pattern_length, len(df))
        pattern_data = df.iloc[start_index:end_index].copy()

        # Chart card
        with ui.card().classes('w-full'):
            ui.label('Chart - Click to Select Pattern Start').classes('text-h6')
            ui.label('Click on any bar to set the pattern start position').classes('text-caption text-grey-7 q-mb-md')

            fig = _create_candlestick_chart_with_pattern(df, start_index, end_index, f"{symbol} - {timeframe}")

            # Create plotly chart with click event handler
            plot = ui.plotly(fig).classes('w-full h-96')

            # Handle click events - NiceGUI allows direct event handling on plotly charts
            def handle_click(e):
                """Handle chart click events."""
                if e.args and 'points' in e.args and len(e.args['points']) > 0:
                    point = e.args['points'][0]
                    if 'pointIndex' in point:
                        clicked_index = point['pointIndex']
                        app_state['start_index'] = clicked_index
                        ui.navigate.reload()

            plot.on('plotly_click', handle_click)

        # Normalized pattern card
        with ui.card().classes('w-full'):
            show_normalized = ui.checkbox('Show Normalized Pattern', value=False)

            normalized_container = ui.column().classes('w-full q-mt-md')

            def toggle_normalized(e):
                normalized_container.clear()
                if e.value:
                    with normalized_container:
                        preprocessor = app_state['preprocessor']
                        normalized = preprocessor.normalize_pattern(pattern_data)

                        fig_norm = go.Figure()
                        fig_norm.add_trace(go.Scatter(
                            y=normalized,
                            mode='lines',
                            name='Normalized Pattern',
                            line=dict(color='#2196F3')
                        ))
                        fig_norm.update_layout(
                            title="Normalized Pattern (DDTW)",
                            xaxis_title="Bar Index",
                            yaxis_title="Normalized Value",
                            height=300,
                            template='plotly_dark'
                        )
                        ui.plotly(fig_norm).classes('w-full')

            show_normalized.on('update:model-value', toggle_normalized)

        # Save section
        with ui.card().classes('w-full'):
            ui.label('Save Pattern').classes('text-h6 q-mb-md')

            with ui.row().classes('w-full items-center justify-between gap-4'):
                pattern_label = app_state.get('pattern_label', '')

                def save_pattern():
                    if not pattern_label:
                        ui.notify('Please enter a pattern label', type='warning')
                        return
                    _save_pattern(app_state, pattern_data, pattern_label, symbol, timeframe)
                    app_state['pattern_label'] = ''
                    ui.navigate.reload()

                ui.button(
                    'Save Pattern',
                    on_click=save_pattern,
                    color='primary',
                    icon='save'
                ).props('disable' if not pattern_label else '')

                library = app_state['pattern_library']
                with ui.column():
                    ui.label(f'Total Patterns: {library.get_template_count()}').classes('text-subtitle2')
                    if library.get_template_count() > 0:
                        labels_str = ', '.join(library.get_all_labels())
                        ui.label(f'Labels: {labels_str}').classes('text-caption text-grey-7')


def _create_candlestick_chart_with_pattern(df: pd.DataFrame, start_idx: int, end_idx: int, title: str):
    """Create candlestick chart with full data and highlighted pattern region."""
    # Convert index to strings to avoid Timestamp serialization issues
    df_plot = df.copy()
    df_plot.index = df_plot.index.astype(str)

    fig = go.Figure(data=[go.Candlestick(
        x=df_plot.index,
        open=df_plot['open'],
        high=df_plot['high'],
        low=df_plot['low'],
        close=df_plot['close'],
        name='OHLC'
    )])

    # Add vertical lines to mark pattern boundaries
    pattern_start = df_plot.index[start_idx]
    pattern_end = df_plot.index[end_idx - 1] if end_idx > 0 else df_plot.index[start_idx]

    # Add shaded rectangle to highlight pattern region
    fig.add_vrect(
        x0=pattern_start,
        x1=pattern_end,
        fillcolor="rgba(255, 165, 0, 0.2)",
        layer="below",
        line_width=2,
        line_color="orange",
        annotation_text="Selected Pattern",
        annotation_position="top left"
    )

    fig.update_layout(
        title=title,
        xaxis_title="Time",
        yaxis_title="Price",
        height=600,
        xaxis_rangeslider_visible=True,
        hovermode='x unified',
        dragmode='pan',
        template='plotly_dark'
    )

    # Enable scroll wheel zoom
    fig.update_xaxes(fixedrange=False)
    fig.update_yaxes(fixedrange=False)

    return fig


def _save_pattern(app_state, pattern_data: pd.DataFrame, label: str, symbol: str, timeframe: str):
    """Save pattern to library."""
    library = app_state['pattern_library']

    metadata = {
        'symbol': symbol,
        'timeframe': timeframe,
        'start_time': pattern_data.index[0],
        'end_time': pattern_data.index[-1]
    }

    template = library.add_pattern(label, pattern_data, metadata)
    library.save()

    ui.notify(f"Pattern '{label}' saved successfully! (ID: {template.id[:8]}...)", type='positive')
