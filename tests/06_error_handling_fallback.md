# Test Scenario: Error Handling and Fallback Tests

## Purpose
Verify that the application handles errors gracefully, provides clear error messages, and implements fallback mechanisms when primary data sources fail.

## Prerequisites
- Application is running (`streamlit run app.py`)
- Ability to simulate various error conditions

---

## Test Case 1: Empty Universe Error Handling
**Objective:** Verify error message when universe is empty

### Steps:
1. Select "Custom CSV" universe
2. Leave the text area empty (or clear any existing text)
3. Click "Run Screener"

### Expected Results:
- Error message displayed:
  - "❌ **Empty Universe**: No symbols found in the selected universe set. Please select a different universe or enter custom symbols."
- Warning message:
  - "⚠️ No symbols to screen. Please select a universe or enter custom symbols."
- Application does not crash
- Previous results (if any) remain visible

### Pass Criteria:
- ✅ Clear error messages displayed
- ✅ No application crash
- ✅ User can recover by selecting valid universe

---

## Test Case 2: Invalid Price Range Error Handling
**Objective:** Verify validation for invalid price ranges

### Steps:
1. Select "S&P 500" universe
2. Set Min Price to `$200.00`
3. Set Max Price to `$100.00` (less than min)
4. Observe warnings
5. Click "Run Screener"

### Expected Results:
- **Before running:**
  - Sidebar warning: "⚠️ **Invalid Price Range**: Min price must be less than max price. No price filtering will be applied. Please adjust the range."
- **After running:**
  - Warning: "⚠️ **Price filter not applied**: Invalid price range (min >= max). Showing all results with valid prices."
  - All symbols with valid prices shown (no filtering)
  - Filtering pipeline: "After Price Filter" = "Fetched" - "Missing Price"

### Pass Criteria:
- ✅ Warnings displayed in both locations
- ✅ No filtering applied (fail-safe behavior)
- ✅ No crash

---

## Test Case 3: Missing Alpaca Credentials (Fallback)
**Objective:** Verify fallback to Yahoo when Alpaca credentials missing

### Steps:
1. Ensure no Alpaca credentials set (unset env vars, leave UI fields empty)
2. Select "Alpaca Movers (Intraday)"
3. Select "S&P 500" universe
4. Observe warning before running
5. Click "Run Screener"

### Expected Results:
- **Before running:**
  - Warning: "⚠️ **Missing Alpaca API Keys**: No API credentials found. The app will fall back to Yahoo Finance data."
  - Instructions provided for setting up Alpaca
- **After running:**
  - Source badge: "⚠️ Alpaca (Fallback to Yahoo)"
  - Data fetched from Yahoo Finance for S&P 500 universe
  - No application crash

### Pass Criteria:
- ✅ Clear warning with actionable guidance
- ✅ Automatic fallback to Yahoo
- ✅ No crash

---

## Test Case 4: Invalid Alpaca Credentials (Fallback)
**Objective:** Verify fallback when Alpaca credentials are invalid

### Steps:
1. Select "Alpaca Movers (Intraday)"
2. Enter **invalid** credentials:
   - API Key: `invalid_key_test`
   - Secret: `invalid_secret_test`
3. Select "S&P 500" universe
4. Click "Run Screener"

### Expected Results:
- Alpaca API call fails (authentication error)
- Automatic fallback to Yahoo Finance
- Source badge: "⚠️ Alpaca (Fallback to Yahoo)"
- Data fetched successfully from Yahoo
- No application crash

### Pass Criteria:
- ✅ Graceful authentication error handling
- ✅ Automatic fallback successful
- ✅ No crash

---

## Test Case 5: TradingView Unavailable (Fallback)
**Objective:** Verify fallback when TradingView is unavailable

**Note:** This test may be difficult to execute without simulating a failure. You can:
- Test during TradingView API outage
- Modify code temporarily to force failure
- Use network blocking tools

### Steps:
1. Select "TradingView (Advanced)"
2. Select "S&P 500" universe
3. **Simulate TradingView failure** (if possible)
4. Click "Run Screener"

### Expected Results:
- TradingView API call fails
- Automatic fallback to Yahoo Finance
- Source badge: "⚠️ TradingView (Fallback to Yahoo)"
- Info message: "Session cookies may be required for real-time data"
- Data fetched from Yahoo for S&P 500
- Advanced fields NOT available in fallback
- No application crash

### Pass Criteria:
- ✅ Fallback to Yahoo successful
- ✅ Clear warning badge
- ✅ No crash

---

## Test Case 6: Invalid Symbols in Custom Universe
**Objective:** Verify handling of invalid/non-existent symbols

### Steps:
1. Select "Custom CSV" universe
2. Enter mix of valid and invalid symbols:
   ```
   AAPL, INVALID123, MSFT, FAKE456, GOOGL, NOTREAL789
   ```
3. Click "Run Screener"
4. Review filtering pipeline metrics

### Expected Results:
- Total Requested: 6
- Fetched: May vary (valid symbols fetched)
- Missing Price: Count of invalid symbols (likely 3: INVALID123, FAKE456, NOTREAL789)
- After Price Filter: Valid symbols within price range
- Results table shows only valid symbols
- No error popups or crashes

