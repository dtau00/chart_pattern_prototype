"""Pattern labeling tab - interactive chart with pattern annotation."""

from nicegui import ui
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

from utils.app_init import initialize_pattern_library
from components.charts.tradingview_chart import create_tradingview_chart


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

        # Chart card
        with ui.card().classes('w-full'):
            ui.label(f'{symbol} - {timeframe}').classes('text-h6')
            ui.label('Right-click on a bar to set start/end date').classes('text-caption text-grey-7')

            # Pattern overlay toggle
            if 'show_all_patterns' not in app_state:
                app_state['show_all_patterns'] = False

            with ui.element('div').style('border: 2px solid #4FC3F7; background-color: transparent; border-radius: 4px; padding: 8px; display: inline-block; margin-top: 8px;'):
                show_patterns_checkbox = ui.checkbox('Show all existing patterns', value=app_state.get('show_all_patterns', False))

                def toggle_patterns(e):
                    # e.args contains the new value for update:model-value event
                    app_state['show_all_patterns'] = e.args
                    ui.navigate.reload()

                show_patterns_checkbox.on('update:model-value', toggle_patterns)

            # Define context menu handler
            def handle_context_menu(event_data):
                """Handle context menu selection for setting start/end dates."""
                action = event_data['action']
                index = event_data['index']
                time = event_data['time']

                if action == 'start_date':
                    # Set start index
                    app_state['_pattern_start_index'] = index
                    ui.notify(f"Start date set to {time} (index: {index})", type='positive')
                    ui.navigate.reload() #Reload to show the marker

                elif action == 'end_date':
                    # Get start index
                    current_start = app_state.get('_pattern_start_index', 0)
                    new_length = index - current_start + 1

                    if new_length > 0:
                        # Get existing pattern labels
                        library = app_state['pattern_library']
                        existing_labels = library.get_all_labels()

                        # Show dialog to select or create pattern label
                        with ui.dialog() as label_dialog, ui.card():
                            ui.label('Save Pattern').classes('text-h6 q-mb-md')

                            ui.label(f"Pattern range: {time}").classes('text-caption text-grey-7')
                            ui.label(f"Pattern length: {new_length} bars").classes('text-caption text-grey-7 q-mb-md')

                            # Dropdown for existing labels or custom input
                            selected_label = {'value': existing_labels[0] if existing_labels else ''}
                            custom_label = {'value': ''}

                            if existing_labels:
                                # Add "Create New" option at the beginning
                                label_options = ['-- Create New --'] + existing_labels

                                label_select = ui.select(
                                    label='Select Existing Pattern Label',
                                    options=label_options,
                                    value=label_options[0]
                                ).classes('w-full')

                                def on_label_select(e):
                                    value = e.args if hasattr(e, 'args') else e.value
                                    selected_label['value'] = value if value != '-- Create New --' else ''
                                    if value == '-- Create New --':
                                        custom_input.set_visibility(True)
                                    else:
                                        custom_input.set_visibility(False)
                                        custom_label['value'] = ''

                                label_select.on('update:model-value', on_label_select)
                            else:
                                ui.label('No existing patterns. Create a new label:').classes('text-body2 q-mb-sm')

                            # Custom label input
                            custom_input = ui.input(
                                label='Custom Pattern Label',
                                placeholder='e.g., head_and_shoulders, double_top'
                            ).classes('w-full')

                            # Show custom input by default if no existing labels or "Create New" selected
                            if not existing_labels:
                                custom_input.set_visibility(True)
                            else:
                                custom_input.set_visibility(False)

                            def on_custom_input(e):
                                custom_label['value'] = e.args if hasattr(e, 'args') else e.value

                            custom_input.on('update:model-value', on_custom_input)

                            ui.separator().classes('q-my-md')

                            with ui.row().classes('w-full justify-end gap-2'):
                                ui.button('Cancel', on_click=label_dialog.close).props('flat')

                                def save_and_close():
                                    # Determine which label to use
                                    final_label = custom_label['value'] if custom_label['value'] else selected_label['value']

                                    if not final_label or final_label == '-- Create New --':
                                        ui.notify('Please enter or select a pattern label', type='warning')
                                        return

                                    # Save the pattern
                                    pattern_data = df.iloc[current_start:index + 1].copy()
                                    _save_pattern(app_state, pattern_data, final_label, symbol, timeframe)

                                    # Clear the start index to remove markers
                                    if '_pattern_start_index' in app_state:
                                        app_state.pop('_pattern_start_index', None)

                                    # Close dialog first, then reload to reset the UI
                                    label_dialog.close()
                                    ui.navigate.reload()

                                ui.button('Save Pattern', on_click=save_and_close, color='primary')

                        label_dialog.open()
                    else:
                        ui.notify(f"End date must be after start date (index {current_start})", type='warning')

            # Create TradingView chart with click and context menu handlers
            # Get the start index from state (if set)
            pattern_start = app_state.get('_pattern_start_index', None)

            # Prepare pattern overlays if enabled
            pattern_overlays = []
            if app_state.get('show_all_patterns', False):
                library = app_state['pattern_library']
                # Get all patterns that match the current symbol and timeframe
                for template in library.templates.values():
                    if template.symbol == symbol and template.timeframe == timeframe:
                        # Find the pattern's position in the current dataframe
                        try:
                            # Match by timestamp
                            start_time = pd.Timestamp(template.start_time)
                            end_time = pd.Timestamp(template.end_time)

                            if start_time in df.index and end_time in df.index:
                                start_pos = df.index.get_loc(start_time)
                                end_pos = df.index.get_loc(end_time)

                                pattern_overlays.append({
                                    'start_idx': start_pos,
                                    'end_idx': end_pos + 1,
                                    'label': template.label,
                                    'color': 'rgba(79, 195, 247, 0.2)'  # Light blue with transparency
                                })
                        except (KeyError, ValueError):
                            # Pattern not found in current data range, skip it
                            pass

            create_tradingview_chart(
                df=df,
                start_idx=pattern_start if pattern_start is not None else 0,
                end_idx=None,  # No end until user sets it
                height=600,
                on_bar_click=None,  # No left-click handler
                on_context_menu=handle_context_menu,
                app_state=app_state,  # Pass app_state to preserve zoom/pan
                pattern_overlays=pattern_overlays  # Pass pattern overlays
            )

        # Pattern library statistics
        with ui.card().classes('w-full'):
            library = app_state['pattern_library']
            with ui.column():
                ui.label(f'Total Patterns: {library.get_template_count()}').classes('text-subtitle2')
                if library.get_template_count() > 0:
                    labels_str = ', '.join(library.get_all_labels())
                    ui.label(f'Labels: {labels_str}').classes('text-caption text-grey-7')




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
