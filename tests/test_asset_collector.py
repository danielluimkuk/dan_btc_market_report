"""
Unit tests for asset_data_collector.py

This test suite covers the HybridBTCCollector and HybridAssetDataCollector classes
with comprehensive mocking of external dependencies (APIs, network calls, etc.).

Test Categories:
1. Class initialization and configuration
2. BTC data collection with various scenarios
3. Price collection with fallback mechanisms
4. Technical indicator calculations (EMA, RSI)
5. API connection testing
6. Error handling and edge cases
7. Integration workflows

All external dependencies are mocked - no real API calls are made.
"""

import pytest
import unittest.mock as mock
from unittest.mock import Mock, patch, MagicMock, call
import pandas as pd
from datetime import datetime, timezone, timedelta
import json
import os
import sys
import logging

# Configure logging for CI compatibility
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the module to test
from asset_data_collector import (
    HybridBTCCollector,
    HybridAssetDataCollector,
    UpdatedAssetDataCollector,
    EnhancedPolygonBTCCollector
)


class TestHybridBTCCollector:
    """Test suite for HybridBTCCollector class"""

    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables for testing"""
        with patch.dict(os.environ, {'POLYGON_API_KEY': 'test_api_key_123'}):
            yield

    @pytest.fixture
    def collector(self, mock_env_vars):
        """Create a HybridBTCCollector instance for testing"""
        with patch('asset_data_collector.MVRVScraper') as mock_mvrv:
            mock_mvrv_instance = Mock()
            mock_mvrv_instance.get_mvrv_value.return_value = 2.1
            mock_mvrv.return_value = mock_mvrv_instance

            collector = HybridBTCCollector(api_key='test_api_key_123')
            return collector

    @pytest.fixture
    def sample_polygon_response(self):
        """Sample Polygon API response for testing"""
        return {
            'status': 'OK',
            'results': [
                {'c': 95000.0, 't': 1640995200000},  # Close price, timestamp
                {'c': 94000.0, 't': 1640908800000},
                {'c': 93000.0, 't': 1640822400000},
            ]
        }

    def test_initialization_with_api_key(self):
        """Test HybridBTCCollector initialization with API key"""
        with patch('asset_data_collector.MVRVScraper'):
            collector = HybridBTCCollector(api_key='test_key')

            assert collector.api_key == 'test_key'
            assert collector.base_url == "https://api.polygon.io"
            assert collector.session is not None
            assert 'User-Agent' in collector.session.headers

    def test_initialization_from_env_var(self, mock_env_vars):
        """Test initialization using environment variable"""
        with patch('asset_data_collector.MVRVScraper'):
            collector = HybridBTCCollector()

            assert collector.api_key == 'test_api_key_123'

    def test_initialization_missing_api_key(self):
        """Test initialization fails when API key is missing"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('asset_data_collector.MVRVScraper'):
                with pytest.raises(ValueError, match="Polygon API key required"):
                    HybridBTCCollector()

    @patch('asset_data_collector.time.sleep')  # Speed up tests
    def test_get_btc_data_success(self, mock_sleep, collector):
        """Test successful BTC data collection"""
        # Mock the price collection
        mock_price_result = {
            'price': 95000.0,
            'source': 'coingecko',
            'note': '🟢 LIVE PRICE (updated 30s ago)',
            'method': 'live_api'
        }

        with patch.object(collector, 'get_live_btc_price_with_fallback', return_value=mock_price_result), \
                patch.object(collector, 'get_daily_ema_200', return_value=90000.0), \
                patch.object(collector, 'get_weekly_rsi', return_value=65.5), \
                patch.object(collector.mvrv_scraper, 'get_mvrv_value', return_value=2.1):
            result = collector.get_btc_data()

            assert result['success'] is True
            assert result['price'] == 95000.0
            assert result['price_source'] == 'coingecko'
            assert result['ema_200'] == 90000.0
            assert result['weekly_rsi'] == 65.5
            assert result['mvrv'] == 2.1
            assert 'timestamp' in result

    def test_get_btc_data_error_handling(self, collector):
        """Test error handling in get_btc_data"""
        with patch.object(collector, 'get_live_btc_price_with_fallback',
                          side_effect=Exception("Network error")):
            result = collector.get_btc_data()

            assert result['success'] is False
            assert 'error' in result
            assert 'Network error' in result['error']
            assert 'timestamp' in result

    @patch('asset_data_collector.requests.Session.get')
    def test_get_live_btc_price_coingecko_success(self, mock_get, collector):
        """Test successful CoinGecko price collection"""
        # Mock successful CoinGecko response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'bitcoin': {
                'usd': 95000.0,
                'last_updated_at': int(datetime.now().timestamp()) - 60  # 1 minute ago
            }
        }
        mock_get.return_value = mock_response

        result = collector.get_live_btc_price_with_fallback()

        assert result['price'] == 95000.0
        assert result['source'] == 'coingecko'
        assert 'LIVE PRICE' in result['note'] or 'RECENT PRICE' in result['note']
        assert result['method'] == 'live_api'

    @patch('asset_data_collector.requests.Session.get')
    def test_get_live_btc_price_fallback_to_polygon(self, mock_get, collector):
        """Test fallback to Polygon when CoinGecko fails"""
        # First call (CoinGecko) fails
        mock_get.side_effect = [
            Exception("CoinGecko failed"),
            # Second call (Polygon yesterday) succeeds
            Mock(status_code=200, json=lambda: {'status': 'OK', 'close': 94000.0})
        ]

        with patch('asset_data_collector.datetime') as mock_datetime:
            # Mock yesterday's date
            mock_now = datetime(2024, 1, 15, 12, 0, 0)
            mock_datetime.now.return_value = mock_now

            result = collector.get_live_btc_price_with_fallback()

            assert result['price'] == 94000.0
            assert result['source'] == 'polygon_yesterday'
            assert 'YESTERDAY CLOSE' in result['note']
            assert result['method'] == 'historical_fallback'

    @patch('asset_data_collector.requests.Session.get')
    def test_get_live_btc_price_all_methods_fail(self, mock_get, collector):
        """Test when all price collection methods fail"""
        mock_get.side_effect = Exception("All methods failed")

        with pytest.raises(Exception, match="Could not get BTC price from any source"):
            collector.get_live_btc_price_with_fallback()

    @patch('asset_data_collector.requests.Session.get')
    def test_get_daily_ema_200_success(self, mock_get, collector, sample_polygon_response):
        """Test successful EMA 200 calculation"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = sample_polygon_response
        mock_get.return_value = mock_response

        # Create enough data points for EMA calculation
        sample_polygon_response['results'] = [
            {'c': 90000.0 + i * 100} for i in range(250)  # 250 data points
        ]

        result = collector.get_daily_ema_200()

        assert isinstance(result, float)
        assert result > 0
        # EMA should be somewhere in the range of our data
        assert 85000 < result < 120000

    @patch('asset_data_collector.requests.Session.get')
    def test_get_daily_ema_200_insufficient_data(self, mock_get, collector):
        """Test EMA calculation with insufficient data"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'status': 'OK',
            'results': [{'c': 95000.0}] * 50  # Only 50 data points, need 200+
        }
        mock_get.return_value = mock_response

        with pytest.raises(Exception, match="Insufficient data for EMA200"):
            collector.get_daily_ema_200()

    @patch('asset_data_collector.requests.Session.get')
    def test_get_weekly_rsi_success(self, mock_get, collector):
        """Test successful weekly RSI calculation"""
        # Create mock data with price trend for RSI calculation
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None

        # Create trending price data for meaningful RSI
        base_price = 90000
        results = []
        for i in range(50):
            # Create some up and down movements
            price_change = (i % 3 - 1) * 1000  # -1000, 0, 1000 pattern
            results.append({'c': base_price + i * 500 + price_change})

        mock_response.json.return_value = {
            'status': 'OK',
            'results': results
        }
        mock_get.return_value = mock_response

        result = collector.get_weekly_rsi()

        assert isinstance(result, float)
        assert 0 <= result <= 100  # RSI should be between 0 and 100

    def test_calculate_ema_basic(self, collector):
        """Test EMA calculation with simple data"""
        prices = [100, 102, 104, 103, 105, 107, 106, 108, 110, 109] * 25  # 250 prices

        result = collector.calculate_ema(prices, 10)

        assert isinstance(result, float)
        assert result > 0
        # EMA should be influenced by recent prices
        assert 105 < result < 115

    def test_calculate_ema_insufficient_data(self, collector):
        """Test EMA calculation with insufficient data"""
        prices = [100, 102, 104]  # Only 3 prices, need more for period=10

        with pytest.raises(ValueError, match="Not enough data points"):
            collector.calculate_ema(prices, 10)

    def test_calculate_rsi_basic(self, collector):
        """Test RSI calculation with trending data"""
        # Create upward trending prices for RSI calculation
        prices = []
        base = 100
        for i in range(30):
            if i % 3 == 0:
                base += 2  # Gain
            elif i % 3 == 1:
                base -= 1  # Loss
            else:
                base += 1  # Small gain
            prices.append(base)

        result = collector.calculate_rsi(prices, 14)

        assert isinstance(result, float)
        assert 0 <= result <= 100
        # With our upward trend, RSI should be > 50
        assert result > 40

    def test_calculate_rsi_insufficient_data(self, collector):
        """Test RSI calculation with insufficient data"""
        prices = [100, 102, 104]  # Only 3 prices, need 15+ for period=14

        with pytest.raises(ValueError, match="Not enough data points for RSI"):
            collector.calculate_rsi(prices, 14)

    @patch('asset_data_collector.requests.Session.get')
    def test_api_connection_test_success(self, mock_get, collector):
        """Test successful API connection test"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {'status': 'OK'}
        mock_get.return_value = mock_response

        result = collector.test_api_connection()

        assert result is True

    @patch('asset_data_collector.requests.Session.get')
    def test_api_connection_test_failure(self, mock_get, collector):
        """Test API connection test failure"""
        mock_get.side_effect = Exception("Connection failed")

        result = collector.test_api_connection()

        assert result is False

    @patch('asset_data_collector.requests.Session.get')
    def test_coingecko_connection_test_success(self, mock_get, collector):
        """Test successful CoinGecko connection test"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'bitcoin': {'usd': 95000.0}
        }
        mock_get.return_value = mock_response

        result = collector.test_coingecko_connection()

        assert result is True

    @patch('asset_data_collector.requests.Session.get')
    def test_coingecko_connection_test_failure(self, mock_get, collector):
        """Test CoinGecko connection test failure"""
        mock_get.side_effect = Exception("Connection failed")

        result = collector.test_coingecko_connection()

        assert result is False


