"""
Universe Sets Module
Defines different stock universe sets for screening
"""

# S&P 500 - Top 50 for demo purposes
SP500_SYMBOLS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK.B", "UNH", "XOM",
    "JNJ", "JPM", "V", "PG", "MA", "HD", "CVX", "MRK", "ABBV", "PEP",
    "COST", "AVGO", "KO", "ADBE", "MCD", "WMT", "TMO", "CSCO", "PFE", "ACN",
    "NFLX", "LLY", "ABT", "DIS", "NKE", "INTC", "VZ", "CRM", "TXN", "CMCSA",
    "DHR", "ORCL", "NEE", "AMD", "WFC", "UPS", "PM", "BMY", "QCOM", "RTX"
]

# NASDAQ-100 - Top 50 for demo purposes
NASDAQ100_SYMBOLS = [
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA", "AVGO", "COST",
    "ASML", "NFLX", "AMD", "ADBE", "PEP", "CSCO", "TMUS", "CMCSA", "TXN", "INTC",
    "QCOM", "INTU", "AMGN", "HON", "AMAT", "SBUX", "ISRG", "BKNG", "VRTX", "PANW",
    "ADP", "ADI", "GILD", "MU", "LRCX", "REGN", "MDLZ", "PYPL", "MELI", "SNPS",
    "KLAC", "CDNS", "ABNB", "MAR", "CTAS", "CRWD", "NXPI", "MNST", "ORLY", "ADSK"
]

# Leveraged ETFs
LEVERAGED_ETF_SYMBOLS = [
    "TQQQ", "SQQQ", "SPXL", "SPXS", "UPRO", "SOXL", "SOXS", 
    "TECL", "TECS", "TNA", "TZA", "TMF", "FAS", "NUGT", "FNGU"
]

# All NMS stocks (simplified - using major indices for demo)
ALL_NMS_SYMBOLS = list(set(SP500_SYMBOLS + NASDAQ100_SYMBOLS))


def get_universe_symbols(universe_set: str, custom_symbols: list = None) -> list:
    """
    Get symbols for a specific universe set
    
    Args:
        universe_set: Name of the universe set
        custom_symbols: List of custom symbols if universe_set is "Custom CSV"
    
    Returns:
        List of stock symbols
    """
    universe_map = {
        "All NMS": ALL_NMS_SYMBOLS,
        "S&P 500": SP500_SYMBOLS,
        "NASDAQ-100": NASDAQ100_SYMBOLS,
        "Leveraged ETFs": LEVERAGED_ETF_SYMBOLS,
    }
    
    if universe_set == "Custom CSV":
        return custom_symbols or []
    
    return universe_map.get(universe_set, [])
