"""Data preprocessing for pattern recognition."""

import pandas as pd
import numpy as np
from typing import Optional


class Preprocessor:
    """Transform raw OHLCV data into normalized features for DTW."""

    def __init__(self, normalization: str = "zscore"):
        """
        Initialize preprocessor.

        Args:
            normalization: Normalization method ("zscore", "minmax", or "none")
        """
        self.normalization = normalization

    def normalize_pattern(self, ohlc_data: pd.DataFrame, use_derivative: bool = True) -> np.ndarray:
        """
        Normalize pattern for DTW matching.

        Args:
            ohlc_data: DataFrame with OHLCV data
            use_derivative: Whether to use derivative DTW (DDTW)

        Returns:
            Normalized feature vector
        """
        # Step 1: Extract close prices
        prices = ohlc_data['close'].values

        # Step 2: Compute first-order derivative (for DDTW)
        if use_derivative:
            derivatives = np.diff(prices)
        else:
            derivatives = prices

        # Step 3: Apply normalization
        normalized = self._apply_normalization(derivatives)

        return normalized

    def _apply_normalization(self, data: np.ndarray) -> np.ndarray:
        """Apply normalization to data."""
        if self.normalization == "zscore":
            mean = np.mean(data)
            std = np.std(data)
            return (data - mean) / (std + 1e-8)
        elif self.normalization == "minmax":
            min_val = np.min(data)
            max_val = np.max(data)
            return (data - min_val) / (max_val - min_val + 1e-8)
        else:  # "none"
            return data

    def extract_fixed_length(self, df: pd.DataFrame, start_idx: int, length: int) -> pd.DataFrame:
        """
        Extract pattern of fixed bar count.

        Args:
            df: Source DataFrame
            start_idx: Starting index
            length: Number of bars to extract

        Returns:
            Extracted pattern
        """
        return df.iloc[start_idx : start_idx + length].copy()

    def extract_anchored(
        self,
        df: pd.DataFrame,
        breakout_idx: int,
        lookback: int,
        lookforward: int
    ) -> pd.DataFrame:
        """
        Extract pattern centered on key point (e.g., breakout).

        Args:
            df: Source DataFrame
            breakout_idx: Index of key point
            lookback: Bars before key point
            lookforward: Bars after key point

        Returns:
            Extracted pattern
        """
        start = max(0, breakout_idx - lookback)
        end = min(len(df), breakout_idx + lookforward)
        return df.iloc[start:end].copy()

    def sliding_window_extract(
        self,
        df: pd.DataFrame,
        window_size: int,
        step: int = 1
    ) -> list:
        """
        Extract multiple overlapping patterns from single dataset.

        Args:
            df: Source DataFrame
            window_size: Size of each window
            step: Step size between windows

        Returns:
            List of extracted windows
        """
        windows = []
        for i in range(0, len(df) - window_size + 1, step):
            windows.append(df.iloc[i : i + window_size].copy())
        return windows
