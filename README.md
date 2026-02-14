# SwingTrade Stock Screener 📈

A modular Streamlit-based stock screener for filtering and analyzing stocks across different universes and data sources.

## Features

- **Multiple Universe Sets**: Screen stocks from S&P 500, NASDAQ-100, All NMS stocks, Leveraged ETFs, or custom symbol lists
- **Multiple Data Sources**: 
  - Yahoo Finance (EOD data) - End-of-day data with basic fields
  - **TradingView (Advanced)** - 3,000+ fields including technicals and fundamentals
  - **Alpaca Movers (Intraday)** - Real-time movers lists with intraday data
- **Alpaca Movers Lists**:
  - Most Actives - Top stocks by trading activity
  - Market Movers (Gainers) - Top gaining stocks
  - Market Movers (Losers) - Top losing stocks
  - Top Volume - Highest volume stocks
- **Price Range Filter**: Filter stocks by minimum and maximum price
- **Real-time Results**: View filtered results with price, volume, and change information
- **Data Caching**: Efficient caching to reduce API calls and improve performance (45 seconds for Alpaca movers)
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

## Usage

Run the Streamlit application:
```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

### Alpaca API Setup (Optional)

To use the Alpaca Movers (Intraday) data source:

1. **Create an Alpaca Account**:
   - Sign up at [Alpaca Markets](https://alpaca.markets/)
   - Navigate to your account dashboard
   - Generate API keys (use Paper Trading keys for testing)

2. **Configure API Credentials**:

   **Option A: Environment Variables (Recommended)**
   ```bash
   export ALPACA_API_KEY="your_api_key_here"
   export ALPACA_API_SECRET="your_api_secret_here"
   ```

   **Option B: UI Input**
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

### TradingView Advanced (Optional)

To use the TradingView (Advanced) data source with 3,000+ fields:

1. **Features**:
   - **Large Field Set**: Access to technicals (RSI, MACD, Bollinger Bands, etc.) and fundamentals (market cap, volume, etc.)
   - **Advanced Filters**: Select from 13+ technical indicators and moving averages
   - **Result Limiting**: Cap at 500 results (adjustable) to keep UI responsive
   - **Smart Caching**: 5-minute cache reduces API calls when adjusting filters

2. **Field Selection**:
   - **Default Fields** (always included): Symbol, Price (close), Volume, Change, Change %, Market Cap
   - **Optional Technical Indicators**: RSI, MACD, Stochastic, Bollinger Bands, VWAP, Relative Volume
   - **Optional Moving Averages**: EMA 5, 10, 20, 50 periods

3. **Authentication & Data Access**:
   - **Delayed Data**: Works out-of-the-box with public TradingView data
   - **Real-time Data**: May require session cookies from TradingView
   - **Fallback**: Automatically falls back to Yahoo Finance if TradingView is unavailable
   - The app will display a warning badge if using fallback data

4. **Usage Tips**:
   - Start with default fields to test connectivity
   - Add advanced fields only when needed to minimize data transfer
   - Use Result Limit slider to control response size
   - Watch for "Results truncated" badge if limit is reached
   - Data is cached for 5 minutes based on universe + field combination

5. **Rate Limits & Performance**:
   - TradingView has rate limits on scanner API calls
   - Caching strategy reduces repeated API calls
   - Result limit (default: 500) keeps UI responsive
   - Consider filtering by universe set before applying technical filters

**Note on Data Quality**: TradingView provides comprehensive data but may require authentication for real-time access. The app will automatically fall back to Yahoo Finance (delayed data) if TradingView is unavailable or requires authentication.

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

1. **Select Universe Source**: Choose between Yahoo (EOD), TradingView (Advanced), or Alpaca Movers (Intraday)
   - **TradingView Users**: Optionally select advanced technical indicators and set result limit
2. **Select Universe Set**: Pick from predefined universe sets or enter custom symbols
3. **Set Price Range**: Define minimum and maximum price filters
4. **Run Screener**: Click the "Run Screener" button to fetch and filter stocks
5. **View Results**: See filtered stocks with price, volume, and change information
   - **TradingView**: Advanced fields (RSI, MACD, etc.) appear as additional columns on the right
   - Watch for "Results truncated" badge if result limit is reached
6. **Download**: Export results to CSV for further analysis

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

## License

MIT License