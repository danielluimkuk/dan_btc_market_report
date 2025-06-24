"""
conftest.py - Shared pytest fixtures for all tests

This file provides shared fixtures that can be used across all test files
to fix the missing fixture errors in GitHub Actions.
"""

import pytest
import os
from unittest.mock import Mock, patch
from datetime import datetime, timezone


# =============================================================================
# MSTR Test Scenario Fixtures
# =============================================================================

@pytest.fixture(params=[
    "Severely Overvalued + High Volatility",
    "Severely Overvalued + Low Volatility", 
    "Moderately Overvalued + Normal Volatility",
    "Fair Valued + High Volatility",
    "Fair Valued + Low Volatility",
    "Severely Undervalued + Low Volatility",
    "MSTR Collection Error"
])
def scenario_name(request):
    """Fixture providing different MSTR test scenario names"""
    return request.param


@pytest.fixture
def mstr_data(scenario_name):
    """Fixture providing MSTR test data based on scenario name"""
    
    def create_mstr_scenario(scenario_name, price, model_price, iv, iv_percentile, iv_rank, error=None):
        """Create MSTR data for specific scenario"""
        if error:
            return {
                'type': 'stock',
                'error': error,
                'last_updated': datetime.now(timezone.utc).isoformat()
            }

        deviation_pct = ((price - model_price) / model_price) * 100

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
            'analysis': {
                'price_signal': {
                    'status': 'overvalued' if deviation_pct >= 25 else 'undervalued' if deviation_pct <= -20 else 'neutral',
                    'signal': 'SELL' if deviation_pct >= 25 else 'BUY' if deviation_pct <= -20 else 'HOLD',
                    'message': f'MSTR {"Overvalued" if deviation_pct >= 25 else "Undervalued" if deviation_pct <= -20 else "Fair Valued"} ({deviation_pct:+.1f}%)'
                },
                'options_strategy': {
                    'primary_strategy': 'no_preference',
                    'message': 'No Strong Options Preference',
                    'description': 'Normal volatility + fair valuation'
                }
            },
            'metadata': {
                'source': 'mstr_analyzer',
                'scenario': scenario_name
            },
            'last_updated': datetime.now(timezone.utc).isoformat()
        }

    # Map scenario names to data
    scenario_mapping = {
        "Severely Overvalued + High Volatility": 
            create_mstr_scenario(scenario_name, 500, 350, 95.2, 85, 82),
        "Severely Overvalued + Low Volatility": 
            create_mstr_scenario(scenario_name, 480, 350, 45.3, 15, 18),
        "Moderately Overvalued + Normal Volatility": 
            create_mstr_scenario(scenario_name, 440, 350, 68.4, 45, 52),
        "Fair Valued + High Volatility": 
            create_mstr_scenario(scenario_name, 360, 350, 89.7, 78, 75),
        "Fair Valued + Low Volatility": 
            create_mstr_scenario(scenario_name, 365, 350, 35.2, 22, 19),
        "Severely Undervalued + Low Volatility": 
            create_mstr_scenario(scenario_name, 250, 350, 42.1, 12, 15),
        "MSTR Collection Error": 
            create_mstr_scenario(scenario_name, 0, 0, 0, 0, 0, error="Failed to scrape ballistic data: Timeout")
    }
    
    return scenario_mapping.get(scenario_name, scenario_mapping["Fair Valued + Low Volatility"])


# =============================================================================
# Options Testing Fixtures
# =============================================================================

@pytest.fixture(params=[20, 35, 50, 65, 80])
def iv_percentile(request):
    """Fixture providing different IV percentile values for testing"""
    return request.param


@pytest.fixture(params=[15, 30, 45, 60, 75])
def iv_rank(request):
    """Fixture providing different IV rank values for testing"""
    return request.param


@pytest.fixture(params=[-25, -10, 5, 15, 30])
def deviation_pct(request):
    """Fixture providing different deviation percentages for testing"""
    return request.param


@pytest.fixture(params=['undervalued', 'neutral', 'overvalued'])
def price_signal_status(request):
    """Fixture providing different price signal statuses for testing"""
    return request.param


@pytest.fixture(params=[True, False])
def volatility_conflicting(request):
    """Fixture providing volatility conflict scenarios"""
    return request.param


# =============================================================================
# Common Test Data Fixtures
# =============================================================================

@pytest.fixture
def sample_btc_data():
    """Fixture providing sample BTC data for testing"""
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
    """Fixture providing sample MSTR data for testing"""
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
                'message': 'No Strong Options Preference'
            }
        },
        'metadata': {'source': 'mstr_analyzer'},
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def sample_monetary_data():
    """Fixture providing sample monetary data for testing"""
    return {
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


# =============================================================================
# Environment and Mock Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def mock_azure_completely():
    """Completely mock Azure to prevent connection/padding errors"""
    with patch('azure.cosmosdb.table.TableService') as mock_table_service:
        mock_service = Mock()
        mock_service.create_table = Mock()
        mock_service.insert_or_replace_entity = Mock()
        mock_service.insert_entity = Mock()
        mock_service.query_entities = Mock(return_value=[])
        mock_service.delete_entity = Mock()
        mock_table_service.return_value = mock_service
        
        with patch('azure.cosmosdb.table.models.Entity', Mock):
            with patch('azure.cosmosdb.table.models.AzureException', Exception):
                yield

@pytest.fixture(autouse=True)
def mock_environment():
    """Automatically mock environment variables for all tests"""
    env_vars = {
        'POLYGON_API_KEY': 'test_polygon_key',
        'FRED_API_KEY': 'test_fred_key',
        'EMAIL_USER': 'test@example.com',
        'EMAIL_PASSWORD': 'test_password',
        'RECIPIENT_EMAILS': 'test1@example.com,test2@example.com',
        'AZURE_STORAGE_ACCOUNT': 'test_storage',
        'AZURE_STORAGE_KEY': 'test_key',
        'IMGUR_CLIENT_ID': 'test_imgur_client'
    }
    
    with patch.dict(os.environ, env_vars):
        yield


@pytest.fixture
def mock_storage():
    """Fixture providing a mock DataStorage instance"""
    mock_storage = Mock()
    mock_storage.table_service = Mock()
    return mock_storage


@pytest.fixture
def mock_webdriver():
    """Fixture providing a mock WebDriver for testing"""
    with patch('selenium.webdriver.Chrome') as mock_chrome:
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        yield mock_driver


# =============================================================================
# Pytest Configuration
# =============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_network: mark test as requiring network access"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names"""
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)
        
        # Mark slow tests
        if any(keyword in item.nodeid.lower() for keyword in ["full", "comprehensive", "complete"]):
            item.add_marker(pytest.mark.slow)
        
        # Mark tests that need network
        if any(keyword in item.nodeid.lower() for keyword in ["api", "screenshot", "imgur"]):
            item.add_marker(pytest.mark.requires_network)


# =============================================================================
# Test Utilities
# =============================================================================

@pytest.fixture
def create_test_image():
    """Fixture that creates a test image as base64"""
    # Minimal PNG image as base64
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAHPn4JI0QAAAABJRU5ErkJggg=="


@pytest.fixture
def mock_logger():
    """Fixture providing a mock logger"""
    with patch('logging.getLogger') as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        yield mock_logger


# =============================================================================
# Cleanup Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Automatically cleanup after each test"""
    yield
    # Cleanup code here if needed
    # e.g., close any open files, reset global state, etc.
