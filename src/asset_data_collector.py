import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Dict
import os
import time
import logging
from mvrv_scraper import MVRVScraper

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
    🎯 HYBRID BTC Collector: CoinGecko Live Prices + Polygon Historical Data

    Primary: CoinGecko for live BTC prices (real-time, free)
    Secondary: Polygon.io for EMA200 & Weekly RSI (historical, works on free tier)
    Tertiary: TradingView for MVRV (web scraping)
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

    def get_btc_data(self) -> Dict:
        """
        Get complete BTC data: Live price + Historical indicators + MVRV
        Returns dict with: price, weekly_rsi, ema_200, mvrv, price_source
        """
        try:
            logging.info("Starting HYBRID BTC data collection...")

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

            # 🎯 FINAL STATUS LOG
            logging.info(f"📊 Complete BTC indicators: EMA200=${daily_ema_200:,.2f}, "
                        f"Weekly RSI={weekly_rsi:.1f}, MVRV={mvrv_value:.2f}")

            result = {
                'success': True,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'price': current_price,
                'price_source': price_source,
                'price_note': price_note,
                'ema_200': daily_ema_200,
                'weekly_rsi': weekly_rsi,
                'mvrv': mvrv_value,
                'source': f'{price_source} + polygon_historical + tradingview'
            }

            logging.info(f"🎉 Complete HYBRID BTC data collected successfully!")
            return result

        except Exception as e:
            logging.error(f"Error collecting BTC data: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
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
    avg_gain = gains.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1/period, adjust=False).mean()
    
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


# Updated AssetDataCollector class for integration
class HybridAssetDataCollector:
    """
    🎯 HYBRID Asset collector: CoinGecko live prices + Polygon historical + TradingView MVRV
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
        """🎯 HYBRID: Collect Bitcoin data using CoinGecko live + Polygon historical"""
        btc_data = {
            'success': False,
            'type': 'crypto',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'price': 0,
            'price_source': 'unknown',
            'price_note': '',
            'indicators': {},
            'metadata': {'source': 'coingecko_live + polygon_historical + tradingview'}
        }

        try:
            if not self.btc_collector:
                raise Exception("Hybrid BTC collector not available")

            # Get complete BTC data (live price + historical indicators)
            hybrid_data = self.btc_collector.get_btc_data()

            if hybrid_data.get('success'):
                btc_data['price'] = hybrid_data.get('price', 0)
                btc_data['price_source'] = hybrid_data.get('price_source', 'unknown')
                btc_data['price_note'] = hybrid_data.get('price_note', '')
                btc_data['indicators']['ema_200'] = hybrid_data.get('ema_200')
                btc_data['indicators']['weekly_rsi'] = hybrid_data.get('weekly_rsi')
                btc_data['indicators']['mvrv'] = hybrid_data.get('mvrv')
                btc_data['metadata']['source'] = hybrid_data.get('source')
                btc_data['success'] = True

                # 🎯 Enhanced logging with price source info (already in hybrid_data method)
                # The logging is already done in the HybridBTCCollector.get_btc_data() method
                # so we don't need to duplicate it here

            else:
                btc_data['error'] = hybrid_data.get('error', 'Unknown hybrid API error')
                logging.error(f'Hybrid API error: {btc_data["error"]}')

        except Exception as e:
            btc_data['error'] = str(e)
            logging.error(f'Error collecting hybrid BTC data: {str(e)}')

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

    print("Testing HYBRID BTC Collector (CoinGecko Live + Polygon Historical)...")
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
                print(f"\n📊 Complete HYBRID BTC Data Retrieved:")
                print(f"   💰 Price: ${btc_data['price']:,.2f}")
                print(f"   📡 Source: {btc_data['price_source']}")
                print(f"   📝 Note: {btc_data['price_note']}")
                print(f"   📈 Daily EMA200: ${btc_data['ema_200']:,.2f}")
                print(f"   📊 Weekly RSI: {btc_data['weekly_rsi']:.1f}")
                print(f"   🔥 MVRV: {btc_data['mvrv']:.2f}")
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
