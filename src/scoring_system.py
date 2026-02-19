"""
Stock Scoring System
Calculates composite scores and probability of upward trends for stocks
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import yfinance as yf
from datetime import datetime, timedelta


class StockScorer:
    """Score stocks based on technical indicators and probability of upward trend"""
    
    def __init__(self, lookback_days: int = 60, forecast_days: int = 14):
        """
        Initialize the stock scorer
        
        Args:
            lookback_days: Number of days of historical data to analyze
            forecast_days: Number of days to forecast price movement
        """
        self.lookback_days = lookback_days
        self.forecast_days = forecast_days
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """
        Calculate Relative Strength Index (RSI)
        
        Args:
            prices: Series of closing prices
            period: RSI period (default 14 days)
            
        Returns:
            RSI value (0-100)
        """
        if len(prices) < period + 1:
            return 50.0  # Neutral value if insufficient data
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0
    
    def calculate_macd(self, prices: pd.Series) -> Tuple[float, float, float]:
        """
        Calculate MACD (Moving Average Convergence Divergence)
        
        Args:
            prices: Series of closing prices
            
        Returns:
            Tuple of (MACD, Signal, Histogram)
        """
        if len(prices) < 26:
            return 0.0, 0.0, 0.0
        
        ema_12 = prices.ewm(span=12, adjust=False).mean()
        ema_26 = prices.ewm(span=26, adjust=False).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal
        
        return (
            macd.iloc[-1] if not pd.isna(macd.iloc[-1]) else 0.0,
            signal.iloc[-1] if not pd.isna(signal.iloc[-1]) else 0.0,
            histogram.iloc[-1] if not pd.isna(histogram.iloc[-1]) else 0.0
        )
    
    def calculate_moving_averages(self, prices: pd.Series) -> Dict[str, float]:
        """
        Calculate various moving averages
        
        Args:
            prices: Series of closing prices
            
        Returns:
            Dictionary with SMA and EMA values
        """
        mas = {}
        
        # Simple Moving Averages
        for period in [20, 50]:
            if len(prices) >= period:
                ma = prices.rolling(window=period).mean().iloc[-1]
                mas[f'SMA_{period}'] = ma if not pd.isna(ma) else prices.iloc[-1]
        
        # Exponential Moving Averages
        for period in [12, 26]:
            if len(prices) >= period:
                ema = prices.ewm(span=period, adjust=False).mean().iloc[-1]
                mas[f'EMA_{period}'] = ema if not pd.isna(ema) else prices.iloc[-1]
        
        return mas
    
    def calculate_volume_trend(self, volumes: pd.Series, period: int = 20) -> float:
        """
        Calculate volume trend (relative to average)
        
        Args:
            volumes: Series of volume data
            period: Lookback period for average
            
        Returns:
            Volume ratio (current / average)
        """
        if len(volumes) < period:
            return 1.0
        
        avg_volume = volumes.rolling(window=period).mean().iloc[-1]
        current_volume = volumes.iloc[-1]
        
        if avg_volume > 0:
            return current_volume / avg_volume
        return 1.0
    
    def calculate_price_momentum(self, prices: pd.Series, period: int = 10) -> float:
        """
        Calculate price momentum (rate of change)
        
        Args:
            prices: Series of closing prices
            period: Lookback period
            
        Returns:
            Percentage change over period
        """
        if len(prices) < period:
            return 0.0
        
        old_price = prices.iloc[-period]
        current_price = prices.iloc[-1]
        
        if old_price > 0:
            return ((current_price - old_price) / old_price) * 100
        return 0.0
    
    def calculate_volatility(self, prices: pd.Series, period: int = 20) -> float:
        """
        Calculate price volatility (standard deviation of returns)
        
        Args:
            prices: Series of closing prices
            period: Lookback period
            
        Returns:
            Annualized volatility percentage
        """
        if len(prices) < period:
            return 0.0
        
        returns = prices.pct_change().dropna()
        if len(returns) < period:
            return 0.0
        
        # Calculate standard deviation of returns and annualize
        volatility = returns.tail(period).std() * np.sqrt(252) * 100
        return volatility if not pd.isna(volatility) else 0.0
    
    def calculate_price_range(self, prices: pd.Series, period: int = 20) -> float:
        """
        Calculate price range (high-low spread as percentage of price)
        
        Args:
            prices: Series of closing prices
            period: Lookback period
            
        Returns:
            Price range as percentage
        """
        if len(prices) < period:
            return 0.0
        
        recent_prices = prices.tail(period)
        high = recent_prices.max()
        low = recent_prices.min()
        
        if low > 0:
            return ((high - low) / low) * 100
        return 0.0
    
    def calculate_support_resistance(self, hist_data: pd.DataFrame, period: int = 90) -> Tuple[float, float, int]:
        """
        Calculate support and resistance levels based on historical price data
        
        Args:
            hist_data: DataFrame with historical OHLC data
            period: Lookback period for calculating levels (default 90 days)
            
        Returns:
            Tuple of (support_level, resistance_level, days_used)
            days_used indicates actual number of days used for calculation
        """
        # Minimum 30 days required for meaningful support/resistance calculation
        MIN_DAYS = 30
        
        if hist_data.empty or len(hist_data) < MIN_DAYS:
            # Insufficient data - cannot calculate meaningful levels
            return 0.0, 0.0, 0
        
        # Use available data up to 'period' days
        # If less than requested period, use what's available (min 30 days)
        actual_period = min(period, len(hist_data))
        recent_data = hist_data.tail(actual_period)
        
        # Support: minimum of low prices in period
        support = recent_data['Low'].min() if 'Low' in recent_data.columns else recent_data['Close'].min()
        
        # Resistance: maximum of high prices in period
        resistance = recent_data['High'].max() if 'High' in recent_data.columns else recent_data['Close'].max()
        
        return support, resistance, actual_period
    
    def calculate_relative_position(self, current_price: float, support: float, resistance: float) -> float:
        """
        Calculate relative position of price between support and resistance
        
        Args:
            current_price: Current stock price
            support: Support level
            resistance: Resistance level
            
        Returns:
            Relative position (0.0 to 1.0, where 0 is at support and 1 is at resistance)
        """
        if resistance <= support or support <= 0:
            return 0.5  # Neutral position if invalid levels
        
        position = (current_price - support) / (resistance - support)
        
        # Clamp to 0-1 range (though price can be outside support/resistance)
        return max(0.0, min(1.0, position))
    
    def check_breakout_filters(self, current_price: float, support: float, resistance: float,
                              volume_ratio: float, rsi: float, macd_hist: float, 
                              macd: float, macd_signal: float) -> Dict[str, bool]:
        """
        Check if stock passes momentum and breakout filters
        
        Args:
            current_price: Current stock price
            support: Support level
            resistance: Resistance level
            volume_ratio: Current volume / average volume
            rsi: RSI value
            macd_hist: MACD histogram value
            macd: MACD line value
            macd_signal: MACD signal line value
            
        Returns:
            Dictionary with filter results
        """
        filters = {}
        
        # Volume spike detection (1.5x average)
        filters['volume_spike'] = volume_ratio >= 1.5
        
        # RSI momentum (50-70 range for upward momentum)
        filters['rsi_momentum'] = 50 <= rsi <= 70
        
        # MACD momentum (histogram positive OR MACD crossing above signal)
        filters['macd_momentum'] = macd_hist > 0 or macd > macd_signal
        
        # Relative position (40%-75% of support-resistance range)
        # This ensures at least 25% distance from resistance
        relative_pos = self.calculate_relative_position(current_price, support, resistance)
        filters['position_favorable'] = 0.4 <= relative_pos <= 0.75
        
        # Overall breakout signal (all filters must pass)
        # Rationale: A true breakout requires confluence of multiple factors:
        # - Volume spike confirms genuine interest (not just price movement)
        # - RSI momentum ensures healthy upward trend without being overbought
        # - MACD momentum confirms directional strength
        # - Favorable position ensures room to run before hitting resistance
        # All four must align for a high-confidence breakout signal
        filters['breakout_signal'] = all([
            filters['volume_spike'],
            filters['rsi_momentum'],
            filters['macd_momentum'],
            filters['position_favorable']
        ])
        
        return filters
    
    def fetch_historical_data(self, symbol: str) -> pd.DataFrame:
        """
        Fetch historical OHLCV data for a symbol
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            DataFrame with historical data
        """
        try:
            ticker = yf.Ticker(symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.lookback_days + 30)  # Extra buffer
            
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty:
                return pd.DataFrame()
            
            return hist
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def score_stock(self, symbol: str, current_price: float) -> Dict:
        """
        Calculate comprehensive score for a stock
        
        Args:
            symbol: Stock ticker symbol
            current_price: Current stock price
            
        Returns:
            Dictionary with score, probability, and indicator breakdown
        """
        # Fetch historical data
        hist = self.fetch_historical_data(symbol)
        
        if hist.empty or len(hist) < 20:
            return {
                'symbol': symbol,
                'score': 0,
                'probability': 0,
                'indicators': {},
                'error': 'Insufficient data'
            }
        
        prices = hist['Close']
        volumes = hist['Volume']
        
        # Calculate indicators
        rsi = self.calculate_rsi(prices)
        macd, macd_signal, macd_hist = self.calculate_macd(prices)
        mas = self.calculate_moving_averages(prices)
        volume_ratio = self.calculate_volume_trend(volumes)
        momentum = self.calculate_price_momentum(prices)
        volatility = self.calculate_volatility(prices)
        price_range = self.calculate_price_range(prices)
        
        # Calculate support and resistance levels
        support, resistance, data_quality_days = self.calculate_support_resistance(hist)
        relative_position = self.calculate_relative_position(current_price, support, resistance)
        
        # Check breakout filters
        breakout_filters = self.check_breakout_filters(
            current_price, support, resistance, volume_ratio,
            rsi, macd_hist, macd, macd_signal
        )
        
        # Calculate individual scores (0-100 scale)
        scores = {}
        
        # RSI Score (oversold = bullish, overbought = bearish)
        # Optimal range: 30-70, with 40-60 being most bullish for swing trading
        if rsi < 30:
            scores['rsi'] = 85  # Very oversold - high potential
        elif rsi < 40:
            scores['rsi'] = 95  # Oversold - optimal entry
        elif rsi < 50:
            scores['rsi'] = 75  # Slightly oversold - good
        elif rsi < 60:
            scores['rsi'] = 60  # Neutral to slightly bullish
        elif rsi < 70:
            scores['rsi'] = 40  # Getting overbought
        else:
            scores['rsi'] = 20  # Overbought - risky
        
        # MACD Score (positive histogram and rising = bullish)
        if macd_hist > 0 and macd > macd_signal:
            scores['macd'] = 80 + min(20, abs(macd_hist) * 10)  # 80-100
        elif macd_hist > 0:
            scores['macd'] = 60
        elif macd > macd_signal:
            scores['macd'] = 55
        else:
            scores['macd'] = 30
        
        # Moving Average Score (price above MAs = bullish)
        ma_score = 0
        ma_count = 0
        for ma_name, ma_value in mas.items():
            if current_price > ma_value:
                ma_score += 100
            ma_count += 1
        scores['moving_avg'] = ma_score / ma_count if ma_count > 0 else 50
        
        # Volume Score (higher than average = bullish)
        if volume_ratio > 1.5:
            scores['volume'] = 90
        elif volume_ratio > 1.2:
            scores['volume'] = 75
        elif volume_ratio > 1.0:
            scores['volume'] = 60
        elif volume_ratio > 0.8:
            scores['volume'] = 45
        else:
            scores['volume'] = 30
        
        # Momentum Score (positive momentum = bullish, penalize negative)
        # For flat ranges, we're more lenient on negative momentum since
        # consolidating stocks may have slight negative momentum before breakout
        if momentum > 5:
            scores['momentum'] = 100
        elif momentum > 2:
            scores['momentum'] = 80
        elif momentum > 0:
            scores['momentum'] = 60
        elif momentum > -2:
            # Flat to slightly negative - not as bad for consolidating stocks
            scores['momentum'] = 40
        else:
            # Highly negative momentum - reduced penalty (was 0, now 10)
            # to avoid completely excluding stocks in tight consolidation patterns
            scores['momentum'] = 10
        
        # Calculate composite score (weighted average)
        weights = {
            'rsi': 0.25,
            'macd': 0.25,
            'moving_avg': 0.20,
            'volume': 0.15,
            'momentum': 0.15
        }
        
        composite_score = sum(scores[k] * weights[k] for k in scores.keys())
        
        # Flat Range Bonus: Identify stocks with low volatility and tight ranges
        # that are oversold (RSI < 50) - these are ideal consolidation patterns
        # like NEE and PFE that could break out
        # Thresholds: volatility < 30% (annualized), price_range < 15% of price
        is_flat_range = (volatility < 30 and price_range < 15)  # Low volatility and tight range
        is_oversold = rsi < 50
        
        if is_flat_range and is_oversold:
            # Apply bonus for flat consolidating stocks that are oversold
            # Tighter the range, higher the bonus (max 10 points)
            range_tightness = max(0, 15 - price_range)  # 0-15 scale
            flat_range_bonus = min(10, range_tightness * 0.67)  # Up to 10 points
            composite_score = min(100, composite_score + flat_range_bonus)
        
        # Calculate probability of upward trend (sigmoid-like function)
        # Score ranges: 0-100, probability ranges: 0-100%
        probability = min(100, max(0, composite_score))
        
        # Prepare indicator breakdown
        indicators = {
            'RSI': round(rsi, 2),
            'MACD': round(macd, 4),
            'MACD_Signal': round(macd_signal, 4),
            'MACD_Histogram': round(macd_hist, 4),
            'Volume_Ratio': round(volume_ratio, 2),
            'Momentum_10d': round(momentum, 2),
            'Volatility': round(volatility, 2),
            'Price_Range_20d': round(price_range, 2),
            'Support_90d': round(support, 2),
            'Resistance_90d': round(resistance, 2),
            'Relative_Position': round(relative_position, 3),
            **{k: round(v, 2) for k, v in mas.items()}
        }
        
        # Add score contributions
        score_contributions = {
            f'{k}_score': round(v, 1) for k, v in scores.items()
        }
        
        return {
            'symbol': symbol,
            'score': round(composite_score, 2),
            'probability': round(probability, 1),
            'indicators': indicators,
            'score_contributions': score_contributions,
            'raw_scores': scores,
            'breakout_filters': breakout_filters,
            'support_resistance': {
                'support': round(support, 2),
                'resistance': round(resistance, 2),
                'relative_position': round(relative_position, 3),
                'data_quality_days': data_quality_days
            }
        }
    
    def rank_stocks(self, stocks_df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
        """
        Score and rank stocks, returning top N
        
        Args:
            stocks_df: DataFrame with stock data (must have 'symbol' and 'price' columns)
            top_n: Number of top stocks to return
            
        Returns:
            DataFrame with top N stocks and their scores
        """
        results = []
        
        for _, row in stocks_df.iterrows():
            symbol = row['symbol']
            price = row.get('price', row.get('close', 0))
            
            score_data = self.score_stock(symbol, price)
            
            # Merge original data with score data
            result = row.to_dict()
            result.update(score_data)
            results.append(result)
        
        # Create DataFrame
        results_df = pd.DataFrame(results)
        
        # Sort by score (descending) and return top N
        if 'score' in results_df.columns:
            results_df = results_df.sort_values('score', ascending=False).head(top_n)
        
        return results_df
