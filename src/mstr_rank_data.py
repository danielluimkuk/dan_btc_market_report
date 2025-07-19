#!/usr/bin/env python3
"""
Clean MSTR Market Cap Rank Scraper - Production Ready
Reliable, minimal, and won't break if popup is removed
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
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from typing import Dict
from datetime import datetime, timezone

# Fix Windows console encoding
if os.name == 'nt':
    try:
        os.system('chcp 65001 >nul')
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
    except:
        pass


class MSTRRankScraper:
    """Clean MSTR Market Cap Rank Scraper"""

    def __init__(self):
        self.url = "https://stockanalysis.com/list/biggest-companies/"

    def get_mstr_rank(self) -> Dict:
        """Get MSTR's market cap rank"""
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
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Load page
            driver.get(self.url)
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)

            # Handle popup if present (graceful - won't fail if no popup)
            self._handle_popup_gracefully(driver)

            # Wait for main table
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "main-table")))
            
            # Wait for content to load
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//table[@id='main-table']//td[contains(text(), 'Apple')]"))
                )
                logging.info("✅ Table content loaded")
            except TimeoutException:
                logging.warning("⚠️ Content loading timeout, proceeding anyway...")
            
            time.sleep(3)

            # Light scrolling to ensure content is loaded
            self._ensure_content_loaded(driver)

            # Find MSTR
            mstr_rank = self._find_mstr_rank(driver)

            if mstr_rank and isinstance(mstr_rank, int) and 1 <= mstr_rank <= 500:
                logging.info(f"✅ Found MSTR at rank #{mstr_rank}")
                return {
                    'success': True,
                    'rank': mstr_rank,
                    'company_name': 'MicroStrategy Incorporated',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            else:
                logging.warning("⚠️ MSTR not found or rank outside valid range")
                return {
                    'success': True,  # Still success, just with N/A rank
                    'rank': 'N/A',
                    'company_name': 'MicroStrategy Incorporated',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }

        except Exception as e:
            logging.error(f"❌ Scraping failed: {str(e)}")
            return {
                'success': True,  # Still success, just with N/A rank
                'rank': 'N/A',
                'company_name': 'MicroStrategy Incorporated',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        finally:
            if driver:
                driver.quit()

    def _handle_popup_gracefully(self, driver):
        """
        Handle popup if present - graceful, won't fail if popup doesn't exist
        """
        try:
            # Quick popup dismissal attempts - no exceptions if they fail
            popup_actions = [
                # ESC key (most universal)
                lambda: driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE),
                # JavaScript removal (catches most modals)
                lambda: driver.execute_script("""
                    try {
                        document.querySelectorAll('.modal, .popup, .overlay, [class*="modal"], [class*="popup"], [class*="overlay"]').forEach(el => el.remove());
                        document.body.style.overflow = 'auto';
                    } catch(e) { /* ignore */ }
                """),
            ]
            
            for action in popup_actions:
                try:
                    action()
                    time.sleep(1)
                except:
                    pass  # Gracefully ignore any errors
                    
        except Exception:
            pass  # Completely graceful - no logging even

    def _ensure_content_loaded(self, driver):
        """Light scrolling to ensure table content is fully loaded"""
        try:
            # Simple scroll pattern to trigger any lazy loading
            for scroll_pct in [0.3, 0.6, 1.0]:
                driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {scroll_pct});")
                time.sleep(1)
            
            # Scroll back to top
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
        except Exception:
            pass  # Graceful failure

    def _find_mstr_rank(self, driver) -> int:
        """Find MSTR rank using the reliable main-table approach"""
        try:
            # Primary method: XPath with main-table ID (what we know works)
            xpath_selectors = [
                "//table[@id='main-table']//a[contains(@href, '/stocks/mstr/')]/ancestor::tr/td[1]",
                "//table[@id='main-table']//td[contains(text(), 'MSTR')]/ancestor::tr/td[1]",
                "//table[@id='main-table']//tr[contains(., 'MSTR')]/td[1]",
            ]
            
            for selector in xpath_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text.isdigit():
                            rank = int(text)
                            if 1 <= rank <= 500:  # Reasonable range
                                return rank
                except:
                    continue

            # Fallback method: Table iteration (backup)
            try:
                main_table = driver.find_element(By.ID, "main-table")
                tbody = main_table.find_element(By.TAG_NAME, "tbody")
                rows = tbody.find_elements(By.TAG_NAME, "tr")
                
                for row in rows:
                    try:
                        if 'MSTR' in row.text.upper() or 'MICROSTRATEGY' in row.text.upper():
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if cells:
                                rank_text = cells[0].text.strip()
                                if rank_text.isdigit():
                                    rank = int(rank_text)
                                    if 1 <= rank <= 500:
                                        return rank
                    except:
                        continue
                        
            except:
                pass

            return None
            
        except Exception:
            return None


def get_mstr_rank(max_attempts: int = 2) -> Dict:
    """Get MSTR rank with retry - returns 'N/A' if unable to find valid rank"""
    for attempt in range(1, max_attempts + 1):
        logging.info(f"🔄 Attempt {attempt}/{max_attempts}")
        try:
            scraper = MSTRRankScraper()
            result = scraper.get_mstr_rank()

            # Check if we got a valid numeric rank
            if result.get('success') and isinstance(result.get('rank'), int):
                logging.info(f"✅ Success on attempt {attempt}")
                result['attempts_made'] = attempt
                return result

            # If we got N/A and this is the last attempt, return it
            if attempt == max_attempts:
                logging.warning(f"⚠️ Returning N/A after {max_attempts} attempts")
                result['attempts_made'] = attempt
                return result

            if attempt < max_attempts:
                logging.info("💤 Waiting 10s before retry...")
                time.sleep(10)

        except Exception as e:
            logging.error(f"❌ Attempt {attempt} failed: {str(e)}")
            if attempt == max_attempts:
                return {
                    'success': True,  # Still success, just with N/A
                    'rank': 'N/A',
                    'company_name': 'MicroStrategy Incorporated',
                    'attempts_made': attempt,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            time.sleep(10)

    # Fallback (shouldn't reach here, but just in case)
    return {
        'success': True,
        'rank': 'N/A',
        'company_name': 'MicroStrategy Incorporated',
        'attempts_made': max_attempts,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    print("🎯 Clean MSTR Market Cap Rank Scraper")
    print("✅ Production ready - handles popup gracefully")
    print("✅ Won't break if popup is removed")
    print("✅ Returns 'N/A' instead of failing")
    print("=" * 60)

    result = get_mstr_rank()

    if result.get('success'):
        rank = result.get('rank')
        if isinstance(rank, int):
            print(f"\n🎉 SUCCESS! MSTR Rank: #{rank}")
        else:
            print(f"\n⚠️ RANK N/A: {rank}")
        print(f"   Company: {result.get('company_name', 'N/A')}")
        print(f"   Attempts: {result.get('attempts_made', 1)}")
    else:
        print(f"\n❌ UNEXPECTED ERROR: {result.get('error', 'Unknown error')}")
        print(f"   Attempts: {result.get('attempts_made', 'N/A')}")

    print(f"\n🎯 Clean scraper test completed!")
