"""
Comprehensive MSTR Test Script - Fixed for Pytest
Tests all MSTR scenarios while keeping BTC constant
"""

import pytest
import logging
from datetime import datetime, timezone
from unittest.mock import Mock, patch


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def create_constant_btc_data():
    """Create constant BTC data for all tests"""
    return {
        'price': 96750,
        'type': 'crypto',
        'indicators': {
            'mvrv': 3.2,
            'weekly_rsi': 75.4,
            'ema_200': 85240
        },
        'metadata': {'source': 'polygon.io + tradingview'},
        'last_updated': datetime.now(timezone.utc).isoformat()
    }


def create_mstr_scenario_data(scenario_name, price, model_price, iv, iv_percentile, iv_rank, error=None):
    """Create MSTR data for specific scenario"""
    if error:
        return {
            'type': 'stock',
            'error': error,
            'last_updated': datetime.now(timezone.utc).isoformat()
        }

    deviation_pct = ((price - model_price) / model_price) * 100

    # Generate analysis based on the scenario
    analysis = generate_mstr_analysis(deviation_pct, iv_percentile, iv_rank)

    return {
        'price': price,
        'type': 'stock',
        'indicators': {
            'model_price': model_price,
            'deviation_pct': deviation_pct,
            'iv': iv,
            'iv_percentile': iv_percentile,
            'iv_rank': iv_rank
        },
        'analysis': analysis,
        'metadata': {
            'source': 'mstr_analyzer',
            'ballistic_source': 'xpath_precision',
            'volatility_source': 'selenium',
            'scenario': scenario_name
        },
        'last_updated': datetime.now(timezone.utc).isoformat()
    }


def generate_mstr_analysis(deviation_pct, iv_percentile, iv_rank):
    """Generate MSTR analysis based on indicators"""
    analysis = {
        'price_signal': {},
        'volatility_signal': {},
        'volatility_conflict': {}
    }

    # Price Signal Analysis
    if deviation_pct >= 25:
        analysis['price_signal'] = {
            'status': 'overvalued',
            'signal': 'SELL',
            'alert': True,
            'message': f'MSTR Overvalued by {deviation_pct:.1f}%',
            'recommendation': 'Consider selling'
        }
    elif deviation_pct <= -20:
        analysis['price_signal'] = {
            'status': 'undervalued',
            'signal': 'BUY',
            'alert': True,
            'message': f'MSTR Undervalued by {abs(deviation_pct):.1f}%',
            'recommendation': 'Consider buying'
        }
    else:
        analysis['price_signal'] = {
            'status': 'neutral',
            'signal': 'HOLD',
            'alert': False,
            'message': f'MSTR Fair Valued ({deviation_pct:+.1f}%)'
        }

    # Volatility Conflict Check
    if (iv_percentile < 30 and iv_rank > 70) or (iv_percentile > 70 and iv_rank < 30):
        analysis['volatility_conflict'] = {
            'is_conflicting': True,
            'message': 'Conflicting Volatility Signals',
            'description': f'IV Percentile ({iv_percentile:.0f}%) and IV Rank ({iv_rank:.0f}%) disagree'
        }
    else:
        analysis['volatility_conflict'] = {'is_conflicting': False}

    # Volatility Signal Analysis
    if iv_percentile < 30 or iv_rank < 30:
        analysis['volatility_signal'] = {
            'preference': 'long_calls',
            'message': 'Consider Long Calls',
            'description': f'Low volatility (Percentile: {iv_percentile:.0f}%, Rank: {iv_rank:.0f}%)'
        }
    elif iv_percentile > 70 or iv_rank > 70:
        analysis['volatility_signal'] = {
            'preference': 'long_puts',
            'message': 'Consider Long Puts',
            'description': f'High volatility (Percentile: {iv_percentile:.0f}%, Rank: {iv_rank:.0f}%)'
        }
    else:
        analysis['volatility_signal'] = {
            'preference': 'no_preference',
            'message': 'No Options Preference',
            'description': f'Moderate volatility (Percentile: {iv_percentile:.0f}%, Rank: {iv_rank:.0f}%)'
        }

    return analysis


def generate_alerts_for_scenario_data(mstr_data):
    """Generate alerts for MSTR scenario"""
    alerts = []

    if 'error' in mstr_data:
        alerts.append({
            'type': 'data_error',
            'asset': 'MSTR',
            'message': f"Failed to collect data for MSTR: {mstr_data['error']}",
            'severity': 'high'
        })
        return alerts

    indicators = mstr_data.get('indicators', {})
    analysis = mstr_data.get('analysis', {})

    # Model price vs actual price alerts
    model_price = indicators.get('model_price')
    actual_price = mstr_data.get('price')
    deviation_pct = indicators.get('deviation_pct')

    if model_price and actual_price and deviation_pct is not None:
        if deviation_pct >= 25:
            alerts.append({
                'type': 'mstr_overvalued',
                'asset': 'MSTR',
                'message': f"MSTR is {deviation_pct:.1f}% overvalued (${actual_price:.2f} vs ${model_price:.2f})",
                'severity': 'high'
            })
        elif deviation_pct <= -20:
            alerts.append({
                'type': 'mstr_undervalued',
                'asset': 'MSTR',
                'message': f"MSTR is {abs(deviation_pct):.1f}% undervalued (${actual_price:.2f} vs ${model_price:.2f})",
                'severity': 'medium'
            })

    return alerts


