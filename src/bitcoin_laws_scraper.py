# Updated bitcoin_laws_scraper.py - Higher Quality for Imgur Hosting

import time
import io
import base64
import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
from datetime import datetime


class BitcoinLawsScraper:
    """
    Bitcoin Laws scraper with HIGH QUALITY output for Imgur hosting
    """

    def __init__(self):
        self.target_url = "https://bitcoinlaws.io"

    def capture_and_crop(self, crop_coords, output_width=800, output_height=600):
        """
        🎯 HIGH QUALITY: Since we're using Imgur hosting, we can use larger, higher quality images

        Args:
            crop_coords: (left, top, right, bottom) coordinates for 1200x900 reference
            output_width: Final width (default: 800 - high quality for external hosting)
            output_height: Final height (default: 600 - high quality for external hosting)
        """
        driver = None
        try:
            # Setup Chrome
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.set_window_size(2000, 1500)

            # Load page with patient timing
            driver.get(self.target_url)
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            WebDriverWait(driver, 20).until(lambda d: d.execute_script("return document.readyState") == "complete")

            # Patient waits
            time.sleep(20)
            for _ in range(3):
                driver.execute_script("window.dispatchEvent(new Event('resize')); window.scrollTo(0, 0);")
                time.sleep(5)
            time.sleep(15)

            # Process screenshot
            screenshot_png = driver.get_screenshot_as_png()
            return self._process_image(screenshot_png, crop_coords, output_width, output_height)

        except Exception as e:
            logging.error(f"Capture failed: {e}")
            return None
        finally:
            if driver:
                driver.quit()

    def _process_image(self, screenshot_bytes, crop_coords, output_width, output_height):
        """
        🎯 HIGH QUALITY: Process with minimal compression for external hosting
        """
        try:
            image = Image.open(io.BytesIO(screenshot_bytes))

            # Step 1: Resize to 1200x900 reference
            image = image.resize((1200, 900), Image.Resampling.LANCZOS)

            # Step 2: Crop using coordinates
            left, top, right, bottom = crop_coords
            image = image.crop((max(0, left), max(0, top), min(1200, right), min(900, bottom)))

            # Step 3: Resize to final dimensions (HIGH QUALITY)
            image = image.resize((output_width, output_height), Image.Resampling.LANCZOS)

            # Step 4: Minimal compression for external hosting
            if image.mode in ('RGBA', 'LA', 'P'):
                rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'RGBA':
                    rgb_image.paste(image, mask=image.split()[-1])
                else:
                    rgb_image.paste(image)
                image = rgb_image

            output_buffer = io.BytesIO()
            # 🎯 HIGH QUALITY: Use 90% quality since we're hosting externally
            image.save(output_buffer, format='JPEG', quality=90, optimize=True)

            base64_string = base64.b64encode(output_buffer.getvalue()).decode('utf-8')

            # Log final size
            final_size = len(base64_string)
            logging.info(f"HIGH QUALITY Bitcoin Laws screenshot: {output_width}x{output_height}, {final_size:,} chars")

            return base64_string

        except Exception as e:
            logging.error(f"Image processing failed: {e}")
            return None


def capture_bitcoin_laws_screenshot(crop_coords=(260, 218, 890, 760), verbose=False):
    """
    🎯 HIGH QUALITY: Updated function for Imgur hosting with larger, higher quality images

    Args:
        crop_coords: (left, top, right, bottom) for 1200x900 reference
        verbose: Enable verbose logging (for compatibility)

    Returns:
        str: Base64 encoded image (800x600 - high quality for external hosting)
    """
    if verbose:
        logging.info("Starting HIGH QUALITY Bitcoin Laws screenshot capture...")

    scraper = BitcoinLawsScraper()

    # Use high quality dimensions for external hosting
    result = scraper.capture_and_crop(
        crop_coords=crop_coords,
        output_width=800,  # High quality width for external hosting
        output_height=600  # High quality height for external hosting
    )

    if verbose:
        if result:
            size_kb = len(result) * 0.75 / 1024  # Approximate KB size
            logging.info(f"✅ HIGH QUALITY Bitcoin Laws screenshot captured ({len(result):,} chars, ~{size_kb:.1f}KB)")
        else:
            logging.warning("❌ Bitcoin Laws screenshot capture failed")

    return result


# Legacy function for backward compatibility
def capture_bitcoin_laws(crop_coords=(260, 218, 890, 760)):
    """
    Legacy function name for backward compatibility
    """
    return capture_bitcoin_laws_screenshot(crop_coords, verbose=False)


