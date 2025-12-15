"""Confidence scoring for pattern matches."""

import numpy as np
from typing import List, Tuple
from collections import defaultdict


class ConfidenceScorer:
    """Computes confidence scores from multiple signals."""

    def __init__(
        self,
        closeness_weight: float = 0.35,
        consensus_weight: float = 0.30,
        separation_weight: float = 0.20,
        quality_weight: float = 0.15
    ):
        """
        Initialize confidence scorer.

        Args:
            closeness_weight: Weight for closeness score
            consensus_weight: Weight for consensus score
            separation_weight: Weight for separation score
            quality_weight: Weight for quality score
        """
        self.closeness_weight = closeness_weight
        self.consensus_weight = consensus_weight
        self.separation_weight = separation_weight
        self.quality_weight = quality_weight

    def compute_confidence(
        self,
        label: str,
        k_nearest: List[Tuple[object, float]],
        vote_weight: float,
        query: np.ndarray
    ) -> float:
        """
        Combine multiple confidence signals.

        Signals:
        1. Closeness: How close is the nearest match?
        2. Consensus: Do k neighbors agree on label?
        3. Separation: How far is the next-best label?
        4. Quality: How good are the matching templates?

        Args:
            label: Pattern label
            k_nearest: List of (template, distance) tuples
            vote_weight: Vote weight for this label
            query: Query pattern

        Returns:
            Confidence score (0-1)
        """
        # 1. Closeness score (inverse of nearest distance)
        nearest_distance = self._get_nearest_distance(label, k_nearest)
        closeness = 1.0 / (nearest_distance + 1e-6)
        closeness_normalized = min(closeness / 10.0, 1.0)

        # 2. Consensus score (what % of k neighbors agree?)
        label_matches = sum(1 for t, _ in k_nearest if t.label == label)
        consensus = label_matches / len(k_nearest) if k_nearest else 0.0

        # 3. Separation score (gap to next-best label)
        all_labels = set(t.label for t, _ in k_nearest)
        if len(all_labels) > 1:
            sorted_labels = sorted(
                all_labels,
                key=lambda l: self._get_label_weight(l, k_nearest),
                reverse=True
            )
            best_weight = self._get_label_weight(sorted_labels[0], k_nearest)
            second_weight = self._get_label_weight(sorted_labels[1], k_nearest)
            separation = (best_weight - second_weight) / (best_weight + 1e-6)
        else:
            separation = 1.0

        # 4. Template quality (average quality of matching neighbors)
        label_templates = [t for t, _ in k_nearest if t.label == label]
        avg_quality = np.mean([t.quality_score for t in label_templates]) if label_templates else 0.0

        # Combine scores with weights
        confidence = (
            self.closeness_weight * closeness_normalized +
            self.consensus_weight * consensus +
            self.separation_weight * separation +
            self.quality_weight * avg_quality
        )

        return confidence

    def _get_nearest_distance(
        self,
        label: str,
        k_nearest: List[Tuple[object, float]]
    ) -> float:
        """Get distance to nearest neighbor with matching label."""
        for template, distance in k_nearest:
            if template.label == label:
                return distance
        return float('inf')

    def _get_label_weight(
        self,
        label: str,
        k_nearest: List[Tuple[object, float]]
    ) -> float:
        """Get total vote weight for a label."""
        return sum(1.0 / (d + 1e-6) for t, d in k_nearest if t.label == label)
