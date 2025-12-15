"""Pattern template data model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import pandas as pd
import numpy as np


@dataclass
class PatternTemplate:
    """Represents a single labeled pattern template."""

    id: str
    label: str
    raw_data: pd.DataFrame
    normalized: np.ndarray

    # Metadata
    symbol: str
    timeframe: str
    start_time: datetime
    end_time: datetime
    bars_count: int

    # Augmentation info
    is_augmented: bool = False
    augmentation_type: Optional[str] = None
    parent_id: Optional[str] = None

    # Quality metrics
    quality_score: float = 1.0

    # Indexing data (for LB_Keogh)
    upper_envelope: Optional[np.ndarray] = None
    lower_envelope: Optional[np.ndarray] = None

    def to_dict(self) -> dict:
        """Serialize pattern for storage."""
        return {
            'id': self.id,
            'label': self.label,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'bars_count': self.bars_count,
            'is_augmented': self.is_augmented,
            'augmentation_type': self.augmentation_type,
            'parent_id': self.parent_id,
            'quality_score': self.quality_score,
        }
