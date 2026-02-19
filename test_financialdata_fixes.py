#!/usr/bin/env python3
"""
Tests for symbol utilities used across data sources.
Tests clean_symbols handles various input formats correctly.
"""
import sys
import os
import unittest
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


if __name__ == '__main__':
    print("\n🧪 Running Symbol Utility Tests\n")
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestCleanSymbolsStringInput))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
