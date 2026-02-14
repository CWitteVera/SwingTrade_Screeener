# Test Scenario: Price Range Behavior

## Purpose
Verify that price range filtering works correctly across different scenarios, including edge cases and validation.

## Prerequisites
- Application is running (`streamlit run app.py`)
- Select any universe (recommend "Leveraged ETFs" for quick testing with diverse prices)
- Yahoo (EOD) data source selected

---

## Test Case 1: Default Price Range
**Objective:** Verify default price range allows all stocks

### Steps:
1. Launch the application
2. Select "Leveraged ETFs" universe
3. Select "Yahoo (EOD)" data source
4. Observe default price range values
5. Click "Run Screener"

### Expected Results:
- Default Min Price: `$0.00`
- Default Max Price: `$1000.00`
- All symbols with valid prices should pass filter
- "After Price Filter" count should match or be close to "Fetched" count (minus missing prices)

### Pass Criteria:
- ✅ Default range is $0 - $1000
- ✅ Wide range captures most/all stocks

---

## Test Case 2: Narrow Price Range
**Objective:** Verify filtering with a narrow price range

### Steps:
1. Select "Leveraged ETFs" universe
2. Set Min Price to `$40.00`
3. Set Max Price to `$60.00`
4. Click "Run Screener"
5. Observe filtering pipeline metrics

### Expected Results:
- "After Price Filter" count should be less than "Fetched" count
- Only stocks with prices between $40 and $60 displayed in results table
- All displayed prices should be within range

### Pass Criteria:
- ✅ Only stocks within $40-$60 displayed
- ✅ Filtering pipeline shows correct counts

---

## Test Case 3: High Price Range (Premium Stocks)
**Objective:** Filter for expensive stocks only

### Steps:
1. Select "S&P 500" universe
2. Set Min Price to `$200.00`
3. Set Max Price to `$1000.00`
4. Click "Run Screener"

### Expected Results:
- Results should include high-priced stocks (e.g., GOOGL, NVDA if above $200)
- Lower-priced stocks filtered out
- Filter rate (percentage) should be relatively low

### Pass Criteria:
- ✅ Only stocks priced ≥ $200 displayed
- ✅ Lower-priced stocks excluded

---

## Test Case 4: Low Price Range (Penny/Budget Stocks)
**Objective:** Filter for low-priced stocks only

### Steps:
1. Select "NASDAQ-100" universe
2. Set Min Price to `$0.00`
3. Set Max Price to `$20.00`
4. Click "Run Screener"

### Expected Results:
- Only stocks under $20 displayed
- Higher-priced stocks filtered out
- May result in few or no matches depending on market conditions

### Pass Criteria:
- ✅ Only stocks priced ≤ $20 displayed
- ✅ If no matches, appropriate message: "No stocks match the current filter criteria"

---

## Test Case 5: Invalid Price Range (Min >= Max)
**Objective:** Verify validation for invalid price ranges

### Steps:
1. Select any universe
2. Set Min Price to `$100.00`
3. Set Max Price to `$50.00` (less than min)
4. Observe sidebar warnings
5. Click "Run Screener"

### Expected Results:
- Warning in sidebar: "⚠️ **Invalid Price Range**: Min price must be less than max price. No price filtering will be applied."
- Warning in results: "⚠️ **Price filter not applied**: Invalid price range (min >= max). Showing all results with valid prices."
- All stocks with valid prices shown (no filtering applied)
- "After Price Filter" metric should show full count

### Pass Criteria:
- ✅ Warning messages displayed in sidebar and results
- ✅ No price filtering applied
- ✅ Application does not crash

---

## Test Case 6: Equal Min and Max Price
**Objective:** Verify behavior when min equals max

### Steps:
1. Select "Leveraged ETFs" universe
2. Set Min Price to `$50.00`
3. Set Max Price to `$50.00` (equal to min)
4. Click "Run Screener"

### Expected Results:
- Same as Test Case 5 (invalid range)
- Warning displayed
- No filtering applied

### Pass Criteria:
- ✅ Treated as invalid range
- ✅ Warning displayed

---

## Test Case 7: Extreme Price Range (Very High Max)
**Objective:** Verify handling of very high max prices

