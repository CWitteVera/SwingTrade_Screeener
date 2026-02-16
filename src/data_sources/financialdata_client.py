"""
FinancialData.Net Data Source
Advanced data provider with prices, OHLCV, fundamentals, and technical indicators
"""
import pandas as pd
from typing import List, Optional, Dict, Any
import os
import streamlit as st
from .base import DataSource

try:
    from fdnpy import FinancialDataClient as FDNClient
    HAS_SDK = True
except ImportError:
    HAS_SDK = False
    FDNClient = None


class FinancialDataNetSource(DataSource):
    """FinancialData.Net data source for advanced market data"""
    
    # Cache for API responses (avoid recomputation)
    _cache = {}
    _cache_ttl = 300  # 5 minutes TTL
    
    # Default fields for basic screening
    DEFAULT_FIELDS = [
        'symbol',
        'price',
        'volume',
        'market_cap',
    ]
    
    # Available technical indicators
    TECHNICAL_INDICATORS = [
        'rsi',
        'macd',
        'sma_50',
        'sma_150',
        'sma_200',
        'ema_5',
        'ema_10',
        'ema_20',
        'ema_50',
        'relative_volume_10d',
    ]
    
    # Available fundamental fields
    FUNDAMENTAL_FIELDS = [
        'market_cap',
        'pe_ratio',
        'eps',
        'revenue',
        'profit_margin',
    ]
    
    def __init__(self, selected_fields: Optional[List[str]] = None, 
                 interval: str = '1d', lookback_days: int = 365):
        """
        Initialize FinancialData.Net data source
        
        Args:
            selected_fields: List of additional fields to fetch
            interval: Timeframe for OHLCV data (1d, 1h, etc.)
            lookback_days: How many days of historical data to fetch
        """
        self.selected_fields = selected_fields or []
        self.interval = interval
        self.lookback_days = lookback_days
        self.api_key = self._get_api_key()
        self.client = None
        
        if self.api_key and HAS_SDK:
            self.client = FDNClient(api_key=self.api_key)
    
    def _get_api_key(self) -> Optional[str]:
        """
        Get API key from environment or Streamlit secrets
        
        Returns:
            API key string or None if not found
        """
        # Try environment variable first
        api_key = os.environ.get('FINANCIALDATA_API_KEY')
        
        # Try Streamlit secrets
        if not api_key:
            try:
                api_key = st.secrets.get("FINANCIALDATA_API_KEY")
            except (AttributeError, FileNotFoundError):
                pass
        
        return api_key
    
    def get_name(self) -> str:
        return "Advanced Data (financialdata.net)"
    
    def is_available(self) -> bool:
        """Check if the data source is available (has API key and SDK)"""
        return self.api_key is not None and HAS_SDK and self.client is not None
    
    def get_universe(self, set_name: str, limit: int = 500, offset: int = 0) -> List[str]:
        """
        Get universe of symbols from financialdata.net
        
        Args:
            set_name: Universe set name (e.g., 'stock-symbols', 'etf-symbols')
            limit: Maximum number of symbols to return
            offset: Starting offset for pagination
            
        Returns:
            List of symbol strings
        """
        if not self.is_available():
            return []
        
        try:
            if set_name == 'stock-symbols':
                # Get US stock symbols
                symbols_data = self.client.get_stock_symbols()
            elif set_name == 'etf-symbols':
                # Get ETF symbols
                symbols_data = self.client.get_etf_symbols()
            else:
                # Default to stock symbols
                symbols_data = self.client.get_stock_symbols()
            
            # Extract symbols from response
            symbols = [item.get('trading_symbol', '').upper() 
                      for item in symbols_data if item.get('trading_symbol')]
            
            # Apply limit and offset
            return symbols[offset:offset + limit]
            
        except Exception as e:
            # Log error and return empty list
            print(f"Error fetching universe from financialdata.net: {e}")
            return []
    
    def get_quotes(self, symbols: List[str]) -> pd.DataFrame:
        """
        Get current quotes for symbols
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            DataFrame with symbol, price, volume columns
        """
        if not self.is_available() or not symbols:
            return pd.DataFrame()
        
        try:
            # Fetch quotes using the SDK
            quotes_data = self.client.get_stock_quotes(identifiers=','.join(symbols))
            
            if not quotes_data:
                return pd.DataFrame()
            
            # Normalize to our schema
            records = []
            for quote in quotes_data:
                record = {
                    'symbol': quote.get('trading_symbol', '').upper(),
                    'price': float(quote.get('close', 0) or quote.get('last', 0) or 0),
                    'open': float(quote.get('open', 0) or 0),
                    'high': float(quote.get('high', 0) or 0),
                    'low': float(quote.get('low', 0) or 0),
                    'close': float(quote.get('close', 0) or 0),
                    'volume': int(quote.get('volume', 0) or 0),
                    'market_cap': float(quote.get('market_cap', 0) or 0),
                }
                records.append(record)
            
            return pd.DataFrame(records)
            
        except Exception as e:
            print(f"Error fetching quotes from financialdata.net: {e}")
            return pd.DataFrame()
    
    def get_ohlcv(self, symbols: List[str], interval: str = '1d', 
                   lookback_days: int = 365) -> Dict[str, pd.DataFrame]:
        """
        Get OHLCV data for symbols
        
        Args:
            symbols: List of stock symbols
            interval: Timeframe (1d, 1h, etc.)
            lookback_days: Number of days to look back
            
        Returns:
            Dictionary mapping symbol -> DataFrame with OHLC data
        """
        if not self.is_available() or not symbols:
            return {}
        
        result = {}
        
        for symbol in symbols:
            try:
                # Fetch price history
                prices_data = self.client.get_stock_prices(identifier=symbol)
                
                if not prices_data:
                    continue
                
                # Convert to DataFrame
                df = pd.DataFrame(prices_data)
                
                # Normalize column names
                if 'date' in df.columns:
                    df['ts'] = pd.to_datetime(df['date'])
                elif 'timestamp' in df.columns:
                    df['ts'] = pd.to_datetime(df['timestamp'])
                
                # Ensure OHLCV columns exist
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    if col not in df.columns:
                        df[col] = 0
                
                # Limit to lookback period
                if 'ts' in df.columns:
                    df = df.sort_values('ts', ascending=False).head(lookback_days)
                
                result[symbol] = df
                
            except Exception as e:
                print(f"Error fetching OHLCV for {symbol}: {e}")
                continue
        
        return result
    
    def get_fundamentals(self, symbols: List[str], fields: List[str]) -> pd.DataFrame:
        """
        Get fundamental data for symbols
        
        Args:
            symbols: List of stock symbols
            fields: List of fundamental fields to fetch
            
        Returns:
            DataFrame with requested fundamental fields
        """
        if not self.is_available() or not symbols:
            return pd.DataFrame()
        
        records = []
        
        for symbol in symbols:
            try:
                # Fetch company information and key metrics
                info = self.client.get_company_information(identifier=symbol)
                metrics = self.client.get_key_metrics(identifier=symbol)
                
                record = {'symbol': symbol}
                
                # Extract requested fields
                if info:
                    info_data = info[0] if isinstance(info, list) else info
                    if 'market_cap' in fields:
                        record['market_cap'] = info_data.get('market_cap', 0)
                
                if metrics:
                    metrics_data = metrics[0] if isinstance(metrics, list) else metrics
                    if 'pe_ratio' in fields:
                        record['pe_ratio'] = metrics_data.get('pe_ratio', 0)
                    if 'eps' in fields:
                        record['eps'] = metrics_data.get('eps', 0)
                
                records.append(record)
                
            except Exception as e:
                print(f"Error fetching fundamentals for {symbol}: {e}")
                continue
        
        return pd.DataFrame(records)
    
    def get_indicators(self, symbols: List[str], indicators_list: List[str], 
                      interval: str = '1d') -> pd.DataFrame:
        """
        Get technical indicators for symbols
        
        Note: financialdata.net doesn't provide pre-calculated indicators,
        so we would need to calculate them from OHLCV data.
        For now, this returns an empty DataFrame.
        
        Args:
            symbols: List of stock symbols
            indicators_list: List of indicator names
            interval: Timeframe for indicators
            
        Returns:
            DataFrame with requested indicators
        """
        # This would require calculating indicators from OHLCV data
        # or using a different endpoint if available
        return pd.DataFrame()
    
    def fetch_data(self, symbols: List[str]) -> pd.DataFrame:
        """
        Main fetch method implementing DataSource interface
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            DataFrame with normalized columns
        """
        # Check if API is available, otherwise fallback to Yahoo
        if not self.is_available():
            # Import here to avoid circular dependency
            from .yahoo import YahooDataSource
            yahoo_source = YahooDataSource()
            df = yahoo_source.fetch_data(symbols)
            # Mark as fallback
            df.attrs['is_fallback'] = True
            return df
        
        # Fetch quotes as the primary data source
        df = self.get_quotes(symbols)
        
        # If selected fields include fundamentals, fetch and merge
        fundamental_fields = [f for f in self.selected_fields 
                             if f in self.FUNDAMENTAL_FIELDS]
        if fundamental_fields and not df.empty:
            fundamentals = self.get_fundamentals(symbols, fundamental_fields)
            if not fundamentals.empty:
                df = df.merge(fundamentals, on='symbol', how='left', suffixes=('', '_fund'))
        
        # Add symbol column if missing
        if not df.empty and 'symbol' not in df.columns:
            df['symbol'] = symbols[0] if len(symbols) == 1 else None
        
        # Mark as not a fallback
        df.attrs['is_fallback'] = False
        
        return df
