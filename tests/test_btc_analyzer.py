"""
Unit tests for btc_analyzer.py

This test suite covers the BTCAnalyzer class which handles Bitcoin market signal
analysis and state management with Azure Table Storage persistence.

Test Categories:
1. Class initialization with/without storage
2. Bitcoin signal analysis (bull/bear market scenarios)
3. Signal condition calculations (MVRV, RSI thresholds)
4. Signal state management and persistence
5. Signal status determination and predictions
6. Historical signal tracking
7. Error handling and edge cases

All external dependencies are mocked - no real Azure storage calls are made.
"""

import pytest
import unittest.mock as mock
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
import logging

# Configure logging for CI compatibility
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

import sys
import os

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from btc_analyzer import BTCAnalyzer


class TestBTCAnalyzer:
    """Test suite for BTCAnalyzer class"""

    @pytest.fixture
    def mock_storage(self):
        """Create a mock DataStorage instance"""
        mock_storage = Mock()
        mock_storage.table_service = Mock()
        return mock_storage

    @pytest.fixture
    def analyzer_with_storage(self, mock_storage):
        """Create BTCAnalyzer with mocked storage"""
        return BTCAnalyzer(storage=mock_storage)

    @pytest.fixture
    def analyzer_without_storage(self):
        """Create BTCAnalyzer without storage"""
        return BTCAnalyzer(storage=None)

    @pytest.fixture
    def sample_btc_data_bull_market(self):
        """Sample BTC data for bull market scenario"""
        return {
            'price': 100000.0,
            'indicators': {
                'ema_200': 90000.0,  # Price above EMA = bull market
                'weekly_rsi': 75.0,  # High RSI
                'mvrv': 3.5  # High MVRV
            }
        }

    @pytest.fixture
    def sample_btc_data_bear_market(self):
        """Sample BTC data for bear market scenario"""
        return {
            'price': 45000.0,
            'indicators': {
                'ema_200': 60000.0,  # Price below EMA = bear market
                'weekly_rsi': 25.0,  # Low RSI
                'mvrv': 0.8  # Low MVRV
            }
        }

    @pytest.fixture
    def sample_btc_data_neutral(self):
        """Sample BTC data for neutral market scenario"""
        return {
            'price': 90000.0,
            'indicators': {
                'ema_200': 89000.0,  # Price slightly above EMA
                'weekly_rsi': 55.0,  # Neutral RSI
                'mvrv': 2.0  # Neutral MVRV
            }
        }

    def test_initialization_with_storage(self, mock_storage):
        """Test BTCAnalyzer initialization with storage"""
        analyzer = BTCAnalyzer(storage=mock_storage)

        assert analyzer.storage == mock_storage

    def test_initialization_without_storage(self):
        """Test BTCAnalyzer initialization without storage"""
        with patch('btc_analyzer.DataStorage') as mock_data_storage_class:
            mock_data_storage_instance = Mock()
            mock_data_storage_class.return_value = mock_data_storage_instance

            analyzer = BTCAnalyzer()

            assert analyzer.storage == mock_data_storage_instance

    def test_analyze_btc_signals_bull_market_sell_signal(self, analyzer_with_storage, sample_btc_data_bull_market):
        """Test BTC signal analysis in bull market with sell conditions"""
        # Mock signal state retrieval and saving
        mock_signal_state = {
            'active': False,
            'signal_type': '',
            'start_date': '',
            'end_date': '',
            'conditions_failing_since': '',
            'last_updated': '',
            'days_active': 0
        }

        with patch.object(analyzer_with_storage, '_get_signal_state', return_value=mock_signal_state), \
                patch.object(analyzer_with_storage, '_save_signal_state'), \
                patch('btc_analyzer.datetime') as mock_datetime:
            # Mock current date
            mock_now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            mock_datetime.strftime = lambda self, fmt: self.strftime(fmt)

            result = analyzer_with_storage.analyze_btc_signals(sample_btc_data_bull_market)

            # Verify bull market detection
            assert result['is_bull_market'] is True
            assert result['market_status'] == 'bull'

            # Verify price analysis
            assert result['price'] == 100000.0
            assert result['ema_200'] == 90000.0
            assert abs(result['price_vs_ema_pct'] - 11.11) < 0.1  # ~11.11% above EMA

            # Verify indicators
            assert result['indicators']['mvrv'] == 3.5
            assert result['indicators']['weekly_rsi'] == 75.0

            # Verify signal conditions (bull market = sell signal conditions)
            signal_conditions = result['signal_conditions']
            assert signal_conditions['signal_type'] == 'SELL'
            assert signal_conditions['both_conditions_met'] is True  # MVRV > 3.0 AND RSI > 70
            assert signal_conditions['mvrv']['condition_met'] is True
            assert signal_conditions['rsi']['condition_met'] is True

            # Verify timestamp
            assert 'analysis_timestamp' in result

    def test_analyze_btc_signals_bear_market_buy_signal(self, analyzer_with_storage, sample_btc_data_bear_market):
        """Test BTC signal analysis in bear market with buy conditions"""
        mock_signal_state = {
            'active': False,
            'signal_type': '',
            'start_date': '',
            'end_date': '',
            'conditions_failing_since': '',
            'last_updated': '',
            'days_active': 0
        }

        with patch.object(analyzer_with_storage, '_get_signal_state', return_value=mock_signal_state), \
                patch.object(analyzer_with_storage, '_save_signal_state'), \
                patch('btc_analyzer.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now

            result = analyzer_with_storage.analyze_btc_signals(sample_btc_data_bear_market)

            # Verify bear market detection
            assert result['is_bull_market'] is False
            assert result['market_status'] == 'bear'

            # Verify price analysis
            assert result['price'] == 45000.0
            assert result['ema_200'] == 60000.0
            assert result['price_vs_ema_pct'] < 0  # Price below EMA

            # Verify signal conditions (bear market = buy signal conditions)
            signal_conditions = result['signal_conditions']
            assert signal_conditions['signal_type'] == 'BUY'
            assert signal_conditions['both_conditions_met'] is True  # MVRV < 1.0 AND RSI < 30
            assert signal_conditions['mvrv']['condition_met'] is True
            assert signal_conditions['rsi']['condition_met'] is True

    def test_analyze_btc_signals_neutral_conditions(self, analyzer_with_storage, sample_btc_data_neutral):
        """Test BTC signal analysis with neutral conditions"""
        mock_signal_state = {
            'active': False,
            'signal_type': '',
            'start_date': '',
            'end_date': '',
            'conditions_failing_since': '',
            'last_updated': '',
            'days_active': 0
        }

        with patch.object(analyzer_with_storage, '_get_signal_state', return_value=mock_signal_state), \
                patch.object(analyzer_with_storage, '_save_signal_state'), \
                patch('btc_analyzer.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now

            result = analyzer_with_storage.analyze_btc_signals(sample_btc_data_neutral)

            # Verify neutral conditions
            signal_conditions = result['signal_conditions']
            assert signal_conditions['both_conditions_met'] is False

            # In bull market but neither MVRV > 3.0 nor RSI > 70
            assert signal_conditions['signal_type'] == 'SELL'  # Bull market
            assert signal_conditions['mvrv']['condition_met'] is False  # MVRV 2.0 < 3.0
            assert signal_conditions['rsi']['condition_met'] is False  # RSI 55 < 70

    def test_analyze_btc_signals_error_handling(self, analyzer_with_storage):
        """Test error handling in analyze_btc_signals"""
        # Test graceful handling of empty data (this is actually good behavior)
        empty_data = {}
        result = analyzer_with_storage.analyze_btc_signals(empty_data)

        # Should NOT have error - this is graceful handling
        assert 'error' not in result
        assert result['price'] == 0
        assert result['ema_200'] == 0

        # Test actual error by forcing an exception
        with patch.object(analyzer_with_storage, '_get_signal_state',
                          side_effect=Exception("Storage error")):
            result = analyzer_with_storage.analyze_btc_signals({
                'price': 50000,
                'indicators': {'ema_200': 45000, 'weekly_rsi': 50, 'mvrv': 1.5}
            })

            assert 'error' in result
            assert 'Storage error' in result['error']

    def test_calculate_signal_conditions_bull_market_sell(self, analyzer_with_storage):
        """Test signal condition calculation for bull market sell signal"""
        weekly_rsi = 75.0
        mvrv = 3.5
        is_bull_market = True

        result = analyzer_with_storage._calculate_signal_conditions(weekly_rsi, mvrv, is_bull_market)

        assert result['signal_type'] == 'SELL'
        assert result['both_conditions_met'] is True
        assert result['market_type'] == 'bull'

        # Check MVRV condition
        mvrv_status = result['mvrv']
        assert mvrv_status['value'] == 3.5
        assert mvrv_status['condition_met'] is True
        assert mvrv_status['threshold'] == 3.0
        assert mvrv_status['operator'] == '>'

        # Check RSI condition
        rsi_status = result['rsi']
        assert rsi_status['value'] == 75.0
        assert rsi_status['condition_met'] is True
        assert rsi_status['threshold'] == 70
        assert rsi_status['operator'] == '>'

    def test_calculate_signal_conditions_bear_market_buy(self, analyzer_with_storage):
        """Test signal condition calculation for bear market buy signal"""
        weekly_rsi = 25.0
        mvrv = 0.8
        is_bull_market = False

        result = analyzer_with_storage._calculate_signal_conditions(weekly_rsi, mvrv, is_bull_market)

        assert result['signal_type'] == 'BUY'
        assert result['both_conditions_met'] is True
        assert result['market_type'] == 'bear'

        # Check MVRV condition
        mvrv_status = result['mvrv']
        assert mvrv_status['value'] == 0.8
        assert mvrv_status['condition_met'] is True
        assert mvrv_status['threshold'] == 1.0
        assert mvrv_status['operator'] == '<'

        # Check RSI condition
        rsi_status = result['rsi']
        assert rsi_status['value'] == 25.0
        assert rsi_status['condition_met'] is True
        assert rsi_status['threshold'] == 30
        assert rsi_status['operator'] == '<'

    def test_get_signal_state_with_storage(self, analyzer_with_storage, mock_storage):
        """Test signal state retrieval with Azure storage"""
        # Mock Azure table query response
        mock_entity = Mock()
        mock_entity.active = True
        mock_entity.signal_type = 'SELL'
        mock_entity.start_date = '2024-01-10'
        mock_entity.end_date = ''
        mock_entity.conditions_failing_since = ''
        mock_entity.last_updated = '2024-01-15'

        mock_storage.table_service.query_entities.return_value = [mock_entity]

        with patch.object(analyzer_with_storage, '_calculate_days_active', return_value=5):
            result = analyzer_with_storage._get_signal_state()

        assert result['active'] is True
        assert result['signal_type'] == 'SELL'
        assert result['start_date'] == '2024-01-10'
        assert result['end_date'] == ''
        assert result['days_active'] == 5

    def test_get_signal_state_no_storage(self, analyzer_without_storage):
        """Test signal state retrieval without storage"""
        result = analyzer_without_storage._get_signal_state()

        # Should return default state
        assert result['active'] is False
        assert result['signal_type'] == ''
        assert result['start_date'] == ''
        assert result['end_date'] == ''
        assert result['days_active'] == 0

    def test_get_signal_state_empty_query(self, analyzer_with_storage, mock_storage):
        """Test signal state retrieval with empty query result"""
        mock_storage.table_service.query_entities.return_value = []

        result = analyzer_with_storage._get_signal_state()

        # Should return default state
        assert result['active'] is False
        assert result['signal_type'] == ''
        assert result['start_date'] == ''
        assert result['end_date'] == ''
        assert result['days_active'] == 0

    def test_update_signal_state_activation(self, analyzer_with_storage):
        """Test signal state update when signal activates"""
        current_state = {
            'active': False,
            'signal_type': '',
            'start_date': '',
            'end_date': '',
            'conditions_failing_since': '',
            'last_updated': '',
            'days_active': 0
        }

        signal_conditions = {
            'both_conditions_met': True,
            'signal_type': 'SELL'
        }

        current_date = '2024-01-15'

        result = analyzer_with_storage._update_signal_state(current_state, signal_conditions, current_date)

        assert result['active'] is True
        assert result['signal_type'] == 'SELL'
        assert result['start_date'] == '2024-01-15'
        assert result['end_date'] == ''
        assert result['conditions_failing_since'] == ''
        assert result['last_updated'] == '2024-01-15'

    def test_update_signal_state_deactivation_after_30_days(self, analyzer_with_storage):
        """Test signal deactivation after 30 days of failing conditions"""
        current_state = {
            'active': True,
            'signal_type': 'SELL',
            'start_date': '2024-01-01',
            'end_date': '',
            'conditions_failing_since': '2023-12-15',  # 31 days ago
            'last_updated': '2024-01-14',
            'days_active': 14
        }

        signal_conditions = {
            'both_conditions_met': False,
            'signal_type': 'SELL'
        }

        current_date = '2024-01-15'

        with patch('btc_analyzer.datetime') as mock_datetime:
            # Mock date parsing
            mock_datetime.strptime.side_effect = lambda date_str, fmt: datetime.strptime(date_str, fmt)

            result = analyzer_with_storage._update_signal_state(current_state, signal_conditions, current_date)

        assert result['active'] is False
        assert result['end_date'] == '2024-01-15'
        assert result['conditions_failing_since'] == ''

    def test_update_signal_state_conditions_restore(self, analyzer_with_storage):
        """Test signal state when failing conditions are restored"""
        current_state = {
            'active': True,
            'signal_type': 'SELL',
            'start_date': '2024-01-01',
            'end_date': '',
            'conditions_failing_since': '2024-01-10',  # Was failing
            'last_updated': '2024-01-14',
            'days_active': 14
        }

        signal_conditions = {
            'both_conditions_met': True,  # Conditions restored
            'signal_type': 'SELL'
        }

        current_date = '2024-01-15'

        result = analyzer_with_storage._update_signal_state(current_state, signal_conditions, current_date)

        assert result['active'] is True
        assert result['conditions_failing_since'] == ''  # Cleared
        assert result['end_date'] == ''

    def test_calculate_days_active_ongoing_signal(self, analyzer_with_storage):
        """Test days active calculation for ongoing signal"""
        start_date = '2024-01-10'
        end_date = ''  # Still active

        with patch('btc_analyzer.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            mock_datetime.strptime.return_value = datetime(2024, 1, 10, 0, 0, 0)

            result = analyzer_with_storage._calculate_days_active(start_date, end_date)

        assert result == 5  # 5 days between Jan 10 and Jan 15

    def test_calculate_days_active_ended_signal(self, analyzer_with_storage):
        """Test days active calculation for ended signal"""
        start_date = '2024-01-10'
        end_date = '2024-01-20'

        with patch('btc_analyzer.datetime') as mock_datetime:
            mock_datetime.strptime.side_effect = lambda date_str, fmt: datetime.strptime(date_str, fmt)

            result = analyzer_with_storage._calculate_days_active(start_date, end_date)

        assert result == 10  # 10 days between Jan 10 and Jan 20

    def test_calculate_days_active_no_start_date(self, analyzer_with_storage):
        """Test days active calculation with no start date"""
        result = analyzer_with_storage._calculate_days_active('', '')
        assert result == 0

    def test_save_signal_state_success(self, analyzer_with_storage, mock_storage):
        """Test successful signal state saving"""
        signal_state = {
            'active': True,
            'signal_type': 'SELL',
            'start_date': '2024-01-15',
            'end_date': '',
            'conditions_failing_since': '',
            'last_updated': '2024-01-15',
            'days_active': 0
        }

        # Patch the correct Entity import path
        with patch('azure.cosmosdb.table.models.Entity') as mock_entity_class:
            mock_entity = Mock()
            mock_entity_class.return_value = mock_entity

            analyzer_with_storage._save_signal_state(signal_state)

            # Verify entity creation and storage
            mock_entity_class.assert_called_once()
            mock_storage.table_service.insert_or_replace_entity.assert_called_once_with(
                'systemhealth', mock_entity
            )

    def test_save_signal_state_no_storage(self, analyzer_without_storage):
        """Test signal state saving without storage"""
        signal_state = {'active': True}

        # Should not raise exception
        analyzer_without_storage._save_signal_state(signal_state)

    def test_determine_signal_status_active_signal(self, analyzer_with_storage):
        """Test signal status determination for active signal"""
        signal_state = {
            'active': True,
            'signal_type': 'SELL',
            'start_date': '2024-01-10',
            'end_date': '',
            'days_active': 5
        }

        signal_conditions = {
            'both_conditions_met': True
        }

        result = analyzer_with_storage._determine_signal_status(signal_state, signal_conditions)

        assert result['status'] == 'active'
        assert result['message'] == 'SELL SIGNAL ACTIVE'
        assert result['emoji'] == '🔴'
        assert 'Top is likely to be reached' in result['prediction']
        assert result['days_active'] == 5

    def test_determine_signal_status_weakening_signal(self, analyzer_with_storage):
        """Test signal status determination for weakening signal"""
        signal_state = {
            'active': True,
            'signal_type': 'BUY',
            'start_date': '2024-01-10',
            'end_date': '',
            'days_active': 5
        }

        signal_conditions = {
            'both_conditions_met': False  # Conditions weakening
        }

        result = analyzer_with_storage._determine_signal_status(signal_state, signal_conditions)

        assert result['status'] == 'weakening'
        assert result['message'] == 'BUY SIGNAL WEAKENING'
        assert result['emoji'] == '🟡'
        assert 'One parameter no longer met' in result['prediction']

    def test_determine_signal_status_recently_off(self, analyzer_with_storage):
        """Test signal status determination for recently ended signal"""
        signal_state = {
            'active': False,
            'signal_type': 'SELL',
            'start_date': '2024-01-10',
            'end_date': '2024-01-20',
            'days_active': 10
        }

        signal_conditions = {
            'both_conditions_met': False
        }

        result = analyzer_with_storage._determine_signal_status(signal_state, signal_conditions)

        assert result['status'] == 'recently_off'
        assert result['message'] == 'SELL SIGNAL OFF'
        assert result['emoji'] == '🟡'
        assert 'Was active: 2024-01-10 to 2024-01-20' in result['prediction']

    def test_determine_signal_status_no_signal(self, analyzer_with_storage):
        """Test signal status determination for no signal"""
        signal_state = {
            'active': False,
            'signal_type': '',
            'start_date': '',
            'end_date': '',
            'days_active': 0
        }

        signal_conditions = {
            'both_conditions_met': False
        }

        result = analyzer_with_storage._determine_signal_status(signal_state, signal_conditions)

        assert result['status'] == 'none'
        assert result['message'] == ''
        assert result['emoji'] == ''
        assert result['prediction'] == ''

    def test_get_signal_history_with_storage(self, analyzer_with_storage):
        """Test signal history retrieval"""
        mock_current_state = {
            'active': True,
            'signal_type': 'SELL',
            'start_date': '2024-01-10'
        }

        with patch.object(analyzer_with_storage, '_get_signal_state', return_value=mock_current_state):
            result = analyzer_with_storage.get_signal_history(30)

        assert result['current_signal'] == mock_current_state
        assert result['period_days'] == 30
        assert result['history_available'] is True

    def test_get_signal_history_no_storage(self, analyzer_without_storage):
        """Test signal history retrieval without storage"""
        result = analyzer_without_storage.get_signal_history()

        assert 'error' in result
        assert result['error'] == 'Storage not available'

    def test_reset_signal_state_success(self, analyzer_with_storage):
        """Test successful signal state reset"""
        with patch.object(analyzer_with_storage, '_save_signal_state') as mock_save, \
                patch('btc_analyzer.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now

            result = analyzer_with_storage.reset_signal_state()

            assert result is True
            mock_save.assert_called_once()

    def test_reset_signal_state_error(self, analyzer_with_storage):
        """Test signal state reset with error"""
        with patch.object(analyzer_with_storage, '_save_signal_state', side_effect=Exception("Save failed")):
            result = analyzer_with_storage.reset_signal_state()

            assert result is False


class TestIntegrationScenarios:
    """Integration-style tests with multiple components"""

    @pytest.fixture
    def mock_storage_with_data(self):
        """Mock storage with existing signal state"""
        mock_storage = Mock()
        mock_storage.table_service = Mock()

        # Mock existing signal state
        mock_entity = Mock()
        mock_entity.active = True
        mock_entity.signal_type = 'SELL'
        mock_entity.start_date = '2024-01-10'
        mock_entity.end_date = ''
        mock_entity.conditions_failing_since = ''
        mock_entity.last_updated = '2024-01-14'

        mock_storage.table_service.query_entities.return_value = [mock_entity]

        return mock_storage

    def test_complete_signal_analysis_workflow(self, mock_storage_with_data):
        """Test complete signal analysis workflow from BTC data to final status"""
        analyzer = BTCAnalyzer(storage=mock_storage_with_data)

        # Bull market data with strong sell signal
        btc_data = {
            'price': 120000.0,
            'indicators': {
                'ema_200': 95000.0,
                'weekly_rsi': 80.0,
                'mvrv': 4.0
            }
        }

        with patch('btc_analyzer.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            mock_datetime.strptime.side_effect = lambda date_str, fmt: datetime.strptime(date_str, fmt)

            result = analyzer.analyze_btc_signals(btc_data)

        # Verify complete analysis
        assert result['is_bull_market'] is True
        assert result['market_status'] == 'bull'
        assert result['price'] == 120000.0

        # Verify signal conditions
        signal_conditions = result['signal_conditions']
        assert signal_conditions['signal_type'] == 'SELL'
        assert signal_conditions['both_conditions_met'] is True

        # Verify signal state management
        signal_state = result['signal_state']
        assert signal_state['active'] is True
        assert signal_state['signal_type'] == 'SELL'

        # Verify signal status
        signal_status = result['signal_status']
        assert signal_status['status'] == 'active'
        assert 'SELL SIGNAL ACTIVE' in signal_status['message']


# Test runner and utility functions
def run_quick_test():
    """Quick test function for development use"""
    logging.info("Running quick btc_analyzer tests...")

    # Test basic initialization
    from btc_analyzer import BTCAnalyzer

    analyzer = BTCAnalyzer(storage=None)
    assert analyzer.storage is not None  # Should create default storage
    logging.info("✅ Basic initialization test passed")

    # Test signal condition calculation
    result = analyzer._calculate_signal_conditions(75.0, 3.5, True)
    assert result['signal_type'] == 'SELL'
    assert result['both_conditions_met'] is True
    logging.info("✅ Signal condition calculation test passed")

    # Test default signal state
    state = analyzer._get_default_signal_state()
    assert state['active'] is False
    assert state['signal_type'] == ''
    logging.info("✅ Default signal state test passed")

    logging.info("✅ Quick tests completed successfully!")


if __name__ == '__main__':
    # Run quick test if executed directly
    run_quick_test()

    # For full test suite, use: pytest tests/test_btc_analyzer.py -v
    print("\n" + "=" * 70)
    print("BTC ANALYZER TEST SUITE")
    print("=" * 70)
    print("To run full test suite:")
    print("  pytest tests/test_btc_analyzer.py -v")
    print("\nTo run specific test categories:")
    print("  pytest tests/test_btc_analyzer.py::TestBTCAnalyzer -v")
    print("  pytest tests/test_btc_analyzer.py::TestIntegrationScenarios -v")
    print("\nFor CI/CD environments:")
    print("  CI=true pytest tests/test_btc_analyzer.py")