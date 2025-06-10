# =============================================================================
# test_function_app.py - Comprehensive Unit Tests for Azure Function App
# =============================================================================

import unittest
from unittest.mock import Mock, patch, MagicMock
import pytest
import json
from datetime import datetime, timezone
import azure.functions as func

# Import the module we're testing
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import functions from function_app.py
from function_app import (
    asset_monitor_timer,
    should_send_daily_report_enhanced,
    validate_btc_data_quality,
    validate_mstr_data_quality,
    process_asset_data,
    generate_alerts,
    generate_btc_alerts,
    generate_mstr_alerts
)


class TestFunctionApp(unittest.TestCase):
    """
    Comprehensive unit tests for the Azure Function App
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.sample_btc_data = {
            'success': True,
            'type': 'crypto',
            'price': 95000.50,
            'indicators': {
                'mvrv': 2.1,
                'weekly_rsi': 65.0,
                'ema_200': 88000.0
            },
            'metadata': {'source': 'polygon_api'},
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        self.sample_mstr_data = {
            'success': True,
            'type': 'stock',
            'price': 425.67,
            'indicators': {
                'model_price': 398.12,
                'deviation_pct': 6.9,
                'iv': 53.0,
                'iv_percentile': 35.0,
                'iv_rank': 42.0
            },
            'analysis': {
                'price_signal': {
                    'status': 'neutral',
                    'signal': 'HOLD',
                    'message': 'MSTR Fair Valued (+6.9%)'
                },
                'options_strategy': {
                    'primary_strategy': 'no_preference',
                    'message': 'No Strong Options Preference',
                    'description': 'Normal volatility + fair valuation'
                }
            },
            'metadata': {'source': 'mstr_analyzer'},
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        self.sample_monetary_data = {
            'success': True,
            'data_date': '2024-12-01',
            'days_old': 2,
            'fixed_rates': {
                'fed_funds': 5.25,
                'real_rate': 2.8
            },
            'table_data': [
                {
                    'metric': 'M2 Money Supply',
                    'monthly': '+0.2%',
                    'ytd': '+2.1%',
                    '1y': '+5.3%',
                    '10y': '+82.4%',
                    '20y': '+238.7%'
                }
            ],
            'true_inflation_rate': 6.2,
            'm2_20y_growth': 238.7
        }

    def tearDown(self):
        """Clean up after each test method."""
        pass


class TestDataValidation(TestFunctionApp):
    """Test data validation functions"""

    def test_validate_btc_data_quality_success(self):
        """Test BTC data validation with valid data"""
        result = validate_btc_data_quality(self.sample_btc_data)

        self.assertTrue(result['is_valid'])
        self.assertEqual(len(result['issues']), 0)

    def test_validate_btc_data_quality_missing_price(self):
        """Test BTC data validation with missing/invalid price"""
        invalid_data = self.sample_btc_data.copy()
        invalid_data['price'] = 0

        result = validate_btc_data_quality(invalid_data)

        self.assertFalse(result['is_valid'])
        self.assertIn('Invalid price: 0', ' '.join(result['issues']))

    def test_validate_btc_data_quality_with_error(self):
        """Test BTC data validation when data contains error"""
        error_data = {'error': 'API connection failed'}

        result = validate_btc_data_quality(error_data)

        self.assertFalse(result['is_valid'])
        self.assertIn('BTC has error: API connection failed', result['issues'])

    def test_validate_btc_data_quality_invalid_indicators(self):
        """Test BTC data validation with invalid technical indicators"""
        invalid_data = self.sample_btc_data.copy()
        invalid_data['indicators'] = {
            'mvrv': -1.0,  # Invalid MVRV
            'weekly_rsi': 0,  # Invalid RSI
            'ema_200': -5000  # Invalid EMA
        }

        result = validate_btc_data_quality(invalid_data)

        self.assertFalse(result['is_valid'])
        self.assertTrue(len(result['issues']) >= 3)

    def test_validate_mstr_data_quality_success(self):
        """Test MSTR data validation with valid data"""
        result = validate_mstr_data_quality(self.sample_mstr_data)

        self.assertTrue(result['is_valid'])
        self.assertEqual(len(result['issues']), 0)

    def test_validate_mstr_data_quality_collection_failed(self):
        """Test MSTR data validation when collection failed"""
        failed_data = {
            'success': False,
            'error': 'Scraping failed'
        }

        result = validate_mstr_data_quality(failed_data)

        self.assertFalse(result['is_valid'])
        self.assertIn('Collection failed: Scraping failed', result['issues'])

    def test_validate_mstr_data_quality_invalid_model_price(self):
        """Test MSTR data validation with invalid model price"""
        invalid_data = self.sample_mstr_data.copy()
        invalid_data['indicators']['model_price'] = 50000  # Unreasonable price

        result = validate_mstr_data_quality(invalid_data)

        self.assertFalse(result['is_valid'])
        self.assertIn('Invalid model price: 50000', ' '.join(result['issues']))


class TestReportDecisionLogic(TestFunctionApp):
    """Test the logic for deciding when to send daily reports"""

    def test_should_send_daily_report_all_success(self):
        """Test report sending when all components are successful"""
        processed_data = {
            'assets': {
                'BTC': self.sample_btc_data,
                'MSTR': self.sample_mstr_data
            }
        }
        collected_data = {
            'BTC': self.sample_btc_data,
            'MSTR': self.sample_mstr_data
        }
        screenshot = "base64encodedimagedata" * 100  # Simulate valid screenshot

        result = should_send_daily_report_enhanced(
            processed_data, collected_data, screenshot, self.sample_monetary_data
        )

        self.assertTrue(result['send'])
        self.assertIn('ALL components successful', result['reason'])

    def test_should_send_daily_report_btc_failed(self):
        """Test report decision when BTC collection fails"""
        failed_btc = self.sample_btc_data.copy()
        failed_btc['success'] = False
        failed_btc['error'] = 'API timeout'

        processed_data = {
            'assets': {
                'BTC': failed_btc,
                'MSTR': self.sample_mstr_data
            }
        }
        collected_data = {
            'BTC': failed_btc,
            'MSTR': self.sample_mstr_data
        }
        screenshot = "base64encodedimagedata" * 100

        result = should_send_daily_report_enhanced(
            processed_data, collected_data, screenshot, self.sample_monetary_data
        )

        self.assertFalse(result['send'])
        self.assertIn('Core components failed', result['reason'])
        self.assertIn('BTC collection failed', result['details'])

    def test_should_send_daily_report_no_screenshot(self):
        """Test report decision when Bitcoin Laws screenshot fails"""
        processed_data = {
            'assets': {
                'BTC': self.sample_btc_data,
                'MSTR': self.sample_mstr_data
            }
        }
        collected_data = {
            'BTC': self.sample_btc_data,
            'MSTR': self.sample_mstr_data
        }
        screenshot = ""  # Empty screenshot

        result = should_send_daily_report_enhanced(
            processed_data, collected_data, screenshot, self.sample_monetary_data
        )

        self.assertFalse(result['send'])
        self.assertIn('Bitcoin Laws screenshot failed/empty', result['details'])

    def test_should_send_daily_report_monetary_failed_but_proceed(self):
        """Test that core components still send report even if monetary data fails"""
        processed_data = {
            'assets': {
                'BTC': self.sample_btc_data,
                'MSTR': self.sample_mstr_data
            }
        }
        collected_data = {
            'BTC': self.sample_btc_data,
            'MSTR': self.sample_mstr_data
        }
        screenshot = "base64encodedimagedata" * 100

        # Monetary data failed
        failed_monetary = {
            'success': False,
            'error': 'FRED API rate limit'
        }

        result = should_send_daily_report_enhanced(
            processed_data, collected_data, screenshot, failed_monetary
        )

        # Should still send because core components (BTC + MSTR + screenshot) are successful
        self.assertTrue(result['send'])
        self.assertIn('Monetary data failed but proceeding', result['reason'])


class TestDataProcessing(TestFunctionApp):
    """Test data processing and structuring functions"""

    def test_process_asset_data_success(self):
        """Test processing of successful asset data collection"""
        collected_data = {
            'BTC': self.sample_btc_data,
            'MSTR': self.sample_mstr_data
        }

        result = process_asset_data(collected_data)

        # Check structure
        self.assertIn('timestamp', result)
        self.assertIn('assets', result)
        self.assertIn('summary', result)

        # Check summary
        self.assertEqual(result['summary']['total_assets'], 2)
        self.assertEqual(result['summary']['successful_collections'], 2)
        self.assertEqual(result['summary']['failed_collections'], 0)

        # Check BTC data processing
        btc_processed = result['assets']['BTC']
        self.assertEqual(btc_processed['type'], 'crypto')
        self.assertEqual(btc_processed['price'], 95000.50)
        self.assertIn('indicators', btc_processed)

        # Check MSTR data processing
        mstr_processed = result['assets']['MSTR']
        self.assertEqual(mstr_processed['type'], 'stock')
        self.assertEqual(mstr_processed['price'], 425.67)
        self.assertIn('analysis', mstr_processed)  # MSTR should include analysis

    def test_process_asset_data_with_failures(self):
        """Test processing when some asset collections fail"""
        failed_mstr = {
            'success': False,
            'type': 'stock',
            'error': 'Scraping timeout'
        }

        collected_data = {
            'BTC': self.sample_btc_data,
            'MSTR': failed_mstr
        }

        result = process_asset_data(collected_data)

        # Check summary reflects the failure
        self.assertEqual(result['summary']['successful_collections'], 1)
        self.assertEqual(result['summary']['failed_collections'], 1)

        # Check failed asset has error info
        mstr_processed = result['assets']['MSTR']
        self.assertIn('error', mstr_processed)
        self.assertEqual(mstr_processed['error'], 'Scraping timeout')


class TestAlertGeneration(TestFunctionApp):
    """Test alert generation logic"""

    def test_generate_btc_alerts_high_mvrv(self):
        """Test BTC alert generation for high MVRV"""
        btc_data_high_mvrv = self.sample_btc_data.copy()
        btc_data_high_mvrv['indicators']['mvrv'] = 3.5

        mock_storage = Mock()
        alerts = generate_btc_alerts(btc_data_high_mvrv, mock_storage)

        # Should generate MVRV high alert
        mvrv_alerts = [a for a in alerts if a['type'] == 'mvrv_high']
        self.assertEqual(len(mvrv_alerts), 1)
        self.assertIn('sell signal', mvrv_alerts[0]['message'].lower())

    def test_generate_btc_alerts_low_mvrv(self):
        """Test BTC alert generation for low MVRV"""
        btc_data_low_mvrv = self.sample_btc_data.copy()
        btc_data_low_mvrv['indicators']['mvrv'] = 0.8

        mock_storage = Mock()
        alerts = generate_btc_alerts(btc_data_low_mvrv, mock_storage)

        # Should generate MVRV low alert
        mvrv_alerts = [a for a in alerts if a['type'] == 'mvrv_low']
        self.assertEqual(len(mvrv_alerts), 1)
        self.assertIn('buy opportunity', mvrv_alerts[0]['message'].lower())

    def test_generate_btc_alerts_overbought_rsi(self):
        """Test BTC alert generation for overbought RSI"""
        btc_data_high_rsi = self.sample_btc_data.copy()
        btc_data_high_rsi['indicators']['weekly_rsi'] = 75.0

        mock_storage = Mock()
        alerts = generate_btc_alerts(btc_data_high_rsi, mock_storage)

        # Should generate RSI overbought alert
        rsi_alerts = [a for a in alerts if a['type'] == 'rsi_overbought']
        self.assertEqual(len(rsi_alerts), 1)
        self.assertIn('overbought', rsi_alerts[0]['message'].lower())

    def test_generate_mstr_alerts_overvalued(self):
        """Test MSTR alert generation for overvaluation"""
        mstr_data_overvalued = self.sample_mstr_data.copy()
        mstr_data_overvalued['indicators']['deviation_pct'] = 30.0
        mstr_data_overvalued['price'] = 500.0

        mock_storage = Mock()
        alerts = generate_mstr_alerts(mstr_data_overvalued, mock_storage)

        # Should generate overvalued alert
        overvalued_alerts = [a for a in alerts if a['type'] == 'mstr_overvalued']
        self.assertEqual(len(overvalued_alerts), 1)
        self.assertIn('overvalued', overvalued_alerts[0]['message'].lower())

    def test_generate_alerts_with_error_data(self):
        """Test alert generation when asset data contains errors"""
        processed_data = {
            'assets': {
                'BTC': {'error': 'API connection failed'},
                'MSTR': self.sample_mstr_data
            }
        }

        mock_storage = Mock()
        alerts = generate_alerts(processed_data, mock_storage)

        # Should generate data error alert for BTC
        error_alerts = [a for a in alerts if a['type'] == 'data_error' and a['asset'] == 'BTC']
        self.assertEqual(len(error_alerts), 1)
        self.assertIn('Failed to collect data for BTC', error_alerts[0]['message'])


class TestTimerTriggerIntegration(TestFunctionApp):
    """Test the main timer trigger function with mocked dependencies"""

    @patch('function_app.capture_bitcoin_laws_screenshot')
    @patch('function_app.MonetaryAnalyzer')
    @patch('function_app.collect_mstr_data_with_retry')
    @patch('function_app.AssetDataCollector')
    @patch('function_app.EnhancedNotificationHandler')
    @patch('function_app.DataStorage')
    def test_asset_monitor_timer_all_success(self, mock_storage, mock_notification,
                                             mock_collector, mock_mstr_collect,
                                             mock_monetary, mock_screenshot):
        """Test the main timer function when all components succeed"""

        # Setup mocks
        mock_timer = Mock(spec=func.TimerRequest)

        # Mock asset data collector
        mock_collector_instance = Mock()
        mock_collector_instance.collect_asset_data.return_value = self.sample_btc_data
        mock_collector.return_value = mock_collector_instance

        # Mock MSTR collection
        mock_mstr_collect.return_value = self.sample_mstr_data

        # Mock monetary analyzer
        mock_monetary_instance = Mock()
        mock_monetary_instance.get_monetary_analysis.return_value = self.sample_monetary_data
        mock_monetary.return_value = mock_monetary_instance

        # Mock Bitcoin Laws screenshot
        mock_screenshot.return_value = "base64encodedimagedata" * 100

        # Mock storage
        mock_storage_instance = Mock()
        mock_storage.return_value = mock_storage_instance

        # Mock notification handler
        mock_notification_instance = Mock()
        mock_notification.return_value = mock_notification_instance

        # Execute the function
        try:
            asset_monitor_timer(mock_timer)
        except Exception as e:
            self.fail(f"Timer function raised an exception: {e}")

        # Verify key interactions
        mock_collector_instance.collect_asset_data.assert_called()
        mock_mstr_collect.assert_called()
        mock_monetary_instance.get_monetary_analysis.assert_called()
        mock_screenshot.assert_called()
        mock_storage_instance.store_daily_data.assert_called()
        mock_notification_instance.send_daily_report.assert_called()

    @patch('function_app.capture_bitcoin_laws_screenshot')
    @patch('function_app.MonetaryAnalyzer')
    @patch('function_app.collect_mstr_data_with_retry')
    @patch('function_app.AssetDataCollector')
    @patch('function_app.EnhancedNotificationHandler')
    @patch('function_app.DataStorage')
    def test_asset_monitor_timer_btc_failure(self, mock_storage, mock_notification,
                                             mock_collector, mock_mstr_collect,
                                             mock_monetary, mock_screenshot):
        """Test the timer function when BTC collection fails"""

        # Setup mocks
        mock_timer = Mock(spec=func.TimerRequest)

        # Mock BTC collection failure
        mock_collector_instance = Mock()
        mock_collector_instance.collect_asset_data.return_value = {
            'success': False,
            'error': 'Polygon API timeout'
        }
        mock_collector.return_value = mock_collector_instance

        # Mock MSTR success
        mock_mstr_collect.return_value = self.sample_mstr_data

        # Mock monetary success
        mock_monetary_instance = Mock()
        mock_monetary_instance.get_monetary_analysis.return_value = self.sample_monetary_data
        mock_monetary.return_value = mock_monetary_instance

        # Mock screenshot success
        mock_screenshot.return_value = "base64encodedimagedata" * 100

        # Mock storage and notification
        mock_storage_instance = Mock()
        mock_storage.return_value = mock_storage_instance
        mock_notification_instance = Mock()
        mock_notification.return_value = mock_notification_instance

        # Execute the function
        asset_monitor_timer(mock_timer)

        # Should send error notification instead of daily report
        mock_notification_instance.send_error_notification.assert_called()
        mock_notification_instance.send_daily_report.assert_not_called()

    @patch('function_app.capture_bitcoin_laws_screenshot')
    @patch('function_app.MonetaryAnalyzer')
    @patch('function_app.collect_mstr_data_with_retry')
    @patch('function_app.AssetDataCollector')
    @patch('function_app.EnhancedNotificationHandler')
    @patch('function_app.DataStorage')
    def test_asset_monitor_timer_exception_handling(self, mock_storage, mock_notification,
                                                    mock_collector, mock_mstr_collect,
                                                    mock_monetary, mock_screenshot):
        """Test the timer function handles exceptions gracefully"""

        # Setup mocks
        mock_timer = Mock(spec=func.TimerRequest)

        # Mock an exception during collection
        mock_collector.side_effect = Exception("Unexpected error")

        # Mock notification handler for error reporting
        mock_notification_instance = Mock()
        mock_notification.return_value = mock_notification_instance

        # Execute the function - should not raise exception
        try:
            asset_monitor_timer(mock_timer)
        except Exception as e:
            self.fail(f"Timer function should handle exceptions gracefully but raised: {e}")

        # Should attempt to send error notification
        mock_notification_instance.send_error_notification.assert_called()


# =============================================================================
# Test Runner Configuration
# =============================================================================

class TestConfig:
    """Configuration for running tests in different environments"""

    @staticmethod
    def setup_azure_test_environment():
        """Setup test environment for Azure Functions"""
        # Set environment variables for testing
        os.environ.setdefault('POLYGON_API_KEY', 'test_key')
        os.environ.setdefault('EMAIL_USER', 'test@example.com')
        os.environ.setdefault('EMAIL_PASSWORD', 'test_password')
        os.environ.setdefault('RECIPIENT_EMAILS', 'test1@example.com,test2@example.com')
        os.environ.setdefault('AZURE_STORAGE_ACCOUNT', 'test_storage')
        os.environ.setdefault('AZURE_STORAGE_KEY', 'test_key')

    @staticmethod
    def cleanup_test_environment():
        """Clean up test environment"""
        test_env_vars = [
            'POLYGON_API_KEY', 'EMAIL_USER', 'EMAIL_PASSWORD',
            'RECIPIENT_EMAILS', 'AZURE_STORAGE_ACCOUNT', 'AZURE_STORAGE_KEY'
        ]
        for var in test_env_vars:
            if var in os.environ:
                del os.environ[var]


# =============================================================================
# Pytest Configuration and Fixtures
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment for all tests"""
    TestConfig.setup_azure_test_environment()
    yield
    TestConfig.cleanup_test_environment()


