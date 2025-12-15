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
    on_bar_click: Optional[callable] = None
) -> None:
    """
    Create a TradingView candlestick chart with pattern highlighting.

    Args:
        df: DataFrame with OHLC data and datetime index
        start_idx: Start index of pattern region
        end_idx: End index of pattern region
        height: Chart height in pixels
        on_bar_click: Optional callback function when a bar is clicked
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
                vertLines: {{ color: '#2a2e39' }},
                horzLines: {{ color: '#2a2e39' }},
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
        }}

        // Handle click events
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

        // Fit content to view
        setTimeout(() => chart.timeScale().fitContent(), 100);
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

    # End marker
    if end_idx and end_idx > start_idx and (end_idx - 1) < len(timestamps):
        markers.append({
            'time': timestamps[end_idx - 1],
            'position': 'aboveBar',
            'color': '#f68410',
            'shape': 'arrowDown',
            'text': 'End'
        })

    return markers


