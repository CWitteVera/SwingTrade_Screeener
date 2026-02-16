# Manual Test Scenarios: Advanced Data (financialdata.net)

This document contains manual test scenarios for the Advanced Data (financialdata.net) integration.

## Test Scenario Categories
1. Basic Fetch Tests
2. API Key Configuration Tests
3. Field Selection Tests
4. Universe Integration Tests
5. Fallback Behavior Tests
6. Caching Tests
7. Error Handling Tests

---

## 1. Basic Fetch Tests

### Test 1.1: Basic Data Fetch with API Key
**Objective:** Verify basic data fetching works with valid API key

**Setup:**
- Set valid `FINANCIALDATA_API_KEY` in environment or secrets

**Steps:**
1. Launch app
2. Select "Advanced Data (financialdata.net)" as data source
3. Select "S&P 500" universe
4. Set price range: $10 - $500
5. Click "Run Screener"

**Expected:**
- ✅ Green success badge: "✅ FinancialData.Net"
- Table shows stock data with: symbol, price, volume, market_cap
- At least 100 symbols returned (S&P 500 has ~500 stocks)
- No error messages

**Status:** ⏳ Pending


### Test 1.2: All NMS Universe Fetch (Limit 200)
**Objective:** Verify fetching from All NMS universe with reasonable limit

**Setup:**
- Valid API key configured

**Steps:**
1. Select "Advanced Data (financialdata.net)"
2. Select "All NMS" universe
3. Price range: $5 - $100
4. Run screener

**Expected:**
- Table shows diverse stock symbols
- Filtering pipeline shows: Requested → Fetched → After Price Filter
- Results within price range $5-$100
- Response time < 10 seconds

**Status:** ⏳ Pending


---

## 2. API Key Configuration Tests

### Test 2.1: Missing API Key - Fallback to Yahoo
**Objective:** Verify graceful fallback when API key is missing

**Setup:**
- Remove or unset `FINANCIALDATA_API_KEY`

**Steps:**
1. Select "Advanced Data (financialdata.net)"
2. Observe warning message
3. Select "S&P 500" universe
4. Run screener

**Expected:**
- ⚠️ Yellow warning: "Missing FinancialData.Net API Key"
- App automatically falls back to Yahoo Finance
- Orange badge: "⚠️ FinancialData.Net (Fallback to Yahoo)"
- Data still appears (from Yahoo)
- No crashes or errors

**Status:** ⏳ Pending


### Test 2.2: Invalid API Key - Error Handling
**Objective:** Verify error handling for invalid API key

**Setup:**
- Set `FINANCIALDATA_API_KEY=invalid_key_12345`

**Steps:**
1. Select "Advanced Data (financialdata.net)"
2. Run screener with any universe

**Expected:**
- Error message or fallback warning
- App does not crash
- Falls back to Yahoo Finance if possible

**Status:** ⏳ Pending


### Test 2.3: API Key from Environment Variable
**Objective:** Verify API key is read from environment

**Setup:**
- Set: `export FINANCIALDATA_API_KEY=your_valid_key`

**Steps:**
1. Launch app
2. Select "Advanced Data (financialdata.net)"
3. Run screener

**Expected:**
- No warning about missing key
- Green success badge
- Data fetched successfully

**Status:** ⏳ Pending


---

## 3. Field Selection Tests

### Test 3.1: Default Fields Only
**Objective:** Verify default field set works correctly

**Setup:**
- Valid API key
- Do NOT select any additional fields

