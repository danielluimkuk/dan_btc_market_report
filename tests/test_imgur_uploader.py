import pytest
import json
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime, timezone
import requests


class TestImgurUploader:
    """Unit tests for ImgurUploader class"""

    @pytest.fixture
    def uploader(self):
        """Create ImgurUploader instance for testing"""
        from imgur_uploader import ImgurUploader
        with patch.dict('os.environ', {'IMGUR_CLIENT_ID': 'test_client_id'}):
            return ImgurUploader()

    @pytest.fixture
    def uploader_no_key(self):
        """Create ImgurUploader instance without API key"""
        from imgur_uploader import ImgurUploader
        with patch.dict('os.environ', {}, clear=True):
            return ImgurUploader()

    def test_init_with_client_id(self):
        """Test initialization with valid client ID"""
        from imgur_uploader import ImgurUploader

        with patch.dict('os.environ', {'IMGUR_CLIENT_ID': 'test_client_id'}):
            uploader = ImgurUploader()
            assert uploader.client_id == 'test_client_id'
            assert uploader.upload_url == "https://api.imgur.com/3/image"

    def test_init_without_client_id(self):
        """Test initialization without client ID"""
        from imgur_uploader import ImgurUploader

        with patch.dict('os.environ', {}, clear=True):
            uploader = ImgurUploader()
            assert uploader.client_id is None

    @patch('imgur_uploader.requests.post')
    def test_upload_base64_image_success(self, mock_post, uploader):
        """Test successful base64 image upload"""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            'success': True,
            'data': {'link': 'https://i.imgur.com/test123.png'}
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        test_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAHPn4JI0QAAAABJRU5ErkJggg=="

        result = uploader.upload_base64_image(test_b64, "Test Image")

        assert result == 'https://i.imgur.com/test123.png'
        mock_post.assert_called_once()

        # Verify request parameters
        call_args = mock_post.call_args
        assert 'Authorization' in call_args[1]['headers']
        assert 'Client-ID test_client_id' in call_args[1]['headers']['Authorization']

    def test_upload_base64_image_no_client_id(self, uploader_no_key):
        """Test upload attempt without client ID"""
        test_b64 = "test_base64_data"

        result = uploader_no_key.upload_base64_image(test_b64)

        assert result is None

    def test_upload_base64_image_empty_data(self, uploader):
        """Test upload with empty image data"""
        result = uploader.upload_base64_image("")

        assert result is None

    def test_upload_base64_image_none_data(self, uploader):
        """Test upload with None image data"""
        result = uploader.upload_base64_image(None)

        assert result is None

    @patch('imgur_uploader.requests.post')
    def test_upload_base64_image_api_failure(self, mock_post, uploader):
        """Test upload with API failure"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'success': False,
            'data': {'error': 'Invalid image'}
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        test_b64 = "test_base64_data"
        result = uploader.upload_base64_image(test_b64)

        assert result is None

    @patch('imgur_uploader.requests.post')
    def test_upload_base64_image_network_error(self, mock_post, uploader):
        """Test upload with network error"""
        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        test_b64 = "test_base64_data"
        result = uploader.upload_base64_image(test_b64)

        assert result is None

    @patch('imgur_uploader.requests.post')
    def test_upload_base64_image_timeout(self, mock_post, uploader):
        """Test upload with timeout"""
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        test_b64 = "test_base64_data"
        result = uploader.upload_base64_image(test_b64)

        assert result is None

    @patch('builtins.open', new_callable=mock_open, read_data=b'fake_image_data')
    @patch('imgur_uploader.base64.b64encode')
    def test_upload_image_file_success(self, mock_b64encode, mock_file, uploader):
        """Test successful file upload"""
        mock_b64encode.return_value = b'encoded_data'

        with patch.object(uploader, 'upload_base64_image', return_value='https://i.imgur.com/test.png') as mock_upload:
            result = uploader.upload_image_file('/path/to/image.png')

            assert result == 'https://i.imgur.com/test.png'
            mock_upload.assert_called_once_with('encoded_data', 'Bitcoin Laws Screenshot')

    def test_upload_image_file_not_found(self, uploader):
        """Test file upload with non-existent file"""
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            result = uploader.upload_image_file('/nonexistent/file.png')

            assert result is None

    def test_upload_image_file_no_client_id(self, uploader_no_key):
        """Test file upload without client ID"""
        result = uploader_no_key.upload_image_file('/path/to/image.png')

        assert result is None


class TestImgurTestFunction:
    """Test the test function for Imgur uploader"""

    @patch('imgur_uploader.ImgurUploader')
    def test_imgur_upload_success(self, mock_uploader_class):
        """Test successful Imgur upload test"""
        from imgur_uploader import test_imgur_upload

        mock_uploader = Mock()
        mock_uploader.client_id = 'test_client_id'
        mock_uploader.upload_base64_image.return_value = 'https://i.imgur.com/test.png'
        mock_uploader_class.return_value = mock_uploader

        result = test_imgur_upload()

        assert result is True

    @patch('imgur_uploader.ImgurUploader')
    def test_imgur_upload_no_client_id(self, mock_uploader_class):
        """Test Imgur upload test without client ID"""
        from imgur_uploader import test_imgur_upload

        mock_uploader = Mock()
        mock_uploader.client_id = None
        mock_uploader_class.return_value = mock_uploader

        result = test_imgur_upload()

        assert result is False

    @patch('imgur_uploader.ImgurUploader')
    def test_imgur_upload_failure(self, mock_uploader_class):
        """Test Imgur upload test failure"""
        from imgur_uploader import test_imgur_upload

        mock_uploader = Mock()
        mock_uploader.client_id = 'test_client_id'
        mock_uploader.upload_base64_image.return_value = None
        mock_uploader_class.return_value = mock_uploader

        result = test_imgur_upload()

        assert result is False


# =============================================================================
# Test Configuration and Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def mock_logging():
    """Mock logging to prevent test output pollution"""
    with patch('logging.info'), \
            patch('logging.warning'), \
            patch('logging.error'):
        yield


@pytest.fixture(autouse=True)
def mock_time_sleep():
    """Mock time.sleep to speed up tests"""
    with patch('time.sleep'):
        yield


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for module interactions"""

    def test_mstr_collect_data_format(self):
        """Test that collect_mstr_data returns expected format"""
        from mstr_analyzer import collect_mstr_data

        with patch('mstr_analyzer.MSTRAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_result = {
                'success': True,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'ballistic_data': {
                    'model_price': 398.12,
                    'actual_price': 425.67,
                    'deviation_pct': 6.9
                },
                'volatility_data': {
                    'iv': 53.0,
                    'iv_percentile': 45.0,
                    'iv_rank': 40.0
                },
                'analysis': {}
            }
            mock_analyzer.analyze_mstr.return_value = mock_result
            mock_analyzer_class.return_value = mock_analyzer

            result = collect_mstr_data(95000.0)

            # Check expected format
            assert 'success' in result
            assert 'type' in result
            assert 'timestamp' in result
            assert 'price' in result
            assert 'indicators' in result
            assert 'metadata' in result

            # Check specific values
            assert result['type'] == 'stock'
            assert result['price'] == 425.67
            assert result['indicators']['model_price'] == 398.12


