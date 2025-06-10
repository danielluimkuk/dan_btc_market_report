"""
Test suite for Bitcoin Laws Scraper Module

Expected directory structure:
repo/
├── bitcoin_laws_scraper.py  (main module)
├── test/
│   └── test_bitcoin_laws_scraper.py  (this file)
└── other_files...

Save this file as: test/test_bitcoin_laws_scraper.py

Windows Notes:
- PIL Image objects keep file handles open, which can cause PermissionError on cleanup
- Tests include proper file handle management with context managers
- Some temp file cleanup errors on Windows are expected and handled gracefully
"""

import pytest
import unittest.mock as mock
import base64
import io
import os
import tempfile
import platform
from PIL import Image
import logging

# Import the module we're testing (from parent directory)
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import bitcoin_laws_scraper

# Windows-specific helper for file cleanup
def safe_cleanup(filepath):
    """Safely clean up files on Windows (ignores permission errors)"""
    if os.path.exists(filepath):
        try:
            os.unlink(filepath)
        except PermissionError:
            # Windows sometimes keeps file handles open
            if platform.system() == "Windows":
                pass  # Ignore on Windows
            else:
                raise


class TestBitcoinLawsScraper:
    """Test suite for BitcoinLawsScraper class"""

    def setup_method(self):
        """Setup for each test method"""
        self.scraper = bitcoin_laws_scraper.BitcoinLawsScraper()

    def test_init(self):
        """Test scraper initialization"""
        assert self.scraper.target_url == "https://bitcoinlaws.io"

    @mock.patch('bitcoin_laws_scraper.webdriver.Chrome')
    @mock.patch('bitcoin_laws_scraper.WebDriverWait')
    @mock.patch('bitcoin_laws_scraper.time.sleep')
    def test_capture_and_crop_success(self, mock_sleep, mock_wait, mock_chrome):
        """Test successful capture and crop operation"""
        # Create a mock image (simple 100x100 red square)
        test_image = Image.new('RGB', (100, 100), color='red')
        img_buffer = io.BytesIO()
        test_image.save(img_buffer, format='PNG')
        mock_screenshot_bytes = img_buffer.getvalue()

        # Setup mocks
        mock_driver = mock.MagicMock()
        mock_chrome.return_value = mock_driver
        mock_driver.get_screenshot_as_png.return_value = mock_screenshot_bytes
        mock_driver.execute_script.return_value = "complete"

        mock_wait_instance = mock.MagicMock()
        mock_wait.return_value = mock_wait_instance
        mock_wait_instance.until.return_value = True

        # Test the capture
        result = self.scraper.capture_and_crop(
            crop_coords=(0, 0, 50, 50),
            output_width=100,
            output_height=100
        )

        # Verify results
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

        # Verify driver was called correctly
        mock_chrome.assert_called_once()
        mock_driver.get.assert_called_once_with("https://bitcoinlaws.io")
        mock_driver.quit.assert_called_once()

    @mock.patch('bitcoin_laws_scraper.webdriver.Chrome')
    def test_capture_and_crop_exception(self, mock_chrome):
        """Test capture and crop with exception handling"""
        # Make Chrome throw an exception
        mock_chrome.side_effect = Exception("WebDriver failed")

        result = self.scraper.capture_and_crop((0, 0, 100, 100))

        assert result is None

    def test_process_image_success(self):
        """Test successful image processing"""
        # Create a test image
        test_image = Image.new('RGB', (200, 200), color='blue')
        img_buffer = io.BytesIO()
        test_image.save(img_buffer, format='PNG')
        screenshot_bytes = img_buffer.getvalue()

        # Process the image
        result = self.scraper._process_image(
            screenshot_bytes=screenshot_bytes,
            crop_coords=(50, 50, 150, 150),
            output_width=100,
            output_height=100
        )

        # Verify results
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

        # Verify we can decode the base64 back to an image
        decoded_bytes = base64.b64decode(result)
        decoded_image = Image.open(io.BytesIO(decoded_bytes))
        assert decoded_image.size == (100, 100)

    def test_process_image_rgba_conversion(self):
        """Test RGBA to RGB conversion"""
        # Create an RGBA image
        test_image = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        img_buffer = io.BytesIO()
        test_image.save(img_buffer, format='PNG')
        screenshot_bytes = img_buffer.getvalue()

        result = self.scraper._process_image(
            screenshot_bytes=screenshot_bytes,
            crop_coords=(0, 0, 100, 100),
            output_width=50,
            output_height=50
        )

        assert result is not None
        # Verify the result is a valid base64 JPEG
        decoded_bytes = base64.b64decode(result)
        decoded_image = Image.open(io.BytesIO(decoded_bytes))
        assert decoded_image.mode == 'RGB'

    def test_process_image_invalid_input(self):
        """Test image processing with invalid input"""
        # Test with invalid image data
        result = self.scraper._process_image(
            screenshot_bytes=b"invalid image data",
            crop_coords=(0, 0, 100, 100),
            output_width=50,
            output_height=50
        )

        assert result is None


