# SwingTrade Stock Screener 📈

A modular Streamlit-based stock screener for filtering and analyzing stocks across different universes and data sources.

## Features

- **Multiple Universe Sets**: Screen stocks from S&P 500, NASDAQ-100, All NMS stocks, Leveraged ETFs, or custom symbol lists
- **Multiple Data Sources**: 
  - Yahoo Finance (EOD data) - Fully functional
  - TradingView (Advanced) - Placeholder for future implementation
  - Alpaca Movers (Intraday) - Placeholder for future implementation
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

## Usage

Run the Streamlit application:
```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

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
│       ├── tradingview.py         # TradingView placeholder
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
2. **Select Universe Set**: Pick from predefined universe sets or enter custom symbols
3. **Set Price Range**: Define minimum and maximum price filters
4. **Run Screener**: Click the "Run Screener" button to fetch and filter stocks
5. **View Results**: See filtered stocks with price, volume, and change information
6. **Download**: Export results to CSV for further analysis

## Notes

- Yahoo Finance data source is fully functional and fetches real EOD data
- TradingView and Alpaca data sources are placeholders for future API integration
- Data is cached for 5 minutes to improve performance and reduce API calls
- Universe sets contain demo subsets of major indices for faster screening

## License

MIT License