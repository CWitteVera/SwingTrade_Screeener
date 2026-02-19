#!/usr/bin/env python3
"""
Test script to verify the support/resistance fixes
Tests:
1. Support and resistance are never identical (unless both 0.0)
2. Position filter correctly uses 75% threshold
3. Minimum 30 days of data is required
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import pandas as pd
import numpy as np
from scoring_system import StockScorer


def test_support_resistance_not_matching():
    """Test that support and resistance are never identical when data is available"""
    print("=" * 60)
    print("TEST 1: Support/Resistance Should Not Match")
    print("=" * 60)
    
    scorer = StockScorer()
    
    # Create mock historical data with varying prices (50 days)
    dates = pd.date_range(end=pd.Timestamp.now(), periods=50, freq='D')
    prices = [100 + i * 0.5 + np.random.random() * 2 for i in range(50)]
    
    hist_data = pd.DataFrame({
        'Close': prices,
        'High': [p + 1 for p in prices],
        'Low': [p - 1 for p in prices],
        'Volume': [1000000 + np.random.randint(0, 500000) for _ in range(50)]
    }, index=dates)
    
    support, resistance = scorer.calculate_support_resistance(hist_data, period=90)
    
    print(f"Historical data: {len(hist_data)} days")
    print(f"Support: ${support:.2f}")
    print(f"Resistance: ${resistance:.2f}")
    
    # Test 1: Support and resistance should NOT be identical
    if support == resistance and support != 0.0:
        print(f"❌ FAIL: Support and resistance are identical (${support:.2f})")
        return False
    elif support != resistance:
        print(f"✅ PASS: Support and resistance are different")
    else:
        print(f"⚠️  Both are 0.0 (insufficient data)")
    
    # Test 2: Support should be less than resistance
    if support > 0 and resistance > 0:
        if support < resistance:
            print(f"✅ PASS: Support (${support:.2f}) < Resistance (${resistance:.2f})")
        else:
            print(f"❌ FAIL: Support should be less than resistance")
            return False
    
    return True


def test_minimum_data_requirement():
    """Test that minimum 30 days of data is required"""
    print("\n" + "=" * 60)
    print("TEST 2: Minimum Data Requirement (30 days)")
    print("=" * 60)
    
    scorer = StockScorer()
    
    # Test with 29 days (insufficient)
    dates_29 = pd.date_range(end=pd.Timestamp.now(), periods=29, freq='D')
    hist_29 = pd.DataFrame({
        'Close': [100 + i for i in range(29)],
        'High': [101 + i for i in range(29)],
        'Low': [99 + i for i in range(29)]
    }, index=dates_29)
    
    support_29, resistance_29 = scorer.calculate_support_resistance(hist_29, period=90)
    
    print(f"\nWith 29 days of data:")
    print(f"  Support: {support_29}, Resistance: {resistance_29}")
    if support_29 == 0.0 and resistance_29 == 0.0:
        print(f"  ✅ PASS: Returns (0.0, 0.0) for insufficient data")
    else:
        print(f"  ❌ FAIL: Should return (0.0, 0.0) for < 30 days")
        return False
    
    # Test with 30 days (sufficient)
    dates_30 = pd.date_range(end=pd.Timestamp.now(), periods=30, freq='D')
    hist_30 = pd.DataFrame({
        'Close': [100 + i for i in range(30)],
        'High': [101 + i for i in range(30)],
        'Low': [99 + i for i in range(30)]
    }, index=dates_30)
    
    support_30, resistance_30 = scorer.calculate_support_resistance(hist_30, period=90)
    
    print(f"\nWith 30 days of data:")
    print(f"  Support: {support_30:.2f}, Resistance: {resistance_30:.2f}")
    if support_30 > 0 and resistance_30 > 0 and support_30 != resistance_30:
        print(f"  ✅ PASS: Returns valid support/resistance with 30+ days")
    else:
        print(f"  ❌ FAIL: Should return valid values for 30+ days")
        return False
    
    return True


def test_position_filter_75_percent():
    """Test that position filter correctly uses 75% threshold"""
    print("\n" + "=" * 60)
    print("TEST 3: Position Filter (40%-75%)")
    print("=" * 60)
    
    scorer = StockScorer()
    
    # Test cases: (current_price, support, resistance, expected_result, description)
    # Formula: relative_pos = (current - support) / (resistance - support)
    # For support=100, resistance=200, range is 100
    # 40% = 100 + 40 = 140
    # 75% = 100 + 75 = 175
    test_cases = [
        (150, 100, 200, True, "50% position - should pass"),      # (150-100)/(200-100) = 50% - should pass
        (170, 100, 200, True, "70% position - should pass"),      # (170-100)/(200-100) = 70% - should pass
        (175, 100, 200, True, "75% position - should pass"),      # (175-100)/(200-100) = 75% - should pass (edge case)
        (180, 100, 200, False, "80% position - should fail"),     # (180-100)/(200-100) = 80% - should fail (too close to resistance)
        (140, 100, 200, True, "40% position - should pass"),      # (140-100)/(200-100) = 40% - should pass (edge case)
        (135, 100, 200, False, "35% position - should fail"),     # (135-100)/(200-100) = 35% - should fail (too close to support)
    ]
    
    all_passed = True
    for current, support, resistance, expected, description in test_cases:
        filters = scorer.check_breakout_filters(
            current_price=current,
            support=support,
            resistance=resistance,
            volume_ratio=2.0,  # Above 1.5
            rsi=60,            # In 50-70 range
            macd_hist=0.1,     # Positive
            macd=0.5,
            macd_signal=0.4    # MACD > signal
        )
        
        relative_pos = scorer.calculate_relative_position(current, support, resistance)
        result = filters['position_favorable']
        
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"  {status}: {description}")
        print(f"    Price: ${current}, Support: ${support}, Resistance: ${resistance}")
        print(f"    Relative position: {relative_pos:.1%}, Filter: {result}")
        
        if result != expected:
            all_passed = False
    
    return all_passed


def test_uses_available_data():
    """Test that the function uses available data even if less than requested period"""
    print("\n" + "=" * 60)
    print("TEST 4: Uses Available Data (< 90 days but >= 30)")
    print("=" * 60)
    
    scorer = StockScorer()
    
    # Create 60 days of data (less than 90 but more than 30)
    dates = pd.date_range(end=pd.Timestamp.now(), periods=60, freq='D')
    prices = [100 + i * 0.5 for i in range(60)]
    
    hist_data = pd.DataFrame({
        'Close': prices,
        'High': [p + 2 for p in prices],
        'Low': [p - 2 for p in prices],
    }, index=dates)
    
    support, resistance = scorer.calculate_support_resistance(hist_data, period=90)
    
    print(f"Data available: 60 days (requested: 90 days)")
    print(f"Support: ${support:.2f}")
    print(f"Resistance: ${resistance:.2f}")
    
    # Should use available data
    expected_support = min([p - 2 for p in prices])
    expected_resistance = max([p + 2 for p in prices])
    
    if abs(support - expected_support) < 0.01 and abs(resistance - expected_resistance) < 0.01:
        print(f"✅ PASS: Uses all available 60 days")
        print(f"  Expected support: ${expected_support:.2f}, Got: ${support:.2f}")
        print(f"  Expected resistance: ${expected_resistance:.2f}, Got: ${resistance:.2f}")
        return True
    else:
        print(f"❌ FAIL: Not using available data correctly")
        print(f"  Expected support: ${expected_support:.2f}, Got: ${support:.2f}")
        print(f"  Expected resistance: ${expected_resistance:.2f}, Got: ${resistance:.2f}")
        return False


if __name__ == '__main__':
    print("\n🧪 Running Support/Resistance Fix Tests\n")
    
    results = []
    results.append(("Support/Resistance Not Matching", test_support_resistance_not_matching()))
    results.append(("Minimum Data Requirement", test_minimum_data_requirement()))
    results.append(("Position Filter 75%", test_position_filter_75_percent()))
    results.append(("Uses Available Data", test_uses_available_data()))
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
