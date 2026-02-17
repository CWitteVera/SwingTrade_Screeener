# Auto-Run Mode Quick Start Guide

## What is Auto-Run Mode?

Auto-Run Mode is a new feature that automatically screens stocks across multiple scenarios without requiring any manual selection. Perfect for:
- 🚀 Quick exploration of available stocks
- ✅ Testing your API configurations
- 📊 Finding which combinations return results
- ⏱️ Saving time on repetitive screening

## How to Use Auto-Run Mode

### Step 1: Launch the App
```bash
streamlit run app.py
```

### Step 2: Enable Auto-Run Mode
At the top of the page, check the box:
```
☑️ Enable Auto-Run Mode
```

### Step 3: Wait for Results
The app will automatically:
1. Run through 6-8 different screening scenarios
2. Test multiple universes (S&P 500, NASDAQ-100, Leveraged ETFs, All NMS)
3. Try different price ranges (Penny Stocks $1-$10, Swing Trades $10-$200, High Value $200+)
4. Use all available data sources (Yahoo, FinancialData.net if configured, Alpaca if configured)

### Step 4: Review Results
You'll see:
- **Scenario Summary Table**: Shows which scenarios succeeded and how many results each found
- **Detailed Results**: Expandable sections for each successful scenario showing the actual stock data
- **Download Options**: CSV download button for each result set

## What Scenarios Are Tested?

### Always Run (Yahoo Finance):
1. S&P 500 - Swing Trades ($10-$200)
2. NASDAQ-100 - Swing Trades ($10-$200)
3. Leveraged ETFs - All Prices ($0-$10,000)
4. S&P 500 - Penny Stocks ($1-$10)
5. NASDAQ-100 - High Value ($200+)
6. All NMS - Swing Trades ($10-$200)

### Additional (if API keys configured):
7. S&P 500 - Swing Trades (Advanced Data with technicals)
8. NASDAQ-100 - Swing Trades (Advanced Data)
9. Alpaca Most Actives - All Prices (Intraday)
10. Alpaca Gainers - Swing Trades (Intraday)

## Interpreting Results

### ✅ Success
Scenario ran successfully and found stocks matching the criteria.

### ⚠️ No Results
Scenario ran successfully but no stocks matched the price range. This is normal - not all scenarios will return results depending on market conditions.

### ❌ Failed
Scenario encountered an error. Common causes:
- Missing API keys
- Network connectivity issues
- Invalid configuration

## Tips

1. **First Time Users**: Auto-Run Mode is the best way to get started. You'll instantly see what the screener can do.

2. **API Testing**: Auto-Run Mode automatically detects which API services you have configured and tests them all.

3. **No Results?**: If you see mostly "No Results", this is normal. Try:
   - Different market conditions (run at different times)
   - Wider price ranges
   - Different universe sets

4. **Customize Later**: After seeing Auto-Run results, uncheck the box to switch to Manual Mode for precise control.

## Performance

Auto-Run Mode is optimized for speed:
- Uses cached data when possible
- Runs scenarios sequentially to avoid rate limits
- Samples small batches first to validate before full runs
- Typically completes in 30-60 seconds

## Switching Back to Manual Mode

Simply uncheck:
```
☐ Enable Auto-Run Mode
```

The manual controls will reappear, allowing you to:
- Select specific data sources
- Choose specific universes
- Set custom price ranges
- Select technical indicators (for Advanced Data)

## Need Help?

If Auto-Run Mode isn't working:
1. Enable "Developer Mode" in the sidebar for detailed logs
2. Check API Status Dashboard (shows which services are configured)
3. Review error messages in the Failed Scenarios section
4. Ensure your `.env` file has valid API keys if using advanced features

## Example Output

```
📊 SCENARIO SUMMARY
┌─────────────────────────────────────────┬───────────────┬──────────┐
│ Scenario                                │ Status        │ Results  │
├─────────────────────────────────────────┼───────────────┼──────────┤
│ S&P 500 - Swing Trades (Yahoo)          │ ✅ Success    │ 45       │
│ NASDAQ-100 - Swing Trades (Yahoo)       │ ✅ Success    │ 38       │
│ Leveraged ETFs - All Prices (Yahoo)     │ ✅ Success    │ 15       │
│ S&P 500 - Penny Stocks (Yahoo)          │ ⚠️ No Results │ 0        │
│ NASDAQ-100 - High Value (Yahoo)         │ ✅ Success    │ 12       │
│ All NMS - Swing Trades (Yahoo)          │ ✅ Success    │ 67       │
└─────────────────────────────────────────┴───────────────┴──────────┘
```

---

**Happy Screening!** 🎯