class TestHybridAssetDataCollector:
    """Test suite for HybridAssetDataCollector class"""

    @pytest.fixture
    def asset_collector(self):
        """Create HybridAssetDataCollector instance for testing"""
        with patch('asset_data_collector.HybridBTCCollector') as mock_btc_collector_class:
            # Mock the BTC collector instance
            mock_btc_collector = Mock()
            mock_btc_collector.test_api_connection.return_value = True
            mock_btc_collector.test_coingecko_connection.return_value = True
            mock_btc_collector_class.return_value = mock_btc_collector

            collector = HybridAssetDataCollector()
            return collector

    def test_initialization_success(self, asset_collector):
        """Test successful initialization of HybridAssetDataCollector"""
        assert asset_collector.btc_collector is not None

    def test_initialization_btc_collector_failure(self):
        """Test initialization when BTC collector fails"""
        with patch('asset_data_collector.HybridBTCCollector', side_effect=Exception("Init failed")):
            collector = HybridAssetDataCollector()

            assert collector.btc_collector is None

    def test_collect_asset_data_btc_success(self, asset_collector):
        """Test successful BTC data collection"""
        # Mock successful BTC data
        mock_btc_data = {
            'success': True,
            'price': 95000.0,
            'price_source': 'coingecko',
            'price_note': 'Live price',
            'ema_200': 90000.0,
            'weekly_rsi': 65.5,
            'mvrv': 2.1,
            'source': 'coingecko + polygon_historical + tradingview'
        }

        asset_collector.btc_collector.get_btc_data.return_value = mock_btc_data

        result = asset_collector.collect_asset_data('BTC', {})

        assert result['success'] is True
        assert result['price'] == 95000.0
        assert result['price_source'] == 'coingecko'
        assert result['indicators']['ema_200'] == 90000.0
        assert result['indicators']['weekly_rsi'] == 65.5
        assert result['indicators']['mvrv'] == 2.1
        assert result['type'] == 'crypto'

    def test_collect_asset_data_btc_failure(self, asset_collector):
        """Test BTC data collection failure"""
        mock_btc_data = {
            'success': False,
            'error': 'API connection failed'
        }

        asset_collector.btc_collector.get_btc_data.return_value = mock_btc_data

        result = asset_collector.collect_asset_data('BTC', {})

        assert result['success'] is False
        assert 'error' in result
        assert 'API connection failed' in result['error']

    def test_collect_asset_data_btc_collector_unavailable(self, asset_collector):
        """Test BTC collection when collector is unavailable"""
        asset_collector.btc_collector = None

        result = asset_collector.collect_asset_data('BTC', {})

        assert result['success'] is False
        assert 'Hybrid BTC collector not available' in result['error']

    def test_collect_asset_data_mstr(self, asset_collector):
        """Test MSTR data collection (not implemented)"""
        result = asset_collector.collect_asset_data('MSTR', {})

        assert result['success'] is False
        assert result['type'] == 'stock'
        assert 'MSTR collection not implemented' in result['error']

    def test_collect_asset_data_unknown_asset(self, asset_collector):
        """Test collection for unknown asset"""
        result = asset_collector.collect_asset_data('UNKNOWN', {})

        assert result['success'] is False
        assert 'Unknown asset: UNKNOWN' in result['error']

    def test_collect_asset_data_exception_handling(self, asset_collector):
        """Test exception handling in asset data collection"""
        asset_collector.btc_collector.get_btc_data.side_effect = Exception("Unexpected error")

        result = asset_collector.collect_asset_data('BTC', {})

        assert result['success'] is False
        assert 'Unexpected error' in result['error']