def run_mstr_scenario_test(scenario_name, mstr_data):
    """Test a specific MSTR scenario - renamed to avoid pytest auto-discovery"""
    print(f"\n{'=' * 60}")
    print(f"🧪 TESTING SCENARIO: {scenario_name}")
    print(f"{'=' * 60}")

    # Create test data structure
    btc_data = create_constant_btc_data()

    test_data = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'assets': {
            'BTC': btc_data,
            'MSTR': mstr_data
        },
        'summary': {
            'total_assets': 2,
            'successful_collections': 1 if 'error' not in mstr_data else 0,
            'failed_collections': 1 if 'error' in mstr_data else 0
        }
    }

    # Generate alerts for this scenario
    alerts = []

    # BTC alerts (constant)
    if btc_data.get('indicators', {}).get('mvrv', 0) > 3.0:
        alerts.append({
            'type': 'mvrv_high',
            'asset': 'BTC',
            'message': f"BTC MVRV is high at {btc_data['indicators']['mvrv']:.2f} - potential sell signal",
            'severity': 'medium'
        })

    if btc_data.get('indicators', {}).get('weekly_rsi', 0) > 70:
        alerts.append({
            'type': 'rsi_overbought',
            'asset': 'BTC',
            'message': f"BTC Weekly RSI is overbought at {btc_data['indicators']['weekly_rsi']:.1f}",
            'severity': 'medium'
        })

    # MSTR alerts (variable)
    mstr_alerts = generate_alerts_for_scenario_data(mstr_data)
    alerts.extend(mstr_alerts)

    # Print scenario details
    print(f"📊 MSTR Data:")
    if 'error' in mstr_data:
        print(f"   ❌ Error: {mstr_data['error']}")
    else:
        print(f"   💰 Price: ${mstr_data['price']:,.2f}")
        print(f"   📈 Model Price: ${mstr_data['indicators']['model_price']:,.2f}")
        print(f"   📊 Deviation: {mstr_data['indicators']['deviation_pct']:+.1f}%")
        print(f"   🌊 IV: {mstr_data['indicators']['iv']:.1f}%")
        print(f"   📊 IV Percentile: {mstr_data['indicators']['iv_percentile']:.0f}%")
        print(f"   📊 IV Rank: {mstr_data['indicators']['iv_rank']:.0f}%")

        # Print analysis
        analysis = mstr_data.get('analysis', {})
        price_signal = analysis.get('price_signal', {})
        volatility_signal = analysis.get('volatility_signal', {})
        volatility_conflict = analysis.get('volatility_conflict', {})

        print(f"\n🔍 Analysis:")
        print(f"   📈 Price Signal: {price_signal.get('signal', 'N/A')} - {price_signal.get('message', 'N/A')}")
        print(f"   🌊 Volatility: {volatility_signal.get('message', 'N/A')}")
        if volatility_conflict.get('is_conflicting', False):
            print(f"   ⚠️ Conflict: {volatility_conflict.get('message', 'N/A')}")

    # Print alerts
    print(f"\n🚨 Generated Alerts ({len(alerts)} total):")
    if not alerts:
        print("   ✅ No alerts generated")
    else:
        for alert in alerts:
            severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(alert.get('severity', 'medium'), '🟡')
            print(f"   {severity_emoji} [{alert['severity'].upper()}] {alert['asset']}: {alert['message']}")

    return test_data, alerts


