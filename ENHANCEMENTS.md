# Enhanced Stock Screening Features

## Overview
This document describes the enhancements made to the SwingTrade Stock Screener to include momentum and resistance breakout indicators with comprehensive technical analysis visualizations.

## New Features

### 1. Support and Resistance Level Calculation

The screener now automatically calculates support and resistance levels for each stock:

- **Support Level**: Minimum of low prices over the last 90 days
- **Resistance Level**: Maximum of high prices over the last 90 days
- **Relative Position**: Calculates where the current price sits between support and resistance (0.0 = at support, 1.0 = at resistance)

**Key Methods:**
- `calculate_support_resistance(hist_data, period=90)` - Calculates support and resistance levels
- `calculate_relative_position(current_price, support, resistance)` - Determines relative position (0.0 to 1.0)

### 2. Breakout Filter Detection

The screener includes comprehensive breakout filters to identify stocks with potential upward momentum:

#### Volume Spike Detection
- **Filter**: Current volume ≥ 1.5x the 20-day average volume
- **Purpose**: Identifies increased trading interest and potential breakouts

#### RSI Momentum Filter
- **Filter**: RSI between 50 and 70
- **Purpose**: Identifies stocks with good upward momentum without being overbought
- **Optimal Range**: 50-70 represents healthy upward momentum

#### MACD Momentum Filter
- **Filter**: MACD histogram > 0 OR MACD line crossing above signal line
- **Purpose**: Identifies positive momentum shifts
- **Indicators**:
  - Positive histogram = bullish momentum
  - MACD > Signal = bullish crossover

#### Position Filter
- **Filter**: Relative position between 40% and 70% of support-resistance range
- **Purpose**: Identifies stocks positioned favorably for breakouts
- **Logic**: 
  - Above 40% (not near support/oversold)
  - Below 70% (room to run before resistance)

#### Overall Breakout Signal
- **Condition**: ALL filters must pass (volume spike + RSI momentum + MACD momentum + favorable position)
- **Result**: Boolean flag indicating a comprehensive breakout signal

**Key Method:**
- `check_breakout_filters(current_price, support, resistance, volume_ratio, rsi, macd_hist, macd, macd_signal)` - Returns dictionary with all filter results

### 3. Technical Analysis Charts

A new comprehensive technical analysis chart has been added that includes:

#### Price Chart with Support/Resistance
- **Price Line**: Blue line showing historical closing prices (last 60 days)
- **Support Line**: Green dashed horizontal line at 90-day support level
- **Resistance Line**: Red dashed horizontal line at 90-day resistance level
- **Current Price**: Purple marker highlighting the most recent price

#### Volume Chart with Spike Highlighting
- **Volume Bars**: Blue bars for normal volume, red bars for volume spikes (≥1.5x average)
- **Spike Threshold Line**: Red dashed line showing 1.5x average volume threshold
- **Purpose**: Quickly identify volume spikes that may indicate breakout activity

#### RSI Indicator Chart
- **RSI Line**: Purple line showing RSI values over time
- **Overbought Zone**: Red shaded area above 70 (potential reversal zone)
- **Oversold Zone**: Green shaded area below 30 (potential bounce zone)
- **Momentum Zone**: Yellow shaded area between 50-70 (optimal upward momentum)
- **Threshold Lines**: Horizontal lines at 30 and 70

#### MACD Chart
- **MACD Histogram**: Green bars for positive values, red bars for negative values
- **MACD Line**: Blue line showing the MACD indicator
- **Signal Line**: Purple line showing the signal line
- **Zero Line**: Black horizontal line at zero
- **Crossovers**: Visual identification of bullish/bearish crossovers

**Key Method:**
- `create_technical_analysis_chart(symbol, score_data, hist_data)` - Generates the comprehensive 4-panel chart

### 4. Breakout Signal Dashboard

The UI now displays a breakout signal dashboard showing the status of all filters:

- **Volume Spike**: ✅/❌ indicator
- **RSI Momentum**: ✅/❌ indicator  
- **MACD Momentum**: ✅/❌ indicator
- **Position**: ✅/❌ indicator (favorable position check)
- **Breakout**: ✅/❌ indicator (overall signal)

## Updated Indicators

The following indicators are now included in the stock scoring data:

### New Indicators
- `Support_90d`: Support level (90-day low)
- `Resistance_90d`: Resistance level (90-day high)
- `Relative_Position`: Position between support and resistance (0.0-1.0)

### Existing Indicators (Still Available)
- `RSI`: Relative Strength Index (14-period)
- `MACD`: MACD line value
- `MACD_Signal`: MACD signal line value
- `MACD_Histogram`: MACD histogram value
- `Volume_Ratio`: Current volume / 20-day average volume
- `Momentum_10d`: 10-day price momentum (% change)
- `Volatility`: Annualized volatility
- `Price_Range_20d`: 20-day price range as percentage
- `SMA_20`, `SMA_50`: Simple moving averages
- `EMA_12`, `EMA_26`: Exponential moving averages

## Usage Examples

### Example 1: Checking Breakout Filters

