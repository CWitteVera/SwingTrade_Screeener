# Test Scenario: Trend Template Filter

## Purpose
This test scenario documents the **future enhancement** for Trend Template filtering. Currently, the application only supports price range filtering. This document serves as a template for testing trend-based filters when they are implemented.

## Current Status
🚧 **NOT YET IMPLEMENTED** - This is a placeholder for future development

The current application (`v1.x`) only implements:
- Universe selection
- Price range filtering
- Data source selection

Trend Template filtering is **planned for a future release**.

---

## Planned Features (Future Implementation)

### Trend Template Filter Types
The following trend filters are planned for future implementation:

1. **Moving Average Crossovers**
   - Price above/below MA(20, 50, 200)
   - Golden Cross (50 MA crosses above 200 MA)
   - Death Cross (50 MA crosses below 200 MA)

2. **Momentum Indicators**
   - RSI thresholds (oversold < 30, overbought > 70)
   - MACD signal crossovers
   - Stochastic oscillator levels

3. **Volume Patterns**
   - Above average volume
   - Volume surge (2x, 3x, 5x average)
   - Volume declining

4. **Price Patterns**
   - Higher highs, higher lows (uptrend)
   - Lower highs, lower lows (downtrend)
   - Consolidation (narrow range)

5. **Breakout Detection**
   - 52-week high breakout
   - Resistance level breakout
   - Support level breakdown

---

## Placeholder Test Cases (For Future Implementation)

### Test Case 1: Enable Trend Filter (Planned)
**Objective:** Enable and configure a trend template filter

**Steps (Planned):**
1. Launch application
2. In sidebar, look for "Trend Template" section
3. Enable "Apply Trend Filter" checkbox
4. Select a template (e.g., "MA Crossover - Bullish")
5. Configure parameters (e.g., MA periods)
6. Run screener

**Expected Results (Planned):**
- Filter applies in addition to price range
- Results show only symbols matching trend criteria
- Filtering pipeline shows "After Trend Filter" metric

**Current Status:** ❌ Not implemented

---

### Test Case 2: Combine Price and Trend Filters (Planned)
**Objective:** Use price range and trend filter together

**Steps (Planned):**
1. Set price range: $20 - $100
2. Enable trend filter: "RSI Oversold" (RSI < 30)
3. Run screener

**Expected Results (Planned):**
- Results match BOTH price and trend criteria
- Filtering pipeline: Total → Fetched → After Price → After Trend
- Fewer results than price-only filter

**Current Status:** ❌ Not implemented

---

### Test Case 3: TradingView Advanced Fields for Trend Analysis (Current Workaround)
**Objective:** Use TradingView's advanced fields to manually analyze trends

**Current Workaround:**
While true Trend Template filters are not yet implemented, you can use TradingView's advanced fields to fetch technical indicators and analyze trends manually:

**Steps:**
1. Select "TradingView (Advanced)" data source
2. Expand "Advanced Fields (Optional)"
3. Select technical indicators:
   - ✅ RSI
   - ✅ MACD
   - ✅ Stochastic
   - ✅ EMA5, EMA10, EMA20, EMA50
4. Run screener
5. Manually review results table for trend signals:
   - RSI < 30 = oversold
   - RSI > 70 = overbought
   - MACD.macd > MACD.signal = bullish
   - Price > EMA20 = above moving average

**Expected Results:**
- Additional columns appear in results table
- Technical indicator values displayed for each symbol
- Manual trend analysis possible by reviewing columns

**Pass Criteria:**
- ✅ Advanced fields loaded successfully
- ✅ Technical indicators displayed in table
- ✅ Values are reasonable (RSI 0-100, etc.)

**Limitations:**
- No automatic filtering based on trend criteria
- Requires manual review of results
- Cannot set thresholds or conditions

---

## Implementation Roadmap (Planned)

### Phase 1: Basic Trend Filters
- [ ] Add "Trend Template" section to sidebar
- [ ] Implement MA crossover detection
- [ ] Implement RSI threshold filter
- [ ] Add "After Trend Filter" metric to pipeline

### Phase 2: Advanced Trend Filters
- [ ] MACD signal crossovers
- [ ] Stochastic oscillator filters
- [ ] Volume pattern detection
- [ ] Custom indicator combinations

### Phase 3: Pattern Recognition
- [ ] Chart pattern detection (triangles, flags, etc.)
- [ ] Support/resistance breakouts
- [ ] Consolidation ranges

### Phase 4: Backtesting
- [ ] Historical trend filter performance
- [ ] Signal accuracy metrics
- [ ] Win rate analysis

---

## Current Alternatives

Until Trend Template filters are implemented, consider these workarounds:

### Option 1: TradingView Advanced Fields (Recommended)
Use TradingView data source with advanced technical indicators:
- Enable RSI, MACD, Bollinger Bands, Moving Averages
- Export results to CSV
- Analyze trends in Excel/Python with custom formulas

### Option 2: Export and Post-Process
1. Run screener with price filter only
2. Download results as CSV
3. Use external tools (Excel, Python, TradingView charts) for trend analysis

### Option 3: Multiple Screener Runs
1. First pass: Price filter only
2. Review results manually on TradingView or similar
3. Identify symbols matching trend criteria
4. Use "Custom CSV" universe with filtered symbols

---

## Data Source Considerations (For Future Implementation)

When Trend Template filters are implemented, they should work with:

1. **Yahoo Finance (EOD)**
   - Limited fields (price, volume, change)
   - Would require calculating indicators from historical data
   - May need additional API calls for historical prices

2. **TradingView (Advanced)**
   - Already provides technical indicators (RSI, MACD, etc.)
   - Best suited for trend filtering
   - Real-time or delayed data available

3. **Alpaca Markets (Intraday)**
   - Real-time price data
   - Would require calculating indicators from intraday bars
   - Good for intraday trend detection

---

## Testing Checklist (For Future Use)

When Trend Template filters are implemented, test:

- [ ] Single trend filter (MA crossover only)
- [ ] Multiple trend filters (MA + RSI)
- [ ] Trend filter with price range
- [ ] Trend filter with all data sources
- [ ] Invalid trend parameters (error handling)
- [ ] Performance with large universes (S&P 500)
- [ ] Cache behavior with trend filters
- [ ] Debug log shows trend filter timings

---

## Notes
- This document is a **planning template** for future development
- Current application (v1.x) does **NOT** include trend filtering
- TradingView Advanced fields provide a temporary workaround
- Trend filters would significantly increase complexity and API usage
- Consider implementing as opt-in feature for performance

## Related Issues
- Feature Request: Trend Template Filters (Future)
- Enhancement: Advanced Screening Criteria (Future)

## Related Files
- `app.py` - Main application (would need trend filter UI/logic)
- `src/data_sources/tradingview.py` - Already fetches technical indicators
- `src/universe_sets.py` - Might need trend-based universe filters
