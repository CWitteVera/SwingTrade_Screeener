#!/usr/bin/env python3
"""
Unit tests for enhanced stock screening features with mock data
Tests support/resistance, breakout filters, and technical analysis with synthetic data
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scoring_system import StockScorer
from visualizations import StockVisualizer
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def create_mock_stock_data(days=120, base_price=100, volatility=0.02):
    """Create mock stock data for testing"""
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    # Generate price data with random walk
    np.random.seed(42)
    returns = np.random.normal(0, volatility, days)
    prices = base_price * np.exp(np.cumsum(returns))
    
    # Create OHLCV data
    data = pd.DataFrame({
        'Open': prices * (1 + np.random.uniform(-0.01, 0.01, days)),
        'High': prices * (1 + np.random.uniform(0, 0.02, days)),
        'Low': prices * (1 - np.random.uniform(0, 0.02, days)),
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, days)
    }, index=dates)
    
    return data


def test_support_resistance_with_mock_data():
    """Test support and resistance calculation with mock data"""
    print("=" * 60)
    print("TEST 1: Support and Resistance Calculation (Mock Data)")
    print("=" * 60)
    
    scorer = StockScorer(lookback_days=120, forecast_days=14)
    
    # Create mock data
    hist = create_mock_stock_data(days=120, base_price=150)
    
    print("\nMock stock data:")
    print(f"  Data points: {len(hist)}")
    print(f"  Price range: ${hist['Close'].min():.2f} - ${hist['Close'].max():.2f}")
    
    # Calculate support and resistance
    support, resistance = scorer.calculate_support_resistance(hist, period=90)
    current_price = hist['Close'].iloc[-1]
    relative_pos = scorer.calculate_relative_position(current_price, support, resistance)
    
    print(f"\nResults:")
    print(f"  Current Price: ${current_price:.2f}")
    print(f"  Support (90d): ${support:.2f}")
    print(f"  Resistance (90d): ${resistance:.2f}")
    print(f"  Relative Position: {relative_pos:.1%}")
    
    # Verify calculations
    assert support > 0, "Support should be positive"
    assert resistance > support, "Resistance should be greater than support"
    assert 0 <= relative_pos <= 1, "Relative position should be between 0 and 1"
    
    if 0.4 <= relative_pos <= 0.75:
        print(f"  ✓ In favorable position range!")
    else:
        print(f"  ✗ Outside favorable range (40%-75%)")
    
    print("\n✓ Support/Resistance test PASSED")
    return True


def test_breakout_filters_with_mock_data():
    """Test breakout filter detection with mock data"""
    print("\n" + "=" * 60)
    print("TEST 2: Breakout Filter Detection (Mock Data)")
    print("=" * 60)
    
    scorer = StockScorer(lookback_days=120, forecast_days=14)
    
    # Create mock data with increasing volume (simulating breakout)
    hist = create_mock_stock_data(days=120, base_price=100)
    
    # Simulate volume spike in recent days - boost it more
    # Use 2.5x to ensure we exceed the 1.5x threshold with margin
    MOCK_VOLUME_SPIKE_MULTIPLIER = 2.5
    hist.loc[hist.index[-1:], 'Volume'] = hist['Volume'].iloc[-20:].mean() * MOCK_VOLUME_SPIKE_MULTIPLIER
    
    current_price = hist['Close'].iloc[-1]
    
    # Calculate all indicators
    rsi = scorer.calculate_rsi(hist['Close'])
    macd, macd_signal, macd_hist = scorer.calculate_macd(hist['Close'])
    volume_ratio = scorer.calculate_volume_trend(hist['Volume'])
    support, resistance = scorer.calculate_support_resistance(hist)
    
    print(f"\nIndicator values:")
    print(f"  RSI: {rsi:.1f}")
    print(f"  MACD Histogram: {macd_hist:.4f}")
    print(f"  MACD: {macd:.4f} vs Signal: {macd_signal:.4f}")
    print(f"  Volume Ratio: {volume_ratio:.2f}x")
    
    # Check filters
    filters = scorer.check_breakout_filters(
        current_price, support, resistance,
        volume_ratio, rsi, macd_hist, macd, macd_signal
    )
    
    print(f"\nFilter results:")
    print(f"  Volume Spike (≥1.5x): {filters['volume_spike']}")
    print(f"  RSI Momentum (50-70): {filters['rsi_momentum']}")
    print(f"  MACD Momentum: {filters['macd_momentum']}")
    print(f"  Position Favorable (40-75%): {filters['position_favorable']}")
    print(f"  Overall Breakout Signal: {filters['breakout_signal']}")
    
    # Verify the filters are working
    assert 'volume_spike' in filters
    assert 'rsi_momentum' in filters
    assert 'macd_momentum' in filters
    assert 'position_favorable' in filters
    assert 'breakout_signal' in filters
    
    # Check that the values make sense (should be True/False, could be numpy.bool_)
    assert filters['volume_spike'] in [True, False]
    assert filters['breakout_signal'] in [True, False]
    
    print("\n✓ Breakout filter test PASSED")
    return True


def test_comprehensive_scoring_with_mock_data():
    """Test comprehensive scoring with new features"""
    print("\n" + "=" * 60)
    print("TEST 3: Comprehensive Scoring (Mock Data)")
    print("=" * 60)
    
    scorer = StockScorer(lookback_days=120, forecast_days=14)
    
    # Create mock data
    hist = create_mock_stock_data(days=120, base_price=200)
    current_price = hist['Close'].iloc[-1]
    
    print(f"\nScoring stock with price: ${current_price:.2f}")
    
    # Mock the fetch_historical_data to use our mock data
    original_fetch = scorer.fetch_historical_data
    scorer.fetch_historical_data = lambda symbol: hist
    
    try:
        score_data = scorer.score_stock('MOCK', current_price)
        
        print(f"\nScoring results:")
        print(f"  Score: {score_data['score']:.2f}")
        print(f"  Probability: {score_data['probability']:.1f}%")
        
        # Verify score data structure
        assert 'score' in score_data, "Should have score"
        assert 'probability' in score_data, "Should have probability"
        assert 'indicators' in score_data, "Should have indicators"
        assert 'support_resistance' in score_data, "Should have support_resistance"
        assert 'breakout_filters' in score_data, "Should have breakout_filters"
        
        # Display support/resistance info
        sr_data = score_data['support_resistance']
        print(f"\nSupport/Resistance:")
        print(f"  Support: ${sr_data['support']:.2f}")
        print(f"  Resistance: ${sr_data['resistance']:.2f}")
        print(f"  Relative Position: {sr_data['relative_position']:.1%}")
        
        # Verify support/resistance structure
        assert 'support' in sr_data, "Should have support"
        assert 'resistance' in sr_data, "Should have resistance"
        assert 'relative_position' in sr_data, "Should have relative_position"
        assert sr_data['support'] > 0, "Support should be positive"
        assert sr_data['resistance'] > sr_data['support'], "Resistance > Support"
        
        # Display breakout filters
        filters = score_data['breakout_filters']
        print(f"\nBreakout Filters:")
        for key, value in filters.items():
            print(f"  {key}: {value}")
        
        # Verify breakout filters structure
        assert 'breakout_signal' in filters, "Should have breakout_signal"
        
        # Display key indicators
        indicators = score_data['indicators']
        print(f"\nKey Indicators:")
        print(f"  RSI: {indicators['RSI']:.1f}")
        print(f"  MACD Hist: {indicators['MACD_Histogram']:.4f}")
        print(f"  Volume Ratio: {indicators['Volume_Ratio']:.2f}x")
        print(f"  Support (90d): ${indicators['Support_90d']:.2f}")
        print(f"  Resistance (90d): ${indicators['Resistance_90d']:.2f}")
        print(f"  Relative Position: {indicators['Relative_Position']:.3f}")
        
        # Verify new indicators are present
        assert 'Support_90d' in indicators, "Should have Support_90d"
        assert 'Resistance_90d' in indicators, "Should have Resistance_90d"
        assert 'Relative_Position' in indicators, "Should have Relative_Position"
        
    finally:
        # Restore original method
        scorer.fetch_historical_data = original_fetch
    
    print("\n✓ Comprehensive scoring test PASSED")
    return True


def test_technical_chart_with_mock_data():
    """Test technical analysis chart generation with mock data"""
    print("\n" + "=" * 60)
    print("TEST 4: Technical Analysis Chart (Mock Data)")
    print("=" * 60)
    
    scorer = StockScorer(lookback_days=120, forecast_days=14)
    visualizer = StockVisualizer()
    
    # Create mock data
    hist = create_mock_stock_data(days=120, base_price=150)
    current_price = hist['Close'].iloc[-1]
    
    print(f"\nGenerating technical analysis chart...")
    print(f"  Mock data points: {len(hist)}")
    print(f"  Current price: ${current_price:.2f}")
    
    # Mock the fetch to use our data
    original_fetch = scorer.fetch_historical_data
    scorer.fetch_historical_data = lambda symbol: hist
    
    try:
        score_data = scorer.score_stock('MOCK', current_price)
        
        # Generate technical analysis chart
        chart_data = visualizer.create_technical_analysis_chart('MOCK', score_data, hist)
        
        if chart_data:
            print(f"\n✓ Chart generated successfully!")
            print(f"  Chart data length: {len(chart_data)} characters")
            print(f"  Contains base64 image: {'data:image/png;base64' in chart_data}")
            
            # Verify chart data
            assert chart_data.startswith('data:image/png;base64,'), "Should be base64 PNG"
            assert len(chart_data) > 1000, "Chart data should be substantial"
        else:
            print(f"  ✗ Chart generation failed")
            return False
            
    finally:
        scorer.fetch_historical_data = original_fetch
    
    print("\n✓ Technical chart test PASSED")
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("ENHANCED STOCK SCREENING UNIT TESTS (Mock Data)")
    print("=" * 60)
    
    tests = [
        test_support_resistance_with_mock_data,
        test_breakout_filters_with_mock_data,
        test_comprehensive_scoring_with_mock_data,
        test_technical_chart_with_mock_data,
    ]
    
    results = []
    
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 60)
    if all(results):
        print("ALL TESTS PASSED SUCCESSFULLY!")
        print("=" * 60)
        return 0
    else:
        print(f"SOME TESTS FAILED: {sum(results)}/{len(results)} passed")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