class TestModuleFunctions:
    """Test module-level functions"""

    @mock.patch.object(bitcoin_laws_scraper.BitcoinLawsScraper, 'capture_and_crop')
    def test_capture_bitcoin_laws_screenshot_success(self, mock_capture):
        """Test successful screenshot capture function"""
        expected_result = "fake_base64_string"
        mock_capture.return_value = expected_result

        result = bitcoin_laws_scraper.capture_bitcoin_laws_screenshot(
            crop_coords=(100, 100, 200, 200),
            verbose=True
        )

        assert result == expected_result
        mock_capture.assert_called_once_with(
            crop_coords=(100, 100, 200, 200),
            output_width=800,
            output_height=600
        )

    @mock.patch.object(bitcoin_laws_scraper.BitcoinLawsScraper, 'capture_and_crop')
    def test_capture_bitcoin_laws_screenshot_failure(self, mock_capture):
        """Test screenshot capture function with failure"""
        mock_capture.return_value = None

        result = bitcoin_laws_scraper.capture_bitcoin_laws_screenshot()

        assert result is None

    @mock.patch('bitcoin_laws_scraper.capture_bitcoin_laws_screenshot')
    def test_capture_bitcoin_laws_legacy(self, mock_capture):
        """Test legacy function calls the new function"""
        expected_result = "legacy_test_result"
        mock_capture.return_value = expected_result

        result = bitcoin_laws_scraper.capture_bitcoin_laws((50, 50, 150, 150))

        assert result == expected_result
        mock_capture.assert_called_once_with((50, 50, 150, 150), verbose=False)

    def test_save_screenshot_success(self):
        """Test successful screenshot saving"""
        # Create a simple base64 encoded image
        test_image = Image.new('RGB', (10, 10), color='green')
        img_buffer = io.BytesIO()
        test_image.save(img_buffer, format='JPEG')
        test_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        # Ensure image is closed to prevent Windows file handle issues
        test_image.close()

        # Use temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            test_filename = os.path.join(temp_dir, "test_screenshot.jpg")

            result = bitcoin_laws_scraper.save_screenshot(
                base64_string=test_base64,
                filename=test_filename
            )

            assert result == test_filename
            assert os.path.exists(test_filename)

            # Verify the saved file is a valid image
            with Image.open(test_filename) as saved_image:
                assert saved_image.size == (10, 10)
            # File handle is now properly closed

    def test_save_screenshot_auto_filename(self):
        """Test save screenshot with automatic filename generation"""
        test_image = Image.new('RGB', (5, 5), color='yellow')
        img_buffer = io.BytesIO()
        test_image.save(img_buffer, format='JPEG')
        test_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        # Ensure image is closed to prevent Windows file handle issues
        test_image.close()

        # Use manual temp directory management instead of TemporaryDirectory
        # to avoid Windows cleanup issues
        original_cwd = os.getcwd()
        temp_dir = tempfile.mkdtemp()

        try:
            os.chdir(temp_dir)

            result = bitcoin_laws_scraper.save_screenshot(test_base64)

            assert result != ""
            assert result.startswith("bitcoin_laws_hq_")
            assert result.endswith(".jpg")
            assert os.path.exists(result)

            # Verify the file and close handle properly
            with Image.open(result) as saved_image:
                assert saved_image.size == (5, 5)

            # Manual cleanup with Windows-safe handling
            safe_cleanup(result)

        finally:
            os.chdir(original_cwd)
            # Manual temp directory cleanup
            try:
                os.rmdir(temp_dir)
            except (OSError, PermissionError):
                # Windows sometimes can't remove the directory immediately
                # This is acceptable for tests since it's just temp cleanup
                pass

    def test_save_screenshot_invalid_base64(self):
        """Test save screenshot with invalid base64 data"""
        result = bitcoin_laws_scraper.save_screenshot("invalid_base64_data")
        assert result == ""

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific test")
    def test_windows_file_handling(self):
        """Windows-specific test for file handle management"""
        # This test ensures Windows file handle issues don't break functionality
        test_image = Image.new('RGB', (10, 10), color='blue')
        img_buffer = io.BytesIO()
        test_image.save(img_buffer, format='JPEG')
        test_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        test_image.close()

        # Create a regular temp file instead of TemporaryDirectory
        import tempfile
        fd, temp_path = tempfile.mkstemp(suffix='.jpg')
        os.close(fd)  # Close the file descriptor

        try:
            result = bitcoin_laws_scraper.save_screenshot(test_base64, temp_path)
            assert result == temp_path
            assert os.path.exists(temp_path)

            # Verify file without keeping handle open
            file_size = os.path.getsize(temp_path)
            assert file_size > 0

        finally:
            safe_cleanup(temp_path)

    def test_update_notification_handler_for_hq(self, capsys):
        """Test the informational function"""
        bitcoin_laws_scraper.update_notification_handler_for_hq()

        captured = capsys.readouterr()
        assert "💡 To implement high quality images:" in captured.out
        assert "Replace bitcoin_laws_scraper.py" in captured.out


