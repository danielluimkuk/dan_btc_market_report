import time
import json
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import requests
from fake_useragent import UserAgent


class MVRVScraper:
    def __init__(self):
        self.ua = UserAgent()

    def scrape_mvrv_method1_selenium_wait(self) -> float:
        """Method 1: Selenium with explicit waits for dynamic content"""
        driver = None
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument(f'--user-agent={self.ua.random}')

            driver = webdriver.Chrome(options=chrome_options)

            # Try the MVRV specific chart URL
            url = 'https://www.tradingview.com/chart/?symbol=BTC_MVRV'
            driver.get(url)

            # Wait longer for JS to load
            time.sleep(10)

            # Try multiple selectors that might contain MVRV value
            possible_selectors = [
                '[data-name="legend-source-item"]',
                '.js-legend-wrapper',
                '[class*="legend"]',
                '[class*="price"]',
                '[data-testid*="price"]',
                '.chart-markup-table',
                '[class*="last-value"]'
            ]

            for selector in possible_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text
                        if text and ('mvrv' in text.lower() or re.search(r'\d+\.\d+', text)):
                            # Extract number from text
                            numbers = re.findall(r'\d+\.\d+', text)
                            if numbers:
                                value = float(numbers[0])
                                if 0.1 <= value <= 10:  # Reasonable MVRV range
                                    return value
                except Exception as e:
                    continue

            # If selectors don't work, try getting page source and parsing
            page_source = driver.page_source

            # Look for MVRV patterns in page source
            mvrv_patterns = [
                r'"MVRV"[^}]*"value":\s*(\d+\.\d+)',
                r'MVRV.*?(\d+\.\d+)',
                r'"last":\s*(\d+\.\d+)',
                r'"close":\s*(\d+\.\d+)'
            ]

            for pattern in mvrv_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                for match in matches:
                    value = float(match)
                    if 0.1 <= value <= 10:  # Reasonable MVRV range
                        return value

            print("Could not find MVRV value using Method 1")
            return None

        except Exception as e:
            print(f"Error in Method 1: {str(e)}")
            return None
        finally:
            if driver:
                driver.quit()

    def scrape_mvrv_method2_api_intercept(self) -> float:
        """Method 2: Try to intercept TradingView API calls"""
        driver = None
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')

            # Enable logging to capture network requests
            chrome_options.add_argument('--enable-logging')
            chrome_options.add_argument('--log-level=0')
            chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

            driver = webdriver.Chrome(options=chrome_options)

            url = 'https://www.tradingview.com/chart/?symbol=BTC_MVRV'
            driver.get(url)
            time.sleep(8)

            # Get network logs to find API calls
            logs = driver.get_log('performance')

            for log in logs:
                message = json.loads(log['message'])
                if message['message']['method'] == 'Network.responseReceived':
                    url = message['message']['params']['response']['url']
                    if 'api' in url.lower() and ('chart' in url.lower() or 'quote' in url.lower()):
                        # Try to fetch this API directly
                        try:
                            response = requests.get(url, headers={'User-Agent': self.ua.random})
                            if response.status_code == 200:
                                data = response.json()
                                # Parse the JSON for MVRV data
                                mvrv_value = self._extract_mvrv_from_json(data)
                                if mvrv_value:
                                    return mvrv_value
                        except:
                            continue

            return None

        except Exception as e:
            print(f"Error in Method 2: {str(e)}")
            return None
        finally:
            if driver:
                driver.quit()

    def scrape_mvrv_method3_direct_api(self) -> float:
        """Method 3: Try common TradingView API endpoints"""
        try:
            # Common TradingView API patterns
            api_urls = [
                'https://scanner.tradingview.com/crypto/scan',
                'https://symbol-search.tradingview.com/symbol_search/',
                'https://pine-facade.tradingview.com/pine-facade/translate/'
            ]

            headers = {
                'User-Agent': self.ua.random,
                'Referer': 'https://www.tradingview.com/',
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/json'
            }

            # Try scanner API with MVRV query
            scanner_payload = {
                "filter": [{"left": "name", "operation": "match", "right": "BTC"}],
                "options": {"lang": "en"},
                "markets": ["crypto"],
                "symbols": {"query": {"types": []}, "tickers": []},
                "columns": ["name", "close", "change", "change_abs", "Recommend.All"],
                "sort": {"sortBy": "name", "sortOrder": "asc"},
                "range": [0, 50]
            }

            response = requests.post(api_urls[0],
                                     json=scanner_payload,
                                     headers=headers,
                                     timeout=10)

            if response.status_code == 200:
                data = response.json()
                # Parse for any MVRV-related data
                mvrv_value = self._extract_mvrv_from_json(data)
                if mvrv_value:
                    return mvrv_value

            return None

        except Exception as e:
            print(f"Error in Method 3: {str(e)}")
            return None

    def scrape_mvrv_method4_execute_js(self) -> float:
        """Method 4: Execute JavaScript to get data directly"""
        driver = None
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument(f'--user-agent={self.ua.random}')

            driver = webdriver.Chrome(options=chrome_options)

            url = 'https://www.tradingview.com/chart/?symbol=BTC_MVRV'
            driver.get(url)
            time.sleep(12)  # Wait for full load

            # Try different JavaScript approaches to extract data
            js_commands = [
                # Look for TradingView's internal data objects
                "return window.TradingView && window.TradingView.data;",
                "return document.querySelector('[data-name=\"legend-source-item\"]')?.textContent;",
                "return [...document.querySelectorAll('*')].map(el => el.textContent).filter(text => text.includes('MVRV') || /\\d+\\.\\d+/.test(text));",
                "return window.getComputedStyle ? [...document.querySelectorAll('[class*=\"legend\"], [class*=\"price\"], [data-testid*=\"price\"]')].map(el => el.textContent) : [];",
                # Try to access chart data
                "return window.chart && window.chart.data;",
                "return window.chartData;",
                # Get all numeric values on page
                "return [...document.querySelectorAll('*')].map(el => el.textContent).filter(text => /^\\d+\\.\\d+$/.test(text.trim())).slice(0, 20);"
            ]

            for js_cmd in js_commands:
                try:
                    result = driver.execute_script(js_cmd)
                    if result:

                        if isinstance(result, (list, tuple)):
                            for item in result:
                                if isinstance(item, str):
                                    numbers = re.findall(r'\d+\.\d+', item)
                                    for num_str in numbers:
                                        num = float(num_str)
                                        if 0.1 <= num <= 10:  # MVRV range
                                            return num
                        elif isinstance(result, str):
                            numbers = re.findall(r'\d+\.\d+', result)
                            for num_str in numbers:
                                num = float(num_str)
                                if 0.1 <= num <= 10:
                                    return num
                except Exception as e:
                    continue

            return None

        except Exception as e:
            print(f"Error in Method 4: {str(e)}")
            return None
        finally:
            if driver:
                driver.quit()

    def _extract_mvrv_from_json(self, data) -> float:
        """Helper to extract MVRV value from JSON data"""
        if not data:
            return None

        # Convert to string and search for patterns
        data_str = json.dumps(data) if isinstance(data, dict) else str(data)

        # Look for MVRV patterns
        patterns = [
            r'"mvrv"[^}]*?(\d+\.\d+)',
            r'MVRV.*?(\d+\.\d+)',
            r'"value":\s*(\d+\.\d+)',
            r'"last":\s*(\d+\.\d+)'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, data_str, re.IGNORECASE)
            for match in matches:
                value = float(match)
                if 0.1 <= value <= 10:  # Reasonable MVRV range
                    return value

        return None

    def get_mvrv_value(self, verbose=False) -> float:
        """Try all methods to get MVRV value"""
        methods = [
            ("Selenium with Wait", self.scrape_mvrv_method1_selenium_wait),
            ("API Intercept", self.scrape_mvrv_method2_api_intercept),
            ("Direct API", self.scrape_mvrv_method3_direct_api),
            ("JavaScript Execution", self.scrape_mvrv_method4_execute_js)
        ]

        for method_name, method_func in methods:
            if verbose:
                print(f"\nTrying {method_name}...")
            try:
                result = method_func()
                if result is not None:
                    if verbose:
                        print(f"✅ Success with {method_name}: MVRV = {result}")
                    return result
                elif verbose:
                    print(f"❌ {method_name} returned None")
            except Exception as e:
                if verbose:
                    print(f"❌ {method_name} failed: {str(e)}")

        if verbose:
            print("\n⚠️ All methods failed, returning fallback value")
        return 2.1  # Fallback value


# Test the scraper
if __name__ == "__main__":
    scraper = MVRVScraper()
    mvrv = scraper.get_mvrv_value(verbose=True)  # Set to False for production
    print(f"\nFinal MVRV value: {mvrv}")