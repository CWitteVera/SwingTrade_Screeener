# SwingTrade Stock Screener 📈

A modular Streamlit-based stock screener for filtering and analyzing stocks across different universes and data sources.

## Features

- **🤖 Auto-Run Mode**: NEW! Automatically run multiple screening scenarios without manual selection
  - Test all combinations of universes, price ranges, and data sources
  - Get consolidated results instantly
  - Perfect for quick exploration and testing
- **Multiple Universe Sets**: Screen stocks from S&P 500, NASDAQ-100, All NMS stocks, Leveraged ETFs, or custom symbol lists
- **Multiple Data Sources**: 
  - Yahoo Finance (EOD data) - End-of-day data with basic fields
  - **Advanced Data (financialdata.net)** - Comprehensive market data with prices, fundamentals, and technical indicators
  - **Alpaca Movers (Intraday)** - Real-time movers lists with intraday data
- **Alpaca Movers Lists**:
  - Most Actives - Top stocks by trading activity
  - Market Movers (Gainers) - Top gaining stocks
  - Market Movers (Losers) - Top losing stocks
  - Top Volume - Highest volume stocks
- **Price Range Filter**: Filter stocks by minimum and maximum price
- **Real-time Results**: View filtered results with price, volume, and change information
- **Data Caching**: Efficient caching to reduce API calls and improve performance
- **Export Capability**: Download results as CSV

## Installation

1. Clone the repository:
```bash
git clone https://github.com/CWitteVera/SwingTrade_Screeener.git
cd SwingTrade_Screeener
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

**Important**: After creating the `.env` file, edit it and replace the placeholder values with your actual API keys:
- `FINANCIALDATA_API_KEY` - Get from [FinancialData.Net](https://financialdata.net/)
- `ALPACA_API_KEY` and `ALPACA_API_SECRET` - Get from [Alpaca Markets](https://alpaca.markets/)

The application will automatically load these variables when it starts.

## Usage

Run the Streamlit application:
```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

### Advanced Data (financialdata.net) Setup

To use the Advanced Data source with comprehensive market data:

