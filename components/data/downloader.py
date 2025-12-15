# components/histdata_downloader.py
"""
HistData.com downloader utility for OHLCV data.
Downloads monthly CSV files and converts them to Parquet format.
"""
import os
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import requests
from bs4 import BeautifulSoup
import pandas as pd


class HistDataDownloader:
    """
    Downloads OHLCV data from HistData.com and manages local storage.
    """

    # Supported symbols on HistData.com
    # Note: These are the actual symbols available on HistData.com as of 2025
    # HistData.com uses format like "EURUSD" for forex, "SPXUSD" for indices, "XAUUSD" for metals

    # Forex Currency Pairs (48 pairs available on HistData.com)
    FOREX_PAIRS = [
        # Major pairs
        "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD",
        # Minor and Cross pairs
        "EURGBP", "EURJPY", "EURCHF", "EURCAD", "EURAUD", "EURNZD",
        "GBPJPY", "GBPCHF", "GBPCAD", "GBPAUD", "GBPNZD",
        "AUDJPY", "AUDCHF", "AUDCAD", "AUDNZD",
        "NZDJPY", "NZDCHF", "NZDCAD",
        "CADJPY", "CADCHF", "CHFJPY",
        # Exotic pairs
        "USDMXN", "USDHKD", "USDNOK", "USDTRY", "USDHUF", "USDPLN",
        "USDZAR", "USDDKK", "USDSGD", "USDCZK", "USDSEK",
        "EURCZK", "EURDKK", "EURHUF", "EURNOK", "EURPLN", "EURSEK", "EURTRYR",
        "ZARJPY", "SGDJPY"
    ]

    # Stock Indices (10 indices available on HistData.com)
    # HistData.com format: SPX/USD, NSX/USD, etc.
    INDICES = [
        "SPXUSD",  # S&P 500
        "NSXUSD",  # Nasdaq 100
        "JPXJPY",  # Nikkei 225
        "FRXEUR",  # French CAC 40
        "UDXUSD",  # US Dollar Index
        "UKXGBP",  # FTSE 100
        "GRXEUR",  # DAX 30
        "AUXAUD",  # ASX 200
        "HKXHKD",  # Hang Seng
        "ETXEUR",  # Eurostoxx 50
    ]

    # Commodities (2 oil products available on HistData.com)
    COMMODITIES = [
        "WTIUSD",  # West Texas Intermediate Crude Oil
        "BCOUSD",  # Brent Crude Oil
    ]

    # Precious Metals (5 metals available on HistData.com)
    PRECIOUS_METALS = [
        "XAUUSD",  # Gold/USD
        "XAUAUD",  # Gold/AUD
        "XAUCHF",  # Gold/CHF
        "XAUGBP",  # Gold/GBP
        "XAGUSD",  # Silver/USD
    ]

    # All supported symbols combined (66 total instruments)
    SUPPORTED_SYMBOLS = FOREX_PAIRS + INDICES + COMMODITIES + PRECIOUS_METALS

    # Supported timeframes on HistData.com
    SUPPORTED_TIMEFRAMES = {
        "M1": "TICK_DATA",  # 1 minute
        "M5": "TICK_DATA",  # 5 minute (needs aggregation)
        "M15": "TICK_DATA", # 15 minute (needs aggregation)
        "H1": "TICK_DATA",  # 1 hour (needs aggregation)
    }

    BASE_URL = "http://www.histdata.com/download-free-forex-historical-data/"

    def __init__(self, data_dir: str = "./data"):
        """
        Initialize the downloader.

        Args:
            data_dir: Base directory for storing data
        """
        self.data_dir = Path(data_dir)
        self.downloads_dir = self.data_dir / "downloads"
        self.parquet_dir = self.data_dir / "parquet"

        # Create directories if they don't exist
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        self.parquet_dir.mkdir(parents=True, exist_ok=True)

    def get_download_url(self, symbol: str, timeframe: str, year: int, month: int) -> str:
        """
        Construct the download URL for a specific symbol, timeframe, and month.

        Args:
            symbol: Trading pair symbol (e.g., "EURUSD")
            timeframe: Timeframe (e.g., "M1")
            year: Year (e.g., 2024)
            month: Month (1-12)

        Returns:
            Download URL string
        """
        # HistData.com URL pattern (this is simplified and may need adjustment)
        # Actual URLs may require session tokens or form submissions
        month_str = f"{month:02d}"
        filename = f"{symbol}_{timeframe}_{year}_{month_str}.zip"
        url = f"{self.BASE_URL}?/ascii/tick-data-quotes/{symbol.lower()}/{year}/{month_str}"
        return url

    def download_month(self, symbol: str, timeframe: str, year: int, month: int) -> Optional[Path]:
        """
        Download data for a specific month from HistData.com.

        HistData.com requires a two-step process:
        1. GET the download page with the symbol/year/month
        2. Submit the form to get the actual ZIP file

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe
            year: Year
            month: Month

        Returns:
            Path to downloaded ZIP file, or None if download failed
        """
        if symbol not in self.SUPPORTED_SYMBOLS:
            raise ValueError(f"Symbol {symbol} not supported")

        if timeframe not in self.SUPPORTED_TIMEFRAMES:
            raise ValueError(f"Timeframe {timeframe} not supported")

        # Create filename for downloaded zip
        filename = f"{symbol}_{timeframe}_{year}_{month:02d}.zip"
        zip_path = self.downloads_dir / filename

        # Skip if already downloaded and is a valid ZIP
        if zip_path.exists():
            try:
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    pass  # Just test if it's valid
                return zip_path
            except zipfile.BadZipFile:
                # Invalid zip, delete and re-download
                zip_path.unlink()

        # Step 1: Get the download page
        page_url = self.get_download_url(symbol, timeframe, year, month)

        try:
            session = requests.Session()

            # Set proper headers to avoid bot detection
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'http://www.histdata.com/download-free-forex-historical-data/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            })

            # Get the download page
            page_response = session.get(page_url, timeout=30)
            page_response.raise_for_status()

            # Parse the page to find the download form
            soup = BeautifulSoup(page_response.content, 'html.parser')

            # Find the form with name="file_down" or id containing "download"
            form = soup.find('form', {'name': 'file_down'}) or soup.find('form', id=lambda x: x and 'download' in x.lower())

            if not form:
                print(f"No download form found for {filename}")
                return None

            # Get form action and method
            form_action = form.get('action', '')
            form_method = form.get('method', 'post').lower()

            # Build the form data
            form_data = {}
            for input_tag in form.find_all('input'):
                input_name = input_tag.get('name')
                input_value = input_tag.get('value', '')
                if input_name:
                    form_data[input_name] = input_value

            # Submit the form to get the actual download
            if form_action.startswith('http'):
                download_url = form_action
            else:
                # Relative URL - construct full URL
                from urllib.parse import urljoin
                download_url = urljoin(page_url, form_action)

            if form_method == 'post':
                download_response = session.post(download_url, data=form_data, timeout=60)
            else:
                download_response = session.get(download_url, params=form_data, timeout=60)

            download_response.raise_for_status()

            # Check if we got a ZIP file by examining the content
            # ZIP files start with 'PK' (0x504B)
            content = download_response.content
            if not content.startswith(b'PK'):
                content_type = download_response.headers.get('content-type', '')
                print(f"Did not receive ZIP file for {filename}, got content-type: {content_type}")
                print(f"Content starts with: {content[:50]}")
                return None

            # Save the ZIP file
            with open(zip_path, 'wb') as f:
                f.write(content)

            # Verify it's a valid ZIP
            try:
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    pass
                return zip_path
            except zipfile.BadZipFile:
                print(f"Downloaded file is not a valid ZIP: {filename}")
                zip_path.unlink()
                return None

        except requests.RequestException as e:
            print(f"Failed to download {filename}: {e}")
            return None

    def extract_csv_from_zip(self, zip_path: Path) -> Optional[Path]:
        """
        Extract CSV file from downloaded ZIP.

        Args:
            zip_path: Path to ZIP file

        Returns:
            Path to extracted CSV file, or None if extraction failed
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Get first CSV file in archive
                csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
                if not csv_files:
                    return None

                csv_filename = csv_files[0]
                extract_path = self.downloads_dir / csv_filename
                zip_ref.extract(csv_filename, self.downloads_dir)

                return extract_path

        except zipfile.BadZipFile as e:
            print(f"Failed to extract {zip_path}: {e}")
            return None

    def parse_csv_to_dataframe(self, csv_path: Path, timeframe: str) -> Optional[pd.DataFrame]:
        """
        Parse CSV file to pandas DataFrame.

        Args:
            csv_path: Path to CSV file
            timeframe: Timeframe for the data

        Returns:
            DataFrame with OHLCV data, or None if parsing failed
        """
        try:
            # HistData.com tick data CSV format (no headers):
            # DateTime (YYYYMMDD HHMMSSmmm),Bid,Ask,Volume
            df = pd.read_csv(csv_path, header=None, names=['datetime', 'bid', 'ask', 'volume'])

            # Parse datetime - format is like "20241201 170048121"
            # This is YYYYMMDD HHMMSSmmm (with milliseconds)
            df['datetime'] = pd.to_datetime(df['datetime'], format='%Y%m%d %H%M%S%f')

            # Convert tick data to OHLCV
            df = self._convert_tick_to_ohlcv(df, timeframe)

            return df

        except Exception as e:
            print(f"Failed to parse {csv_path}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _convert_tick_to_ohlcv(self, tick_df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """
        Convert tick data to OHLCV format.

        Args:
            tick_df: DataFrame with tick data (columns: datetime, bid, ask, volume)
            timeframe: Target timeframe

        Returns:
            DataFrame with OHLCV data indexed by datetime
        """
        # Set datetime as index if not already
        if 'datetime' in tick_df.columns:
            tick_df = tick_df.set_index('datetime')

        # Use mid price between bid and ask
        tick_df['price'] = (tick_df['bid'] + tick_df['ask']) / 2

        # Resample based on timeframe
        timeframe_map = {
            'M1': '1min',
            'M5': '5min',
            'M15': '15min',
            'H1': '1h'
        }
        freq = timeframe_map.get(timeframe, '1min')

        # Create OHLCV by resampling
        ohlcv = tick_df['price'].resample(freq).ohlc()
        ohlcv['volume'] = tick_df['price'].resample(freq).count()

        return ohlcv

    def combine_and_save_parquet(self, symbol: str, timeframe: str, dataframes: List[pd.DataFrame]) -> Path:
        """
        Combine multiple DataFrames and save as Parquet.

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe
            dataframes: List of DataFrames to combine

        Returns:
            Path to saved Parquet file
        """
        # Combine all dataframes
        combined_df = pd.concat(dataframes, ignore_index=False)
        combined_df = combined_df.sort_index()

        # Remove duplicates
        combined_df = combined_df[~combined_df.index.duplicated(keep='first')]

        # Save as Parquet
        parquet_filename = f"{symbol}_{timeframe}.parquet"
        parquet_path = self.parquet_dir / parquet_filename

        combined_df.to_parquet(parquet_path, compression='gzip')

        return parquet_path

    def download_symbol_timeframe(
        self,
        symbol: str,
        timeframe: str,
        years: int = 10,
        progress_callback: Optional[callable] = None
    ) -> Tuple[bool, str]:
        """
        Download all available data for a symbol and timeframe.

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe
            years: Number of years to download (from current date backwards)
            progress_callback: Optional callback function for progress updates

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years * 365)

            dataframes = []
            zip_files_to_cleanup = []  # Track ZIP files for cleanup after successful save
            current_date = start_date

            total_months = years * 12
            processed_months = 0

            while current_date <= end_date:
                year = current_date.year
                month = current_date.month

                if progress_callback:
                    progress_callback(processed_months, total_months, f"Downloading {symbol} {timeframe} {year}-{month:02d}")

                # Download month
                zip_path = self.download_month(symbol, timeframe, year, month)

                if zip_path:
                    # Extract CSV
                    csv_path = self.extract_csv_from_zip(zip_path)

                    if csv_path:
                        # Parse to DataFrame
                        df = self.parse_csv_to_dataframe(csv_path, timeframe)

                        if df is not None:
                            dataframes.append(df)
                            zip_files_to_cleanup.append(zip_path)  # Mark for cleanup

                        # Clean up CSV
                        csv_path.unlink(missing_ok=True)

                # Move to next month
                current_date = current_date + timedelta(days=32)
                current_date = current_date.replace(day=1)
                processed_months += 1

            if not dataframes:
                return False, f"No data downloaded for {symbol} {timeframe}"

            # Combine and save as Parquet
            parquet_path = self.combine_and_save_parquet(symbol, timeframe, dataframes)

            # Clean up ZIP files now that data is safely saved to Parquet
            for zip_path in zip_files_to_cleanup:
                zip_path.unlink(missing_ok=True)

            return True, f"Successfully downloaded and saved to {parquet_path}"

        except Exception as e:
            return False, f"Error downloading {symbol} {timeframe}: {str(e)}"

    def get_available_data(self) -> List[Dict[str, any]]:
        """
        Get list of all available data files.

        Returns:
            List of dictionaries with info about each data file
        """
        data_files = []

        for parquet_file in self.parquet_dir.glob("*.parquet"):
            # Parse filename: SYMBOL_TIMEFRAME.parquet
            parts = parquet_file.stem.split("_")
            if len(parts) >= 2:
                symbol = parts[0]
                timeframe = parts[1]

                # Get file info
                stat = parquet_file.stat()
                size_mb = stat.st_size / (1024 * 1024)
                modified = datetime.fromtimestamp(stat.st_mtime)

                # Read parquet to get date range
                try:
                    df = pd.read_parquet(parquet_file)
                    start_date = df.index.min()
                    end_date = df.index.max()
                    rows = len(df)
                except Exception:
                    start_date = None
                    end_date = None
                    rows = 0

                data_files.append({
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "filename": parquet_file.name,
                    "path": parquet_file,
                    "size_mb": round(size_mb, 2),
                    "modified": modified,
                    "start_date": start_date,
                    "end_date": end_date,
                    "rows": rows
                })

        return data_files

    def update_data(
        self,
        symbol: str,
        timeframe: str,
        progress_callback: Optional[callable] = None
    ) -> Tuple[bool, str]:
        """
        Update existing data with the latest available data.

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe
            progress_callback: Optional callback function for progress updates

        Returns:
            Tuple of (success: bool, message: str)
        """
        parquet_filename = f"{symbol}_{timeframe}.parquet"
        parquet_path = self.parquet_dir / parquet_filename

        if not parquet_path.exists():
            return False, f"No existing data found for {symbol} {timeframe}"

        try:
            # Load existing data
            existing_df = pd.read_parquet(parquet_path)
            last_date = existing_df.index.max()

            # Download from last_date to now
            current_date = last_date + timedelta(days=1)
            end_date = datetime.now()

            dataframes = [existing_df]

            while current_date <= end_date:
                year = current_date.year
                month = current_date.month

                if progress_callback:
                    progress_callback(0, 1, f"Updating {symbol} {timeframe} {year}-{month:02d}")

                # Download month
                zip_path = self.download_month(symbol, timeframe, year, month)

                if zip_path:
                    csv_path = self.extract_csv_from_zip(zip_path)

                    if csv_path:
                        df = self.parse_csv_to_dataframe(csv_path, timeframe)

                        if df is not None:
                            # Only keep data newer than what we have
                            df = df[df.index > last_date]
                            if not df.empty:
                                dataframes.append(df)

                        csv_path.unlink(missing_ok=True)

                # Move to next month
                current_date = current_date + timedelta(days=32)
                current_date = current_date.replace(day=1)

            # Combine and save
            updated_path = self.combine_and_save_parquet(symbol, timeframe, dataframes)

            return True, f"Successfully updated {symbol} {timeframe}"

        except Exception as e:
            return False, f"Error updating {symbol} {timeframe}: {str(e)}"
