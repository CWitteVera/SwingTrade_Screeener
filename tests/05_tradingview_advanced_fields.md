# Test Scenario: TradingView Advanced Fields

## Purpose
Verify that the TradingView (Advanced) data source works correctly, including field selection, technical indicators, caching, and fallback behavior.

## Prerequisites
- Application is running (`streamlit run app.py`)
- Internet connection for TradingView API
- **Note:** Real-time data may require session cookies (see TradingView documentation)

---

## Test Case 1: TradingView Data Source Selection
**Objective:** Verify TradingView data source can be selected

### Steps:
1. Launch the application
2. In sidebar, locate "Universe Source" radio buttons
3. Select "TradingView (Advanced)"
4. Observe sidebar changes

### Expected Results:
- Info message about large field set and real-time data
- "TradingView Configuration" section appears
- "Advanced Fields (Optional)" expander visible
- "Result Limit" slider visible (default: 500)

### Pass Criteria:
- ✅ TradingView configuration UI appears
- ✅ Default settings: No advanced fields, limit 500

---

## Test Case 2: TradingView Default Fields Only
**Objective:** Fetch data with default fields (no advanced fields selected)

### Steps:
1. Select "TradingView (Advanced)"
2. Do NOT select any advanced fields
3. Select "Leveraged ETFs" universe
4. Click "Run Screener"
5. Review results table columns

### Expected Results:
- Default columns displayed:
  - Symbol
  - Price (close)
  - Volume
  - Change ($)
  - Change (%)
  - Market Cap
- Data fetched successfully
- Source badge: "✅ TradingView (Advanced)"

### Pass Criteria:
- ✅ Data fetched with default fields
- ✅ All default columns present

---

## Test Case 3: TradingView with Technical Indicators - RSI
**Objective:** Add RSI indicator field

### Steps:
1. Select "TradingView (Advanced)"
2. Expand "Advanced Fields (Optional)"
3. Under "Technical Indicators", check "RSI"
4. Select "S&P 500" universe
5. Click "Run Screener"
6. Review results table

### Expected Results:
- RSI column appears in table (on the right side)
- RSI values between 0-100
- Values formatted as "XX.XX"

### Pass Criteria:
- ✅ RSI column present
- ✅ Values in valid range (0-100)

---

## Test Case 4: TradingView with Technical Indicators - MACD
**Objective:** Add MACD indicator fields

### Steps:
1. Select "TradingView (Advanced)"
2. Expand "Advanced Fields (Optional)"
3. Check "MACD"
4. Select "NASDAQ-100" universe
5. Click "Run Screener"

### Expected Results:
- Two MACD columns appear:
  - MACD
  - MACD Signal
- Values are decimal numbers (can be negative)

### Pass Criteria:
- ✅ Both MACD columns present
- ✅ Values are reasonable decimals

---

## Test Case 5: TradingView with Multiple Technical Indicators
**Objective:** Select multiple technical indicators at once

### Steps:
1. Select "TradingView (Advanced)"
2. Expand "Advanced Fields (Optional)"
3. Select ALL technical indicators:
   - ✅ Relative Volume (10d)
   - ✅ RSI
   - ✅ MACD
   - ✅ Stochastic
   - ✅ Bollinger Bands
   - ✅ VWAP
4. Select "Leveraged ETFs" universe (smaller for faster testing)
5. Click "Run Screener"

### Expected Results:
- All indicator columns appear in results table
- Columns ordered: default fields first, then advanced fields
- All values formatted correctly
- No errors or missing data warnings

### Pass Criteria:
- ✅ All requested indicator columns present
- ✅ Data populated for most/all symbols

---

## Test Case 6: TradingView with Moving Averages - Single Period
**Objective:** Add a single EMA period

### Steps:
1. Select "TradingView (Advanced)"
2. Expand "Advanced Fields (Optional)"
3. Under "Moving Averages", select "EMA Periods" = ["20"]
4. Select "S&P 500" universe
5. Click "Run Screener"

### Expected Results:
- "EMA 20" column appears
- Values are decimal prices
- EMA20 values should be reasonably close to current price

### Pass Criteria:
- ✅ EMA 20 column present
- ✅ Values are reasonable prices

---

## Test Case 7: TradingView with Multiple Moving Averages
**Objective:** Add multiple EMA periods

### Steps:
1. Select "TradingView (Advanced)"
2. Expand "Advanced Fields (Optional)"
3. Select "EMA Periods" = ["5", "10", "20", "50"]
4. Select "Leveraged ETFs" universe
5. Click "Run Screener"

### Expected Results:
- Four EMA columns appear: EMA 5, EMA 10, EMA 20, EMA 50
- Shorter EMAs (5, 10) closer to current price
- Longer EMAs (20, 50) may differ more from current price
- EMA 5 > EMA 10 > EMA 20 > EMA 50 in uptrends (and vice versa)

### Pass Criteria:
- ✅ All four EMA columns present
- ✅ Logical relationship between EMAs

---

## Test Case 8: TradingView with All Advanced Fields
**Objective:** Select ALL available advanced fields

