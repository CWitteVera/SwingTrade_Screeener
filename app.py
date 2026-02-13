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
def fetch_and_filter_data(source_name: str, symbols: List[str], min_price: float, max_price: float) -> pd.DataFrame:
    """
    Fetch data and apply price filter with caching
    
    Args:
        source_name: Name of the data source
        symbols: List of symbols to fetch
        min_price: Minimum price filter
        max_price: Maximum price filter
        
    Returns:
        Filtered DataFrame
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
    
    # Apply price filter
    if not df.empty:
        df = df[(df['price'] >= min_price) & (df['price'] <= max_price)]
    
    return df


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
        st.slider(
            "Price Range Visual",
            min_value=0.0,
            max_value=1000.0,
            value=(min_price, min(max_price, 1000.0)),
            disabled=True,
            help="Visual representation of selected price range"
        )
    
    # Main content area
    st.header("Results")
    
    # Get symbols for selected universe
    symbols = get_universe_symbols(universe_set, custom_symbols)
    
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
                # Fetch and filter data
                results_df = fetch_and_filter_data(source, symbols, min_price, max_price)
                
                # Store in session state
                st.session_state['results'] = results_df
                st.session_state['filtered_count'] = len(results_df)
    
    # Display results
    if 'results' in st.session_state:
        results_df = st.session_state['results']
        filtered_count = st.session_state['filtered_count']
        
        st.markdown("---")
        
        # Results summary
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Matched Symbols", filtered_count)
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
