"""
Yahoo Finance Data Source
Fetches end-of-day (EOD) stock data
"""
import pandas as pd
import yfinance as yf
from typing import List
import random
from .base import DataSource


class YahooDataSource(DataSource):
    """Yahoo Finance data source for EOD data"""
    
    def get_name(self) -> str:
        return "Yahoo (EOD)"
    
    def _generate_mock_data(self, symbols: List[str]) -> pd.DataFrame:
        """
        Generate mock data for demo purposes when API is unavailable
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            DataFrame with symbol, price, volume, change, change_pct
        """
        results = []
        random.seed(42)  # Consistent results
        
        for symbol in symbols:
            # Generate realistic-looking mock data
            base_price = random.uniform(10, 500)
            change_pct = random.uniform(-5, 5)
            change = base_price * (change_pct / 100)
            volume = random.randint(1000000, 50000000)
            
            results.append({
                'symbol': symbol,
                'price': round(base_price, 2),
                'volume': volume,
                'change': round(change, 2),
                'change_pct': round(change_pct, 2)
            })
        
        return pd.DataFrame(results)
    
    def fetch_data(self, symbols: List[str]) -> pd.DataFrame:
        """
        Fetch EOD data from Yahoo Finance
        Falls back to mock data if API is unavailable
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            DataFrame with symbol, price, volume, change, change_pct
        """
        results = []
        api_available = True
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                hist = ticker.history(period="1d")
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    prev_close = info.get('previousClose', current_price)
                    volume = hist['Volume'].iloc[-1]
                    
                    change = current_price - prev_close
                    change_pct = (change / prev_close * 100) if prev_close else 0
                    
                    results.append({
                        'symbol': symbol,
                        'price': round(current_price, 2),
                        'volume': int(volume),
                        'change': round(change, 2),
                        'change_pct': round(change_pct, 2)
                    })
                else:
                    api_available = False
                    break
            except Exception as e:
                # API likely unavailable
                api_available = False
                break
        
        # If API is unavailable, use mock data
        if not api_available or not results:
            return self._generate_mock_data(symbols)
        
        return pd.DataFrame(results)
