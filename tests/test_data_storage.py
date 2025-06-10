"""
Unit tests for data_storage.py

This test suite covers the DataStorage class which handles Azure Table Storage
operations for asset data, alerts, system health, and monetary data.

Test Categories:
1. Class initialization with/without Azure credentials
2. Table creation and management
3. Daily asset data storage and retrieval
4. Historical data querying and analytics
5. Alert history management
6. System health tracking
7. Data cleanup and maintenance
8. Error handling and edge cases

All Azure dependencies are mocked - no real Azure storage calls are made.
"""

import pytest
import unittest.mock as mock
from unittest.mock import Mock, patch, MagicMock, call
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import sys
import logging

# Configure logging for CI compatibility
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_storage import DataStorage


class TestDataStorageInitialization:
    """Test suite for DataStorage initialization"""

    @pytest.fixture
    def mock_azure_credentials(self):
        """Mock Azure storage credentials"""
        return {
            'AZURE_STORAGE_ACCOUNT': 'test_account',
            'AZURE_STORAGE_KEY': 'test_key_123'
        }

    def test_initialization_with_credentials(self, mock_azure_credentials):
        """Test DataStorage initialization with valid Azure credentials"""
        with patch.dict(os.environ, mock_azure_credentials), \
                patch('data_storage.TableService') as mock_table_service, \
                patch.object(DataStorage, '_ensure_tables_exist') as mock_ensure_tables:
            mock_service_instance = Mock()
            mock_table_service.return_value = mock_service_instance

            storage = DataStorage()

            assert storage.account_name == 'test_account'
            assert storage.account_key == 'test_key_123'
            assert storage.table_service == mock_service_instance
            assert storage.table_name == 'assetdata'
            assert storage.alerts_table == 'alerthistory'
            assert storage.health_table == 'systemhealth'
            assert storage.monetary_table == 'monetarydata'

            # Verify TableService was created with correct parameters
            mock_table_service.assert_called_once_with(
                account_name='test_account',
                account_key='test_key_123'
            )
            mock_ensure_tables.assert_called_once()

    def test_initialization_without_credentials(self):
        """Test DataStorage initialization without Azure credentials"""
        with patch.dict(os.environ, {}, clear=True):
            storage = DataStorage()

            assert storage.account_name is None
            assert storage.account_key is None
            assert storage.table_service is None

    def test_initialization_partial_credentials(self):
        """Test initialization with only account name"""
        with patch.dict(os.environ, {'AZURE_STORAGE_ACCOUNT': 'test_account'}):
            storage = DataStorage()

            assert storage.account_name == 'test_account'
            assert storage.account_key is None
            assert storage.table_service is None

    @patch('data_storage.TableService')
    def test_ensure_tables_exist_success(self, mock_table_service, mock_azure_credentials):
        """Test successful table creation"""
        with patch.dict(os.environ, mock_azure_credentials):
            mock_service_instance = Mock()
            mock_table_service.return_value = mock_service_instance

            storage = DataStorage()

            # Verify all tables were created
            expected_calls = [
                call('assetdata'),
                call('alerthistory'),
                call('systemhealth'),
                call('monetarydata')
            ]
            mock_service_instance.create_table.assert_has_calls(expected_calls, any_order=True)

    @patch('data_storage.TableService')
    def test_ensure_tables_exist_table_already_exists(self, mock_table_service, mock_azure_credentials):
        """Test table creation when table already exists"""
        with patch.dict(os.environ, mock_azure_credentials):
            mock_service_instance = Mock()
            mock_table_service.return_value = mock_service_instance

            # Create a proper exception class that inherits from BaseException
            class MockAzureException(Exception):
                pass

            # Mock the AzureException with a proper exception class
            with patch('data_storage.AzureException', MockAzureException):
                # Mock TableAlreadyExists exception
                mock_exception = MockAzureException("TableAlreadyExists")
                mock_service_instance.create_table.side_effect = mock_exception

                # Should not raise exception
                storage = DataStorage()

                assert storage.table_service == mock_service_instance


