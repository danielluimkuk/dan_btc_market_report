import requests
import base64
import logging
import os
from typing import Optional


class ImgurUploader:
    """
    Imgur image uploader for email-friendly image hosting
    Solves Gmail image display issues by hosting images externally
    """

    def __init__(self):
        # Get Imgur client ID from environment
        self.client_id = os.getenv('IMGUR_CLIENT_ID')
        self.upload_url = "https://api.imgur.com/3/image"

        if not self.client_id:
            logging.warning("IMGUR_CLIENT_ID not found - image hosting will be disabled")

    def upload_base64_image(self, base64_image: str, title: str = "Bitcoin Laws Screenshot") -> Optional[str]:
        """
        Upload base64 image to Imgur and return public URL

        Args:
            base64_image: Base64 encoded image string
            title: Title for the uploaded image

        Returns:
            Public Imgur URL or None if upload fails
        """
        if not self.client_id:
            logging.error("Cannot upload to Imgur: IMGUR_CLIENT_ID not configured")
            return None

        if not base64_image:
            logging.error("Cannot upload empty image")
            return None

        try:
            headers = {
                "Authorization": f"Client-ID {self.client_id}",
                "Content-Type": "application/json"
            }

            # Prepare the data
            data = {
                "image": base64_image,
                "type": "base64",
                "title": title,
                "description": f"Bitcoin Laws screenshot generated at {logging.Formatter().formatTime(logging.LogRecord('', 0, '', 0, '', (), None))}"
            }

            logging.info(f"Uploading {len(base64_image):,} character image to Imgur...")

            # Upload to Imgur
            response = requests.post(self.upload_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()

            result = response.json()

            if result.get('success'):
                image_url = result['data']['link']
                logging.info(f"✅ Imgur upload successful: {image_url}")
                return image_url
            else:
                logging.error(f"Imgur upload failed: {result.get('data', {}).get('error', 'Unknown error')}")
                return None

        except requests.exceptions.RequestException as e:
            logging.error(f"Network error uploading to Imgur: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error uploading to Imgur: {str(e)}")
            return None

    def upload_image_file(self, file_path: str, title: str = "Bitcoin Laws Screenshot") -> Optional[str]:
        """
        Upload image file to Imgur and return public URL

        Args:
            file_path: Path to image file
            title: Title for the uploaded image

        Returns:
            Public Imgur URL or None if upload fails
        """
        if not self.client_id:
            logging.error("Cannot upload to Imgur: IMGUR_CLIENT_ID not configured")
            return None

        try:
            with open(file_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')

            return self.upload_base64_image(image_data, title)

        except FileNotFoundError:
            logging.error(f"Image file not found: {file_path}")
            return None
        except Exception as e:
            logging.error(f"Error reading image file: {str(e)}")
            return None


def test_imgur_upload():
    """Test function to verify Imgur upload is working"""

    # Create a small test image (red 1x1 pixel)
    test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAHPn4JI0QAAAABJRU5ErkJggg=="

    uploader = ImgurUploader()

    if not uploader.client_id:
        print("❌ IMGUR_CLIENT_ID not configured")
        print("💡 Add IMGUR_CLIENT_ID to your environment variables")
        print("📝 Get one free at: https://api.imgur.com/oauth2/addclient")
        return False

    print("🔍 Testing Imgur upload...")
    url = uploader.upload_base64_image(test_image_b64, "Test Image")

    if url:
        print(f"✅ Imgur upload test successful: {url}")
        return True
    else:
        print("❌ Imgur upload test failed")
        return False


if __name__ == "__main__":
    test_imgur_upload()
