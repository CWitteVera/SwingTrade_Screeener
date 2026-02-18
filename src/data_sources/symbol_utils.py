"""
Symbol utility functions for data sources
"""
import re
from typing import List

# Compile regex pattern at module level for better performance
VALID_SYMBOL_PATTERN = re.compile(r'^[A-Z0-9.\-]+$')


def clean_symbols(symbols: List[str]) -> List[str]:
    """
    Clean and sanitize a list of stock symbols.
    
    This function:
    - Strips whitespace from each symbol
    - Converts to uppercase
    - Removes empty entries
    - Allows only A-Z, 0-9, dot (.), and dash (-) characters
    - Removes duplicates while preserving order
    
    Args:
        symbols: List of raw stock symbols
        
    Returns:
        List of cleaned, valid stock symbols
        
    Examples:
        >>> clean_symbols(['aapl', ' MSFT ', 'GOOG', 'aapl'])
        ['AAPL', 'MSFT', 'GOOG']
        
        >>> clean_symbols(['TSLA', 'INVALID@SYMBOL', 'BRK.B', 'BRK-A'])
        ['TSLA', 'BRK.B', 'BRK-A']
    """
    if not symbols:
        return []
    
    cleaned = []
    seen = set()
    
    for symbol in symbols:
        # Skip non-string entries
        if not isinstance(symbol, str):
            continue
            
        # Strip whitespace and convert to uppercase
        symbol = symbol.strip().upper()
        
        # Skip empty strings
        if not symbol:
            continue
        
        # Skip symbols with invalid characters
        if not VALID_SYMBOL_PATTERN.match(symbol):
            continue
        
        # Skip duplicates (preserve first occurrence order)
        if symbol in seen:
            continue
        
        seen.add(symbol)
        cleaned.append(symbol)
    
    return cleaned
