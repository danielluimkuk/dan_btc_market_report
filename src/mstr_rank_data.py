#!/usr/bin/env python3
"""
MSTR Market Cap Rank Scraper - Clean & Simple
Scrapes MSTR's rank from stockanalysis.com biggest companies list
"""

import os
import sys
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Dict
from datetime import datetime, timezone
import re

# Fix Windows console encoding
if os.name == 'nt':
    try:
        os.system('chcp 65001 >nul')
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
    except:
        pass


class MSTRRankScraper:
    """Simple MSTR Market Cap Rank Scraper"""

    def __init__(self):
        self.url = "https://stockanalysis.com/list/biggest-companies/"

    def get_mstr_rank(self) -> Dict:
        """Get MSTR's rank from stockanalysis.com"""
        driver = None
        try:
            logging.info("🔍 Starting MSTR rank scraping...")

            # Setup Chrome
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

            driver = webdriver.Chrome(options=chrome_options)
            driver.get(self.url)

            # Wait and load content
            logging.info("🔄 Loading page content...")
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            time.sleep(8)

            # Scroll to load all content
            for scroll_pct in [0.3, 0.6, 1.0]:
                driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {scroll_pct});")
                time.sleep(2)

            logging.info("📊 Searching for MSTR in rankings...")

            # Find MSTR using regex on page source
            page_source = driver.page_source

            # Regex patterns to find MSTR rank (ordered by reliability)
            patterns = [
                # Exact table structure
                r'<tr[^>]*>\s*<td[^>]*>(\d+)</td>\s*<td[^>]*sym[^>]*>\s*<a[^>]*href="/stocks/mstr/"[^>]*>MSTR</a></td>\s*<td[^>]*>([^<]+)</td>\s*<td[^>]*>([^<]+)</td>\s*<td[^>]*>([^<]+)</td>',
                # Simple rank + MSTR link
                r'>(\d+)</td>\s*<td[^>]*>\s*<a[^>]*href="/stocks/mstr/"[^>]*>MSTR</a>',
                # Number before MSTR link
                r'(\d+)</td>.*?<a[^>]*href="/stocks/mstr/"[^>]*>MSTR</a>',
                # General pattern
                r'>(\d+)</td>.*?MSTR.*?MicroStrategy',
            ]

            for pattern in patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE | re.DOTALL)
                if matches:
                    for match in matches:
                        try:
                            rank_str = match[0] if isinstance(match, tuple) else match
                            rank = int(rank_str)

                            if 1 <= rank <= 500:  # Valid rank range
                                logging.info(f"✅ MSTR found at rank #{rank}")
                                result = {
                                    'success': True,
                                    'rank': rank,
                                    'company_name': 'MicroStrategy Incorporated',
                                    'market_cap': 'Unknown',
                                    'stock_price': 'Unknown',
                                    'timestamp': datetime.now(timezone.utc).isoformat()
                                }

                                # Extract additional data if available
                                if isinstance(match, tuple) and len(match) >= 4:
                                    result['company_name'] = match[1].strip()
                                    result['market_cap'] = match[2].strip()
                                    result['stock_price'] = match[3].strip()

                                return result
                        except (ValueError, IndexError):
                            continue

            # Fallback: Try XPath if regex fails
            logging.info("🔄 Trying XPath fallback method...")
            try:
                mstr_link = driver.find_element(By.XPATH,
                                                "//a[@href='/stocks/mstr/' or contains(@href, '/stocks/mstr/')]")
                row = mstr_link.find_element(By.XPATH, "./ancestor::tr")
                cells = row.find_elements(By.TAG_NAME, "td")

                if cells:
                    rank_text = cells[0].text.strip()
                    if rank_text.isdigit():
                        rank = int(rank_text)
                        if 1 <= rank <= 500:
                            logging.info(f"✅ MSTR found via XPath at rank #{rank}")
                            return {
                                'success': True,
                                'rank': rank,
                                'company_name': cells[2].text.strip() if len(
                                    cells) > 2 else 'MicroStrategy Incorporated',
                                'market_cap': cells[3].text.strip() if len(cells) > 3 else 'Unknown',
                                'stock_price': cells[4].text.strip() if len(cells) > 4 else 'Unknown',
                                'timestamp': datetime.now(timezone.utc).isoformat()
                            }
            except:
                pass

            logging.warning("⚠️ MSTR not found in rankings")
            return {
                'success': False,
                'error': 'MSTR not found in rankings',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logging.error(f"❌ Scraping failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        finally:
            if driver:
                driver.quit()


def get_mstr_rank(max_attempts: int = 2) -> Dict:
    """Get MSTR rank with retry"""
    for attempt in range(1, max_attempts + 1):
        logging.info(f"🔄 Attempt {attempt}/{max_attempts}")
        try:
            scraper = MSTRRankScraper()
            result = scraper.get_mstr_rank()

            if result.get('success'):
                logging.info(f"✅ Success on attempt {attempt}")
                result['attempts_made'] = attempt
                return result

            if attempt < max_attempts:
                logging.info("💤 Waiting 10s before retry...")
                time.sleep(10)

        except Exception as e:
            logging.error(f"❌ Attempt {attempt} failed: {str(e)}")
            if attempt == max_attempts:
                return {
                    'success': False,
                    'error': str(e),
                    'attempts_made': attempt,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            time.sleep(10)

    return {
        'success': False,
        'error': f'Failed after {max_attempts} attempts',
        'attempts_made': max_attempts,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    result = get_mstr_rank()

    if result.get('success'):
        print(f"✅ MSTR Rank: #{result['rank']}")
        print(f"   Company: {result.get('company_name', 'N/A')}")
        print(f"   Market Cap: {result.get('market_cap', 'N/A')}")
        print(f"   Stock Price: {result.get('stock_price', 'N/A')}")
    else:
        print(f"❌ Failed: {result.get('error', 'Unknown error')}")