### Steps:
1. Select "TradingView (Advanced)"
2. Expand "Advanced Fields (Optional)"
3. Select ALL technical indicators (6 items)
4. Select ALL EMA periods (4 items: 5, 10, 20, 50)
5. Select "Leveraged ETFs" universe
6. Click "Run Screener"

### Expected Results:
- ~10+ additional columns in results table
- Table scrolls horizontally
- All fields populated with data
- Some "N/A" values acceptable for certain fields/symbols
- Performance remains acceptable

### Pass Criteria:
- ✅ All advanced field columns present
- ✅ Most data populated
- ✅ UI remains responsive

---

## Test Case 9: TradingView Result Limit Adjustment
**Objective:** Test different result limit values

### Steps:
1. Select "TradingView (Advanced)"
2. Select "All NMS" universe (~80 symbols)
3. Test with different "Result Limit" values:
   - Run with limit = 50
   - Run with limit = 500
4. Compare results counts

### Expected Results:
- With limit = 50: Max 50 symbols returned
- With limit = 500: All ~80 symbols returned (less than limit)
- "Results truncated" warning shows only when limit reached
- Higher limits may take slightly longer to fetch

### Pass Criteria:
- ✅ Limit enforced correctly
- ✅ Truncation warning shown when appropriate

---

## Test Case 10: TradingView with Large Universe (Result Truncation)
**Objective:** Verify result truncation with large universe

### Steps:
1. Select "TradingView (Advanced)"
2. Set "Result Limit" = 100
3. Select "Custom CSV" universe
4. Enter a large list of symbols (200+ symbols):
   ```
   AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA, ... (200+ total)
   ```
5. Click "Run Screener"

### Expected Results:
- Max 100 symbols returned
- Warning: "⚠️ **Results truncated:** Showing top results (limit reached)"
- "After Price Filter" metric shows 100 (or less if price filtered)

### Pass Criteria:
- ✅ Result limit enforced
- ✅ Truncation warning displayed

---

## Test Case 11: TradingView Cache Behavior (5-minute TTL)
**Objective:** Verify TradingView data caching

### Steps:
1. Enable Developer Mode
2. Clear Debug Log
3. Select "TradingView (Advanced)"
4. Select RSI field, limit 500
5. Select "Leveraged ETFs" universe
6. Click "Run Screener"
7. Check Debug Log → API Calls (note TradingView call count)
8. Wait 2 minutes
9. Click "Run Screener" again (same settings)
10. Check API Calls again

### Expected Results:
- First run: TradingView API call = 1
- Second run (within 5 min): TradingView API call remains 1 (cached)
- Wait > 5 minutes, then run: API call increments (cache expired)

### Pass Criteria:
- ✅ Cache hit within 5 minutes
- ✅ Cache miss after 5 minutes

---

## Test Case 12: TradingView Cache Invalidation on Field Change
**Objective:** Verify cache invalidates when fields change

### Steps:
1. Enable Developer Mode
2. Clear Debug Log
3. Run screener with TradingView, NO advanced fields
4. Note API call count (should be 1)
5. Add RSI field
6. Run screener again
7. Check API call count

### Expected Results:
- Adding/removing fields invalidates cache
- API call count increments to 2
- New fetch with updated field set

### Pass Criteria:
- ✅ Field change invalidates cache
- ✅ New API call made

---

## Test Case 13: TradingView Fallback to Yahoo
**Objective:** Verify fallback when TradingView unavailable

### Steps:
1. Select "TradingView (Advanced)"
2. Select "S&P 500" universe
3. **Simulate TradingView failure** (requires code modification or network blocking)
   - OR test during TradingView API outage
4. Click "Run Screener"

### Expected Results:
- TradingView API call fails
- Automatic fallback to Yahoo Finance
- Warning badge: "⚠️ TradingView (Fallback to Yahoo)"
- Info message: "Session cookies may be required for real-time data"
- Data fetched from Yahoo for S&P 500 universe
- Advanced fields NOT available in fallback mode

### Pass Criteria:
- ✅ Fallback to Yahoo successful
- ✅ Warning badge displayed
- ✅ No application crash

**Note:** This test case may be difficult to execute without simulating a failure condition.

---

## Test Case 14: TradingView with Price Range Filter
**Objective:** Verify price filtering works with TradingView data

### Steps:
1. Select "TradingView (Advanced)"
2. Select RSI and EMA20 fields
3. Select "S&P 500" universe
4. Set price range: $100 - $300
5. Click "Run Screener"

### Expected Results:
- TradingView fetches all S&P 500 symbols with advanced fields
- Price filter applied after fetch
- Only symbols priced $100-$300 displayed
- Advanced field columns (RSI, EMA20) present in results

### Pass Criteria:
- ✅ Price filter applies correctly
- ✅ Advanced fields present for filtered results

---

## Test Case 15: TradingView Field Selection UI
**Objective:** Verify field selection UI is intuitive

### Steps:
1. Select "TradingView (Advanced)"
2. Expand "Advanced Fields (Optional)"
3. Test field selection:
   - Check/uncheck individual indicators
   - Select/deselect EMA periods
   - Observe UI feedback

