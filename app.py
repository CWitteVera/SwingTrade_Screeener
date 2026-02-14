"""
SwingTrade Stock Screener
A Streamlit app for filtering stocks by price and universe
"""
import streamlit as st
import pandas as pd
from typing import List, Dict, Optional
import sys
import os
from datetime import datetime, date

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from universe_sets import get_universe_symbols
from data_sources import YahooDataSource, TradingViewDataSource, AlpacaDataSource


# Page configuration
st.set_page_config(
    page_title="SwingTrade Stock Screener",
    page_icon="📈",
    layout="wide"
)


# ============================================================================
# STATE MANAGEMENT FOR REAL-TIME SCANNING SCALABILITY
# ============================================================================
# These structures prepare the app for future real-time monitoring features
# without requiring a rewrite of the core pipeline

def init_session_state():
    """
    Initialize session state for scalable real-time scanning
    
    Scalability Pattern:
    - symbol_directory: Central registry of all symbols across universes
    - prior_close_cache: Cache of prior closing prices (key: symbol+date)
    - alert_thresholds: User-defined alert conditions for real-time monitoring
    - scan_results_history: Rolling buffer of recent scan results
    
    These structures enable:
    1. Incremental updates (only changed symbols)
    2. Cross-session persistence (Redis/cache layer in production)
    3. Alert triggering without full rescans
    4. Historical comparison for trend analysis
    """
    if 'symbol_directory' not in st.session_state:
        # Symbol directory: Maps symbol -> {universe, last_price, last_update}
        st.session_state['symbol_directory'] = {}
    
    if 'prior_close_cache' not in st.session_state:
        # Prior close cache: Maps (symbol, date) -> close_price
        # Used for change calculations in real-time scenarios
        st.session_state['prior_close_cache'] = {}
    
    if 'alert_thresholds' not in st.session_state:
        # Alert thresholds: Maps symbol -> {min_price, max_price, volume_threshold}
        # Reserved for future real-time alert features
        st.session_state['alert_thresholds'] = {}
    
    if 'scan_results_history' not in st.session_state:
        # Scan results history: List of (timestamp, results_df) tuples
        # Limited to last N scans for trend analysis
        st.session_state['scan_results_history'] = []


def update_symbol_directory(symbols: List[str], universe_set: str):
    """
    Update symbol directory with current universe
    
    Args:
        symbols: List of symbols in current scan
        universe_set: Name of the universe set
    """
    for symbol in symbols:
        if symbol not in st.session_state['symbol_directory']:
            st.session_state['symbol_directory'][symbol] = {
                'universes': set(),
                'last_price': None,
                'last_update': None
            }
        st.session_state['symbol_directory'][symbol]['universes'].add(universe_set)


def update_prior_close_cache(df: pd.DataFrame, scan_date: date = None):
    """
    Update prior close cache with latest prices
    
    Args:
        df: DataFrame with symbol and price columns
        scan_date: Date of the scan (defaults to today)
    """
    if scan_date is None:
        scan_date = date.today()
    
    for _, row in df.iterrows():
        symbol = row.get('symbol')
        price = row.get('price')
        if symbol and price:
            cache_key = (symbol, scan_date.isoformat())
            st.session_state['prior_close_cache'][cache_key] = price
            
            # Update symbol directory
            if symbol in st.session_state['symbol_directory']:
                st.session_state['symbol_directory'][symbol]['last_price'] = price
                st.session_state['symbol_directory'][symbol]['last_update'] = datetime.now()


def add_scan_to_history(results_df: pd.DataFrame, max_history: int = 10):
    """
    Add current scan results to history
    
    Args:
        results_df: DataFrame with scan results
        max_history: Maximum number of scans to keep in history
    """
    timestamp = datetime.now()
    st.session_state['scan_results_history'].append((timestamp, results_df.copy()))
    
    # Limit history size
    if len(st.session_state['scan_results_history']) > max_history:
        st.session_state['scan_results_history'] = st.session_state['scan_results_history'][-max_history:]


# ============================================================================
# CACHING FUNCTIONS
# ============================================================================


def parse_custom_symbols(text: str) -> List[str]:
    """Parse comma-separated symbols from text input"""
    if not text:
        return []
    return [s.strip().upper() for s in text.replace('\n', ',').split(',') if s.strip()]