```python
from scoring_system import StockScorer

scorer = StockScorer(lookback_days=120, forecast_days=14)
hist = scorer.fetch_historical_data('AAPL')
current_price = hist['Close'].iloc[-1]

# Calculate indicators
rsi = scorer.calculate_rsi(hist['Close'])
macd, macd_signal, macd_hist = scorer.calculate_macd(hist['Close'])
volume_ratio = scorer.calculate_volume_trend(hist['Volume'])
support, resistance = scorer.calculate_support_resistance(hist)

# Check breakout filters
filters = scorer.check_breakout_filters(
    current_price, support, resistance,
    volume_ratio, rsi, macd_hist, macd, macd_signal
)

if filters['breakout_signal']:
    print(f"BREAKOUT DETECTED for AAPL!")
else:
    print(f"No breakout signal for AAPL")
    print(f"Filters: {filters}")
```

### Example 2: Generating Technical Analysis Chart

```python
from scoring_system import StockScorer
from visualizations import StockVisualizer

scorer = StockScorer(lookback_days=120, forecast_days=14)
visualizer = StockVisualizer()

# Get stock data and score
hist = scorer.fetch_historical_data('MSFT')
current_price = hist['Close'].iloc[-1]
score_data = scorer.score_stock('MSFT', current_price)

# Generate technical analysis chart
chart = visualizer.create_technical_analysis_chart('MSFT', score_data, hist)

if chart:
    # chart is base64-encoded image
    print(f"Chart generated: {len(chart)} characters")
```

### Example 3: Finding Stocks in Breakout Position

```python
from scoring_system import StockScorer
import pandas as pd

scorer = StockScorer()

# Score multiple stocks
symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
results = []

for symbol in symbols:
    hist = scorer.fetch_historical_data(symbol)
    if not hist.empty:
        current_price = hist['Close'].iloc[-1]
        score_data = scorer.score_stock(symbol, current_price)
        
        # Check if breakout signal is present
        if score_data.get('breakout_filters', {}).get('breakout_signal', False):
            results.append({
                'symbol': symbol,
                'score': score_data['score'],
                'relative_position': score_data['support_resistance']['relative_position']
            })

# Display breakout candidates
breakout_df = pd.DataFrame(results)
print(breakout_df.sort_values('score', ascending=False))
```

## Technical Details

### Calculation Methods

#### Support/Resistance
- Uses OHLC data from the last 90 days (configurable)
- Support = minimum of 'Low' prices
- Resistance = maximum of 'High' prices
- Falls back to 'Close' prices if OHLC not available

#### Volume Spike
- Calculated using 20-day rolling average
- Spike threshold = 1.5x average
- Uses most recent volume for comparison

#### RSI Momentum
- 14-period RSI calculation
- Acceptable range: 50-70
- Below 50: Not enough momentum
- Above 70: Potentially overbought

#### MACD Momentum
- Standard MACD calculation (12, 26, 9 periods)
- Bullish conditions:
  1. MACD histogram > 0 (positive momentum)
  2. MACD line > Signal line (bullish crossover)
- Either condition triggers the filter

#### Position Calculation
- Formula: `(current_price - support) / (resistance - support)`
- Favorable range: 0.4 to 0.7 (40% to 70%)
- Clamped to 0.0-1.0 range

## Integration in Streamlit App

The technical analysis chart and breakout signals are automatically displayed in:

1. **Top 5 Combined Results**: When viewing aggregated top stocks
2. **Top 5 Scoring Section**: When viewing top-ranked stocks from screening
3. **Auto-Run Results**: When displaying top stocks from automated screening

Each stock's detail view includes:
- Original combined chart (price forecast + indicator scores)
- New technical analysis chart (price + volume + RSI + MACD)
- Breakout signal dashboard (5-column indicator status)

## Testing

### Unit Tests
Run the comprehensive unit tests with mock data:

```bash
python test_enhancements_mock.py
```

This will test:
- Support and resistance calculation
- Breakout filter detection
- Comprehensive scoring with new features
- Technical analysis chart generation

### Manual Testing
1. Start the Streamlit app: `streamlit run app.py`
2. Navigate to any screening section
3. Enable "Top 5 Scoring" or view "Top 5 Combined Results"
4. Expand a stock to view:
   - Technical analysis chart with all 4 panels
   - Breakout signal indicators
   - Support/resistance levels in the indicators section

## Performance Considerations

- **Chart Generation**: Technical analysis charts are generated on-demand and may take 1-2 seconds per stock
- **Historical Data**: Fetches 120 days of data per stock for accurate calculations
- **Caching**: Uses existing app caching mechanisms for historical data
- **Memory**: Each chart image is ~160KB in base64 encoding

## Future Enhancements

Potential improvements for future versions:

1. **Configurable Thresholds**: Allow users to adjust breakout filter thresholds
2. **Additional Indicators**: Add Bollinger Bands, Stochastic RSI, ATR
3. **Alert System**: Email/SMS alerts when breakout signals are detected
4. **Backtesting**: Historical performance analysis of breakout signals
5. **Sector Comparison**: Compare stocks against sector averages
6. **Custom Time Periods**: Adjustable support/resistance calculation periods

## References

- RSI: https://en.wikipedia.org/wiki/Relative_strength_index
- MACD: https://en.wikipedia.org/wiki/MACD
- Support/Resistance: https://www.investopedia.com/trading/support-and-resistance-basics/
- Volume Analysis: https://www.investopedia.com/articles/technical/02/010702.asp
