#!/usr/bin/env python3
"""
Tests for FinancialData.Net integration fixes:
1. Symbol corruption fix - clean_symbols handles string input
2. Fallback mechanism triggers when API returns empty data
3. 401 error produces actionable log message
"""
import sys
import os
import logging
import unittest
from unittest.mock import MagicMock, patch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_sources.symbol_utils import clean_symbols


class TestCleanSymbolsStringInput(unittest.TestCase):
    """Test that clean_symbols handles string input correctly (Issue #2 fix)"""

    def test_list_input_unchanged(self):
        """Normal list input should still work"""
        result = clean_symbols(['AAPL', 'MSFT', 'GOOGL'])
        self.assertEqual(result, ['AAPL', 'MSFT', 'GOOGL'])

    def test_string_input_split_on_comma(self):
        """Comma-separated string should be split into symbols"""
        result = clean_symbols('AAPL,MSFT,GOOGL')
        self.assertEqual(result, ['AAPL', 'MSFT', 'GOOGL'])

    def test_string_input_with_spaces(self):
        """String with spaces around commas should be handled"""
        result = clean_symbols('AAPL, MSFT, GOOGL')
        self.assertEqual(result, ['AAPL', 'MSFT', 'GOOGL'])

    def test_string_input_lowercase(self):
        """Lowercase symbols in string input should be uppercased"""
        result = clean_symbols('aapl,msft,googl')
        self.assertEqual(result, ['AAPL', 'MSFT', 'GOOGL'])

    def test_empty_string_returns_empty_list(self):
        """Empty string should return empty list"""
        result = clean_symbols('')
        self.assertEqual(result, [])

    def test_list_deduplication_preserved(self):
        """Duplicates in list input are still removed"""
        result = clean_symbols(['AAPL', 'MSFT', 'AAPL'])
        self.assertEqual(result, ['AAPL', 'MSFT'])

    def test_string_deduplication(self):
        """Duplicates in string input are also removed"""
        result = clean_symbols('AAPL,MSFT,AAPL')
        self.assertEqual(result, ['AAPL', 'MSFT'])

    def test_list_with_invalid_chars_filtered(self):
        """Symbols with invalid characters are filtered out"""
        result = clean_symbols(['AAPL', 'INVALID@SYMBOL', 'MSFT'])
        self.assertEqual(result, ['AAPL', 'MSFT'])

    def test_list_with_whitespace_stripped(self):
        """Whitespace is stripped from symbols"""
        result = clean_symbols([' AAPL ', '  MSFT  '])
        self.assertEqual(result, ['AAPL', 'MSFT'])

    def test_symbols_with_dot_and_dash(self):
        """Symbols with dot and dash are preserved"""
        result = clean_symbols(['BRK.B', 'BRK-A'])
        self.assertEqual(result, ['BRK.B', 'BRK-A'])

    def test_none_input_returns_empty(self):
        """None input should return empty list"""
        result = clean_symbols(None)
        self.assertEqual(result, [])

    def test_empty_list_returns_empty(self):
        """Empty list input returns empty list"""
        result = clean_symbols([])
        self.assertEqual(result, [])

    def test_single_symbol_string(self):
        """Single symbol string (no comma) is returned as one-item list"""
        result = clean_symbols('AAPL')
        self.assertEqual(result, ['AAPL'])


