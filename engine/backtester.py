"""Backtesting and cross-validation for pattern recognition."""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from collections import defaultdict
from sklearn.model_selection import LeaveOneOut, KFold
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support

from .pattern_library import PatternLibrary
from .pattern_matcher import PatternMatcher
from models.pattern import PatternTemplate


class Backtester:
    """Backtesting and validation for pattern recognition system."""

    def __init__(self, library: PatternLibrary, matcher: PatternMatcher):
        """
        Initialize backtester.

        Args:
            library: Pattern library
            matcher: Pattern matcher
        """
        self.library = library
        self.matcher = matcher

    def cross_validate(
        self,
        min_confidence: float = 0.7,
        cv_folds: int = 5,
        exclude_augmented: bool = True
    ) -> Dict:
        """
        Perform k-fold cross-validation on pattern library.

        Args:
            min_confidence: Minimum confidence threshold
            cv_folds: Number of cross-validation folds
            exclude_augmented: Whether to exclude augmented patterns from validation

        Returns:
            Dictionary with validation metrics
        """
        # Get templates (optionally exclude augmented)
        templates = [
            t for t in self.library.templates.values()
            if not (exclude_augmented and t.is_augmented)
        ]

        if len(templates) < 2:
            return {
                'error': 'Need at least 2 templates for cross-validation',
                'template_count': len(templates)
            }

        # Prepare data
        X = [t.normalized for t in templates]  # Keep as list to avoid dtype issues
        y = np.array([t.label for t in templates])
        template_ids = [t.id for t in templates]

        # Choose validation strategy
        if len(templates) <= 10:
            cv = LeaveOneOut()
            cv_name = "Leave-One-Out"
        else:
            cv = KFold(n_splits=min(cv_folds, len(templates)), shuffle=True, random_state=42)
            cv_name = f"{cv_folds}-Fold"

        # Perform cross-validation
        y_true = []
        y_pred = []
        y_conf = []

        for train_idx, test_idx in cv.split(X):
            # Create temporary library with only training templates
            temp_library_templates = {
                template_ids[i]: templates[i]
                for i in train_idx
            }

            # Temporarily swap library templates
            original_templates = self.library.templates
            self.library.templates = temp_library_templates
            self.library.index_dirty = True

            # Test on held-out template
            for idx in test_idx:
                query = X[idx]
                true_label = y[idx]

                matches = self.matcher.find_matches(query, min_confidence=0.0)

                if matches and matches[0].confidence >= min_confidence:
                    predicted_label = matches[0].label
                    confidence = matches[0].confidence
                else:
                    predicted_label = "NO_MATCH"
                    confidence = 0.0

                y_true.append(true_label)
                y_pred.append(predicted_label)
                y_conf.append(confidence)

            # Restore original library
            self.library.templates = original_templates
            self.library.index_dirty = True

        # Calculate metrics
        results = self._calculate_metrics(y_true, y_pred, y_conf, min_confidence)
        results['cv_strategy'] = cv_name
        results['template_count'] = len(templates)
        results['min_confidence'] = min_confidence

        return results

    def test_confidence_thresholds(
        self,
        thresholds: List[float] = None,
        exclude_augmented: bool = True
    ) -> pd.DataFrame:
        """
        Test multiple confidence thresholds to find optimal precision/recall tradeoff.

        Args:
            thresholds: List of confidence thresholds to test
            exclude_augmented: Whether to exclude augmented patterns

        Returns:
            DataFrame with metrics for each threshold
        """
        if thresholds is None:
            thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]

        results = []
        for threshold in thresholds:
            metrics = self.cross_validate(
                min_confidence=threshold,
                exclude_augmented=exclude_augmented
            )
            if 'error' not in metrics:
                results.append({
                    'threshold': threshold,
                    'accuracy': metrics['accuracy'],
                    'precision': metrics['macro_precision'],
                    'recall': metrics['macro_recall'],
                    'f1': metrics['macro_f1'],
                    'matched_rate': metrics['matched_rate']
                })

        return pd.DataFrame(results)

    def get_confusion_matrix(
        self,
        min_confidence: float = 0.7,
        exclude_augmented: bool = True
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Generate confusion matrix for current library.

        Args:
            min_confidence: Minimum confidence threshold
            exclude_augmented: Whether to exclude augmented patterns

        Returns:
            (confusion_matrix, labels)
        """
        # Run cross-validation to get predictions
        templates = [
            t for t in self.library.templates.values()
            if not (exclude_augmented and t.is_augmented)
        ]

        X = [t.normalized for t in templates]  # Keep as list to avoid dtype issues
        y = np.array([t.label for t in templates])
        template_ids = [t.id for t in templates]

        y_true = []
        y_pred = []

        # Leave-one-out for confusion matrix
        for i, (query, true_label) in enumerate(zip(X, y)):
            # Create temp library without this template
            temp_templates = {
                template_ids[j]: templates[j]
                for j in range(len(templates))
                if j != i
            }

            original_templates = self.library.templates
            self.library.templates = temp_templates
            self.library.index_dirty = True

            matches = self.matcher.find_matches(query, min_confidence=0.0)

            if matches and matches[0].confidence >= min_confidence:
                predicted_label = matches[0].label
            else:
                predicted_label = "NO_MATCH"

            y_true.append(true_label)
            y_pred.append(predicted_label)

            self.library.templates = original_templates
            self.library.index_dirty = True

        # Get all unique labels
        all_labels = sorted(set(y_true + y_pred))

        # Generate confusion matrix
        cm = confusion_matrix(y_true, y_pred, labels=all_labels)

        return cm, all_labels

    def _calculate_metrics(
        self,
        y_true: List[str],
        y_pred: List[str],
        y_conf: List[float],
        min_confidence: float
    ) -> Dict:
        """Calculate classification metrics."""
        # Overall accuracy
        correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
        accuracy = correct / len(y_true) if y_true else 0.0

        # Matched rate (how many got predictions above threshold)
        matched = sum(1 for p in y_pred if p != "NO_MATCH")
        matched_rate = matched / len(y_pred) if y_pred else 0.0

        # Per-class metrics (excluding NO_MATCH)
        actual_labels = [t for t, p in zip(y_true, y_pred) if p != "NO_MATCH"]
        predicted_labels = [p for p in y_pred if p != "NO_MATCH"]

        if actual_labels and predicted_labels:
            precision, recall, f1, support = precision_recall_fscore_support(
                actual_labels,
                predicted_labels,
                average='macro',
                zero_division=0
            )
        else:
            precision = recall = f1 = 0.0

        # Average confidence
        avg_confidence = np.mean([c for c in y_conf if c > 0]) if y_conf else 0.0

        return {
            'accuracy': accuracy,
            'macro_precision': precision,
            'macro_recall': recall,
            'macro_f1': f1,
            'matched_rate': matched_rate,
            'avg_confidence': avg_confidence,
            'total_samples': len(y_true),
            'predictions': list(zip(y_true, y_pred, y_conf))
        }

    def backtest_on_data(
        self,
        ohlc_data: pd.DataFrame,
        window_size: int,
        step: int = 1,
        min_confidence: float = 0.7
    ) -> List[Dict]:
        """
        Run sliding window backtest on historical data.

        Args:
            ohlc_data: OHLCV data to scan
            window_size: Size of sliding window
            step: Step size between windows
            min_confidence: Minimum confidence threshold

        Returns:
            List of detected patterns with metadata
        """
        from .preprocessor import Preprocessor

        preprocessor = Preprocessor()
        detections = []

        for i in range(0, len(ohlc_data) - window_size + 1, step):
            window_data = ohlc_data.iloc[i:i + window_size]

            # Normalize window
            query = preprocessor.normalize_pattern(window_data)

            # Find matches
            matches = self.matcher.find_matches(query, min_confidence=min_confidence)

            if matches:
                for match in matches:
                    detections.append({
                        'start_index': i,
                        'end_index': i + window_size,
                        'start_time': window_data.index[0],
                        'end_time': window_data.index[-1],
                        'label': match.label,
                        'confidence': match.confidence,
                        'window_data': window_data
                    })

        return detections