class TestAliases:
    """Test module aliases for backward compatibility"""

    def test_updated_asset_data_collector_alias(self):
        """Test UpdatedAssetDataCollector is an alias for HybridAssetDataCollector"""
        assert UpdatedAssetDataCollector is HybridAssetDataCollector

    def test_enhanced_polygon_btc_collector_alias(self):
        """Test EnhancedPolygonBTCCollector is an alias for HybridBTCCollector"""
        assert EnhancedPolygonBTCCollector is HybridBTCCollector


class TestIntegrationScenarios:
    """Integration-style tests with multiple components"""

    @pytest.fixture
    def full_collector_setup(self):
        """Set up a complete collector with all mocks"""
        with patch.dict(os.environ, {'POLYGON_API_KEY': 'test_key'}), \
                patch('asset_data_collector.MVRVScraper') as mock_mvrv_class, \
                patch('asset_data_collector.requests.Session') as mock_session_class:
            # Mock MVRV scraper
            mock_mvrv = Mock()
            mock_mvrv.get_mvrv_value.return_value = 2.1
            mock_mvrv_class.return_value = mock_mvrv

            # Mock HTTP session
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            collector = HybridAssetDataCollector()

            return collector, mock_session

    def test_complete_btc_data_workflow(self, full_collector_setup):
        """Test complete BTC data collection workflow"""
        collector, mock_session = full_collector_setup

        # Mock successful API responses in sequence
        mock_responses = [
            # CoinGecko price response
            Mock(status_code=200, json=lambda: {
                'bitcoin': {'usd': 95000.0, 'last_updated_at': int(datetime.now().timestamp())}
            }),
            # Polygon daily EMA data
            Mock(status_code=200, json=lambda: {
                'status': 'OK',
                'results': [{'c': 90000.0 + i * 100} for i in range(250)]
            }),
            # Polygon weekly RSI data
            Mock(status_code=200, json=lambda: {
                'status': 'OK',
                'results': [{'c': 90000.0 + i * 500} for i in range(50)]
            })
        ]

        mock_session.get.side_effect = mock_responses

        with patch('asset_data_collector.time.sleep'):  # Speed up test
            result = collector.collect_asset_data('BTC', {})

        assert result['success'] is True
        assert result['price'] == 95000.0
        assert result['price_source'] == 'coingecko'
        assert 'ema_200' in result['indicators']
        assert 'weekly_rsi' in result['indicators']
        assert 'mvrv' in result['indicators']
        assert result['type'] == 'crypto'


