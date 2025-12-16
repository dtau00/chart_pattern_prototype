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

    # Filter out weekend bars (Saturday=5, Sunday=6)
    df = df[~df.index.dayofweek.isin([5, 6])]

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

            # Collect matching patterns ONCE (for both UI and chart)
            matching_pattern_templates = []
            if current_selection is not None:
                for template in library.templates.values():
                    template_label = template.label
                    if isinstance(template_label, dict):
                        template_label = template_label.get('label', str(template_label))
                    elif not isinstance(template_label, str):
                        template_label = str(template_label)

                    if (template_label == current_selection and
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

                                matching_pattern_templates.append({
                                    'template': template,
                                    'start_idx': start_pos,
                                    'end_idx': end_pos + 1,
                                    'start_time': start_time,
                                    'end_time': end_time
                                })
                        except (KeyError, ValueError):
                            # Pattern not found in current data range, skip it
                            pass

                # Sort patterns by start index to maintain consistent ordering
                matching_pattern_templates.sort(key=lambda x: x['start_idx'])

            if all_labels:
                with ui.element('div').style('border: 2px solid #4FC3F7; background-color: transparent; border-radius: 4px; padding: 8px; display: inline-block; margin-top: 8px;'):
                    with ui.row().classes('items-center gap-2'):
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
                            # Reset current pattern index when changing filter
                            app_state['current_pattern_index'] = 0
                            ui.navigate.reload()

                        pattern_select.on('update:model-value', on_pattern_select)

                        # Navigation buttons (only show when a pattern is selected)
                        if current_selection is not None:
                            # Always show navigation if patterns exist
                            if len(matching_pattern_templates) >= 1:
                                # Initialize current pattern index
                                current_idx = app_state.get('current_pattern_index', 0)
                                # Ensure index is within bounds
                                current_idx = max(0, min(current_idx, len(matching_pattern_templates) - 1))
                                app_state['current_pattern_index'] = current_idx

                                # Navigation buttons
                                def go_to_previous():
                                    app_state['current_pattern_index'] = max(0, current_idx - 1)
                                    ui.navigate.reload()

                                def go_to_next():
                                    app_state['current_pattern_index'] = min(len(matching_pattern_templates) - 1, current_idx + 1)
                                    ui.navigate.reload()

                                # Visual separator
                                ui.separator().props('vertical').classes('q-mx-md')

                                # Create buttons with conditional enabling
                                prev_btn = ui.button(
                                    icon='chevron_left',
                                    on_click=go_to_previous
                                ).props('round').props('size=sm')
                                if current_idx == 0:
                                    prev_btn.props('disable')

                                ui.label(f'{current_idx + 1} / {len(matching_pattern_templates)}').classes('text-subtitle2 q-mx-sm')

                                next_btn = ui.button(
                                    icon='chevron_right',
                                    on_click=go_to_next
                                ).props('round').props('size=sm')
                                if current_idx >= len(matching_pattern_templates) - 1:
                                    next_btn.props('disable')

                                # Go to pattern index input
                                ui.separator().props('vertical').classes('q-mx-md')

                                # Create a simple text input instead of number input to avoid arrow button confusion
                                goto_input = ui.input(
                                    label='Go to',
                                    value=str(current_idx + 1),
                                    validation={'Please enter a valid number': lambda value: value.isdigit() and 1 <= int(value) <= len(matching_pattern_templates)}
                                ).classes('w-20').props('dense')

                                def go_to_index():
                                    try:
                                        target_idx = int(goto_input.value) - 1  # Convert from 1-based to 0-based
                                        if 0 <= target_idx < len(matching_pattern_templates):
                                            app_state['current_pattern_index'] = target_idx
                                            ui.navigate.reload()
                                        else:
                                            ui.notify(f'Please enter a number between 1 and {len(matching_pattern_templates)}', type='warning')
                                    except (ValueError, TypeError):
                                        ui.notify('Please enter a valid number', type='warning')

                                ui.button('Go', on_click=go_to_index).props('dense')

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
                            selected_label = {'value': ''}
                            custom_label = {'value': ''}

                            if existing_labels:
                                # Add "Create New" option at the beginning
                                label_options = ['-- Create New --'] + existing_labels

                                label_select = ui.select(
                                    label='Select Existing Pattern Label',
                                    options=label_options,
                                    value='-- Create New --'
                                ).classes('w-full')

                                def on_label_select(e):
                                    value = e.args
                                    selected_label['value'] = value if value != '-- Create New --' else ''
                                    if value == '-- Create New --':
                                        custom_input.set_visibility(True)
                                        custom_label['value'] = ''  # Clear custom label when switching to "Create New"
                                    else:
                                        custom_input.set_visibility(False)
                                        custom_input.set_value('')  # Clear the input field
                                        custom_label['value'] = ''

                                label_select.on('update:model-value', on_label_select)
                            else:
                                ui.label('No existing patterns. Create a new label:').classes('text-body2 q-mb-sm')

                            # Custom label input (always created)
                            custom_input = ui.input(
                                label='Custom Pattern Label',
                                placeholder='e.g., head_and_shoulders, double_top'
                            ).classes('w-full')

                            # Show custom input by default (for "Create New" or no existing labels)
                            custom_input.set_visibility(True)

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

            if len(matching_pattern_templates) > 0:
                # Get current pattern index
                current_pattern_idx = app_state.get('current_pattern_index', 0)
                current_pattern_idx = max(0, min(current_pattern_idx, len(matching_pattern_templates) - 1))

                # Check if pattern index changed (indicates navigation, not just reload)
                prev_pattern_idx = app_state.get('_prev_pattern_index', None)
                pattern_changed = prev_pattern_idx != current_pattern_idx
                app_state['_prev_pattern_index'] = current_pattern_idx

                # Add all patterns to overlays, highlighting the current one
                for idx, pattern_template in enumerate(matching_pattern_templates):
                    # Extract label as string (handle dict labels)
                    template_label = pattern_template['template'].label
                    if isinstance(template_label, dict):
                        template_label = template_label.get('label', str(template_label))
                    elif not isinstance(template_label, str):
                        template_label = str(template_label)

                    # Create overlay dict
                    overlay = {
                        'start_idx': pattern_template['start_idx'],
                        'end_idx': pattern_template['end_idx'],
                        'label': template_label,
                        'pattern_id': pattern_template['template'].id
                    }

                    # Highlight current pattern with different color and opacity
                    if idx == current_pattern_idx:
                        overlay['color'] = 'rgba(50, 205, 50, 0.8)'  # Lime green for current pattern

                        # Only update visible range if pattern changed (user navigated)
                        if pattern_changed:
                            # Set visible range to center on this pattern
                            pattern_length = pattern_template['end_idx'] - pattern_template['start_idx']
                            context_bars = max(pattern_length * 2, 50)  # Show 2x pattern length or min 50 bars

                            # Calculate visible range indices
                            center_idx = (pattern_template['start_idx'] + pattern_template['end_idx']) // 2
                            range_start_idx = max(0, center_idx - context_bars // 2)
                            range_end_idx = min(len(df) - 1, center_idx + context_bars // 2)

                            # Convert to timestamps (Unix timestamp in seconds)
                            range_start_time = int(df.index[range_start_idx].timestamp())
                            range_end_time = int(df.index[range_end_idx].timestamp())

                            # Update the saved range to center on current pattern
                            app_state['_chart_visible_range'] = {
                                'from': range_start_time,
                                'to': range_end_time
                            }
                    else:
                        overlay['color'] = 'rgba(50, 205, 50, 0.5)'  # Dimmer lime green for other patterns

                    pattern_overlays.append(overlay)

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

                # Extract template label as string
                template_label = template.label
                if isinstance(template_label, dict):
                    template_label = template_label.get('label', str(template_label))
                elif not isinstance(template_label, str):
                    template_label = str(template_label)

                # Show dialog to edit or delete pattern
                with ui.dialog() as pattern_dialog, ui.card():
                    ui.label('Edit Pattern').classes('text-h6 q-mb-md')

                    # Show pattern info
                    ui.label(f"Pattern ID: {template.id[:8]}...").classes('text-caption text-grey-7')
                    ui.label(f"Start: {template.start_time}").classes('text-caption text-grey-7')
                    ui.label(f"End: {template.end_time}").classes('text-caption text-grey-7 q-mb-md')

                    # Dropdown to change pattern label
                    selected_label = {'value': template_label}

                    label_select = ui.select(
                        label='Pattern Name',
                        options=all_labels,
                        value=template_label
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
                            ui.notify(f"Pattern '{template_label}' deleted", type='positive')

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
                                if new_label != template_label:
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
