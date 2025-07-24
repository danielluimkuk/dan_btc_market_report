import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Dict
import os
import time
import logging
from mvrv_scraper import MVRVScraper
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 🎯 NEW: Import Pi Cycle indicator
from pi_cycle_indicator import PiCycleTopIndicator

# Add this at the top of asset_data_collector.py (after imports)
import os
import sys

# Fix Windows console encoding for Unicode characters
if os.name == 'nt':  # Windows
    try:
        # Try to set UTF-8 encoding for Windows console
        os.system('chcp 65001 >nul')
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='ignore')
    except:
        pass  # If it fails, just continue without emoji support


# Alternative: Replace emoji logging with simple text
# In your logging statements, you could replace:
# logging.info("🟢 HYBRID BTC: LIVE price from CoinGecko...")
# with:
# logging.info("SUCCESS: HYBRID BTC: LIVE price from CoinGecko...")

class HybridBTCCollector:
    """
    🎯 HYBRID BTC Collector: CoinGecko Live Prices + Polygon Historical Data + Pi Cycle

    Primary: CoinGecko for live BTC prices (real-time, free)
    Secondary: Polygon.io for EMA200 & Weekly RSI (historical, works on free tier)
    Tertiary: TradingView for MVRV (web scraping)
    🎯 NEW: Pi Cycle Top Indicator integration
    Fallback: Polygon yesterday close (when CoinGecko fails)
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('POLYGON_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Polygon API key required for historical data. Set POLYGON_API_KEY environment variable or pass api_key parameter")

        self.api_key = self.api_key.strip()
        self.base_url = "https://api.polygon.io"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BTC-Monitor-Hybrid/1.0'
        })

        # Initialize MVRV scraper
        self.mvrv_scraper = MVRVScraper()

        # 🎯 NEW: Initialize Pi Cycle indicator
        self.pi_cycle_indicator = PiCycleTopIndicator(polygon_api_key=self.api_key)

    def get_btc_data(self) -> Dict:
        """
        🎯 ENHANCED: Get complete BTC data: Live price + Historical indicators + MVRV + Pi Cycle + Mining Cost
        Returns dict with: price, weekly_rsi, ema_200, mvrv, pi_cycle, mining_cost, price_source
        """
        try:
            logging.info("🎯 Starting ENHANCED HYBRID BTC data collection with Pi Cycle + Mining Cost...")

            # 🎯 Get LIVE BTC price from CoinGecko (or fallback to Polygon yesterday)
            price_result = self.get_live_btc_price_with_fallback()
            current_price = price_result['price']
            price_source = price_result['source']
            price_note = price_result['note']

            # 🎯 ENHANCED LOGGING: Clear indication of what's happening
            if price_source == 'coingecko':
                logging.info(f"🟢 HYBRID BTC: LIVE price from CoinGecko: ${current_price:,.2f}")
                logging.info(f"   📡 {price_note}")
                logging.info(f"   🎯 SUCCESS: Using real-time market data!")
            elif price_source == 'polygon_yesterday':
                logging.warning(f"🟡 HYBRID BTC: Yesterday close from Polygon: ${current_price:,.2f}")
                logging.warning(f"   📡 {price_note}")
                logging.warning(f"   ⚠️ FALLBACK: CoinGecko failed, using 1-day old data")
            elif price_source == 'polygon_2day_old':
                logging.error(f"🔴 HYBRID BTC: 2-day old close from Polygon: ${current_price:,.2f}")
                logging.error(f"   📡 {price_note}")
                logging.error(f"   🚨 STALE FALLBACK: Using 2-day old data - check APIs!")
            else:
                logging.warning(f"❓ HYBRID BTC: Unknown source '{price_source}': ${current_price:,.2f}")

            # Add delay to respect rate limits
            time.sleep(15)

            # Get daily data for EMA200 calculation (Polygon historical - works on free tier)
            daily_ema_200 = self.get_daily_ema_200()
            logging.info(f"✅ EMA200 collected: ${daily_ema_200:,.2f}")

            # Add delay to respect rate limits
            time.sleep(15)

            # Get weekly data for RSI calculation (Polygon historical - works on free tier)
            weekly_rsi = self.get_weekly_rsi()
            logging.info(f"✅ Weekly RSI collected: {weekly_rsi:.1f}")

            # Get MVRV from TradingView scraper
            logging.info("Collecting MVRV data from TradingView...")
            mvrv_value = self.mvrv_scraper.get_mvrv_value(verbose=False)
            logging.info(f"✅ MVRV collected: {mvrv_value:.2f}")

            # 🎯 NEW: Get Pi Cycle Top indicator data
            logging.info("🥧 Collecting Pi Cycle Top indicator data...")
            pi_cycle_data = self.pi_cycle_indicator.get_pi_cycle_analysis(current_btc_price=current_price)

            # 🎯 DEBUG: Log Pi Cycle collection status
            if pi_cycle_data.get('success'):
                proximity_level = pi_cycle_data.get('signal_status', {}).get('proximity_level', 'UNKNOWN')
                gap_percentage = pi_cycle_data.get('current_values', {}).get('gap_percentage', 0)
                logging.info(f"✅ Pi Cycle collected: {proximity_level} ({gap_percentage:.1f}% gap)")
            else:
                logging.warning(f"⚠️ Pi Cycle collection failed: {pi_cycle_data.get('error', 'Unknown error')}")

            # 🎯 NEW: Get Mining Cost data
            logging.info("⛏️ Collecting Bitcoin mining cost data...")
            mining_cost_data = self.get_mining_cost_data()

            if mining_cost_data.get('success'):
                mining_cost = mining_cost_data.get('mining_cost', 'N/A')
                data_date = mining_cost_data.get('data_date', 'Unknown')
                logging.info(f"✅ Mining Cost collected: ${mining_cost:,.0f} (Date: {data_date})")
            else:
                mining_cost = 'N/A'
                data_date = 'N/A'
                logging.warning(f"⚠️ Mining Cost collection failed: {mining_cost_data.get('error', 'Unknown error')}")

            # 🎯 FINAL STATUS LOG
            logging.info(f"📊 Complete BTC indicators: EMA200=${daily_ema_200:,.2f}, "
                         f"Weekly RSI={weekly_rsi:.1f}, MVRV={mvrv_value:.2f}, "
                         f"Pi Cycle={pi_cycle_data.get('signal_status', {}).get('proximity_level', 'FAILED')}, "
                         f"Mining Cost=${mining_cost if mining_cost != 'N/A' else 'N/A'}")

            result = {
                'success': True,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'price': current_price,
                'price_source': price_source,
                'price_note': price_note,
                'ema_200': daily_ema_200,
                'weekly_rsi': weekly_rsi,
                'mvrv': mvrv_value,
                'pi_cycle': pi_cycle_data,  # 🎯 NEW: Include Pi Cycle data
                'mining_cost': mining_cost,  # 🎯 NEW: Include Mining Cost
                'mining_cost_date': data_date,  # 🎯 NEW: Include data date
                'source': f'{price_source} + polygon_historical + tradingview + pi_cycle + macromicro'
            }

            logging.info(f"🎉 Complete ENHANCED HYBRID BTC data collected successfully with Pi Cycle + Mining Cost!")
            return result

        except Exception as e:
            logging.error(f"Error collecting enhanced BTC data: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'pi_cycle': {'success': False, 'error': f'Collection failed: {str(e)}'},  # 🎯 Include failed Pi Cycle
                'mining_cost': 'N/A',  # 🎯 Include failed Mining Cost
                'mining_cost_date': 'N/A'
            }

    def get_live_btc_price_with_fallback(self) -> Dict:
        """
        🎯 PRIMARY: Get live BTC price from CoinGecko
        🔄 FALLBACK: Use Polygon yesterday closing price (free tier compatible)
        """

        # Method 1: CoinGecko Live Price (BEST - Real-time, Free, No API key)
        try:
            logging.info("🥒 Attempting CoinGecko live price collection...")
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': 'bitcoin',
                'vs_currencies': 'usd',
                'include_last_updated_at': 'true'
            }

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            price = data['bitcoin']['usd']
            last_updated = data['bitcoin'].get('last_updated_at', 0)

            if last_updated:
                updated_time = datetime.fromtimestamp(last_updated)
                age_seconds = (datetime.now() - updated_time).total_seconds()

                if age_seconds < 300:  # Less than 5 minutes old
                    note = f"🟢 LIVE PRICE (updated {age_seconds:.0f}s ago)"
                else:
                    note = f"🟡 RECENT PRICE (updated {age_seconds / 60:.0f}m ago)"
            else:
                note = "🟢 LIVE PRICE"

            logging.info(f"✅ CoinGecko live BTC price: ${price:,.2f} - {note}")

            return {
                'price': price,
                'source': 'coingecko',
                'note': note,
                'method': 'live_api'
            }

        except Exception as e:
            logging.error(f"❌ CoinGecko price collection failed: {str(e)}")

        # Method 2: Polygon Yesterday Close (FALLBACK - Free tier compatible)
        logging.warning("🚨 CoinGecko failed, falling back to Polygon yesterday close")

        try:
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            url = f"{self.base_url}/v1/open-close/crypto/BTC/USD/{yesterday}"

            logging.info(f"🟠 Attempting Polygon yesterday close for {yesterday}...")
            response = self.session.get(url, params={'apikey': self.api_key})
            response.raise_for_status()

            data = response.json()
            if data.get('status') == 'OK' and 'close' in data:
                price = data['close']

                # 🚨 CLEAR VISUAL INDICATOR for yesterday's price
                note = f"🔴 YESTERDAY CLOSE ({yesterday}) - NOT LIVE!"

                logging.warning(f"⚠️ Using Polygon yesterday close: ${price:,.2f} ({yesterday})")

                return {
                    'price': price,
                    'source': 'polygon_yesterday',
                    'note': note,
                    'method': 'historical_fallback',
                    'date': yesterday
                }

        except Exception as e:
            logging.error(f"❌ Polygon yesterday close also failed: {str(e)}")

        # Method 3: Try 2 days ago (final fallback)
        try:
            two_days_ago = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
            url = f"{self.base_url}/v1/open-close/crypto/BTC/USD/{two_days_ago}"

            logging.warning(f"🚨 Attempting Polygon 2-day old close for {two_days_ago}...")
            response = self.session.get(url, params={'apikey': self.api_key})
            response.raise_for_status()

            data = response.json()
            if data.get('status') == 'OK' and 'close' in data:
                price = data['close']

                # 🚨 EVEN MORE PROMINENT WARNING for 2-day old price
                note = f"🔴 2-DAY OLD CLOSE ({two_days_ago}) - VERY STALE!"

                logging.error(f"🚨 Using 2-day old Polygon close: ${price:,.2f} ({two_days_ago})")

                return {
                    'price': price,
                    'source': 'polygon_2day_old',
                    'note': note,
                    'method': 'stale_fallback',
                    'date': two_days_ago
                }

        except Exception as e:
            logging.error(f"❌ All price collection methods failed: {str(e)}")

        raise Exception("Could not get BTC price from any source (CoinGecko + Polygon fallbacks)")

    def get_daily_ema_200(self) -> float:
        """Get daily EMA200 for BTC using Polygon free tier (WORKS - Historical data)"""
        try:
            end_date = datetime.now() - timedelta(days=2)
            start_date = end_date - timedelta(days=450)

            url = f"{self.base_url}/v2/aggs/ticker/X:BTCUSD/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"

            response = self.session.get(url, params={'apikey': self.api_key})
            response.raise_for_status()

            data = response.json()

            if data.get('status') not in ['OK', 'DELAYED']:
                raise Exception(f"API returned status: {data.get('status', 'unknown')}")

            if 'results' not in data or not data['results']:
                raise Exception("No results in API response")

            closes = [bar['c'] for bar in data['results']]

            if len(closes) < 200:
                raise Exception(f"Insufficient data for EMA200: only {len(closes)} days available")

            ema_200 = self.calculate_ema(closes, 200)
            logging.info(f"Daily EMA200 calculated: ${ema_200:.2f} (using {len(closes)} days of data)")
            return ema_200

        except Exception as e:
            logging.error(f"Error calculating daily EMA200: {str(e)}")
            raise Exception(f"Could not calculate daily EMA200: {str(e)}")

    def get_weekly_rsi(self) -> float:
        """Get weekly RSI for BTC using Polygon free tier (WORKS - Historical data)"""
        try:
            end_date = datetime.now() - timedelta(days=7)
            start_date = end_date - timedelta(days=800)

            url = f"{self.base_url}/v2/aggs/ticker/X:BTCUSD/range/1/week/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"

            response = self.session.get(url, params={'apikey': self.api_key})
            response.raise_for_status()

            data = response.json()

            if data.get('status') not in ['OK', 'DELAYED']:
                raise Exception(f"API returned status: {data.get('status', 'unknown')}")

            if 'results' not in data or not data['results']:
                raise Exception("No results in weekly API response")

            closes = [bar['c'] for bar in data['results']]

            if len(closes) < 30:
                raise Exception(f"Insufficient weekly data for RSI: only {len(closes)} weeks available")

            rsi = self.calculate_rsi(closes, 14)
            logging.info(f"Weekly RSI calculated: {rsi:.1f} (using {len(closes)} weeks of data)")
            return rsi

        except Exception as e:
            logging.error(f"Error calculating weekly RSI: {str(e)}")
            raise Exception(f"Could not calculate weekly RSI: {str(e)}")

    def calculate_ema(self, prices: list, period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            raise ValueError(f"Not enough data points. Need {period}, got {len(prices)}")

        df = pd.Series(prices)
        ema = df.ewm(span=period, adjust=False).mean()
        return float(ema.iloc[-1])

    def calculate_rsi(self, prices: list, period: int = 14) -> float:
        """Calculate Relative Strength Index using STANDARD Wilder's method"""
        if len(prices) < period + 1:
            raise ValueError(f"Not enough data points for RSI. Need {period + 1}, got {len(prices)}")

        prices_series = pd.Series(prices)
        delta = prices_series.diff().dropna()

        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)

        # ✅ FIX: Use Wilder's exponential smoothing instead of simple average
        avg_gain = gains.ewm(alpha=1 / period, adjust=False).mean()
        avg_loss = losses.ewm(alpha=1 / period, adjust=False).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return float(rsi.iloc[-1])

    def test_api_connection(self) -> bool:
        """Test if Polygon API connection is working"""
        try:
            url = f"{self.base_url}/v3/reference/tickers/X:BTCUSD"
            response = self.session.get(url, params={'apikey': self.api_key})
            response.raise_for_status()

            data = response.json()
            if data.get('status') == 'OK':
                logging.info("Polygon API connection test successful")
                return True
            else:
                logging.error(f"API test failed: {data}")
                return False

        except Exception as e:
            logging.error(f"API connection test failed: {str(e)}")
            return False

    def test_coingecko_connection(self) -> bool:
        """Test if CoinGecko API is working"""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {'ids': 'bitcoin', 'vs_currencies': 'usd'}

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            if 'bitcoin' in data and 'usd' in data['bitcoin']:
                price = data['bitcoin']['usd']
                logging.info(f"CoinGecko connection test successful - BTC: ${price:,.2f}")
                return True
            else:
                logging.error("CoinGecko test failed: Invalid response format")
                return False

        except Exception as e:
            logging.error(f"CoinGecko connection test failed: {str(e)}")
            return False

    def get_mining_cost_data(self) -> Dict:
        """
        Get Bitcoin average mining cost from CCAF (Cambridge Centre for Alternative Finance)
        Returns dict with mining_cost and data_date, or N/A values if failed
        """
        driver = None
        try:
            logging.info("⛏️ Collecting Bitcoin mining cost from CCAF...")

            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

            driver = webdriver.Chrome(options=chrome_options)
            driver.get("https://ccaf.io/cbnsi/cbeci/mining_map/mining_data")

            # Wait for page to load
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(8)  # Additional wait for dynamic content

            # Extract mining cost value using CCAF XPath
            try:
                mining_cost_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH,
                                                    '//*[@id="wrap-container"]/div[3]/div/div[1]/div[1]/div/div/div[2]/div/div[2]/div/div[2]/h2'))
                )
                mining_cost_text = mining_cost_element.text.strip()
                logging.info(f"📊 Raw CCAF mining cost text: '{mining_cost_text}'")

                # Parse the value - remove commas, dollar signs, etc.
                clean_text = mining_cost_text.replace(',', '').replace('$', '').replace(' ', '')

                # Extract numeric value
                value_match = re.search(r'([0-9]+\.?[0-9]*)', clean_text)
                if value_match:
                    mining_cost = float(value_match.group(1))

                    # Validate range (10,000 to 1,500,000)
                    if 10000 <= mining_cost <= 1500000:
                        logging.info(f"✅ Valid CCAF mining cost extracted: ${mining_cost:,.0f}")
                    else:
                        logging.warning(f"⚠️ CCAF mining cost out of valid range: ${mining_cost:,.0f}")
                        return {'mining_cost': 'N/A', 'data_date': 'CCAF Data', 'error': 'Value out of range'}
                else:
                    logging.warning(f"⚠️ Could not parse numeric value from CCAF: '{mining_cost_text}'")
                    return {'mining_cost': 'N/A', 'data_date': 'CCAF Data', 'error': 'Could not parse value'}

            except Exception as e:
                logging.error(f"❌ Failed to extract CCAF mining cost: {str(e)}")
                return {'mining_cost': 'N/A', 'data_date': 'CCAF Data', 'error': 'Element not found'}

            # Small delay to be respectful to the server
            time.sleep(2)

            return {
                'mining_cost': mining_cost,
                'data_date': 'CCAF Data',  # Static label since no date extraction needed
                'success': True
            }

        except Exception as e:
            logging.error(f"❌ CCAF mining cost collection failed: {str(e)}")
            return {'mining_cost': 'N/A', 'data_date': 'CCAF Data', 'error': str(e)}
        finally:
            if driver:
                driver.quit()