class TestDataStorageOperations:
    """Test suite for main data storage operations"""

    @pytest.fixture
    def mock_storage_with_service(self):
        """Create DataStorage with mocked table service"""
        storage = DataStorage()
        storage.table_service = Mock()
        storage.account_name = 'test_account'
        storage.account_key = 'test_key'
        return storage

    @pytest.fixture
    def mock_storage_without_service(self):
        """Create DataStorage without table service"""
        storage = DataStorage()
        storage.table_service = None
        return storage

    @pytest.fixture
    def sample_asset_data(self):
        """Sample asset data for testing"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'assets': {
                'BTC': {
                    'type': 'crypto',
                    'price': 95000.0,
                    'indicators': {
                        'mvrv': 2.1,
                        'weekly_rsi': 65.5,
                        'ema_200': 90000.0
                    },
                    'metadata': {
                        'source': 'hybrid_api',
                        'collection_time': datetime.utcnow().isoformat()
                    }
                },
                'MSTR': {
                    'type': 'stock',
                    'price': 425.67,
                    'indicators': {
                        'model_price': 398.12,
                        'deviation_pct': 6.9,
                        'iv': 53.0
                    },
                    'metadata': {
                        'source': 'mstr_analyzer',
                        'attempts': 1
                    }
                }
            }
        }

    @pytest.fixture
    def sample_error_data(self):
        """Sample data with errors for testing"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'assets': {
                'BTC': {
                    'type': 'crypto',
                    'error': 'API connection failed'
                }
            }
        }

    def test_store_daily_data_success(self, mock_storage_with_service, sample_asset_data):
        """Test successful daily data storage"""
        with patch('data_storage.datetime') as mock_datetime, \
                patch('data_storage.Entity') as mock_entity_class:
            # Mock current time
            mock_now = datetime(2024, 1, 15, 12, 0, 0)
            mock_datetime.utcnow.return_value = mock_now

            # Mock Entity creation
            mock_entity = Mock()
            mock_entity_class.return_value = mock_entity

            mock_storage_with_service.store_daily_data(sample_asset_data)

            # Verify entities were created for each asset
            assert mock_entity_class.call_count >= 2  # BTC + MSTR

            # Verify insert_or_replace_entity was called
            assert mock_storage_with_service.table_service.insert_or_replace_entity.call_count >= 2

    def test_store_daily_data_with_errors(self, mock_storage_with_service, sample_error_data):
        """Test daily data storage with error data"""
        with patch('data_storage.datetime') as mock_datetime, \
                patch('data_storage.Entity') as mock_entity_class, \
                patch.object(mock_storage_with_service, '_store_error_data') as mock_store_error:
            mock_now = datetime(2024, 1, 15, 12, 0, 0)
            mock_datetime.utcnow.return_value = mock_now

            mock_storage_with_service.store_daily_data(sample_error_data)

            # Verify error data storage was called
            mock_store_error.assert_called_once()

    def test_store_daily_data_no_service(self, mock_storage_without_service, sample_asset_data):
        """Test daily data storage without table service"""
        # Should not raise exception, just log warning
        mock_storage_without_service.store_daily_data(sample_asset_data)

    def test_store_error_data(self, mock_storage_with_service):
        """Test error data storage"""
        asset = 'BTC'
        asset_data = {
            'type': 'crypto',
            'error': 'Connection timeout'
        }
        date_key = '2024-01-15'
        timestamp = '2024-01-15T12:00:00'

        with patch('data_storage.Entity') as mock_entity_class:
            mock_entity = Mock()
            mock_entity_class.return_value = mock_entity

            mock_storage_with_service._store_error_data(asset, asset_data, date_key, timestamp)

            # Verify entity properties
            assert mock_entity.PartitionKey == asset
            assert mock_entity.RowKey == date_key
            assert mock_entity.collection_success is False
            assert mock_entity.error_message == 'Connection timeout'

            # Verify storage call
            mock_storage_with_service.table_service.insert_or_replace_entity.assert_called_once_with(
                'assetdata', mock_entity
            )

    def test_store_collection_summary(self, mock_storage_with_service):
        """Test collection summary storage"""
        date_key = '2024-01-15'
        timestamp = '2024-01-15T12:00:00'
        successful = 2
        failed = 1
        data = {}

        with patch('data_storage.Entity') as mock_entity_class:
            mock_entity = Mock()
            mock_entity_class.return_value = mock_entity

            mock_storage_with_service._store_collection_summary(date_key, timestamp, successful, failed, data)

            # Verify entity properties
            assert mock_entity.PartitionKey == 'SYSTEM'
            assert mock_entity.RowKey == f'SUMMARY_{date_key}'
            assert mock_entity.successful_collections == successful
            assert mock_entity.failed_collections == failed
            assert mock_entity.total_assets == successful + failed

            # Verify storage call
            mock_storage_with_service.table_service.insert_or_replace_entity.assert_called_once_with(
                'systemhealth', mock_entity
            )

    def test_get_historical_data_success(self, mock_storage_with_service):
        """Test successful historical data retrieval"""
        # Mock query entities response
        mock_entity1 = Mock()
        mock_entity1.RowKey = '2024-01-15'
        mock_entity1.Timestamp = '2024-01-15T12:00:00'
        mock_entity1.price = 95000.0
        mock_entity1.collection_success = True
        mock_entity1.indicators = '{"mvrv": 2.1, "weekly_rsi": 65.5}'
        mock_entity1.metadata = '{"source": "hybrid_api"}'

        mock_entity2 = Mock()
        mock_entity2.RowKey = '2024-01-14'
        mock_entity2.Timestamp = '2024-01-14T12:00:00'
        mock_entity2.price = 94000.0
        mock_entity2.collection_success = True
        mock_entity2.indicators = '{"mvrv": 2.0, "weekly_rsi": 60.0}'
        mock_entity2.metadata = '{"source": "hybrid_api"}'

        mock_storage_with_service.table_service.query_entities.return_value = [mock_entity1, mock_entity2]

        result = mock_storage_with_service.get_historical_data('BTC', days=7)

        assert len(result) == 2
        assert result[0]['date'] == '2024-01-15'  # Most recent first
        assert result[0]['price'] == 95000.0
        assert result[0]['success'] is True
        assert result[0]['indicators']['mvrv'] == 2.1
        assert result[1]['date'] == '2024-01-14'
        assert result[1]['price'] == 94000.0

    def test_get_historical_data_no_service(self, mock_storage_without_service):
        """Test historical data retrieval without table service"""
        result = mock_storage_without_service.get_historical_data('BTC', days=7)
        assert result == []

    def test_get_historical_data_invalid_json(self, mock_storage_with_service):
        """Test historical data retrieval with invalid JSON in indicators"""
        # Mock entity with invalid JSON
        mock_entity = Mock()
        mock_entity.RowKey = '2024-01-15'
        mock_entity.Timestamp = '2024-01-15T12:00:00'
        mock_entity.price = 95000.0
        mock_entity.collection_success = True
        mock_entity.indicators = 'invalid_json'  # Invalid JSON
        mock_entity.metadata = '{"source": "test"}'

        mock_storage_with_service.table_service.query_entities.return_value = [mock_entity]

        result = mock_storage_with_service.get_historical_data('BTC', days=7)

        # Should handle gracefully and skip invalid entries
        assert len(result) == 0  # Invalid entry skipped

    def test_get_latest_data_success(self, mock_storage_with_service):
        """Test latest data retrieval"""
        with patch.object(mock_storage_with_service, 'get_historical_data') as mock_get_historical:
            mock_historical_data = [
                {'date': '2024-01-15', 'price': 95000.0},
                {'date': '2024-01-14', 'price': 94000.0}
            ]
            mock_get_historical.return_value = mock_historical_data

            result = mock_storage_with_service.get_latest_data('BTC')

            assert result == mock_historical_data[0]
            mock_get_historical.assert_called_once_with('BTC', days=1)

    def test_get_latest_data_no_data(self, mock_storage_with_service):
        """Test latest data retrieval with no data"""
        with patch.object(mock_storage_with_service, 'get_historical_data', return_value=[]):
            result = mock_storage_with_service.get_latest_data('BTC')
            assert result is None


