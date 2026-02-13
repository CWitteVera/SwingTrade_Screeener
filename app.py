"""
SwingTrade Stock Screener
A Streamlit app for filtering stocks by price and universe
"""
import streamlit as st
import pandas as pd
from typing import List
import sys
import os

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


def parse_custom_symbols(text: str) -> List[str]:
    """Parse comma-separated symbols from text input"""
    if not text:
        return []
    return [s.strip().upper() for s in text.replace('\n', ',').split(',') if s.strip()]


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_cached_universe_symbols(universe_set: str, custom_symbols_tuple: tuple = None) -> List[str]:
    """
    Cached wrapper for getting universe symbols
    
    Args:
        universe_set: Name of the universe set
        custom_symbols_tuple: Tuple of custom symbols (tuple is hashable for caching)
        
    Returns:
        List of symbols in the universe
    """
    custom_symbols = list(custom_symbols_tuple) if custom_symbols_tuple else None
    return get_universe_symbols(universe_set, custom_symbols)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_and_filter_data(source_name: str, symbols: List[str], min_price: float, max_price: float) -> tuple:
    """
    Fetch data and apply price filter with caching
    
    Caching Strategy:
    - Cache key includes: source_name, symbols, min_price, max_price
    - TTL: 5 minutes (reduces API calls when only slider moves)
    - When min_price/max_price change, cache is used if same values
    
    Args:
        source_name: Name of the data source
        symbols: List of symbols to fetch
        min_price: Minimum price filter
        max_price: Maximum price filter
        
    Returns:
        Tuple of (filtered_df, fetched_count, missing_price_count, after_price_filter_count)
    """
    # Select data source
    if source_name == "Yahoo (EOD)":
        source = YahooDataSource()
    elif source_name == "TradingView (Advanced)":
        source = TradingViewDataSource()
    else:  # Alpaca Movers (Intraday)
        source = AlpacaDataSource()
    
    # Fetch data
    df = source.fetch_data(symbols)
    
    # Track counts for diagnostics
    fetched_count = len(df)
    missing_price_count = df.attrs.get('missing_price_count', 0)
    
    # Apply price filter immediately after fetch/normalize
    # Symbols without valid price have already been dropped in fetch_data
    if not df.empty:
        df = df[(df['price'] >= min_price) & (df['price'] <= max_price)]
    
    after_price_filter_count = len(df)
    
    return df, fetched_count, missing_price_count, after_price_filter_count


def main():
    """Main application"""
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
                results_df, fetched_count, missing_price_count, after_price_filter_count = fetch_and_filter_data(
                    source, symbols, min_price, max_price
                )
                
                # Store in session state
                st.session_state['results'] = results_df
                st.session_state['fetched_count'] = fetched_count
                st.session_state['missing_price_count'] = missing_price_count
                st.session_state['after_price_filter_count'] = after_price_filter_count
                st.session_state['filtered_count'] = len(results_df)
                st.session_state['data_source'] = source
    
    # Display results
    if 'results' in st.session_state:
        results_df = st.session_state['results']
        filtered_count = st.session_state['filtered_count']
        fetched_count = st.session_state.get('fetched_count', 0)
        missing_price_count = st.session_state.get('missing_price_count', 0)
        after_price_filter_count = st.session_state.get('after_price_filter_count', 0)
        data_source = st.session_state.get('data_source', source)
        
        st.markdown("---")
        
        # Diagnostic counts: Fetched → After price filter → After all filters
        st.subheader("📊 Filtering Pipeline")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Requested", len(symbols), help="Total symbols in selected universe")
        with col2:
            st.metric("Fetched", fetched_count, help="Symbols with valid price data")
        with col3:
            missing_delta = f"-{missing_price_count}" if missing_price_count > 0 else None
            st.metric("Missing Price", missing_price_count, delta=missing_delta, delta_color="inverse", 
                     help="Symbols dropped due to missing/invalid price data")
        with col4:
            st.metric("After Price Filter", after_price_filter_count, 
                     help=f"Symbols within price range ${min_price:.2f} - ${max_price:.2f}")
        
        # Data source note
        if data_source == "Yahoo (EOD)":
            st.info("📌 **Data source:** Yahoo Finance (EOD/Delayed) - Prices represent end-of-day closing values")
        
        st.markdown("---")
        
        # Results summary
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Final Matched Symbols", filtered_count)
        with col2:
            filter_pct = (filtered_count / len(symbols) * 100) if len(symbols) > 0 else 0
            st.metric("Filter Rate", f"{filter_pct:.1f}%")
        
        # Display results table
        if not results_df.empty:
            st.subheader("Filtered Stocks")
            
            # Format the dataframe for display
            display_df = results_df.copy()
            display_df['price'] = display_df['price'].apply(lambda x: f"${x:,.2f}")
            display_df['volume'] = display_df['volume'].apply(lambda x: f"{x:,}")
            display_df['change'] = display_df['change'].apply(lambda x: f"${x:,.2f}")
            display_df['change_pct'] = display_df['change_pct'].apply(lambda x: f"{x:+.2f}%")
            
            # Rename columns for display
            display_df.columns = ['Symbol', 'Price', 'Volume', 'Change ($)', 'Change (%)']
            
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
