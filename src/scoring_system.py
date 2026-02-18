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
        if momentum > 5:
            scores['momentum'] = 100
        elif momentum > 2:
            scores['momentum'] = 80
        elif momentum > 0:
            scores['momentum'] = 60
        elif momentum > -2:
            scores['momentum'] = 30
        else:
            scores['momentum'] = 0
        
        # Calculate composite score (weighted average)
        weights = {
            'rsi': 0.25,
            'macd': 0.25,
            'moving_avg': 0.20,
            'volume': 0.15,
            'momentum': 0.15
        }
        
        composite_score = sum(scores[k] * weights[k] for k in scores.keys())
        
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
            'raw_scores': scores
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
