# Test Scenario: Alpaca Intraday Source

## Purpose
Verify that the Alpaca Markets intraday data source works correctly, including authentication, movers lists, caching, and fallback behavior.

## Prerequisites
- Application is running (`streamlit run app.py`)
- Alpaca Markets account (free or paid)
- API credentials (Paper Trading or Live)
- **Optional:** Set environment variables `ALPACA_API_KEY` and `ALPACA_API_SECRET`

---

## Test Case 1: Alpaca Data Source Selection
**Objective:** Verify Alpaca data source can be selected

### Steps:
1. Launch the application
2. In sidebar, locate "Universe Source" radio buttons
3. Select "Alpaca Movers (Intraday)"
4. Observe sidebar changes

### Expected Results:
- "Alpaca Configuration" section appears
- API Credentials expander visible
- Movers List dropdown visible
- Number of Top Movers slider visible

### Pass Criteria:
- ✅ Alpaca configuration UI appears
- ✅ Default settings: Most Actives, Top 50

---

## Test Case 2: Alpaca with Environment Variables
**Objective:** Verify Alpaca works with environment variables

### Steps:
1. Set environment variables (before running app):
   ```bash
   export ALPACA_API_KEY="your_paper_api_key"
   export ALPACA_API_SECRET="your_paper_secret_key"
   ```
2. Launch application: `streamlit run app.py`
3. Select "Alpaca Movers (Intraday)"
4. Leave API credential fields empty in UI
5. Select any universe (e.g., "S&P 500")
6. Click "Run Screener"

### Expected Results:
- No warning about missing credentials
- Data fetched successfully from Alpaca
- Source badge shows "✅ Alpaca (Intraday)"
- Results show intraday prices

### Pass Criteria:
- ✅ Credentials read from environment
- ✅ Data fetched successfully
- ✅ No fallback to Yahoo

---

## Test Case 3: Alpaca with UI Input Credentials
**Objective:** Verify Alpaca works with credentials entered in UI

### Steps:
1. **Do not** set environment variables (or unset them)
2. Launch application
3. Select "Alpaca Movers (Intraday)"
4. Expand "API Credentials" section
5. Enter API Key and Secret in input fields
6. Select universe "S&P 500"
7. Click "Run Screener"

### Expected Results:
- Data fetched successfully from Alpaca
- Source badge shows "✅ Alpaca (Intraday)"
- No fallback warning

### Pass Criteria:
- ✅ UI credentials override environment
- ✅ Data fetched successfully

---

## Test Case 4: Alpaca Most Actives List
**Objective:** Test "Most Actives" movers list

### Steps:
1. Select "Alpaca Movers (Intraday)"
2. Provide valid credentials
3. Select "Movers List" = "Most Actives"
4. Set "Number of Top Movers" = 50
5. **Note:** Universe selection is ignored for Alpaca movers
6. Click "Run Screener"

### Expected Results:
- Top 50 most active stocks fetched
- Results show symbols with high trading activity
- Source badge: "✅ Alpaca (Intraday)"

### Pass Criteria:
- ✅ Results returned (≤ 50 symbols)
- ✅ Intraday data displayed

---

## Test Case 5: Alpaca Market Movers - Gainers
**Objective:** Test "Market Movers - Gainers" list

### Steps:
1. Select "Alpaca Movers (Intraday)"
2. Provide valid credentials
3. Select "Movers List" = "Market Movers - Gainers"
4. Set "Number of Top Movers" = 30
5. Click "Run Screener"

### Expected Results:
- Top 30 gaining stocks fetched
- Results show stocks with positive change%
- Most symbols should have positive "Change (%)" values

### Pass Criteria:
- ✅ Results returned (≤ 30 symbols)
- ✅ Majority have positive change%

---

## Test Case 6: Alpaca Market Movers - Losers
**Objective:** Test "Market Movers - Losers" list

### Steps:
1. Select "Alpaca Movers (Intraday)"
2. Provide valid credentials
3. Select "Movers List" = "Market Movers - Losers"
4. Set "Number of Top Movers" = 30
5. Click "Run Screener"

