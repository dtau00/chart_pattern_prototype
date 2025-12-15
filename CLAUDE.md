# Project Description

Chart pattern recognition application built with NiceGUI for enhanced control over interactive components like Plotly charts with full event handling support.

# Implementation Patterns

## Main Entry Point
```python
# main.py
from nicegui import ui
from app.routes import *

ui.run(title='OHLCV Analysis Platform', port=8080)
```

## Routes
```python
# app/routes.py
from nicegui import ui
from app.state import app_state
from views.pattern_manager import render_pattern_manager

@ui.page('/pattern_manager')
def pattern_manager_page():
    ui.dark_mode().enable()
    render_header()
    render_navigation_drawer()
    render_pattern_manager(app_state)
```

## State Management
```python
# app/state.py - Global state
from app.state import app_state

# Initialize defaults
if 'pattern_length' not in app_state:
    app_state['pattern_length'] = 50

# Get state
value = app_state.get('pattern_length', 50)
value = app_state['pattern_length']

# Set state
app_state['pattern_length'] = 100
app_state.set('pattern_length', 100)
```

AppState automatically separates JSON-serializable values from complex Python objects (DataFrames, Timestamps).

## Component Structure
```python
# components/patterns/label_patterns.py
from nicegui import ui

def render_label_patterns_tab(app_state):
    with ui.card().classes('w-full'):
        ui.label('Label Patterns').classes('text-h5')

        # Create interactive Plotly chart
        fig = create_chart(data)
        plot = ui.plotly(fig).classes('w-full')

        # Handle events
        def handle_click(e):
            if e.args and 'points' in e.args:
                point = e.args['points'][0]
                app_state['start_index'] = point['pointIndex']
                ui.navigate.reload()

        plot.on('plotly_click', handle_click)
```

# NiceGUI Essentials

## Navigation
```python
ui.navigate.to('/page_path')    # Navigate to route
ui.navigate.reload()             # Reload current page
```

## UI Components
```python
ui.label("Title").classes('text-h5')
ui.button("Click", on_click=handler, color='primary', icon='search')
ui.input(label='Name', value='default')
ui.number(label='Count', value=50, min=1, max=100)
ui.select(label='Pick', options=['A', 'B'], value='A')
ui.checkbox('Enabled', value=True)
ui.slider(min=0, max=10, value=5)
```

## Layout
```python
with ui.header():
    ui.label('Title')

with ui.left_drawer():
    ui.button('Nav Item')

with ui.card().classes('w-full'):
    ui.label('Card content')

with ui.row().classes('gap-4'):
    with ui.column():
        # Column 1
    with ui.column():
        # Column 2
```

## Events
```python
# Input events
input.on('update:model-value', lambda e: handle_change(e.value))

# Button events
button.on('click', lambda: do_something())

# Plotly events
plot.on('plotly_click', handle_click)
plot.on('plotly_hover', handle_hover)
plot.on('plotly_relayout', handle_zoom)
```

## Notifications
```python
ui.notify("Success!", type='positive')
ui.notify("Info", type='info')
ui.notify("Warning", type='warning')
ui.notify("Error!", type='negative')
```

## Styling
Use Quasar classes:
- `'text-h4'`, `'text-h5'`, `'text-h6'` - Headers
- `'text-subtitle1'`, `'text-subtitle2'` - Subtitles
- `'text-body1'`, `'text-body2'`, `'text-caption'` - Body text
- `'w-full'`, `'h-96'` - Width/height
- `'q-pa-lg'`, `'q-ma-md'` - Padding/margin
- `'gap-4'`, `'items-center'` - Flexbox utilities
- `'bg-blue-grey-9'` - Background colors

## Plotly Charts
```python
import plotly.graph_objects as go

# IMPORTANT: Convert Timestamps to strings to avoid serialization errors
df_plot = df.copy()
df_plot.index = df_plot.index.astype(str)

fig = go.Figure(data=[go.Candlestick(
    x=df_plot.index,  # Use string index
    open=df_plot['open'],
    high=df_plot['high'],
    low=df_plot['low'],
    close=df_plot['close']
)])

ui.plotly(fig).classes('w-full')
```

# Key Rules

- Pass `app_state` to all render functions
- Use `ui.navigate.reload()` after state changes to refresh the page
- Convert pandas Timestamps to strings before passing to Plotly
- Keep view files lightweight - just compose components
- Use domain-organized component structure
- Don't create unnecessary documentation
- Use NiceGUI's Quasar classes for styling

# Running the Application

```bash
python main.py
# Available at http://localhost:8080
```
