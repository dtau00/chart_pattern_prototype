"""Pattern library management with augmentation and indexing."""

import pickle
import uuid
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from models.pattern import PatternTemplate
from .preprocessor import Preprocessor
from .dtw_core import DTWCalculator


class PatternLibrary:
    """Manages collection of pattern templates."""

    def __init__(self, storage_path: Path, preprocessor: Preprocessor, dtw_calculator: DTWCalculator):
        """
        Initialize pattern library.

        Args:
            storage_path: Path to store library data
            preprocessor: Preprocessor instance
            dtw_calculator: DTW calculator instance
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.preprocessor = preprocessor
        self.dtw_calculator = dtw_calculator
        self.templates: Dict[str, PatternTemplate] = {}
        self.index_dirty = False

    def add_pattern(
        self,
        label: str,
        ohlc_data: pd.DataFrame,
        metadata: dict
    ) -> PatternTemplate:
        """
        Add new labeled pattern to library.

        Args:
            label: Pattern label/name
            ohlc_data: OHLCV data
            metadata: Additional metadata (symbol, timeframe, etc.)

        Returns:
            Created PatternTemplate
        """
        # Preprocess
        normalized = self.preprocessor.normalize_pattern(ohlc_data)

        # Compute quality score
        quality = self._compute_quality_score(ohlc_data)

        # Create template
        template = PatternTemplate(
            id=str(uuid.uuid4()),
            label=label,
            raw_data=ohlc_data,
            normalized=normalized,
            quality_score=quality,
            symbol=metadata.get('symbol', 'UNKNOWN'),
            timeframe=metadata.get('timeframe', 'UNKNOWN'),
            start_time=metadata.get('start_time', ohlc_data.index[0]),
            end_time=metadata.get('end_time', ohlc_data.index[-1]),
            bars_count=len(ohlc_data)
        )

        self.templates[template.id] = template
        self.index_dirty = True
        return template

    def augment_library(self, mirror_patterns: bool = True):
        """
        Generate augmented versions of all templates.

        Args:
            mirror_patterns: Whether to create mirrored versions
        """
        original_templates = [t for t in self.templates.values() if not t.is_augmented]

        for template in original_templates:
            if mirror_patterns:
                # Create mirrored (bearish ↔ bullish) version
                mirrored = self._create_mirror(template)
                self.templates[mirrored.id] = mirrored

        self.index_dirty = True

    def _create_mirror(self, template: PatternTemplate) -> PatternTemplate:
        """Create mirrored version of pattern (flip vertically)."""
        # Mirror the normalized data
        mirrored_normalized = -template.normalized

        # Create new label (add "_inverted" suffix if not present)
        new_label = template.label
        if "_inverted" not in new_label.lower():
            if "bullish" in new_label.lower():
                new_label = new_label.replace("bullish", "bearish").replace("Bullish", "Bearish")
            elif "bearish" in new_label.lower():
                new_label = new_label.replace("bearish", "bullish").replace("Bearish", "Bullish")
            else:
                new_label = f"{new_label}_inverted"

        # Create mirrored template
        mirrored = PatternTemplate(
            id=str(uuid.uuid4()),
            label=new_label,
            raw_data=template.raw_data.copy(),
            normalized=mirrored_normalized,
            symbol=template.symbol,
            timeframe=template.timeframe,
            start_time=template.start_time,
            end_time=template.end_time,
            bars_count=template.bars_count,
            is_augmented=True,
            augmentation_type="mirror",
            parent_id=template.id,
            quality_score=template.quality_score
        )

        return mirrored

    def build_index(self, window_fraction: Optional[float] = None):
        """
        Build LB_Keogh envelopes for all templates.

        Args:
            window_fraction: Window size as fraction (0-1), defaults to DTW window
        """
        for template in self.templates.values():
            upper, lower = self.dtw_calculator.compute_envelopes(
                template.normalized,
                window_fraction
            )
            template.upper_envelope = upper
            template.lower_envelope = lower

        self.index_dirty = False

    def get_templates_by_label(self, label: str) -> List[PatternTemplate]:
        """
        Retrieve all templates for a given label.

        Args:
            label: Pattern label

        Returns:
            List of matching templates
        """
        return [t for t in self.templates.values() if t.label == label]

    def get_all_labels(self) -> List[str]:
        """Get list of all unique labels."""
        labels = []
        for t in self.templates.values():
            # Handle case where label might be corrupted/wrong type
            if isinstance(t.label, str):
                labels.append(t.label)
            elif isinstance(t.label, dict):
                # Try to extract label from dict if it's stored that way
                labels.append(t.label.get('label', str(t.label)))
            else:
                labels.append(str(t.label))
        return sorted(set(labels))

    def get_template_count(self) -> int:
        """Get total number of templates."""
        return len(self.templates)

    def save(self):
        """Persist library to disk."""
        library_file = self.storage_path / "library.pkl"
        with open(library_file, "wb") as f:
            pickle.dump(self.templates, f)

    def load(self):
        """Load library from disk."""
        library_file = self.storage_path / "library.pkl"
        if library_file.exists():
            with open(library_file, "rb") as f:
                self.templates = pickle.load(f)
            self.index_dirty = True
        else:
            self.templates = {}

    def _compute_quality_score(self, ohlc_data: pd.DataFrame) -> float:
        """
        Rate pattern quality based on:
        - Smoothness (low noise)
        - Data completeness (no gaps)

        Args:
            ohlc_data: OHLCV data

        Returns:
            Quality score (0-1)
        """
        scores = []

        # 1. Smoothness score (inverse of volatility)
        returns = ohlc_data['close'].pct_change()
        smoothness = 1.0 / (1.0 + returns.std())
        scores.append(smoothness)

        # 2. Completeness (assume no missing bars for now)
        completeness = 1.0
        scores.append(completeness)

        return np.mean(scores)
