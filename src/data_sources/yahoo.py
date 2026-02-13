"""
Yahoo Finance Data Source
Fetches end-of-day (EOD) stock data
"""
import pandas as pd
import yfinance as yf
from typing import List
from .base import DataSource


class YahooDataSource(DataSource):
    """Yahoo Finance data source for EOD data"""
    
    def get_name(self) -> str:
        return "Yahoo (EOD)"
    
    def fetch_data(self, symbols: List[str]) -> pd.DataFrame:
        """
        Fetch EOD data from Yahoo Finance
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            DataFrame with symbol, price, volume, change, change_pct
        """
        results = []
        
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
            except Exception as e:
                # Skip symbols that fail to fetch
                continue
        
        return pd.DataFrame(results)