@pytest.fixture
def sample_btc_data():
    """Fixture providing sample BTC data"""
    return {
        'success': True,
        'type': 'crypto',
        'price': 95000.50,
        'indicators': {
            'mvrv': 2.1,
            'weekly_rsi': 65.0,
            'ema_200': 88000.0
        },
        'metadata': {'source': 'polygon_api'},
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def sample_mstr_data():
    """Fixture providing sample MSTR data"""
    return {
        'success': True,
        'type': 'stock',
        'price': 425.67,
        'indicators': {
            'model_price': 398.12,
            'deviation_pct': 6.9,
            'iv': 53.0,
            'iv_percentile': 35.0,
            'iv_rank': 42.0
        },
        'analysis': {
            'price_signal': {
                'status': 'neutral',
                'signal': 'HOLD',
                'message': 'MSTR Fair Valued (+6.9%)'
            },
            'options_strategy': {
                'primary_strategy': 'no_preference',
                'message': 'No Strong Options Preference',
                'description': 'Normal volatility + fair valuation'
            }
        },
        'metadata': {'source': 'mstr_analyzer'},
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


# =============================================================================
# Command Line Test Runner
# =============================================================================

def run_tests():
    """Run all tests with detailed output"""
    print("🧪 Running Function App Unit Tests...")
    print("=" * 60)

    # Setup test environment
    TestConfig.setup_azure_test_environment()

    try:
        # Discover and run tests
        loader = unittest.TestLoader()
        suite = loader.discover('.', pattern='test_function_app.py')
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        # Print summary
        print("\n" + "=" * 60)
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print(
            f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")

        if result.failures:
            print("\n❌ FAILURES:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback}")

        if result.errors:
            print("\n💥 ERRORS:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback}")

        if not result.failures and not result.errors:
            print("\n✅ All tests passed!")

        return result.wasSuccessful()

    finally:
        # Cleanup
        TestConfig.cleanup_test_environment()


if __name__ == "__main__":
    # Run tests when script is executed directly
    success = run_tests()
    exit(0 if success else 1)

# =============================================================================
# Usage Instructions
# =============================================================================

"""
USAGE INSTRUCTIONS:

1. Install required testing packages:
   pip install pytest unittest-mock

2. Run tests using unittest:
   python test_function_app.py

3. Run tests using pytest (more detailed output):
   pytest test_function_app.py -v

4. Run specific test class:
   python -m unittest TestDataValidation -v

5. Run specific test method:
   python -m unittest TestDataValidation.test_validate_btc_data_quality_success -v

6. For Azure Functions testing, you can also use Azure Functions Core Tools:
   func start --python

   Then run tests against the local function endpoint.

COVERAGE ANALYSIS:
To check test coverage, install coverage.py and run:
   pip install coverage
   coverage run test_function_app.py
   coverage report -m
   coverage html  # Generate HTML report

CONTINUOUS INTEGRATION:
For Azure DevOps or GitHub Actions, add this to your pipeline:
   - python -m pytest test_function_app.py --junitxml=test-results.xml

The tests cover:
✅ Data validation functions
✅ Report sending decision logic  
✅ Data processing and structuring
✅ Alert generation
✅ Main timer trigger function
✅ Error handling and exception scenarios
✅ Mocking of external dependencies
✅ Edge cases and failure scenarios
"""