class TestAlertOperations:
    """Test suite for alert operations"""

    @pytest.fixture
    def storage_with_service(self):
        """Create DataStorage with mocked table service"""
        storage = DataStorage()
        storage.table_service = Mock()
        return storage

    @pytest.fixture
    def sample_alerts(self):
        """Sample alerts for testing"""
        return [
            {
                'asset': 'BTC',
                'type': 'mvrv_high',
                'message': 'BTC MVRV is high at 3.5',
                'severity': 'medium'
            },
            {
                'asset': 'MSTR',
                'type': 'overvalued',
                'message': 'MSTR is 25% overvalued',
                'severity': 'high'
            }
        ]

    def test_store_alert_history_success(self, storage_with_service, sample_alerts):
        """Test successful alert history storage"""
        with patch('data_storage.datetime') as mock_datetime, \
                patch('data_storage.Entity') as mock_entity_class:
            mock_now = datetime(2024, 1, 15, 12, 30, 45)
            mock_datetime.utcnow.return_value = mock_now

            mock_entity = Mock()
            mock_entity_class.return_value = mock_entity

            storage_with_service.store_alert_history(sample_alerts)

            # Verify entities were created for each alert
            assert mock_entity_class.call_count == len(sample_alerts)

            # Verify insert_entity was called for each alert
            assert storage_with_service.table_service.insert_entity.call_count == len(sample_alerts)

    def test_store_alert_history_no_service(self):
        """Test alert history storage without table service"""
        storage = DataStorage()
        storage.table_service = None

        # Should not raise exception
        storage.store_alert_history([{'asset': 'BTC', 'type': 'test'}])

    def test_store_alert_history_empty_alerts(self, storage_with_service):
        """Test alert history storage with empty alerts"""
        storage_with_service.store_alert_history([])

        # Should not make any storage calls
        storage_with_service.table_service.insert_entity.assert_not_called()

    def test_get_alert_history_success(self, storage_with_service):
        """Test successful alert history retrieval"""
        # Mock query response
        mock_entity1 = Mock()
        mock_entity1.PartitionKey = 'BTC'
        mock_entity1.Timestamp = '2024-01-15T12:00:00'
        mock_entity1.alert_type = 'mvrv_high'
        mock_entity1.message = 'BTC MVRV is high'
        mock_entity1.severity = 'medium'
        mock_entity1.date_created = '2024-01-15'

        mock_entity2 = Mock()
        mock_entity2.PartitionKey = 'MSTR'
        mock_entity2.Timestamp = '2024-01-14T12:00:00'
        mock_entity2.alert_type = 'overvalued'
        mock_entity2.message = 'MSTR overvalued'
        mock_entity2.severity = 'high'
        mock_entity2.date_created = '2024-01-14'

        storage_with_service.table_service.query_entities.return_value = [mock_entity1, mock_entity2]

        result = storage_with_service.get_alert_history(days=30)

        assert len(result) == 2
        assert result[0]['asset'] == 'BTC'
        assert result[0]['type'] == 'mvrv_high'
        assert result[0]['message'] == 'BTC MVRV is high'
        assert result[0]['severity'] == 'medium'

    def test_get_alert_history_for_specific_asset(self, storage_with_service):
        """Test alert history retrieval for specific asset"""
        storage_with_service.table_service.query_entities.return_value = []

        storage_with_service.get_alert_history(asset='BTC', days=30)

        # Verify query included asset filter
        args, kwargs = storage_with_service.table_service.query_entities.call_args
        assert 'BTC' in kwargs['filter']

    def test_get_alert_history_no_service(self):
        """Test alert history retrieval without table service"""
        storage = DataStorage()
        storage.table_service = None

        result = storage.get_alert_history()
        assert result == []


