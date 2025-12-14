# components/tab_download.py
import streamlit as st
from components.histdata_downloader import HistDataDownloader


def render_download_tab():
    """Renders the content for the Download Data tab."""
    st.header("Download OHLCV Data")
    st.info("Source: components/tab_download.py")

    # Initialize downloader
    if 'downloader' not in st.session_state:
        st.session_state.downloader = HistDataDownloader(data_dir="./data")

    downloader = st.session_state.downloader

    st.markdown("""
    Download historical OHLCV (Open, High, Low, Close, Volume) data from **HistData.com**.
    Data is downloaded as monthly CSV files, then combined and compressed into Parquet format for efficient storage and analysis.

    **Available on HistData.com:** 48 Forex pairs, 10 Stock Indices, 5 Precious Metals, 2 Oil commodities (66 total instruments)
    """)

    # Selection controls
    col1, col2, col3 = st.columns(3)

    with col1:
        symbol = st.selectbox(
            "Select Symbol",
            options=downloader.SUPPORTED_SYMBOLS,
            help="Choose a symbol: 48 Forex pairs, 10 Indices, 5 Precious Metals, 2 Oil commodities"
        )

    with col2:
        timeframe = st.selectbox(
            "Select Timeframe",
            options=list(downloader.SUPPORTED_TIMEFRAMES.keys()),
            help="Choose the timeframe for the data"
        )

    with col3:
        years = st.number_input(
            "Years to Download",
            min_value=1,
            max_value=20,
            value=10,
            help="Number of years to download (from current date backwards)"
        )

    # Display information
    st.divider()

    col_info1, col_info2 = st.columns(2)

    with col_info1:
        st.metric("Selected Symbol", symbol)
        st.metric("Timeframe", timeframe)

    with col_info2:
        st.metric("Years", years)
        st.metric("Approx. Months", years * 12)

    # Download button
    st.divider()

    if st.button("Start Download", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()

        def progress_callback(current, total, message):
            """Update progress bar and status text."""
            progress = current / total if total > 0 else 0
            progress_bar.progress(progress)
            status_text.text(message)

        with st.spinner(f"Downloading {symbol} {timeframe} data..."):
            success, message = downloader.download_symbol_timeframe(
                symbol=symbol,
                timeframe=timeframe,
                years=years,
                progress_callback=progress_callback
            )

        progress_bar.empty()
        status_text.empty()

        if success:
            st.success(message)
            st.balloons()
        else:
            st.error(message)

    # Warning about HistData.com limitations
    st.warning("""
    **Important**: HistData.com may have limitations or require authentication for automated downloads.
    This implementation provides the framework, but you may need to adjust the download URLs or
    add authentication tokens based on HistData.com's current API/website structure.
    """)