@st.cache_data(ttl=3600)  # Cache for 1 hour (long TTL - universe lists change infrequently)
def get_cached_universe_symbols(universe_set: str, custom_symbols_tuple: tuple = None) -> List[str]:
    """
    Cached wrapper for getting universe symbols
    
    Caching Strategy:
    - Universe symbol lists are static and change infrequently
    - Long TTL (1 hour) to minimize recomputation
    - Cache key: universe_set + custom_symbols_tuple (hashable)
    - Separate cache from data fetching to allow independent invalidation
    
    Args:
        universe_set: Name of the universe set
        custom_symbols_tuple: Tuple of custom symbols (tuple is hashable for caching)
        
    Returns:
        List of symbols in the universe
    """
    custom_symbols = list(custom_symbols_tuple) if custom_symbols_tuple else None
    return get_universe_symbols(universe_set, custom_symbols)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_and_filter_data(source_name: str, symbols: List[str], min_price: float, max_price: float,
                         alpaca_api_key: str = None, alpaca_api_secret: str = None, 
                         alpaca_movers_type: str = "most_actives", alpaca_top_n: int = 50,
                         tradingview_fields: tuple = (), tradingview_limit: int = 500) -> tuple:
    """
    Fetch data and apply price filter with caching
    
    Caching Strategy:
    - Cache key includes: source_name, symbols, min_price, max_price, source-specific params
    - TTL: 5 minutes (reduces API calls when only slider moves)
    - When min_price/max_price change, cache is used if same values
    - TradingView and Alpaca have additional internal caching
    
    Args:
        source_name: Name of the data source
        symbols: List of symbols to fetch
        min_price: Minimum price filter
        max_price: Maximum price filter
        alpaca_api_key: Alpaca API key (optional)
        alpaca_api_secret: Alpaca API secret (optional)
        alpaca_movers_type: Type of movers list for Alpaca
        alpaca_top_n: Number of top movers to fetch
        tradingview_fields: Tuple of additional fields for TradingView (tuple for hashable caching)
        tradingview_limit: Result limit for TradingView
        
    Returns:
        Tuple of (filtered_df, fetched_count, missing_price_count, after_price_filter_count, 
                  truncated, is_fallback, error_info)
    """
    error_info = None  # Dictionary with provider, error, next_steps
    
    # Select data source
    if source_name == "Yahoo (EOD)":
        source = YahooDataSource()
    elif source_name == "TradingView (Advanced)":
        source = TradingViewDataSource(
            selected_fields=list(tradingview_fields),
            limit=tradingview_limit
        )
    else:  # Alpaca Movers (Intraday)
        source = AlpacaDataSource(
            api_key=alpaca_api_key,
            api_secret=alpaca_api_secret,
            movers_type=alpaca_movers_type,
            top_n=alpaca_top_n
        )
    
    # Fetch data with error handling
    try:
        df = source.fetch_data(symbols)
    except Exception as e:
        # Provider failed - set error info for consolidated error panel
        error_info = {
            'provider': source_name,
            'error': str(e),
            'next_steps': f"The {source_name} data source encountered an error. "
                         f"Please check your configuration or try a different data source."
        }
        # Return empty result with error info
        df = pd.DataFrame(columns=['symbol', 'price', 'volume', 'change', 'change_pct'])
        df.attrs['missing_price_count'] = len(symbols)
        df.attrs['truncated'] = False
        df.attrs['is_fallback'] = False
        
        return df, 0, len(symbols), 0, False, False, error_info
    
    # Track counts and metadata for diagnostics
    fetched_count = len(df)
    missing_price_count = df.attrs.get('missing_price_count', 0)
    truncated = df.attrs.get('truncated', False)
    is_fallback = df.attrs.get('is_fallback', False)
    
    # Apply price filter immediately after fetch/normalize
    # Symbols without valid price have already been dropped in fetch_data
    # Validation: Only apply filter if price range is valid
    if not df.empty and min_price < max_price:
        df = df[(df['price'] >= min_price) & (df['price'] <= max_price)]
    
    after_price_filter_count = len(df)
    
    return df, fetched_count, missing_price_count, after_price_filter_count, truncated, is_fallback, error_info