class TestIntegrationScenarios:
    """Integration tests for common usage scenarios"""

    @mock.patch('bitcoin_laws_scraper.webdriver.Chrome')
    @mock.patch('bitcoin_laws_scraper.WebDriverWait')
    @mock.patch('bitcoin_laws_scraper.time.sleep')
    def test_full_workflow_success(self, mock_sleep, mock_wait, mock_chrome):
        """Test the complete workflow from capture to save"""
        # Create a mock screenshot
        test_image = Image.new('RGB', (1200, 900), color='purple')
        img_buffer = io.BytesIO()
        test_image.save(img_buffer, format='PNG')
        mock_screenshot_bytes = img_buffer.getvalue()
        # Close the test image to prevent file handle issues
        test_image.close()

        # Setup mocks
        mock_driver = mock.MagicMock()
        mock_chrome.return_value = mock_driver
        mock_driver.get_screenshot_as_png.return_value = mock_screenshot_bytes
        mock_driver.execute_script.return_value = "complete"

        mock_wait_instance = mock.MagicMock()
        mock_wait.return_value = mock_wait_instance
        mock_wait_instance.until.return_value = True

        # Test full workflow
        screenshot_b64 = bitcoin_laws_scraper.capture_bitcoin_laws_screenshot(
            crop_coords=(200, 200, 800, 600),
            verbose=True
        )

        assert screenshot_b64 is not None

        # Test saving the result
        with tempfile.TemporaryDirectory() as temp_dir:
            test_filename = os.path.join(temp_dir, "integration_test.jpg")
            saved_filename = bitcoin_laws_scraper.save_screenshot(
                screenshot_b64,
                test_filename
            )

            assert saved_filename == test_filename
            assert os.path.exists(saved_filename)

            # Properly verify and close the saved file
            with Image.open(saved_filename) as saved_image:
                assert saved_image.size == (800, 600)  # Should match output dimensions

    def test_error_handling_chain(self):
        """Test error handling through the entire chain"""
        # This tests that errors propagate correctly through the system
        # Mock the webdriver to fail, which should be caught and return None
        with mock.patch('bitcoin_laws_scraper.webdriver.Chrome') as mock_chrome:
            # Make Chrome initialization fail
            mock_chrome.side_effect = Exception("WebDriver initialization failed")

            result = bitcoin_laws_scraper.capture_bitcoin_laws_screenshot()

            # The function should catch the exception and return None
            assert result is None


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_extreme_crop_coordinates(self):
        """Test with extreme crop coordinates"""
        scraper = bitcoin_laws_scraper.BitcoinLawsScraper()

        # Create a small test image
        test_image = Image.new('RGB', (50, 50), color='orange')
        img_buffer = io.BytesIO()
        test_image.save(img_buffer, format='PNG')
        screenshot_bytes = img_buffer.getvalue()

        # Test with coordinates outside image bounds
        result = scraper._process_image(
            screenshot_bytes=screenshot_bytes,
            crop_coords=(-100, -100, 2000, 2000),  # Way outside bounds
            output_width=100,
            output_height=100
        )

        # Should still work (PIL handles bounds checking)
        assert result is not None

    def test_zero_size_output(self):
        """Test with zero or very small output dimensions"""
        scraper = bitcoin_laws_scraper.BitcoinLawsScraper()

        test_image = Image.new('RGB', (100, 100), color='cyan')
        img_buffer = io.BytesIO()
        test_image.save(img_buffer, format='PNG')
        screenshot_bytes = img_buffer.getvalue()

        # Test with 1x1 output (edge case)
        result = scraper._process_image(
            screenshot_bytes=screenshot_bytes,
            crop_coords=(0, 0, 50, 50),
            output_width=1,
            output_height=1
        )

        assert result is not None
        # Verify the result decodes to a 1x1 image
        decoded_bytes = base64.b64decode(result)
        decoded_image = Image.open(io.BytesIO(decoded_bytes))
        assert decoded_image.size == (1, 1)


