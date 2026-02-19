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
    
    def calculate_atr(self, hist_data: pd.DataFrame, period: int = 14) -> float:
        """
        Calculate Average True Range (ATR)

        Args:
            hist_data: DataFrame with OHLC data (must have 'High', 'Low', 'Close' columns)
            period: ATR period (default: 14)

        Returns:
            ATR value or 0.0 if insufficient data
        """
        if not {'High', 'Low', 'Close'}.issubset(hist_data.columns) or len(hist_data) < period + 1:
            return 0.0

        high_low = hist_data['High'] - hist_data['Low']
        high_close = np.abs(hist_data['High'] - hist_data['Close'].shift(1))
        low_close = np.abs(hist_data['Low'] - hist_data['Close'].shift(1))

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean().iloc[-1]

        return atr if not pd.isna(atr) else 0.0

    def detect_market_regime(self, current_price: float, sma20: float, sma50: float) -> str:
        """
        Detect market regime based on price and moving averages

        Args:
            current_price: Current stock price
            sma20: 20-day simple moving average
            sma50: 50-day simple moving average

        Returns:
            Regime string: 'uptrend', 'downtrend', or 'range'
        """
        if sma20 <= 0 or sma50 <= 0:
            return 'range'

        if current_price > sma50 and sma20 > sma50:
            return 'uptrend'
        elif current_price < sma50 and sma20 < sma50:
            return 'downtrend'
        else:
            return 'range'

    def _calculate_trend_score(self, current_price: float, mas: Dict,
                               macd: float, macd_signal: float, momentum: float) -> float:
        """
        Calculate trend strength score (0-100)

        Inputs: price vs SMA50, SMA20 vs SMA50, MACD direction, momentum

        Args:
            current_price: Current stock price
            mas: Dictionary of moving averages (keys: 'SMA_20', 'SMA_50', etc.)
            macd: MACD line value
            macd_signal: MACD signal line value
            momentum: 10-day price momentum percentage

        Returns:
            Trend score 0-100
        """
        score = 0.0

        sma20 = mas.get('SMA_20', 0)
        sma50 = mas.get('SMA_50', 0)

        # Price vs SMA20 (20 points)
        if sma20 > 0:
            score += 20 if current_price > sma20 else 0

        # Price vs SMA50 (20 points)
        if sma50 > 0:
            score += 20 if current_price > sma50 else 0

        # SMA20 vs SMA50 alignment (20 points)
        if sma20 > 0 and sma50 > 0:
            score += 20 if sma20 > sma50 else 0

        # MACD direction (20 points)
        score += 20 if macd > macd_signal else 0

        # Positive momentum (20 points)
        if momentum > 5:
            score += 20
        elif momentum > 2:
            score += 15
        elif momentum > 0:
            score += 10

        return min(100.0, score)

    def _calculate_entry_score(self, current_price: float, support: float, resistance: float,
                               rsi: float, volume_ratio: float,
                               entry: float, stop: float, target: float) -> float:
        """
        Calculate entry quality score (0-100) with penalties applied

        Inputs: support/resistance distance, RSI pullback zone, volume expansion, R:R ratio

        Args:
            current_price: Current stock price
            support: Support level
            resistance: Resistance level
            rsi: RSI value
            volume_ratio: Current volume / average volume
            entry: Suggested entry price
            stop: Suggested stop-loss price
            target: Suggested target price

        Returns:
            Entry score 0-100 (after penalties)
        """
        score = 0.0

        # RSI pullback zone 40-55 is optimal for swing entry (25 points)
        if 40 <= rsi <= 55:
            score += 25
        elif 35 <= rsi <= 60:
            score += 15
        elif rsi < 35:
            score += 10  # Very oversold, potential reversal

        # Position in support-resistance range (25 points)
        # Closer to support = better entry
        if resistance > support > 0:
            rel_pos = (current_price - support) / (resistance - support)
            if rel_pos < 0.30:
                score += 25  # Near support - ideal entry
            elif rel_pos < 0.50:
                score += 20
            elif rel_pos < 0.65:
                score += 10
            # Above 65%: no points (chasing price near resistance)

        # Volume expansion confirms entry (25 points)
        if volume_ratio > 1.5:
            score += 25
        elif volume_ratio > 1.2:
            score += 18
        elif volume_ratio > 1.0:
            score += 10

        # Risk/Reward ratio (25 points base, penalties applied below)
        rr_ratio = 0.0
        if entry > 0 and stop > 0 and target > 0 and entry > stop:
            risk = entry - stop
            reward = target - entry
            if risk > 0:
                rr_ratio = reward / risk
                if rr_ratio >= 2.0:
                    score += 25
                elif rr_ratio >= 1.5:
                    score += 20
                elif rr_ratio >= 1.2:
                    score += 10

        # --- Penalties ---
        # Resistance proximity penalty: within 3% of resistance is risky
        if resistance > 0:
            dist_to_resistance = (resistance - current_price) / current_price
            if dist_to_resistance < 0.03:
                score -= 20

        # Poor R:R penalty
        if rr_ratio > 0:
            if rr_ratio < 1.2:
                score -= 25
            elif rr_ratio < 1.5:
                score -= 15

        return max(0.0, min(100.0, score))

    def _calculate_confidence(self, trend_score: float, volume_ratio: float,
                              volatility: float, rr_ratio: float) -> str:
        """
        Calculate qualitative confidence level based on signal quality

        Args:
            trend_score: Trend strength score (0-100)
            volume_ratio: Volume ratio (current / average)
            volatility: Annualized volatility percentage
            rr_ratio: Risk/reward ratio

        Returns:
            Confidence level: 'low', 'medium', or 'high'
        """
        # Trend alignment (0-25)
        trend_component = min(25.0, trend_score * 0.25)

        # Volume confirmation (0-25)
        if volume_ratio > 1.5:
            volume_component = 25.0
        elif volume_ratio > 1.2:
            volume_component = 18.0
        elif volume_ratio > 1.0:
            volume_component = 10.0
        else:
            volume_component = 0.0

        # Volatility stability (0-25): lower volatility = more confident
        if volatility < 20:
            vol_component = 25.0
        elif volatility < 30:
            vol_component = 18.0
        elif volatility < 40:
            vol_component = 10.0
        else:
            vol_component = 0.0  # High volatility reduces confidence

        # R:R quality (0-25)
        if rr_ratio >= 2.0:
            rr_component = 25.0
        elif rr_ratio >= 1.5:
            rr_component = 18.0
        elif rr_ratio >= 1.2:
            rr_component = 10.0
        else:
            rr_component = 0.0

        confidence_score = trend_component + volume_component + vol_component + rr_component

        # High volatility penalty: extremely volatile stocks reduce confidence
        if volatility > 40:
            confidence_score -= 15

        if confidence_score >= 65:
            return 'high'
        elif confidence_score >= 40:
            return 'medium'
        else:
            return 'low'

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
        Calculate comprehensive score for a stock using separate trend and entry scores.

        Composite score = 0.6 * trend_score + 0.4 * entry_score

        Args:
            symbol: Stock ticker symbol
            current_price: Current stock price

        Returns:
            Dictionary with score, probability, indicators, trend/entry breakdown,
            regime, strategy_type, confidence, rr_ratio, and expected_return_pct
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
        atr = self.calculate_atr(hist)

        # Calculate support and resistance levels
        support, resistance, data_quality_days = self.calculate_support_resistance(hist)
        relative_position = self.calculate_relative_position(current_price, support, resistance)

        # Detect market regime
        sma20 = mas.get('SMA_20', 0)
        sma50 = mas.get('SMA_50', 0)
        regime = self.detect_market_regime(current_price, sma20, sma50)

        # Determine strategy type and compute entry/stop/target for R:R
        if regime == 'uptrend' and 35 <= rsi <= 60 and sma20 > 0:
            strategy_type = 'pullback_entry'
            entry = sma20 * 1.02  # Entry near SMA20 on pullback
            stop = (support - atr * 0.5) if (support > 0 and atr > 0) else current_price * 0.95
            target = resistance if resistance > entry else entry + (entry - stop) * 2
        elif current_price > (resistance * 0.99) and volume_ratio > 1.2 and resistance > 0:
            strategy_type = 'breakout_entry'
            entry = current_price
            stop = (resistance - atr * 0.5) if atr > 0 else current_price * 0.95
            target = resistance + (resistance - support) if support > 0 else current_price * 1.10
        elif regime == 'range' and support > 0 and (current_price - support) / current_price < 0.05:
            strategy_type = 'range_reversal'
            entry = current_price
            stop = (support - atr * 0.5) if atr > 0 else current_price * 0.95
            target = resistance if resistance > entry else entry * 1.10
        else:
            strategy_type = 'no_setup'
            entry = current_price
            stop = (current_price - atr * 1.5) if atr > 0 else current_price * 0.95
            target = (current_price + atr * 2.0) if atr > 0 else current_price * 1.10

        # Calculate separate trend and entry scores
        trend_score = self._calculate_trend_score(current_price, mas, macd, macd_signal, momentum)
        entry_score = self._calculate_entry_score(
            current_price, support, resistance, rsi, volume_ratio, entry, stop, target
        )

        # Composite score: 60% trend + 40% entry
        composite_score = 0.6 * trend_score + 0.4 * entry_score

        # --- Forecast direction alignment ---
        # Calculate expected return based on regime and trend
        if atr > 0:
            if regime == 'uptrend' and trend_score > 60:
                expected_target = current_price + atr * 2.0
            elif regime == 'downtrend':
                expected_target = current_price - atr * 2.0
            else:
                # Range: use midpoint as mean-reversion target
                midpoint = (support + resistance) / 2 if (support > 0 and resistance > 0) else current_price
                expected_target = midpoint
        else:
            expected_target = current_price * (1 + momentum / 100)

        expected_return_pct = ((expected_target - current_price) / current_price * 100) if current_price > 0 else 0

        # Penalize if forecast is bearish in an uptrend regime while composite score is bullish.
        # Only applied in uptrend to avoid double-penalizing downtrend stocks.
        if regime == 'uptrend' and expected_return_pct < 0 and composite_score > 50:
            composite_score = max(0, composite_score - 20)

        # Flat Range Bonus: low-volatility consolidation patterns near support
        is_flat_range = (volatility < 30 and price_range < 15)
        is_oversold = rsi < 50
        if is_flat_range and is_oversold:
            range_tightness = max(0, 15 - price_range)
            flat_range_bonus = min(10, range_tightness * 0.67)
            composite_score = min(100, composite_score + flat_range_bonus)

        # Volatility filter: high volatility reduces entry_score (and therefore composite_score)
        if volatility > 40:
            entry_score = max(0, entry_score - 15)

        # Compute R:R ratio for output
        rr_ratio = 0.0
        if entry > stop > 0 and target > entry:
            risk = entry - stop
            reward = target - entry
            if risk > 0:
                rr_ratio = reward / risk

        # Sigmoid-based probability: maps composite_score to realistic probability range ~50%-95%
        sigmoid_input = (composite_score / 100.0) * 3.0
        probability = (1.0 / (1.0 + np.exp(-sigmoid_input))) * 100.0
        probability = min(100.0, max(0.0, probability))

        # Confidence level based on signal quality
        confidence = self._calculate_confidence(trend_score, volume_ratio, volatility, rr_ratio)

        # Check breakout filters (legacy, for backwards compatibility)
        breakout_filters = self.check_breakout_filters(
            current_price, support, resistance, volume_ratio,
            rsi, macd_hist, macd, macd_signal
        )

        # Indicator breakdown
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

        # Score contributions include both legacy and new scores
        score_contributions = {
            'trend_score': round(trend_score, 1),
            'entry_score': round(entry_score, 1),
        }

        return {
            'symbol': symbol,
            'score': round(composite_score, 2),
            'probability': round(probability, 1),
            'trend_score': round(trend_score, 1),
            'entry_score': round(entry_score, 1),
            'regime': regime,
            'strategy_type': strategy_type,
            'confidence': confidence,
            'rr_ratio': round(rr_ratio, 2),
            'expected_return_pct': round(expected_return_pct, 2),
            'indicators': indicators,
            'score_contributions': score_contributions,
            'raw_scores': {
                'trend': round(trend_score, 1),
                'entry': round(entry_score, 1),
            },
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