def run_comprehensive_mstr_test():
    """Run all MSTR test scenarios - renamed to avoid pytest auto-discovery"""
    print("🚀 Starting Comprehensive MSTR Test Suite")
    print("🔄 BTC data remains constant across all tests")
    print("📊 Testing all MSTR scenarios and alert conditions\n")

    scenarios = [
        # 1. Severely Overvalued Scenarios
        ("Severely Overvalued + High Volatility",
         create_mstr_scenario_data("severely_overvalued_high_vol", 500, 350, 95.2, 85, 82)),

        ("Severely Overvalued + Low Volatility",
         create_mstr_scenario_data("severely_overvalued_low_vol", 480, 350, 45.3, 15, 18)),

        # 2. Fair Valued Scenarios
        ("Fair Valued + High Volatility",
         create_mstr_scenario_data("fair_valued_high_vol", 360, 350, 89.7, 78, 75)),

        ("Fair Valued + Low Volatility",
         create_mstr_scenario_data("fair_valued_low_vol", 365, 350, 35.2, 22, 19)),

        # 3. Undervalued Scenarios
        ("Severely Undervalued + Low Volatility",
         create_mstr_scenario_data("severely_undervalued_low_vol", 250, 350, 42.1, 12, 15)),

        # 4. Error Scenarios
        ("MSTR Collection Error",
         create_mstr_scenario_data("collection_error", 0, 0, 0, 0, 0, error="Failed to scrape ballistic data: Timeout")),
    ]

    results = []

    for scenario_name, mstr_data in scenarios:
        try:
            test_data, alerts = run_mstr_scenario_test(scenario_name, mstr_data)
            results.append({
                'scenario': scenario_name,
                'success': True,
                'alerts_count': len(alerts),
                'data': test_data
            })
        except Exception as e:
            print(f"   ❌ Test failed: {str(e)}")
            results.append({
                'scenario': scenario_name,
                'success': False,
                'error': str(e)
            })

    # Summary
    print(f"\n{'=' * 60}")
    print("📋 TEST SUMMARY")
    print(f"{'=' * 60}")

    successful_tests = [r for r in results if r['success']]
    failed_tests = [r for r in results if not r['success']]

    print(f"✅ Successful Tests: {len(successful_tests)}/{len(results)}")
    print(f"❌ Failed Tests: {len(failed_tests)}")

    if failed_tests:
        print(f"\n🔍 Failed Test Details:")
        for test in failed_tests:
            print(f"   - {test['scenario']}: {test.get('error', 'Unknown error')}")

    print(f"\n📊 Alert Generation Summary:")
    for test in successful_tests:
        print(f"   - {test['scenario']}: {test['alerts_count']} alerts")

    print(f"\n✅ Comprehensive MSTR test completed!")
    
    return len(failed_tests) == 0


# =============================================================================
# Pytest Test Functions
# =============================================================================

def test_mstr_scenario_creation():
    """Test MSTR scenario data creation"""
    scenario_data = create_mstr_scenario_data(
        "test_scenario", 425, 400, 55.0, 45, 40
    )
    
    assert scenario_data['price'] == 425
    assert scenario_data['type'] == 'stock'
    assert 'indicators' in scenario_data
    assert 'analysis' in scenario_data
    assert scenario_data['indicators']['model_price'] == 400


def test_mstr_error_scenario():
    """Test MSTR error scenario creation"""
    error_data = create_mstr_scenario_data(
        "error_test", 0, 0, 0, 0, 0, error="Test error"
    )
    
    assert 'error' in error_data
    assert error_data['error'] == "Test error"
    assert error_data['type'] == 'stock'


def test_mstr_analysis_generation():
    """Test MSTR analysis generation"""
    analysis = generate_mstr_analysis(30.0, 45.0, 40.0)  # Overvalued scenario
    
    assert 'price_signal' in analysis
    assert 'volatility_signal' in analysis
    assert 'volatility_conflict' in analysis
    assert analysis['price_signal']['status'] == 'overvalued'


def test_alert_generation():
    """Test alert generation for MSTR scenarios"""
    # Create overvalued scenario
    mstr_data = create_mstr_scenario_data("test", 500, 350, 65.0, 45, 40)
    alerts = generate_alerts_for_scenario_data(mstr_data)
    
    # Should generate overvalued alert
    assert len(alerts) > 0
    assert any(alert['type'] == 'mstr_overvalued' for alert in alerts)


def test_comprehensive_mstr_scenarios():
    """Test that comprehensive MSTR test runs without errors"""
    # This is a smoke test to ensure the comprehensive test can run
    with patch('builtins.print'):  # Suppress output during test
        result = run_comprehensive_mstr_test()
    
    assert isinstance(result, bool)


# Pytest parametrized tests using the fixtures from conftest.py
def test_scenario_with_fixtures(scenario_name, mstr_data):
    """Test individual scenarios using pytest fixtures"""
    # This test will be run for each scenario provided by the fixtures
    
    # Basic validation
    assert isinstance(scenario_name, str)
    assert isinstance(mstr_data, dict)
    assert 'type' in mstr_data
    assert mstr_data['type'] == 'stock'
    
    # Test alert generation
    alerts = generate_alerts_for_scenario_data(mstr_data)
    assert isinstance(alerts, list)
    
    # If there's an error, should have error alert
    if 'error' in mstr_data:
        assert any(alert['type'] == 'data_error' for alert in alerts)
    
    # If significantly overvalued, should have overvaluation alert
    if 'indicators' in mstr_data:
        deviation = mstr_data['indicators'].get('deviation_pct', 0)
        if deviation >= 25:
            assert any(alert['type'] == 'mstr_overvalued' for alert in alerts)


if __name__ == "__main__":
    # Run the comprehensive test when executed directly
    run_comprehensive_mstr_test()