# Updated AssetDataCollector class for integration
class HybridAssetDataCollector:
    """
    🎯 ENHANCED HYBRID Asset collector: CoinGecko live prices + Polygon historical + TradingView MVRV + Pi Cycle
    """

    def __init__(self):
        self.btc_collector = None
        try:
            self.btc_collector = HybridBTCCollector()

            # Test both APIs
            polygon_ok = self.btc_collector.test_api_connection()
            coingecko_ok = self.btc_collector.test_coingecko_connection()

            if not polygon_ok:
                logging.warning("Polygon API connection test failed during initialization")
            if not coingecko_ok:
                logging.warning("CoinGecko API connection test failed during initialization")

        except Exception as e:
            logging.error(f"Failed to initialize hybrid BTC collector: {str(e)}")

    def collect_asset_data(self, asset: str, config: Dict) -> Dict:
        """Main method to collect data for an asset"""
        try:
            if asset == 'BTC':
                return self._collect_btc_data_hybrid()
            elif asset == 'MSTR':
                return self._collect_mstr_data()
            else:
                return {'success': False, 'error': f'Unknown asset: {asset}'}

        except Exception as e:
            logging.error(f'Error collecting data for {asset}: {str(e)}')
            return {'success': False, 'error': str(e)}

    def _collect_btc_data_hybrid(self) -> Dict:
        """🎯 ENHANCED HYBRID: Collect Bitcoin data using CoinGecko live + Polygon historical + Pi Cycle + Mining Cost"""
        btc_data = {
            'success': False,
            'type': 'crypto',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'price': 0,
            'price_source': 'unknown',
            'price_note': '',
            'indicators': {},
            'pi_cycle': {},  # 🎯 NEW: Initialize Pi Cycle data
            'metadata': {'source': 'coingecko_live + polygon_historical + tradingview + pi_cycle + macromicro'}
        }

        try:
            if not self.btc_collector:
                raise Exception("Hybrid BTC collector not available")

            # Get complete BTC data (live price + historical indicators + Pi Cycle + Mining Cost)
            hybrid_data = self.btc_collector.get_btc_data()

            if hybrid_data.get('success'):
                btc_data['price'] = hybrid_data.get('price', 0)
                btc_data['price_source'] = hybrid_data.get('price_source', 'unknown')
                btc_data['price_note'] = hybrid_data.get('price_note', '')
                btc_data['indicators']['ema_200'] = hybrid_data.get('ema_200')
                btc_data['indicators']['weekly_rsi'] = hybrid_data.get('weekly_rsi')
                btc_data['indicators']['mvrv'] = hybrid_data.get('mvrv')

                # 🎯 NEW: Add mining cost to indicators
                mining_cost = hybrid_data.get('mining_cost', 'N/A')
                mining_cost_date = hybrid_data.get('mining_cost_date', 'N/A')

                btc_data['indicators']['mining_cost'] = mining_cost
                btc_data['indicators']['mining_cost_date'] = mining_cost_date

                # 🎯 NEW: Calculate price/cost ratio
                if mining_cost != 'N/A' and mining_cost > 0:
                    price_cost_ratio = round(hybrid_data.get('price', 0) / mining_cost, 2)
                    btc_data['indicators']['price_cost_ratio'] = price_cost_ratio
                    logging.info(f"💰 Price/Cost Ratio calculated: {price_cost_ratio}")
                else:
                    btc_data['indicators']['price_cost_ratio'] = 'N/A'
                    logging.warning("⚠️ Could not calculate Price/Cost Ratio")

                btc_data['pi_cycle'] = hybrid_data.get('pi_cycle', {})  # 🎯 NEW: Include Pi Cycle data
                btc_data['metadata']['source'] = hybrid_data.get('source')
                btc_data['success'] = True

                # 🎯 DEBUG: Log Pi Cycle data persistence
                pi_cycle_success = btc_data['pi_cycle'].get('success', False)
                if pi_cycle_success:
                    proximity_level = btc_data['pi_cycle'].get('signal_status', {}).get('proximity_level', 'UNKNOWN')
                    gap_percentage = btc_data['pi_cycle'].get('current_values', {}).get('gap_percentage', 0)
                    logging.info(f"🎯 Pi Cycle data persisted: {proximity_level} ({gap_percentage:.1f}% gap)")
                else:
                    logging.warning(
                        f"⚠️ Pi Cycle data failed to persist: {btc_data['pi_cycle'].get('error', 'Unknown')}")

            else:
                btc_data['error'] = hybrid_data.get('error', 'Unknown hybrid API error')
                btc_data['pi_cycle'] = hybrid_data.get('pi_cycle', {'success': False, 'error': 'Collection failed'})
                btc_data['indicators']['mining_cost'] = 'N/A'
                btc_data['indicators']['mining_cost_date'] = 'N/A'
                btc_data['indicators']['price_cost_ratio'] = 'N/A'
                logging.error(f'Hybrid API error: {btc_data["error"]}')

        except Exception as e:
            btc_data['error'] = str(e)
            btc_data['pi_cycle'] = {'success': False, 'error': f'Collection exception: {str(e)}'}
            btc_data['indicators']['mining_cost'] = 'N/A'
            btc_data['indicators']['mining_cost_date'] = 'N/A'
            btc_data['indicators']['price_cost_ratio'] = 'N/A'
            logging.error(f'Error collecting enhanced hybrid BTC data: {str(e)}')

        return btc_data

    def _collect_mstr_data(self) -> Dict:
        """Keep existing MSTR collection logic"""
        return {
            'success': False,
            'type': 'stock',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error': 'MSTR collection not implemented in this version'
        }


