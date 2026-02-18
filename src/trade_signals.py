"""
Trade Signals Module
Provides ATR/RSI/SMA/pivot logic and entry/exit suggestions
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, List


def calculate_atr(df: pd.DataFrame, period: int = 14) -> float:
    """
    Calculate Average True Range (ATR)
    
    Args:
        df: DataFrame with OHLC data (must have 'High', 'Low', 'Close' columns)
        period: ATR period (default: 14)
        
    Returns:
        ATR value or NaN if insufficient data
    """
    if not {'High', 'Low', 'Close'}.issubset(df.columns) or len(df) < period + 1:
        return np.nan
    
    # Calculate True Range
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift(1))
    low_close = np.abs(df['Low'] - df['Close'].shift(1))
    
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    
    # Calculate ATR as moving average of True Range
    atr = true_range.rolling(window=period).mean().iloc[-1]
    
    return atr if not pd.isna(atr) else np.nan


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> float:
    """
    Calculate Relative Strength Index (RSI)
    
    Args:
        df: DataFrame with price data (must have 'Close' column)
        period: RSI period (default: 14)
        
    Returns:
        RSI value (0-100) or NaN if insufficient data
    """
    if 'Close' not in df.columns or len(df) < period + 1:
        return np.nan
    
    prices = df['Close']
    delta = prices.diff()
    
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else np.nan


def sma(df: pd.DataFrame, period: int = 20, column: str = 'Close') -> float:
    """
    Calculate Simple Moving Average (SMA)
    
    Args:
        df: DataFrame with price data
        period: SMA period (default: 20)
        column: Column to calculate SMA on (default: 'Close')
        
    Returns:
        SMA value or NaN if insufficient data
    """
    if column not in df.columns or len(df) < period:
        return np.nan
    
    sma_value = df[column].rolling(window=period).mean().iloc[-1]
    
    return sma_value if not pd.isna(sma_value) else np.nan


def detect_pivots(df: pd.DataFrame, lookback: int = 5) -> Dict[str, Optional[float]]:
    """
    Detect recent pivot highs and lows
    
    Args:
        df: DataFrame with OHLC data
        lookback: Number of periods to look back for pivots
        
    Returns:
        Dictionary with 'pivot_high' and 'pivot_low' values
    """
    if not {'High', 'Low'}.issubset(df.columns) or len(df) < lookback * 2 + 1:
        return {'pivot_high': None, 'pivot_low': None}
    
    # Get recent data
    recent_data = df.tail(lookback * 2 + 1)
    
    # Find pivot high (highest high in the middle of the window)
    highs = recent_data['High'].values
    pivot_high_idx = len(highs) // 2
    is_pivot_high = all(highs[pivot_high_idx] >= highs[i] for i in range(len(highs)) if i != pivot_high_idx)
    pivot_high = highs[pivot_high_idx] if is_pivot_high else None
    
    # Find pivot low (lowest low in the middle of the window)
    lows = recent_data['Low'].values
    pivot_low_idx = len(lows) // 2
    is_pivot_low = all(lows[pivot_low_idx] <= lows[i] for i in range(len(lows)) if i != pivot_low_idx)
    pivot_low = lows[pivot_low_idx] if is_pivot_low else None
    
    # If no pivot in middle, use recent min/max
    if pivot_high is None:
        pivot_high = recent_data['High'].max()
    if pivot_low is None:
        pivot_low = recent_data['Low'].min()
    
    return {
        'pivot_high': pivot_high,
        'pivot_low': pivot_low
    }


def suggest_entry_exit(
    df: pd.DataFrame,
    pullback_pct: float = 0.02,
    atr_mult_stop: float = 1.5,
    atr_mult_targets: Tuple[float, float] = (1.5, 2.5)
) -> Dict:
    """
    Suggest entry/exit levels based on pullback or breakout setups
    
    Args:
        df: DataFrame with OHLC data
        pullback_pct: Percentage pullback from SMA20 for entry (default: 2%)
        atr_mult_stop: ATR multiplier for stop loss (default: 1.5)
        atr_mult_targets: Tuple of ATR multipliers for targets (default: 1.5, 2.5)
        
    Returns:
        Dictionary with entry/exit suggestions
    """
    if df.empty or len(df) < 30:
        return {
            'strategy': 'Insufficient data',
            'entry': None,
            'stop': None,
            'target1': None,
            'target2': None,
            'confidence': 'Low',
            'notes': 'Need at least 30 days of historical data'
        }
    
    # Calculate indicators
    current_price = df['Close'].iloc[-1]
    sma20 = sma(df, period=20)
    rsi_value = calculate_rsi(df, period=14)
    atr = calculate_atr(df, period=14)
    pivots = detect_pivots(df, lookback=5)
    
    # Calculate 20-day average volume
    avg_volume = df['Volume'].rolling(window=20).mean().iloc[-1] if 'Volume' in df.columns else 0
    current_volume = df['Volume'].iloc[-1] if 'Volume' in df.columns else 0
    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
    
    # Initialize result
    result = {
        'strategy': None,
        'entry': None,
        'stop': None,
        'target1': None,
        'target2': None,
        'confidence': 'Low',
        'notes': []
    }
    
    # Check for pullback setup
    if not pd.isna(sma20) and not pd.isna(rsi_value):
        if current_price > sma20 and 35 <= rsi_value <= 60:
            # Pullback entry setup
            result['strategy'] = 'Pullback Entry'
            result['entry'] = sma20 * (1 + pullback_pct)
            
            # Stop loss: below pivot low or ATR-based
            if pivots['pivot_low'] is not None and not pd.isna(atr):
                result['stop'] = min(pivots['pivot_low'], current_price - atr * atr_mult_stop)
            elif not pd.isna(atr):
                result['stop'] = current_price - atr * atr_mult_stop
            else:
                result['stop'] = current_price * 0.95  # 5% stop as fallback
            
            # Targets based on ATR
            if not pd.isna(atr):
                result['target1'] = result['entry'] + atr * atr_mult_targets[0]
                result['target2'] = result['entry'] + atr * atr_mult_targets[1]
            else:
                result['target1'] = result['entry'] * 1.05
                result['target2'] = result['entry'] * 1.10
            
            result['confidence'] = 'Medium'
            result['notes'].append(f"Price above SMA20 (${sma20:.2f}), RSI in optimal range ({rsi_value:.1f})")
    
    # Check for breakout setup
    if pivots['pivot_high'] is not None and volume_ratio > 1.2:
        if current_price > pivots['pivot_high']:
            # Breakout entry setup
            result['strategy'] = 'Breakout Entry'
            result['entry'] = current_price
            
            # Stop loss: at pivot low or ATR-based
            if pivots['pivot_low'] is not None and not pd.isna(atr):
                result['stop'] = max(pivots['pivot_low'], current_price - atr * atr_mult_stop)
            elif not pd.isna(atr):
                result['stop'] = current_price - atr * atr_mult_stop
            else:
                result['stop'] = current_price * 0.95
            
            # Targets based on ATR
            if not pd.isna(atr):
                result['target1'] = current_price + atr * atr_mult_targets[0]
                result['target2'] = current_price + atr * atr_mult_targets[1]
            else:
                result['target1'] = current_price * 1.05
                result['target2'] = current_price * 1.10
            
            result['confidence'] = 'High' if volume_ratio > 1.5 else 'Medium'
            result['notes'].append(f"Breakout above pivot high (${pivots['pivot_high']:.2f}), Volume ratio: {volume_ratio:.2f}")
    
    # If no setup detected
    if result['strategy'] is None:
        result['strategy'] = 'No Clear Setup'
        result['notes'].append('No pullback or breakout pattern detected')
        result['confidence'] = 'Low'
    
    return result