### Steps:
1. Select "S&P 500" universe
2. Set Min Price to `$0.00`
3. Set Max Price to `$10000.00` (maximum allowed)
4. Click "Run Screener"

### Expected Results:
- All stocks with valid prices should pass filter
- No truncation or errors
- Results similar to default range

### Pass Criteria:
- ✅ All stocks captured
- ✅ No errors with extreme value

---

## Test Case 8: Price Range Adjustment (Cache Behavior)
**Objective:** Verify cache behavior when adjusting price range

### Steps:
1. Enable Developer Mode
2. Select "Leveraged ETFs" universe
3. Set price range $0 - $1000
4. Click "Run Screener"
5. Check Debug Log → Cache Stats (note fetch cache misses)
6. Adjust price range to $40 - $60 (without changing other settings)
7. Click "Run Screener" again
8. Check Cache Stats again

### Expected Results:
- First run: Fetch cache miss = 1
- Second run: Fetch cache may hit or miss depending on TTL (5 minutes)
- If within 5 minutes, fetch should use cache
- Price filtering should be reapplied to cached data

### Pass Criteria:
- ✅ Cache behavior consistent with TTL
- ✅ Price filtering applied correctly to cached data

---

## Test Case 9: Price Range with Different Data Sources
**Objective:** Verify price filtering works across all data sources

### Steps:
1. Test with Yahoo (EOD):
   - Select "S&P 500", set range $100-$200, run screener
2. Test with TradingView (Advanced):
   - Switch to TradingView, keep same range, run screener
3. Test with Alpaca (if credentials available):
   - Switch to Alpaca Movers, keep same range, run screener

### Expected Results:
- Price filtering works consistently across all sources
- Different sources may return different symbols (based on their data)
- Filtering pipeline metrics should be accurate for each source

### Pass Criteria:
- ✅ Price filter works with Yahoo
- ✅ Price filter works with TradingView
- ✅ Price filter works with Alpaca (or fallback)

---

## Test Case 10: Rapid Price Range Changes
**Objective:** Verify UI responsiveness with rapid filter adjustments

### Steps:
1. Select "Leveraged ETFs" universe
2. Run screener with default range
3. Rapidly change price range multiple times:
   - $0 - $50
   - $50 - $100
   - $30 - $70
4. Run screener after each change

### Expected Results:
- UI remains responsive
- Each run produces correct filtered results
- No errors or crashes
- Cache may help performance

### Pass Criteria:
- ✅ UI responsive to rapid changes
- ✅ Correct results each time
- ✅ No errors

---

## Test Case 11: Price Range Visual Slider
**Objective:** Verify visual price range slider displays correctly

### Steps:
1. Select any universe
2. Set Min Price to `$25.00`
3. Set Max Price to `$75.00`
4. Observe the "Price Range Visual" slider in sidebar

### Expected Results:
- Visual slider should reflect the selected range ($25-$75)
- Slider is disabled (not interactive)
- Slider provides visual feedback only

### Pass Criteria:
- ✅ Visual slider matches selected range
- ✅ Slider is disabled as expected

---

## Test Case 12: Price Filter with Missing Price Data
**Objective:** Verify handling when some symbols have missing prices

### Steps:
1. Select "Custom CSV" universe
2. Enter: `AAPL, MSFT, INVALID123, GOOGL`
3. Set price range $0 - $1000
4. Click "Run Screener"
5. Check "Missing Price" metric

### Expected Results:
- Invalid symbol (INVALID123) should have missing price
- Valid symbols should pass filter
- "Missing Price" count should be 1 (or more if others invalid)
- Only valid symbols with prices in range displayed

### Pass Criteria:
- ✅ Missing prices handled gracefully
- ✅ Valid symbols processed correctly
- ✅ Accurate "Missing Price" count

---

## Notes
- Price filtering is applied **after** data fetch and normalization
- Cache TTL for fetch operations is 5 minutes
- Invalid price ranges (min >= max) disable filtering but don't crash app
- All data sources support price filtering consistently

## Related Files
- `app.py` - Price range filtering logic (lines 236-238, 397-431)
- Price range validation in main UI section
