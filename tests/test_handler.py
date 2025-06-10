# =============================================================================
# test_enhanced_notification_handler.py - Comprehensive Unit Tests
# =============================================================================

import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import pytest
import base64
import io
import os
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Import the module we're testing
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_notification_handler import EnhancedNotificationHandler


class TestEnhancedNotificationHandler(unittest.TestCase):
    """
    Comprehensive unit tests for Enhanced Notification Handler
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'SMTP_SERVER': 'smtp.test.com',
            'SMTP_PORT': '587',
            'EMAIL_USER': 'test@example.com',
            'EMAIL_PASSWORD': 'test_password',
            'RECIPIENT_EMAILS': 'user1@test.com,user2@test.com',
            'IMGUR_CLIENT_ID': 'test_imgur_client'
        })
        self.env_patcher.start()

        # Sample data for testing
        self.sample_btc_data = {
            'success': True,
            'type': 'crypto',
            'price': 95000.50,
            'indicators': {
                'mvrv': 2.1,
                'weekly_rsi': 65.0,
                'ema_200': 88000.0
            },
            'metadata': {'source': 'polygon_api'}
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
                    'description': 'Normal volatility + fair valuation',
                    'reasoning': 'Neither volatility nor fundamentals provide clear edge',
                    'confidence': 'low'
                }
            }
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

        self.sample_processed_data = {
            'assets': {
                'BTC': self.sample_btc_data,
                'MSTR': self.sample_mstr_data
            },
            'monetary': self.sample_monetary_data
        }

        # Create a small test image as base64
        self.test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAHPn4JI0QAAAABJRU5ErkJggg=="

    def tearDown(self):
        """Clean up after each test method."""
        self.env_patcher.stop()


class TestInitialization(TestEnhancedNotificationHandler):
    """Test handler initialization and configuration"""

    @patch('enhanced_notification_handler.ImgurUploader')
    @patch('enhanced_notification_handler.BTCAnalyzer')
    def test_initialization_with_imgur(self, mock_btc_analyzer, mock_imgur):
        """Test handler initialization when Imgur is available"""
        mock_imgur_instance = Mock()
        mock_imgur_instance.client_id = 'test_client_id'
        mock_imgur.return_value = mock_imgur_instance

        handler = EnhancedNotificationHandler()

        self.assertEqual(handler.smtp_server, 'smtp.test.com')
        self.assertEqual(handler.smtp_port, 587)
        self.assertEqual(handler.email_user, 'test@example.com')
        self.assertEqual(handler.email_password, 'test_password')
        self.assertEqual(len(handler.recipients), 2)
        self.assertIn('user1@test.com', handler.recipients)
        self.assertIn('user2@test.com', handler.recipients)
        self.assertIsNotNone(handler.imgur_uploader)

    @patch('enhanced_notification_handler.ImgurUploader', None)  # Imgur not available
    @patch('enhanced_notification_handler.BTCAnalyzer')
    def test_initialization_without_imgur(self, mock_btc_analyzer):
        """Test handler initialization when Imgur is not available"""
        handler = EnhancedNotificationHandler()

        self.assertIsNone(handler.imgur_uploader)

    def test_parse_recipients_multiple_emails(self):
        """Test parsing multiple email recipients"""
        with patch.dict(os.environ, {'RECIPIENT_EMAILS': 'test1@example.com,test2@example.com,test3@example.com'}):
            handler = EnhancedNotificationHandler()
            self.assertEqual(len(handler.recipients), 3)

    def test_parse_recipients_single_email_fallback(self):
        """Test fallback to single email when RECIPIENT_EMAILS is not set"""
        with patch.dict(os.environ, {'RECIPIENT_EMAIL': 'single@example.com'}, clear=True):
            # Clear RECIPIENT_EMAILS and only have RECIPIENT_EMAIL
            env_dict = os.environ.copy()
            if 'RECIPIENT_EMAILS' in env_dict:
                del env_dict['RECIPIENT_EMAILS']
            env_dict['RECIPIENT_EMAIL'] = 'single@example.com'
            env_dict['SMTP_SERVER'] = 'smtp.test.com'
            env_dict['SMTP_PORT'] = '587'
            env_dict['EMAIL_USER'] = 'test@example.com'
            env_dict['EMAIL_PASSWORD'] = 'test_password'

            with patch.dict(os.environ, env_dict, clear=True):
                handler = EnhancedNotificationHandler()
                self.assertEqual(len(handler.recipients), 1)
                self.assertEqual(handler.recipients[0], 'single@example.com')

    def test_parse_recipients_invalid_emails_filtered(self):
        """Test that invalid email addresses are filtered out"""
        with patch.dict(os.environ, {'RECIPIENT_EMAILS': 'valid@example.com,invalid-email,another@test.com'}):
            handler = EnhancedNotificationHandler()
            self.assertEqual(len(handler.recipients), 2)
            self.assertIn('valid@example.com', handler.recipients)
            self.assertIn('another@test.com', handler.recipients)
            self.assertNotIn('invalid-email', handler.recipients)


class TestImageProcessing(TestEnhancedNotificationHandler):
    """Test image processing and resizing functionality"""

    @patch('enhanced_notification_handler.Image')
    def test_resize_screenshot_for_email_success(self, mock_image_class):
        """Test successful image resizing"""
        # Mock PIL Image operations
        mock_image = Mock()
        mock_image.size = (1200, 900)  # Original size
        mock_image.mode = 'RGB'
        mock_image.resize.return_value = mock_image

        mock_image_class.open.return_value = mock_image
        mock_image_class.new.return_value = mock_image

        # Mock the output buffer
        mock_output = Mock()
        mock_output.getvalue.return_value = b'mock_image_data'

        handler = EnhancedNotificationHandler()

        with patch('io.BytesIO', return_value=mock_output):
            with patch('base64.b64decode', return_value=b'original_image_data'):
                with patch('base64.b64encode', return_value=b'resized_image_data'):
                    result = handler._resize_screenshot_for_email(self.test_image_base64)

        self.assertEqual(result, 'resized_image_data')
        mock_image.resize.assert_called_once()

    def test_resize_screenshot_empty_input(self):
        """Test image resizing with empty input"""
        handler = EnhancedNotificationHandler()
        result = handler._resize_screenshot_for_email("")
        self.assertEqual(result, "")

    @patch('enhanced_notification_handler.Image')
    def test_resize_screenshot_error_handling(self, mock_image_class):
        """Test image resizing error handling"""
        mock_image_class.open.side_effect = Exception("PIL error")

        handler = EnhancedNotificationHandler()

        with patch('base64.b64decode', return_value=b'invalid_image_data'):
            result = handler._resize_screenshot_for_email(self.test_image_base64)

        self.assertEqual(result, "")

    @patch('enhanced_notification_handler.Image')
    def test_resize_screenshot_rgba_conversion(self, mock_image_class):
        """Test RGBA to RGB conversion during resizing"""
        # Mock RGBA image that needs conversion
        mock_rgba_image = Mock()
        mock_rgba_image.size = (800, 600)
        mock_rgba_image.mode = 'RGBA'
        mock_rgba_image.split.return_value = [Mock(), Mock(), Mock(), Mock()]  # R, G, B, A channels

        mock_rgb_image = Mock()
        mock_rgb_image.paste = Mock()

        mock_image_class.open.return_value = mock_rgba_image
        mock_image_class.new.return_value = mock_rgb_image

        mock_output = Mock()
        mock_output.getvalue.return_value = b'converted_image_data'

        handler = EnhancedNotificationHandler()

        with patch('io.BytesIO', return_value=mock_output):
            with patch('base64.b64decode', return_value=b'rgba_image_data'):
                with patch('base64.b64encode', return_value=b'converted_image_data'):
                    result = handler._resize_screenshot_for_email(self.test_image_base64)

        # Should create new RGB image and paste RGBA with alpha mask
        mock_image_class.new.assert_called_with('RGB', mock_rgba_image.size, (255, 255, 255))
        mock_rgb_image.paste.assert_called_once()


class TestHTMLGeneration(TestEnhancedNotificationHandler):
    """Test HTML report generation"""

    @patch('enhanced_notification_handler.BTCAnalyzer')
    def test_generate_enhanced_report_html_success(self, mock_btc_analyzer_class):
        """Test successful HTML report generation"""
        # Mock BTC analyzer
        mock_analyzer = Mock()
        mock_analysis = {
            'market_status': 'bull',
            'is_bull_market': True,
            'price': 95000.50,
            'ema_200': 88000.0,
            'indicators': {'mvrv': 2.1, 'weekly_rsi': 65.0},
            'signal_conditions': {
                'mvrv': {'value': 2.1, 'condition_met': False},
                'rsi': {'value': 65.0, 'condition_met': False}
            },
            'signal_status': {
                'status': 'none',
                'message': '',
                'emoji': '',
                'prediction': ''
            }
        }
        mock_analyzer.analyze_btc_signals.return_value = mock_analysis
        mock_btc_analyzer_class.return_value = mock_analyzer

        handler = EnhancedNotificationHandler()

        html_result = handler._generate_enhanced_report_html(
            self.sample_processed_data,
            [],
            "December 09, 2024",
            self.test_image_base64
        )

        self.assertIsInstance(html_result, str)
        self.assertIn('<!DOCTYPE html>', html_result)
        self.assertIn("Dan's Market Report", html_result)
        self.assertIn('December 09, 2024', html_result)
        self.assertIn('95,000.50', html_result)  # BTC price should be in report (formatted with commas)
        self.assertIn('425.67', html_result)  # MSTR price should be in report

    @patch('enhanced_notification_handler.BTCAnalyzer')
    def test_generate_enhanced_report_html_with_imgur_url(self, mock_btc_analyzer_class):
        """Test HTML report generation with Imgur URL"""
        mock_analyzer = Mock()
        mock_analysis = {
            'market_status': 'bear',
            'is_bull_market': False,
            'price': 85000.0,
            'ema_200': 88000.0,
            'indicators': {'mvrv': 1.8, 'weekly_rsi': 45.0},
            'signal_conditions': {
                'mvrv': {'value': 1.8, 'condition_met': False},
                'rsi': {'value': 45.0, 'condition_met': False}
            },
            'signal_status': {
                'status': 'none',
                'message': '',
                'emoji': '',
                'prediction': ''
            }
        }
        mock_analyzer.analyze_btc_signals.return_value = mock_analysis
        mock_btc_analyzer_class.return_value = mock_analyzer

        handler = EnhancedNotificationHandler()

        imgur_url = "https://i.imgur.com/test123.jpg"
        html_result = handler._generate_enhanced_report_html_with_url(
            self.sample_processed_data,
            [],
            "December 09, 2024",
            imgur_url
        )

        self.assertIn(imgur_url, html_result)
        self.assertIn('img src="' + imgur_url, html_result)

    @patch('enhanced_notification_handler.BTCAnalyzer')
    def test_generate_enhanced_btc_section_html_success(self, mock_btc_analyzer_class):
        """Test BTC section HTML generation"""
        mock_analyzer = Mock()
        mock_analysis = {
            'price': 95000.50,
            'ema_200': 88000.0,
            'is_bull_market': True,
            'market_status': 'bull',
            'indicators': {'mvrv': 2.1, 'weekly_rsi': 65.0},
            'signal_conditions': {
                'mvrv': {'value': 2.1, 'condition_met': False},
                'rsi': {'value': 65.0, 'condition_met': False}
            },
            'signal_status': {
                'status': 'none',
                'message': '',
                'emoji': '',
                'prediction': ''
            }
        }
        mock_analyzer.analyze_btc_signals.return_value = mock_analysis
        mock_btc_analyzer_class.return_value = mock_analyzer

        handler = EnhancedNotificationHandler()

        btc_html = handler._generate_enhanced_btc_section_html(self.sample_btc_data)

        self.assertIn('₿ BTC', btc_html)
        self.assertIn('95,000.50', btc_html)
        self.assertIn('🐂 Bull Market', btc_html)
        self.assertIn('MVRV', btc_html)
        self.assertIn('Weekly RSI', btc_html)

    @patch('enhanced_notification_handler.BTCAnalyzer')
    def test_generate_enhanced_btc_section_html_error(self, mock_btc_analyzer_class):
        """Test BTC section HTML generation with error data"""
        mock_btc_analyzer_class.return_value = Mock()

        handler = EnhancedNotificationHandler()

        error_data = {'error': 'API connection failed'}
        btc_html = handler._generate_enhanced_btc_section_html(error_data)

        self.assertIn('ERROR', btc_html)
        self.assertIn('API connection failed', btc_html)

    def test_generate_mstr_section_html_success(self):
        """Test MSTR section HTML generation"""
        handler = EnhancedNotificationHandler()

        mstr_html = handler._generate_mstr_section_html(self.sample_mstr_data)

        self.assertIn('📊 MSTR', mstr_html)
        self.assertIn('425.67', mstr_html)
        self.assertIn('Model Price', mstr_html)
        self.assertIn('398.12', mstr_html)
        self.assertIn('Deviation', mstr_html)
        self.assertIn('6.9%', mstr_html)
        self.assertIn('Options Strategy', mstr_html)

    def test_generate_mstr_section_html_error(self):
        """Test MSTR section HTML generation with error"""
        handler = EnhancedNotificationHandler()

        error_data = {'error': 'Scraping timeout'}
        mstr_html = handler._generate_mstr_section_html(error_data)

        self.assertIn('ERROR', mstr_html)
        self.assertIn('Scraping timeout', mstr_html)

    def test_generate_monetary_section_html_success(self):
        """Test monetary section HTML generation"""
        handler = EnhancedNotificationHandler()

        monetary_html = handler._generate_monetary_section_html(self.sample_monetary_data)

        self.assertIn('🏦 Monetary Policy Analysis', monetary_html)
        self.assertIn('2024-12-01', monetary_html)
        self.assertIn('2 days ago', monetary_html)
        self.assertIn('5.25%', monetary_html)  # Fed funds rate
        self.assertIn('M2 Money Supply', monetary_html)
        self.assertIn('True Inflation', monetary_html)
        self.assertIn('6.2%', monetary_html)

    def test_generate_monetary_section_html_failure(self):
        """Test monetary section HTML generation with failed data"""
        handler = EnhancedNotificationHandler()

        failed_data = {
            'success': False,
            'error': 'FRED API timeout'
        }

        monetary_html = handler._generate_monetary_section_html(failed_data)

        self.assertIn('Data Unavailable', monetary_html)
        self.assertIn('FRED API timeout', monetary_html)
        self.assertIn('fred.stlouisfed.org', monetary_html)

    def test_generate_bitcoin_laws_section_html_with_image(self):
        """Test Bitcoin Laws section HTML generation with image"""
        handler = EnhancedNotificationHandler()

        laws_html = handler._generate_bitcoin_laws_section_html(self.test_image_base64)

        self.assertIn('⚖️ Bitcoin Laws in USA', laws_html)
        self.assertIn('data:image/jpeg;base64,', laws_html)
        self.assertIn('bitcoinlaws.io', laws_html)

    def test_generate_bitcoin_laws_section_html_no_image(self):
        """Test Bitcoin Laws section HTML generation without image"""
        handler = EnhancedNotificationHandler()

        laws_html = handler._generate_bitcoin_laws_section_html("")

        self.assertIn('Screenshot Unavailable', laws_html)
        self.assertIn('bitcoinlaws.io', laws_html)

    def test_get_email_css(self):
        """Test CSS generation for email styling"""
        handler = EnhancedNotificationHandler()

        css = handler._get_email_css()

        self.assertIsInstance(css, str)
        self.assertIn('body {', css)
        self.assertIn('.container {', css)
        self.assertIn('.asset-section {', css)
        self.assertIn('@media (max-width: 768px)', css)  # Mobile responsive CSS


class TestEmailSending(TestEnhancedNotificationHandler):
    """Test email sending functionality"""

    @patch('enhanced_notification_handler.smtplib.SMTP')
    def test_send_email_to_multiple_success(self, mock_smtp):
        """Test successful email sending to multiple recipients"""
        # Mock SMTP server
        mock_server = Mock()
        mock_smtp.return_value = mock_server

        handler = EnhancedNotificationHandler()

        # Send test email
        subject = "Test Subject"
        body = "<html><body>Test Body</body></html>"

        handler._send_email_to_multiple(subject, body, is_html=True)

        # Verify SMTP operations
        mock_smtp.assert_called_once_with('smtp.test.com', 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with('test@example.com', 'test_password')
        mock_server.send_message.assert_called_once()
        mock_server.quit.assert_called_once()

    @patch('enhanced_notification_handler.smtplib.SMTP')
    def test_send_email_smtp_error(self, mock_smtp):
        """Test email sending with SMTP error"""
        mock_smtp.side_effect = Exception("SMTP connection failed")

        handler = EnhancedNotificationHandler()

        with self.assertRaises(Exception):
            handler._send_email_to_multiple("Test", "Body")

    def test_send_email_no_credentials(self):
        """Test email sending without credentials"""
        with patch.dict(os.environ, {}, clear=True):
            handler = EnhancedNotificationHandler()

            # Should not raise exception, just return early
            handler._send_email_to_multiple("Test", "Body")

    def test_send_email_no_recipients(self):
        """Test email sending without recipients"""
        with patch.dict(os.environ, {'RECIPIENT_EMAILS': ''}, clear=True):
            handler = EnhancedNotificationHandler()

            # Should not raise exception, just return early
            handler._send_email_to_multiple("Test", "Body")


class TestDailyReportIntegration(TestEnhancedNotificationHandler):
    """Test the main daily report sending functionality"""

    @patch('enhanced_notification_handler.smtplib.SMTP')
    @patch('enhanced_notification_handler.BTCAnalyzer')
    def test_send_daily_report_success_imgur(self, mock_btc_analyzer_class, mock_smtp):
        """Test successful daily report sending with Imgur"""
        # Mock BTC analyzer
        mock_analyzer = Mock()
        mock_analysis = {
            'market_status': 'bull',
            'is_bull_market': True,
            'price': 95000.50,
            'ema_200': 88000.0,
            'indicators': {'mvrv': 2.1, 'weekly_rsi': 65.0},
            'signal_conditions': {
                'mvrv': {'value': 2.1, 'condition_met': False},
                'rsi': {'value': 65.0, 'condition_met': False}
            },
            'signal_status': {'status': 'none', 'message': '', 'emoji': '', 'prediction': ''}
        }
        mock_analyzer.analyze_btc_signals.return_value = mock_analysis
        mock_btc_analyzer_class.return_value = mock_analyzer

        # Mock SMTP
        mock_server = Mock()
        mock_smtp.return_value = mock_server

        # Mock Imgur uploader
        with patch('enhanced_notification_handler.ImgurUploader') as mock_imgur_class:
            mock_imgur_instance = Mock()
            mock_imgur_instance.client_id = 'test_client'
            mock_imgur_instance.upload_base64_image.return_value = 'https://i.imgur.com/test123.jpg'
            mock_imgur_class.return_value = mock_imgur_instance

            handler = EnhancedNotificationHandler()

            with patch.object(handler, '_resize_screenshot_for_email', return_value='resized_image'):
                # Use try/except to catch any exceptions that might prevent email sending
                try:
                    handler.send_daily_report(
                        self.sample_processed_data,
                        [],
                        self.test_image_base64
                    )
                except Exception as e:
                    self.fail(f"send_daily_report raised an unexpected exception: {e}")

            # Verify Imgur upload was attempted
            mock_imgur_instance.upload_base64_image.assert_called_once()

            # Verify email was sent (check if any email method was called)
            self.assertTrue(
                mock_server.send_message.called or mock_server.sendmail.called,
                "Expected email to be sent but no SMTP send method was called"
            )

    @patch('enhanced_notification_handler.smtplib.SMTP')
    @patch('enhanced_notification_handler.BTCAnalyzer')
    def test_send_daily_report_fallback_embedded(self, mock_btc_analyzer_class, mock_smtp):
        """Test daily report sending falls back to embedded images"""
        # Mock BTC analyzer
        mock_analyzer = Mock()
        mock_analysis = {
            'market_status': 'bull',
            'is_bull_market': True,
            'price': 95000.50,
            'ema_200': 88000.0,
            'indicators': {'mvrv': 2.1, 'weekly_rsi': 65.0},
            'signal_conditions': {
                'mvrv': {'value': 2.1, 'condition_met': False},
                'rsi': {'value': 65.0, 'condition_met': False}
            },
            'signal_status': {'status': 'none', 'message': '', 'emoji': '', 'prediction': ''}
        }
        mock_analyzer.analyze_btc_signals.return_value = mock_analysis
        mock_btc_analyzer_class.return_value = mock_analyzer

        # Mock SMTP
        mock_server = Mock()
        mock_smtp.return_value = mock_server

        # Handler without Imgur
        with patch('enhanced_notification_handler.ImgurUploader', None):
            handler = EnhancedNotificationHandler()

            with patch.object(handler, '_resize_screenshot_for_email', return_value='resized_image'):
                # Use try/except to catch any exceptions that might prevent email sending
                try:
                    handler.send_daily_report(
                        self.sample_processed_data,
                        [],
                        self.test_image_base64
                    )
                except Exception as e:
                    self.fail(f"send_daily_report raised an unexpected exception: {e}")

            # Should still send email with embedded image (check if any email method was called)
            self.assertTrue(
                mock_server.send_message.called or mock_server.sendmail.called,
                "Expected email to be sent but no SMTP send method was called"
            )

    @patch('enhanced_notification_handler.smtplib.SMTP')
    def test_send_error_notification(self, mock_smtp):
        """Test error notification sending"""
        mock_server = Mock()
        mock_smtp.return_value = mock_server

        handler = EnhancedNotificationHandler()

        error_message = "Test error occurred"
        handler.send_error_notification(error_message)

        # Verify email was sent
        mock_server.send_message.assert_called_once()

        # Check that the sent message contains the error
        call_args = mock_server.send_message.call_args
        sent_message = call_args[0][0]
        self.assertIn("Market Monitor Error", sent_message['Subject'])


class TestUtilityFunctions(TestEnhancedNotificationHandler):
    """Test utility and helper functions"""

    def test_generate_project_footer_html(self):
        """Test project footer HTML generation"""
        handler = EnhancedNotificationHandler()

        footer_html = handler._generate_project_footer_html()

        self.assertIn('automated Bitcoin market intelligence', footer_html)
        self.assertIn('github.com', footer_html)
        self.assertIn('README.md', footer_html)
        self.assertIn('README_TRAD_CHI.md', footer_html)

    def test_generate_error_report_html(self):
        """Test error report HTML generation"""
        handler = EnhancedNotificationHandler()

        error_html = handler._generate_error_report_html(
            "December 09, 2024",
            "Both BTC and MSTR collection failed"
        )

        self.assertIn('Data Collection Error', error_html)
        self.assertIn('December 09, 2024', error_html)
        self.assertIn('Both BTC and MSTR collection failed', error_html)


# =============================================================================
# Pytest Configuration and Fixtures
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment for all tests"""
    test_env = {
        'SMTP_SERVER': 'smtp.test.com',
        'SMTP_PORT': '587',
        'EMAIL_USER': 'test@example.com',
        'EMAIL_PASSWORD': 'test_password',
        'RECIPIENT_EMAILS': 'user1@test.com,user2@test.com',
        'IMGUR_CLIENT_ID': 'test_imgur_client'
    }

    with patch.dict(os.environ, test_env):
        yield