# For backward compatibility - use this as your main collector
UpdatedAssetDataCollector = HybridAssetDataCollector
EnhancedPolygonBTCCollector = HybridBTCCollector

# Testing
if __name__ == "__main__":
    import logging
    from dotenv import load_dotenv

    # Load .env file
    load_dotenv()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    print("Testing ENHANCED HYBRID BTC Collector (CoinGecko Live + Polygon Historical + Pi Cycle)...")
    print("=" * 80)

    try:
        collector = HybridBTCCollector()

        # Test API connections
        polygon_ok = collector.test_api_connection()
        coingecko_ok = collector.test_coingecko_connection()

        print(f"🔌 Polygon API: {'✅ Connected' if polygon_ok else '❌ Failed'}")
        print(f"🔌 CoinGecko API: {'✅ Connected' if coingecko_ok else '❌ Failed'}")

        if polygon_ok or coingecko_ok:
            print("\n📊 Testing complete BTC data collection...")
            btc_data = collector.get_btc_data()

            if btc_data['success']:
                print(f"\n📊 Complete ENHANCED HYBRID BTC Data Retrieved:")
                print(f"   💰 Price: ${btc_data['price']:,.2f}")
                print(f"   📡 Source: {btc_data['price_source']}")
                print(f"   📝 Note: {btc_data['price_note']}")
                print(f"   📈 Daily EMA200: ${btc_data['ema_200']:,.2f}")
                print(f"   📊 Weekly RSI: {btc_data['weekly_rsi']:.1f}")
                print(f"   🔥 MVRV: {btc_data['mvrv']:.2f}")

                # 🎯 NEW: Show Pi Cycle data
                pi_cycle = btc_data.get('pi_cycle', {})
                if pi_cycle.get('success'):
                    proximity_level = pi_cycle.get('signal_status', {}).get('proximity_level', 'UNKNOWN')
                    gap_percentage = pi_cycle.get('current_values', {}).get('gap_percentage', 0)
                    print(f"   🥧 Pi Cycle: {proximity_level} ({gap_percentage:.1f}% gap)")
                else:
                    print(f"   🥧 Pi Cycle: FAILED - {pi_cycle.get('error', 'Unknown error')}")

                print(f"   🕐 Timestamp: {btc_data['timestamp']}")
                print(f"   📡 Full Source: {btc_data['source']}")

                # Show the improvement
                if btc_data['price_source'] == 'coingecko':
                    print(f"\n🎉 SUCCESS: Using LIVE price from CoinGecko!")
                else:
                    print(f"\n⚠️ FALLBACK: Using historical price from Polygon")
                    print(f"   💡 This is better than broken real-time attempts")

            else:
                print(f"❌ Error: {btc_data['error']}")
        else:
            print("❌ Both API connections failed")

    except Exception as e:
        print(f"❌ Failed to initialize: {str(e)}")
        print("\n💡 Make sure to:")
        print("   1. Create a .env file with POLYGON_API_KEY=your_api_key")
        print("   2. Install required packages: pip install pandas numpy requests python-dotenv")
        print("   3. Ensure internet connection for CoinGecko API")
        print("   4. Ensure pi_cycle_indicator.py is in the same directory")
