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

            # Pattern overlay selector
            library = app_state['pattern_library']
            all_labels = library.get_all_labels()

            # Ensure selected_pattern_filter is a string or None (fix corrupted data)
            current_selection = app_state.get('selected_pattern_filter', None)
            if isinstance(current_selection, dict):
                # Handle corrupted data - try to extract label or reset to None
                current_selection = current_selection.get('label', None) if isinstance(current_selection.get('label'), str) else None
                app_state['selected_pattern_filter'] = current_selection
            elif not isinstance(current_selection, (str, type(None))):
                # Reset if it's some other type
                current_selection = None
                app_state['selected_pattern_filter'] = None

            if all_labels:
                with ui.element('div').style('border: 2px solid #4FC3F7; background-color: transparent; border-radius: 4px; padding: 8px; display: inline-block; margin-top: 8px;'):
                    # Create dropdown options with "None" as first option
                    pattern_options = ['-- None --'] + all_labels

                    # Ensure current_selection is valid
                    if current_selection not in all_labels:
                        current_selection = None

                    dropdown_value = '-- None --' if current_selection is None else current_selection

                    pattern_select = ui.select(
                        label='Show Pattern',
                        options=pattern_options,
                        value=dropdown_value
                    ).classes('w-64')

                    def on_pattern_select(e):
                        selected = e.args
                        app_state['selected_pattern_filter'] = None if selected == '-- None --' else selected
                        ui.navigate.reload()

                    pattern_select.on('update:model-value', on_pattern_select)

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
                                    value = e.args
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
                                custom_label['value'] = e.args

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

                                    # Force pattern library to reload from disk on next page load
                                    if 'pattern_library' in app_state:
                                        del app_state['pattern_library']

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

            # Prepare pattern overlays based on selected pattern filter
            pattern_overlays = []
            selected_pattern_label = app_state.get('selected_pattern_filter', None)

            if selected_pattern_label is not None:
                library = app_state['pattern_library']
                # Get all patterns that match the selected label, symbol, and timeframe
                for template in library.templates.values():
                    # Normalize template label to string for comparison
                    template_label = template.label
                    if isinstance(template_label, dict):
                        template_label = template_label.get('label', str(template_label))
                    elif not isinstance(template_label, str):
                        template_label = str(template_label)

                    if (template_label == selected_pattern_label and
                        template.symbol == symbol and
                        template.timeframe == timeframe):
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
                                    'color': 'rgba(79, 195, 247, 0.2)',  # Light blue with transparency
                                    'pattern_id': template.id  # Add pattern ID for click detection
                                })
                        except (KeyError, ValueError):
                            # Pattern not found in current data range, skip it
                            pass

            # Define handler for pattern rectangle clicks
            def handle_pattern_click(pattern_data):
                """Handle clicks on pattern rectangles."""
                pattern_id = pattern_data.get('pattern_id')
                if not pattern_id:
                    return

                # Get the pattern from library
                library = app_state['pattern_library']
                template = library.templates.get(pattern_id)
                if not template:
                    ui.notify("Pattern not found", type='warning')
                    return

                # Get all available labels for dropdown
                all_labels = library.get_all_labels()

                # Show dialog to edit or delete pattern
                with ui.dialog() as pattern_dialog, ui.card():
                    ui.label('Edit Pattern').classes('text-h6 q-mb-md')

                    # Show pattern info
                    ui.label(f"Pattern ID: {template.id[:8]}...").classes('text-caption text-grey-7')
                    ui.label(f"Start: {template.start_time}").classes('text-caption text-grey-7')
                    ui.label(f"End: {template.end_time}").classes('text-caption text-grey-7 q-mb-md')

                    # Dropdown to change pattern label
                    selected_label = {'value': template.label}

                    label_select = ui.select(
                        label='Pattern Name',
                        options=all_labels,
                        value=template.label
                    ).classes('w-full')

                    def on_label_change(e):
                        selected_label['value'] = e.args

                    label_select.on('update:model-value', on_label_change)

                    ui.separator().classes('q-my-md')

                    with ui.row().classes('w-full justify-between gap-2'):
                        # Delete button on the left
                        def delete_pattern():
                            library.delete_template(pattern_id)
                            library.save()
                            ui.notify(f"Pattern '{template.label}' deleted", type='positive')

                            # Force pattern library to reload from disk on next page load
                            if 'pattern_library' in app_state:
                                del app_state['pattern_library']

                            pattern_dialog.close()
                            ui.navigate.reload()

                        ui.button('Delete', on_click=delete_pattern, color='negative')

                        # Cancel and Save buttons on the right
                        with ui.row().classes('gap-2'):
                            ui.button('Cancel', on_click=pattern_dialog.close).props('flat')

                            def save_changes():
                                new_label = selected_label['value']
                                if new_label != template.label:
                                    # Update the label
                                    template.label = new_label
                                    library.save()
                                    ui.notify(f"Pattern label updated to '{new_label}'", type='positive')

                                    # Force pattern library to reload from disk on next page load
                                    if 'pattern_library' in app_state:
                                        del app_state['pattern_library']

                                pattern_dialog.close()
                                ui.navigate.reload()

                            ui.button('Save', on_click=save_changes, color='primary')

                pattern_dialog.open()

            create_tradingview_chart(
                df=df,
                start_idx=pattern_start if pattern_start is not None else 0,
                end_idx=None,  # No end until user sets it
                height=600,
                on_bar_click=None,  # No left-click handler for bars
                on_context_menu=handle_context_menu,
                app_state=app_state,  # Pass app_state to preserve zoom/pan
                pattern_overlays=pattern_overlays,  # Pass pattern overlays
                on_pattern_click=handle_pattern_click  # Handle pattern rectangle clicks
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