### Pass Criteria:
- ✅ Invalid symbols silently dropped
- ✅ Valid symbols processed
- ✅ "Missing Price" count accurate

---

## Test Case 7: Network Timeout Simulation
**Objective:** Verify behavior during network issues

**Note:** Difficult to test without simulating network conditions

### Steps:
1. **Simulate slow/unstable network** (if possible)
2. Select "Yahoo (EOD)" data source
3. Select "S&P 500" universe
4. Click "Run Screener"

### Expected Results:
- Spinner shows "Fetching data for X symbols..."
- If timeout occurs:
  - Error info panel displayed
  - Error message: "The Yahoo (EOD) data source encountered an error"
  - Suggestion: "Please check your configuration or try a different data source"
- Application remains stable

### Pass Criteria:
- ✅ Timeout handled gracefully
- ✅ Error message displayed
- ✅ No crash

---

## Test Case 8: Data Source Provider Error (General)
**Objective:** Verify consolidated error panel for provider failures

### Steps:
1. Force a provider error (modify credentials, network block, etc.)
2. Run screener
3. Look for error panel in results section

### Expected Results:
- Expandable error panel appears:
  - Title: "❌ **Data Source Error**"
  - Expanded by default
- Error panel shows:
  - **Provider:** Name of data source (e.g., "Alpaca Movers (Intraday)")
  - **Error:** Actual error message from provider
  - **Next Steps:** Actionable guidance for user
- Application does not crash

### Pass Criteria:
- ✅ Error panel displayed
- ✅ Clear, actionable error message
- ✅ No crash

---

## Test Case 9: Partial Data Fetch (Some Symbols Fail)
**Objective:** Verify handling when some symbols fetch successfully, others fail

### Steps:
1. Select "Custom CSV" universe
2. Enter a large mix (50+ symbols, include some invalid)
3. Click "Run Screener"
4. Review filtering pipeline

### Expected Results:
- Fetched: Count of successfully fetched symbols
- Missing Price: Count of failed symbols
- Results table shows only successful fetches
- "Missing Price" metric indicates partial failure
- No complete failure or crash

### Pass Criteria:
- ✅ Partial success handled
- ✅ Accurate counts in pipeline
- ✅ No crash

---

## Test Case 10: Cache Expiration and Re-fetch
**Objective:** Verify behavior when cache expires and data must be re-fetched

### Steps:
1. Enable Developer Mode
2. Select "Yahoo (EOD)", "Leveraged ETFs" universe
3. Click "Run Screener"
4. Note API call count (should be 1)
5. Wait 6+ minutes (cache TTL = 5 minutes)
6. Click "Run Screener" again (same settings)
7. Check API call count

### Expected Results:
- First run: Fetch cache miss, API call = 1
- After 6+ minutes: Cache expired, API call = 2
- Data re-fetched successfully
- No errors due to cache expiration

### Pass Criteria:
- ✅ Cache expiration handled smoothly
- ✅ Data re-fetched automatically
- ✅ No errors

---

## Test Case 11: Developer Mode Error Logging
**Objective:** Verify errors are logged in Debug Log

### Steps:
1. Enable Developer Mode
2. Clear Debug Log
3. Force an error (invalid Alpaca credentials, invalid symbols, etc.)
4. Run screener
5. Go to Debug Log → Errors tab

### Expected Results:
- Error count incremented in summary metrics
- Errors tab shows error details:
  - Error type (e.g., `AuthenticationError`)
  - Error message
  - Context (where error occurred)
  - Full traceback
- Full Log tab also shows error entry

### Pass Criteria:
- ✅ Error captured in Debug Log
- ✅ Full traceback available
- ✅ Error context provided

---

## Test Case 12: Multiple Consecutive Errors
**Objective:** Verify application handles multiple errors without crashing

### Steps:
1. Enable Developer Mode
2. Run screener with invalid Alpaca credentials → Error 1
3. Run screener with empty universe → Error 2
4. Run screener with invalid price range → Warning (not error)
5. Run screener with invalid custom symbols → Error 3
6. Check Debug Log → Errors tab

### Expected Results:
- All errors logged separately
- Application remains stable
- User can continue using app after each error
- Error count reflects all errors (3 in this case)

### Pass Criteria:
- ✅ All errors logged
- ✅ Application stable
- ✅ User can recover

---

## Test Case 13: Validation Error Recovery
**Objective:** Verify user can recover from validation errors

### Steps:
1. Set invalid price range (min > max)
2. Observe warning
3. Click "Run Screener" (should work with warning)
4. Correct price range (min < max)
5. Run screener again

### Expected Results:
- First run: Warning displayed, no filtering
- Second run: Warning gone, filtering applied correctly
- User can easily correct and re-run

### Pass Criteria:
- ✅ Warning clears when corrected
- ✅ Easy recovery path

---

## Test Case 14: Session State Persistence Across Errors
**Objective:** Verify session state remains intact after errors