class TestAnalyticsOperations:
    """Test suite for data analytics operations"""

    @pytest.fixture
    def storage_with_service(self):
        """Create DataStorage with mocked table service"""
        storage = DataStorage()
        storage.table_service = Mock()
        return storage

    def test_get_data_analytics_success(self, storage_with_service):
        """Test successful data analytics generation"""
        # Mock historical data
        mock_historical_data = [
            {'date': '2024-01-15', 'price': 95000.0, 'success': True, 'indicators': {'mvrv': 2.1, 'rsi': 65}},
            {'date': '2024-01-14', 'price': 94000.0, 'success': True, 'indicators': {'mvrv': 2.0, 'rsi': 60}},
            {'date': '2024-01-13', 'price': 0.0, 'success': False, 'indicators': {}},  # Failed collection
        ]

        with patch.object(storage_with_service, 'get_historical_data', return_value=mock_historical_data):
            result = storage_with_service.get_data_analytics('BTC', days=30)

        assert result['asset'] == 'BTC'
        assert result['period_days'] == 30
        assert result['total_data_points'] == 3
        assert result['successful_collections'] == 2
        assert result['failed_collections'] == 1
        assert result['data_quality'] == (2 / 3) * 100  # 66.67%

        # Price analytics
        assert result['price_current'] == 95000.0
        assert result['price_min'] == 94000.0
        assert result['price_max'] == 95000.0
        assert result['price_avg'] == 94500.0  # Average of successful prices

        # Indicators analytics
        assert 'indicators' in result
        indicators = result['indicators']
        assert 'mvrv' in indicators
        assert indicators['mvrv']['current'] == 2.1
        assert indicators['mvrv']['min'] == 2.0
        assert indicators['mvrv']['max'] == 2.1
        assert indicators['mvrv']['count'] == 2

    def test_get_data_analytics_no_data(self, storage_with_service):
        """Test data analytics with no historical data"""
        with patch.object(storage_with_service, 'get_historical_data', return_value=[]):
            result = storage_with_service.get_data_analytics('BTC', days=30)

        assert 'error' in result
        assert result['error'] == 'No data available'

    def test_get_data_analytics_exception(self, storage_with_service):
        """Test data analytics with exception"""
        with patch.object(storage_with_service, 'get_historical_data', side_effect=Exception("Query failed")):
            result = storage_with_service.get_data_analytics('BTC', days=30)

        assert 'error' in result
        assert 'Query failed' in result['error']

    def test_analyze_indicators_success(self, storage_with_service):
        """Test indicator analysis"""
        # Create mock DataFrame
        mock_df = pd.DataFrame([
            {'indicators': {'mvrv': 2.1, 'rsi': 65.0}},
            {'indicators': {'mvrv': 2.0, 'rsi': 60.0}},
            {'indicators': {'mvrv': 1.9, 'rsi': 55.0}},
        ])

        result = storage_with_service._analyze_indicators(mock_df)

        assert 'mvrv' in result
        assert 'rsi' in result

        mvrv_stats = result['mvrv']
        assert mvrv_stats['current'] == 2.1
        assert mvrv_stats['min'] == 1.9
        assert mvrv_stats['max'] == 2.1
        assert mvrv_stats['count'] == 3

    def test_analyze_indicators_empty_data(self, storage_with_service):
        """Test indicator analysis with empty data"""
        mock_df = pd.DataFrame([])

        result = storage_with_service._analyze_indicators(mock_df)

        assert result == {}


