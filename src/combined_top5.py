"""
Combined Top 5 Aggregator and Visualization
Aggregates Top 5 symbols from all auto-run scans and provides visualization
"""
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import yfinance as yf
from typing import Callable, Dict, List, Optional

# Constants
SUPPORT_RESISTANCE_DAYS = 90


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
                # Skip if fetch fails - silently ignore
                continue
        else:
            # Add to source scans
            st.session_state["top5_union"][symbol]['source_scans'].add(scan_label)


def render_combined_top5_plot(default_lookback: int = 60):
    """
    Render the combined Top 5 plot with radio controls and enhanced indicators
    
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
    
    # Chart type selector
    chart_type = st.radio(
        "Chart Type",
        ["Price Performance", "Individual Stock Analysis"],
        horizontal=True,
        help="Choose between normalized price comparison or detailed individual stock analysis"
    )
    
    if chart_type == "Price Performance":
        # Original normalized price chart
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
    
    else:  # Individual Stock Analysis
        # Show detailed analysis for each selected symbol
        
        for symbol in selected_symbols:
            if symbol not in st.session_state["top5_union"]:
                continue
            
            st.markdown(f"#### {symbol} - Technical Analysis")
            
            try:
                # Fetch full historical data for indicators
                # Note: We fetch 120 days which is sufficient for SUPPORT_RESISTANCE_DAYS (90) calculation
                ticker = yf.Ticker(symbol)
                hist_full = ticker.history(period="120d")
                
                if hist_full.empty or len(hist_full) < 20:
                    st.warning(f"Insufficient data for {symbol}")
                    continue
                
                # Get last N days for display
                hist_data = hist_full.tail(default_lookback)
                
                # Calculate indicators
                # Moving averages
                hist_full['SMA_20'] = hist_full['Close'].rolling(window=20).mean()
                hist_full['SMA_50'] = hist_full['Close'].rolling(window=50).mean()
                
                # RSI
                delta = hist_full['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                hist_full['RSI'] = 100 - (100 / (1 + rs))
                
                # MACD
                exp1 = hist_full['Close'].ewm(span=12, adjust=False).mean()
                exp2 = hist_full['Close'].ewm(span=26, adjust=False).mean()
                hist_full['MACD'] = exp1 - exp2
                hist_full['Signal'] = hist_full['MACD'].ewm(span=9, adjust=False).mean()
                
                # Get display data
                hist_display = hist_full.tail(default_lookback)
                
                # Create subplots
                fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True, 
                                                     gridspec_kw={'height_ratios': [3, 1, 1]})
                
                # Price chart with moving averages and support/resistance
                ax1.plot(hist_display.index, hist_display['Close'], label='Close Price', linewidth=2, color='#2E86AB')
                ax1.plot(hist_display.index, hist_display['SMA_20'], label='SMA 20', linewidth=1.5, 
                        linestyle='--', alpha=0.7, color='#F5B700')
                ax1.plot(hist_display.index, hist_display['SMA_50'], label='SMA 50', linewidth=1.5, 
                        linestyle='--', alpha=0.7, color='#D62839')
                
                # Add support and resistance levels
                resistance = hist_full.tail(SUPPORT_RESISTANCE_DAYS)['High'].max()
                support = hist_full.tail(SUPPORT_RESISTANCE_DAYS)['Low'].min()
                ax1.axhline(y=resistance, color='#D62839', linestyle=':', linewidth=1.5, 
                           alpha=0.5, label=f'{SUPPORT_RESISTANCE_DAYS}d Resistance (${resistance:.2f})')
                ax1.axhline(y=support, color='#06A77D', linestyle=':', linewidth=1.5, 
                           alpha=0.5, label=f'{SUPPORT_RESISTANCE_DAYS}d Support (${support:.2f})')
                
                ax1.set_ylabel('Price ($)', fontsize=10)
                ax1.set_title(f'{symbol} - Price with Support/Resistance & Moving Averages', 
                             fontsize=12, fontweight='bold')
                ax1.legend(loc='best', fontsize=8)
                ax1.grid(True, alpha=0.3)
                
                # RSI
                ax2.plot(hist_display.index, hist_display['RSI'], label='RSI', linewidth=2, color='#A23B72')
                ax2.axhline(y=70, color='#D62839', linestyle='--', linewidth=1, alpha=0.5, label='Overbought (70)')
                ax2.axhline(y=30, color='#06A77D', linestyle='--', linewidth=1, alpha=0.5, label='Oversold (30)')
                ax2.set_ylabel('RSI', fontsize=10)
                ax2.set_ylim(0, 100)
                ax2.legend(loc='best', fontsize=8)
                ax2.grid(True, alpha=0.3)
                
                # MACD
                ax3.plot(hist_display.index, hist_display['MACD'], label='MACD', linewidth=2, color='#2E86AB')
                ax3.plot(hist_display.index, hist_display['Signal'], label='Signal', linewidth=1.5, 
                        linestyle='--', alpha=0.7, color='#F5B700')
                ax3.axhline(y=0, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
                ax3.bar(hist_display.index, hist_display['MACD'] - hist_display['Signal'], 
                       label='Histogram', alpha=0.3, color='#06A77D')
                ax3.set_xlabel('Date', fontsize=10)
                ax3.set_ylabel('MACD', fontsize=10)
                ax3.legend(loc='best', fontsize=8)
                ax3.grid(True, alpha=0.3)
                
                # Rotate x-axis labels
                plt.xticks(rotation=45, ha='right')
                
                # Tight layout
                plt.tight_layout()
                
                # Display the plot
                st.pyplot(fig)
                
                # Show current indicator values
                col1, col2, col3, col4, col5 = st.columns(5)
                
                current_price = hist_full['Close'].iloc[-1]
                current_rsi = hist_full['RSI'].iloc[-1]
                current_macd = hist_full['MACD'].iloc[-1]
                current_signal = hist_full['Signal'].iloc[-1]
                
                with col1:
                    st.metric("Current Price", f"${current_price:.2f}")
                with col2:
                    rsi_status = "Overbought" if current_rsi > 70 else ("Oversold" if current_rsi < 30 else "Neutral")
                    st.metric("RSI", f"{current_rsi:.1f}", help=rsi_status)
                with col3:
                    macd_signal = "Bullish" if current_macd > current_signal else "Bearish"
                    st.metric("MACD Signal", macd_signal)
                with col4:
                    distance_to_resistance = ((resistance - current_price) / current_price * 100)
                    st.metric("To Resistance", f"{distance_to_resistance:.1f}%")
                with col5:
                    distance_to_support = ((current_price - support) / current_price * 100)
                    st.metric("Above Support", f"{distance_to_support:.1f}%")
                
                st.markdown("---")
                
            except Exception as e:
                st.error(f"Error analyzing {symbol}: {str(e)}")