class TestFinancialDataFallback(unittest.TestCase):
    """Test that fetch_data falls back to Yahoo Finance when API is unavailable or returns empty data"""

    def _make_yahoo_df(self):
        """Helper to create a mock Yahoo Finance DataFrame"""
        import pandas as pd
        return pd.DataFrame([{'symbol': 'AAPL', 'price': 150.0, 'volume': 1000000,
                               'change': 1.0, 'change_pct': 0.67}])

    @patch('data_sources.financialdata_client.HAS_SDK', True)
    def test_fallback_when_not_available(self):
        """Should fall back to Yahoo Finance when is_available() returns False"""
        from data_sources.financialdata_client import FinancialDataNetSource

        source = FinancialDataNetSource()
        # Ensure not available (no API key)
        source.api_key = None
        source.client = None

        with patch('data_sources.yahoo.YahooDataSource.fetch_data', return_value=self._make_yahoo_df()):
            result = source.fetch_data(['AAPL', 'MSFT'])

        self.assertTrue(result.attrs.get('is_fallback', False))
        self.assertFalse(result.empty)

    @patch('data_sources.financialdata_client.HAS_SDK', True)
    def test_fallback_when_get_quotes_returns_empty(self):
        """Should fall back to Yahoo Finance when get_quotes returns empty DataFrame"""
        from data_sources.financialdata_client import FinancialDataNetSource

        source = FinancialDataNetSource()
        source.api_key = 'test_key'

        mock_client = MagicMock()
        mock_client.get_stock_quotes.return_value = []
        source.client = mock_client

        with patch('data_sources.yahoo.YahooDataSource.fetch_data', return_value=self._make_yahoo_df()):
            result = source.fetch_data(['AAPL', 'MSFT'])

        self.assertTrue(result.attrs.get('is_fallback', False))
        self.assertFalse(result.empty)

    @patch('data_sources.financialdata_client.HAS_SDK', True)
    def test_no_fallback_when_data_returned(self):
        """Should NOT fall back when get_quotes returns valid data"""
        import pandas as pd
        from data_sources.financialdata_client import FinancialDataNetSource

        source = FinancialDataNetSource()
        source.api_key = 'test_key'

        mock_client = MagicMock()
        mock_client.get_stock_quotes.return_value = [
            {'trading_symbol': 'AAPL', 'close': 150.0, 'volume': 1000000, 'market_cap': 2e12,
             'open': 148.0, 'high': 152.0, 'low': 147.0}
        ]
        source.client = mock_client

        result = source.fetch_data(['AAPL'])

        self.assertFalse(result.attrs.get('is_fallback', True))
        self.assertFalse(result.empty)
        self.assertEqual(result.iloc[0]['symbol'], 'AAPL')


class TestDebugLogging(unittest.TestCase):
    """Test that debug logging is present in get_quotes"""

    @patch('data_sources.financialdata_client.HAS_SDK', True)
    def test_debug_logging_called(self):
        """Debug logging should be called before API request"""
        import pandas as pd
        from data_sources.financialdata_client import FinancialDataNetSource

        source = FinancialDataNetSource()
        source.api_key = 'test_key'

        mock_client = MagicMock()
        mock_client.get_stock_quotes.return_value = [
            {'trading_symbol': 'AAPL', 'close': 150.0, 'volume': 1000000, 'market_cap': 2e12,
             'open': 148.0, 'high': 152.0, 'low': 147.0}
        ]
        source.client = mock_client

        with patch('data_sources.financialdata_client.logger') as mock_logger:
            source.get_quotes(['AAPL', 'MSFT'])
            # Verify debug was called (at least 2 times for symbol count and first 5 symbols)
            self.assertGreaterEqual(mock_logger.debug.call_count, 2)

    @patch('data_sources.financialdata_client.HAS_SDK', True)
    def test_401_error_logs_troubleshooting_steps(self):
        """401 error should produce log message with troubleshooting steps"""
        from data_sources.financialdata_client import FinancialDataNetSource

        source = FinancialDataNetSource()
        source.api_key = 'test_key'

        mock_client = MagicMock()
        mock_client.get_stock_quotes.side_effect = Exception("401 Client Error: Unauthorized")
        source.client = mock_client

        with patch('data_sources.financialdata_client.logger') as mock_logger:
            source.get_quotes(['AAPL'])
            # Should log an error
            self.assertTrue(mock_logger.error.called)
            # Error message should contain actionable guidance
            error_msg = mock_logger.error.call_args[0][0]
            self.assertIn('401', error_msg)
            self.assertIn('FINANCIALDATA_API_KEY', error_msg)
            self.assertIn('financialdata.net', error_msg)


if __name__ == '__main__':
    print("\n🧪 Running FinancialData.Net Integration Fix Tests\n")
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestCleanSymbolsStringInput))
    suite.addTests(loader.loadTestsFromTestCase(TestFinancialDataFallback))
    suite.addTests(loader.loadTestsFromTestCase(TestDebugLogging))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