class TestSystemHealthOperations:
    """Test suite for system health operations"""

    @pytest.fixture
    def storage_with_service(self):
        """Create DataStorage with mocked table service"""
        storage = DataStorage()
        storage.table_service = Mock()
        return storage

    def test_get_system_health_success(self, storage_with_service):
        """Test successful system health retrieval"""
        # Mock health entities
        mock_entity1 = Mock()
        mock_entity1.RowKey = 'SUMMARY_2024-01-15'
        mock_entity1.successful_collections = 2
        mock_entity1.failed_collections = 0
        mock_entity1.total_assets = 2
        mock_entity1.collection_time = '2024-01-15T12:00:00'

        mock_entity2 = Mock()
        mock_entity2.RowKey = 'SUMMARY_2024-01-14'
        mock_entity2.successful_collections = 1
        mock_entity2.failed_collections = 1
        mock_entity2.total_assets = 2
        mock_entity2.collection_time = '2024-01-14T12:00:00'

        storage_with_service.table_service.query_entities.return_value = [mock_entity1, mock_entity2]

        result = storage_with_service.get_system_health(days=7)

        assert result['period_days'] == 7
        assert result['total_collection_runs'] == 2
        assert result['total_asset_collections'] == 4  # 2 + 2
        assert result['successful_collections'] == 3  # 2 + 1
        assert result['failed_collections'] == 1  # 0 + 1
        assert result['overall_success_rate'] == 75.0  # 3/4 * 100

        # Check daily health data
        daily_health = result['daily_health']
        assert len(daily_health) == 2
        assert daily_health[0]['date'] == '2024-01-15'  # Most recent first
        assert daily_health[0]['success_rate'] == 100.0  # 2/2 * 100
        assert daily_health[1]['date'] == '2024-01-14'
        assert daily_health[1]['success_rate'] == 50.0  # 1/2 * 100

    def test_get_system_health_no_data(self, storage_with_service):
        """Test system health with no data"""
        storage_with_service.table_service.query_entities.return_value = []

        result = storage_with_service.get_system_health(days=7)

        assert result['period_days'] == 7
        assert result['total_collection_runs'] == 0
        assert 'message' in result
        assert 'No health data available' in result['message']

    def test_get_system_health_no_service(self):
        """Test system health without table service"""
        storage = DataStorage()
        storage.table_service = None

        result = storage.get_system_health(days=7)

        assert 'error' in result
        assert result['error'] == 'Storage not configured'