@pytest.fixture
def mock_handler():
    """Fixture providing a mocked notification handler"""
    with patch('enhanced_notification_handler.BTCAnalyzer'):
        with patch('enhanced_notification_handler.ImgurUploader'):
            handler = EnhancedNotificationHandler()
            yield handler


@pytest.fixture
def sample_data():
    """Fixture providing sample test data"""
    return {
        'btc': {
            'success': True,
            'price': 95000.50,
            'indicators': {'mvrv': 2.1, 'weekly_rsi': 65.0, 'ema_200': 88000.0}
        },
        'mstr': {
            'success': True,
            'price': 425.67,
            'indicators': {'model_price': 398.12, 'deviation_pct': 6.9},
            'analysis': {'price_signal': {'status': 'neutral'}}
        }
    }


# =============================================================================
# Test Runner Configuration
# =============================================================================

def run_notification_handler_tests():
    """Run all notification handler tests with detailed output"""
    print("📧 Running Enhanced Notification Handler Unit Tests...")
    print("=" * 70)

    try:
        # Discover and run tests
        loader = unittest.TestLoader()
        suite = loader.discover('.', pattern='test_enhanced_notification_handler.py')
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        # Print summary
        print("\n" + "=" * 70)
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
            print("\n✅ All notification handler tests passed!")

        return result.wasSuccessful()

    except Exception as e:
        print(f"❌ Test execution failed: {str(e)}")
        return False


