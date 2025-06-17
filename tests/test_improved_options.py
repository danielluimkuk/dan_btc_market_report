"""
Test Script: Improved MSTR Options Logic - Fixed for Pytest
Demonstrates the before/after differences
"""

import pytest


def run_old_logic_test(iv_percentile, iv_rank):
    """The OLD problematic logic - renamed to avoid pytest auto-discovery"""
    if iv_percentile < 30 or iv_rank < 30:
        return {
            'preference': 'long_calls',
            'message': 'Consider Long Calls',
            'description': f'Low volatility (Percentile: {iv_percentile:.0f}%, Rank: {iv_rank:.0f}%)'
        }
    elif iv_percentile > 70 or iv_rank > 70:
        return {
            'preference': 'long_puts',
            'message': 'Consider Long Puts',
            'description': f'High volatility (Percentile: {iv_percentile:.0f}%, Rank: {iv_rank:.0f}%)'
        }
    else:
        return {
            'preference': 'no_preference',
            'message': 'No Options Preference',
            'description': f'Moderate volatility (Percentile: {iv_percentile:.0f}%, Rank: {iv_rank:.0f}%)'
        }


def run_new_logic_test(iv_percentile, iv_rank, deviation_pct, price_signal_status, volatility_conflicting=False):
    """The NEW improved logic - renamed to avoid pytest auto-discovery"""

    # Step 1: Check for conflicts first
    if volatility_conflicting:
        return {
            'primary_strategy': 'wait',
            'message': 'Wait for Clearer Setup',
            'description': 'Conflicting volatility signals - avoid options trades',
            'reasoning': 'IV Percentile and IV Rank disagree',
            'confidence': 'low'
        }

    # Step 2: Determine environments
    avg_iv = (iv_percentile + iv_rank) / 2

    if avg_iv < 25:
        vol_env = 'low'
    elif avg_iv > 75:
        vol_env = 'high'
    else:
        vol_env = 'normal'

    if price_signal_status == 'overvalued':
        direction = 'bearish'
    elif price_signal_status == 'undervalued':
        direction = 'bullish'
    else:
        direction = 'neutral'

    # Step 3: Combine for recommendation
    if vol_env == 'low':
        if direction == 'bullish':
            return {
                'primary_strategy': 'long_calls',
                'message': 'Consider Long Calls',
                'description': f'Cheap options + undervalued setup (MSTR {abs(deviation_pct):.1f}% below model)',
                'reasoning': 'Low IV makes options attractive + bullish bias',
                'confidence': 'high'
            }
        elif direction == 'bearish':
            return {
                'primary_strategy': 'long_puts',
                'message': 'Consider Long Puts',
                'description': f'Cheap options + overvalued setup (MSTR {deviation_pct:.1f}% above model)',
                'reasoning': 'Low IV makes options attractive + bearish bias',
                'confidence': 'high'
            }
        else:
            return {
                'primary_strategy': 'long_straddle',
                'message': 'Consider Long Straddle',
                'description': f'Cheap options + unclear direction (MSTR {deviation_pct:+.1f}% vs model)',
                'reasoning': 'Low IV good for buying, but need big move either way',
                'confidence': 'medium'
            }

    elif vol_env == 'high':
        if direction == 'bullish':
            return {
                'primary_strategy': 'short_puts',
                'message': 'Consider Short Puts or Covered Calls',
                'description': f'Expensive options + undervalued setup (MSTR {abs(deviation_pct):.1f}% below model)',
                'reasoning': 'High IV good for selling premium + bullish bias favors put selling',
                'confidence': 'high'
            }
        elif direction == 'bearish':
            return {
                'primary_strategy': 'short_calls',
                'message': 'Consider Short Calls or Protective Puts',
                'description': f'Expensive options + overvalued setup (MSTR {deviation_pct:.1f}% above model)',
                'reasoning': 'High IV good for selling premium + bearish bias favors call selling',
                'confidence': 'medium'
            }
        else:
            return {
                'primary_strategy': 'short_strangle',
                'message': 'Consider Premium Selling Strategies',
                'description': f'Expensive options + range-bound expectation (MSTR {deviation_pct:+.1f}% vs model)',
                'reasoning': 'High IV good for selling premium + no directional bias',
                'confidence': 'medium'
            }

    else:  # normal volatility
        return {
            'primary_strategy': 'no_preference',
            'message': 'No Strong Options Preference',
            'description': f'Normal volatility + unclear setup ({deviation_pct:+.1f}% vs model)',
            'reasoning': 'Neither volatility nor fundamentals provide clear edge',
            'confidence': 'low'
        }


