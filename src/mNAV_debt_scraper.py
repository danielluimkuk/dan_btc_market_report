#!/usr/bin/env python3
"""
MSTR Metrics Scraper - Strategy.com Only
Scrapes mNAV, Debt Ratio, and Bitcoin Count from strategy.com using exact XPaths
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


class MSTRMetricsScraper:
    """MSTR Metrics Scraper - Strategy.com Only with Exact XPaths"""

    def __init__(self):
        self.url = "https://www.strategy.com/"

    def scrape_strategy_com(self) -> Dict:
        """
        Scrape strategy.com using exact XPaths provided by user
        """
        driver = None
        try:
            logging.info("⚡ Scraping strategy.com with exact XPaths...")

            # Setup Chrome
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument(
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            logging.info("🌐 Loading strategy.com...")
            driver.get(self.url)

            # Wait for page load
            logging.info("⏳ Waiting for page to load...")
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)

            # Quick scroll to load content
            logging.info("📜 Quick scroll to load content...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(0.5)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)

            metrics = {}

            # Exact XPaths provided by user
            xpaths = {
                'mnav_label': '/html/body/div[1]/main/div/div/div[2]/div[1]/div/div/div/div[14]/div/p[1]/span',
                'mnav_value': '/html/body/div[1]/main/div/div/div[2]/div[1]/div/div/div/div[14]/div/p[2]',
                'debt_label': '/html/body/div[1]/main/div/div/div[2]/div[1]/div/div/div/div[19]/div/p[1]/span',
                'debt_value': '/html/body/div[1]/main/div/div/div[2]/div[1]/div/div/div/div[19]/div/p[2]',
                'bitcoin_count_label': '//*[@id="__next"]/main/div/div/div[2]/div[1]/div/div/div/div[12]/div/p[1]/span',
                'bitcoin_count_value': '//*[@id="__next"]/main/div/div/div[2]/div[1]/div/div/div/div[12]/div/p[2]'
            }

            # Extract mNAV
            logging.info("🎯 Extracting mNAV...")
            try:
                mnav_label_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, xpaths['mnav_label']))
                )
                label_text = mnav_label_element.text.strip().lower()
                logging.info(f"📋 mNAV label: '{label_text}'")

                time.sleep(0.5)

                mnav_value_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, xpaths['mnav_value']))
                )
                value_text = mnav_value_element.text.strip()
                logging.info(f"📊 mNAV raw text: '{value_text}'")

                value_match = re.search(r'([0-9]+\.?[0-9]*)', value_text)
                if value_match:
                    mnav_value = float(value_match.group(1))
                    if 0.1 <= mnav_value <= 20:
                        metrics['mnav'] = mnav_value
                        logging.info(f"✅ mNAV extracted: {mnav_value}")
                    else:
                        logging.warning(f"⚠️ mNAV out of range: {mnav_value}")
                else:
                    logging.warning(f"⚠️ Could not parse mNAV from: '{value_text}'")

            except Exception as e:
                logging.error(f"❌ Failed to extract mNAV: {str(e)}")

            time.sleep(1)

            # Extract Debt Ratio
            logging.info("💰 Extracting debt ratio...")
            try:
                debt_label_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, xpaths['debt_label']))
                )
                label_text = debt_label_element.text.strip().lower()
                logging.info(f"📋 Debt label: '{label_text}'")

                time.sleep(0.5)

                debt_value_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, xpaths['debt_value']))
                )
                value_text = debt_value_element.text.strip()
                logging.info(f"💵 Debt raw text: '{value_text}'")

                value_match = re.search(r'([0-9]+\.?[0-9]*)', value_text)
                if value_match:
                    debt_value = float(value_match.group(1))
                    if 0 <= debt_value <= 100:
                        metrics['debt_ratio'] = debt_value
                        logging.info(f"✅ Debt ratio extracted: {debt_value}%")
                    else:
                        logging.warning(f"⚠️ Debt ratio out of range: {debt_value}")
                else:
                    logging.warning(f"⚠️ Could not parse debt ratio from: '{value_text}'")

            except Exception as e:
                logging.error(f"❌ Failed to extract debt ratio: {str(e)}")

            time.sleep(1)

            # Extract Bitcoin Count
            logging.info("₿ Extracting Bitcoin Count...")
            try:
                btc_label_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, xpaths['bitcoin_count_label']))
                )
                label_text = btc_label_element.text.strip().lower()
                logging.info(f"📋 Bitcoin Count label: '{label_text}'")

                time.sleep(0.5)

                btc_value_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, xpaths['bitcoin_count_value']))
                )
                value_text = btc_value_element.text.strip()
                logging.info(f"₿ Bitcoin Count raw text: '{value_text}'")

                # Clean and extract numeric value
                clean_text = value_text.replace(',', '').replace(' ', '').replace('₿', '').replace('BTC', '').replace(
                    '$', '')
                value_match = re.search(r'([0-9]+\.?[0-9]*)', clean_text)
                if value_match:
                    btc_count = float(value_match.group(1))
                    # Bitcoin count should be in hundreds of thousands
                    if 100000 <= btc_count <= 1000000:
                        metrics['bitcoin_count'] = btc_count
                        logging.info(f"✅ Bitcoin Count extracted: {btc_count}")
                    else:
                        logging.warning(f"⚠️ Bitcoin Count out of range: {btc_count}")
                        # If it's smaller, might still be valid (could be formatted differently)
                        if 100 <= btc_count <= 99999:
                            metrics['bitcoin_count'] = btc_count
                            logging.info(f"✅ Bitcoin Count extracted (alt range): {btc_count}")
                else:
                    logging.warning(f"⚠️ Could not parse Bitcoin Count from: '{value_text}'")

            except Exception as e:
                logging.error(f"❌ Failed to extract Bitcoin Count: {str(e)}")

            success = len(metrics) > 0
            if success:
                logging.info(f"🎉 Extracted {len(metrics)} metrics from strategy.com")
            else:
                logging.warning("⚠️ No metrics extracted")

            return {
                'source': 'strategy.com',
                'success': success,
                'metrics': metrics,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logging.error(f"❌ strategy.com scraping failed: {str(e)}")
            return {
                'source': 'strategy.com',
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        finally:
            if driver:
                logging.info("🧹 Cleaning up browser...")
                driver.quit()


def get_mstr_metrics(max_attempts: int = 2) -> Dict:
    """Get MSTR metrics with retry logic"""
    for attempt in range(1, max_attempts + 1):
        logging.info(f"🔄 Attempt {attempt}/{max_attempts}")
        try:
            scraper = MSTRMetricsScraper()
            result = scraper.scrape_strategy_com()

            if result.get('success'):
                logging.info(f"✅ Success on attempt {attempt}")
                result['attempts_made'] = attempt
                return result

            if attempt < max_attempts:
                logging.info("💤 Waiting 5s before retry...")
                time.sleep(5)

        except Exception as e:
            logging.error(f"❌ Attempt {attempt} failed: {str(e)}")
            if attempt == max_attempts:
                return {
                    'success': False,
                    'error': str(e),
                    'attempts_made': attempt,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            time.sleep(5)

    return {
        'success': False,
        'error': f'Failed after {max_attempts} attempts',
        'attempts_made': max_attempts,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    print("🚀 MSTR Metrics Scraper - Strategy.com Complete")
    print("📊 Targeting: mNAV, Debt Ratio, and Bitcoin Count")
    print("⚡ Using exact XPaths only...")
    print("=" * 70)

    result = get_mstr_metrics()

    if result.get('success'):
        metrics = result['metrics']
        print("\n🎉 Successfully scraped metrics from strategy.com:")
        print(f"   📊 mNAV: {metrics.get('mnav', 'Not found')}")
        print(f"   💰 (Debt + Pref)/Bitcoin NAV: {metrics.get('debt_ratio', 'Not found')}%")
        print(f"   ₿ Bitcoin Count: {metrics.get('bitcoin_count', 'Not found')}")
        print(f"   🕒 Scraped at: {result.get('timestamp', 'Unknown')}")

        # Summary
        metrics_found = len([k for k in ['mnav', 'debt_ratio', 'bitcoin_count'] if k in metrics])
        print(f"   📈 Metrics found: {metrics_found}/3")

    else:
        print(f"\n❌ Failed to scrape metrics: {result.get('error', 'Unknown error')}")
        print(f"   🔄 Attempts made: {result.get('attempts_made', 'Unknown')}")

    print(f"\n⚡ Strategy.com exclusive scraping completed! ⚡")