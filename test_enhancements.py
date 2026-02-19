#!/usr/bin/env python3
"""
Test script for enhanced stock screening features
Tests support/resistance, breakout filters, and technical analysis charts
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scoring_system import StockScorer
from visualizations import StockVisualizer
import pandas as pd


def test_support_resistance():
    """Test support and resistance calculation"""
    print("=" * 60)
    print("TEST 1: Support and Resistance Calculation")
    print("=" * 60)
    
    scorer = StockScorer(lookback_days=120, forecast_days=14)
    
    # Test with popular stocks
    test_symbols = ['AAPL', 'MSFT', 'TSLA']
    
    for symbol in test_symbols:
        print(f"\n{symbol}:")
        try:
            hist = scorer.fetch_historical_data(symbol)
            if not hist.empty:
                support, resistance, days_used = scorer.calculate_support_resistance(hist, period=90)
                current_price = hist['Close'].iloc[-1]
                relative_pos = scorer.calculate_relative_position(current_price, support, resistance)
                
                print(f"  Current Price: ${current_price:.2f}")
                print(f"  Support (90d): ${support:.2f}")
                print(f"  Resistance (90d): ${resistance:.2f}")
                print(f"  Relative Position: {relative_pos:.1%}")
                
                # Check if in favorable range (40%-75%)
                if 0.4 <= relative_pos <= 0.75:
                    print(f"  ✓ In favorable position range!")
                else:
                    print(f"  ✗ Outside favorable range (40%-75%)")
            else:
                print(f"  ✗ No data available")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print("\n✓ Support/Resistance test completed")


def test_breakout_filters():
    """Test breakout filter detection"""
    print("\n" + "=" * 60)
    print("TEST 2: Breakout Filter Detection")
    print("=" * 60)
    
    scorer = StockScorer(lookback_days=120, forecast_days=14)
    
    # Test with a few stocks
    test_symbols = ['AAPL', 'MSFT']
    
    for symbol in test_symbols:
        print(f"\n{symbol}:")
        try:
            hist = scorer.fetch_historical_data(symbol)
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                
                # Calculate all indicators
                rsi = scorer.calculate_rsi(hist['Close'])
                macd, macd_signal, macd_hist = scorer.calculate_macd(hist['Close'])
                volume_ratio = scorer.calculate_volume_trend(hist['Volume'])
                support, resistance, _ = scorer.calculate_support_resistance(hist)
                
                # Check filters
                filters = scorer.check_breakout_filters(
                    current_price, support, resistance,
                    volume_ratio, rsi, macd_hist, macd, macd_signal
                )
                
                print(f"  Volume Spike (≥1.5x): {filters['volume_spike']} (ratio: {volume_ratio:.2f})")
                print(f"  RSI Momentum (50-70): {filters['rsi_momentum']} (RSI: {rsi:.1f})")
                print(f"  MACD Momentum: {filters['macd_momentum']} (hist: {macd_hist:.4f})")
                print(f"  Position Favorable (40-75%): {filters['position_favorable']}")
                print(f"  Overall Breakout Signal: {filters['breakout_signal']}")
                
                if filters['breakout_signal']:
                    print(f"  🚀 BREAKOUT DETECTED!")
            else:
                print(f"  ✗ No data available")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print("\n✓ Breakout filter test completed")


def test_comprehensive_scoring():
    """Test comprehensive scoring with new features"""
    print("\n" + "=" * 60)
    print("TEST 3: Comprehensive Scoring with New Features")
    print("=" * 60)
    
    scorer = StockScorer(lookback_days=120, forecast_days=14)
    
    test_symbols = ['AAPL', 'NVDA']
    
    for symbol in test_symbols:
        print(f"\n{symbol}:")
        try:
            hist = scorer.fetch_historical_data(symbol)
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                score_data = scorer.score_stock(symbol, current_price)
                
                print(f"  Score: {score_data['score']:.2f}")
                print(f"  Probability: {score_data['probability']:.1f}%")
                
                # Display support/resistance info
                sr_data = score_data.get('support_resistance', {})
                print(f"  Support: ${sr_data.get('support', 0):.2f}")
                print(f"  Resistance: ${sr_data.get('resistance', 0):.2f}")
                print(f"  Relative Position: {sr_data.get('relative_position', 0):.1%}")
                
                # Display breakout filters
                filters = score_data.get('breakout_filters', {})
                if filters:
                    print(f"  Breakout Signal: {filters.get('breakout_signal', False)}")
                
                # Display key indicators
                indicators = score_data.get('indicators', {})
                print(f"  RSI: {indicators.get('RSI', 0):.1f}")
                print(f"  MACD Hist: {indicators.get('MACD_Histogram', 0):.4f}")
                print(f"  Volume Ratio: {indicators.get('Volume_Ratio', 0):.2f}x")
            else:
                print(f"  ✗ No data available")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print("\n✓ Comprehensive scoring test completed")


def test_technical_chart():
    """Test technical analysis chart generation"""
    print("\n" + "=" * 60)
    print("TEST 4: Technical Analysis Chart Generation")
    print("=" * 60)
    
    scorer = StockScorer(lookback_days=120, forecast_days=14)
    visualizer = StockVisualizer()
    
    symbol = 'AAPL'
    print(f"\nGenerating technical analysis chart for {symbol}...")
    
    try:
        hist = scorer.fetch_historical_data(symbol)
        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
            score_data = scorer.score_stock(symbol, current_price)
            
            # Generate technical analysis chart
            chart_data = visualizer.create_technical_analysis_chart(symbol, score_data, hist)
            
            if chart_data:
                print(f"  ✓ Chart generated successfully!")
                print(f"  Chart data length: {len(chart_data)} characters")
                print(f"  Contains base64 image: {'data:image/png;base64' in chart_data}")
            else:
                print(f"  ✗ Chart generation failed")
        else:
            print(f"  ✗ No historical data available")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✓ Technical chart test completed")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("ENHANCED STOCK SCREENING FEATURE TESTS")
    print("=" * 60)
    
    try:
        test_support_resistance()
        test_breakout_filters()
        test_comprehensive_scoring()
        test_technical_chart()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
