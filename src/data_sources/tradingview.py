"""
TradingView Data Source (Advanced)
For advanced real-time data with 3,000+ fields
Uses tradingview-screener package for data fetching
"""
import pandas as pd
from typing import List, Optional, Dict
import time
from .base import DataSource


class TradingViewDataSource(DataSource):
    """TradingView data source for advanced/real-time data"""
    
    # Cache for TradingView queries (avoid recomputation when only slider moves)
    _cache = {}
    _cache_ttl = 300  # 5 minutes (same as streamlit cache)
    
    # Default result limit to keep UI responsive
    DEFAULT_LIMIT = 500
    
    # Default fields for basic screening (safe defaults)
    DEFAULT_FIELDS = [
        'name',           # Ticker symbol
        'close',          # Close/Last price (normalized to 'price')
        'volume',         # Trading volume
        'change',         # Price change ($)
        'change_pct',     # Price change (%)
        'market_cap_basic',  # Market capitalization
    ]
    
    # Additional advanced fields users can select
    ADVANCED_FIELDS = [
        'relative_volume_10d_calc',  # Relative volume (10-day)
        'MACD.macd',                 # MACD indicator
        'MACD.signal',               # MACD signal line
        'RSI',                       # RSI indicator
        'Stoch.K',                   # Stochastic K
        'Stoch.D',                   # Stochastic D
        'EMA5',                      # 5-day EMA
        'EMA10',                     # 10-day EMA
        'EMA20',                     # 20-day EMA
        'EMA50',                     # 50-day EMA
        'BB.upper',                  # Bollinger Band upper
        'BB.lower',                  # Bollinger Band lower
        'VWAP',                      # Volume-weighted average price
    ]
    
    def __init__(self, selected_fields: Optional[List[str]] = None, 
                 limit: int = DEFAULT_LIMIT):
        """
        Initialize TradingView data source
        
        Args:
            selected_fields: List of additional fields to fetch (beyond defaults)
            limit: Maximum number of results to return (default: 500)
        """
        self.selected_fields = selected_fields or []
        self.limit = min(limit, self.DEFAULT_LIMIT)  # Cap at default limit
        self.has_session_cookies = False  # Track if session cookies are available
        self.is_realtime = False  # Track if data is real-time or delayed
    
    def get_name(self) -> str:
        return "TradingView (Advanced)"
    
    def _get_cache_key(self, universe_key: str) -> str:
        """Generate cache key based on universe and selected fields"""
        fields_key = ','.join(sorted(self.DEFAULT_FIELDS + self.selected_fields))
        return f"tv_{universe_key}_{fields_key}_{self.limit}"
    
    def _get_cached_data(self, cache_key: str) -> Optional[pd.DataFrame]:
        """Get data from cache if still valid"""
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                return data
        return None
    
    def _set_cached_data(self, cache_key: str, data: pd.DataFrame):
        """Store data in cache with timestamp"""
        self._cache[cache_key] = (data, time.time())
    
    def _normalize_price_field(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize TradingView's price fields to standard 'price' column
        
        Price Field Mapping:
        - TradingView provides 'close' (daily close) or 'last' (last trade)
        - We normalize to 'price' column for pipeline consistency
        - Priority: 'close' > 'last' > None
        
        Args:
            df: DataFrame from TradingView with 'close' or 'last' column
            
        Returns:
            DataFrame with normalized 'price' column
        """
        if 'close' in df.columns:
            df['price'] = df['close']
        elif 'last' in df.columns:
            df['price'] = df['last']
        else:
            # No price field available - this shouldn't happen with default fields
            df['price'] = None
        
        return df
    
    def _fetch_from_tradingview(self, symbols: List[str]) -> pd.DataFrame:
        """
        Fetch data from TradingView screener API
        
        Args:
            symbols: List of stock symbols (used as universe filter)
            
        Returns:
            DataFrame with requested fields
        """
        try:
            from tradingview_screener import Query, Column
            
            # Build field list (preserve order, remove duplicates)
            all_fields = list(dict.fromkeys(self.DEFAULT_FIELDS + self.selected_fields))
            
            # Create query
            query = Query()
            query = query.select(*all_fields)
            
            # Filter by symbols if specific ones are provided
            # Note: TradingView screener works best when screening the whole market
            # and then filtering by ticker. For large symbol lists, we just limit results.
            if len(symbols) <= 20:
                # For small symbol lists, we can use set_tickers
                query = query.set_tickers(*symbols)
            
            # Apply result limit
            query = query.limit(self.limit)
            
            # Fetch data
            data = query.get_scanner_data()
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Note: We set is_realtime flag but this is a placeholder.
            # Actual real-time status would require checking TradingView's response headers
            # or data timestamps, which is beyond the scope of basic integration.
            self.is_realtime = len(df) > 0
            
            return df
            
        except Exception as e:
            # Connection error, auth error, or other API issue
            error_msg = str(e).lower()
            if 'auth' in error_msg or 'session' in error_msg or 'cookie' in error_msg:
                self.has_session_cookies = False
            raise
    
    def _generate_fallback_data(self, symbols: List[str]) -> pd.DataFrame:
        """
        Generate fallback data when TradingView API is unavailable
        Uses Yahoo Finance as fallback for reliability
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            DataFrame with symbol, price, volume, change, change_pct
        """
        try:
            import yfinance as yf
            
            results = []
            missing_price_count = 0
            
            # Limit symbols to respect the overall limit
            limited_symbols = symbols[:self.limit]
            
            for symbol in limited_symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    hist = ticker.history(period="1d")
                    
                    if not hist.empty:
                        # Use Close price as primary field
                        if 'Close' in hist.columns and pd.notna(hist['Close'].iloc[-1]):
                            current_price = hist['Close'].iloc[-1]
                        elif 'Adj Close' in hist.columns and pd.notna(hist['Adj Close'].iloc[-1]):
                            current_price = hist['Adj Close'].iloc[-1]
                        else:
                            missing_price_count += 1
                            continue
                        
                        prev_close = info.get('previousClose', current_price)
                        volume = hist['Volume'].iloc[-1] if 'Volume' in hist.columns else 0
                        
                        change = current_price - prev_close
                        change_pct = (change / prev_close * 100) if prev_close else 0
                        
                        result = {
                            'symbol': symbol,
                            'name': symbol,
                            'price': round(current_price, 2),
                            'volume': int(volume),
                            'change': round(change, 2),
                            'change_pct': round(change_pct, 2),
                            'close': round(current_price, 2),
                        }
                        
                        # Add market cap if available
                        if 'marketCap' in info:
                            result['market_cap_basic'] = info['marketCap']
                        
                        results.append(result)
                    else:
                        missing_price_count += 1
                        
                except Exception:
                    missing_price_count += 1
                    continue
            
            df = pd.DataFrame(results)
            df.attrs['missing_price_count'] = missing_price_count
            df.attrs['is_fallback'] = True
            
            return df
            
        except Exception:
            # If Yahoo also fails, return empty DataFrame
            df = pd.DataFrame(columns=['symbol', 'name', 'price', 'volume', 'change', 'change_pct'])
            df.attrs['missing_price_count'] = len(symbols)
            df.attrs['is_fallback'] = True
            return df
    
    def fetch_data(self, symbols: List[str]) -> pd.DataFrame:
        """
        Fetch data from TradingView with advanced fields
        
        Fetching Strategy:
        1. Try to fetch from TradingView screener API
        2. Apply result limit (default: 500) to keep UI responsive
        3. Fall back to Yahoo Finance if TradingView is unavailable
        4. Cache results by universe + field set for 5 minutes
        
        Price Field Normalization:
        - TradingView returns 'close' or 'last' fields
        - We normalize to standard 'price' column for pipeline consistency
        - Symbols without valid price are dropped and counted
        
        Session Cookies:
        - Real-time data may require session cookies
        - Falls back to delayed data if cookies are missing
        - Displays tooltip to inform user
        
        Args:
            symbols: List of stock symbols to screen
            
        Returns:
            DataFrame with columns: symbol, price, volume, change, change_pct, [advanced fields]
            DataFrame.attrs['missing_price_count'] = number of symbols with missing price
            DataFrame.attrs['truncated'] = True if results were limited
            DataFrame.attrs['is_fallback'] = True if using fallback data
        """
        # Generate cache key based on symbols
        universe_key = f"{len(symbols)}_{hash(tuple(sorted(symbols[:10])))}"
        cache_key = self._get_cache_key(universe_key)
        
        # Check cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Try TradingView first
        try:
            df = self._fetch_from_tradingview(symbols)
            
            # Normalize price field
            df = self._normalize_price_field(df)
            
            # Ensure we have symbol column
            if 'name' in df.columns and 'symbol' not in df.columns:
                df['symbol'] = df['name']
            
            # Count missing prices and drop them
            missing_price_count = df['price'].isna().sum()
            df = df.dropna(subset=['price'])
            
            # Track if results were truncated
            was_truncated = len(df) >= self.limit
            
            # Store metadata
            df.attrs['missing_price_count'] = int(missing_price_count)
            df.attrs['truncated'] = was_truncated
            df.attrs['is_fallback'] = False
            
            # Cache the result
            self._set_cached_data(cache_key, df)
            
            return df
            
        except Exception:
            # Fall back to Yahoo Finance
            df = self._generate_fallback_data(symbols)
            
            # Normalize price field (should already be done, but ensure it)
            if 'price' not in df.columns and 'close' in df.columns:
                df['price'] = df['close']
            
            # Cache the fallback result too
            self._set_cached_data(cache_key, df)
            
            return df
