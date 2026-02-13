"""
Base Data Source Interface
"""
from abc import ABC, abstractmethod
from typing import List
import pandas as pd


class DataSource(ABC):
    """Base class for data sources"""
    
    @abstractmethod
    def fetch_data(self, symbols: List[str]) -> pd.DataFrame:
        """
        Fetch data for given symbols
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            DataFrame with columns: symbol, price, volume, etc.
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the name of the data source"""
        pass