# Test runner configuration
if __name__ == "__main__":
    # Configure logging for tests
    logging.basicConfig(level=logging.INFO)

    # Run tests with pytest if available, otherwise with unittest
    try:
        import pytest
        print("Running tests with pytest...")
        pytest.main([__file__, "-v", "--tb=short"])
    except ImportError:
        print("pytest not available, running with unittest...")
        import unittest

        # Create a test suite
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()

        # Add all test classes
        for test_class in [TestBitcoinLawsScraper, TestModuleFunctions,
                          TestIntegrationScenarios, TestEdgeCases]:
            tests = loader.loadTestsFromTestClass(test_class)
            suite.addTests(tests)

        # Run the tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        # Print summary
        if result.wasSuccessful():
            print(f"\n✅ All tests passed! ({result.testsRun} tests)")
        else:
            print(f"\n❌ {len(result.failures)} failures, {len(result.errors)} errors")


# Utility function for manual testing
def run_quick_test():
    """Quick test function for manual verification"""
    print("🧪 Running quick manual test...")

    # Test image processing without web scraping
    scraper = bitcoin_laws_scraper.BitcoinLawsScraper()

    # Create a test image
    test_image = Image.new('RGB', (200, 200), color='magenta')
    for x in range(0, 200, 20):
        for y in range(0, 200, 20):
            # Create a checkerboard pattern
            if (x//20 + y//20) % 2:
                for i in range(20):
                    for j in range(20):
                        if x+i < 200 and y+j < 200:
                            test_image.putpixel((x+i, y+j), (255, 255, 255))

    # Convert to bytes
    img_buffer = io.BytesIO()
    test_image.save(img_buffer, format='PNG')
    test_bytes = img_buffer.getvalue()
    # Close the test image to prevent file handle issues
    test_image.close()

    # Test processing
    result = scraper._process_image(
        test_bytes,
        (50, 50, 150, 150),
        100,
        100
    )

    if result:
        print("✅ Image processing test passed!")
        print(f"📏 Result length: {len(result)} characters")

        # Test saving
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            filename = bitcoin_laws_scraper.save_screenshot(result, tmp.name)
            if filename:
                print(f"✅ Save test passed! File: {filename}")
                # Verify the file can be opened and then clean up
                try:
                    with Image.open(filename) as saved_image:
                        print(f"📏 Saved image size: {saved_image.size}")
                    os.unlink(filename)
                    print("🧹 Cleanup completed")
                except Exception as e:
                    print(f"⚠️ Cleanup issue (normal on Windows): {e}")
            else:
                print("❌ Save test failed!")
    else:
        print("❌ Image processing test failed!")


# Example usage and test data
EXAMPLE_USAGE = """
# Example usage of the test suite:

# From repo root directory:
# 1. Run all tests:
python -m pytest test/

# 2. Run specific test file:
python -m pytest test/test_bitcoin_laws_scraper.py -v

# 3. Run specific test class:
python -m pytest test/test_bitcoin_laws_scraper.py::TestBitcoinLawsScraper -v

# 4. Run specific test method:
python -m pytest test/test_bitcoin_laws_scraper.py::TestBitcoinLawsScraper::test_capture_and_crop_success -v

# 5. Run with coverage (if pytest-cov is installed):
python -m pytest test/ --cov=bitcoin_laws_scraper --cov-report=html

# From test directory:
# 6. Run directly:
cd test && python test_bitcoin_laws_scraper.py

# 7. Run quick manual test:
cd test && python -c "from test_bitcoin_laws_scraper import run_quick_test; run_quick_test()"
"""

print(EXAMPLE_USAGE)