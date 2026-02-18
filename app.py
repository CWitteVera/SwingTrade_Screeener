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
import time
import traceback
from dotenv import load_dotenv
import yfinance as yf

# Load environment variables from .env file if it exists
# This should be called before importing any modules that use env vars
load_dotenv(override=False)  # Don't override existing environment variables

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from universe_sets import get_universe_symbols
from data_sources import YahooDataSource, AlpacaDataSource, FinancialDataNetSource
from data_sources.financialdata_client import HAS_SDK
from scoring_system import StockScorer
from price_predictor import PricePredictor
from visualizations import StockVisualizer
from combined_top5 import add_to_top5_aggregator, render_combined_top5_plot
from trade_signals import suggest_entry_exit


# Page configuration
st.set_page_config(
    page_title="SwingTrade Stock Screener",
    page_icon="📈",
    layout="wide"
)


# ============================================================================
# CONSTANTS
# ============================================================================
DEFAULT_FORECAST_DAYS = 14  # Default forecast period for scoring (auto-run uses this; manual mode allows slider adjustment)
DEFAULT_LOOKBACK_DAYS = 60  # Lookback period for scoring analysis (used in both auto-run and manual modes)


# ============================================================================
# DEBUG LOG FUNCTIONS FOR DEVELOPER MODE
# ============================================================================

def init_debug_log():
    """
    Initialize debug log structure for Developer Mode
    """
    if 'debug_log' not in st.session_state:
        st.session_state['debug_log'] = {
            'enabled': False,
            'entries': [],
            'cache_stats': {
                'universe_misses': 0,
                'fetch_misses': 0
            },
            'api_calls': {
                'yahoo': 0,
                'financialdata': 0,
                'alpaca': 0
            },
            'timings': {},
            'errors': []
        }

def redact_sensitive_data(data: Dict) -> Dict:
    """
    Redact sensitive information from debug log data
    
    Args:
        data: Dictionary that may contain sensitive information
        
    Returns:
        Dictionary with sensitive values redacted
    """
    if not data:
        return data
    
    sensitive_keys = ['api_key', 'api_secret', 'key', 'secret', 'password', 'token', 
                     'FINANCIALDATA_API_KEY', 'ALPACA_API_KEY', 'ALPACA_API_SECRET']
    
    redacted = data.copy()
    for key, value in redacted.items():
        # Check if key name contains sensitive keywords
        if any(sensitive in key.lower() for sensitive in ['key', 'secret', 'password', 'token']):
            if isinstance(value, str) and len(value) > 0:
                # Show first 4 chars, redact the rest
                redacted[key] = value[:4] + '*' * (len(value) - 4) if len(value) > 4 else '****'
        # Check if value is a dict and recursively redact
        elif isinstance(value, dict):
            redacted[key] = redact_sensitive_data(value)
    
    return redacted

def log_debug(category: str, message: str, data: Dict = None):
    """
    Add entry to debug log with automatic redaction of sensitive data
    
    Args:
        category: Category of log entry (info, cache, timing, api, error)
        message: Log message
        data: Optional dictionary of additional data
    """
    if st.session_state.get('debug_log', {}).get('enabled', False):
        # Redact sensitive data before logging
        safe_data = redact_sensitive_data(data) if data else {}
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'category': category,
            'message': message,
            'data': safe_data
        }
        st.session_state['debug_log']['entries'].append(entry)

def log_cache_hit(cache_type: str):
    """
    Log a cache hit
    
    Note: Not actively used because Streamlit's @st.cache_data decorator
    means cached functions don't execute on cache hits, so we can't log them.
    This function is kept as a no-op to maintain a consistent API interface
    with log_cache_miss() in case future enhancements allow cache hit tracking
    (e.g., if Streamlit adds cache hit callbacks or if we implement custom caching).
    """
    pass  # Can't track hits with current Streamlit caching mechanism

def log_cache_miss(cache_type: str):
    """Log a cache miss"""
    if st.session_state.get('debug_log', {}).get('enabled', False):
        st.session_state['debug_log']['cache_stats'][f'{cache_type}_misses'] += 1
        log_debug('cache', f'Cache MISS: {cache_type}')

def log_api_call(provider: str):
    """Log an API call"""
    if st.session_state.get('debug_log', {}).get('enabled', False):
        st.session_state['debug_log']['api_calls'][provider] += 1
        log_debug('api', f'API call to {provider}')

def log_timing(step: str, duration: float):
    """Log timing for a step"""
    if st.session_state.get('debug_log', {}).get('enabled', False):
        st.session_state['debug_log']['timings'][step] = duration
        log_debug('timing', f'{step}: {duration:.3f}s')

def log_error(error: Exception, context: str):
    """Log an error with full traceback"""
    if st.session_state.get('debug_log', {}).get('enabled', False):
        error_info = {
            'context': context,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc()
        }
        st.session_state['debug_log']['errors'].append(error_info)
        log_debug('error', f'Error in {context}: {str(error)}', error_info)

def clear_debug_log():
    """Clear all debug log entries"""
    if 'debug_log' in st.session_state:
        st.session_state['debug_log']['entries'] = []
        st.session_state['debug_log']['cache_stats'] = {
            'universe_misses': 0,
            'fetch_misses': 0
        }
        st.session_state['debug_log']['api_calls'] = {
            'yahoo': 0,
            'tradingview': 0,
            'alpaca': 0
        }
        st.session_state['debug_log']['timings'] = {}
        st.session_state['debug_log']['errors'] = []

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
    # Initialize debug log
    init_debug_log()
    
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


