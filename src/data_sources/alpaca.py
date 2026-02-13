"""
Alpaca Data Source (Placeholder)
For intraday movers data
"""
import pandas as pd
from typing import List
import random
from .base import DataSource


class AlpacaDataSource(DataSource):
    """Alpaca data source for intraday movers"""
    
    def get_name(self) -> str:
        return "Alpaca Movers (Intraday)"
    
    def fetch_data(self, symbols: List[str]) -> pd.DataFrame:
        """
        Placeholder for Alpaca movers data
        In a real implementation, this would connect to Alpaca API
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            DataFrame with symbol, price, volume, change, change_pct
        """
        # Placeholder implementation - returns sample data with higher volatility
        results = []
        random.seed(200)  # Different seed for variety
        
        for symbol in symbols:
            base_price = random.uniform(5, 600)
            # Intraday movers have higher volatility
            change_pct = random.uniform(-15, 15)
            change = base_price * (change_pct / 100)
            volume = random.randint(5000000, 100000000)
            
            results.append({
                'symbol': symbol,
                'price': round(base_price, 2),
                'volume': volume,
                'change': round(change, 2),
                'change_pct': round(change_pct, 2)
            })
        
        return pd.DataFrame(results)
