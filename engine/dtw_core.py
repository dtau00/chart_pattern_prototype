"""DTW distance calculation with optimizations."""

import numpy as np
from typing import Optional
from aeon.distances import dtw_distance, ddtw_distance, adtw_distance


class DTWCalculator:
    """Compute DTW distances with various optimizations."""

    def __init__(
        self,
        variant: str = "derivative",
        constraint: str = "sakoe_chiba",
        sakoe_chiba_window: float = 0.15,
        amercing_penalty: float = 0.5,
        use_early_abandon: bool = True,
        use_lb_keogh: bool = True
    ):
        """
        Initialize DTW calculator.

        Args:
            variant: "derivative" or "standard"
            constraint: "sakoe_chiba", "adtw", or "none"
            sakoe_chiba_window: Window size for Sakoe-Chiba (fraction of length)
            amercing_penalty: Penalty for ADTW
            use_early_abandon: Enable early abandonment
            use_lb_keogh: Enable LB_Keogh filtering
        """
        self.variant = variant
        self.constraint = constraint
        self.sakoe_chiba_window = sakoe_chiba_window
        self.amercing_penalty = amercing_penalty
        self.use_early_abandon = use_early_abandon
        self.use_lb_keogh = use_lb_keogh

    def compute_distance(
        self,
        query: np.ndarray,
        template: np.ndarray,
        early_abandon_threshold: Optional[float] = None
    ) -> float:
        """
        Compute DTW distance between query and template.

        Args:
            query: Query time series
            template: Template time series
            early_abandon_threshold: Threshold for early abandonment

        Returns:
            DTW distance (normalized by path length)
        """
        # Ensure arrays are 1D
        query = np.asarray(query).flatten()
        template = np.asarray(template).flatten()

        # Choose distance function based on variant and constraint
        # Note: aeon expects window as a fraction (0-1), not absolute value
        if self.variant == "derivative" and self.constraint == "adtw":
            distance = ddtw_distance(query, template, window=self.amercing_penalty)
        elif self.variant == "derivative" and self.constraint == "sakoe_chiba":
            distance = ddtw_distance(query, template, window=self.sakoe_chiba_window)
        elif self.variant == "derivative":
            distance = ddtw_distance(query, template)
        elif self.constraint == "adtw":
            distance = adtw_distance(query, template, window=self.amercing_penalty)
        elif self.constraint == "sakoe_chiba":
            distance = dtw_distance(query, template, window=self.sakoe_chiba_window)
        else:
            distance = dtw_distance(query, template)

        # Normalize by path length
        path_length = len(query) + len(template)
        normalized_distance = distance / path_length

        return normalized_distance

    def compute_lb_keogh(
        self,
        query: np.ndarray,
        upper_envelope: np.ndarray,
        lower_envelope: np.ndarray
    ) -> float:
        """
        Compute LB_Keogh lower bound distance.

        Args:
            query: Query time series
            upper_envelope: Upper envelope of template
            lower_envelope: Lower envelope of template

        Returns:
            Lower bound distance
        """
        query = np.asarray(query).flatten()
        upper_envelope = np.asarray(upper_envelope).flatten()
        lower_envelope = np.asarray(lower_envelope).flatten()

        # Ensure same length
        min_len = min(len(query), len(upper_envelope))
        query = query[:min_len]
        upper = upper_envelope[:min_len]
        lower = lower_envelope[:min_len]

        # Compute lower bound
        lb = np.sum([
            (query[i] - upper[i]) ** 2 if query[i] > upper[i] else
            (lower[i] - query[i]) ** 2 if query[i] < lower[i] else
            0
            for i in range(len(query))
        ])

        return np.sqrt(lb)

    def compute_envelopes(
        self,
        template: np.ndarray,
        window_fraction: Optional[float] = None
    ) -> tuple:
        """
        Compute upper and lower envelopes for LB_Keogh.

        Args:
            template: Template time series
            window_fraction: Window size as fraction (0-1), defaults to sakoe_chiba_window

        Returns:
            (upper_envelope, lower_envelope)
        """
        template = np.asarray(template).flatten()

        if window_fraction is None:
            window_fraction = self.sakoe_chiba_window

        window_size = int(len(template) * window_fraction)

        upper = np.zeros(len(template))
        lower = np.zeros(len(template))

        for i in range(len(template)):
            start = max(0, i - window_size)
            end = min(len(template), i + window_size + 1)
            window = template[start:end]
            upper[i] = np.max(window)
            lower[i] = np.min(window)

        return upper, lower