1. **Get Your API Key**:
   - Sign up at [FinancialData.Net](https://financialdata.net/)
   - Navigate to your account dashboard
   - Generate an API key

2. **Configure API Key**:

   You have three options to provide your API key (in order of recommendation):

   **Option A: .env File (Recommended)**
   ```bash
   # If you haven't already, copy the example file:
   cp .env.example .env
   
   # Edit .env and set your key:
   # FINANCIALDATA_API_KEY=your_actual_api_key_here
   ```
   The application automatically loads the `.env` file on startup.

   **Option B: Environment Variable**
   ```bash
   export FINANCIALDATA_API_KEY="your_api_key_here"
   ```

   **Option C: Streamlit Secrets**
   Create `.streamlit/secrets.toml`:
   ```toml
   FINANCIALDATA_API_KEY = "your_api_key_here"
   ```

3. **Features**:
   - **Real-time Quotes**: Current stock prices and market data
   - **Technical Indicators**: RSI, MACD, SMA 50/150/200, EMA 5/10/20/50, Relative Volume
   - **Fundamentals**: Market Cap, P/E Ratio, EPS, Revenue, Profit Margin
   - **Multiple Timeframes**: Daily (1d), Hourly (1h), 5-minute (5m)
   - **Smart Caching**: 5-minute cache reduces API calls

4. **Field Selection**:
   - **Default Fields**: Symbol, Price, Volume, Market Cap
   - **Optional Technical Indicators**: Relative Volume (10d), RSI, MACD, SMA 50/150/200
   - **Optional Moving Averages**: EMA 5, 10, 20, 50 periods
   - **Optional Fundamentals**: P/E Ratio, EPS

**Note on Fallback**: If the API key is not provided or invalid, the application automatically falls back to Yahoo Finance data with a warning message.

### Alpaca API Setup (Optional)

To use the Alpaca Movers (Intraday) data source:

1. **Create an Alpaca Account**:
   - Sign up at [Alpaca Markets](https://alpaca.markets/)
   - Navigate to your account dashboard
   - Generate API keys (use Paper Trading keys for testing)

2. **Configure API Credentials**:

   You have three options to provide your Alpaca API credentials (in order of recommendation):

   **Option A: .env File (Recommended)**
   ```bash
   # If you haven't already, copy the example file:
   cp .env.example .env
   
   # Edit .env and set your credentials:
   # ALPACA_API_KEY=your_actual_api_key_here
   # ALPACA_API_SECRET=your_actual_api_secret_here
   ```
   The application automatically loads the `.env` file on startup.

   **Option B: Environment Variables**
   ```bash
   export ALPACA_API_KEY="your_api_key_here"
   export ALPACA_API_SECRET="your_api_secret_here"
   ```

   **Option C: UI Input**
   - Select "Alpaca Movers (Intraday)" in the Universe Source
   - Expand "API Credentials" section in sidebar
   - Enter your API Key and Secret

3. **Select Movers List**:
   - Most Actives - Top stocks by trading activity
   - Market Movers - Gainers - Stocks with highest price increases
   - Market Movers - Losers - Stocks with highest price decreases
   - Top Volume - Stocks with highest trading volume

4. **Adjust Settings**:
   - Number of Top Movers: 10-100 (default: 50)
   - Results are cached for 45 seconds to reduce API calls

**Note on Fallback**: If Alpaca credentials are not provided or invalid, the application automatically falls back to Yahoo Finance data for the selected universe set.

**Rate Limits**: 
- Alpaca has rate limits on API calls
- The app caches movers data for 30-60 seconds to minimize API usage
- Consider using Paper Trading API for development/testing
- See [Alpaca API Documentation](https://alpaca.markets/docs/api-references/market-data-api/) for current limits

## Migration Notes

### TradingView Source Removed

The TradingView (Advanced) data source has been removed and replaced with **Advanced Data (financialdata.net)**. 

**What changed:**
- TradingView integration has been completely removed
- New Advanced Data (financialdata.net) provider offers similar functionality with better reliability
- API key is now required for advanced features (free tier available)

**If you were using TradingView:**
1. Switch to "Advanced Data (financialdata.net)" in the data source selector
2. Get a free API key from [FinancialData.Net](https://financialdata.net/)
3. Configure the API key using one of the methods above
4. Select the same technical indicators and fundamentals you were using before

## Project Structure

```
SwingTrade_Screeener/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── src/
│   ├── universe_sets.py           # Stock universe definitions
│   └── data_sources/              # Data source modules
│       ├── __init__.py
│       ├── base.py                # Base data source interface
│       ├── yahoo.py               # Yahoo Finance implementation
│       ├── tradingview.py         # TradingView Advanced implementation
│       └── alpaca.py              # Alpaca placeholder
└── README.md
```

## Universe Sets

- **All NMS**: Major stocks from S&P 500 and NASDAQ-100 combined
- **S&P 500**: Top 50 S&P 500 stocks (demo subset)
- **NASDAQ-100**: Top 50 NASDAQ-100 stocks (demo subset)
- **Leveraged ETFs**: TQQQ, SQQQ, SPXL, SPXS, UPRO, SOXL, SOXS, TECL, TECS, TNA, TZA, TMF, FAS, NUGT, FNGU
- **Custom CSV**: Enter your own comma-separated list of symbols

## How to Use

### Auto-Run Mode (Recommended for Quick Results)

**NEW!** Enable **Auto-Run Mode** to automatically screen multiple scenarios without any manual selection:

1. Launch the app: `streamlit run app.py`
2. Check the box: **🤖 Enable Auto-Run Mode**
3. Wait while the app automatically runs through various scenarios:
   - Multiple universes (S&P 500, NASDAQ-100, Leveraged ETFs, All NMS)
   - Multiple price ranges (Penny Stocks, Swing Trades, High Value)
   - Available data sources (Yahoo, Advanced Data, Alpaca)
4. View consolidated results from all scenarios
5. Download any result set as CSV

**Benefits:**
- **No manual selection needed** - just enable and go
- **See all results at once** - comprehensive view across scenarios
- **Faster exploration** - quickly find which combinations return results
- **Perfect for testing** - validates your API setup across all data sources

### Manual Mode (Advanced Users)

For manual control over screening parameters:

1. **Uncheck Auto-Run Mode** (if enabled)
2. **Select Universe Source**: Choose between Yahoo (EOD), Advanced Data (financialdata.net), or Alpaca Movers (Intraday)
   - **Advanced Data Users**: Optionally select technical indicators (RSI, MACD, EMAs, etc.)
   - **Alpaca Users**: Choose movers list type (Most Actives, Gainers, Losers, Top Volume)
3. **Select Universe Set**: Pick from predefined universe sets or enter custom symbols
4. **Set Price Range**: Choose preset (Penny Stocks, Swing Trades, All Prices) or enter custom range
5. **Run Screener**: Click the "Run Screener" button to fetch and filter stocks
6. **View Results**: See filtered stocks with price, volume, and change information
   - Advanced Data: Technical indicators and fundamentals appear as additional columns
   - Watch for "Results truncated" badge if limit is reached
7. **Download**: Export results to CSV for further analysis

## Notes

- **Yahoo Finance data source** is fully functional and fetches real EOD data
  - Best for simple price/volume screening with reliable data
- **TradingView Advanced data source** provides 3,000+ fields including technicals and fundamentals
  - Access to RSI, MACD, Stochastic, Bollinger Bands, Moving Averages, and more
  - Result limit (default: 500) keeps UI responsive
  - Caches data for 5 minutes based on universe + field combination
  - Automatically falls back to Yahoo Finance if TradingView is unavailable
- **Alpaca Movers data source** fetches real-time intraday movers lists (requires API credentials)
  - Supports Most Actives, Market Movers (Gainers/Losers), and Top Volume lists
  - Caches data for 45 seconds to reduce API calls
  - Automatically falls back to Yahoo Finance if credentials are missing/invalid
- Data is cached to improve performance and reduce API calls
- Universe sets contain demo subsets of major indices for faster screening

## Performance & Limits

### Caching Strategy

The app implements a multi-layer caching system to optimize performance and reduce API calls:

#### 1. Universe Symbol Lists (Long TTL)
- **Cache Duration**: 1 hour
- **Cache Key**: `universe_set + custom_symbols`
- **Rationale**: Universe lists change infrequently (S&P 500, NASDAQ-100, etc.)
- **Benefit**: Eliminates repeated list lookups when switching between sources or adjusting filters

#### 2. Price Lookups per Source+Symbol+Date
- **Yahoo Finance**: Cached at yfinance library level (session-based)
- **TradingView**: 5-minute cache per universe + field set combination
  - Cache Key: `universe_key + fields + limit`
  - Benefit: Reuses data when only slider adjustments occur
- **Alpaca Movers**: 45-second cache per movers type + top_n
  - Cache Key: `movers_type + top_n`
  - Cache Duration: 45 seconds
  - Benefit: Reduces API calls during rapid UI interactions

#### 3. Fetch & Filter Pipeline (Streamlit Cache)
- **Cache Duration**: 5 minutes
- **Cache Key**: `source + symbols + min_price + max_price + source_params`
- **Benefit**: When only price slider moves, the entire fetch is cached
- **Invalidation**: Automatic after TTL or when parameters change

### Optimization: Avoid Recompute on Slider Changes

The caching system is designed to avoid expensive API calls when only the price slider changes:

1. **Initial Fetch**: Data is fetched from provider and cached with price range
2. **Slider Adjustment**: If you adjust the price slider to values already queried, the cached result is reused
3. **In-Memory Refiltering**: For new price ranges, the cached unfiltered data could be reused (future enhancement)

**Current Behavior**: Each unique price range creates a new cache entry
**Future Enhancement**: Cache raw fetched data separately, then apply price filter in-memory

### Rate Limits & Resilience

#### Yahoo Finance (EOD)
- **Rate Limits**: Generally permissive for reasonable usage
- **Fallback**: Mock data generation if API is unavailable
- **Error Handling**: Graceful degradation with informative messages

#### TradingView (Advanced)
- **Rate Limits**: Undocumented, but exists
- **Fallback**: Automatic fallback to Yahoo Finance if unavailable
- **Warning**: Yellow badge indicates fallback mode
- **Session Cookies**: May be required for real-time data access

#### Alpaca (Intraday)
- **Rate Limits**: 
  - Free tier: 200 requests/minute
  - Paid tiers: Higher limits
  - Cached for 45 seconds to stay well within limits
- **Fallback**: Automatic fallback to Yahoo Finance if:
  - Credentials missing or invalid
  - API error or timeout
  - Rate limit exceeded
- **Warning**: Yellow badge indicates fallback mode

### Validation & Error Handling

#### Input Validation
- **Price Range**: Min price must be < max price
  - Invalid ranges show warning and disable filtering
  - Previous valid results are preserved
- **Empty Universes**: Error message if no symbols in selected universe
- **Missing API Keys**: Clear actionable message for Alpaca setup

#### Error Consolidation
- Provider errors are caught and displayed in a consolidated error panel
- Each error shows:
  - Provider name
  - Error message
  - Actionable next steps
- Errors don't crash the app - fallbacks are attempted first

#### Graceful Degradation
1. **Provider Failure**: Falls back to Yahoo Finance
2. **Yahoo Failure**: Falls back to mock data (for demo purposes)
3. **Partial Failures**: Symbols with missing data are counted and reported in diagnostics

### Diagnostics & Monitoring

#### Filtering Pipeline Counters
The app displays four key metrics showing data flow through the pipeline:

1. **Total Requested**: Symbols in selected universe
2. **Fetched**: Symbols successfully retrieved from provider
3. **Missing Price**: Symbols dropped due to missing/invalid price data
4. **After Price Filter**: Symbols passing the price range filter

These counters help you understand:
- Data quality issues (high "Missing Price" count)
- Filter effectiveness (gap between "Fetched" and "After Price Filter")
- Provider reliability (gap between "Requested" and "Fetched")

#### Source Badge
A compact badge near the results table shows:
- **Active Data Source**: Yahoo EOD, TradingView, or Alpaca Intraday
- **Fallback Status**: Yellow warning if using fallback provider
- **Data Freshness**: EOD (delayed) vs. Intraday (real-time)

### Scalability for Real-Time Scanning

The app is architected to support future real-time monitoring without requiring a rewrite:

#### State Management Structures
1. **Symbol Directory**: Central registry mapping symbols to universes and last prices
2. **Prior Close Cache**: Historical closing prices for change calculations
3. **Alert Thresholds**: Reserved for user-defined alert conditions
4. **Scan Results History**: Rolling buffer of recent scans for trend analysis

#### Future Enhancements
These structures enable:
- **Incremental Updates**: Only fetch changed symbols, not full universe
- **Cross-Session Persistence**: Cache layer (Redis) for multi-user scenarios
- **Alert Triggering**: Real-time alerts without full rescans
- **Historical Comparison**: Trend analysis across multiple scans

#### Architecture Reference
The design follows patterns from high-performance real-time screeners:
- Separate symbol directory from live price data
- Cache prior closes for efficient change calculations
- Rolling buffers for recent history
- Modular data source interface for easy extension

For more details on fast real-time screening architecture, see:
[How to Build a Blazing Fast Real-Time Stock Screener](https://databento.com/blog/how-to-build-a-blazing-fast-real-time-stock-screener-with-python)

## License

MIT License