**Steps:**
1. Select "Advanced Data (financialdata.net)"
2. Keep "Additional Fields" collapsed (don't select any)
3. Run screener with S&P 500

**Expected:**
- Table shows: Symbol, Price, Volume, Market Cap
- All fields have valid data (no N/A for most stocks)
- Clean, readable display

**Status:** ⏳ Pending


### Test 3.2: Technical Indicators Selection
**Objective:** Verify technical indicators can be selected and fetched

**Setup:**
- Valid API key

**Steps:**
1. Select "Advanced Data (financialdata.net)"
2. Expand "Additional Fields (Optional)"
3. Check: Relative Volume (10d), RSI, SMA 50, SMA 200
4. Run screener with S&P 500

**Expected:**
- Table includes new columns: Rel Vol (10d), RSI, SMA 50, SMA 200
- Technical indicators appear to the right of base columns
- Values are numeric and reasonable (e.g., RSI 0-100)

**Status:** ⏳ Pending


### Test 3.3: Moving Averages Selection
**Objective:** Verify EMA periods can be selected

**Steps:**
1. Select "Advanced Data (financialdata.net)"
2. Expand "Additional Fields"
3. Select EMA Periods: 5, 10, 20, 50
4. Run screener

**Expected:**
- Columns: EMA 5, EMA 10, EMA 20, EMA 50
- Values are numeric and close to current price
- EMAs ordered correctly (faster EMAs more reactive)

**Status:** ⏳ Pending


### Test 3.4: Fundamentals Selection
**Objective:** Verify fundamental fields work

**Steps:**
1. Select "Advanced Data (financialdata.net)"
2. Check: P/E Ratio, EPS
3. Run screener with S&P 500

**Expected:**
- Table includes: P/E Ratio, EPS
- Values are reasonable (P/E > 0 for most, EPS can be negative)
- Some stocks may show N/A if data unavailable

**Status:** ⏳ Pending


---

## 4. Universe Integration Tests

### Test 4.1: S&P 500 Universe
**Objective:** Verify S&P 500 universe works with financialdata.net

**Steps:**
1. Select "Advanced Data (financialdata.net)"
2. Select "S&P 500" universe
3. Price range: $0 - $10,000 (no filtering)
4. Run screener

**Expected:**
- ~500 symbols (or close to it)
- All major S&P 500 stocks present (AAPL, MSFT, GOOGL, etc.)
- Market cap values seem reasonable

**Status:** ⏳ Pending


### Test 4.2: NASDAQ-100 Universe
**Objective:** Verify NASDAQ-100 universe integration

**Steps:**
1. Select "Advanced Data (financialdata.net)"
2. Select "NASDAQ-100" universe
3. Run screener

**Expected:**
- ~100 symbols
- Tech-heavy stocks (AAPL, MSFT, AMZN, GOOGL, META, etc.)
- All prices and volumes present

**Status:** ⏳ Pending


### Test 4.3: Leveraged ETFs with Custom Hydration
**Objective:** Verify Leveraged ETFs work (custom list hydrated via API)

**Steps:**
1. Select "Advanced Data (financialdata.net)"
2. Select "Leveraged ETFs" universe
3. Run screener

**Expected:**
- Known leveraged ETFs appear (TQQQ, SQQQ, UPRO, SPXU, etc.)
- Prices and volumes are current
- Data is successfully "hydrated" from financialdata.net

**Status:** ⏳ Pending


### Test 4.4: Custom CSV Symbols
**Objective:** Verify custom symbols work with financialdata.net

**Steps:**
1. Select "Advanced Data (financialdata.net)"
2. Select "Custom CSV"
3. Enter: `AAPL, MSFT, TSLA, NVDA, AMD`
4. Run screener

**Expected:**
- Exactly 5 symbols returned
- All are valid tech stocks
- Current prices displayed

**Status:** ⏳ Pending


---

## 5. Fallback Behavior Tests

### Test 5.1: Automatic Yahoo Fallback on Missing Key
**Objective:** Verify smooth fallback to Yahoo when key missing

**Setup:**
- No API key configured

**Steps:**
1. Select "Advanced Data (financialdata.net)"
2. Observe warning
3. Run screener with any universe

**Expected:**
- Warning displayed before running
- Data still loads (from Yahoo)
- Badge shows fallback status
- No additional errors

**Status:** ⏳ Pending


### Test 5.2: Fallback Preserves Price Range Filter
**Objective:** Verify price filter still works in fallback mode

**Setup:**
- No API key

**Steps:**
1. Select "Advanced Data (financialdata.net)"
2. Set price range: $50 - $150
3. Run screener

**Expected:**
- Results filtered to $50-$150
- Filtering pipeline metrics accurate
- No symbols outside range

**Status:** ⏳ Pending


---

## 6. Caching Tests

### Test 6.1: Cache Hit on Repeat Query
**Objective:** Verify caching works for repeated queries

**Steps:**
1. Enable Developer Mode
2. Select "Advanced Data (financialdata.net)", S&P 500
3. Run screener (cache miss)
4. Immediately run again with same settings

**Expected:**
- First run: Cache miss logged
- Second run: Instant results (cached)
- API call count doesn't increase on second run
- Debug log shows cache behavior

**Status:** ⏳ Pending


### Test 6.2: Cache Invalidation on Field Change
**Objective:** Verify cache updates when fields change

**Steps:**
1. Run screener with default fields
2. Add RSI field
3. Run again

**Expected:**
- Cache miss on second run (different fields)
- New column (RSI) appears in results
- Fresh API call logged

**Status:** ⏳ Pending


---

## 7. Error Handling Tests

### Test 7.1: Network Error Handling
**Objective:** Verify graceful handling of network errors

**Setup:**
- Simulate network issue (disconnect WiFi briefly, or use invalid endpoint)

**Expected:**
- Error message displayed
- App doesn't crash
- User can retry

**Status:** ⏳ Pending


### Test 7.2: Rate Limit Handling
**Objective:** Verify handling of API rate limits

**Setup:**
- Make many rapid requests to trigger rate limit

**Expected:**
- Error or warning about rate limit
- Suggests waiting or upgrading plan
- Cache reduces likelihood of hitting limit

**Status:** ⏳ Pending


---

## Summary Dashboard

| Category | Total Tests | Passed | Failed | Pending |
|----------|-------------|--------|--------|---------|
| Basic Fetch | 2 | 0 | 0 | 2 |
| API Key Config | 3 | 0 | 0 | 3 |
| Field Selection | 4 | 0 | 0 | 4 |
| Universe Integration | 4 | 0 | 0 | 4 |
| Fallback Behavior | 2 | 0 | 0 | 2 |
| Caching | 2 | 0 | 0 | 2 |
| Error Handling | 2 | 0 | 0 | 2 |
| **TOTAL** | **19** | **0** | **0** | **19** |

---

## Notes for Testers

1. **API Key Setup**: Before testing, obtain a free API key from https://financialdata.net/
2. **Environment Variables**: Use `.env` file or export commands to set keys
3. **Developer Mode**: Enable for detailed debugging information
4. **Screenshots**: Capture screenshots for UI tests
5. **Performance**: Note response times for large universes
6. **Data Quality**: Spot-check a few stock prices against known sources

---

## Migration Verification Checklist

- [ ] TradingView no longer appears in data source dropdown
- [ ] All TradingView test cases migrated or deprecated
- [ ] README updated with financialdata.net instructions
- [ ] No broken imports or references to TradingView
- [ ] API key configuration documented
- [ ] Fallback behavior works as expected
- [ ] Similar functionality to old TradingView integration
