"""Match result data model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Tuple
import pandas as pd
import numpy as np


@dataclass
class MatchResult:
    """Result of pattern matching operation."""

    label: str
    confidence: float
    nearest_neighbors: List[Tuple[object, float]]  # (PatternTemplate, distance)
    vote_weight: float

    # Optional metadata
    timestamp: Optional[datetime] = None
    symbol: Optional[str] = None
    timeframe: Optional[str] = None

    # For visualization
    query_data: Optional[pd.DataFrame] = None
    best_match_template: Optional[object] = None  # PatternTemplate

    def to_dict(self) -> dict:
        """Serialize for storage/display."""
        return {
            'label': self.label,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'k_neighbors': len(self.nearest_neighbors),
            'avg_distance': np.mean([d for _, d in self.nearest_neighbors]) if self.nearest_neighbors else 0.0
        }
