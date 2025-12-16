"""TradingView Lightweight Charts component for NiceGUI."""

from nicegui import ui
import pandas as pd
from typing import Optional
import json


def create_tradingview_chart(
    df: pd.DataFrame,
    start_idx: int = 0,
    end_idx: Optional[int] = None,
    height: int = 600,
    on_bar_click: Optional[callable] = None,
    on_context_menu: Optional[callable] = None,
    app_state: Optional[dict] = None
) -> None:
    """
    Create a TradingView candlestick chart with pattern highlighting.

    Args:
        df: DataFrame with OHLC data and datetime index
        start_idx: Start index of pattern region
        end_idx: End index of pattern region
        height: Chart height in pixels
        on_bar_click: Optional callback function when a bar is clicked
        on_context_menu: Optional callback function when a context menu item is selected
        app_state: Optional app state to persist zoom/pan position across reloads
    """
    if end_idx is None:
        end_idx = len(df)

    # Prepare candlestick data
    candlestick_data = _prepare_candlestick_data(df)
    markers = _prepare_markers(df, start_idx, end_idx)

    # Generate unique chart ID
    chart_id = f"tvChart_{id(df)}_{start_idx}"

    # Add TradingView library to head (only once)
    ui.add_head_html('''
        <script src="https://unpkg.com/lightweight-charts@4.2.3/dist/lightweight-charts.standalone.production.js"></script>
    ''')

    # Create chart container
    chart_div = ui.element('div').props(f'id="{chart_id}"').style(f'width: 100%; height: {height}px;')

    # Prepare data as JSON strings
    data_json = json.dumps(candlestick_data)
    markers_json = json.dumps(markers)

    # Get saved visible range from app_state if available
    saved_range = None
    if app_state is not None:
        saved_range = app_state.get('_chart_visible_range', None)
    saved_range_json = json.dumps(saved_range) if saved_range else 'null'

    # Create JavaScript for chart
    chart_script = f'''
    (function() {{
        const chartDiv = document.getElementById('{chart_id}');
        if (!chartDiv || typeof LightweightCharts === 'undefined') {{
            console.error('Chart div or LightweightCharts not found');
            return;
        }}

        // Create chart with dark theme
        const chart = LightweightCharts.createChart(chartDiv, {{
            width: chartDiv.clientWidth,
            height: {height},
            layout: {{
                background: {{ color: '#1e1e1e' }},
                textColor: '#d1d4dc',
            }},
            grid: {{
                vertLines: {{ visible: false }},
                horzLines: {{ visible: false }},
            }},
            crosshair: {{
                mode: LightweightCharts.CrosshairMode.Normal,
            }},
            rightPriceScale: {{
                borderColor: '#2a2e39',
            }},
            timeScale: {{
                borderColor: '#2a2e39',
                timeVisible: true,
                secondsVisible: false,
            }},
        }});

        // Add candlestick series
        const candlestickSeries = chart.addCandlestickSeries({{
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
            priceLineVisible: false,
            lastValueVisible: false,
        }});

        // Set data
        const data = {data_json};
        candlestickSeries.setData(data);

        // Add markers
        const markers = {markers_json};
        if (markers.length > 0) {{
            candlestickSeries.setMarkers(markers);
        }}

        // Add highlight region
        const highlightStart = {start_idx};
        const highlightEnd = {end_idx};

        if (highlightStart < data.length && highlightEnd <= data.length && highlightEnd > highlightStart) {{
            const startTime = data[highlightStart].time;
            const endTime = data[highlightEnd - 1].time;

            // Get price range for highlighted region
            const highlightData = data.slice(highlightStart, highlightEnd);
            const maxPrice = Math.max(...highlightData.map(d => d.high));
            const minPrice = Math.min(...highlightData.map(d => d.low));
            const priceRange = maxPrice - minPrice;

            // Add filled rectangle for highlighting (using priceLine workaround)
            const upperLine = chart.addLineSeries({{
                color: 'rgba(255, 165, 0, 0.3)',
                lineWidth: 1,
                priceLineVisible: false,
                lastValueVisible: false,
                crosshairMarkerVisible: false,
            }});

            const lowerLine = chart.addLineSeries({{
                color: 'rgba(255, 165, 0, 0.3)',
                lineWidth: 1,
                priceLineVisible: false,
                lastValueVisible: false,
                crosshairMarkerVisible: false,
            }});

            // Create box outline
            upperLine.setData([
                {{ time: startTime, value: maxPrice + priceRange * 0.02 }},
                {{ time: endTime, value: maxPrice + priceRange * 0.02 }}
            ]);

            lowerLine.setData([
                {{ time: startTime, value: minPrice - priceRange * 0.02 }},
                {{ time: endTime, value: minPrice - priceRange * 0.02 }}
            ]);

            // Add vertical line at start index
            const startBar = data[highlightStart];
            const startVerticalLine = chart.addLineSeries({{
                color: '#00ff00',
                lineWidth: 2,
                lineStyle: 2, // Dashed line
                priceLineVisible: false,
                lastValueVisible: false,
                crosshairMarkerVisible: false,
            }});

            // Create vertical line effect by drawing from min to max price at start time
            startVerticalLine.setData([
                {{ time: startTime, value: minPrice - priceRange * 0.05 }},
                {{ time: startTime, value: maxPrice + priceRange * 0.05 }}
            ]);
        }}

        // Create context menu HTML
        const contextMenu = document.createElement('div');
        contextMenu.id = '{chart_id}_contextmenu';
        contextMenu.style.cssText = `
            position: fixed;
            display: none;
            background: #2a2e39;
            border: 1px solid #434651;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            z-index: 10000;
            padding: 4px 0;
            min-width: 150px;
        `;

        const menuItems = [
            {{ label: 'Set Start Date', action: 'start_date' }},
            {{ label: 'Set End Date', action: 'end_date' }}
        ];

        menuItems.forEach(item => {{
            const menuItem = document.createElement('div');
            menuItem.textContent = item.label;
            menuItem.style.cssText = `
                padding: 8px 16px;
                cursor: pointer;
                color: #d1d4dc;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                font-size: 14px;
            `;
            menuItem.addEventListener('mouseenter', () => {{
                menuItem.style.background = '#434651';
            }});
            menuItem.addEventListener('mouseleave', () => {{
                menuItem.style.background = 'transparent';
            }});
            menuItem.dataset.action = item.action;
            contextMenu.appendChild(menuItem);
        }});

        document.body.appendChild(contextMenu);

        // Store context menu data
        let contextMenuData = null;

        // Handle right-click on chart
        chartDiv.addEventListener('contextmenu', (e) => {{
            e.preventDefault();

            // Get the position within the chart
            const rect = chartDiv.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            // Get the time at this position
            const timeScale = chart.timeScale();
            const time = timeScale.coordinateToTime(x);

            if (time) {{
                // Find the bar data
                const barIndex = data.findIndex(d => d.time === time);
                if (barIndex >= 0) {{
                    const barData = data[barIndex];

                    // Store the bar data
                    contextMenuData = {{
                        index: barData.index,
                        time: new Date(barData.time * 1000).toLocaleString(),
                        open: barData.open.toFixed(2),
                        high: barData.high.toFixed(2),
                        low: barData.low.toFixed(2),
                        close: barData.close.toFixed(2),
                        change: ((barData.close - barData.open) / barData.open * 100).toFixed(2)
                    }};

                    // Show context menu at cursor position
                    contextMenu.style.display = 'block';
                    contextMenu.style.left = e.clientX + 'px';
                    contextMenu.style.top = e.clientY + 'px';
                }}
            }}
        }});

        // Handle context menu item clicks
        contextMenu.addEventListener('click', (e) => {{
            const menuItem = e.target.closest('div[data-action]');
            if (menuItem && contextMenuData) {{
                const action = menuItem.dataset.action;

                // Send event to Python with action type
                window.dispatchEvent(new CustomEvent('tvChartContextMenu', {{
                    detail: {{
                        ...contextMenuData,
                        action: action
                    }}
                }}));

                // Hide menu
                contextMenu.style.display = 'none';
                contextMenuData = null;
            }}
        }});

        // Hide context menu when clicking elsewhere
        document.addEventListener('click', () => {{
            contextMenu.style.display = 'none';
        }});

        // Handle regular click events (left-click)
        chart.subscribeClick(param => {{
            if (!param.point || !param.time) return;

            const price = param.seriesData.get(candlestickSeries);
            if (price) {{
                const barIndex = data.findIndex(d => d.time === param.time);
                if (barIndex >= 0) {{
                    const barData = data[barIndex];

                    // Create timestamp string
                    const date = new Date(barData.time * 1000);
                    const timeStr = date.toLocaleString();

                    const eventData = {{
                        index: barData.index,
                        time: timeStr,
                        open: barData.open.toFixed(2),
                        high: barData.high.toFixed(2),
                        low: barData.low.toFixed(2),
                        close: barData.close.toFixed(2),
                        change: ((barData.close - barData.open) / barData.open * 100).toFixed(2)
                    }};

                    // Send data to Python
                    window.dispatchEvent(new CustomEvent('tvChartClick', {{
                        detail: eventData
                    }}));
                }}
            }}
        }});

        // Handle resize
        const resizeObserver = new ResizeObserver(entries => {{
            if (entries.length === 0 || entries[0].target !== chartDiv) return;
            const newRect = entries[0].contentRect;
            chart.applyOptions({{ width: newRect.width }});
        }});
        resizeObserver.observe(chartDiv);

        // Restore saved zoom/pan or fit content
        const savedRange = {saved_range_json};
        if (savedRange && savedRange.from && savedRange.to) {{
            setTimeout(() => {{
                chart.timeScale().setVisibleRange({{
                    from: savedRange.from,
                    to: savedRange.to
                }});
            }}, 100);
        }} else {{
            // Fit content to view on first load
            setTimeout(() => chart.timeScale().fitContent(), 100);
        }}

        // Save visible range when user zooms/pans
        chart.timeScale().subscribeVisibleTimeRangeChange(() => {{
            const visibleRange = chart.timeScale().getVisibleRange();
            if (visibleRange) {{
                // Send to Python to save in app_state
                window.dispatchEvent(new CustomEvent('tvChartRangeChange', {{
                    detail: {{
                        from: visibleRange.from,
                        to: visibleRange.to
                    }}
                }}));
            }}
        }});
    }})();
    '''

    # Store chart reference for later
    chart_div._props['data-chart-id'] = chart_id

    # Run the JavaScript to create the chart
    ui.run_javascript(chart_script, timeout=10.0)

    # If callback provided, create event listener
    if on_bar_click:
        event_name = f'{chart_id}_click'

        # Set up JavaScript event listener to bridge to Python
        emit_script = f'''
        window.addEventListener('tvChartClick', (event) => {{
            emitEvent('{event_name}', event.detail);
        }});
        '''
        ui.run_javascript(emit_script)

        # Attach Python event handler
        ui.on(event_name, lambda e: on_bar_click(e.args))

    # If context menu callback provided, create event listener
    if on_context_menu:
        context_event_name = f'{chart_id}_contextmenu'

        # Set up JavaScript event listener to bridge to Python
        context_emit_script = f'''
        window.addEventListener('tvChartContextMenu', (event) => {{
            emitEvent('{context_event_name}', event.detail);
        }});
        '''
        ui.run_javascript(context_emit_script)

        # Attach Python event handler
        ui.on(context_event_name, lambda e: on_context_menu(e.args))

    # If app_state provided, set up event listener to save zoom/pan position
    if app_state is not None:
        range_event_name = f'{chart_id}_range'

        # Set up JavaScript event listener to bridge to Python
        range_emit_script = f'''
        window.addEventListener('tvChartRangeChange', (event) => {{
            emitEvent('{range_event_name}', event.detail);
        }});
        '''
        ui.run_javascript(range_emit_script)

        # Attach Python event handler to save visible range
        def save_visible_range(e):
            app_state['_chart_visible_range'] = e.args

        ui.on(range_event_name, save_visible_range)


def _prepare_candlestick_data(df: pd.DataFrame):
    """Convert DataFrame to TradingView format."""
    data = []
    df_copy = df.copy()

    # Convert timestamps to Unix timestamps (seconds)
    if isinstance(df_copy.index, pd.DatetimeIndex):
        timestamps = (df_copy.index.astype(int) // 10**9).tolist()
    else:
        timestamps = list(range(len(df_copy)))

    for i, (timestamp, row) in enumerate(zip(timestamps, df_copy.itertuples())):
        data.append({
            'time': timestamp,
            'open': float(row.open),
            'high': float(row.high),
            'low': float(row.low),
            'close': float(row.close),
            'index': i
        })

    return data


def _prepare_markers(df: pd.DataFrame, start_idx: int, end_idx: Optional[int]):
    """Create markers for pattern boundaries."""
    if start_idx is None or start_idx >= len(df):
        return []

    markers = []
    timestamps = (df.index.astype(int) // 10**9).tolist()

    # Start marker
    if start_idx < len(timestamps):
        markers.append({
            'time': timestamps[start_idx],
            'position': 'aboveBar',
            'color': '#f68410',
            'shape': 'arrowDown',
            'text': 'Start'
        })

    return markers