class TestDataCleanupOperations:
    """Test suite for data cleanup operations"""

    @pytest.fixture
    def storage_with_service(self):
        """Create DataStorage with mocked table service"""
        storage = DataStorage()
        storage.table_service = Mock()
        return storage

    def test_cleanup_old_data_success(self, storage_with_service):
        """Test successful old data cleanup"""
        # Mock old entities to delete
        mock_entity1 = Mock()
        mock_entity1.PartitionKey = 'BTC'
        mock_entity1.RowKey = '2023-01-01'

        mock_entity2 = Mock()
        mock_entity2.PartitionKey = 'MSTR'
        mock_entity2.RowKey = '2023-01-02'

        # Mock query_entities to return old entities for each table
        storage_with_service.table_service.query_entities.return_value = [mock_entity1, mock_entity2]

        with patch('data_storage.datetime') as mock_datetime:
            mock_now = datetime(2024, 4, 15)  # 90+ days after mock entities
            mock_datetime.utcnow.return_value = mock_now

            result = storage_with_service.cleanup_old_data(retention_days=90)

        assert result['entities_deleted'] == 6  # 2 entities × 3 tables = 6 total
        assert result['tables_processed'] == 3
        assert len(result['errors']) == 0

        # Verify delete_entity was called for each entity in each table
        assert storage_with_service.table_service.delete_entity.call_count == 6

    def test_cleanup_old_data_with_errors(self, storage_with_service):
        """Test data cleanup with deletion errors"""
        mock_entity = Mock()
        mock_entity.PartitionKey = 'BTC'
        mock_entity.RowKey = '2023-01-01'

        storage_with_service.table_service.query_entities.return_value = [mock_entity]
        storage_with_service.table_service.delete_entity.side_effect = Exception("Delete failed")

        with patch('data_storage.datetime') as mock_datetime:
            mock_now = datetime(2024, 4, 15)
            mock_datetime.utcnow.return_value = mock_now

            result = storage_with_service.cleanup_old_data(retention_days=90)

        assert result['entities_deleted'] == 0  # No successful deletions
        assert len(result['errors']) > 0  # Should have error messages

    def test_cleanup_old_data_no_service(self):
        """Test data cleanup without table service"""
        storage = DataStorage()
        storage.table_service = None

        result = storage.cleanup_old_data(retention_days=90)

        assert 'error' in result
        assert result['error'] == 'Storage not configured'


