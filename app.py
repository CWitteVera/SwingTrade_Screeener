"""
SwingTrade Stock Screener
A Streamlit app for filtering stocks by price and universe
"""
import streamlit as st
import pandas as pd
from typing import List, Dict, Optional
import sys
import os
import re
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
from data_sources import YahooDataSource, AlpacaDataSource
from scoring_system import StockScorer
from price_predictor import PricePredictor
from visualizations import StockVisualizer
from combined_top5 import add_to_top5_aggregator, render_combined_top5_plot
from trade_signals import suggest_entry_exit, calculate_rsi, sma


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
HISTORICAL_DATA_PERIOD = "120d"  # Period for fetching historical data for analysis and charts
TOP_STOCKS_LIMIT = 5  # Number of top stocks to display in summary


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def prepare_score_data_for_chart(indicators: Dict) -> Dict:
    """
    Helper function to prepare score data for technical analysis chart
    
    Args:
        indicators: Dictionary of stock indicators
        
    Returns:
        Dictionary formatted for technical chart visualization
    """
    return {
        'support_resistance': {
            'support': indicators.get('Support_90d', 0),
            'resistance': indicators.get('Resistance_90d', 0),
            'relative_position': indicators.get('Relative_Position', 0)
        },
        'indicators': indicators
    }



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
                         alpaca_movers_type: str = "most_actives", alpaca_top_n: int = 50) -> tuple:
    """
    Fetch data and apply price filter with caching
    
    Caching Strategy:
    - Cache key includes: source_name, symbols, min_price, max_price, source-specific params
    - TTL: 5 minutes (reduces API calls when only slider moves)
    - When min_price/max_price change, cache is used if same values
    - Alpaca has additional internal caching
    
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
        if provider_key not in ['yahoo', 'alpaca']:
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
    
    # Process scoring for successful results
    successful_results = [r for r in all_results if r['status'] == 'success' and not r['results'].empty]
    
    for result in successful_results:
        try:
            # Initialize scorer
            scorer = StockScorer(lookback_days=DEFAULT_LOOKBACK_DAYS, forecast_days=DEFAULT_FORECAST_DAYS)
            
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
                    lambda s: yf.Ticker(s).history(period=HISTORICAL_DATA_PERIOD)
                )
        except Exception as e:
            # Skip scoring if it fails for this result
            continue
    
    # Store all results in session state for tab rendering
    st.session_state['auto_run_all_results'] = all_results


def render_top5_summary_tab():
    """
    Render the Top 5 Results tab with connection status, progress, and top stocks with entry/exit points
    """
    st.subheader("🏆 Top 5 Results Summary")
    
    # Connection Status
    st.markdown("### 🔌 Connection Status")
    col1, col2 = st.columns(2)
    
    with col1:
        alpaca_key = os.getenv('ALPACA_API_KEY')
        alpaca_secret = os.getenv('ALPACA_API_SECRET')
        if alpaca_key and alpaca_secret:
            st.success("✅ Alpaca API Connected")
        else:
            st.info("ℹ️ Alpaca API Not configured")
    
    with col2:
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
    all_top_df = all_top_df.sort_values('score', ascending=False).drop_duplicates(subset=['symbol']).head(TOP_STOCKS_LIMIT)
    
    st.markdown("### 🎯 Top 5 Stocks with Entry/Exit Points")
    st.info(f"Displaying top 5 stocks ranked by upward potential across all screening scenarios.")
    
    # Display each stock
    for idx, row in all_top_df.iterrows():
        symbol = row['symbol']
        score = row.get('score', 0)
        probability = row.get('probability', 0)
        score_contributions = row.get('score_contributions', {})
        indicators = row.get('indicators', {})
        
        rank_emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        rank_idx = list(all_top_df.index).index(idx)
        
        with st.expander(
            f"{rank_emoji[rank_idx]} **{symbol}** - Score: {score:.1f}/100 | Probability: {probability:.1f}%",
            expanded=(rank_idx == 0)
        ):
            # Basic metrics
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
            
            # Fetch historical data for charts and predictions
            try:
                ticker = yf.Ticker(symbol)
                hist_data = ticker.history(period=HISTORICAL_DATA_PERIOD)
                
                if not hist_data.empty:
                    # Price prediction
                    current_price = row.get('price', row.get('close', 0))
                    predictor = PricePredictor(forecast_days=DEFAULT_FORECAST_DAYS)
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
                    
                    # Combined Visualization & Technical Analysis chart
                    st.markdown("#### 📊 Visualization & Technical Analysis")
                    visualizer = StockVisualizer()
                    score_data_for_chart = prepare_score_data_for_chart(indicators)
                    full_chart_img = visualizer.create_full_analysis_chart(
                        symbol,
                        {'score_contributions': score_contributions},
                        prediction,
                        score_data_for_chart,
                        hist_data
                    )
                    
                    if full_chart_img:
                        st.markdown(f'<img src="{full_chart_img}" style="width:100%"/>', unsafe_allow_html=True)
                    else:
                        st.info("Chart generation requires matplotlib. Install with: pip install matplotlib")
                    
                    # Display breakout filters if available
                    breakout_filters = row.get('breakout_filters', {})
                    if breakout_filters:
                        st.markdown("##### 🚀 Breakout Signals")
                        filter_cols = st.columns(5)
                        
                        filter_names = ['Volume Spike', 'RSI Momentum', 'MACD Momentum', 'Position', 'Breakout']
                        filter_keys = ['volume_spike', 'rsi_momentum', 'macd_momentum', 'position_favorable', 'breakout_signal']
                        
                        for i, (name, key) in enumerate(zip(filter_names, filter_keys)):
                            with filter_cols[i]:
                                value = breakout_filters.get(key, False)
                                emoji = "✅" if value else "❌"
                                st.markdown(f"**{name}**<br>{emoji}", unsafe_allow_html=True)
                    
                    # Entry/Exit Strategy
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
                    
                    # Indicator breakdown
                    if indicators:
                        st.markdown("#### 🔍 Contributing Indicators")
                        col1, col2 = st.columns(2)
                        
                        indicator_items = list(indicators.items())
                        mid_point = len(indicator_items) // 2
                        
                        with col1:
                            for key, value in indicator_items[:mid_point]:
                                st.metric(key.replace('_', ' ').title(), f"{value}")
                        
                        with col2:
                            for key, value in indicator_items[mid_point:]:
                                st.metric(key.replace('_', ' ').title(), f"{value}")
                else:
                    st.warning(f"Unable to fetch historical data for {symbol}")
            except Exception as e:
                st.error(f"Error generating analysis: {str(e)}")


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
                
                # Display top 5 stocks with detailed analysis
                if result.get('top_stocks_df') is not None and not result['top_stocks_df'].empty:
                    st.markdown("---")
                    st.markdown("#### 🏆 Top 5 Stocks by Upward Potential")
                    
                    top_stocks = result['top_stocks_df']
                    predictor = PricePredictor(forecast_days=DEFAULT_FORECAST_DAYS)
                    scorer = StockScorer(lookback_days=DEFAULT_LOOKBACK_DAYS, forecast_days=DEFAULT_FORECAST_DAYS)
                    visualizer = StockVisualizer()
                    
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
                            expanded=False
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
                                
                                # Combined Visualization & Technical Analysis chart
                                st.markdown("##### 📊 Visualization & Technical Analysis")
                                score_data_for_chart = prepare_score_data_for_chart(indicators)
                                full_chart_img = visualizer.create_full_analysis_chart(
                                    symbol,
                                    {'score_contributions': score_contributions},
                                    prediction,
                                    score_data_for_chart,
                                    hist_data
                                )
                                
                                if full_chart_img:
                                    st.markdown(f'<img src="{full_chart_img}" style="width:100%"/>', unsafe_allow_html=True)
                                else:
                                    st.info("Chart generation requires matplotlib. Install with: pip install matplotlib")
                                
                                # Display breakout filters if available
                                breakout_filters = row.get('breakout_filters', {})
                                if breakout_filters:
                                    st.markdown("###### 🚀 Breakout Signals")
                                    filter_cols = st.columns(5)
                                    
                                    filter_names = ['Volume Spike', 'RSI Momentum', 'MACD Momentum', 'Position', 'Breakout']
                                    filter_keys = ['volume_spike', 'rsi_momentum', 'macd_momentum', 'position_favorable', 'breakout_signal']
                                    
                                    for i, (name, key) in enumerate(zip(filter_names, filter_keys)):
                                        with filter_cols[i]:
                                            value = breakout_filters.get(key, False)
                                            emoji = "✅" if value else "❌"
                                            st.markdown(f"**{name}**<br>{emoji}", unsafe_allow_html=True)
                            
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
                
                st.markdown("---")
                
                # Download button
                csv = result['results'].to_csv(index=False)
                # Sanitize filename: replace non-alphanumeric chars with underscores
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
    
    # Entry/Exit Suggestions
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
                hist_data = ticker.history(period=HISTORICAL_DATA_PERIOD)
                
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


# ============================================================================
# HOLDINGS FILE PATH
# ============================================================================
HOLDINGS_FILE = os.path.join(os.path.dirname(__file__), "my_holdings.csv")


def load_holdings() -> pd.DataFrame:
    """Load holdings from my_holdings.csv, returning empty DataFrame if not found."""
    if os.path.exists(HOLDINGS_FILE):
        try:
            df = pd.read_csv(HOLDINGS_FILE)
            required_cols = ['ticker', 'shares', 'avg_cost', 'purchase_date']
            if all(col in df.columns for col in required_cols):
                df['purchase_date'] = pd.to_datetime(df['purchase_date'], errors='coerce')
                return df
        except (OSError, pd.errors.ParserError, ValueError):
            pass
    return pd.DataFrame(columns=['ticker', 'shares', 'avg_cost', 'purchase_date', 'notes'])


def save_holdings(df: pd.DataFrame):
    """Save holdings DataFrame to my_holdings.csv."""
    save_df = df.copy()
    if 'purchase_date' in save_df.columns:
        save_df['purchase_date'] = save_df['purchase_date'].apply(
            lambda d: d.strftime('%Y-%m-%d') if pd.notna(d) else ''
        )
    save_df.to_csv(HOLDINGS_FILE, index=False)


def render_watchlist_tab():
    """
    Render the Watchlist tab for managing current holdings and getting
    buy/sell/average-down recommendations with tax awareness.
    """
    st.subheader("📋 My Watchlist & Holdings")
    st.info(
        f"Holdings are stored in `my_holdings.csv` (gitignored — your data stays private). "
        "Add your current positions below to get personalized buy/sell recommendations."
    )

    holdings_df = load_holdings()

    # -------------------------------------------------------------------------
    # Add new holding form
    # -------------------------------------------------------------------------
    st.markdown("### ➕ Add a Holding")
    with st.form("add_holding_form", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            new_ticker = st.text_input("Ticker Symbol", placeholder="AAPL")
        with col2:
            new_shares = st.number_input("Shares", min_value=0.001, value=1.0, step=0.001, format="%.3f")
        with col3:
            new_cost = st.number_input("Avg Cost/Share ($)", min_value=0.01, value=100.0, step=0.01, format="%.2f")
        with col4:
            new_date = st.date_input("Purchase Date", value=date.today())
        new_notes = st.text_input("Notes (optional)", placeholder="e.g., Initial position")
        submitted = st.form_submit_button("➕ Add Holding", type="primary")

    if submitted:
        ticker_clean = new_ticker.strip().upper()
        if ticker_clean:
            new_row = pd.DataFrame([{
                'ticker': ticker_clean,
                'shares': new_shares,
                'avg_cost': new_cost,
                'purchase_date': pd.Timestamp(new_date),
                'notes': new_notes
            }])
            holdings_df = pd.concat([holdings_df, new_row], ignore_index=True)
            save_holdings(holdings_df)
            st.success(f"Added {new_shares:.3f} shares of {ticker_clean} at ${new_cost:.2f}")
            st.rerun()

    if holdings_df.empty:
        st.warning("No holdings yet. Add your first position above or edit `my_holdings.csv` directly.")
        return

    st.markdown("---")

    # -------------------------------------------------------------------------
    # Summary table across all tickers
    # -------------------------------------------------------------------------
    st.markdown("### 📊 Portfolio Summary")

    tickers = holdings_df['ticker'].unique().tolist()

    # Fetch current prices (use fast_info to avoid heavy API calls)
    current_prices: Dict[str, Optional[float]] = {}
    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).fast_info
            price = getattr(info, 'last_price', None)
            current_prices[ticker] = float(price) if price and not pd.isna(price) else None
        except Exception:
            current_prices[ticker] = None

    summary_rows = []
    for ticker in tickers:
        lots = holdings_df[holdings_df['ticker'] == ticker]
        total_shares = lots['shares'].sum()
        weighted_cost = (lots['shares'] * lots['avg_cost']).sum() / total_shares
        cp = current_prices.get(ticker)

        today_ts = pd.Timestamp.now()
        has_st = any(
            (today_ts - lot['purchase_date']).days < 365
            for _, lot in lots.iterrows()
            if pd.notna(lot['purchase_date'])
        )
        has_lt = any(
            (today_ts - lot['purchase_date']).days >= 365
            for _, lot in lots.iterrows()
            if pd.notna(lot['purchase_date'])
        )
        tax_label = '/'.join(filter(None, ['ST' if has_st else '', 'LT' if has_lt else '']))

        if cp is not None:
            total_cost = total_shares * weighted_cost
            total_value = total_shares * cp
            pnl = total_value - total_cost
            pnl_pct = (pnl / total_cost * 100) if total_cost else 0
            summary_rows.append({
                'Ticker': ticker,
                'Shares': f"{total_shares:.3f}",
                'Avg Cost': f"${weighted_cost:.2f}",
                'Current Price': f"${cp:.2f}",
                'Total Value': f"${total_value:,.2f}",
                'P&L $': f"${pnl:+,.2f}",
                'P&L %': f"{pnl_pct:+.1f}%",
                'Tax Status': tax_label or 'Unknown',
            })
        else:
            summary_rows.append({
                'Ticker': ticker,
                'Shares': f"{total_shares:.3f}",
                'Avg Cost': f"${weighted_cost:.2f}",
                'Current Price': 'N/A',
                'Total Value': 'N/A',
                'P&L $': 'N/A',
                'P&L %': 'N/A',
                'Tax Status': tax_label or 'Unknown',
            })

    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)
    st.markdown("---")

    # -------------------------------------------------------------------------
    # Per-ticker detailed analysis
    # -------------------------------------------------------------------------
    st.markdown("### 🎯 Position Analysis & Recommendations")

    for ticker in tickers:
        lots = holdings_df[holdings_df['ticker'] == ticker]
        total_shares = lots['shares'].sum()
        weighted_cost = (lots['shares'] * lots['avg_cost']).sum() / total_shares
        cp = current_prices.get(ticker)

        # Quick headline for expander label
        if cp is not None:
            pnl_pct_val = (cp - weighted_cost) / weighted_cost * 100
            if pnl_pct_val > 15:
                headline = "🔴 Consider Selling"
            elif pnl_pct_val < -10:
                headline = "🟡 Review Position"
            else:
                headline = "🟢 Hold"
            price_str = f"${cp:.2f} (now) / ${weighted_cost:.2f} (avg) | {pnl_pct_val:+.1f}%"
        else:
            headline = "⚪ Price Unavailable"
            pnl_pct_val = None
            price_str = f"${weighted_cost:.2f} avg cost"

        with st.expander(
            f"**{ticker}** — {total_shares:.3f} shares | {price_str} | {headline}",
            expanded=True
        ):
            # --- Position metrics ---
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Avg Cost Basis", f"${weighted_cost:.2f}")
            with col2:
                if cp is not None:
                    st.metric(
                        "Current Price", f"${cp:.2f}",
                        delta=f"{pnl_pct_val:+.1f}%"
                    )
                else:
                    st.metric("Current Price", "N/A")
            with col3:
                if cp is not None:
                    total_pnl = (cp - weighted_cost) * total_shares
                    st.metric("Total P&L", f"${total_pnl:+,.2f}")
                else:
                    st.metric("Total P&L", "N/A")
            with col4:
                st.metric("Total Shares", f"{total_shares:.3f}")

            # --- Tax analysis ---
            st.markdown("#### 💰 Tax Lot Analysis")
            today_ts = pd.Timestamp.now()
            tax_rows = []
            for _, lot in lots.iterrows():
                if pd.notna(lot['purchase_date']):
                    days_held = (today_ts - lot['purchase_date']).days
                    is_lt = days_held >= 365
                    treatment = "Long-Term (≥1yr) — 0–20%" if is_lt else "Short-Term (<1yr) — up to 37%"
                    days_to_lt = max(0, 365 - days_held) if not is_lt else 0
                    lot_gain = (cp - lot['avg_cost']) * lot['shares'] if cp is not None else None
                    tax_rows.append({
                        'Purchase Date': lot['purchase_date'].strftime('%Y-%m-%d'),
                        'Shares': lot['shares'],
                        'Cost/Share': f"${lot['avg_cost']:.2f}",
                        'Days Held': days_held,
                        'Tax Treatment': treatment,
                        'Est. Gain/Loss': f"${lot_gain:+,.2f}" if lot_gain is not None else 'N/A',
                        'Days → Long-Term': days_to_lt if not is_lt else 'Already LT',
                        'Notes': lot.get('notes', ''),
                    })
            if tax_rows:
                st.dataframe(pd.DataFrame(tax_rows), use_container_width=True, hide_index=True)
                # Near-LT advisories
                for row in tax_rows:
                    dlt = row['Days → Long-Term']
                    if isinstance(dlt, int) and 0 < dlt <= 90:
                        st.warning(
                            f"⚠️ **Tax Advisory — {ticker}**: {row['Shares']} shares purchased "
                            f"{row['Purchase Date']} are **{dlt} days** from long-term treatment. "
                            "Waiting before selling could significantly reduce your tax bill."
                        )

            # --- Fetch historical data ---
            hist_data: Optional[pd.DataFrame] = None
            try:
                hist_data = yf.Ticker(ticker).history(period=HISTORICAL_DATA_PERIOD)
            except Exception:
                pass

            if hist_data is not None and not hist_data.empty:
                # --- Technical indicators ---
                st.markdown("#### 📊 Technical Indicators")
                rsi_val = calculate_rsi(hist_data)
                sma20_val = sma(hist_data, period=20)
                sma50_val = sma(hist_data, period=50)

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    rsi_str = f"{rsi_val:.1f}" if not pd.isna(rsi_val) else "N/A"
                    rsi_state = (
                        "Overbought (>70)" if not pd.isna(rsi_val) and rsi_val > 70
                        else ("Oversold (<30)" if not pd.isna(rsi_val) and rsi_val < 30 else "Neutral")
                    )
                    st.metric("RSI (14)", rsi_str, delta=rsi_state)
                with col2:
                    st.metric("SMA-20", f"${sma20_val:.2f}" if not pd.isna(sma20_val) else "N/A")
                with col3:
                    st.metric("SMA-50", f"${sma50_val:.2f}" if not pd.isna(sma50_val) else "N/A")
                with col4:
                    if cp is not None and not pd.isna(sma20_val):
                        pos_label = "Above SMA-20 ✅" if cp > sma20_val else "Below SMA-20 ⚠️"
                        st.metric("Trend Position", pos_label)

                # --- Chart ---
                st.markdown("#### 📈 Price Chart & Analysis")
                visualizer = StockVisualizer()
                predictor = PricePredictor(forecast_days=DEFAULT_FORECAST_DAYS)
                chart_price = cp if cp is not None else float(hist_data['Close'].iloc[-1])
                prediction = predictor.predict_price_range(ticker, chart_price, hist_data)
                chart_img = visualizer.create_full_analysis_chart(
                    ticker, {}, prediction,
                    {'support_resistance': {'support': 0, 'resistance': 0, 'relative_position': 0},
                     'indicators': {}},
                    hist_data
                )
                if chart_img:
                    st.markdown(f'<img src="{chart_img}" style="width:100%"/>', unsafe_allow_html=True)
                else:
                    st.info("Chart requires matplotlib: `pip install matplotlib`")

                # --- Entry/Exit technical levels ---
                suggestion = suggest_entry_exit(hist_data)
                if suggestion.get('entry') is not None:
                    st.markdown("#### 📍 Technical Entry/Exit Levels")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Entry Level", f"${suggestion['entry']:.2f}")
                    with col2:
                        st.metric("Stop Loss", f"${suggestion['stop']:.2f}")
                    with col3:
                        st.metric("Target 1", f"${suggestion['target1']:.2f}")
                    with col4:
                        st.metric("Target 2", f"${suggestion['target2']:.2f}")
                    st.caption(
                        f"Strategy: {suggestion['strategy']} | Confidence: {suggestion['confidence']}"
                    )

                # --- Buy/Sell Recommendations ---
                st.markdown("#### 💡 Buy / Sell Recommendations")
                if cp is not None:
                    sell_signals = []
                    buy_signals = []

                    # RSI signals
                    if not pd.isna(rsi_val):
                        if rsi_val > 70:
                            sell_signals.append(
                                f"RSI overbought ({rsi_val:.1f} > 70) — momentum may be fading"
                            )
                        elif rsi_val < 30:
                            buy_signals.append(
                                f"RSI oversold ({rsi_val:.1f} < 30) — potential bounce opportunity"
                            )

                    # SMA signals
                    if not pd.isna(sma20_val):
                        if cp < sma20_val * 0.97:
                            sell_signals.append(
                                f"Price >3% below SMA-20 (${sma20_val:.2f}) — bearish signal"
                            )
                        elif cp > sma20_val:
                            buy_signals.append(f"Price above SMA-20 (${sma20_val:.2f}) — uptrend intact")

                    # P&L signals
                    if pnl_pct_val is not None:
                        if pnl_pct_val > 20:
                            sell_signals.append(
                                f"Position up {pnl_pct_val:.1f}% — consider taking profits"
                            )
                        if pnl_pct_val < -15:
                            sell_signals.append(
                                f"Position down {pnl_pct_val:.1f}% — consider cutting losses"
                            )
                            buy_signals.append(
                                f"Position down {pnl_pct_val:.1f}% — averaging down could lower cost basis "
                                "(only if you are confident in the stock's fundamentals)"
                            )

                    # Tax-aware sell signal
                    for row in tax_rows:
                        dlt = row['Days → Long-Term']
                        if isinstance(dlt, int) and 0 < dlt <= 90:
                            sell_signals.append(
                                f"⚠️ Tax: {row['Shares']} shares are {dlt} days from long-term treatment — "
                                "delay selling this lot to qualify for lower capital-gains rate"
                            )

                    # Technical strategy signals
                    strategy = suggestion.get('strategy', '')
                    if 'Breakout' in strategy:
                        buy_signals.append(
                            f"Technical breakout detected ({strategy}) — positive momentum"
                        )
                    elif 'Pullback' in strategy:
                        buy_signals.append(
                            f"Pullback entry opportunity ({strategy}) — consider adding on dips"
                        )

                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("##### 🔴 Sell / Reduce Signals")
                        if sell_signals:
                            for sig in sell_signals:
                                st.markdown(f"- {sig}")
                        else:
                            st.success("No sell signals at this time")
                    with col2:
                        st.markdown("##### 🟢 Buy / Average Down Signals")
                        if buy_signals:
                            for sig in buy_signals:
                                st.markdown(f"- {sig}")
                        else:
                            st.info("No buy/add signals at this time")

                    # Overall action box
                    st.markdown("##### 📋 Overall Recommendation")
                    tax_urgent = any(
                        isinstance(r.get('Days → Long-Term'), int) and 0 < r['Days → Long-Term'] <= 30
                        for r in tax_rows
                    )
                    n_sell = len(sell_signals)
                    n_buy = len(buy_signals)

                    if tax_urgent:
                        st.warning(
                            "🚨 **HOLD — Tax Priority**: One or more lots are within 30 days of qualifying "
                            "for long-term capital gains. Wait before selling these lots to minimize taxes, "
                            "unless a significant technical breakdown warrants immediate action."
                        )
                    elif n_sell > n_buy and pnl_pct_val is not None and pnl_pct_val > 0:
                        any_st = any('Short-Term' in r['Tax Treatment'] for r in tax_rows)
                        tax_note = "Check tax treatment before selling — some lots are short-term." if any_st else "Long-term rates apply."
                        st.error(
                            f"🔴 **CONSIDER SELLING**: Multiple sell signals with a {pnl_pct_val:.1f}% gain. "
                            f"Consider selling all or part of your position. {tax_note}"
                        )
                    elif n_sell > n_buy and pnl_pct_val is not None and pnl_pct_val < -10:
                        st.error(
                            f"🔴 **CONSIDER EXITING**: Down {pnl_pct_val:.1f}% with bearish signals. "
                            "Consider exiting completely to limit further losses."
                        )
                    elif n_buy > n_sell and pnl_pct_val is not None and pnl_pct_val < -5:
                        st.warning(
                            f"🟡 **CONSIDER AVERAGING DOWN**: Down {pnl_pct_val:.1f}% with positive technical "
                            "signals. Averaging down can improve your cost basis but increases position risk — "
                            "only do this with conviction in the stock's fundamentals."
                        )
                    elif n_buy > n_sell:
                        msg = (
                            "Consider adding to your position on dips."
                            if pnl_pct_val is not None and pnl_pct_val < 10
                            else "Hold and let winners run."
                        )
                        st.success(f"🟢 **HOLD / ADD**: Positive signals present. {msg}")
                    else:
                        pnl_str = f"{pnl_pct_val:+.1f}%" if pnl_pct_val is not None else "N/A"
                        st.info(f"⚪ **HOLD**: Mixed or neutral signals. Monitor the position. Current P&L: {pnl_str}")
                else:
                    st.warning("Current price unavailable — cannot generate buy/sell recommendations.")
            else:
                st.warning(f"Unable to fetch historical data for **{ticker}**.")

            # --- Remove lot buttons ---
            st.markdown("#### 🗑️ Remove Lots")
            lots_reset = lots.reset_index()
            for _, lot_row in lots_reset.iterrows():
                orig_idx = lot_row['index']
                date_str = (
                    lot_row['purchase_date'].strftime('%Y-%m-%d')
                    if pd.notna(lot_row['purchase_date']) else 'Unknown date'
                )
                label = f"Remove: {lot_row['shares']:.3f} shares @ ${lot_row['avg_cost']:.2f} ({date_str})"
                if st.button(label, key=f"remove_{ticker}_{orig_idx}"):
                    holdings_df = holdings_df.drop(index=orig_idx).reset_index(drop=True)
                    save_holdings(holdings_df)
                    st.success(f"Removed lot from {ticker}")
                    st.rerun()


def render_backtest_tab():
    """
    Render the Backtesting tab for testing and refining screening criteria
    against historical data to measure predictive accuracy.
    """
    from datetime import timedelta

    st.subheader("📉 Backtesting — Refine Your Screening Tools")
    st.info(
        "Simulate running the screener at a past date and measure how selected stocks "
        "actually performed afterward. Use this to evaluate and tune your screening criteria."
    )

    col1, col2 = st.columns(2)

    with col1:
        backtest_symbols_input = st.text_area(
            "Symbols to backtest (comma-separated):",
            value="AAPL, MSFT, GOOGL, AMZN, TSLA, NVDA, META, NFLX",
            help="Enter stock symbols to include in the backtest",
            height=100
        )

    with col2:
        period_options = {
            "30 days ago": 30,
            "60 days ago": 60,
            "90 days ago": 90,
            "6 months ago": 180,
            "1 year ago": 365,
        }
        period_label = st.selectbox(
            "Signal Date (simulate screener running):",
            list(period_options.keys()),
            index=1,
            help="The hypothetical date when you would have run the screener"
        )
        lookback_days = period_options[period_label]

        forward_window = st.slider(
            "Forward Performance Window (days):",
            min_value=5,
            max_value=60,
            value=14,
            step=1,
            help="How many days after the signal date to measure performance"
        )

        min_score_threshold = st.slider(
            "Minimum Score Filter:",
            min_value=0,
            max_value=100,
            value=0,
            step=5,
            help="Only include stocks that met this score threshold at the signal date"
        )

    run_bt = st.button("🚀 Run Backtest", type="primary", use_container_width=True)

    if run_bt:
        symbols = [s.strip().upper() for s in
                   backtest_symbols_input.replace('\n', ',').split(',') if s.strip()]
        if not symbols:
            st.warning("⚠️ Please enter at least one symbol.")
            return

        total_days_needed = lookback_days + forward_window + 60  # extra buffer
        scorer = StockScorer(lookback_days=DEFAULT_LOOKBACK_DAYS, forecast_days=forward_window)

        results = []
        progress = st.progress(0)
        status = st.empty()

        for i, symbol in enumerate(symbols):
            status.text(f"Processing {symbol} ({i + 1}/{len(symbols)})...")
            progress.progress((i + 1) / len(symbols))

            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=f"{total_days_needed}d")

                if hist.empty or len(hist) < lookback_days + forward_window:
                    results.append({
                        'Symbol': symbol,
                        'Signal Price': None,
                        'Exit Price': None,
                        'Return %': None,
                        'Score': None,
                        'Probability': None,
                        'Regime': None,
                        'Status': 'Insufficient Data'
                    })
                    continue

                # Slice: signal history = everything except the last forward_window rows
                signal_hist = hist.iloc[:-forward_window]
                if len(signal_hist) < 20:
                    results.append({
                        'Symbol': symbol,
                        'Signal Price': None,
                        'Exit Price': None,
                        'Return %': None,
                        'Score': None,
                        'Probability': None,
                        'Regime': None,
                        'Status': 'Insufficient Data'
                    })
                    continue

                signal_price = float(signal_hist['Close'].iloc[-1])

                # Score the stock using only signal-date data
                score_result = scorer.score_stock_from_hist(symbol, signal_price, signal_hist)

                # Actual price after forward_window trading days
                exit_price = float(hist['Close'].iloc[-1])
                pct_change = (exit_price - signal_price) / signal_price * 100

                results.append({
                    'Symbol': symbol,
                    'Signal Price': round(signal_price, 2),
                    'Exit Price': round(exit_price, 2),
                    'Return %': round(pct_change, 2),
                    'Score': round(score_result.get('score', 0), 1),
                    'Probability': round(score_result.get('probability', 0), 1),
                    'Regime': score_result.get('regime', 'N/A'),
                    'Status': 'Success'
                })

            except Exception as e:
                results.append({
                    'Symbol': symbol,
                    'Signal Price': None,
                    'Exit Price': None,
                    'Return %': None,
                    'Score': None,
                    'Probability': None,
                    'Regime': None,
                    'Status': f'Error: {str(e)}'
                })

        progress.empty()
        status.empty()

        success_rows = [r for r in results if r['Status'] == 'Success']
        failed_rows = [r for r in results if r['Status'] != 'Success']

        if not success_rows:
            st.warning("⚠️ No successful backtest results. Check the symbols and try again.")
        else:
            df = pd.DataFrame(success_rows)

            # Apply minimum score filter
            if min_score_threshold > 0:
                filtered_df = df[df['Score'] >= min_score_threshold].copy()
                if filtered_df.empty:
                    st.warning(
                        f"No stocks met the minimum score of {min_score_threshold}. "
                        "Showing all results instead."
                    )
                    filtered_df = df
            else:
                filtered_df = df

            # Summary metrics
            avg_return = filtered_df['Return %'].mean()
            win_rate = (filtered_df['Return %'] > 0).mean() * 100
            best_idx = filtered_df['Return %'].idxmax()
            worst_idx = filtered_df['Return %'].idxmin()
            best = filtered_df.loc[best_idx]
            worst = filtered_df.loc[worst_idx]

            st.markdown("### 📊 Backtest Summary")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Signals Analyzed", len(filtered_df))
            with c2:
                st.metric(
                    "Avg Return",
                    f"{avg_return:.1f}%",
                    delta=f"{avg_return:.1f}%",
                    delta_color="normal"
                )
            with c3:
                st.metric("Win Rate", f"{win_rate:.0f}%")
            with c4:
                st.metric(
                    "Best Performer",
                    best['Symbol'],
                    delta=f"{best['Return %']:.1f}%"
                )

            # Score vs Return correlation
            if len(filtered_df) >= 2:
                corr = filtered_df[['Score', 'Return %']].corr().iloc[0, 1]
                if abs(corr) >= 0.5:
                    corr_msg = f"Strong correlation ({corr:.2f}) between score and return."
                elif abs(corr) >= 0.25:
                    corr_msg = f"Moderate correlation ({corr:.2f}) between score and return."
                else:
                    corr_msg = f"Weak correlation ({corr:.2f}) between score and return."
                st.info(f"📈 **Predictive Power:** {corr_msg}")

            st.markdown("### 📋 Detailed Results")
            display_df = filtered_df.copy()
            display_df['Signal Price'] = display_df['Signal Price'].apply(lambda x: f"${x:.2f}")
            display_df['Exit Price'] = display_df['Exit Price'].apply(lambda x: f"${x:.2f}")
            display_df['Return %'] = display_df['Return %'].apply(
                lambda x: f"{x:+.1f}%"
            )
            display_df['Score'] = display_df['Score'].apply(lambda x: f"{x:.1f}/100")
            display_df['Probability'] = display_df['Probability'].apply(lambda x: f"{x:.1f}%")
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            # Download
            csv_data = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Backtest Results (CSV)",
                data=csv_data,
                file_name=f"backtest_{period_label.replace(' ', '_')}.csv",
                mime="text/csv"
            )

            # Worst performer note
            st.caption(
                f"Worst performer: {worst['Symbol']} ({worst['Return %']:+.1f}%) | "
                f"Signal period: {period_label} | "
                f"Forward window: {forward_window} days"
            )

            # ------------------------------------------------------------------ #
            # Backtested forecast accuracy charts (one per symbol)
            # ------------------------------------------------------------------ #
            st.markdown("### 📈 Backtested Forecast Charts")
            st.info(
                "Each chart overlays historical forecast cones on the price history. "
                "🟢 **Green** = the actual price landed inside the predicted 80% confidence band (hit). "
                "🔴 **Red** = the price fell outside the band (miss). "
                "🟣 **Purple** = the current forward-looking forecast."
            )
            bt_visualizer = StockVisualizer()
            for result_row in success_rows:
                bt_symbol = result_row['Symbol']
                with st.expander(f"📊 {bt_symbol} — Forecast History", expanded=False):
                    try:
                        bt_ticker = yf.Ticker(bt_symbol)
                        bt_hist = bt_ticker.history(period=f"{total_days_needed}d")
                        if not bt_hist.empty and len(bt_hist) >= forward_window * 3 + 20:
                            bt_chart = bt_visualizer.create_backtested_forecast_chart(
                                bt_symbol, bt_hist, forecast_days=forward_window,
                                # +1 reserves one extra window for look-ahead validation
                                num_past_forecasts=min(5, len(bt_hist) // (forward_window + 1))
                            )
                            if bt_chart:
                                st.markdown(
                                    f'<img src="{bt_chart}" style="width:100%"/>',
                                    unsafe_allow_html=True
                                )
                            else:
                                st.info("Not enough historical data to render forecast chart.")
                        else:
                            st.info("Not enough historical data to render forecast chart.")
                    except Exception as bt_err:
                        st.warning(f"Could not render chart for {bt_symbol}: {bt_err}")

        if failed_rows:
            with st.expander(f"⚠️ {len(failed_rows)} symbol(s) with issues", expanded=False):
                for r in failed_rows:
                    st.write(f"**{r['Symbol']}**: {r['Status']}")


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
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🏆 Top 5 Results",
            "📊 All Scenarios",
            "📈 Combined Visualization",
            "📉 Backtesting",
            "📋 Watchlist"
        ])
        
        with tab1:
            render_top5_summary_tab()
        
        with tab2:
            render_all_scenarios_tab()
        
        with tab3:
            render_combined_top5_plot(default_lookback=60)
        
        with tab4:
            render_backtest_tab()
        
        with tab5:
            render_watchlist_tab()
        
        st.markdown("---")
        st.info("💡 **Tip:** Uncheck 'Enable Auto-Run Mode' to return to manual screening mode. Click 'Refresh Scan' to update results.")
        return  # Exit early, don't show manual controls
    
    st.markdown("---")
    
    # ========================================================================
    # API STATUS DASHBOARD (Top of main area, before sidebar)
    # ========================================================================
    st.subheader("🔌 API Status Dashboard")
    col1, col2 = st.columns(2)
    
    with col1:
        # Alpaca API Status
        alpaca_key = os.getenv('ALPACA_API_KEY')
        alpaca_secret = os.getenv('ALPACA_API_SECRET')
        if alpaca_key and alpaca_secret:
            st.success("✅ Alpaca API")
            st.caption("Credentials loaded")
        else:
            st.info("ℹ️ Alpaca API")
            st.caption("Not configured (optional)")
    
    with col2:
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
            ["Yahoo (EOD)", "Alpaca Movers (Intraday)"],
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
            results_df, fetched_count, missing_price_count, after_price_filter_count, truncated, is_fallback, error_info = fetch_and_filter_data(
                source, symbols, min_price, max_price,
                alpaca_api_key=alpaca_api_key,
                alpaca_api_secret=alpaca_api_secret,
                alpaca_movers_type=alpaca_movers_type,
                alpaca_top_n=alpaca_top_n
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
                                        
                                        # Combined Visualization & Technical Analysis chart
                                        st.markdown("#### 📊 Visualization & Technical Analysis")
                                        score_data_for_chart = prepare_score_data_for_chart(indicators)
                                        full_chart_img = visualizer.create_full_analysis_chart(
                                            symbol,
                                            {'score_contributions': score_contributions},
                                            prediction,
                                            score_data_for_chart,
                                            hist_data
                                        )
                                        
                                        if full_chart_img:
                                            st.markdown(f'<img src="{full_chart_img}" style="width:100%"/>', unsafe_allow_html=True)
                                        else:
                                            st.info("Chart generation requires matplotlib. Install with: pip install matplotlib")
                                        
                                        # Display breakout filters if available
                                        breakout_filters = row.get('breakout_filters', {})
                                        if breakout_filters:
                                            st.markdown("##### 🚀 Breakout Signals")
                                            filter_cols = st.columns(5)
                                            
                                            filter_names = ['Volume Spike', 'RSI Momentum', 'MACD Momentum', 'Position', 'Breakout']
                                            filter_keys = ['volume_spike', 'rsi_momentum', 'macd_momentum', 'position_favorable', 'breakout_signal']
                                            
                                            for i, (name, key) in enumerate(zip(filter_names, filter_keys)):
                                                with filter_cols[i]:
                                                    value = breakout_filters.get(key, False)
                                                    emoji = "✅" if value else "❌"
                                                    st.markdown(f"**{name}**<br>{emoji}", unsafe_allow_html=True)
                                    
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

    # Additional tabs always visible in manual mode
    st.markdown("---")
    tab_backtest, tab_watchlist = st.tabs(["📉 Backtesting", "📋 Watchlist"])
    with tab_backtest:
        render_backtest_tab()
    with tab_watchlist:
        render_watchlist_tab()


if __name__ == "__main__":
    main()