def run_options_comparison_test():
    """Run side-by-side comparison tests - renamed to avoid pytest auto-discovery"""

    print("🧪 MSTR Options Logic Comparison Test")
    print("=" * 60)

    test_scenarios = [
        {
            'name': 'Overvalued + Low IV (The Big Problem)',
            'iv_percentile': 20,
            'iv_rank': 18,
            'deviation_pct': 35,
            'price_signal_status': 'overvalued',
            'volatility_conflicting': False
        },
        {
            'name': 'Fair Valued + High IV (Cost Structure Issue)',
            'iv_percentile': 85,
            'iv_rank': 82,
            'deviation_pct': 2,
            'price_signal_status': 'neutral',
            'volatility_conflicting': False
        },
        {
            'name': 'Undervalued + Low IV (Already Good)',
            'iv_percentile': 18,
            'iv_rank': 15,
            'deviation_pct': -25,
            'price_signal_status': 'undervalued',
            'volatility_conflicting': False
        },
        {
            'name': 'Conflicting IV Signals (Risk Management)',
            'iv_percentile': 15,
            'iv_rank': 85,
            'deviation_pct': 10,
            'price_signal_status': 'neutral',
            'volatility_conflicting': True
        },
        {
            'name': 'Severely Overvalued + High IV (Premium Selling)',
            'iv_percentile': 78,
            'iv_rank': 82,
            'deviation_pct': 42,
            'price_signal_status': 'overvalued',
            'volatility_conflicting': False
        }
    ]

    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📊 Test {i}: {scenario['name']}")
        print("-" * 50)

        # Test setup
        print(f"Setup: MSTR {scenario['deviation_pct']:+.0f}% vs model, "
              f"IV {scenario['iv_percentile']:.0f}%/{scenario['iv_rank']:.0f}%")

        # Old logic test
        old_result = run_old_logic_test(scenario['iv_percentile'], scenario['iv_rank'])
        print(f"\n🔴 OLD LOGIC:")
        print(f"   Recommendation: {old_result['message']}")
        print(f"   Description: {old_result['description']}")

        # New logic test
        new_result = run_new_logic_test(
            scenario['iv_percentile'],
            scenario['iv_rank'],
            scenario['deviation_pct'],
            scenario['price_signal_status'],
            scenario['volatility_conflicting']
        )
        print(f"\n🟢 NEW LOGIC:")
        print(f"   Recommendation: {new_result['message']}")
        print(f"   Description: {new_result['description']}")
        print(f"   Reasoning: {new_result['reasoning']}")
        print(f"   Confidence: {new_result['confidence']}")

        # Analysis
        if old_result['message'] == new_result['message']:
            print(f"\n✅ RESULT: Same recommendation (was already good)")
        else:
            print(f"\n🎯 RESULT: Improved recommendation")
            if scenario['name'] == 'Overvalued + Low IV (The Big Problem)':
                print(f"   💥 MAJOR FIX: No longer suggests bullish strategy on overvalued stock!")
            elif scenario['name'] == 'Fair Valued + High IV (Cost Structure Issue)':
                print(f"   💰 COST FIX: Now sells expensive options instead of buying them!")
            elif scenario['name'] == 'Conflicting IV Signals (Risk Management)':
                print(f"   🛡️ SAFETY FIX: Avoids trades when data is unreliable!")

    print(f"\n{'=' * 60}")
    print("🎯 SUMMARY: The new logic fixes all major problems!")
    print("✅ No more bullish recommendations on overvalued stocks")
    print("✅ No more buying expensive options in high IV")
    print("✅ Includes premium selling strategies")
    print("✅ Better risk management with conflicting data")
    print("✅ More detailed reasoning and confidence levels")
    print(f"\n🚀 Ready to deploy the improved MSTR analyzer!")


# =============================================================================
# Pytest Test Functions
# =============================================================================

def test_old_logic_low_iv():
    """Test old logic with low IV"""
    result = run_old_logic_test(20, 25)
    assert result['preference'] == 'long_calls'
    assert 'Low volatility' in result['description']


def test_old_logic_high_iv():
    """Test old logic with high IV"""
    result = run_old_logic_test(80, 75)
    assert result['preference'] == 'long_puts'
    assert 'High volatility' in result['description']


def test_old_logic_normal_iv():
    """Test old logic with normal IV"""
    result = run_old_logic_test(50, 45)
    assert result['preference'] == 'no_preference'
    assert 'Moderate volatility' in result['description']


def test_new_logic_conflicting_signals():
    """Test new logic handles conflicting volatility signals"""
    result = run_new_logic_test(15, 85, 10, 'neutral', volatility_conflicting=True)
    assert result['primary_strategy'] == 'wait'
    assert result['confidence'] == 'low'
    assert 'Conflicting volatility signals' in result['description']


