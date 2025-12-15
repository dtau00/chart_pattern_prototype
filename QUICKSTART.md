# Pattern Recognition System - Quick Start Guide

## Overview
This project implements a DTW (Dynamic Time Warping) + KNN pattern recognition system for identifying chart patterns in OHLCV financial data.

## Installation

1. **Install Dependencies**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Running the Application

```bash
source venv/bin/activate
streamlit run Main_App.py
```

## User Workflow

### Step 1: Download Data
1. Navigate to **Data Manager**
2. Download OHLCV data for your desired currency pairs and timeframes
3. Data is stored in `data/parquet/`

### Step 2: Label Patterns
1. Navigate to **Pattern Manager** > **Label Patterns**
2. Select a data file from the dropdown
3. Use the controls to select a pattern:
   - **Pattern Length**: Number of bars to include (default: 50)
   - **Start Index**: Where the pattern begins
   - **Pattern Label**: Name for this pattern (e.g., "head_and_shoulders", "double_top")
4. Preview the pattern in the candlestick chart
5. Optionally view the normalized pattern (DDTW representation)
6. Click **Save Pattern** to add to library

**Tips:**
- Start with clear, well-formed patterns
- Use consistent naming (e.g., "bullish_flag", "bearish_wedge")
- Aim for 20-50 examples per pattern type
- Patterns are automatically saved to `data/patterns/library.pkl`

### Step 3: Augment & Build Index
1. Navigate to **Pattern Manager** > **View Library**
2. Click **Augment Library (Mirror Patterns)**
   - Automatically creates inverted versions (bullish → bearish)
   - Doubles your training set
3. Click **Build Index (LB_Keogh)**
   - Builds fast search index for pattern matching
   - Required before scanning

### Step 4: Train & Validate (NEW)
1. Navigate to **Pattern Manager** > **Train & Validate**
2. View library statistics and pattern distribution
3. Click **Run Cross-Validation**
   - Set minimum confidence threshold (0.7 recommended)
   - Check accuracy, precision, recall, F1 score
4. Click **Generate Confusion Matrix**
   - See which patterns are confused with each other
5. Click **Test Multiple Thresholds**
   - Find optimal confidence threshold
   - View precision-recall tradeoff chart
   - Use recommended threshold for scanning

**Tips:**
- Aim for >70% accuracy before scanning
- If accuracy is low, add more training examples
- Use recommended threshold from testing

### Step 5: Scan for Patterns (NEW)
1. Navigate to **Pattern Scanner**
2. Select data file to scan
3. Configure settings:
   - **Window Size**: Match your training patterns (e.g., 50 bars)
   - **Min Confidence**: Use threshold from training (e.g., 0.75)
   - **Step Size**: 5 for balanced speed/thoroughness
4. (Optional) Filter by specific pattern labels
5. Click **🔍 Scan for Patterns**
6. Review detected patterns:
   - View statistics (total, unique patterns, avg confidence)
   - Inspect individual detections with charts
   - Analyze price action and timestamps

### Step 6: Browse Library
In the **View Library** tab, you can:
- View statistics (total patterns, unique labels, augmented count)
- Filter patterns by label
- Inspect each pattern (charts, metadata, quality score)
- Delete unwanted patterns

## Pattern Recognition Features

### DTW (Dynamic Time Warping)
- **Derivative DTW (DDTW)**: Matches patterns based on shape, not absolute price
- **Sakoe-Chiba Constraint**: Limits warping for robust matching
- **LB_Keogh Filtering**: Fast pre-filtering for real-time performance

### KNN Classification
- Distance-weighted voting (closer patterns have more influence)
- Configurable k (number of neighbors, default: 5)

### Confidence Scoring
Multi-metric confidence calculation based on:
- **Closeness** (35%): How close is the nearest match?
- **Consensus** (30%): Do neighbors agree on the label?
- **Separation** (20%): How different is the next-best label?
- **Quality** (15%): Quality score of matching templates

## Configuration

Edit `config/pattern_config.yaml` to customize:

```yaml
dtw:
  variant: "derivative"        # "derivative" or "standard"
  constraint: "sakoe_chiba"    # "sakoe_chiba", "adtw", or "none"
  sakoe_chiba_window: 0.15     # Window size (15% of sequence)

knn:
  k: 5                         # Number of neighbors

confidence:
  min_threshold: 0.7           # Default confidence threshold
```

## Testing

Run the test suite:
```bash
source venv/bin/activate
python -m pytest tests/ -v
```

## Project Structure

```
chart_pattern_prototype/
├── Main_App.py                 # Streamlit entry point
├── pages/
│   ├── data_manager_parent.py
│   ├── analysis_parent.py
│   └── pattern_manager_parent.py  # NEW: Pattern management
├── components/
│   ├── tab_label_patterns.py      # NEW: Pattern labeling UI
│   └── tab_view_library.py        # NEW: Library viewer UI
├── engine/                        # NEW: Core pattern recognition
│   ├── preprocessor.py
│   ├── dtw_core.py
│   ├── pattern_library.py
│   ├── pattern_matcher.py
│   └── confidence.py
├── models/                        # NEW: Data models
│   ├── pattern.py
│   └── match_result.py
├── config/
│   └── pattern_config.yaml        # NEW: Configuration
├── data/
│   ├── parquet/                   # OHLCV data
│   └── patterns/                  # NEW: Pattern storage
└── tests/                         # NEW: Test suite
```

## Next Steps

After completing Phases 1-4, you can extend the system with:

1. **Training & Backtesting UI** (Phase 5)
   - Cross-validation metrics
   - Hyperparameter tuning
   - Precision/recall curves

2. **Real-time Pattern Scanner** (Phase 6)
   - Live pattern detection
   - Multi-symbol monitoring
   - Alert system

3. **Advanced Features** (Phase 7)
   - Multi-dimensional OHLC matching
   - Proximity Forest ensemble
   - Pattern discovery via clustering

## Troubleshooting

**Issue**: Pattern library not loading
- **Solution**: Make sure you've saved at least one pattern first

**Issue**: Tests failing
- **Solution**: Make sure all dependencies are installed: `pip install -r requirements.txt`

**Issue**: Streamlit error on startup
- **Solution**: Check that you're in the project root directory and virtual environment is activated

## Technical Details

- **DTW Library**: Uses `aeon` (state-of-the-art time series analysis)
- **Normalization**: Z-score normalization for scale-invariance
- **Storage**: Pickle-based persistence for pattern library
- **UI Framework**: Streamlit with Plotly charts

## Support

For issues or questions:
1. Check `DESIGN_DTW_KNN.md` for design details
2. Check `IMPLEMENTATION_SUMMARY.md` for implementation status
3. Review test files for usage examples
