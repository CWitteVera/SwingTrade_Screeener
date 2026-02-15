# Test Scenario: Universe Selections

## Purpose
Verify that all universe selection options work correctly and return expected symbols.

## Prerequisites
- Application is running (`streamlit run app.py`)
- No specific API credentials required for basic universes

---

## Test Case 1: S&P 500 Universe
**Objective:** Verify S&P 500 universe loads correctly

### Steps:
1. Launch the application
2. In the sidebar, select "Universe Set" dropdown
3. Select "S&P 500"
4. Observe the "Total Symbols" metric

### Expected Results:
- Total Symbols should show `50` (demo subset)
- No error messages displayed

### Pass Criteria:
- ✅ Total Symbols = 50
- ✅ No errors in UI

---

## Test Case 2: NASDAQ-100 Universe
**Objective:** Verify NASDAQ-100 universe loads correctly

### Steps:
1. In the sidebar, select "Universe Set" dropdown
2. Select "NASDAQ-100"
3. Observe the "Total Symbols" metric

### Expected Results:
- Total Symbols should show `50` (demo subset)
- No error messages displayed

### Pass Criteria:
- ✅ Total Symbols = 50
- ✅ No errors in UI

---

## Test Case 3: All NMS Universe
**Objective:** Verify All NMS (combined S&P 500 + NASDAQ-100) universe loads correctly

### Steps:
1. In the sidebar, select "Universe Set" dropdown
2. Select "All NMS"
3. Observe the "Total Symbols" metric

### Expected Results:
- Total Symbols should be approximately `80-85` (combined unique symbols from S&P 500 and NASDAQ-100 demo subsets)
- No error messages displayed
- No duplicate symbols

### Pass Criteria:
- ✅ Total Symbols between 80-85
- ✅ No errors in UI

---

## Test Case 4: Leveraged ETFs Universe
**Objective:** Verify Leveraged ETFs universe loads correctly

### Steps:
1. In the sidebar, select "Universe Set" dropdown
2. Select "Leveraged ETFs"
3. Observe the "Total Symbols" metric

### Expected Results:
- Total Symbols should show `15`
- List includes: TQQQ, SQQQ, SPXL, SPXS, UPRO, SOXL, SOXS, TECL, TECS, TNA, TZA, TMF, FAS, NUGT, FNGU

### Pass Criteria:
- ✅ Total Symbols = 15
- ✅ No errors in UI

---

## Test Case 5: Custom CSV Universe (Valid Input)
**Objective:** Verify custom symbol input works with valid symbols

### Steps:
1. In the sidebar, select "Universe Set" dropdown
2. Select "Custom CSV"
3. A text area should appear
4. Enter the following symbols: `AAPL, MSFT, GOOGL, AMZN, TSLA`
5. Observe the "Total Symbols" metric

### Expected Results:
- Total Symbols should show `5`
- No error messages displayed

### Pass Criteria:
- ✅ Total Symbols = 5
- ✅ No errors in UI

---

## Test Case 6: Custom CSV Universe (Empty Input)
**Objective:** Verify error handling for empty custom input

### Steps:
1. In the sidebar, select "Universe Set" dropdown
2. Select "Custom CSV"
3. Leave the text area empty (or clear any existing text)
4. Click "Run Screener" button

### Expected Results:
- Error message: "❌ **Empty Universe**: No symbols found in the selected universe set"
- Warning: "⚠️ No symbols to screen. Please select a universe or enter custom symbols."

### Pass Criteria:
- ✅ Appropriate error/warning messages displayed
- ✅ Application does not crash

---

## Test Case 7: Custom CSV Universe (Mixed Format)
**Objective:** Verify parser handles various input formats

### Steps:
1. Select "Custom CSV" universe
2. Enter symbols in mixed format:
   ```
   AAPL, msft
   googl,AMZN
   tsla
   ```
3. Observe the "Total Symbols" metric

### Expected Results:
- Total Symbols should show `5`
- All symbols should be normalized to uppercase
- Newlines and varying spacing should be handled

### Pass Criteria:
- ✅ Total Symbols = 5
- ✅ Symbols parsed correctly despite format variations

---

## Test Case 8: Universe Cache Behavior (Developer Mode)
**Objective:** Verify universe caching works correctly

### Steps:
1. Enable Developer Mode in sidebar
2. Clear Debug Log
3. Select "S&P 500" universe
4. Click "Run Screener"
5. Check Debug Log → Cache Misses tab
6. Note universe cache misses (should be 1)
7. Click "Run Screener" again without changing universe (within 1 hour)
8. Check Cache Misses tab again

### Expected Results:
- First run: Universe cache miss = 1 (function executes)
- Second run (within 1 hour): Universe cache miss remains 1 (function doesn't execute - cache hit occurred but not logged)
- Cache TTL is 1 hour (3600 seconds)
- No new cache miss count means cache hit occurred

### Pass Criteria:
- ✅ Cache miss recorded on first fetch
- ✅ No new cache miss on second fetch (indicates cache hit)

**Note:** Streamlit's caching mechanism means cache hits can't be explicitly logged. When a cache hit occurs, the cached function doesn't execute at all. The absence of new cache misses indicates successful cache hits.

---

## Test Case 9: Universe Switch Performance
**Objective:** Verify switching between universes is responsive

### Steps:
1. Select "S&P 500" and note Total Symbols
2. Switch to "NASDAQ-100" and note Total Symbols
3. Switch to "All NMS" and note Total Symbols
4. Switch to "Leveraged ETFs" and note Total Symbols
5. Switch back to "S&P 500"

### Expected Results:
- Each universe switch updates Total Symbols immediately
- No lag or errors
- Correct counts for each universe

### Pass Criteria:
- ✅ Immediate UI updates
- ✅ Correct symbol counts for all universes

---

## Notes
- Universe selections are cached for 1 hour to improve performance
- Custom CSV parsing is case-insensitive and handles various delimiters
- Empty universes are properly validated before running screener

## Related Files
- `src/universe_sets.py` - Universe definitions
- `app.py` - Universe selection UI and caching logic
