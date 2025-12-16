"""View and manage pattern library."""

from nicegui import ui
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.app_init import initialize_pattern_library


def render_view_library_tab(app_state):
    """Render the library viewer interface."""
    initialize_pattern_library(app_state)

    library = app_state['pattern_library']

    if library.get_template_count() == 0:
        ui.label("No patterns in library yet. Use the 'Label Patterns' tab to add patterns.").classes('text-caption')
        return

    with ui.column().classes('w-full gap-4'):
        # Statistics card
        with ui.card().classes('w-full'):
            ui.label('Library Statistics').classes('text-h6 q-mb-md')

            with ui.row().classes('w-full gap-4'):
                with ui.card().classes('bg-blue-grey-9'):
                    ui.label('Total Patterns').classes('text-caption text-grey-7')
                    ui.label(str(library.get_template_count())).classes('text-h5')

                with ui.card().classes('bg-blue-grey-9'):
                    unique_labels = library.get_all_labels()
                    ui.label('Unique Labels').classes('text-caption text-grey-7')
                    ui.label(str(len(unique_labels))).classes('text-h5')

                with ui.card().classes('bg-blue-grey-9'):
                    augmented_count = sum(1 for t in library.templates.values() if t.is_augmented)
                    ui.label('Augmented Patterns').classes('text-caption text-grey-7')
                    ui.label(str(augmented_count)).classes('text-h5')

        # Management card
        with ui.card().classes('w-full'):
            ui.label('Library Management').classes('text-h6 q-mb-md')

            with ui.row().classes('w-full gap-4'):
                def augment_library():
                    config = app_state['config']
                    library.augment_library(mirror_patterns=config['augmentation']['mirror_patterns'])
                    library.save()
                    ui.notify(f'Library augmented! New total: {library.get_template_count()} patterns', type='positive')
                    ui.navigate.reload()

                ui.button(
                    'Augment Library (Mirror Patterns)',
                    on_click=augment_library,
                    color='secondary',
                    icon='flip'
                )

                def build_index():
                    library.build_index()
                    library.save()
                    ui.notify('Index built successfully!', type='positive')

                ui.button(
                    'Build Index (LB_Keogh)',
                    on_click=build_index,
                    color='secondary',
                    icon='build'
                )

        # Filter card
        with ui.card().classes('w-full'):
            ui.label('Pattern Browser').classes('text-h6 q-mb-md')

            unique_labels = library.get_all_labels()
            label_options = ['All'] + unique_labels

            selected_label = ui.select(
                label='Filter by label',
                options=label_options,
                value='All'
            ).classes('w-64')

            templates_container = ui.column().classes('w-full q-mt-md')

            def update_templates(e):
                templates_container.clear()
                with templates_container:
                    _display_templates(app_state, library, e.value)

            selected_label.on('update:model-value', update_templates)

            # Initial display
            with templates_container:
                _display_templates(app_state, library, 'All')


def _display_templates(app_state, library, selected_label):
    """Display templates based on filter."""
    if selected_label == 'All':
        templates = list(library.templates.values())
    else:
        templates = library.get_templates_by_label(selected_label)

    # Sort templates, handling cases where label might be dict or other types
    def get_label_str(t):
        if isinstance(t.label, str):
            return t.label
        elif isinstance(t.label, dict):
            return t.label.get('label', str(t.label))
        else:
            return str(t.label)

    templates.sort(key=get_label_str)

    ui.label(f'Showing {len(templates)} pattern(s)').classes('text-subtitle1 q-mt-md')

    for template in templates:
        # Get label as string for display
        label_str = get_label_str(template)

        with ui.expansion(
            f"{label_str} - {template.symbol} {template.timeframe} ({template.bars_count} bars) - Quality: {template.quality_score:.2f}",
            icon='pattern'
        ).classes('w-full'):
            with ui.row().classes('w-full gap-4'):
                with ui.column():
                    ui.label('Pattern Info').classes('text-subtitle2')
                    ui.label(f"ID: {template.id[:16]}...")
                    ui.label(f"Label: {label_str}")
                    ui.label(f"Bars: {template.bars_count}")
                    ui.label(f"Quality: {template.quality_score:.3f}")

                with ui.column():
                    ui.label('Metadata').classes('text-subtitle2')
                    ui.label(f"Symbol: {template.symbol}")
                    ui.label(f"Timeframe: {template.timeframe}")
                    ui.label(f"Period: {template.start_time.strftime('%Y-%m-%d')} to {template.end_time.strftime('%Y-%m-%d')}")
                    if template.is_augmented:
                        ui.label(f"Augmented: {template.augmentation_type}")

            # Chart
            fig = _create_pattern_chart(template)
            ui.plotly(fig).classes('w-full')

            def delete_pattern(t=template):
                del library.templates[t.id]
                library.save()
                ui.notify('Pattern deleted!', type='positive')
                ui.navigate.reload()

            ui.button(f'Delete Pattern', on_click=delete_pattern, color='negative', icon='delete')


def _create_pattern_chart(template):
    """Create chart showing both raw and normalized patterns."""
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Raw Pattern (OHLC)", "Normalized Pattern (DDTW)"),
        row_heights=[0.6, 0.4]
    )

    # Convert index to strings to avoid Timestamp serialization issues
    raw_data_plot = template.raw_data.copy()
    raw_data_plot.index = raw_data_plot.index.astype(str)

    # Raw candlestick
    fig.add_trace(
        go.Candlestick(
            x=raw_data_plot.index,
            open=raw_data_plot['open'],
            high=raw_data_plot['high'],
            low=raw_data_plot['low'],
            close=raw_data_plot['close'],
            name='OHLC'
        ),
        row=1, col=1
    )

    # Normalized pattern
    fig.add_trace(
        go.Scatter(
            y=template.normalized,
            mode='lines',
            name='Normalized',
            line=dict(color='blue')
        ),
        row=2, col=1
    )

    fig.update_layout(
        height=500,
        showlegend=False,
        xaxis_rangeslider_visible=False,
        xaxis2_title="Bar Index",
        yaxis2_title="Normalized Value",
        template='plotly_dark'
    )

    return fig
