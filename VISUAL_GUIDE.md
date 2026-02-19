# Visual Guide: New Technical Analysis Charts

## Overview
This document describes what users will see when viewing the enhanced stock screening charts in the Streamlit application.

## Chart Layout

The new technical analysis chart consists of 4 vertically stacked panels showing price, volume, RSI, and MACD indicators.

## Color Scheme

### Price Chart (Panel 1)
- **Price Line**: Blue - Historical closing prices
- **Support Line**: Green dashed - 90-day low level
- **Resistance Line**: Red dashed - 90-day high level
- **Current Price Marker**: Purple dot

### Volume Chart (Panel 2)
- **Normal Volume Bars**: Blue
- **Spike Volume Bars**: Red (≥1.5x average)
- **Threshold Line**: Red dashed at 1.5x average

### RSI Chart (Panel 3)
- **RSI Line**: Purple
- **Overbought Zone** (70-100): Light red shading
- **Oversold Zone** (0-30): Light green shading
- **Momentum Zone** (50-70): Light yellow shading

### MACD Chart (Panel 4)
- **Positive Histogram**: Green bars
- **Negative Histogram**: Red bars
- **MACD Line**: Blue
- **Signal Line**: Purple

## Breakout Signal Dashboard

Below each chart, a 5-column indicator dashboard shows:

| Volume Spike | RSI Momentum | MACD Momentum | Position | Breakout |
|:------------:|:------------:|:-------------:|:--------:|:--------:|
| ✅/❌ | ✅/❌ | ✅/❌ | ✅/❌ | ✅/❌ |
| (≥1.5x) | (50-70) | (positive) | (40-70%) | (ALL) |

## Example Interpretation

### Strong Breakout Signal (All Green)
```
✅ Volume Spike    → Trading interest confirmed
✅ RSI Momentum    → Healthy upward trend (50-70)
✅ MACD Momentum   → Positive momentum confirmed
✅ Position        → Good position (40-70% range)
✅ Breakout        → STRONG BREAKOUT SIGNAL!
```

### Weak Signal (Mixed)
```
✅ Volume Spike    → Trading interest confirmed
❌ RSI Momentum    → RSI = 75 (too high, overbought)
✅ MACD Momentum   → Positive momentum
✅ Position        → Good position
❌ Breakout        → NOT a confirmed breakout
```

## How to Use the Charts

1. **Check Overall Breakout Signal**: Look for all green checkmarks (✅✅✅✅✅)
2. **Verify Price Position**: Ensure price is between support (green) and resistance (red)
3. **Confirm Volume Spike**: Look for red volume bars in Panel 2
4. **Check RSI Zone**: Ideal is the yellow shaded zone (50-70)
5. **Verify MACD**: Look for green histogram bars (bullish momentum)

## Where Charts Appear

Technical analysis charts are displayed in:
1. **Top 5 Combined Results** section
2. **Auto-Run Top 5 Stocks** section  
3. **Manual Screening Top 5** section

Each stock's detail view includes both the original combined chart and the new technical analysis chart.

## Additional Metrics

Below the indicators, detailed metrics are shown including:
- Support/Resistance levels with dollar values
- Relative position percentage
- RSI value
- MACD values and histogram
- Volume ratio
- Price momentum

All indicators use industry-standard calculations for accuracy and reliability.
