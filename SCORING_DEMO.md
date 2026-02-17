# Scoring System Demo

This demo shows how the new scoring system works with the SwingTrade Stock Screener.

## Overview

The scoring system adds intelligent ranking to your stock screening results, helping you identify the top 3 stocks with the highest probability of upward price movement.

## How to Use

### 1. Start the App
```bash
streamlit run app.py
```

### 2. Configure Your Screen
- **Select Data Source**: Yahoo (EOD) - works out of the box
- **Choose Universe**: S&P 500 or NASDAQ-100 (recommended for testing)
- **Set Price Range**: Swing Trades ($10-$200) - good starting point

### 3. Enable Scoring System
In the sidebar, under **"5️⃣ Scoring & Ranking"**:
- ✅ Check **"Enable Top 3 Scoring System"**
- 📊 Select **Forecast Period**: 14 days (default)

### 4. Run the Screener
Click **"🔍 Run Screener"** button

### 5. View Results

First, you'll see the standard results table with all filtered stocks.

Then, scroll down to see:

```
🏆 Top 3 Stocks by Upward Potential
```

Each stock shows:
- **Rank**: 🥇 Gold, 🥈 Silver, or 🥉 Bronze
- **Score**: Composite score (0-100)
- **Probability**: Likelihood of upward movement (%)

### 6. Expand for Details

Click on each stock to see:

#### Metrics
- Current Price
- Composite Score
- Upward Probability
- Volume

#### Price Forecast
- Expected Target (predicted price)
- 80% Confidence Range
- Volatility Percentage

#### Visualization
Combined chart showing:
- Historical price (last 30 days)
- Predicted price with confidence bands
- Indicator score breakdown (bar chart)

#### Contributing Indicators
Technical indicator values:
- RSI
- MACD + Signal + Histogram
- SMA 20, SMA 50
- EMA 12, EMA 26
- Volume Ratio
- 10-day Momentum

#### Score Breakdown
Individual scores for each indicator showing why the stock ranked in top 3.

## Example Session

### Step 1: Configure
```
Data Source: Yahoo (EOD)
Universe: S&P 500
Price Range: Swing Trades ($10-$200)
✅ Enable Top 3 Scoring System
Forecast Period: 14 days
```

### Step 2: Results
```
📊 Filtering Pipeline
Total Requested: 50
Fetched: 48
Missing Price: 2
After Price Filter: 35

Filtered Stocks: [Table with 35 stocks]
```

### Step 3: Top 3
```
🏆 Top 3 Stocks by Upward Potential

🥇 AAPL - Score: 85.2/100 | Probability: 85.2%
   Current Price: $150.25
   Expected Target: $157.30 (+4.7%)
   80% Confidence: $153.10 - $161.50
   
   Contributing Indicators:
   - RSI: 38.5 (oversold - bullish)
   - MACD: 0.85 (positive - bullish)
   - Volume Ratio: 1.45 (above average)
   - Momentum: +5.2% (strong)
   
   Score Breakdown:
   - RSI Score: 95.0/100
   - MACD Score: 85.0/100
   - Moving Avg Score: 100.0/100
   - Volume Score: 75.0/100
   - Momentum Score: 90.0/100

🥈 MSFT - Score: 78.5/100 | Probability: 78.5%
   [Similar detailed breakdown...]

🥉 GOOGL - Score: 72.3/100 | Probability: 72.3%
   [Similar detailed breakdown...]
```

## Tips

### Get Better Results
1. **Filter First**: Use price range to narrow down to 20-50 stocks
2. **Choose Liquid Stocks**: Use S&P 500 or NASDAQ-100 for best data quality
3. **Multiple Timeframes**: Try 7, 14, and 30-day forecasts to compare
4. **Check Indicators**: Look at the breakdown to understand WHY a stock scored high

### Interpretation Guide

**High Score (80-100)**
- Strong bullish signals across multiple indicators
- Good probability of upward movement
- Consider for further research

**Medium Score (60-79)**
- Mixed signals, some bullish indicators
- Moderate probability
- Review indicator breakdown for concerns

**Lower Scores**
- These won't appear in top 3
- Focus on the highest-ranked stocks

### Important Notes

⚠️ **Network Required**: Scoring requires internet access to fetch historical data

⚠️ **Processing Time**: Scoring 30+ stocks may take 10-30 seconds

⚠️ **Not Financial Advice**: Scores are educational tools, not investment recommendations

## Troubleshooting

### "Insufficient data" error
- Stock may be newly listed or have limited history
- Try with established S&P 500 stocks

### Charts not showing
- Ensure matplotlib is installed: `pip install matplotlib`
- Check that requirements.txt was used during installation

### Slow performance
- Reduce the number of stocks by using stricter price filters
- Select smaller universes (Leveraged ETFs has only 15 stocks)

### No network connectivity
- Scoring requires internet to fetch Yahoo Finance historical data
- Standard screening still works offline with mock data

## Advanced Usage

### Custom Analysis
After scoring, you can:
1. Download results as CSV
2. Compare top stocks across different timeframes
3. Combine with Advanced Data source for fundamental indicators

### Integration with Auto-Run Mode
Scoring is NOT available in Auto-Run mode (it would be too slow). For scoring:
- Uncheck Auto-Run Mode
- Use manual mode to configure and enable scoring

## Next Steps

1. **Try It**: Run your first scored screen
2. **Experiment**: Try different universes and price ranges
3. **Compare**: Run multiple screens with different forecast periods
4. **Learn**: Study why certain stocks score higher
5. **Research**: Use top 3 as starting point for deeper analysis

## Support

- See `SCORING_SYSTEM_GUIDE.md` for detailed methodology
- Check `README.md` for general usage
- Review indicator definitions online for deeper understanding

---

**Happy Trading!** 📈

Remember: This is an educational tool. Always do your own research and consult financial professionals before making investment decisions.