# Test runner and utility functions
def run_quick_test():
    """Quick test function for development use"""
    logging.info("Running quick asset_data_collector tests...")

    # Test basic initialization
    with patch.dict(os.environ, {'POLYGON_API_KEY': 'test_key'}):
        with patch('asset_data_collector.MVRVScraper'):
            collector = HybridBTCCollector()
            assert collector.api_key == 'test_key'
            logging.info("✅ Basic initialization test passed")

    # Test HybridAssetDataCollector
    with patch('asset_data_collector.HybridBTCCollector'):
        asset_collector = HybridAssetDataCollector()
        assert asset_collector is not None
        logging.info("✅ HybridAssetDataCollector initialization test passed")

    logging.info("✅ Quick tests completed successfully!")


if __name__ == '__main__':
    # Run quick test if executed directly
    run_quick_test()

    # For full test suite, use: pytest tests/test_asset_data_collector.py -v
    print("\n" + "=" * 70)
    print("ASSET DATA COLLECTOR TEST SUITE")
    print("=" * 70)
    print("To run full test suite:")
    print("  pytest tests/test_asset_data_collector.py -v")
    print("\nTo run specific test categories:")
    print("  pytest tests/test_asset_data_collector.py::TestHybridBTCCollector -v")
    print("  pytest tests/test_asset_data_collector.py::TestHybridAssetDataCollector -v")
    print("  pytest tests/test_asset_data_collector.py::TestIntegrationScenarios -v")
    print("\nFor CI/CD environments:")
    print("  CI=true pytest tests/test_asset_data_collector.py")