# Manual Test Scenarios

This folder contains comprehensive manual test scenarios for the SwingTrade Stock Screener application.

## Overview

These test scenarios are designed to be executed manually by developers or QA testers to verify the application's functionality across different features and edge cases.

## Test Scenarios

### 01. Universe Selections (`01_universe_selections.md`)
**Coverage:** Universe set selection, caching, custom CSV parsing  
**Test Cases:** 9  
**Key Areas:**
- S&P 500, NASDAQ-100, All NMS, Leveraged ETFs universes
- Custom CSV input (valid, empty, mixed format)
- Universe cache behavior
- Performance when switching universes

### 02. Price Range Behavior (`02_price_range_behavior.md`)
**Coverage:** Price filtering logic, validation, edge cases  
**Test Cases:** 12  
**Key Areas:**
- Default, narrow, high, and low price ranges
- Invalid price ranges (min >= max)
- Extreme values
- Price filter with different data sources
- Cache behavior with price adjustments
- Visual slider display

### 03. Trend Template Filter (`03_trend_template_filter.md`)
**Coverage:** Future enhancement placeholder  
**Test Cases:** 3 (planned)  
**Status:** 🚧 NOT YET IMPLEMENTED  
**Key Areas:**
- Moving average crossovers (planned)
- Momentum indicators (planned)
- TradingView workaround (current alternative)

### 04. Alpaca Intraday Source (`04_alpaca_intraday_source.md`)
**Coverage:** Alpaca Markets API integration, intraday data  
**Test Cases:** 15  
**Key Areas:**
- API authentication (environment variables, UI input)
- Movers lists (Most Actives, Gainers, Losers, Top Volume)
- Cache behavior (45-second TTL)
- Fallback to Yahoo Finance
- Rate limiting
- Developer Mode logging

### 05. TradingView Advanced Fields (`05_tradingview_advanced_fields.md`)
**Coverage:** TradingView scanner API, technical indicators  
**Test Cases:** 20  
**Key Areas:**
- Default fields (close, volume, change, market cap)
- Technical indicators (RSI, MACD, Stochastic, Bollinger Bands, VWAP)
- Moving averages (EMA 5, 10, 20, 50)
- Result limit enforcement
- Cache behavior (5-minute TTL)
- Fallback to Yahoo Finance
- CSV export with advanced fields

### 06. Error Handling and Fallback (`06_error_handling_fallback.md`)
**Coverage:** Error handling, validation, fallback mechanisms  
**Test Cases:** 20  
**Key Areas:**
- Empty universe handling
- Invalid price range validation
- Missing/invalid API credentials
- Provider failures and fallbacks
- Invalid symbols
- Network timeouts
- Developer Mode error logging
- User experience during errors

## Running the Tests

### Prerequisites
1. Application installed and dependencies available
2. Python 3.8+ environment
3. Streamlit installed (`pip install -r requirements.txt`)
4. **Optional:** Alpaca API credentials for full Alpaca testing
5. Internet connection for data source APIs

### Execution
1. Start the application:
   ```bash
   streamlit run app.py
   ```

2. Open the test scenario file you want to execute

3. Follow the steps in each test case sequentially

4. Record results (pass/fail) and any observations

5. For Developer Mode tests:
   - Enable "Developer Mode" in the sidebar
   - Use the Debug Log to verify internal behavior

### Tips for Testers
- **Enable Developer Mode** for detailed debugging information
- Use **smaller universes** (e.g., Leveraged ETFs) for faster testing
- **Clear Debug Log** before each major test to isolate results
- **Take screenshots** of any unexpected behavior
- **Export Debug Log CSV** for detailed analysis
- Test in **different network conditions** if possible

## Test Coverage Summary

| Area | Test Cases | Coverage |
|------|------------|----------|
| Universe Selections | 9 | ✅ Complete |
| Price Range Behavior | 12 | ✅ Complete |
| Trend Template Filter | 3 | 🚧 Placeholder (future) |
| Alpaca Intraday | 15 | ✅ Complete |
| TradingView Advanced | 20 | ✅ Complete |
| Error Handling | 20 | ✅ Complete |
| **Total** | **79** | **76 current, 3 planned** |

## Test Priority Levels

### High Priority (Run for every release)
- Universe Selections: Test Cases 1-5 (basic universes)
- Price Range Behavior: Test Cases 1-5 (basic filtering)
- Alpaca Intraday: Test Cases 1, 9, 10 (auth and fallback)
- TradingView Advanced: Test Cases 1-3, 13 (basic fields and fallback)
- Error Handling: Test Cases 1-4, 8 (validation and provider errors)

### Medium Priority (Run for major releases)
- All remaining test cases in Universe Selections
- All remaining test cases in Price Range Behavior
- All remaining test cases in Error Handling
- Alpaca: Cache and performance tests
- TradingView: Advanced field combinations

### Low Priority (Run as needed)
- Stress tests (rapid changes, multiple errors)
- Performance tests (max fields, max limits)
- Developer Mode specific tests
- Edge cases and extreme values

## Known Issues / Expected Failures
- **Trend Template Filter:** All tests will fail as feature is not implemented
- **TradingView Fallback:** Difficult to test without simulating API failure
- **Network Timeout:** Requires network simulation tools
- **Alpaca Rate Limiting:** May require intentional over-usage

## Reporting Issues

When reporting issues found during testing, include:
1. **Test Scenario:** Which test file and test case number
2. **Steps to Reproduce:** Exact steps followed
3. **Expected Result:** What should have happened
4. **Actual Result:** What actually happened
5. **Screenshots:** Visual evidence (especially for UI issues)
6. **Debug Log:** Export Debug Log CSV if Developer Mode was enabled
7. **Environment:** OS, Python version, browser (for Streamlit)

## Contributing

To add new test scenarios:
1. Create a new markdown file: `NN_feature_name.md`
2. Follow the existing format:
   - Purpose section
   - Prerequisites section
   - Test cases with Steps/Expected Results/Pass Criteria
   - Notes section
   - Related Files section
3. Update this README with the new test scenario
4. Update the Test Coverage Summary table

## Automation Considerations

While these are currently manual tests, they could be automated in the future using:
- **Streamlit Testing Framework** (when available)
- **Selenium/Playwright** for UI automation
- **pytest** for unit/integration tests
- **Custom test harness** for data source mocking

Priority for automation:
1. Price range validation logic
2. Universe selection and caching
3. Data source fallback mechanisms
4. Error handling paths

## Change Log

- **2024-XX-XX:** Initial test scenarios created
  - 6 test scenario files
  - 79 total test cases (76 current, 3 planned)
  - Comprehensive coverage of core features

## Related Documentation
- [Main README](../README.md) - Application overview and setup
- [PRICE_RANGE_FEATURE_MAPPING.md](../PRICE_RANGE_FEATURE_MAPPING.md) - Price range feature documentation
- [Source Code](../app.py) - Main application code
- [Data Sources](../src/data_sources/) - Data source implementations