def format_volume(volume: float) -> str:
    """
    Format volume in abbreviated notation (K, M, B)
    
    Args:
        volume: Volume value to format
        
    Returns:
        Formatted string with appropriate suffix
    """
    if volume >= 1_000_000_000:
        return f"{volume / 1_000_000_000:.1f}B"
    elif volume >= 1_000_000:
        return f"{volume / 1_000_000:.1f}M"
    elif volume >= 1_000:
        return f"{volume / 1_000:.1f}K"
    else:
        return f"{volume:.0f}"


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
    
    Note: Cache logging happens outside this function since cached functions
    don't execute on cache hits.
    
    Args:
        universe_set: Name of the universe set
        custom_symbols_tuple: Tuple of custom symbols (tuple is hashable for caching)
        
    Returns:
        List of symbols in the universe
    """
    # If this executes, it's a cache miss
    log_cache_miss('universe')
    
    custom_symbols = list(custom_symbols_tuple) if custom_symbols_tuple else None
    result = get_universe_symbols(universe_set, custom_symbols)
    log_debug('info', f'Fetched universe symbols (cache miss): {universe_set}', {
        'universe': universe_set,
        'symbol_count': len(result),
        'symbols': result
    })
    return result


@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_and_filter_data(source_name: str, symbols: List[str], min_price: float, max_price: float,
                         alpaca_api_key: str = None, alpaca_api_secret: str = None, 
                         alpaca_movers_type: str = "most_actives", alpaca_top_n: int = 50,
                         financialdata_fields: tuple = (), financialdata_interval: str = '1d') -> tuple:
    """
    Fetch data and apply price filter with caching
    
    Caching Strategy:
    - Cache key includes: source_name, symbols, min_price, max_price, source-specific params
    - TTL: 5 minutes (reduces API calls when only slider moves)
    - When min_price/max_price change, cache is used if same values
    - FinancialData.Net and Alpaca have additional internal caching
    
    Note: Cache logging happens inside this function. When cached, function doesn't execute,
    so cache misses are logged when function runs, but cache hits aren't tracked.
    
    Args:
        source_name: Name of the data source
        symbols: List of symbols to fetch
        min_price: Minimum price filter
        max_price: Maximum price filter
        alpaca_api_key: Alpaca API key (optional)
        alpaca_api_secret: Alpaca API secret (optional)
        alpaca_movers_type: Type of movers list for Alpaca
        alpaca_top_n: Number of top movers to fetch
        financialdata_fields: Tuple of additional fields for FinancialData.Net (tuple for hashable caching)
        financialdata_interval: Timeframe for FinancialData.Net data
        
    Returns:
        Tuple of (filtered_df, fetched_count, missing_price_count, after_price_filter_count, 
                  truncated, is_fallback, error_info)
    """
    # If this executes, it's a cache miss
    log_cache_miss('fetch')
    
    # Start timing
    start_time = time.time()
    
    error_info = None  # Dictionary with provider, error, next_steps
    
    log_debug('info', f'Fetching data from {source_name} (cache miss)', {
        'source': source_name,
        'symbol_count': len(symbols),
        'symbols': symbols,
        'price_range': {'min': min_price, 'max': max_price}
    })
    
    # Select data source
    source_selection_start = time.time()
    if source_name == "Yahoo (EOD)":
        source = YahooDataSource()
    elif source_name == "Advanced Data (financialdata.net)":
        source = FinancialDataNetSource(
            selected_fields=list(financialdata_fields),
            interval=financialdata_interval
        )
    else:  # Alpaca Movers (Intraday)
        source = AlpacaDataSource(
            api_key=alpaca_api_key,
            api_secret=alpaca_api_secret,
            movers_type=alpaca_movers_type,
            top_n=alpaca_top_n
        )
    log_timing('source_selection', time.time() - source_selection_start)
    
    # Fetch data with error handling
    fetch_start = time.time()
    try:
        # Log API call
        provider_key = source_name.split()[0].lower()
        if provider_key == 'advanced':
            provider_key = 'financialdata'
        elif provider_key not in ['yahoo', 'alpaca']:
            provider_key = 'yahoo'
        log_api_call(provider_key)
        
        df = source.fetch_data(symbols)
        log_timing('data_fetch', time.time() - fetch_start)
    except Exception as e:
        log_error(e, f'fetch_data from {source_name}')
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
        
        log_timing('total_fetch_and_filter', time.time() - start_time)
        return df, 0, len(symbols), 0, False, False, error_info
    
    # Track counts and metadata for diagnostics
    fetched_count = len(df)
    missing_price_count = df.attrs.get('missing_price_count', 0)
    truncated = df.attrs.get('truncated', False)
    is_fallback = df.attrs.get('is_fallback', False)
    
    log_debug('info', f'Fetched {fetched_count} symbols, {missing_price_count} missing prices', {
        'fetched': fetched_count,
        'missing_prices': missing_price_count,
        'truncated': truncated,
        'is_fallback': is_fallback
    })
    
    # Apply price filter immediately after fetch/normalize
    # Symbols without valid price have already been dropped in fetch_data
    # Validation: Only apply filter if price range is valid
    filter_start = time.time()
    if not df.empty and min_price < max_price:
        df = df[(df['price'] >= min_price) & (df['price'] <= max_price)]
    log_timing('price_filter', time.time() - filter_start)
    
    after_price_filter_count = len(df)
    
    log_debug('info', f'After price filter: {after_price_filter_count} symbols', {
        'after_filter': after_price_filter_count,
        'filtered_out': fetched_count - missing_price_count - after_price_filter_count
    })
    
    log_timing('total_fetch_and_filter', time.time() - start_time)
    
    return df, fetched_count, missing_price_count, after_price_filter_count, truncated, is_fallback, error_info


def run_automated_scenarios():
    """
    Run automated screening scenarios across multiple configurations
    
    This function executes a series of predefined screening scenarios
    automatically without requiring user interaction. It cycles through:
    - Multiple data sources
    - Multiple universe sets
    - Multiple price ranges
    
    Displays all results in a consolidated view via Streamlit UI.
    """
    st.subheader("🤖 Auto-Run Mode - Running Automated Scenarios")
    st.info("Running through various scenarios automatically. This may take a few moments...")
    
    # Define scenarios to test
    scenarios = [
        {
            'name': 'S&P 500 - Swing Trades (Yahoo)',
            'source': 'Yahoo (EOD)',
            'universe': 'S&P 500',
            'min_price': 10.0,
            'max_price': 200.0,
            'custom_symbols': None
        },
        {
            'name': 'NASDAQ-100 - Swing Trades (Yahoo)',
            'source': 'Yahoo (EOD)',
            'universe': 'NASDAQ-100',
            'min_price': 10.0,
            'max_price': 200.0,
            'custom_symbols': None
        },
        {
            'name': 'Leveraged ETFs - All Prices (Yahoo)',
            'source': 'Yahoo (EOD)',
            'universe': 'Leveraged ETFs',
            'min_price': 0.0,
            'max_price': 10000.0,
            'custom_symbols': None
        },
        {
            'name': 'NASDAQ-100 - High Value (Yahoo)',
            'source': 'Yahoo (EOD)',
            'universe': 'NASDAQ-100',
            'min_price': 200.0,
            'max_price': 10000.0,
            'custom_symbols': None
        },
        {
            'name': 'All NMS - Swing Trades (Yahoo)',
            'source': 'Yahoo (EOD)',
            'universe': 'All NMS',
            'min_price': 10.0,
            'max_price': 200.0,
            'custom_symbols': None
        }
    ]
    
    # Check if Advanced Data is available
    fdn_source = FinancialDataNetSource()
    if fdn_source.is_available():
        scenarios.extend([
            {
                'name': 'S&P 500 - Swing Trades (Advanced)',
                'source': 'Advanced Data (financialdata.net)',
                'universe': 'S&P 500',
                'min_price': 10.0,
                'max_price': 200.0,
                'custom_symbols': None
            },
            {
                'name': 'NASDAQ-100 - Swing Trades (Advanced)',
                'source': 'Advanced Data (financialdata.net)',
                'universe': 'NASDAQ-100',
                'min_price': 10.0,
                'max_price': 200.0,
                'custom_symbols': None
            }
        ])
    
    # Check if Alpaca is available
    alpaca_key = os.getenv('ALPACA_API_KEY')
    alpaca_secret = os.getenv('ALPACA_API_SECRET')
    if alpaca_key and alpaca_secret:
        scenarios.extend([
            {
                'name': 'Alpaca Most Actives - All Prices',
                'source': 'Alpaca Movers (Intraday)',
                'universe': 'All NMS',  # Placeholder - Alpaca provides its own symbol list via movers API
                'min_price': 0.0,
                'max_price': 10000.0,
                'custom_symbols': None,
                'alpaca_movers_type': 'most_actives',
                'alpaca_top_n': 50
            },
            {
                'name': 'Alpaca Gainers - Swing Trades',
                'source': 'Alpaca Movers (Intraday)',
                'universe': 'All NMS',  # Placeholder - Alpaca provides its own symbol list via movers API
                'min_price': 10.0,
                'max_price': 200.0,
                'custom_symbols': None,
                'alpaca_movers_type': 'gainers',
                'alpaca_top_n': 50
            }
        ])
    
    # Progress tracking
    total_scenarios = len(scenarios)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Store all results
    all_results = []
    
    # Run each scenario
    for idx, scenario in enumerate(scenarios):
        status_text.text(f"Running scenario {idx + 1}/{total_scenarios}: {scenario['name']}...")
        progress_bar.progress((idx + 1) / total_scenarios)
        
        try:
            # Get symbols
            custom_symbols_for_cache = tuple(scenario['custom_symbols']) if scenario.get('custom_symbols') else None
            symbols = get_cached_universe_symbols(scenario['universe'], custom_symbols_for_cache)
            
            if not symbols:
                all_results.append({
                    'scenario': scenario['name'],
                    'status': 'failed',
                    'error': 'No symbols in universe',
                    'results': pd.DataFrame()
                })
                continue
            
            # Fetch and filter data
            alpaca_api_key = alpaca_key if scenario['source'] == 'Alpaca Movers (Intraday)' else None
            alpaca_api_secret = alpaca_secret if scenario['source'] == 'Alpaca Movers (Intraday)' else None
            alpaca_movers_type = scenario.get('alpaca_movers_type', 'most_actives')
            alpaca_top_n = scenario.get('alpaca_top_n', 50)
            
            results_df, fetched_count, missing_price_count, after_price_filter_count, truncated, is_fallback, error_info = fetch_and_filter_data(
                scenario['source'], 
                symbols, 
                scenario['min_price'], 
                scenario['max_price'],
                alpaca_api_key=alpaca_api_key,
                alpaca_api_secret=alpaca_api_secret,
                alpaca_movers_type=alpaca_movers_type,
                alpaca_top_n=alpaca_top_n
            )
            
            all_results.append({
                'scenario': scenario['name'],
                'status': 'success' if not results_df.empty else 'no_results',
                'source': scenario['source'],
                'universe': scenario['universe'],
                'price_range': f"${scenario['min_price']:.0f} - ${scenario['max_price']:.0f}",
                'fetched_count': fetched_count,
                'results_count': len(results_df),
                'is_fallback': is_fallback,
                'results': results_df,
                'error': error_info
            })
            
        except Exception as e:
            all_results.append({
                'scenario': scenario['name'],
                'status': 'failed',
                'error': str(e),
                'results': pd.DataFrame()
            })
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    # Store all results in session state for tab rendering
    st.session_state['auto_run_all_results'] = all_results
    
    # Display summary
    st.success(f"✅ Completed {total_scenarios} automated scenarios!")
    st.markdown("---")
    
    # Summary table
    st.subheader("📊 Scenario Summary")
    summary_data = []
    for result in all_results:
        summary_data.append({
            'Scenario': result['scenario'],
            'Status': '✅ Success' if result['status'] == 'success' else ('⚠️ No Results' if result['status'] == 'no_results' else '❌ Failed'),
            'Source': result.get('source', 'N/A'),
            'Universe': result.get('universe', 'N/A'),
            'Price Range': result.get('price_range', 'N/A'),
            'Results Found': result.get('results_count', 0)
        })
    
    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    # Render combined Top 5 visualization FIRST (before detailed results)
    st.markdown("---")
    render_combined_top5_plot(default_lookback=60)
    
    # Show detailed results for each successful scenario
    st.markdown("---")
    st.subheader("📈 Detailed Results")
    
    successful_results = [r for r in all_results if r['status'] == 'success' and not r['results'].empty]
    
    if not successful_results:
        st.warning("⚠️ No scenarios returned results. This could be due to:")
        st.markdown("""
        - Restrictive price filters (try wider ranges)
        - API connectivity issues
        - Empty universe sets
        - All stocks filtered out by price criteria
        
        **Recommendations:**
        1. Check your API keys are configured correctly
        2. Try running individual scenarios with broader price ranges
        3. Enable Developer Mode to see detailed error logs
        """)
    else:
        for result in successful_results:
            with st.expander(f"🔍 {result['scenario']} - {result['results_count']} stocks found", expanded=True):
                st.write(f"**Source:** {result['source']}")
                st.write(f"**Universe:** {result['universe']}")
                st.write(f"**Price Range:** {result['price_range']}")
                
                if result.get('is_fallback'):
                    st.warning("⚠️ Using fallback data source (Yahoo Finance)")
                
                # Display results
                display_df = result['results'].copy()
                
                # Format the dataframe
                if 'price' in display_df.columns:
                    display_df['price'] = display_df['price'].apply(lambda x: f"${x:,.2f}")
                if 'volume' in display_df.columns:
                    display_df['volume'] = display_df['volume'].apply(lambda x: f"{x:,}")
                if 'change' in display_df.columns:
                    display_df['change'] = display_df['change'].apply(lambda x: f"${x:,.2f}")
                if 'change_pct' in display_df.columns:
                    display_df['change_pct'] = display_df['change_pct'].apply(lambda x: f"{x:+.2f}%")
                
                # Rename columns
                column_mapping = {
                    'symbol': 'Symbol',
                    'price': 'Price',
                    'volume': 'Volume',
                    'change': 'Change ($)',
                    'change_pct': 'Change (%)',
                }
                display_df = display_df.rename(columns={col: column_mapping.get(col, col) for col in display_df.columns})
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # TOP 3 SCORING SYSTEM FOR AUTO-RUN
                # ====================================================================
                st.markdown("---")
                st.markdown("#### 🏆 Top 5 Stocks by Upward Potential")
                
                with st.spinner("🔍 Analyzing stocks and calculating scores..."):
                    try:
                        # Initialize scorer and predictor
                        scorer = StockScorer(lookback_days=DEFAULT_LOOKBACK_DAYS, forecast_days=DEFAULT_FORECAST_DAYS)
                        predictor = PricePredictor(forecast_days=DEFAULT_FORECAST_DAYS)
                        visualizer = StockVisualizer()
                        
                        # Score and rank stocks
                        top_stocks = scorer.rank_stocks(result['results'], top_n=5)
                        
                        if not top_stocks.empty:
                            # Store top stocks in result for later use
                            result['top_stocks_df'] = top_stocks
                            
                            # Add to Top 5 aggregator for combined visualization
                            scan_label = f"{result['universe']} | {result['source']} | {result['price_range']}"
                            add_to_top5_aggregator(
                                scan_label,
                                top_stocks,
                                lambda s: yf.Ticker(s).history(period="120d")
                            )
                            
                            # Display each top stock in an expander
                            for idx, row in top_stocks.iterrows():
                                symbol = row['symbol']
                                score = row.get('score', 0)
                                probability = row.get('probability', 0)
                                indicators = row.get('indicators', {})
                                score_contributions = row.get('score_contributions', {})
                                
                                # Rank display
                                rank_emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
                                rank_idx = list(top_stocks.index).index(idx)
                                
                                with st.expander(
                                    f"{rank_emoji[rank_idx]} **{symbol}** - Score: {score:.1f}/100 | Probability: {probability:.1f}%",
                                    expanded=False  # Collapsed by default for brevity
                                ):
                                    # Display metrics in columns
                                    col1, col2, col3, col4 = st.columns(4)
                                    
                                    with col1:
                                        st.metric("Current Price", f"${row.get('price', 0):.2f}")
                                    with col2:
                                        st.metric("Composite Score", f"{score:.1f}/100")
                                    with col3:
                                        st.metric("Upward Probability", f"{probability:.1f}%")
                                    with col4:
                                        volume = row.get('volume', 0)
                                        st.metric("Volume", format_volume(volume))
                                    
                                    # Fetch historical data for predictions
                                    hist_data = scorer.fetch_historical_data(symbol)
                                    
                                    if not hist_data.empty:
                                        # Price prediction
                                        current_price = row.get('price', row.get('close', 0))
                                        prediction = predictor.predict_price_range(symbol, current_price, hist_data)
                                        
                                        # Display prediction metrics
                                        st.markdown("##### 📈 Price Forecast")
                                        
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            st.metric(
                                                "Expected Target",
                                                f"${prediction['predicted_price']:.2f}",
                                                delta=f"{((prediction['predicted_price'] - current_price) / current_price * 100):.1f}%"
                                            )
                                        with col2:
                                            st.metric(
                                                "80% Confidence Range",
                                                f"${prediction['confidence_80_low']:.2f} - ${prediction['confidence_80_high']:.2f}"
                                            )
                                        with col3:
                                            st.metric(
                                                "Volatility",
                                                f"{prediction['volatility']:.1f}%",
                                                help="Annualized historical volatility"
                                            )
                                        
                                        # Generate and display chart
                                        st.markdown("##### 📊 Visualization")
                                        chart_img = visualizer.create_combined_chart(
                                            symbol, 
                                            {'score_contributions': score_contributions},
                                            prediction,
                                            hist_data
                                        )
                                        
                                        if chart_img:
                                            st.markdown(f'<img src="{chart_img}" style="width:100%"/>', unsafe_allow_html=True)
                                        else:
                                            st.info("Chart generation requires matplotlib. Install with: pip install matplotlib")
                                    
                                    # Indicator breakdown
                                    st.markdown("##### 🔍 Contributing Indicators")
                                    
                                    if indicators:
                                        # Create two columns for indicator display
                                        col1, col2 = st.columns(2)
                                        
                                        indicator_items = list(indicators.items())
                                        mid_point = len(indicator_items) // 2
                                        
                                        with col1:
                                            for key, value in indicator_items[:mid_point]:
                                                st.metric(key.replace('_', ' ').title(), f"{value}")
                                        
                                        with col2:
                                            for key, value in indicator_items[mid_point:]:
                                                st.metric(key.replace('_', ' ').title(), f"{value}")
                                    
                                    # Score breakdown
                                    if score_contributions:
                                        st.markdown("##### 📊 Score Breakdown")
                                        score_df = pd.DataFrame([
                                            {
                                                'Indicator': k.replace('_score', '').replace('_', ' ').title(),
                                                'Score': f"{v:.1f}/100"
                                            }
                                            for k, v in score_contributions.items()
                                        ])
                                        st.dataframe(score_df, use_container_width=True, hide_index=True)
                        else:
                            st.warning("⚠️ Unable to score stocks. Insufficient data for analysis.")
                    
                    except Exception as e:
                        st.error(f"❌ Error during scoring: {str(e)}")
                        st.info("This may be due to insufficient historical data. Try with different stocks.")
                
                st.markdown("---")
                
                # Download button
                csv = result['results'].to_csv(index=False)
                # Sanitize filename: replace non-alphanumeric chars with underscores
                import re
                safe_filename = re.sub(r'[^a-zA-Z0-9_-]', '_', result['scenario'])
                st.download_button(
                    label=f"📥 Download {result['scenario']} (CSV)",
                    data=csv,
                    file_name=f"{safe_filename}_results.csv",
                    mime="text/csv",
                    key=f"download_{result['scenario']}"
                )
    
    # Show failed scenarios if any
    failed_results = [r for r in all_results if r['status'] == 'failed']
    if failed_results:
        st.markdown("---")
        st.subheader("❌ Failed Scenarios")
        for result in failed_results:
            with st.expander(f"⚠️ {result['scenario']}", expanded=False):
                st.error(f"**Error:** {result.get('error', 'Unknown error')}")
    
    # Optional: Entry/Exit Suggestion Preview
    if "top5_union" in st.session_state and st.session_state["top5_union"]:
        st.markdown("---")
        st.markdown("### 🎯 Entry/Exit Suggestions")
        
        available_symbols = list(st.session_state["top5_union"].keys())
        selected_symbol = st.selectbox(
            "Select a symbol to preview entry/exit suggestions:",
            [""] + available_symbols,
            help="Choose a symbol from the Top 5 union to see suggested entry, stop, and target levels"
        )
        
        if selected_symbol:
            try:
                ticker = yf.Ticker(selected_symbol)
                hist_data = ticker.history(period="120d")
                
                if not hist_data.empty:
                    suggestion = suggest_entry_exit(hist_data)
                    
                    st.markdown(f"#### {selected_symbol} - {suggestion['strategy']}")
                    
                    if suggestion['entry'] is not None:
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Entry", f"${suggestion['entry']:.2f}")
                        with col2:
                            st.metric("Stop Loss", f"${suggestion['stop']:.2f}")
                        with col3:
                            st.metric("Target 1", f"${suggestion['target1']:.2f}")
                        with col4:
                            st.metric("Target 2", f"${suggestion['target2']:.2f}")
                        
                        st.info(f"**Confidence:** {suggestion['confidence']}")
                        
                        if suggestion['notes']:
                            st.markdown("**Notes:**")
                            for note in suggestion['notes']:
                                st.markdown(f"- {note}")
                    else:
                        st.warning(f"No clear entry/exit setup detected for {selected_symbol}")
                        if suggestion['notes']:
                            for note in suggestion['notes']:
                                st.markdown(f"- {note}")
                else:
                    st.warning(f"Unable to fetch historical data for {selected_symbol}")
            except Exception as e:
                st.error(f"Error generating suggestion: {str(e)}")


def render_top5_summary_tab():
    """
    Render the Top 5 Results tab with connection status, progress, and top stocks with entry/exit points
    """
    st.subheader("🏆 Top 5 Results Summary")
    
    # Connection Status
    st.markdown("### 🔌 Connection Status")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fdn_source = FinancialDataNetSource()
        if fdn_source.is_available():
            st.success("✅ FinancialData API Connected")
        else:
            st.warning("⚠️ FinancialData API Not configured")
    
    with col2:
        alpaca_key = os.getenv('ALPACA_API_KEY')
        alpaca_secret = os.getenv('ALPACA_API_SECRET')
        if alpaca_key and alpaca_secret:
            st.success("✅ Alpaca API Connected")
        else:
            st.info("ℹ️ Alpaca API Not configured")
    
    with col3:
        st.success("✅ Yahoo Finance Ready")
    
    st.markdown("---")
    
    # Progress/Completion Status
    if 'auto_run_all_results' in st.session_state:
        all_results = st.session_state['auto_run_all_results']
        total_scenarios = len(all_results)
        successful = len([r for r in all_results if r['status'] == 'success'])
        
        st.markdown("### 📊 Screening Progress")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Scenarios", total_scenarios)
        with col2:
            st.metric("Successful", successful)
        with col3:
            completion_pct = (successful / total_scenarios * 100) if total_scenarios > 0 else 0
            st.metric("Completion", f"{completion_pct:.0f}%")
        
        st.progress(completion_pct / 100)
    else:
        st.info("No screening data available. Click 'Refresh Scan' to run scenarios.")
        return
    
    st.markdown("---")
    
    # Get top 5 stocks from union
    if "top5_union" not in st.session_state or not st.session_state["top5_union"]:
        st.warning("⚠️ No top stocks available from screening.")
        return
    
    # Get all symbols with their scores from the top5 aggregator
    # We need to reconstruct scores from session state
    all_top_stocks = []
    
    if 'auto_run_all_results' in st.session_state:
        for result in st.session_state['auto_run_all_results']:
            if result.get('top_stocks_df') is not None and not result['top_stocks_df'].empty:
                for _, row in result['top_stocks_df'].iterrows():
                    all_top_stocks.append(row)
    
    if not all_top_stocks:
        st.warning("⚠️ No scored stocks available.")
        return
    
    # Convert to DataFrame and sort by score, get top 5
    all_top_df = pd.DataFrame(all_top_stocks)
    all_top_df = all_top_df.sort_values('score', ascending=False).drop_duplicates(subset=['symbol']).head(5)
    
    st.markdown("### 🎯 Top 5 Stocks with Entry/Exit Points")
    st.info(f"Displaying top {len(all_top_df)} stocks ranked by upward potential across all screening scenarios.")
    
    # Display each stock
    for idx, row in all_top_df.iterrows():
        symbol = row['symbol']
        score = row.get('score', 0)
        probability = row.get('probability', 0)
        
        rank_emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        rank_idx = list(all_top_df.index).index(idx)
        
        with st.expander(
            f"{rank_emoji[rank_idx]} **{symbol}** - Score: {score:.1f}/100 | Probability: {probability:.1f}%",
            expanded=(rank_idx == 0)
        ):
            # Basic metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Price", f"${row.get('price', 0):.2f}")
            with col2:
                st.metric("Composite Score", f"{score:.1f}/100")
            with col3:
                st.metric("Upward Probability", f"{probability:.1f}%")
            
            # Fetch entry/exit points
            try:
                import yfinance as yf
                ticker = yf.Ticker(symbol)
                hist_data = ticker.history(period="120d")
                
                if not hist_data.empty:
                    suggestion = suggest_entry_exit(hist_data)
                    
                    st.markdown("#### 📈 Entry/Exit Strategy")
                    st.markdown(f"**Strategy:** {suggestion['strategy']}")
                    
                    if suggestion['entry'] is not None:
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Entry Point", f"${suggestion['entry']:.2f}")
                        with col2:
                            st.metric("Stop Loss", f"${suggestion['stop']:.2f}")
                        with col3:
                            st.metric("Target 1", f"${suggestion['target1']:.2f}")
                        with col4:
                            st.metric("Target 2", f"${suggestion['target2']:.2f}")
                        
                        st.info(f"**Confidence:** {suggestion['confidence']}")
                        
                        if suggestion['notes']:
                            st.markdown("**Notes:**")
                            for note in suggestion['notes']:
                                st.markdown(f"- {note}")
                    else:
                        st.warning("No clear entry/exit setup detected")
                        if suggestion['notes']:
                            for note in suggestion['notes']:
                                st.markdown(f"- {note}")
                else:
                    st.warning(f"Unable to fetch historical data for {symbol}")
            except Exception as e:
                st.error(f"Error generating entry/exit suggestion: {str(e)}")


def render_all_scenarios_tab():
    """
    Render the All Scenarios tab with detailed results from all screening scenarios
    """
    if 'auto_run_all_results' not in st.session_state:
        st.info("No screening data available. Click 'Refresh Scan' to run scenarios.")
        return
    
    all_results = st.session_state['auto_run_all_results']
    
    # Summary table
    st.subheader("📊 Scenario Summary")
    summary_data = []
    for result in all_results:
        summary_data.append({
            'Scenario': result['scenario'],
            'Status': '✅ Success' if result['status'] == 'success' else ('⚠️ No Results' if result['status'] == 'no_results' else '❌ Failed'),
            'Source': result.get('source', 'N/A'),
            'Universe': result.get('universe', 'N/A'),
            'Price Range': result.get('price_range', 'N/A'),
            'Results Found': result.get('results_count', 0)
        })
    
    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    # Show detailed results for each successful scenario
    st.markdown("---")
    st.subheader("📈 Detailed Results")
    
    successful_results = [r for r in all_results if r['status'] == 'success' and not r['results'].empty]
    
    if not successful_results:
        st.warning("⚠️ No scenarios returned results. This could be due to:")
        st.markdown("""
        - Restrictive price filters (try wider ranges)
        - API connectivity issues
        - Empty universe sets
        - All stocks filtered out by price criteria
        
        **Recommendations:**
        1. Check your API keys are configured correctly
        2. Try running individual scenarios with broader price ranges
        3. Enable Developer Mode to see detailed error logs
        """)
    else:
        for result in successful_results:
            with st.expander(f"🔍 {result['scenario']} - {result['results_count']} stocks found", expanded=False):
                st.write(f"**Source:** {result['source']}")
                st.write(f"**Universe:** {result['universe']}")
                st.write(f"**Price Range:** {result['price_range']}")
                
                if result.get('is_fallback'):
                    st.warning("⚠️ Using fallback data source (Yahoo Finance)")
                
                # Display results
                display_df = result['results'].copy()
                
                # Format the dataframe
                if 'price' in display_df.columns:
                    display_df['price'] = display_df['price'].apply(lambda x: f"${x:,.2f}")
                if 'volume' in display_df.columns:
                    display_df['volume'] = display_df['volume'].apply(lambda x: f"{x:,}")
                if 'change' in display_df.columns:
                    display_df['change'] = display_df['change'].apply(lambda x: f"${x:,.2f}")
                if 'change_pct' in display_df.columns:
                    display_df['change_pct'] = display_df['change_pct'].apply(lambda x: f"{x:+.2f}%")
                
                # Rename columns
                column_mapping = {
                    'symbol': 'Symbol',
                    'price': 'Price',
                    'volume': 'Volume',
                    'change': 'Change ($)',
                    'change_pct': 'Change (%)',
                }
                display_df = display_df.rename(columns={col: column_mapping.get(col, col) for col in display_df.columns})
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)


def main():
    """Main application"""
    # Initialize session state for scalability
    init_session_state()
    
    st.title("📈 SwingTrade Stock Screener")
    st.markdown("---")
    
    # ========================================================================
    # AUTO-RUN MODE TOGGLE (Top of page)
    # ========================================================================
    auto_run_mode = st.checkbox(
        "🤖 Enable Auto-Run Mode",
        value=True,
        help="Automatically run through multiple screening scenarios without manual selection. "
             "This will test various combinations of data sources, universes, and price ranges.",
        key="auto_run_mode_checkbox"
    )
    
    if auto_run_mode:
        # Add refresh button to manually trigger re-scan
        col1, col2 = st.columns([6, 1])
        with col2:
            if st.button("🔄 Refresh Scan", help="Re-run all automated scenarios"):
                # Clear the execution flag to force re-run
                if 'auto_run_executed' in st.session_state:
                    del st.session_state['auto_run_executed']
                st.rerun()
        
        # Only execute the scan once per session unless manually refreshed
        # This prevents UI widget state changes (like expanders, radio buttons in the
        # combined top5 visualization) from re-triggering the scan operation
        # Note: Results are stored in session_state and will persist across re-renders
        if 'auto_run_executed' not in st.session_state:
            run_automated_scenarios()
            st.session_state['auto_run_executed'] = True
        
        # Create tabs for organized display
        tab1, tab2, tab3 = st.tabs([
            "🏆 Top 5 Results",
            "📊 All Scenarios",
            "📈 Combined Visualization"
        ])
        
        with tab1:
            render_top5_summary_tab()
        
        with tab2:
            render_all_scenarios_tab()
        
        with tab3:
            render_combined_top5_plot(default_lookback=60)
        
        st.markdown("---")
        st.info("💡 **Tip:** Uncheck 'Enable Auto-Run Mode' to return to manual screening mode. Click 'Refresh Scan' to update results.")
        return  # Exit early, don't show manual controls
    
    st.markdown("---")
    
    # ========================================================================
    # API STATUS DASHBOARD (Top of main area, before sidebar)
    # ========================================================================
    st.subheader("🔌 API Status Dashboard")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # FinancialData API Status
        fdn_source = FinancialDataNetSource()
        if fdn_source.is_available():
            st.success("✅ FinancialData API")
            st.caption("Connected & Ready")
        else:
            st.warning("⚠️ FinancialData API")
            st.caption("Not configured (fallback to Yahoo)")
    
    with col2:
        # Alpaca API Status
        alpaca_key = os.getenv('ALPACA_API_KEY')
        alpaca_secret = os.getenv('ALPACA_API_SECRET')
        if alpaca_key and alpaca_secret:
            st.success("✅ Alpaca API")
            st.caption("Credentials loaded")
        else:
            st.info("ℹ️ Alpaca API")
            st.caption("Not configured (optional)")
    
    with col3:
        # Developer Mode Status
        dev_mode = st.session_state.get('debug_log', {}).get('enabled', False)
        if dev_mode:
            st.info("🔧 Developer Mode: ON")
            st.caption("Debug logging enabled")
        else:
            st.info("Developer Mode: OFF")
            st.caption("Standard operation")
    
    st.markdown("---")
    
    # ========================================================================
    # SIDEBAR - REORGANIZED INTO NUMBERED SECTIONS
    # ========================================================================
    with st.sidebar:
        st.header("Filters")
        
        # Developer Mode Toggle (at top for easy access)
        st.markdown("---")
        st.subheader("🔧 Developer Mode")
        developer_mode = st.checkbox(
            "Enable Debug Log",
            value=st.session_state.get('debug_log', {}).get('enabled', False),
            help="Show detailed debug information including cache hits/misses, timing, API calls, and error traces"
        )
        st.session_state['debug_log']['enabled'] = developer_mode
        
        if developer_mode and st.button("Clear Debug Log", help="Clear all debug log entries"):
            clear_debug_log()
            st.success("Debug log cleared!")
        
        st.markdown("---")
        
        # ====================================================================
        # SECTION 1️⃣: DATA SOURCE
        # ====================================================================
        st.subheader("1️⃣ Data Source")
        source = st.radio(
            "Select data source:",
            ["Yahoo (EOD)", "Advanced Data (financialdata.net)", "Alpaca Movers (Intraday)"],
            index=0,
            help="Choose the data source for stock prices"
        )
        
        st.markdown("---")
        
        # ====================================================================
        # SECTION 2️⃣: UNIVERSE
        # ====================================================================
        st.subheader("2️⃣ Universe")
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
        
        # ====================================================================
        # SECTION 3️⃣: PRICE RANGE
        # ====================================================================
        st.subheader("3️⃣ Price Range")
        
        # Preset options dropdown
        price_preset = st.selectbox(
            "Preset:",
            ["Penny Stocks ($1-$10)", "Swing Trades ($10-$200)", "All Prices", "Custom"],
            index=1,  # Default to Swing Trades
            help="Select a price range preset or choose Custom for manual entry"
        )
        
        # Set price range based on preset
        if price_preset == "Penny Stocks ($1-$10)":
            min_price = 1.0
            max_price = 10.0
        elif price_preset == "Swing Trades ($10-$200)":
            min_price = 10.0
            max_price = 200.0
        elif price_preset == "All Prices":
            min_price = 0.0
            max_price = 10000.0
        else:  # Custom
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
        
        st.markdown("---")
        
        # ====================================================================
        # SECTION 4️⃣: TECHNICAL INDICATORS (for FinancialData)
        # ====================================================================
        financialdata_fields = []
        financialdata_interval = '1d'
        
        if source == "Advanced Data (financialdata.net)":
            st.subheader("4️⃣ Technical Indicators")
            
            # Check if API key is available and show detailed error if not
            fdn_source = FinancialDataNetSource()
            if not fdn_source.is_available():
                st.error("⚠️ **FinancialData API Key Missing**\n\n"
                        "The app will fall back to Yahoo Finance data.\n\n"
                        "**To enable Advanced Data:**\n\n"
                        "Add this to your `.env` file:\n"
                        "```\n"
                        "FINANCIALDATA_API_KEY=your_api_key_here\n"
                        "```\n\n"
                        "Get your API key from [FinancialData.Net](https://financialdata.net/)")
                
                # Debug expander
                with st.expander("🔍 Debug Information", expanded=False):
                    st.write("**SDK Status:**", "✅ Installed" if HAS_SDK else "❌ Not Installed")
                    api_key = os.getenv('FINANCIALDATA_API_KEY')
                    st.write("**API Key Found:**", "✅ Yes" if api_key else "❌ No")
                    st.write("**Client Available:**", "✅ Yes" if fdn_source.client else "❌ No")
            else:
                st.success("ℹ️ **Advanced Data Active** - Select optional fields below")
                
                # Field selector - MOVED OUT of expander for direct access
                st.markdown("**Technical Indicators:**")
                col1, col2 = st.columns(2)
                with col1:
                    if st.checkbox("Relative Volume (10d)", key="fdn_relvol"):
                        financialdata_fields.append("relative_volume_10d")
                    if st.checkbox("RSI", key="fdn_rsi"):
                        financialdata_fields.append("rsi")
                    if st.checkbox("MACD", key="fdn_macd"):
                        financialdata_fields.append("macd")
                with col2:
                    if st.checkbox("SMA 50", key="fdn_sma50"):
                        financialdata_fields.append("sma_50")
                    if st.checkbox("SMA 150", key="fdn_sma150"):
                        financialdata_fields.append("sma_150")
                    if st.checkbox("SMA 200", key="fdn_sma200"):
                        financialdata_fields.append("sma_200")
                
                st.markdown("**Moving Averages:**")
                ema_options = st.multiselect(
                    "EMA Periods",
                    options=["5", "10", "20", "50"],
                    help="Select exponential moving average periods"
                )
                for period in ema_options:
                    financialdata_fields.append(f"ema_{period}")
                
                st.markdown("**Fundamentals:**")
                col1, col2 = st.columns(2)
                with col1:
                    if st.checkbox("P/E Ratio", key="fdn_pe"):
                        financialdata_fields.append("pe_ratio")
                with col2:
                    if st.checkbox("EPS", key="fdn_eps"):
                        financialdata_fields.append("eps")
                
                # Timeframe selector
                financialdata_interval = st.selectbox(
                    "Timeframe",
                    options=["1d", "1h", "5m"],
                    index=0,
                    help="Select timeframe for OHLCV data"
                )
            
            st.markdown("---")
        
        # Alpaca-specific configuration (environment-only approach)
        alpaca_api_key = None
        alpaca_api_secret = None
        alpaca_movers_type = "most_actives"
        alpaca_top_n = 50
        
        if source == "Alpaca Movers (Intraday)":
            st.subheader("4️⃣ Alpaca Configuration")
            
            # Read from environment variables only
            alpaca_api_key = os.getenv('ALPACA_API_KEY')
            alpaca_api_secret = os.getenv('ALPACA_API_SECRET')
            
            # Show status
            if alpaca_api_key and alpaca_api_secret:
                st.success("✅ **Alpaca API credentials loaded successfully**")
            else:
                st.error("⚠️ **Alpaca API Credentials Missing**\n\n"
                        "The app will fall back to Yahoo Finance data.\n\n"
                        "**To enable Alpaca intraday data:**\n\n"
                        "Add these to your `.env` file:\n"
                        "```\n"
                        "ALPACA_API_KEY=your_api_key_here\n"
                        "ALPACA_API_SECRET=your_api_secret_here\n"
                        "```\n\n"
                        "Get your keys from [Alpaca Markets](https://alpaca.markets/)")
            
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
        
        # ====================================================================
        # SECTION 5️⃣: SCORING SYSTEM (NEW)
        # ====================================================================
        st.subheader("5️⃣ Scoring & Ranking")
        enable_scoring = st.checkbox(
            "Enable Top 5 Scoring System",
            value=True,
            help="Score and rank stocks by probability of upward trend. Shows top 5 with detailed analysis and price predictions."
        )
        
        forecast_days = 14
        if enable_scoring:
            forecast_days = st.slider(
                "Forecast Period (Days)",
                min_value=7,
                max_value=30,
                value=14,
                step=1,
                help="Number of days to forecast for price predictions"
            )
            st.info("📊 The scoring system analyzes RSI, MACD, moving averages, volume, and momentum to rank stocks by upward potential.")
        
        st.markdown("---")
    
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
        if (not alpaca_api_key and not os.getenv('ALPACA_API_KEY')) or \
           (not alpaca_api_secret and not os.getenv('ALPACA_API_SECRET')):
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
            # Progress indicators
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: Fetching symbols
            status_text.text("📋 Fetching symbols...")
            progress_bar.progress(25)
            
            # Step 2: Downloading data
            status_text.text(f"⬇️ Downloading data for {len(symbols)} symbols...")
            progress_bar.progress(50)
            
            # Fetch and filter data with diagnostic counts
            # Convert financialdata_fields to tuple for hashable caching
            financialdata_fields_tuple = tuple(financialdata_fields) if financialdata_fields else ()
            
            results_df, fetched_count, missing_price_count, after_price_filter_count, truncated, is_fallback, error_info = fetch_and_filter_data(
                source, symbols, min_price, max_price,
                alpaca_api_key=alpaca_api_key,
                alpaca_api_secret=alpaca_api_secret,
                alpaca_movers_type=alpaca_movers_type,
                alpaca_top_n=alpaca_top_n,
                financialdata_fields=financialdata_fields_tuple,
                financialdata_interval=financialdata_interval
            )
            
            # Step 3: Applying filters
            status_text.text("🔍 Applying filters...")
            progress_bar.progress(75)
            
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
            
            # Step 4: Complete
            status_text.text("✅ Complete!")
            progress_bar.progress(100)
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
    
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
            st.metric("After Price Filter", after_price_filter_count, 
                     help=f"Symbols within price range ${min_price:.2f} - ${max_price:.2f}" if price_range_valid 
                          else "Price filter not applied (invalid range)")
        
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
        elif data_source == "Advanced Data (financialdata.net)":
            if is_fallback:
                badge_color = "orange"
                badge_text = "⚠️ FinancialData.Net (Fallback to Yahoo)"
                badge_help = "FinancialData.Net unavailable or missing API key, using Yahoo Finance as fallback"
            else:
                badge_color = "green"
                badge_text = "✅ FinancialData.Net"
                badge_help = "Advanced data with prices, fundamentals, and technicals from FinancialData.Net"
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
        
        # Display results table
        if not results_df.empty:
            st.subheader("Filtered Stocks")
            
            # Add 4-column metrics above results table
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Stocks Found", filtered_count, 
                         help="Total number of stocks matching all filters")
            
            with col2:
                avg_price = results_df['price'].mean() if 'price' in results_df.columns else 0
                st.metric("Avg Price", f"${avg_price:.2f}", 
                         help="Average price of filtered stocks")
            
            with col3:
                avg_volume = results_df['volume'].mean() if 'volume' in results_df.columns else 0
                st.metric("Avg Volume", format_volume(avg_volume), 
                         help="Average daily volume of filtered stocks")
            
            with col4:
                if 'price' in results_df.columns and not results_df.empty:
                    price_min = results_df['price'].min()
                    price_max = results_df['price'].max()
                    st.metric("Price Range", f"${price_min:.2f} - ${price_max:.2f}", 
                             help="Actual price range of filtered stocks")
                else:
                    st.metric("Price Range", "N/A", help="No price data available")
            
            st.markdown("---")
            
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
            
            # ====================================================================
            # TOP 3 SCORING SYSTEM
            # ====================================================================
            if enable_scoring and filtered_count > 0:
                st.markdown("---")
                st.subheader("🏆 Top 5 Stocks by Upward Potential")
                
                with st.spinner("🔍 Analyzing stocks and calculating scores..."):
                    # Initialize scorer and predictor
                    scorer = StockScorer(lookback_days=DEFAULT_LOOKBACK_DAYS, forecast_days=forecast_days)
                    predictor = PricePredictor(forecast_days=forecast_days)
                    visualizer = StockVisualizer()
                    
                    # Score and rank stocks
                    try:
                        top_stocks = scorer.rank_stocks(results_df, top_n=5)
                        
                        if not top_stocks.empty:
                            # Display each top stock in an expander
                            for idx, row in top_stocks.iterrows():
                                symbol = row['symbol']
                                score = row.get('score', 0)
                                probability = row.get('probability', 0)
                                indicators = row.get('indicators', {})
                                score_contributions = row.get('score_contributions', {})
                                
                                # Rank display
                                rank_emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
                                rank_idx = list(top_stocks.index).index(idx)
                                
                                with st.expander(
                                    f"{rank_emoji[rank_idx]} **{symbol}** - Score: {score:.1f}/100 | Probability: {probability:.1f}%",
                                    expanded=(rank_idx == 0)  # Expand first one by default
                                ):
                                    # Display metrics in columns
                                    col1, col2, col3, col4 = st.columns(4)
                                    
                                    with col1:
                                        st.metric("Current Price", f"${row.get('price', 0):.2f}")
                                    with col2:
                                        st.metric("Composite Score", f"{score:.1f}/100")
                                    with col3:
                                        st.metric("Upward Probability", f"{probability:.1f}%")
                                    with col4:
                                        volume = row.get('volume', 0)
                                        st.metric("Volume", format_volume(volume))
                                    
                                    # Fetch historical data for predictions
                                    hist_data = scorer.fetch_historical_data(symbol)
                                    
                                    if not hist_data.empty:
                                        # Price prediction
                                        current_price = row.get('price', row.get('close', 0))
                                        prediction = predictor.predict_price_range(symbol, current_price, hist_data)
                                        
                                        # Display prediction metrics
                                        st.markdown("#### 📈 Price Forecast")
                                        
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            st.metric(
                                                "Expected Target",
                                                f"${prediction['predicted_price']:.2f}",
                                                delta=f"{((prediction['predicted_price'] - current_price) / current_price * 100):.1f}%"
                                            )
                                        with col2:
                                            st.metric(
                                                "80% Confidence Range",
                                                f"${prediction['confidence_80_low']:.2f} - ${prediction['confidence_80_high']:.2f}"
                                            )
                                        with col3:
                                            st.metric(
                                                "Volatility",
                                                f"{prediction['volatility']:.1f}%",
                                                help="Annualized historical volatility"
                                            )
                                        
                                        # Generate and display chart
                                        st.markdown("#### 📊 Visualization")
                                        chart_img = visualizer.create_combined_chart(
                                            symbol, 
                                            {'score_contributions': score_contributions},
                                            prediction,
                                            hist_data
                                        )
                                        
                                        if chart_img:
                                            st.markdown(f'<img src="{chart_img}" style="width:100%"/>', unsafe_allow_html=True)
                                        else:
                                            st.info("Chart generation requires matplotlib. Install with: pip install matplotlib")
                                    
                                    # Indicator breakdown
                                    st.markdown("#### 🔍 Contributing Indicators")
                                    
                                    if indicators:
                                        # Create two columns for indicator display
                                        col1, col2 = st.columns(2)
                                        
                                        indicator_items = list(indicators.items())
                                        mid_point = len(indicator_items) // 2
                                        
                                        with col1:
                                            for key, value in indicator_items[:mid_point]:
                                                st.metric(key.replace('_', ' ').title(), f"{value}")
                                        
                                        with col2:
                                            for key, value in indicator_items[mid_point:]:
                                                st.metric(key.replace('_', ' ').title(), f"{value}")
                                    
                                    # Score breakdown
                                    if score_contributions:
                                        st.markdown("#### 📊 Score Breakdown")
                                        score_df = pd.DataFrame([
                                            {
                                                'Indicator': k.replace('_score', '').replace('_', ' ').title(),
                                                'Score': f"{v:.1f}/100"
                                            }
                                            for k, v in score_contributions.items()
                                        ])
                                        st.dataframe(score_df, use_container_width=True, hide_index=True)
                        else:
                            st.warning("⚠️ Unable to score stocks. Insufficient data for analysis.")
                    
                    except Exception as e:
                        st.error(f"❌ Error during scoring: {str(e)}")
                        st.info("This may be due to insufficient historical data. Try with different stocks.")
            
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
        
        # Developer Mode: Debug Log Display
        if st.session_state.get('debug_log', {}).get('enabled', False):
            st.markdown("---")
            st.subheader("🔧 Debug Log")
            
            debug_log = st.session_state['debug_log']
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                cache_stats = debug_log['cache_stats']
                total_cache = sum(cache_stats.values())
                st.metric("Total Cache Operations", total_cache)
            with col2:
                api_stats = debug_log['api_calls']
                total_api = sum(api_stats.values())
                st.metric("Total API Calls", total_api)
            with col3:
                st.metric("Log Entries", len(debug_log['entries']))
            with col4:
                st.metric("Errors", len(debug_log['errors']))
            
            # Detailed sections
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📊 Cache Misses", "⏱️ Timings", "🌐 API Calls", "❌ Errors", "📝 Full Log"
            ])
            
            with tab1:
                st.subheader("Cache Statistics")
                st.info("**Note:** Due to Streamlit's caching mechanism, only cache misses are logged. "
                       "Cache hits occur when cached functions don't execute, so they're not counted. "
                       "The absence of new misses indicates cache hits are occurring.")
                cache_df = pd.DataFrame([
                    {
                        'Cache Type': 'Universe',
                        'Misses': cache_stats['universe_misses'],
                        'Note': 'Function executes on miss'
                    },
                    {
                        'Cache Type': 'Fetch',
                        'Misses': cache_stats['fetch_misses'],
                        'Note': 'Function executes on miss'
                    }
                ])
                st.dataframe(cache_df, use_container_width=True, hide_index=True)
            
            with tab2:
                st.subheader("Operation Timings")
                if debug_log['timings']:
                    timing_df = pd.DataFrame([
                        {'Operation': k, 'Duration (s)': f"{v:.3f}"}
                        for k, v in debug_log['timings'].items()
                    ])
                    st.dataframe(timing_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No timing data available. Run the screener to see timings.")
            
            with tab3:
                st.subheader("API Call Counts")
                api_df = pd.DataFrame([
                    {'Provider': k.capitalize(), 'Call Count': v}
                    for k, v in api_stats.items() if v > 0
                ])
                if not api_df.empty:
                    st.dataframe(api_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No API calls made yet. Run the screener to see API call statistics.")
            
            with tab4:
                st.subheader("Error Traces")
                if debug_log['errors']:
                    for i, error in enumerate(debug_log['errors'], 1):
                        with st.expander(f"Error {i}: {error['error_type']} in {error['context']}", expanded=False):
                            st.error(f"**Error Type:** {error['error_type']}")
                            st.text(f"Message: {error['error_message']}")
                            st.text("Traceback:")
                            st.code(error['traceback'], language='python')
                else:
                    st.success("No errors encountered!")
            
            with tab5:
                st.subheader("Full Debug Log")
                if debug_log['entries']:
                    # Create DataFrame for display
                    log_df = pd.DataFrame([
                        {
                            'Timestamp': entry['timestamp'],
                            'Category': entry['category'].upper(),
                            'Message': entry['message']
                        }
                        for entry in debug_log['entries']
                    ])
                    st.dataframe(log_df, use_container_width=True, hide_index=True)
                    
                    # Export debug log as CSV
                    debug_csv = log_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Debug Log (CSV)",
                        data=debug_csv,
                        file_name=f"debug_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                    
                    # Show detailed entries with expandable data
                    with st.expander("View Detailed Log Entries", expanded=False):
                        for entry in debug_log['entries']:
                            st.json(entry)
                else:
                    st.info("No log entries yet. Run the screener to see debug information.")
    else:
        st.info("👆 Click 'Run Screener' to fetch and filter stocks.")


if __name__ == "__main__":
    main()