def main():
    """Main application"""
    # Initialize session state for scalability
    init_session_state()
    
    st.title("📈 SwingTrade Stock Screener")
    st.markdown("---")
    
    # Sidebar for filters
    with st.sidebar:
        st.header("Filters")
        
        # Universe Source
        st.subheader("Universe Source")
        source = st.radio(
            "Select data source:",
            ["Yahoo (EOD)", "TradingView (Advanced)", "Alpaca Movers (Intraday)"],
            index=0,
            help="Choose the data source for stock prices"
        )
        
        # TradingView-specific configuration (show when TradingView is selected)
        tradingview_fields = []
        tradingview_limit = 500
        
        if source == "TradingView (Advanced)":
            st.info("ℹ️ **Large field set** (technicals + fundamentals). "
                   "Real-time data may require session cookies. "
                   "See [README](https://github.com/CWitteVera/SwingTrade_Screeener#tradingview-advanced-optional) for details.")
            
            st.markdown("---")
            st.subheader("TradingView Configuration")
            
            # Field selector with safe defaults
            with st.expander("Advanced Fields (Optional)", expanded=False):
                st.markdown("Select additional technical/fundamental fields beyond defaults (close, volume, change, market_cap_basic):")
                
                # Group fields by category for better UX
                st.markdown("**Technical Indicators:**")
                col1, col2 = st.columns(2)
                with col1:
                    if st.checkbox("Relative Volume (10d)", key="tv_relvol"):
                        tradingview_fields.append("relative_volume_10d_calc")
                    if st.checkbox("RSI", key="tv_rsi"):
                        tradingview_fields.append("RSI")
                    if st.checkbox("MACD", key="tv_macd"):
                        tradingview_fields.extend(["MACD.macd", "MACD.signal"])
                with col2:
                    if st.checkbox("Stochastic", key="tv_stoch"):
                        tradingview_fields.extend(["Stoch.K", "Stoch.D"])
                    if st.checkbox("Bollinger Bands", key="tv_bb"):
                        tradingview_fields.extend(["BB.upper", "BB.lower"])
                    if st.checkbox("VWAP", key="tv_vwap"):
                        tradingview_fields.append("VWAP")
                
                st.markdown("**Moving Averages:**")
                ema_options = st.multiselect(
                    "EMA Periods",
                    options=["5", "10", "20", "50"],
                    help="Select exponential moving average periods"
                )
                for period in ema_options:
                    tradingview_fields.append(f"EMA{period}")
            
            # Result limit
            tradingview_limit = st.slider(
                "Result Limit",
                min_value=50,
                max_value=500,
                value=500,
                step=50,
                help="Cap results to keep UI responsive (max: 500)"
            )
        
        # Alpaca-specific configuration (show when Alpaca is selected)
        alpaca_api_key = None
        alpaca_api_secret = None
        alpaca_movers_type = "most_actives"
        alpaca_top_n = 50
        
        if source == "Alpaca Movers (Intraday)":
            st.markdown("---")
            st.subheader("Alpaca Configuration")
            
            # API credentials (with env var fallback)
            with st.expander("API Credentials", expanded=False):
                alpaca_api_key = st.text_input(
                    "API Key",
                    type="password",
                    placeholder="Enter Alpaca API Key or set ALPACA_API_KEY env var",
                    help="Leave empty to use ALPACA_API_KEY environment variable"
                )
                alpaca_api_secret = st.text_input(
                    "API Secret",
                    type="password",
                    placeholder="Enter Alpaca API Secret or set ALPACA_API_SECRET env var",
                    help="Leave empty to use ALPACA_API_SECRET environment variable"
                )
                
                # Show warning if no credentials provided
                if not alpaca_api_key and not os.getenv('ALPACA_API_KEY'):
                    st.warning("⚠️ No API credentials found. Will fall back to Yahoo Finance.")
            
            # Movers list type
            movers_options = {
                "Most Actives": "most_actives",
                "Market Movers - Gainers": "gainers", 
                "Market Movers - Losers": "losers",
                "Top Volume": "top_volume"
            }
            movers_label = st.selectbox(
                "Movers List",
                options=list(movers_options.keys()),
                index=0,
                help="Select the type of movers list to fetch"
            )
            alpaca_movers_type = movers_options[movers_label]
            
            # Top N symbols
            alpaca_top_n = st.slider(
                "Number of Top Movers",
                min_value=10,
                max_value=100,
                value=50,
                step=10,
                help="Limit results to keep UI responsive (capped at 100)"
            )
        
        st.markdown("---")
        
        # Universe Set
        st.subheader("Universe Set")
        universe_set = st.selectbox(
            "Select universe:",
            ["All NMS", "S&P 500", "NASDAQ-100", "Leveraged ETFs", "Custom CSV"],
            index=1,  # Default to S&P 500
            help="Choose the set of stocks to screen"
        )
        
        # Custom symbols input
        custom_symbols = []
        if universe_set == "Custom CSV":
            custom_text = st.text_area(
                "Enter symbols (comma-separated):",
                placeholder="AAPL, MSFT, GOOGL, AMZN",
                help="Enter stock symbols separated by commas"
            )
            custom_symbols = parse_custom_symbols(custom_text)
        
        st.markdown("---")
        
        # Price Range Filter
        st.subheader("Price Range")
        col1, col2 = st.columns(2)
        with col1:
            min_price = st.number_input(
                "Min Price ($)",
                min_value=0.0,
                max_value=10000.0,
                value=0.0,
                step=1.0
            )
        with col2:
            max_price = st.number_input(
                "Max Price ($)",
                min_value=0.0,
                max_value=10000.0,
                value=1000.0,
                step=1.0
            )
        
        # Validation: Check if price_min >= price_max
        price_range_valid = min_price < max_price
        if not price_range_valid:
            st.warning("⚠️ **Invalid Price Range**: Min price must be less than max price. "
                      "No price filtering will be applied. Please adjust the range.")
        
        # Price range slider for visual feedback
        slider_max = min(max_price, 1000.0)
        st.slider(
            "Price Range Visual",
            min_value=0.0,
            max_value=max(slider_max, 100.0),
            value=(min_price, min(max_price, slider_max)),
            disabled=True,
            help="Visual representation of selected price range"
        )
    
    # Main content area
    st.header("Results")
    
    # Get symbols for selected universe (with caching)
    # Convert custom_symbols list to tuple for hashable caching
    custom_symbols_tuple = tuple(custom_symbols) if custom_symbols else None
    symbols = get_cached_universe_symbols(universe_set, custom_symbols_tuple)
    
    # Validation: Check for empty universe
    if not symbols:
        st.error("❌ **Empty Universe**: No symbols found in the selected universe set. "
                "Please select a different universe or enter custom symbols.")
    
    # Validation: Check for missing Alpaca API keys
    alpaca_missing_keys = False
    if source == "Alpaca Movers (Intraday)":
        if not alpaca_api_key and not os.getenv('ALPACA_API_KEY'):
            alpaca_missing_keys = True
            st.warning("⚠️ **Missing Alpaca API Keys**: No API credentials found. "
                      "The app will fall back to Yahoo Finance data. "
                      "To use Alpaca intraday data:\n"
                      "1. Sign up at [Alpaca Markets](https://alpaca.markets/)\n"
                      "2. Generate API keys from your dashboard\n"
                      "3. Enter them in the sidebar or set `ALPACA_API_KEY` and `ALPACA_API_SECRET` environment variables")
    
    # Display universe info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Universe", universe_set)
    with col2:
        st.metric("Source", source)
    with col3:
        st.metric("Total Symbols", len(symbols))
    
    # Fetch and filter button
    if st.button("🔍 Run Screener", type="primary", use_container_width=True):
        if not symbols:
            st.warning("⚠️ No symbols to screen. Please select a universe or enter custom symbols.")
        else:
            with st.spinner(f"Fetching data for {len(symbols)} symbols..."):
                # Fetch and filter data with diagnostic counts
                # Convert tradingview_fields to tuple for hashable caching
                tradingview_fields_tuple = tuple(tradingview_fields) if tradingview_fields else ()
                
                results_df, fetched_count, missing_price_count, after_price_filter_count, truncated, is_fallback, error_info = fetch_and_filter_data(
                    source, symbols, min_price, max_price,
                    alpaca_api_key=alpaca_api_key,
                    alpaca_api_secret=alpaca_api_secret,
                    alpaca_movers_type=alpaca_movers_type,
                    alpaca_top_n=alpaca_top_n,
                    tradingview_fields=tradingview_fields_tuple,
                    tradingview_limit=tradingview_limit
                )
                
                # Store in session state
                st.session_state['results'] = results_df
                st.session_state['fetched_count'] = fetched_count
                st.session_state['missing_price_count'] = missing_price_count
                st.session_state['after_price_filter_count'] = after_price_filter_count
                st.session_state['filtered_count'] = len(results_df)
                st.session_state['data_source'] = source
                st.session_state['truncated'] = truncated
                st.session_state['is_fallback'] = is_fallback
                st.session_state['error_info'] = error_info
                st.session_state['price_range_valid'] = price_range_valid
                
                # Update scalability structures for future real-time scanning
                update_symbol_directory(symbols, universe_set)
                if not results_df.empty:
                    update_prior_close_cache(results_df)
                    add_scan_to_history(results_df)
    
    # Display results
    if 'results' in st.session_state:
        results_df = st.session_state['results']
        filtered_count = st.session_state['filtered_count']
        fetched_count = st.session_state.get('fetched_count', 0)
        missing_price_count = st.session_state.get('missing_price_count', 0)
        after_price_filter_count = st.session_state.get('after_price_filter_count', 0)
        data_source = st.session_state.get('data_source', source)
        truncated = st.session_state.get('truncated', False)
        is_fallback = st.session_state.get('is_fallback', False)
        error_info = st.session_state.get('error_info', None)
        price_range_valid = st.session_state.get('price_range_valid', True)
        
        st.markdown("---")
        
        # Show error panel if there was an error
        if error_info:
            with st.expander("❌ **Data Source Error**", expanded=True):
                st.error(f"**Provider:** {error_info['provider']}\n\n"
                        f"**Error:** {error_info['error']}\n\n"
                        f"**Next Steps:** {error_info['next_steps']}")
        
        # Show warning if price range is invalid
        if not price_range_valid:
            st.warning("⚠️ **Price filter not applied**: Invalid price range (min >= max). "
                      "Showing all results with valid prices.")
        
        # Diagnostic counts: Total Requested → Fetched → Missing Price → After Price Filter
        st.subheader("📊 Filtering Pipeline")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Requested", len(symbols), help="Total symbols in selected universe")
        with col2:
            st.metric("Fetched", fetched_count, help="Symbols successfully fetched from provider")
        with col3:
            missing_delta = f"-{missing_price_count}" if missing_price_count > 0 else None
            st.metric("Missing Price", missing_price_count, delta=missing_delta, delta_color="inverse", 
                     help="Symbols dropped due to missing/invalid price data")
        with col4:
            if price_range_valid:
                st.metric("After Price Filter", after_price_filter_count, 
                         help=f"Symbols within price range ${min_price:.2f} - ${max_price:.2f}")
            else:
                st.metric("After Price Filter", fetched_count - missing_price_count,
                         help="Price filter not applied (invalid range)")
        
        # Compact Source Badge near the table
        if data_source == "Yahoo (EOD)":
            badge_color = "blue"
            badge_text = "📊 Yahoo Finance (EOD)"
            badge_help = "End-of-day data from Yahoo Finance (delayed)"
        elif data_source == "Alpaca Movers (Intraday)":
            if is_fallback:
                badge_color = "orange"
                badge_text = "⚠️ Alpaca (Fallback to Yahoo)"
                badge_help = "Alpaca unavailable, using Yahoo Finance as fallback"
            else:
                badge_color = "green"
                badge_text = "✅ Alpaca (Intraday)"
                badge_help = "Real-time intraday data from Alpaca"
        elif data_source == "TradingView (Advanced)":
            if is_fallback:
                badge_color = "orange"
                badge_text = "⚠️ TradingView (Fallback to Yahoo)"
                badge_help = "TradingView unavailable, using Yahoo Finance as fallback. Session cookies may be required for real-time data."
            else:
                badge_color = "green"
                badge_text = "✅ TradingView (Advanced)"
                badge_help = "Advanced data with technical indicators from TradingView"
        else:
            badge_color = "gray"
            badge_text = f"📊 {data_source}"
            badge_help = "Data source"
        
        # Display badge with color coding
        if badge_color == "blue":
            st.info(f"**Source:** {badge_text} - {badge_help}")
        elif badge_color == "green":
            st.success(f"**Source:** {badge_text} - {badge_help}")
        elif badge_color == "orange":
            st.warning(f"**Source:** {badge_text} - {badge_help}")
        else:
            st.info(f"**Source:** {badge_text} - {badge_help}")
        
        # Show truncated badge if applicable
        if truncated:
            st.warning("⚠️ **Results truncated:** Showing top results (limit reached). "
                      "Adjust the Result Limit slider or refine filters to see more.")
        
        st.markdown("---")
        
        # Results summary
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Matched Symbols", filtered_count, 
                     help="Symbols passing all filters (currently only price range)")
        with col2:
            filter_pct = (filtered_count / len(symbols) * 100) if len(symbols) > 0 else 0
            st.metric("Filter Rate", f"{filter_pct:.1f}%", 
                     help="Percentage of requested symbols that passed filters")
        
        # Display results table
        if not results_df.empty:
            st.subheader("Filtered Stocks")
            
            # Format the dataframe for display
            display_df = results_df.copy()
            
            # Define base columns that all sources should have
            base_columns = ['symbol', 'price', 'volume', 'change', 'change_pct']
            # Define columns with special formatting (not just rounded)
            special_format_columns = base_columns + ['market_cap_basic', 'name', 'close']
            
            # Format base columns
            if 'price' in display_df.columns:
                display_df['price'] = display_df['price'].apply(lambda x: f"${x:,.2f}")
            if 'volume' in display_df.columns:
                display_df['volume'] = display_df['volume'].apply(lambda x: f"{x:,}")
            if 'change' in display_df.columns:
                display_df['change'] = display_df['change'].apply(lambda x: f"${x:,.2f}")
            if 'change_pct' in display_df.columns:
                display_df['change_pct'] = display_df['change_pct'].apply(lambda x: f"{x:+.2f}%")
            
            # Format advanced columns if present (from TradingView)
            if 'market_cap_basic' in display_df.columns:
                display_df['market_cap_basic'] = display_df['market_cap_basic'].apply(
                    lambda x: f"${x/1e9:,.2f}B" if pd.notna(x) else "N/A"
                )
            
            # Keep other numeric columns as-is but round them
            for col in display_df.columns:
                if col not in special_format_columns and display_df[col].dtype in ['float64', 'int64']:
                    display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
            
            # Create column name mapping for display
            column_mapping = {
                'symbol': 'Symbol',
                'name': 'Name',
                'price': 'Price',
                'volume': 'Volume',
                'change': 'Change ($)',
                'change_pct': 'Change (%)',
                'market_cap_basic': 'Market Cap',
                'relative_volume_10d_calc': 'Rel Vol (10d)',
                'RSI': 'RSI',
                'MACD.macd': 'MACD',
                'MACD.signal': 'MACD Signal',
                'Stoch.K': 'Stoch K',
                'Stoch.D': 'Stoch D',
                'BB.upper': 'BB Upper',
                'BB.lower': 'BB Lower',
                'VWAP': 'VWAP',
                'EMA5': 'EMA 5',
                'EMA10': 'EMA 10',
                'EMA20': 'EMA 20',
                'EMA50': 'EMA 50',
            }
            
            # Rename columns that exist in the dataframe
            rename_dict = {col: column_mapping.get(col, col) for col in display_df.columns}
            display_df = display_df.rename(columns=rename_dict)
            
            # Reorder columns: base columns first, then advanced columns
            ordered_cols = []
            for col in ['Symbol', 'Name', 'Price', 'Volume', 'Change ($)', 'Change (%)', 'Market Cap']:
                if col in display_df.columns:
                    ordered_cols.append(col)
            
            # Add remaining columns (advanced fields) to the right
            for col in display_df.columns:
                if col not in ordered_cols:
                    ordered_cols.append(col)
            
            display_df = display_df[ordered_cols]
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Download button
            csv = results_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Results (CSV)",
                data=csv,
                file_name="screener_results.csv",
                mime="text/csv"
            )
        else:
            st.info("No stocks match the current filter criteria.")
    else:
        st.info("👆 Click 'Run Screener' to fetch and filter stocks.")


if __name__ == "__main__":
    main()