def save_screenshot(base64_string, filename=None):
    """Save base64 screenshot to file"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bitcoin_laws_hq_{timestamp}.jpg"

    try:
        image_bytes = base64.b64decode(base64_string)
        with open(filename, 'wb') as f:
            f.write(image_bytes)
        return filename
    except Exception as e:
        logging.error(f"Save failed: {e}")
        return ""


if __name__ == "__main__":
    print("🔍 Bitcoin Laws Scraper - HIGH QUALITY for Imgur Hosting")
    print("=" * 60)

    print("📸 Capturing HIGH QUALITY Bitcoin Laws screenshot...")

    screenshot = capture_bitcoin_laws_screenshot(verbose=True)

    if screenshot:
        filename = save_screenshot(screenshot)
        print(f"✅ Saved: {filename}")
        print(f"📏 High quality: 800x600 pixels")
        print(f"📊 Base64 length: {len(screenshot):,} characters")
        estimated_kb = len(screenshot) * 0.75 / 1024
        print(f"💾 Estimated size: ~{estimated_kb:.1f} KB")
        print(f"🎯 Perfect for Imgur hosting - no size limitations!")
    else:
        print("❌ Capture failed")

    print("\n🎯 High quality capture complete!")


# =====================================================================================
# Enhanced notification handler update for high quality images
# =====================================================================================

def update_notification_handler_for_hq():
    """
    Update the notification handler to use high quality images for Imgur hosting
    """

    # In your enhanced_notification_handler.py, update this method:

    def _resize_screenshot_for_email(self, screenshot_base64: str, max_width: int = 800, max_height: int = 600) -> str:
        """
        🎯 IMGUR OPTIMIZED: Since we're using Imgur hosting, we can use larger, higher quality images

        Args:
            screenshot_base64: Base64 encoded image string
            max_width: Maximum width in pixels (default: 800px - high quality for Imgur)
            max_height: Maximum height in pixels (default: 600px - high quality for Imgur)

        Returns:
            Base64 encoded resized image or empty string if processing fails
        """
        if not screenshot_base64:
            return ""

        try:
            # Decode base64 image
            image_bytes = base64.b64decode(screenshot_base64)
            image = Image.open(io.BytesIO(image_bytes))

            # Get original dimensions
            original_width, original_height = image.size
            logging.info(f"Original image size: {original_width}x{original_height}")

            # Calculate scaling to fit within max dimensions while maintaining aspect ratio
            width_ratio = max_width / original_width
            height_ratio = max_height / original_height
            scale_ratio = min(width_ratio, height_ratio)

            # Only resize if image is larger than max dimensions
            if scale_ratio < 1:
                new_width = int(original_width * scale_ratio)
                new_height = int(original_height * scale_ratio)

                # Resize with high quality
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logging.info(f"Resized image to: {new_width}x{new_height}")
            else:
                logging.info("Image already within size limits, no resizing needed")

            # Convert to RGB if not already (remove transparency)
            if image.mode in ('RGBA', 'LA', 'P'):
                rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'RGBA':
                    rgb_image.paste(image, mask=image.split()[-1])
                else:
                    rgb_image.paste(image)
                image = rgb_image

            # 🎯 HIGH QUALITY: Use 85% quality for Imgur hosting (no size restrictions)
            output_buffer = io.BytesIO()
            image.save(output_buffer, format='JPEG', quality=85, optimize=True)

            # Encode to base64
            resized_base64 = base64.b64encode(output_buffer.getvalue()).decode('utf-8')

            # Log compression results
            original_size = len(screenshot_base64)
            new_size = len(resized_base64)
            compression_ratio = (1 - new_size / original_size) * 100 if original_size > 0 else 0

            logging.info(
                f"High quality optimization: {original_size:,} → {new_size:,} chars ({compression_ratio:.1f}% change)")

            return resized_base64

        except Exception as e:
            logging.error(f"Error resizing screenshot: {str(e)}")
            return ""  # Return empty string on error

    print("💡 To implement high quality images:")
    print("1. Replace bitcoin_laws_scraper.py with the version above")
    print("2. Update the _resize_screenshot_for_email method in enhanced_notification_handler.py")
    print("3. Images will now be 800x600 with 85-90% quality instead of 300x200 with 60% quality")
    print("4. Perfect clarity for Imgur hosting with no size limitations!")


if __name__ == "__main__":
    update_notification_handler_for_hq()
