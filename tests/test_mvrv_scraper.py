import pytest
import json
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime, timezone
import requests


# =============================================================================
# Test for mvrv_scraper.py
# =============================================================================

class TestMVRVScraper:
    """Unit tests for MVRVScraper class"""

    @pytest.fixture
    def scraper(self):
        """Create MVRVScraper instance for testing"""
        from mvrv_scraper import MVRVScraper
        return MVRVScraper()

    @patch('mvrv_scraper.webdriver.Chrome')
    def test_scrape_mvrv_method1_success(self, mock_chrome, scraper):
        """Test successful MVRV scraping with Method 1"""
        # Mock WebDriver
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        # Mock element with MVRV data
        mock_element = Mock()
        mock_element.text = "MVRV: 2.45"
        mock_driver.find_elements.return_value = [mock_element]

        result = scraper.scrape_mvrv_method1_selenium_wait()

        assert result == 2.45
        mock_driver.get.assert_called_once()
        mock_driver.quit.assert_called_once()

    @patch('mvrv_scraper.webdriver.Chrome')
    def test_scrape_mvrv_method1_no_data(self, mock_chrome, scraper):
        """Test Method 1 when no MVRV data is found"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        mock_driver.find_elements.return_value = []
        mock_driver.page_source = "<html>No MVRV data</html>"

        result = scraper.scrape_mvrv_method1_selenium_wait()

        assert result is None
        mock_driver.quit.assert_called_once()

    @patch('mvrv_scraper.webdriver.Chrome')
    def test_scrape_mvrv_method1_driver_exception(self, mock_chrome, scraper):
        """Test Method 1 handling WebDriver exceptions"""
        mock_chrome.side_effect = Exception("WebDriver failed")

        result = scraper.scrape_mvrv_method1_selenium_wait()

        assert result is None

    @patch('mvrv_scraper.requests.get')
    def test_scrape_mvrv_method3_success(self, mock_get, scraper):
        """Test successful API-based scraping with Method 3"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"mvrv": 3.15}]}
        mock_get.return_value = mock_response

        # Mock the _extract_mvrv_from_json method to return the value
        with patch.object(scraper, '_extract_mvrv_from_json', return_value=3.15):
            result = scraper.scrape_mvrv_method3_direct_api()

        assert result == 3.15

    @patch('mvrv_scraper.requests.post')
    def test_scrape_mvrv_method3_api_failure(self, mock_post, scraper):
        """Test Method 3 handling API failures"""
        mock_post.side_effect = requests.exceptions.RequestException("API failed")

        result = scraper.scrape_mvrv_method3_direct_api()

        assert result is None

    def test_extract_mvrv_from_json_success(self, scraper):
        """Test extracting MVRV value from JSON data"""
        test_data = {"mvrv": 2.67, "other_data": "test"}

        result = scraper._extract_mvrv_from_json(test_data)

        assert result == 2.67

    def test_extract_mvrv_from_json_no_mvrv(self, scraper):
        """Test extracting MVRV when no valid data exists"""
        test_data = {"price": 45000, "volume": 1000000}

        result = scraper._extract_mvrv_from_json(test_data)

        assert result is None

    def test_extract_mvrv_from_json_invalid_range(self, scraper):
        """Test extracting MVRV with values outside valid range"""
        test_data = {"mvrv": 15.0}  # Too high for valid MVRV

        result = scraper._extract_mvrv_from_json(test_data)

        assert result is None

    def test_get_mvrv_value_fallback(self, scraper):
        """Test that get_mvrv_value returns fallback when all methods fail"""
        with patch.object(scraper, 'scrape_mvrv_method1_selenium_wait', return_value=None), \
                patch.object(scraper, 'scrape_mvrv_method2_api_intercept', return_value=None), \
                patch.object(scraper, 'scrape_mvrv_method3_direct_api', return_value=None), \
                patch.object(scraper, 'scrape_mvrv_method4_execute_js', return_value=None):
            result = scraper.get_mvrv_value()

            assert result == 2.1  # Fallback value

    def test_get_mvrv_value_first_method_success(self, scraper):
        """Test that get_mvrv_value returns from first successful method"""
        with patch.object(scraper, 'scrape_mvrv_method1_selenium_wait', return_value=2.89):
            result = scraper.get_mvrv_value()

            assert result == 2.89