### Steps:
1. Run successful screener with S&P 500
2. Results displayed correctly
3. Switch to invalid settings and run (causes error)
4. Switch back to S&P 500 and run again

### Expected Results:
- After error, previous valid results still available (in session state)
- Cache may be reused if within TTL
- Application state not corrupted by error

### Pass Criteria:
- ✅ Session state intact after error
- ✅ Can resume normal operation

---

## Test Case 15: Error Message Clarity and Actionability
**Objective:** Verify all error messages provide clear guidance

### Review all error messages in the application:

**Empty Universe:**
- Message: "❌ **Empty Universe**: No symbols found in the selected universe set. Please select a different universe or enter custom symbols."
- ✅ Clear and actionable

**Invalid Price Range:**
- Message: "⚠️ **Invalid Price Range**: Min price must be less than max price. No price filtering will be applied. Please adjust the range."
- ✅ Clear and actionable

**Missing Alpaca Credentials:**
- Message: "⚠️ **Missing Alpaca API Keys**: No API credentials found..." (includes setup instructions)
- ✅ Clear and actionable

**Provider Error:**
- Shows provider, error, and next steps
- ✅ Clear and actionable

### Pass Criteria:
- ✅ All error messages are clear
- ✅ All errors provide actionable guidance
- ✅ No cryptic technical jargon

---

## Test Case 16: Fallback Chain (Multi-level Fallback)
**Objective:** Verify fallback behavior is consistent

### Fallback Hierarchy:
1. **Primary:** User-selected data source (Alpaca or TradingView)
2. **Secondary:** Yahoo Finance
3. **Tertiary:** Mock data (if Yahoo also fails - for demo purposes)

### Steps:
1. Select Alpaca with invalid credentials
2. Observe fallback to Yahoo
3. Source badge shows: "⚠️ Alpaca (Fallback to Yahoo)"

### Expected Results:
- Fallback always goes to Yahoo Finance
- Yahoo is considered the "safe" fallback
- If Yahoo fails, error displayed (no further fallback in production)

### Pass Criteria:
- ✅ Consistent fallback behavior
- ✅ Clear indication of fallback source

---

## Test Case 17: Error Handling with Developer Mode Disabled
**Objective:** Verify errors still handled gracefully without Debug Log

### Steps:
1. **Disable** Developer Mode
2. Force various errors (invalid credentials, empty universe, etc.)
3. Observe error handling

### Expected Results:
- Errors still caught and handled
- Error messages/warnings still displayed in UI
- Fallbacks still work
- Application does not crash
- Debug Log not visible (as expected)

### Pass Criteria:
- ✅ All error handling works without Debug Log
- ✅ No crashes

---

## Test Case 18: Rapid Error Triggering (Stress Test)
**Objective:** Verify stability under rapid error conditions

### Steps:
1. Rapidly switch between settings that cause errors:
   - Invalid price range
   - Invalid universe
   - Invalid data source credentials
2. Click "Run Screener" rapidly between changes
3. Check for crashes, hangs, or UI corruption

### Expected Results:
- Application remains stable
- Each error handled independently
- No crashes or freezes
- UI remains responsive

### Pass Criteria:
- ✅ Application stable under stress
- ✅ No crashes or hangs

---

## Test Case 19: Error Handling Documentation Review
**Objective:** Verify error handling is well documented

### Check:
1. README.md mentions error handling features
2. Test scenarios (this document) cover error handling
3. Code comments explain error handling logic

### Pass Criteria:
- ✅ Error handling documented in README
- ✅ Test scenarios comprehensive
- ✅ Code has adequate comments

---

## Test Case 20: User Experience During Errors
**Objective:** Verify overall UX is positive even during errors

### Evaluate:
1. Error messages are friendly, not technical
2. Next steps always provided
3. User can recover without restarting app
4. No data loss on errors
5. Previous valid results preserved

### Pass Criteria:
- ✅ Friendly error messages
- ✅ Clear recovery path
- ✅ No data loss
- ✅ Positive UX maintained

---

## Fallback Behavior Summary

| Primary Source | Fallback | Trigger |
|----------------|----------|---------|
| Alpaca Movers | Yahoo Finance | Missing/invalid credentials, API error, timeout, rate limit |
| TradingView Advanced | Yahoo Finance | API error, timeout, rate limit, session cookies required |
| Yahoo (EOD) | Error message (no further fallback) | API error, timeout |

## Error Types Handled

1. **Validation Errors:**
   - Empty universe
   - Invalid price range
   - Invalid input format

2. **Authentication Errors:**
   - Missing API credentials
   - Invalid API credentials

3. **Network Errors:**
   - Timeout
   - Connection refused
   - Rate limiting

4. **Data Errors:**
   - Invalid symbols
   - Missing price data
   - Partial fetch failures

5. **Provider Errors:**
   - API unavailable
   - Unexpected response format
   - Service outage

## Notes
- All errors are logged in Developer Mode Debug Log
- Fallback mechanisms prevent complete application failure
- User always has a recovery path
- No errors cause data loss or state corruption

## Related Files
- `app.py` - Error handling and validation logic
- `src/data_sources/*.py` - Provider-specific error handling