if __name__ == "__main__":
    # Run tests when script is executed directly
    success = run_notification_handler_tests()
    exit(0 if success else 1)

# =============================================================================
# Usage Instructions
# =============================================================================

"""
ENHANCED NOTIFICATION HANDLER TEST USAGE:

1. Install dependencies:
   pip install pytest unittest-mock pillow

2. Run all tests:
   python test_enhanced_notification_handler.py

3. Run with pytest (recommended):
   pytest test_enhanced_notification_handler.py -v

4. Run specific test classes:
   python -m unittest TestInitialization -v
   python -m unittest TestImageProcessing -v
   python -m unittest TestHTMLGeneration -v
   python -m unittest TestEmailSending -v

5. Run with coverage:
   coverage run test_enhanced_notification_handler.py
   coverage report -m

TEST COVERAGE INCLUDES:
✅ Handler initialization and configuration
✅ Email recipient parsing and validation
✅ Image processing and resizing (PIL operations)
✅ HTML report generation (all sections)
✅ Email sending (SMTP operations)
✅ Imgur integration
✅ Error handling and fallback scenarios
✅ BTC analysis integration
✅ MSTR analysis with options strategies
✅ Monetary policy section generation
✅ Bitcoin Laws screenshot integration
✅ CSS styling and responsive design
✅ Daily report end-to-end flow

MOCKING STRATEGY:
- SMTP server operations fully mocked
- PIL Image operations mocked for testing
- Imgur uploader mocked for testing
- BTC analyzer mocked with realistic responses
- Environment variables controlled in tests
- File I/O operations mocked where needed

The tests ensure the notification handler works correctly
in isolation while providing confidence that email 
generation and sending functionality operates as expected.
"""