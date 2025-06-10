import pytest
import json
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime, timezone
import requests

# Test for mstr_analyzer.py
# =============================================================================

class TestMSTRAnalyzer:
    """Unit tests for MSTRAnalyzer class"""

    @pytest.fixture
    def analyzer(self):
        """Create MSTRAnalyzer instance for testing"""
        from mstr_analyzer import MSTRAnalyzer
        return MSTRAnalyzer()

    def test_calculate_model_price(self, analyzer):
        """Test ballistic model price calculation"""
        btc_price = 95000.0

        result = analyzer._calculate_model_price(btc_price)

        # Should return a reasonable MSTR price
        assert isinstance(result, float)
        assert 1 < result < 10000

    def test_extract_price_from_text_valid(self, analyzer):
        """Test extracting price from valid text"""
        test_cases = [
            ("$425.67", 425.67),
            ("Price: 350.25", 350.25),
            ("Current: $275", 275.0),
            ("1,234.56", 1234.56)
        ]

        for text, expected in test_cases:
            result = analyzer._extract_price_from_text(text)
            assert result == expected

    def test_extract_price_from_text_invalid(self, analyzer):
        """Test extracting price from invalid text"""
        test_cases = [
            "No price here",
            "$15000",  # Too high
            "$0.50",  # Too low
            "Price: N/A"
        ]

        for text in test_cases:
            result = analyzer._extract_price_from_text(text)
            assert result is None

    def test_extract_percentage_from_text_valid(self, analyzer):
        """Test extracting percentage from valid text"""
        test_cases = [
            ("Overvalued by 25.5%", 25.5),
            ("Undervalued by 15.2%", -15.2),  # Should be negative
            ("Change: +12.3%", 12.3),
            ("Down -8.7%", -8.7)
        ]

        for text, expected in test_cases:
            result = analyzer._extract_percentage_from_text(text)
            assert result == expected

    def test_extract_percentage_from_text_invalid(self, analyzer):
        """Test extracting percentage from invalid text"""
        test_cases = [
            "No percentage here",
            "150%",  # Outside reasonable range
            "Invalid text"
        ]

        for text in test_cases:
            result = analyzer._extract_percentage_from_text(text)
            assert result is None

    @patch('mstr_analyzer.webdriver.Chrome')
    def test_get_ballistic_data_xpath_success(self, mock_chrome, analyzer):
        """Test successful ballistic data collection"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        # Mock model price element
        mock_model_element = Mock()
        mock_model_element.text = "$398.12"

        # Mock deviation element
        mock_dev_element = Mock()
        mock_dev_element.text = "Overvalued by 6.9%"

        # Configure WebDriverWait mock
        with patch('mstr_analyzer.WebDriverWait') as mock_wait:
            mock_wait.return_value.until.side_effect = [mock_model_element, mock_dev_element]

            result = analyzer._get_ballistic_data_xpath(95000.0)

        assert result['success'] is True
        assert 'model_price' in result
        assert 'deviation_pct' in result
        assert 'actual_price' in result
        mock_driver.quit.assert_called_once()

    @patch('mstr_analyzer.webdriver.Chrome')
    def test_get_ballistic_data_xpath_fallback(self, mock_chrome, analyzer):
        """Test ballistic data collection with fallback calculation"""
        mock_chrome.side_effect = Exception("WebDriver failed")

        result = analyzer._get_ballistic_data_xpath(95000.0)

        assert result['success'] is True
        assert result['source'] == 'calculated_fallback'
        assert 'model_price' in result
        assert result['btc_price_used'] == 95000.0

    def test_determine_options_strategy_low_iv_bullish(self, analyzer):
        """Test options strategy for low IV + bullish scenario"""
        result = analyzer._determine_options_strategy(
            iv_percentile=25.0,
            iv_rank=20.0,
            deviation_pct=-22.0,  # Undervalued
            price_signal_status='undervalued',
            volatility_conflicting=False
        )

        assert result['primary_strategy'] == 'long_calls'
        assert 'cheap options' in result['description'].lower()
        assert result['confidence'] == 'high'

    def test_determine_options_strategy_high_iv_bearish(self, analyzer):
        """Test options strategy for high IV + bearish scenario"""
        result = analyzer._determine_options_strategy(
            iv_percentile=80.0,
            iv_rank=75.0,
            deviation_pct=28.0,  # Overvalued
            price_signal_status='overvalued',
            volatility_conflicting=False
        )

        assert result['primary_strategy'] == 'short_calls'
        assert 'expensive options' in result['description'].lower()
        assert result['confidence'] == 'medium'

    def test_determine_options_strategy_conflicting(self, analyzer):
        """Test options strategy when volatility signals conflict"""
        result = analyzer._determine_options_strategy(
            iv_percentile=25.0,
            iv_rank=75.0,  # Conflicting signals
            deviation_pct=5.0,
            price_signal_status='neutral',
            volatility_conflicting=True
        )

        assert result['primary_strategy'] == 'wait'
        assert result['confidence'] == 'low'

    def test_analyze_mstr_complete_success(self, analyzer):
        """Test complete MSTR analysis with successful data collection"""
        with patch.object(analyzer, '_get_ballistic_data_xpath') as mock_ballistic, \
                patch.object(analyzer, '_get_volatility_data') as mock_volatility:
            mock_ballistic.return_value = {
                'success': True,
                'model_price': 398.12,
                'actual_price': 425.67,
                'deviation_pct': 6.9,
                'btc_price_used': 95000.0
            }

            mock_volatility.return_value = {
                'success': True,
                'iv': 53.0,
                'iv_percentile': 45.0,
                'iv_rank': 40.0
            }

            result = analyzer.analyze_mstr(95000.0)

            assert result['success'] is True
            assert 'ballistic_data' in result
            assert 'volatility_data' in result
            assert 'analysis' in result

    def test_analyze_mstr_failure(self, analyzer):
        """Test MSTR analysis when data collection fails"""
        with patch.object(analyzer, '_get_ballistic_data_xpath') as mock_ballistic:
            mock_ballistic.side_effect = Exception("Data collection failed")

            result = analyzer.analyze_mstr(95000.0)

            assert result['success'] is False
            assert 'error' in result


class TestMSTRDataValidation:
    """Test MSTR data validation functions"""

    def test_validate_mstr_data_valid(self):
        """Test validation with valid MSTR data"""
        from mstr_analyzer import _validate_mstr_data

        valid_data = {
            'success': True,
            'price': 425.67,
            'indicators': {
                'model_price': 398.12,
                'deviation_pct': 6.9,
                'iv': 53.0,
                'iv_percentile': 45.0,
                'iv_rank': 40.0
            }
        }

        result = _validate_mstr_data(valid_data)
        assert result is True

    def test_validate_mstr_data_missing_iv(self):
        """Test validation with missing main IV data"""
        from mstr_analyzer import _validate_mstr_data

        invalid_data = {
            'success': True,
            'price': 425.67,
            'indicators': {
                'model_price': 398.12,
                'deviation_pct': 6.9,
                'iv': 0,  # Missing main IV
                'iv_percentile': 45.0,
                'iv_rank': 40.0
            }
        }

        result = _validate_mstr_data(invalid_data)
        assert result is False

    def test_validate_mstr_data_invalid_price(self):
        """Test validation with invalid price"""
        from mstr_analyzer import _validate_mstr_data

        invalid_data = {
            'success': True,
            'price': 0,  # Invalid price
            'indicators': {
                'model_price': 398.12,
                'deviation_pct': 6.9,
                'iv': 53.0
            }
        }

        result = _validate_mstr_data(invalid_data)
        assert result is False

    def test_validate_mstr_data_extreme_deviation(self):
        """Test validation with extreme deviation"""
        from mstr_analyzer import _validate_mstr_data

        invalid_data = {
            'success': True,
            'price': 425.67,
            'indicators': {
                'model_price': 398.12,
                'deviation_pct': 250.0,  # Extreme deviation
                'iv': 53.0
            }
        }

        result = _validate_mstr_data(invalid_data)
        assert result is False


class TestMSTRRetryMechanism:
    """Test MSTR retry mechanism"""

    @patch('mstr_analyzer.collect_mstr_data')
    @patch('mstr_analyzer._validate_mstr_data')
    @patch('mstr_analyzer.time.sleep')
    def test_collect_mstr_data_with_retry_success_first_attempt(self, mock_sleep, mock_validate, mock_collect):
        """Test successful data collection on first attempt"""
        from mstr_analyzer import collect_mstr_data_with_retry

        valid_data = {'success': True, 'price': 425.67}
        mock_collect.return_value = valid_data
        mock_validate.return_value = True

        result = collect_mstr_data_with_retry(95000.0)

        assert result == valid_data
        mock_collect.assert_called_once()
        mock_sleep.assert_not_called()

    @patch('mstr_analyzer.collect_mstr_data')
    @patch('mstr_analyzer._validate_mstr_data')
    @patch('mstr_analyzer.time.sleep')
    def test_collect_mstr_data_with_retry_success_second_attempt(self, mock_sleep, mock_validate, mock_collect):
        """Test successful data collection on second attempt"""
        from mstr_analyzer import collect_mstr_data_with_retry

        invalid_data = {'success': True, 'price': 0}  # Invalid first attempt
        valid_data = {'success': True, 'price': 425.67}  # Valid second attempt

        mock_collect.side_effect = [invalid_data, valid_data]
        mock_validate.side_effect = [False, True]

        result = collect_mstr_data_with_retry(95000.0, max_attempts=2)

        assert result == valid_data
        assert mock_collect.call_count == 2
        mock_sleep.assert_called_once()

    @patch('mstr_analyzer.collect_mstr_data')
    @patch('mstr_analyzer._validate_mstr_data')
    @patch('mstr_analyzer.time.sleep')
    def test_collect_mstr_data_with_retry_all_attempts_fail(self, mock_sleep, mock_validate, mock_collect):
        """Test when all retry attempts fail"""
        from mstr_analyzer import collect_mstr_data_with_retry

        invalid_data = {'success': True, 'price': 0}
        mock_collect.return_value = invalid_data
        mock_validate.return_value = False

        result = collect_mstr_data_with_retry(95000.0, max_attempts=2)

        assert result['success'] is False
        assert 'failed after 2 attempts' in result['error']
        assert result['attempts_made'] == 2
        assert mock_collect.call_count == 2
