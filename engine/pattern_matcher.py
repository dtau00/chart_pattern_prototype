"""KNN-based pattern matching with confidence scoring."""

import numpy as np
from typing import List, Optional
from collections import defaultdict

from models.match_result import MatchResult
from .pattern_library import PatternLibrary
from .dtw_core import DTWCalculator
from .confidence import ConfidenceScorer


class PatternMatcher:
    """DTW + KNN pattern matching with confidence scoring."""

    def __init__(
        self,
        library: PatternLibrary,
        dtw_calculator: DTWCalculator,
        confidence_scorer: ConfidenceScorer,
        k: int = 5,
        use_lb_keogh: bool = True
    ):
        """
        Initialize pattern matcher.

        Args:
            library: Pattern library
            dtw_calculator: DTW calculator
            confidence_scorer: Confidence scorer
            k: Number of nearest neighbors
            use_lb_keogh: Whether to use LB_Keogh filtering
        """
        self.library = library
        self.dtw_calculator = dtw_calculator
        self.confidence_scorer = confidence_scorer
        self.k = k
        self.use_lb_keogh = use_lb_keogh

    def find_matches(
        self,
        query: np.ndarray,
        min_confidence: float = 0.7
    ) -> List[MatchResult]:
        """
        Find k-nearest pattern templates for query.

        Args:
            query: Query pattern (normalized)
            min_confidence: Minimum confidence threshold

        Returns:
            List of matches sorted by confidence (highest first)
        """
        # Rebuild index if dirty
        if self.library.index_dirty:
            self.library.build_index()

        # Step 1: LB_Keogh filtering (if enabled)
        candidates = self._filter_candidates_lb_keogh(query)

        if not candidates:
            return []

        # Step 2: Compute DTW distances for remaining candidates
        distances = []
        for template in candidates:
            dist = self.dtw_calculator.compute_distance(
                query,
                template.normalized
            )

            if dist < float('inf'):
                distances.append((template, dist))

        if not distances:
            return []

        # Step 3: Sort by distance, take k-nearest
        distances.sort(key=lambda x: x[1])
        k_nearest = distances[:self.k]

        # Step 4: Distance-weighted voting
        label_votes = self._weighted_voting(k_nearest)

        # Step 5: Compute confidence scores
        matches = []
        for label, vote_weight in label_votes.items():
            confidence = self.confidence_scorer.compute_confidence(
                label=label,
                k_nearest=k_nearest,
                vote_weight=vote_weight,
                query=query
            )

            if confidence >= min_confidence:
                # Find best matching template for this label
                best_template = None
                best_distance = float('inf')
                for template, dist in k_nearest:
                    if template.label == label and dist < best_distance:
                        best_template = template
                        best_distance = dist

                matches.append(MatchResult(
                    label=label,
                    confidence=confidence,
                    nearest_neighbors=k_nearest,
                    vote_weight=vote_weight,
                    best_match_template=best_template
                ))

        matches.sort(key=lambda m: m.confidence, reverse=True)
        return matches

    def _filter_candidates_lb_keogh(
        self,
        query: np.ndarray,
        percentile: float = 0.2
    ) -> List:
        """
        Use LB_Keogh to filter out candidates.

        Args:
            query: Query pattern
            percentile: Fraction of candidates to keep

        Returns:
            List of candidate templates
        """
        if not self.use_lb_keogh or not self.library.templates:
            return list(self.library.templates.values())

        lb_distances = []
        for template in self.library.templates.values():
            if template.upper_envelope is None or template.lower_envelope is None:
                # If no envelope, include it
                lb = 0.0
            else:
                lb = self.dtw_calculator.compute_lb_keogh(
                    query,
                    template.upper_envelope,
                    template.lower_envelope
                )
            lb_distances.append((template, lb))

        # Keep top percentile closest by lower bound
        lb_distances.sort(key=lambda x: x[1])
        threshold_idx = max(1, int(len(lb_distances) * percentile))
        candidates = [t for t, _ in lb_distances[:threshold_idx]]

        return candidates

    def _weighted_voting(self, k_nearest: List[tuple]) -> dict:
        """
        Distance-weighted voting across k-nearest neighbors.

        Args:
            k_nearest: List of (template, distance) tuples

        Returns:
            Dictionary of label -> vote weight
        """
        label_weights = defaultdict(float)

        for template, distance in k_nearest:
            # Weight = 1 / (distance + epsilon)
            weight = 1.0 / (distance + 1e-6)
            label_weights[template.label] += weight

        return dict(label_weights)
