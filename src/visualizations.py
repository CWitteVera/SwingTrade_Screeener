"""
Visualization Module
Creates charts for price predictions and indicator analysis
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional
import io
import base64


try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class StockVisualizer:
    """Create visualizations for stock analysis"""
    
    def __init__(self):
        """Initialize visualizer"""
        self.has_matplotlib = HAS_MATPLOTLIB
    
    def create_price_range_chart(self, symbol: str, prediction: Dict, 
                                 hist_data: Optional[pd.DataFrame] = None) -> Optional[str]:
        """
        Create a chart showing predicted price range
        
        Args:
            symbol: Stock ticker symbol
            prediction: Price prediction dictionary
            hist_data: Optional historical data to show recent price history
            
        Returns:
            Base64-encoded PNG image or None if matplotlib not available
        """
        if not self.has_matplotlib:
            return None
        
        fig, ax = plt.subplots(figsize=(6, 3))
        
        current_price = prediction.get('current_price', 0)
        predicted_price = prediction.get('predicted_price', current_price)
        forecast_days = prediction.get('forecast_days', 14)
        
        # If we have historical data, plot it
        if hist_data is not None and not hist_data.empty and len(hist_data) > 5:
            # Show last 30 days of history
            recent_hist = hist_data.tail(30).copy()
            recent_hist['day'] = list(range(-len(recent_hist), 0))
            ax.plot(recent_hist['day'], recent_hist['Close'], 
                   color='#2E86AB', linewidth=1.5, label='Historical Price')
            
            # Mark current price
            ax.scatter([0], [current_price], color='#2E86AB', s=50, zorder=5)
        else:
            # Just show current price as a point
            ax.scatter([0], [current_price], color='#2E86AB', s=50, zorder=5, label='Current Price')
        
        # Forecast visualization
        forecast_x = [0, forecast_days]
        
        # Predicted price line
        ax.plot(forecast_x, [current_price, predicted_price], 
               color='#A23B72', linewidth=2, linestyle='--', label='Prediction')
        
        # Confidence bands (80%)
        conf_low = prediction.get('confidence_80_low', current_price * 0.97)
        conf_high = prediction.get('confidence_80_high', current_price * 1.03)
        
        ax.fill_between(forecast_x, 
                       [current_price, conf_low],
                       [current_price, conf_high],
                       alpha=0.3, color='#A23B72', label='80% Confidence')
        
        # Wide range (95%)
        price_low = prediction.get('price_low', current_price * 0.95)
        price_high = prediction.get('price_high', current_price * 1.05)
        
        ax.fill_between(forecast_x,
                       [current_price, price_low],
                       [current_price, price_high],
                       alpha=0.15, color='#A23B72', label='95% Range')
        
        # Formatting
        ax.set_xlabel('Days', fontsize=9)
        ax.set_ylabel('Price ($)', fontsize=9)
        ax.set_title(f'{symbol} - {forecast_days} Day Price Forecast', fontsize=10, fontweight='bold')
        ax.legend(loc='best', fontsize=7)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.tick_params(labelsize=8)
        
        # Add price annotations
        ax.annotate(f'${predicted_price:.2f}', 
                   xy=(forecast_days, predicted_price), 
                   xytext=(5, 5), textcoords='offset points',
                   fontsize=8, color='#A23B72', fontweight='bold')
        
        plt.tight_layout()
        
        # Convert to base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        
        return f"data:image/png;base64,{img_base64}"
    
    def create_indicator_breakdown_chart(self, symbol: str, score_data: Dict) -> Optional[str]:
        """
        Create a horizontal bar chart showing indicator contributions to score
        
        Args:
            symbol: Stock ticker symbol
            score_data: Score data dictionary with score_contributions
            
        Returns:
            Base64-encoded PNG image or None if matplotlib not available
        """
        if not self.has_matplotlib:
            return None
        
        score_contributions = score_data.get('score_contributions', {})
        
        if not score_contributions:
            return None
        
        # Prepare data for plotting
        labels = []
        values = []
        for key, value in score_contributions.items():
            # Clean up label names
            label = key.replace('_score', '').replace('_', ' ').title()
            labels.append(label)
            values.append(value)
        
        # Create horizontal bar chart
        fig, ax = plt.subplots(figsize=(5, 3))
        
        # Color bars based on value (green for high, red for low)
        colors = []
        for v in values:
            if v >= 75:
                colors.append('#06A77D')  # Green
            elif v >= 50:
                colors.append('#F5B700')  # Yellow
            else:
                colors.append('#D62839')  # Red
        
        y_pos = np.arange(len(labels))
        ax.barh(y_pos, values, color=colors, alpha=0.8)
        
        # Formatting
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=8)
        ax.set_xlabel('Score (0-100)', fontsize=9)
        ax.set_xlim(0, 100)
        ax.set_title(f'{symbol} - Indicator Scores', fontsize=10, fontweight='bold')
        ax.grid(True, axis='x', alpha=0.3, linestyle='--')
        ax.tick_params(labelsize=8)
        
        # Add value labels on bars
        for i, v in enumerate(values):
            ax.text(v + 2, i, f'{v:.1f}', va='center', fontsize=8, fontweight='bold')
        
        plt.tight_layout()
        
        # Convert to base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        
        return f"data:image/png;base64,{img_base64}"
    
    def create_combined_chart(self, symbol: str, score_data: Dict, 
                             prediction: Dict, hist_data: Optional[pd.DataFrame] = None) -> Optional[str]:
        """
        Create a combined chart with price forecast and indicator breakdown
        
        Args:
            symbol: Stock ticker symbol
            score_data: Score data dictionary
            prediction: Price prediction dictionary
            hist_data: Optional historical data
            
        Returns:
            Base64-encoded PNG image or None if matplotlib not available
        """
        if not self.has_matplotlib:
            return None
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3.5))
        
        # Left plot: Price forecast
        current_price = prediction.get('current_price', 0)
        predicted_price = prediction.get('predicted_price', current_price)
        forecast_days = prediction.get('forecast_days', 14)
        
        # If we have historical data, plot it
        if hist_data is not None and not hist_data.empty and len(hist_data) > 5:
            recent_hist = hist_data.tail(90).copy()  # Use 90 days for resistance and support bands
            recent_hist['day'] = list(range(-len(recent_hist), 0))
            
            # Calculate 90-day resistance and support levels
            resistance_90d = recent_hist['High'].max()
            support_90d = recent_hist['Low'].min()
            
            # Plot historical price with last 30 days visible
            display_hist = recent_hist.tail(30).copy()
            display_hist['day'] = list(range(-len(display_hist), 0))
            ax1.plot(display_hist['day'], display_hist['Close'], 
                    color='#2E86AB', linewidth=1.5, label='Historical')
            ax1.scatter([0], [current_price], color='#2E86AB', s=50, zorder=5)
            
            # Plot 90-day resistance and support bands
            ax1.axhline(y=resistance_90d, color='#D62839', linestyle='--', 
                       linewidth=1.5, alpha=0.7, label=f'90d Resistance (${resistance_90d:.2f})')
            ax1.axhline(y=support_90d, color='#06A77D', linestyle='--', 
                       linewidth=1.5, alpha=0.7, label=f'90d Support (${support_90d:.2f})')
        else:
            ax1.scatter([0], [current_price], color='#2E86AB', s=50, zorder=5, label='Current')
        
        # Forecast
        forecast_x = [0, forecast_days]
        ax1.plot(forecast_x, [current_price, predicted_price], 
                color='#A23B72', linewidth=2, linestyle='--', label='Forecast')
        
        # Confidence bands
        conf_low = prediction.get('confidence_80_low', current_price * 0.97)
        conf_high = prediction.get('confidence_80_high', current_price * 1.03)
        ax1.fill_between(forecast_x, [current_price, conf_low], [current_price, conf_high],
                        alpha=0.3, color='#A23B72', label='80% Conf.')
        
        ax1.set_xlabel('Days', fontsize=9)
        ax1.set_ylabel('Price ($)', fontsize=9)
        ax1.set_title(f'Price Forecast ({forecast_days} Days)', fontsize=10, fontweight='bold')
        ax1.legend(loc='best', fontsize=6)  # Reduced font size to fit more items
        ax1.grid(True, alpha=0.3, linestyle='--')
        ax1.tick_params(labelsize=8)
        
        # Right plot: Indicator breakdown
        score_contributions = score_data.get('score_contributions', {})
        
        if score_contributions:
            labels = []
            values = []
            for key, value in score_contributions.items():
                label = key.replace('_score', '').replace('_', ' ').title()
                labels.append(label)
                values.append(value)
            
            colors = []
            for v in values:
                if v >= 75:
                    colors.append('#06A77D')
                elif v >= 50:
                    colors.append('#F5B700')
                else:
                    colors.append('#D62839')
            
            y_pos = np.arange(len(labels))
            ax2.barh(y_pos, values, color=colors, alpha=0.8)
            ax2.set_yticks(y_pos)
            ax2.set_yticklabels(labels, fontsize=8)
            ax2.set_xlabel('Score (0-100)', fontsize=9)
            ax2.set_xlim(0, 100)
            ax2.set_title('Indicator Scores', fontsize=10, fontweight='bold')
            ax2.grid(True, axis='x', alpha=0.3, linestyle='--')
            ax2.tick_params(labelsize=8)
            
            for i, v in enumerate(values):
                ax2.text(v + 2, i, f'{v:.1f}', va='center', fontsize=7, fontweight='bold')
        
        plt.tight_layout()
        
        # Convert to base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        
        return f"data:image/png;base64,{img_base64}"
    
    def create_technical_analysis_chart(self, symbol: str, score_data: Dict, 
                                       hist_data: Optional[pd.DataFrame] = None) -> Optional[str]:
        """
        Create a comprehensive technical analysis chart with price, volume, RSI, and MACD
        
        Args:
            symbol: Stock ticker symbol
            score_data: Score data dictionary with indicators
            hist_data: Historical OHLCV data
            
        Returns:
            Base64-encoded PNG image or None if matplotlib not available
        """
        if not self.has_matplotlib or hist_data is None or hist_data.empty:
            return None
        
        # Create figure with 4 subplots (price, volume, RSI, MACD)
        fig = plt.figure(figsize=(12, 10))
        gs = fig.add_gridspec(4, 1, height_ratios=[3, 1, 1, 1], hspace=0.3)
        
        ax_price = fig.add_subplot(gs[0])
        ax_volume = fig.add_subplot(gs[1], sharex=ax_price)
        ax_rsi = fig.add_subplot(gs[2], sharex=ax_price)
        ax_macd = fig.add_subplot(gs[3], sharex=ax_price)
        
        # Prepare data (use last 60 days for visibility)
        plot_data = hist_data.tail(60).copy()
        plot_data['day'] = range(len(plot_data))
        
        # Get support/resistance from score_data
        support_resistance = score_data.get('support_resistance', {})
        support = support_resistance.get('support', 0)
        resistance = support_resistance.get('resistance', 0)
        current_price = plot_data['Close'].iloc[-1] if not plot_data.empty else 0
        
        # --- Price Chart with Support/Resistance ---
        ax_price.plot(plot_data['day'], plot_data['Close'], 
                     color='#2E86AB', linewidth=2, label='Price')
        
        # Add support and resistance lines
        if support > 0:
            ax_price.axhline(y=support, color='#06A77D', linestyle='--', 
                           linewidth=2, alpha=0.7, label=f'Support: ${support:.2f}')
        if resistance > 0:
            ax_price.axhline(y=resistance, color='#D62839', linestyle='--', 
                           linewidth=2, alpha=0.7, label=f'Resistance: ${resistance:.2f}')
        
        # Highlight current price
        ax_price.scatter([plot_data['day'].iloc[-1]], [current_price], 
                        color='#A23B72', s=100, zorder=5, label=f'Current: ${current_price:.2f}')
        
        ax_price.set_ylabel('Price ($)', fontsize=10, fontweight='bold')
        ax_price.set_title(f'{symbol} - Technical Analysis', fontsize=12, fontweight='bold')
        ax_price.legend(loc='upper left', fontsize=9)
        ax_price.grid(True, alpha=0.3, linestyle='--')
        ax_price.tick_params(labelsize=9)
        
        # --- Volume Chart with Spike Highlighting ---
        # Calculate average volume
        avg_volume = plot_data['Volume'].mean()
        volume_colors = ['#D62839' if v >= avg_volume * 1.5 else '#2E86AB' 
                        for v in plot_data['Volume']]
        
        ax_volume.bar(plot_data['day'], plot_data['Volume'], 
                     color=volume_colors, alpha=0.7, width=0.8)
        ax_volume.axhline(y=avg_volume * 1.5, color='#D62839', linestyle='--', 
                         linewidth=1.5, alpha=0.5, label='1.5x Avg Volume')
        
        ax_volume.set_ylabel('Volume', fontsize=10, fontweight='bold')
        ax_volume.legend(loc='upper left', fontsize=8)
        ax_volume.grid(True, alpha=0.3, linestyle='--', axis='y')
        ax_volume.tick_params(labelsize=9)
        ax_volume.ticklabel_format(style='plain', axis='y')
        
        # --- RSI Chart ---
        # Calculate RSI for the plot data
        from scoring_system import StockScorer
        scorer = StockScorer()
        
        # Calculate RSI for each point
        rsi_values = []
        for i in range(len(plot_data)):
            if i < 14:
                rsi_values.append(50)  # Neutral for insufficient data
            else:
                prices_slice = plot_data['Close'].iloc[:i+1]
                rsi_val = scorer.calculate_rsi(prices_slice, period=14)
                rsi_values.append(rsi_val)
        
        plot_data['RSI'] = rsi_values
        
        ax_rsi.plot(plot_data['day'], plot_data['RSI'], 
                   color='#A23B72', linewidth=2, label='RSI')
        
        # Add overbought/oversold zones
        ax_rsi.axhline(y=70, color='#D62839', linestyle='--', linewidth=1, alpha=0.5)
        ax_rsi.axhline(y=30, color='#06A77D', linestyle='--', linewidth=1, alpha=0.5)
        ax_rsi.fill_between(plot_data['day'], 70, 100, alpha=0.1, color='#D62839', label='Overbought')
        ax_rsi.fill_between(plot_data['day'], 0, 30, alpha=0.1, color='#06A77D', label='Oversold')
        ax_rsi.fill_between(plot_data['day'], 50, 70, alpha=0.05, color='#F5B700', label='Momentum Zone')
        
        ax_rsi.set_ylabel('RSI', fontsize=10, fontweight='bold')
        ax_rsi.set_ylim(0, 100)
        ax_rsi.legend(loc='upper left', fontsize=8)
        ax_rsi.grid(True, alpha=0.3, linestyle='--')
        ax_rsi.tick_params(labelsize=9)
        
        # --- MACD Chart ---
        # Calculate MACD for each point
        macd_values = []
        signal_values = []
        histogram_values = []
        
        for i in range(len(plot_data)):
            if i < 26:
                macd_values.append(0)
                signal_values.append(0)
                histogram_values.append(0)
            else:
                prices_slice = plot_data['Close'].iloc[:i+1]
                macd, signal, hist = scorer.calculate_macd(prices_slice)
                macd_values.append(macd)
                signal_values.append(signal)
                histogram_values.append(hist)
        
        plot_data['MACD'] = macd_values
        plot_data['MACD_Signal'] = signal_values
        plot_data['MACD_Hist'] = histogram_values
        
        # Plot MACD histogram
        hist_colors = ['#06A77D' if h > 0 else '#D62839' for h in plot_data['MACD_Hist']]
        ax_macd.bar(plot_data['day'], plot_data['MACD_Hist'], 
                   color=hist_colors, alpha=0.5, width=0.8, label='MACD Histogram')
        
        # Plot MACD and Signal lines
        ax_macd.plot(plot_data['day'], plot_data['MACD'], 
                    color='#2E86AB', linewidth=1.5, label='MACD Line')
        ax_macd.plot(plot_data['day'], plot_data['MACD_Signal'], 
                    color='#A23B72', linewidth=1.5, label='Signal Line')
        ax_macd.axhline(y=0, color='black', linestyle='-', linewidth=0.5, alpha=0.5)
        
        ax_macd.set_ylabel('MACD', fontsize=10, fontweight='bold')
        ax_macd.set_xlabel('Days', fontsize=10, fontweight='bold')
        ax_macd.legend(loc='upper left', fontsize=8)
        ax_macd.grid(True, alpha=0.3, linestyle='--')
        ax_macd.tick_params(labelsize=9)
        
        plt.tight_layout()
        
        # Convert to base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        
        return f"data:image/png;base64,{img_base64}"
