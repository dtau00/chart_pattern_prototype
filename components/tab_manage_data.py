# components/tab_manage_data.py
import streamlit as st
import pandas as pd
from components.histdata_downloader import HistDataDownloader


def render_manage_data_tab():
    """Renders the content for the Manage Data tab."""
    st.header("Manage Downloaded Data")
    st.info("Source: components/tab_manage_data.py")

    # Initialize downloader
    if 'downloader' not in st.session_state:
        st.session_state.downloader = HistDataDownloader(data_dir="./data")

    downloader = st.session_state.downloader

    st.markdown("""
    View and manage all downloaded OHLCV data files. You can update existing datasets with the latest data.
    """)

    # Refresh button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 Refresh List", use_container_width=True):
            st.rerun()

    # Get available data
    available_data = downloader.get_available_data()

    if not available_data:
        st.warning("No data files found. Please download data first using the 'Download Data' tab.")
        return

    st.divider()
    st.subheader(f"Available Data Files ({len(available_data)})")

    # Convert to DataFrame for display
    df = pd.DataFrame(available_data)

    # Display summary metrics
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)

    with col_m1:
        st.metric("Total Files", len(available_data))

    with col_m2:
        total_size = df['size_mb'].sum()
        st.metric("Total Size (MB)", f"{total_size:.2f}")

    with col_m3:
        unique_symbols = df['symbol'].nunique()
        st.metric("Unique Symbols", unique_symbols)

    with col_m4:
        total_rows = df['rows'].sum()
        st.metric("Total Rows", f"{total_rows:,}")

    st.divider()

    # Display data table with action buttons
    for idx, data_file in enumerate(available_data):
        with st.container():
            col_symbol, col_tf, col_info, col_actions = st.columns([2, 1, 3, 2])

            with col_symbol:
                st.markdown(f"**{data_file['symbol']}**")

            with col_tf:
                st.markdown(f"`{data_file['timeframe']}`")

            with col_info:
                if data_file['start_date'] and data_file['end_date']:
                    st.caption(f"📅 {data_file['start_date'].strftime('%Y-%m-%d')} to {data_file['end_date'].strftime('%Y-%m-%d')}")
                    st.caption(f"📊 {data_file['rows']:,} rows | 💾 {data_file['size_mb']} MB")
                else:
                    st.caption(f"💾 {data_file['size_mb']} MB")

            with col_actions:
                col_update, col_delete = st.columns(2)

                with col_update:
                    if st.button("🔄 Update", key=f"update_{idx}", use_container_width=True):
                        with st.spinner(f"Updating {data_file['symbol']} {data_file['timeframe']}..."):
                            progress_bar = st.progress(0)
                            status_text = st.empty()

                            def progress_callback(current, total, message):
                                """Update progress bar and status text."""
                                if total > 0:
                                    progress_bar.progress(current / total)
                                status_text.text(message)

                            success, message = downloader.update_data(
                                symbol=data_file['symbol'],
                                timeframe=data_file['timeframe'],
                                progress_callback=progress_callback
                            )

                            progress_bar.empty()
                            status_text.empty()

                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)

                with col_delete:
                    if st.button("🗑️ Delete", key=f"delete_{idx}", use_container_width=True):
                        # Confirm deletion
                        if st.session_state.get(f'confirm_delete_{idx}', False):
                            try:
                                data_file['path'].unlink()
                                st.success(f"Deleted {data_file['filename']}")
                                st.session_state[f'confirm_delete_{idx}'] = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting file: {e}")
                        else:
                            st.session_state[f'confirm_delete_{idx}'] = True
                            st.warning("Click Delete again to confirm")

            st.divider()

    # Data preview section
    st.subheader("Preview Data")

    if available_data:
        preview_options = [f"{d['symbol']} - {d['timeframe']}" for d in available_data]
        selected_preview = st.selectbox("Select data to preview", preview_options)

        if selected_preview:
            # Parse selection
            symbol, timeframe = selected_preview.split(" - ")

            # Find the data file
            selected_file = next((d for d in available_data if d['symbol'] == symbol and d['timeframe'] == timeframe), None)

            if selected_file:
                try:
                    # Load and display preview
                    df_preview = pd.read_parquet(selected_file['path'])

                    st.markdown(f"**Preview of {symbol} {timeframe}**")
                    st.markdown(f"Total rows: {len(df_preview):,}")

                    # Display first and last few rows
                    col_head, col_tail = st.columns(2)

                    with col_head:
                        st.markdown("**First 10 rows:**")
                        st.dataframe(df_preview.head(10), use_container_width=True)

                    with col_tail:
                        st.markdown("**Last 10 rows:**")
                        st.dataframe(df_preview.tail(10), use_container_width=True)

                    # Basic statistics
                    st.markdown("**Statistics:**")
                    st.dataframe(df_preview.describe(), use_container_width=True)

                except Exception as e:
                    st.error(f"Error loading data: {e}")
