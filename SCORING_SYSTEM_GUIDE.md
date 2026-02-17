# Stock Scoring System Feature

## Overview

The Stock Scoring System is an advanced feature that analyzes stock data to identify the top 3 stocks with the highest probability of upward price movement over a specified period.

## Features

### 1. **Composite Scoring**
The system calculates a composite score (0-100) for each stock based on multiple technical indicators:

- **RSI (Relative Strength Index)**: Identifies oversold/overbought conditions
- **MACD (Moving Average Convergence Divergence)**: Detects momentum and trend changes
- **Moving Averages**: Compares current price to SMA 20/50 and EMA 12/26
- **Volume Analysis**: Measures trading volume relative to 20-day average
- **Price Momentum**: Calculates rate of change over 10-day period

### 2. **Probability Calculation**
Each stock receives a probability score (0-100%) indicating the likelihood of upward price movement based on:
- Technical indicator alignment
- Historical pattern analysis
- Momentum strength
- Volume confirmation

### 3. **Price Prediction**
For the top 3 stocks, the system provides:
- **Expected Price Target**: Predicted price after forecast period
- **Confidence Intervals**: 80% and 95% confidence ranges
- **Volatility Measure**: Annualized historical volatility
- **Trend Strength**: Direction and strength of current trend

### 4. **Visualizations**
Each top stock includes a combined chart showing:
- **Price Forecast**: Historical prices + predicted price range with confidence bands
- **Indicator Scores**: Horizontal bar chart showing contribution of each indicator

## How to Use

### 1. Enable the Feature
In the sidebar, under "Section 5️⃣: Scoring & Ranking":
```
☑️ Enable Top 3 Scoring System
```

### 2. Set Forecast Period
Use the slider to select forecast period (7-30 days, default: 14 days)

### 3. Run Screener
Click "🔍 Run Screener" to fetch and filter stocks as usual

### 4. View Top 3 Results
After the results table, you'll see:
```
🏆 Top 3 Stocks by Upward Potential
```

Each top stock displays:
- 🥇 Rank (Gold, Silver, Bronze medals)
- Composite Score (0-100)
- Upward Probability (%)
- Current Price & Volume

### 5. Analyze Details
Expand each stock to see:
- **Price Forecast Metrics**
  - Expected Target
  - 80% Confidence Range
  - Volatility Percentage
  
- **Visualization**
  - Combined chart with price forecast and indicator breakdown
  
- **Contributing Indicators**
  - RSI, MACD, Moving Averages, Volume Ratio, Momentum
  
- **Score Breakdown**
  - Individual scores for each indicator (0-100)

## Scoring Methodology

### Indicator Weights
```
RSI:              25%
MACD:             25%
Moving Averages:  20%
Volume:           15%
Momentum:         15%
```

### RSI Scoring
- < 30: Very oversold (85/100) - High potential
- 30-40: Oversold (95/100) - Optimal entry
- 40-50: Slightly oversold (75/100) - Good
- 50-60: Neutral to bullish (60/100)
- 60-70: Getting overbought (40/100)
- > 70: Overbought (20/100) - Risky

### MACD Scoring
- Positive histogram + MACD > Signal: 80-100
- Positive histogram only: 60
- MACD > Signal only: 55
- Bearish: 30

### Moving Average Scoring
- Score based on percentage of MAs that price is trading above
- 100 if price > all MAs, 0 if price < all MAs

### Volume Scoring
- > 1.5x average: 90
- 1.2-1.5x average: 75
- 1.0-1.2x average: 60
- 0.8-1.0x average: 45
- < 0.8x average: 30

### Momentum Scoring
- > 5% gain: 90
- 2-5% gain: 75
- 0-2% gain: 60
- -2-0% change: 40
- < -2% loss: 20

## Price Prediction Method

### Historical Volatility
- Calculated from daily returns over 30-day period
- Annualized using 252 trading days
- Used to estimate price range uncertainty

### Trend Analysis
- Linear regression on recent 20 days
- Projects trend forward to forecast period
- Adds volatility-based confidence bands

### Confidence Intervals
- **80% Confidence**: ±1.28 standard deviations
- **95% Confidence**: ±2.0 standard deviations

## Technical Requirements

### Required Packages
```
yfinance>=0.2.32      # Historical data
pandas>=2.0.0         # Data manipulation
numpy>=1.24.0         # Numerical calculations
matplotlib>=3.7.0     # Visualizations
```

### Data Requirements
- Minimum 20 days of historical data
- Valid OHLCV (Open, High, Low, Close, Volume) data
- Access to Yahoo Finance API

## Limitations

1. **Historical Data Dependency**: Scores are based on historical patterns, which may not predict future performance
2. **Network Requirements**: Requires internet access to fetch historical data from Yahoo Finance
3. **Computational Time**: Scoring all stocks may take 10-30 seconds depending on number of results
4. **No Guarantee**: Scores indicate technical probability, not guaranteed returns

## Best Practices

1. **Use with Price Filters**: Narrow down stocks first using price range filters
2. **Compare Multiple Timeframes**: Try different forecast periods (7, 14, 30 days)
3. **Verify Indicators**: Check the indicator breakdown to understand why a stock scored high
4. **Consider Volatility**: High volatility means wider price ranges and higher risk
5. **Combine with Fundamentals**: Use with Advanced Data source for fundamental analysis

## Example Interpretation

```
🥇 AAPL - Score: 82.5/100 | Probability: 82.5%

Current Price: $150.25
Composite Score: 82.5/100
Upward Probability: 82.5%
Volume: 50.0M

Expected Target: $155.80 (+3.7%)
80% Confidence Range: $152.10 - $159.50
Volatility: 28.5%

Contributing Indicators:
- RSI: 42.5 (slightly oversold - bullish)
- MACD: 0.52 (positive - bullish)
- Volume Ratio: 1.35 (above average - bullish)
- Momentum (10d): +4.2% (strong - bullish)
- Price > SMA 20, SMA 50 (bullish)

Score Breakdown:
- RSI Score: 95.0/100
- MACD Score: 80.0/100
- Moving Avg Score: 100.0/100
- Volume Score: 75.0/100
- Momentum Score: 75.0/100
```

**Interpretation**: AAPL shows strong bullish signals across all indicators. The slightly oversold RSI combined with positive MACD and strong momentum suggest good entry point. Expected gain of 3.7% over 14 days with 80% confidence of staying within $152-$160 range.

## Troubleshooting

### "Insufficient data" error
- Stock may be newly listed or delisted
- Try with more established stocks (S&P 500, NASDAQ-100)

### Charts not displaying
- Ensure matplotlib is installed: `pip install matplotlib`
- Check browser supports base64 images

### Slow performance
- Reduce number of stocks before scoring
- Use stricter price filters
- Consider analyzing top stocks only

## Updates and Improvements

Future enhancements may include:
- Machine learning-based predictions
- Sentiment analysis integration
- Real-time data updates
- Custom indicator selection
- Backtesting capabilities
- Risk assessment metrics

---

**Note**: This scoring system is for educational and informational purposes only. Always conduct your own research and consult with financial advisors before making investment decisions.
