"""
Combined Top 5 Aggregator and Visualization
Aggregates Top 5 symbols from all auto-run scans and provides visualization
"""
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import Callable, Dict, List, Optional


def add_to_top5_aggregator(scan_label: str, top_df: pd.DataFrame, data_fetcher_fn: Callable):
    """
    Add Top 5 symbols from a scan to the aggregator
    
    Args:
        scan_label: Descriptive label for the scan (e.g., "SP500 | Yahoo | $50-100")
        top_df: DataFrame with top stocks (should have 'symbol' column)
        data_fetcher_fn: Function to fetch historical data for a symbol
                         e.g., lambda s: yf.Ticker(s).history(period="120d")
    """
    # Initialize session state if needed
    if "top5_by_scan" not in st.session_state:
        st.session_state["top5_by_scan"] = {}
    if "top5_union" not in st.session_state:
        st.session_state["top5_union"] = {}
    
    # Get top 5 symbols
    symbols = top_df['symbol'].head(5).tolist()
    
    # Store by scan
    st.session_state["top5_by_scan"][scan_label] = symbols
    
    # Update union - fetch data for each symbol
    for symbol in symbols:
        if symbol not in st.session_state["top5_union"]:
            # Fetch historical data
            try:
                hist_data = data_fetcher_fn(symbol)
                if not hist_data.empty and 'Close' in hist_data.columns:
                    st.session_state["top5_union"][symbol] = {
                        'hist': hist_data[['Close']],
                        'source_scans': {scan_label}
                    }
                else:
                    # Skip if no data
                    continue
            except Exception as e:
                # Skip if fetch fails
                print(f"Failed to fetch data for {symbol}: {e}")
                continue
        else:
            # Add to source scans
            st.session_state["top5_union"][symbol]['source_scans'].add(scan_label)


def render_combined_top5_plot(default_lookback: int = 60):
    """
    Render the combined Top 5 plot with radio controls
    
    Args:
        default_lookback: Number of days to show in the plot (default: 60)
    """
    st.markdown("---")
    st.markdown("### 📊 Combined Top 5 Visualization")
    
    # Check if we have data
    if "top5_by_scan" not in st.session_state or not st.session_state["top5_by_scan"]:
        st.info("No Top 5 data available. Run auto-scans to populate this visualization.")
        return
    
    # Radio control for visualization mode
    viz_mode = st.radio(
        "Visualization Mode",
        ["Union of Top 5", "Top 5 by Scan", "Hide"],
        horizontal=True,
        help="Union shows all unique symbols, By Scan shows symbols from a specific scan"
    )
    
    if viz_mode == "Hide":
        return
    
    # Determine which symbols to show
    if viz_mode == "Union of Top 5":
        # Show all symbols from union
        available_symbols = list(st.session_state["top5_union"].keys())
        selected_scan = None
    else:  # "Top 5 by Scan"
        # Let user select a scan
        scan_options = list(st.session_state["top5_by_scan"].keys())
        if not scan_options:
            st.warning("No scans available")
            return
        
        selected_scan = st.selectbox(
            "Select Scan",
            scan_options,
            help="Choose which scan's Top 5 to display"
        )
        available_symbols = st.session_state["top5_by_scan"][selected_scan]
    
    if not available_symbols:
        st.warning("No symbols available for visualization")
        return
    
    # Per-symbol checkboxes to toggle series
    st.markdown("**Select symbols to display:**")
    
    # Create columns for checkboxes (5 per row)
    cols = st.columns(5)
    selected_symbols = []
    
    for idx, symbol in enumerate(available_symbols):
        with cols[idx % 5]:
            if st.checkbox(symbol, value=True, key=f"cb_{viz_mode}_{symbol}"):
                selected_symbols.append(symbol)
    
    if not selected_symbols:
        st.info("Select at least one symbol to display")
        return
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot each selected symbol
    for symbol in selected_symbols:
        if symbol in st.session_state["top5_union"]:
            hist_data = st.session_state["top5_union"][symbol]['hist']
            
            # Get last N days
            if len(hist_data) > default_lookback:
                hist_data = hist_data.tail(default_lookback)
            
            if not hist_data.empty:
                # Normalize: divide by first value
                normalized = hist_data['Close'] / hist_data['Close'].iloc[0]
                
                # Plot
                ax.plot(normalized.index, normalized.values, label=symbol, linewidth=2)
    
    # Formatting
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Normalized Price (Starting at 1.0)', fontsize=12)
    ax.set_title(f'Normalized Price Performance - Last {default_lookback} Days', fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45, ha='right')
    
    # Tight layout to prevent label cutoff
    plt.tight_layout()
    
    # Display the plot
    st.pyplot(fig)
    
    # Show metadata
    if viz_mode == "Union of Top 5":
        st.caption(f"Showing {len(selected_symbols)} symbols from union of all scans")
    else:
        st.caption(f"Showing {len(selected_symbols)} symbols from: {selected_scan}")
