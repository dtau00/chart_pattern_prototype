"""Model training and validation tab."""

from nicegui import ui
import plotly.express as px

from utils.app_init import initialize_scanner_components


def render_train_model_tab(app_state):
    """Render the training and validation interface."""
    initialize_scanner_components(app_state)

    library = app_state['pattern_library']

    if library.get_template_count() == 0:
        ui.notify("No patterns in library. Please label some patterns first.", type='warning')
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
                    original_count = sum(1 for t in library.templates.values() if not t.is_augmented)
                    ui.label('Original Patterns').classes('text-caption text-grey-7')
                    ui.label(str(original_count)).classes('text-h5')

                with ui.card().classes('bg-blue-grey-9'):
                    augmented_count = sum(1 for t in library.templates.values() if t.is_augmented)
                    ui.label('Augmented Patterns').classes('text-caption text-grey-7')
                    ui.label(str(augmented_count)).classes('text-h5')

            # Show pattern distribution
            if unique_labels:
                label_counts = {}
                for label in unique_labels:
                    label_counts[label] = len(library.get_templates_by_label(label))

                fig = px.bar(
                    x=list(label_counts.keys()),
                    y=list(label_counts.values()),
                    labels={'x': 'Pattern Label', 'y': 'Count'},
                    title='Patterns per Label',
                    template='plotly_dark'
                )
                ui.plotly(fig).classes('w-full q-mt-md')

        # Cross-validation card
        with ui.card().classes('w-full'):
            ui.label('Cross-Validation').classes('text-h6 q-mb-md')

            with ui.row().classes('w-full items-center gap-4'):
                ui.label('Min Confidence:').classes('text-subtitle2')
                min_confidence_slider = ui.slider(
                    min=0.0,
                    max=1.0,
                    step=0.05,
                    value=0.7
                ).props('label-always').classes('flex-grow')

                exclude_augmented_checkbox = ui.checkbox(
                    'Exclude Augmented',
                    value=True
                )

            results_container = ui.column().classes('w-full q-mt-md')

            def run_cross_validation():
                results_container.clear()

                min_confidence = min_confidence_slider.value
                exclude_augmented = exclude_augmented_checkbox.value

                with results_container:
                    ui.label('Running cross-validation...').classes('text-caption')

                    try:
                        backtester = app_state['backtester']
                        results = backtester.cross_validate(
                            min_confidence=min_confidence,
                            exclude_augmented=exclude_augmented
                        )

                        if 'error' in results:
                            ui.notify(results['error'], type='negative')
                        else:
                            ui.notify(f"Cross-validation complete! ({results['cv_strategy']})", type='positive')

                            # Display metrics
                            with ui.row().classes('w-full gap-4'):
                                with ui.card().classes('bg-blue-grey-9'):
                                    ui.label('Accuracy').classes('text-caption text-grey-7')
                                    ui.label(f"{results['accuracy']:.2%}").classes('text-h5')

                                with ui.card().classes('bg-blue-grey-9'):
                                    ui.label('Precision').classes('text-caption text-grey-7')
                                    ui.label(f"{results['macro_precision']:.2%}").classes('text-h5')

                                with ui.card().classes('bg-blue-grey-9'):
                                    ui.label('Recall').classes('text-caption text-grey-7')
                                    ui.label(f"{results['macro_recall']:.2%}").classes('text-h5')

                                with ui.card().classes('bg-blue-grey-9'):
                                    ui.label('F1 Score').classes('text-caption text-grey-7')
                                    ui.label(f"{results['macro_f1']:.2%}").classes('text-h5')

                            # Additional metrics
                            with ui.row().classes('w-full gap-4 q-mt-md'):
                                ui.label(f"Matched Rate: {results['matched_rate']:.2%}").classes('text-subtitle2')
                                ui.label(f"Avg Confidence: {results['avg_confidence']:.2%}").classes('text-subtitle2')
                                ui.label(f"Total Samples: {results['total_samples']}").classes('text-subtitle2')

                            app_state['cv_results'] = results

                    except Exception as e:
                        ui.notify(f'Error during cross-validation: {str(e)}', type='negative')

            ui.button(
                'Run Cross-Validation',
                on_click=run_cross_validation,
                color='primary',
                icon='model_training'
            ).classes('w-full')
