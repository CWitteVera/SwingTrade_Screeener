"""
Price Prediction Module
Estimates future price ranges based on historical volatility and trends
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple
from datetime import datetime, timedelta


class PricePredictor:
    """Predict future price ranges for stocks"""
    
    def __init__(self, forecast_days: int = 14):
        """
        Initialize price predictor
        
        Args:
            forecast_days: Number of days to forecast
        """
        self.forecast_days = forecast_days
    
    def calculate_historical_volatility(self, prices: pd.Series, period: int = 30) -> float:
        """
        Calculate historical volatility (annualized standard deviation of returns)
        
        Args:
            prices: Series of closing prices
            period: Lookback period for volatility calculation
            
        Returns:
            Annualized volatility as a percentage
        """
        if len(prices) < period:
            return 0.20  # Default 20% volatility
        
        # Calculate daily returns
        returns = prices.pct_change().dropna()
        
        # Calculate standard deviation of returns
        volatility = returns.std()
        
        # Annualize (assuming 252 trading days per year)
        annualized_vol = volatility * np.sqrt(252)
        
        return annualized_vol
    
    def calculate_trend(self, prices: pd.Series, period: int = 20) -> float:
        """
        Calculate trend using linear regression
        
        Args:
            prices: Series of closing prices
            period: Lookback period
            
        Returns:
            Daily trend (slope of linear regression)
        """
        if len(prices) < period:
            return 0.0
        
        # Use last N days
        recent_prices = prices.tail(period)
        
        # Simple linear regression
        x = np.arange(len(recent_prices))
        y = recent_prices.values
        
        # Calculate slope
        slope = np.polyfit(x, y, 1)[0]
        
        return slope
    
    def predict_price_range(self, symbol: str, current_price: float, 
                           hist_data: pd.DataFrame) -> Dict:
        """
        Predict future price range for a stock
        
        Args:
            symbol: Stock ticker symbol
            current_price: Current stock price
            hist_data: Historical OHLCV data
            
        Returns:
            Dictionary with price predictions and confidence intervals
        """
        if hist_data.empty or len(hist_data) < 20:
            # Insufficient data - use conservative estimates
            return {
                'symbol': symbol,
                'current_price': current_price,
                'forecast_days': self.forecast_days,
                'predicted_price': current_price,
                'price_low': current_price * 0.95,
                'price_high': current_price * 1.05,
                'confidence_80_low': current_price * 0.97,
                'confidence_80_high': current_price * 1.03,
                'volatility': 0.20,
                'trend_strength': 0,
                'error': 'Insufficient data for prediction'
            }
        
        prices = hist_data['Close']
        
        # Calculate volatility
        volatility = self.calculate_historical_volatility(prices)
        
        # Calculate trend
        trend_slope = self.calculate_trend(prices)
        
        # Project trend forward
        trend_projection = trend_slope * self.forecast_days
        
        # Predicted price (current + trend projection)
        predicted_price = current_price + trend_projection
        
        # Calculate price range based on volatility
        # Daily volatility
        daily_vol = volatility / np.sqrt(252)
        
        # Volatility over forecast period
        forecast_vol = daily_vol * np.sqrt(self.forecast_days)
        
        # 95% confidence interval (±2 standard deviations)
        price_low = predicted_price * (1 - 2 * forecast_vol)
        price_high = predicted_price * (1 + 2 * forecast_vol)
        
        # 80% confidence interval (±1.28 standard deviations)
        confidence_80_low = predicted_price * (1 - 1.28 * forecast_vol)
        confidence_80_high = predicted_price * (1 + 1.28 * forecast_vol)
        
        # Calculate trend strength (-100 to +100)
        # Positive = upward trend, negative = downward trend
        trend_pct = (trend_projection / current_price) * 100 if current_price > 0 else 0
        trend_strength = max(-100, min(100, trend_pct * 10))  # Scale and cap
        
        return {
            'symbol': symbol,
            'current_price': round(current_price, 2),
            'forecast_days': self.forecast_days,
            'predicted_price': round(predicted_price, 2),
            'price_low': round(max(0, price_low), 2),  # Can't be negative
            'price_high': round(price_high, 2),
            'confidence_80_low': round(max(0, confidence_80_low), 2),
            'confidence_80_high': round(confidence_80_high, 2),
            'volatility': round(volatility * 100, 2),  # As percentage
            'trend_strength': round(trend_strength, 1),
            'daily_trend': round(trend_slope, 4)
        }
    
    def get_price_targets(self, current_price: float, prediction: Dict) -> Dict[str, float]:
        """
        Calculate price targets based on prediction
        
        Args:
            current_price: Current stock price
            prediction: Price prediction dictionary
            
        Returns:
            Dictionary with price targets
        """
        predicted = prediction.get('predicted_price', current_price)
        
        # Conservative target (80% confidence low)
        conservative_target = prediction.get('confidence_80_low', current_price * 0.97)
        
        # Expected target (predicted price)
        expected_target = predicted
        
        # Optimistic target (80% confidence high)
        optimistic_target = prediction.get('confidence_80_high', current_price * 1.03)
        
        # Potential gain/loss percentages
        conservative_gain = ((conservative_target - current_price) / current_price * 100) if current_price > 0 else 0
        expected_gain = ((expected_target - current_price) / current_price * 100) if current_price > 0 else 0
        optimistic_gain = ((optimistic_target - current_price) / current_price * 100) if current_price > 0 else 0
        
        return {
            'conservative_target': round(conservative_target, 2),
            'expected_target': round(expected_target, 2),
            'optimistic_target': round(optimistic_target, 2),
            'conservative_gain_pct': round(conservative_gain, 2),
            'expected_gain_pct': round(expected_gain, 2),
            'optimistic_gain_pct': round(optimistic_gain, 2)
        }