### Expected Results:
- Top 30 losing stocks fetched
- Results show stocks with negative change%
- Most symbols should have negative "Change (%)" values

### Pass Criteria:
- ✅ Results returned (≤ 30 symbols)
- ✅ Majority have negative change%

---

## Test Case 7: Alpaca Top Volume List
**Objective:** Test "Top Volume" movers list

### Steps:
1. Select "Alpaca Movers (Intraday)"
2. Provide valid credentials
3. Select "Movers List" = "Top Volume"
4. Set "Number of Top Movers" = 40
5. Click "Run Screener"

### Expected Results:
- Top 40 stocks by volume fetched
- Results show symbols with high volume
- Volume column should show large numbers

### Pass Criteria:
- ✅ Results returned (≤ 40 symbols)
- ✅ High volume symbols displayed

---

## Test Case 8: Alpaca with Price Range Filter
**Objective:** Verify price filtering works with Alpaca data

### Steps:
1. Select "Alpaca Movers (Intraday)"
2. Provide valid credentials
3. Select "Most Actives" list, Top 50
4. Set price range: $50 - $200
5. Click "Run Screener"
6. Check filtering pipeline metrics

### Expected Results:
- Alpaca fetches top 50 most actives
- Price filter applied after fetch
- "After Price Filter" < "Fetched" (unless all within range)
- Only symbols priced $50-$200 displayed

### Pass Criteria:
- ✅ Price filter applies correctly
- ✅ Filtering pipeline metrics accurate

---

## Test Case 9: Alpaca Missing Credentials (Fallback)
**Objective:** Verify fallback to Yahoo when credentials missing

### Steps:
1. Unset environment variables:
   ```bash
   unset ALPACA_API_KEY
   unset ALPACA_API_SECRET
   ```
2. Launch application
3. Select "Alpaca Movers (Intraday)"
4. Leave credential fields empty
5. Select "S&P 500" universe
6. Click "Run Screener"

### Expected Results:
- Warning before run: "⚠️ No API credentials found. Will fall back to Yahoo Finance."
- After run, warning badge: "⚠️ Alpaca (Fallback to Yahoo)"
- Data fetched from Yahoo instead
- No application crash

### Pass Criteria:
- ✅ Fallback warning displayed
- ✅ Yahoo data used instead
- ✅ No errors or crashes

---

## Test Case 10: Alpaca Invalid Credentials (Fallback)
**Objective:** Verify fallback when credentials are invalid

### Steps:
1. Select "Alpaca Movers (Intraday)"
2. Enter **invalid** credentials:
   - API Key: `invalid_key_12345`
   - Secret: `invalid_secret_67890`
3. Select "S&P 500" universe
4. Click "Run Screener"

### Expected Results:
- Alpaca API call fails (401 or 403 error)
- Automatic fallback to Yahoo Finance
- Warning badge: "⚠️ Alpaca (Fallback to Yahoo)"
- Data fetched from Yahoo for S&P 500 universe

### Pass Criteria:
- ✅ Graceful error handling
- ✅ Fallback to Yahoo successful
- ✅ No application crash

---

## Test Case 11: Alpaca Cache Behavior (45-second TTL)
**Objective:** Verify Alpaca data caching

### Steps:
1. Enable Developer Mode
2. Select "Alpaca Movers (Intraday)" with valid credentials
3. Select "Most Actives", Top 50
4. Click "Run Screener"
5. Check Debug Log → API Calls (note Alpaca call count)
6. Wait 30 seconds
7. Click "Run Screener" again (same settings)
8. Check API Calls again

### Expected Results:
- First run: Alpaca API call = 1
- Second run (within 45s): Alpaca API call remains 1 (cached)
- Wait > 45 seconds, then run again: API call increments (cache expired)

### Pass Criteria:
- ✅ Cache hit within 45 seconds
- ✅ Cache miss after 45 seconds

---