### Expected Results:
- Fields organized by category (Technical Indicators, Moving Averages)
- Checkboxes toggle on/off smoothly
- Multi-select for EMA periods works
- No lag or UI issues

### Pass Criteria:
- ✅ UI responsive
- ✅ Clear organization by category

---

## Test Case 16: TradingView Performance with Max Fields and Max Limit
**Objective:** Test performance under maximum load

### Steps:
1. Enable Developer Mode
2. Select "TradingView (Advanced)"
3. Select ALL advanced fields (10+ fields)
4. Set "Result Limit" = 500
5. Select "All NMS" universe (~80 symbols)
6. Click "Run Screener"
7. Check Debug Log → Timings

### Expected Results:
- Fetch completes within reasonable time (<30 seconds)
- All fields populated
- Timings logged in Debug Log:
  - `data_fetch`: Should be <20 seconds
  - `price_filter`: Should be <1 second
  - `total_fetch_and_filter`: Should be <30 seconds
- UI remains responsive

### Pass Criteria:
- ✅ Fetch completes successfully
- ✅ Acceptable performance (<30s)

---

## Test Case 17: TradingView Developer Mode Logging
**Objective:** Verify comprehensive debug logging for TradingView

### Steps:
1. Enable Developer Mode
2. Clear Debug Log
3. Select "TradingView (Advanced)"
4. Select RSI and MACD fields
5. Select "Leveraged ETFs" universe
6. Click "Run Screener"
7. Review Debug Log tabs:
   - Cache Stats
   - Timings
   - API Calls
   - Full Log

### Expected Results:
- **Cache Stats:** Fetch cache miss recorded
- **Timings:** All timing steps logged
- **API Calls:** TradingView call count = 1
- **Full Log:** 
  - "Fetching data from TradingView (Advanced)"
  - Symbol counts logged
  - Data source info logged

### Pass Criteria:
- ✅ All timing steps logged
- ✅ API call counted correctly
- ✅ Cache behavior tracked

---

## Test Case 18: TradingView Data Quality Validation
**Objective:** Verify technical indicator values are reasonable

### Steps:
1. Select "TradingView (Advanced)"
2. Select RSI, MACD, EMA20 fields
3. Select "Leveraged ETFs" universe
4. Click "Run Screener"
5. Review results for data quality:
   - RSI values: 0-100
   - MACD values: Can be positive or negative
   - EMA20 values: Should be close to current price

### Expected Results:
- RSI: All values between 0 and 100
- MACD: Reasonable values (not extreme outliers)
- EMA20: Within 20% of current price for most symbols
- Few or no "N/A" values

### Pass Criteria:
- ✅ RSI values valid (0-100)
- ✅ MACD values reasonable
- ✅ EMA20 values logical

---

## Test Case 19: TradingView with Invalid Universe
**Objective:** Test error handling with invalid symbols

### Steps:
1. Select "TradingView (Advanced)"
2. Select "Custom CSV" universe
3. Enter invalid symbols: `INVALID123, FAKE456, NOTREAL789`
4. Click "Run Screener"

### Expected Results:
- TradingView may return no data for invalid symbols
- "Missing Price" count = 3 (or all symbols)
- No results displayed (or empty table)
- No application crash
- Appropriate message: "No stocks match the current filter criteria"

### Pass Criteria:
- ✅ Invalid symbols handled gracefully
- ✅ No crash or errors

---

## Test Case 20: TradingView CSV Export
**Objective:** Verify CSV export includes advanced fields

### Steps:
1. Select "TradingView (Advanced)"
2. Select RSI, EMA20, VWAP fields
3. Select "Leveraged ETFs" universe
4. Click "Run Screener"
5. Click "📥 Download Results (CSV)"
6. Open CSV file in Excel/editor

### Expected Results:
- CSV includes all columns from results table
- Default fields: symbol, price, volume, change, change_pct, market_cap_basic
- Advanced fields: RSI, EMA20, VWAP
- Values formatted correctly (no extra quotes or escaping issues)

### Pass Criteria:
- ✅ CSV export successful
- ✅ All columns present
- ✅ Data formatted correctly

---

## Notes

### Data Freshness
- TradingView provides delayed data by default (15-20 minutes)
- Real-time data may require authentication (session cookies)
- Fallback to Yahoo provides end-of-day data

### Field Selection Strategy
- Start with default fields for testing
- Add advanced fields incrementally
- More fields = slightly longer fetch times
- Result limit helps manage response size

### Caching Strategy
- Cache TTL: 5 minutes
- Cache key includes: `universe` + `fields` + `limit`
- Changing fields or limit invalidates cache

### Common Issues
- **Session Cookies:** Real-time data may fail without proper authentication
- **Rate Limiting:** TradingView has undocumented rate limits
- **Field Availability:** Some fields may not be available for all symbols

## Related Files
- `src/data_sources/tradingview.py` - TradingView data source implementation
- `app.py` - TradingView UI configuration (lines 266-317)