class TestExportOperations:
    """Test suite for data export operations"""

    @pytest.fixture
    def storage_with_service(self):
        """Create DataStorage with mocked table service"""
        storage = DataStorage()
        storage.table_service = Mock()
        return storage

    def test_export_data_to_csv_success(self, storage_with_service, tmp_path):
        """Test successful CSV export"""
        # Mock historical data
        mock_historical_data = [
            {
                'date': '2024-01-15',
                'timestamp': '2024-01-15T12:00:00',
                'price': 95000.0,
                'success': True,
                'indicators': {'mvrv': 2.1, 'rsi': 65.0}
            },
            {
                'date': '2024-01-14',
                'timestamp': '2024-01-14T12:00:00',
                'price': 94000.0,
                'success': True,
                'indicators': {'mvrv': 2.0, 'rsi': 60.0}
            }
        ]

        with patch.object(storage_with_service, 'get_historical_data', return_value=mock_historical_data), \
                patch('data_storage.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 15)
            mock_datetime.utcnow.return_value = mock_now

            # Use temporary directory for test output
            output_path = tmp_path / "test_export.csv"

            result = storage_with_service.export_data_to_csv('BTC', days=30, output_path=str(output_path))

            assert result == str(output_path)
            assert output_path.exists()

    def test_export_data_to_csv_no_data(self, storage_with_service):
        """Test CSV export with no data"""
        with patch.object(storage_with_service, 'get_historical_data', return_value=[]):
            with pytest.raises(Exception, match='No data available for BTC'):
                storage_with_service.export_data_to_csv('BTC', days=30)

    def test_export_data_to_csv_default_filename(self, storage_with_service, tmp_path):
        """Test CSV export with default filename"""
        mock_historical_data = [
            {
                'date': '2024-01-15',
                'timestamp': '2024-01-15T12:00:00',
                'price': 95000.0,
                'success': True,
                'indicators': {}
            }
        ]

        with patch.object(storage_with_service, 'get_historical_data', return_value=mock_historical_data), \
                patch('data_storage.datetime') as mock_datetime, \
                patch('data_storage.pd.DataFrame.to_csv') as mock_to_csv:
            mock_now = datetime(2024, 1, 15)
            mock_datetime.utcnow.return_value = mock_now
            mock_datetime.utcnow.strftime = lambda fmt: mock_now.strftime(fmt)

            result = storage_with_service.export_data_to_csv('BTC', days=30)

            # Should generate default filename
            assert 'BTC_data_20240115.csv' in result


# Test runner and utility functions
def run_quick_test():
    """Quick test function for development use"""
    logging.info("Running quick data_storage tests...")

    # Test basic initialization
    storage = DataStorage()
    assert hasattr(storage, 'table_name')
    assert hasattr(storage, 'alerts_table')
    assert hasattr(storage, 'health_table')
    assert hasattr(storage, 'monetary_table')
    logging.info("✅ Basic initialization test passed")

    # Test without credentials
    assert storage.table_service is None  # No credentials provided
    logging.info("✅ No credentials handling test passed")

    # Test date range filter building
    start_date = datetime(2024, 1, 10)
    end_date = datetime(2024, 1, 15)
    filter_str = storage._build_date_range_filter(start_date, end_date)
    assert '2024-01-10' in filter_str
    assert '2024-01-15' in filter_str
    logging.info("✅ Date range filter test passed")

    logging.info("✅ Quick tests completed successfully!")


if __name__ == '__main__':
    # Run quick test if executed directly
    run_quick_test()

    # For full test suite, use: pytest tests/test_data_storage.py -v
    print("\n" + "=" * 70)
    print("DATA STORAGE TEST SUITE")
    print("=" * 70)
    print("To run full test suite:")
    print("  pytest tests/test_data_storage.py -v")
    print("\nTo run specific test categories:")
    print("  pytest tests/test_data_storage.py::TestDataStorageInitialization -v")
    print("  pytest tests/test_data_storage.py::TestDataStorageOperations -v")
    print("  pytest tests/test_data_storage.py::TestAlertOperations -v")
    print("  pytest tests/test_data_storage.py::TestAnalyticsOperations -v")
    print("  pytest tests/test_data_storage.py::TestSystemHealthOperations -v")
    print("  pytest tests/test_data_storage.py::TestDataCleanupOperations -v")
    print("  pytest tests/test_data_storage.py::TestExportOperations -v")
    print("\nFor CI/CD environments:")
    print("  CI=true pytest tests/test_data_storage.py")