## Test Case 12: Alpaca Performance with Different Top N Values
**Objective:** Test varying the number of movers fetched

### Steps:
1. Select "Alpaca Movers (Intraday)" with valid credentials
2. Test with different "Number of Top Movers":
   - Run with N=10
   - Run with N=50
   - Run with N=100
3. Compare fetch times (use Developer Mode timings)

### Expected Results:
- Larger N values may take slightly longer
- All requests should complete within reasonable time (<10 seconds)
- Results count should match requested N (or less if fewer available)

### Pass Criteria:
- ✅ All N values work correctly
- ✅ Performance acceptable for all values

---

## Test Case 13: Alpaca API Rate Limiting
**Objective:** Verify behavior under rate limiting

### Steps:
1. Enable Developer Mode
2. Select "Alpaca Movers (Intraday)"
3. Rapidly click "Run Screener" multiple times (10+ times)
4. Check Debug Log → Errors

### Expected Results:
- Caching should prevent most API calls
- If rate limit hit, error logged in Debug Log
- Possible fallback to Yahoo if rate limited
- Application remains stable

### Pass Criteria:
- ✅ Cache reduces API calls
- ✅ Rate limit errors handled gracefully
- ✅ No application crash

---

## Test Case 14: Alpaca with TradingView Comparison
**Objective:** Compare Alpaca intraday vs TradingView data

### Steps:
1. Run screener with "Alpaca Movers (Intraday)", Most Actives, Top 50
2. Note the symbols and prices
3. Switch to "TradingView (Advanced)"
4. Run screener with same universe (or custom CSV of same symbols)
5. Compare prices

### Expected Results:
- Alpaca shows intraday (real-time or 15-min delayed) prices
- TradingView may show different prices (real-time, delayed, or EOD)
- Price differences expected due to data source and timing
- Both sources should return valid data

### Pass Criteria:
- ✅ Both sources return data
- ✅ Price differences are reasonable (not orders of magnitude off)

---

## Test Case 15: Alpaca Developer Mode Logging
**Objective:** Verify comprehensive debug logging for Alpaca

### Steps:
1. Enable Developer Mode
2. Clear Debug Log
3. Select "Alpaca Movers (Intraday)" with valid credentials
4. Select "Most Actives", Top 30
5. Click "Run Screener"
6. Review Debug Log tabs:
   - Cache Stats
   - Timings
   - API Calls
   - Full Log

### Expected Results:
- **Cache Stats:** Fetch cache miss recorded
- **Timings:** 
  - `source_selection` timing logged
  - `data_fetch` timing logged
  - `price_filter` timing logged
  - `total_fetch_and_filter` timing logged
- **API Calls:** Alpaca call count = 1
- **Full Log:** 
  - Entries for "Fetching data from Alpaca"
  - Entries for symbol counts and data source

### Pass Criteria:
- ✅ All timing steps logged
- ✅ API call counted correctly
- ✅ Cache behavior tracked

---

## Notes

### Data Freshness
- **Paper Trading API:** Real-time data
- **Live API:** Real-time data (requires funded account)
- Data is intraday, not end-of-day

### Movers Lists Behavior
- Alpaca movers lists are **pre-filtered** by Alpaca
- Universe selection in UI is **ignored** when Alpaca Movers is selected
- The movers list itself becomes the effective universe

### Caching Strategy
- Cache TTL: 45 seconds (shorter than Yahoo/TradingView due to intraday data)
- Cache key includes: `movers_type` + `top_n`
- Changing movers type or top N invalidates cache

### Rate Limits
- **Free Tier:** 200 requests/minute
- **Unlimited Plan:** Higher limits
- Caching helps stay within limits

### Fallback Behavior
Alpaca falls back to Yahoo Finance when:
1. Credentials missing or invalid
2. API error (timeout, rate limit, etc.)
3. Network issues

## Related Files
- `src/data_sources/alpaca.py` - Alpaca data source implementation
- `app.py` - Alpaca UI configuration (lines 319-371)
