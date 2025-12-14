# OHLCV Analysis Platform

A modular Streamlit application for downloading and analyzing OHLCV (Open, High, Low, Close, Volume) data from HistData.com.

## Features

- **Modular Architecture**: Clean separation of concerns using `st.navigation` for main pages and imported functions for tab content
- **Data Download Manager**: Download historical forex data from HistData.com with support for multiple symbols and timeframes
- **Efficient Data Storage**: Automatic conversion of monthly CSV files to compressed Parquet format
- **Data Management**: View, update, and manage downloaded datasets with a user-friendly interface
- **Comprehensive Testing**: 77 unit tests covering structure, functionality, and components

## Directory Structure

```
chart_pattern_prototype/
├── Main_App.py              # Application entrypoint and router
├── pages/                   # Main navigation pages
│   ├── analysis_parent.py   # Analysis dashboard with tabs
│   └── data_manager_parent.py  # Data management interface
├── components/              # Reusable UI components
│   ├── __init__.py
│   ├── tab_overview.py      # Overview tab component
│   ├── tab_metrics.py       # Metrics tab component
│   ├── tab_download.py      # Data download tab
│   ├── tab_manage_data.py   # Data management tab
│   └── histdata_downloader.py  # HistData.com downloader utility
├── data/                    # Data storage
│   ├── downloads/           # Temporary CSV files
│   └── parquet/             # Compressed Parquet files
├── tests/                   # Unit tests
│   ├── test_structure.py    # Project structure tests
│   ├── test_histdata_downloader.py  # Downloader tests
│   └── test_components.py   # Component tests
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Installation

1. **Clone the repository**:
   ```bash
   cd chart_pattern_prototype
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Application

Start the Streamlit application:

```bash
streamlit run Main_App.py
```

The application will open in your default web browser at `http://localhost:8501`.

### Downloading Data

1. Navigate to the **Data Manager** page
2. Select the **Download Data** tab
3. Choose:
   - **Symbol**: Forex pair (e.g., EURUSD, GBPUSD)
   - **Timeframe**: Candlestick interval (M1, M5, M15, H1)
   - **Years to Download**: Number of years of historical data
4. Click **Start Download**

Data is automatically downloaded as monthly CSV files and converted to compressed Parquet format for efficient storage and analysis.

### Managing Data

1. Navigate to the **Data Manager** page
2. Select the **Manage Data** tab
3. View all downloaded datasets with:
   - Symbol and timeframe
   - Date range
   - Number of rows
   - File size
4. Actions available:
   - **Update**: Download latest data to extend existing datasets
   - **Delete**: Remove datasets
   - **Preview**: View first/last rows and statistics

### Running Tests

Run all tests:

```bash
pytest tests/ -v
```

Run specific test files:

```bash
pytest tests/test_structure.py -v
pytest tests/test_histdata_downloader.py -v
pytest tests/test_components.py -v
```

## Supported Data

### Symbols (Forex Pairs)

- EURUSD, GBPUSD, USDJPY, USDCHF, USDCAD
- AUDUSD, NZDUSD, EURGBP, EURJPY, EURCHF
- GBPJPY, AUDJPY, AUDNZD, AUDCAD

### Timeframes

- M1 (1 minute)
- M5 (5 minutes)
- M15 (15 minutes)
- H1 (1 hour)

## Architecture

### Multi-Page Navigation

The application uses Streamlit's `st.navigation` API for main page routing:

- **Analysis Dashboard**: Example dashboard with overview and metrics tabs
- **Data Manager**: Download and manage OHLCV data

### Component-Based Tabs

Each page uses `st.tabs()` with content rendered by imported functions from the `components/` directory:

```python
# pages/data_manager_parent.py
from components.tab_download import render_download_tab
from components.tab_manage_data import render_manage_data_tab

tab1, tab2 = st.tabs(["Download Data", "Manage Data"])

with tab1:
    render_download_tab()

with tab2:
    render_manage_data_tab()
```

This approach keeps the code modular, testable, and maintainable.

## Data Processing

### Download Process

1. **Download**: Monthly CSV files from HistData.com
2. **Extract**: Unzip downloaded archives
3. **Parse**: Convert tick data to OHLCV format if needed
4. **Combine**: Merge monthly data into single DataFrame
5. **Compress**: Save as Parquet with gzip compression
6. **Cleanup**: Remove temporary CSV files

### Update Process

1. **Read**: Load existing Parquet file
2. **Identify**: Determine last available date
3. **Download**: Fetch new monthly data from last date to current
4. **Merge**: Combine new data with existing data
5. **Save**: Overwrite Parquet file with updated data

## Important Notes

### HistData.com Limitations

The downloader provides the framework for automated downloads from HistData.com, but the actual website may:

- Require authentication or API tokens
- Have rate limiting
- Change URL structures
- Require captcha solving

You may need to adjust the download URLs or implement additional authentication based on HistData.com's current requirements.

## Development

### Adding New Components

1. Create a new file in `components/` with a render function:
   ```python
   # components/my_new_tab.py
   import streamlit as st

   def render_my_new_tab():
       st.header("My New Tab")
       # Add your UI code here
   ```

2. Import and use in a parent page:
   ```python
   from components.my_new_tab import render_my_new_tab

   with tab:
       render_my_new_tab()
   ```

### Adding New Pages

1. Create a new file in `pages/`:
   ```python
   # pages/my_new_page.py
   import streamlit as st

   st.title("My New Page")
   ```

2. Add to navigation in `Main_App.py`:
   ```python
   app_pages = [
       st.Page("pages/my_new_page.py", title="My Page", icon=":material/star:"),
   ]
   ```

## Testing

The project includes comprehensive tests:

- **26 structure tests**: Verify project organization and imports
- **24 downloader tests**: Test data downloading and processing
- **27 component tests**: Verify UI component functionality

All tests use mocking to avoid external dependencies and network calls.

## License

This project is provided as-is for educational and development purposes.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request