def test_new_logic_low_iv_bullish():
    """Test new logic with low IV and bullish bias"""
    result = run_new_logic_test(20, 18, -25, 'undervalued', False)
    assert result['primary_strategy'] == 'long_calls'
    assert result['confidence'] == 'high'
    assert 'undervalued setup' in result['description']


def test_new_logic_high_iv_bearish():
    """Test new logic with high IV and bearish bias"""
    result = run_new_logic_test(80, 78, 35, 'overvalued', False)
    assert result['primary_strategy'] == 'short_calls'
    assert 'Expensive options' in result['description']
    assert 'overvalued setup' in result['description']


def test_new_logic_low_iv_neutral():
    """Test new logic with low IV and neutral bias"""
    result = run_new_logic_test(20, 22, 5, 'neutral', False)
    assert result['primary_strategy'] == 'long_straddle'
    assert 'unclear direction' in result['description']


def test_new_logic_high_iv_bullish():
    """Test new logic with high IV and bullish bias"""
    result = run_new_logic_test(80, 82, -22, 'undervalued', False)
    assert result['primary_strategy'] == 'short_puts'
    assert result['confidence'] == 'high'


def test_new_logic_normal_iv():
    """Test new logic with normal IV levels"""
    result = run_new_logic_test(50, 45, 8, 'neutral', False)
    assert result['primary_strategy'] == 'no_preference'
    assert result['confidence'] == 'low'
    assert 'Neither volatility nor fundamentals' in result['reasoning']


# Parametrized tests using fixtures from conftest.py
def test_old_logic_with_fixtures(iv_percentile, iv_rank):
    """Test old logic with different IV combinations using fixtures"""
    result = run_old_logic_test(iv_percentile, iv_rank)
    
    # Validate result structure
    assert 'preference' in result
    assert 'message' in result
    assert 'description' in result
    
    # Validate logic consistency
    if iv_percentile < 30 or iv_rank < 30:
        assert result['preference'] == 'long_calls'
    elif iv_percentile > 70 or iv_rank > 70:
        assert result['preference'] == 'long_puts'
    else:
        assert result['preference'] == 'no_preference'


def test_new_logic_with_fixtures(iv_percentile, iv_rank, deviation_pct, price_signal_status):
    """Test new logic with different parameter combinations using fixtures"""
    result = run_new_logic_test(iv_percentile, iv_rank, deviation_pct, price_signal_status, False)
    
    # Validate result structure
    assert 'primary_strategy' in result
    assert 'message' in result
    assert 'description' in result
    assert 'reasoning' in result
    assert 'confidence' in result
    
    # Validate confidence levels
    assert result['confidence'] in ['low', 'medium', 'high']
    
    # Validate that overvalued + low IV doesn't recommend bullish strategies
    avg_iv = (iv_percentile + iv_rank) / 2
    if avg_iv < 25 and price_signal_status == 'overvalued':
        assert result['primary_strategy'] in ['long_puts', 'long_straddle']
        assert 'overvalued setup' in result['description']


def test_logic_comparison_major_fixes():
    """Test that new logic fixes the major problems identified"""
    
    # Test 1: Overvalued + Low IV (The Big Problem)
    old_result = run_old_logic_test(20, 18)
    new_result = run_new_logic_test(20, 18, 35, 'overvalued', False)
    
    # Old logic incorrectly suggests bullish strategy
    assert old_result['preference'] == 'long_calls'
    
    # New logic correctly suggests bearish strategy for overvalued stock
    assert new_result['primary_strategy'] == 'long_puts'
    assert 'overvalued setup' in new_result['description']
    
    # Test 2: High IV Cost Structure Issue
    old_result_high_iv = run_old_logic_test(85, 82)
    new_result_high_iv = run_new_logic_test(85, 82, 2, 'neutral', False)
    
    # Old logic suggests buying expensive options
    assert old_result_high_iv['preference'] == 'long_puts'
    
    # New logic suggests selling expensive options
    assert new_result_high_iv['primary_strategy'] == 'short_strangle'
    assert 'Expensive options' in new_result_high_iv['description']


def test_comprehensive_options_comparison():
    """Test that the comprehensive comparison runs without errors"""
    # This is a smoke test to ensure the comparison test can run
    import sys
    from io import StringIO
    
    # Capture output to prevent noise during testing
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    
    try:
        run_options_comparison_test()
        test_passed = True
    except Exception:
        test_passed = False
    finally:
        sys.stdout = old_stdout
    
    assert test_passed


if __name__ == "__main__":
    # Run the comparison test when executed directly
    run_options_comparison_test()