# =============================================================================
# Performance Tests
# =============================================================================

class TestPerformance:
    """Performance-related tests"""

    def test_mvrv_scraper_timeout_handling(self):
        """Test that MVRV scraper handles timeouts gracefully"""
        from mvrv_scraper import MVRVScraper

        scraper = MVRVScraper()

        # Mock all methods to simulate timeouts
        with patch.object(scraper, 'scrape_mvrv_method1_selenium_wait', side_effect=Exception("Timeout")), \
                patch.object(scraper, 'scrape_mvrv_method2_api_intercept', side_effect=Exception("Timeout")), \
                patch.object(scraper, 'scrape_mvrv_method3_direct_api', side_effect=Exception("Timeout")), \
                patch.object(scraper, 'scrape_mvrv_method4_execute_js', side_effect=Exception("Timeout")):

            # Should return fallback value quickly
            result = scraper.get_mvrv_value()

            assert result == 2.1  # Fallback value

    def test_mstr_analyzer_memory_cleanup(self):
        """Test that MSTRAnalyzer properly cleans up WebDriver instances"""
        from mstr_analyzer import MSTRAnalyzer

        analyzer = MSTRAnalyzer()

        with patch('mstr_analyzer.webdriver.Chrome') as mock_chrome:
            mock_driver = Mock()
            mock_chrome.return_value = mock_driver
            mock_driver.find_elements.return_value = []
            mock_driver.page_source = "<html></html>"

            # Call method that uses WebDriver
            analyzer._get_ballistic_data_xpath(95000.0)

            # Verify driver is properly cleaned up
            mock_driver.quit.assert_called_once()


if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([
        "-v",
        "--cov=mvrv_scraper",
        "--cov=mstr_analyzer",
        "--cov=imgur_uploader",
        "--cov-report=html",
        "--cov-report=term-missing"
    ])