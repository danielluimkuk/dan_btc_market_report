#!/usr/bin/env python3
"""
📊 Manual Market Monitor - FIXED VERSION with Pi Cycle Support
Run this script anytime to get your Bitcoin + MSTR market report!

🎯 FIXES:
- Preserves Pi Cycle data in processing pipeline
- Proper error handling for Pi Cycle integration
- Updated data validation to handle Pi Cycle

Usage:
    python manual_market_monitor.py
    python manual_market_monitor.py --no-emoji  # For Windows console compatibility
"""

import os
import sys
import logging
import traceback
from datetime import datetime, timezone
from typing import Dict, List, Any

# Fix Windows console encoding for Unicode characters
EMOJI_SUPPORT = True
if os.name == 'nt':  # Windows
    try:
        # Try to set UTF-8 encoding for Windows console
        os.system('chcp 65001 >nul 2>&1')
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='ignore')
    except:
        EMOJI_SUPPORT = False  # Disable emojis if encoding fails

# Check command line arguments for emoji disable
if '--no-emoji' in sys.argv:
    EMOJI_SUPPORT = False


def safe_print(message):
    """Print message with emoji fallback for Windows compatibility"""
    if EMOJI_SUPPORT:
        try:
            print(message)
        except UnicodeEncodeError:
            # Fallback: remove emojis and try again
            import re
            clean_message = re.sub(r'[^\x00-\x7F]+', '', message)  # Remove non-ASCII
            print(clean_message)
    else:
        # Remove emojis completely
        import re
        clean_message = re.sub(r'[^\x00-\x7F]+', '', message)
        print(clean_message)


# Import your existing modules
try:
    from asset_data_collector import UpdatedAssetDataCollector as AssetDataCollector
    from enhanced_notification_handler import EnhancedNotificationHandler
    from data_storage import DataStorage
    from mstr_analyzer import collect_mstr_data_with_retry
    from bitcoin_laws_scraper import capture_bitcoin_laws_screenshot
    from monetary_analyzer import MonetaryAnalyzer
except ImportError as e:
    safe_print(f"❌ Import Error: {e}")
    safe_print("💡 Make sure all your module files are in the same directory!")
    sys.exit(1)

# Load environment variables from .env file (if present)
try:
    from dotenv import load_dotenv

    load_dotenv()
    safe_print("✅ Loaded environment variables from .env file")
except ImportError:
    safe_print("💡 python-dotenv not installed - loading env vars from system")
except Exception:
    safe_print("💡 No .env file found - using system environment variables")


class ManualMarketMonitor:
    """
    🚀 FIXED Manual Market Monitor - Now supports Pi Cycle data properly!
    """

    def __init__(self):
        self.setup_logging()
        self.validate_environment()

        # Initialize components
        self.collector = AssetDataCollector()
        self.notification_handler = EnhancedNotificationHandler()

        # Optional: Disable Azure Storage for local testing
        if os.getenv('DISABLE_AZURE_STORAGE', '').lower() in ['true', '1', 'yes']:
            safe_print("💡 Azure Storage disabled for local testing")
            self.data_storage = None
        else:
            self.data_storage = DataStorage()

        self.monetary_analyzer = MonetaryAnalyzer(storage=self.data_storage)

        safe_print("🎯 Manual Market Monitor initialized successfully!")

    def setup_logging(self):
        """Setup logging for console output with Unicode handling"""

        # Create custom formatter that removes emojis from log messages
        class CleanFormatter(logging.Formatter):
            def format(self, record):
                # Remove emojis from log messages to avoid Unicode errors
                if hasattr(record, 'msg'):
                    import re
                    record.msg = re.sub(r'[^\x00-\x7F]+', '', str(record.msg))
                return super().format(record)

        # Configure logging with emoji-free output
        log_formatter = CleanFormatter('%(asctime)s - %(levelname)s - %(message)s')

        # File handler (full logging)
        file_handler = logging.FileHandler(f'market_monitor_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        file_handler.setFormatter(log_formatter)
        file_handler.setLevel(logging.INFO)

        # Console handler (warnings and errors only to reduce noise)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(CleanFormatter('%(levelname)s - %(message)s'))
        console_handler.setLevel(logging.WARNING)  # Only show warnings and errors in console

        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            handlers=[file_handler, console_handler]
        )

        safe_print("📝 Clean logging configured - check log file for detailed output")

    def validate_environment(self):
        """Validate required environment variables"""
        required_vars = [
            'POLYGON_API_KEY',
            'EMAIL_USER',
            'EMAIL_PASSWORD'
        ]

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            safe_print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            safe_print("💡 Set these in your .env file or system environment")
            sys.exit(1)

        # Check for recipients - fallback to EMAIL_USER if RECIPIENT_EMAILS not set
        recipient_emails = os.getenv('RECIPIENT_EMAILS', '').strip()
        email_user = os.getenv('EMAIL_USER', '').strip()

        if not recipient_emails and email_user:
            safe_print("💡 RECIPIENT_EMAILS not set - will send report to EMAIL_USER only")
            os.environ['RECIPIENT_EMAILS'] = email_user
        elif not recipient_emails:
            safe_print("❌ Neither RECIPIENT_EMAILS nor EMAIL_USER is set")
            sys.exit(1)

        safe_print("✅ All required environment variables found")

    def run_market_analysis(self) -> bool:
        """
        🎯 FIXED: Main function with proper Pi Cycle data handling
        """
        try:
            safe_print("\n" + "=" * 80)
            safe_print("🚀 STARTING MANUAL MARKET MONITOR")
            safe_print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            safe_print("=" * 80)

            # Step 1: Define assets to monitor
            assets_config = {
                'BTC': {
                    'type': 'crypto',
                    'sources': ['polygon', 'tradingview_mvrv', 'pi_cycle']  # Added pi_cycle
                },
                'MSTR': {
                    'type': 'stock',
                    'sources': ['ballistic', 'volatility']
                }
            }

            safe_print(f"\n📊 Collecting data for assets: {list(assets_config.keys())}")

            # Step 2: Collect asset data
            collected_data = {}

            # BTC Collection
            safe_print("\n💰 Collecting BTC data...")
            btc_data = self.collector.collect_asset_data('BTC', assets_config['BTC'])
            collected_data['BTC'] = btc_data

            if btc_data.get('success'):
                price = btc_data.get('price', 0)
                safe_print(f"✅ BTC Success: ${price:,.2f}")

                # 🎯 NEW: Check Pi Cycle data
                pi_cycle_data = btc_data.get('pi_cycle', {})
                if pi_cycle_data and pi_cycle_data.get('success'):
                    pi_status = pi_cycle_data.get('signal_status', {}).get('proximity_level', 'UNKNOWN')
                    pi_gap = pi_cycle_data.get('current_values', {}).get('gap_percentage', 0)
                    safe_print(f"🥧 Pi Cycle Success: {pi_status} ({pi_gap:.1f}% gap)")
                else:
                    safe_print(
                        f"⚠️ Pi Cycle Warning: {pi_cycle_data.get('error', 'No data') if pi_cycle_data else 'Missing'}")
            else:
                safe_print(f"❌ BTC Failed: {btc_data.get('error', 'Unknown error')}")

            # MSTR Collection (with retry mechanism)
            safe_print("\n📈 Collecting MSTR data with retry mechanism...")
            btc_price = btc_data.get('price', 95000) if btc_data.get('success') else 95000

            mstr_data = collect_mstr_data_with_retry(btc_price, max_attempts=3)
            collected_data['MSTR'] = mstr_data

            if mstr_data.get('success'):
                price = mstr_data.get('price', 0)
                indicators = mstr_data.get('indicators', {})
                model_price = indicators.get('model_price', 0)
                deviation = indicators.get('deviation_pct', 0)
                safe_print(f"✅ MSTR Success: ${price:.2f} (Model: ${model_price:.2f}, Dev: {deviation:+.1f}%)")
            else:
                safe_print(f"❌ MSTR Failed: {mstr_data.get('error', 'Unknown error')}")

            # Step 3: Collect monetary data
            safe_print("\n🏦 Collecting monetary policy data...")
            monetary_data = self.monetary_analyzer.get_monetary_analysis()

            if monetary_data.get('success'):
                data_date = monetary_data.get('data_date', 'Unknown')
                days_old = monetary_data.get('days_old', 0)
                safe_print(f"✅ Monetary Success: {data_date} ({days_old} days old)")
            else:
                safe_print(f"❌ Monetary Failed: {monetary_data.get('error', 'Unknown error')}")

            # Step 4: Capture Bitcoin Laws screenshot
            safe_print("\n⚖️ Capturing Bitcoin Laws screenshot...")
            bitcoin_laws_screenshot = capture_bitcoin_laws_screenshot(verbose=True)

            if bitcoin_laws_screenshot:
                screenshot_size = len(bitcoin_laws_screenshot)
                safe_print(f"✅ Screenshot Success: {screenshot_size:,} characters")
            else:
                safe_print("❌ Screenshot Failed")

            # Step 5: Process and validate data
            safe_print("\n🔍 Processing and validating data...")
            processed_data = self.process_asset_data_fixed(collected_data)  # 🎯 FIXED method
            processed_data['monetary'] = monetary_data

            # Step 6: Store data (if storage is available)
            if self.data_storage and self.data_storage.table_service:
                safe_print("\n💾 Storing data to Azure Table Storage...")
                try:
                    self.data_storage.store_daily_data(processed_data)
                    safe_print("✅ Data stored successfully")
                except Exception as e:
                    safe_print(f"⚠️ Storage failed: {str(e)} (continuing anyway)")
            else:
                safe_print("💡 Azure Storage not configured/disabled - skipping data storage")

            # Step 7: Determine if we should send report
            should_send = self.should_send_report_fixed(processed_data, collected_data,
                                                        bitcoin_laws_screenshot, monetary_data)

            if should_send['send']:
                safe_print(f"\n📧 {should_send['reason']}")
                safe_print("📤 Generating and sending email report...")

                # Generate alerts
                alerts = self.generate_alerts(processed_data)

                # Send the report
                self.notification_handler.send_daily_report(
                    processed_data, alerts, bitcoin_laws_screenshot
                )

                safe_print("✅ Email report sent successfully!")

                # Summary
                self.print_summary_fixed(collected_data, monetary_data)

                return True
            else:
                safe_print(f"\n⚠️ Report not sent: {should_send['reason']}")
                safe_print(f"📋 Details: {should_send.get('details', 'No additional details')}")

                # Send error notification instead
                error_message = f"""
Manual Market Monitor Report - Components Status

Reason: {should_send['reason']}

COMPONENT STATUS:
- BTC: {'✅ SUCCESS' if collected_data.get('BTC', {}).get('success') else '❌ FAILED'}
- MSTR: {'✅ SUCCESS' if collected_data.get('MSTR', {}).get('success') else '❌ FAILED'}  
- Bitcoin Laws Screenshot: {'✅ SUCCESS' if bitcoin_laws_screenshot else '❌ FAILED'}
- Monetary Data: {'✅ SUCCESS' if monetary_data.get('success') else '❌ FAILED'}

DETAILS:
{should_send.get('details', 'No additional details')}

Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """

                self.notification_handler.send_error_notification(error_message)
                safe_print("📧 Error notification sent instead")
                return False

        except Exception as e:
            error_msg = f"Critical error in manual market analysis: {str(e)}\n{traceback.format_exc()}"
            safe_print(f"\n❌ {error_msg}")
            logging.error(error_msg)

            try:
                self.notification_handler.send_error_notification(error_msg)
                safe_print("📧 Error notification sent")
            except Exception as notify_error:
                safe_print(f"❌ Failed to send error notification: {str(notify_error)}")

            return False

    def process_asset_data_fixed(self, collected_data: Dict) -> Dict:
        """
        🎯 FIXED: Process asset data while preserving Pi Cycle data CORRECTLY
        """
        processed = {
            'timestamp': datetime.utcnow().isoformat(),
            'assets': {},
            'summary': {
                'total_assets': len(collected_data),
                'successful_collections': 0,
                'failed_collections': 0
            }
        }

        for asset, data in collected_data.items():
            if data.get('success', False):
                processed['summary']['successful_collections'] += 1

                if asset == 'BTC':
                    # 🎯 CRITICAL FIX: Only include Pi Cycle if it actually has data
                    btc_asset_data = {
                        'type': data.get('type', 'crypto'),
                        'price': data.get('price', 0),
                        'indicators': data.get('indicators', {}),
                        'metadata': data.get('metadata', {}),
                        'last_updated': data.get('timestamp'),
                        'price_source': data.get('price_source', 'unknown'),
                        'price_note': data.get('price_note', '')
                    }

                    # 🎯 NEW: Only add pi_cycle if it exists AND has success=True
                    pi_cycle_data = data.get('pi_cycle')
                    if pi_cycle_data and pi_cycle_data.get('success'):
                        btc_asset_data['pi_cycle'] = pi_cycle_data
                        print(
                            f"✅ Pi Cycle preserved in processing: {pi_cycle_data.get('signal_status', {}).get('proximity_level', 'UNKNOWN')}")
                    else:
                        print(
                            f"⚠️ Pi Cycle not preserved - data: {bool(pi_cycle_data)}, success: {pi_cycle_data.get('success') if pi_cycle_data else False}")

                    processed['assets'][asset] = btc_asset_data

                elif asset == 'MSTR':
                    processed['assets'][asset] = {
                        'type': data.get('type', 'stock'),
                        'price': data.get('price', 0),
                        'indicators': data.get('indicators', {}),
                        'analysis': data.get('analysis', {}),
                        'metadata': data.get('metadata', {}),
                        'last_updated': data.get('timestamp'),
                        'attempts_made': data.get('attempts_made', 1)
                    }
            else:
                processed['summary']['failed_collections'] += 1
                processed['assets'][asset] = {
                    'type': data.get('type', 'unknown'),
                    'error': data.get('error', 'Unknown error'),
                    'last_updated': datetime.utcnow().isoformat(),
                    'attempts_made': data.get('attempts_made', 1)
                }

        return processed

    def should_send_report_fixed(self, processed_data: Dict, collected_data: Dict,
                                 bitcoin_laws_screenshot: str = "", monetary_data: Dict = None) -> Dict:
        """
        🎯 FIXED: Updated validation that considers Pi Cycle data
        """
        try:
            # Core component checks
            btc_success = collected_data.get('BTC', {}).get('success', False)
            mstr_success = collected_data.get('MSTR', {}).get('success', False)
            screenshot_success = bool(bitcoin_laws_screenshot and len(bitcoin_laws_screenshot) > 100)
            monetary_success = monetary_data.get('success', False) if monetary_data else False

            # Data quality validation (updated to handle Pi Cycle)
            btc_data_quality = self.validate_btc_data_quality_fixed(processed_data.get('assets', {}).get('BTC', {}))
            mstr_data_quality = self.validate_mstr_data_quality(collected_data.get('MSTR', {}))

            # Core components must succeed
            core_components_ready = (
                    btc_success and btc_data_quality['is_valid'] and
                    mstr_success and mstr_data_quality['is_valid'] and
                    screenshot_success
            )

            if core_components_ready:
                if monetary_success:
                    return {
                        'send': True,
                        'reason': 'ALL components successful: BTC + MSTR + Bitcoin Laws + Monetary Data + Pi Cycle',
                        'details': 'Complete enhanced report ready with all data sources including Pi Cycle'
                    }
                else:
                    return {
                        'send': True,
                        'reason': 'Core components successful: BTC + MSTR + Bitcoin Laws + Pi Cycle (Monetary data failed but proceeding)',
                        'details': f'Monetary error: {monetary_data.get("error", "Unknown") if monetary_data else "Not attempted"}'
                    }
            else:
                # Determine what failed
                failed_components = []

                if not btc_success:
                    failed_components.append("BTC collection failed")
                elif not btc_data_quality['is_valid']:
                    failed_components.append(f"BTC data quality poor: {'; '.join(btc_data_quality['issues'])}")

                if not mstr_success:
                    failed_components.append("MSTR collection failed")
                elif not mstr_data_quality['is_valid']:
                    failed_components.append("MSTR data quality poor")

                if not screenshot_success:
                    failed_components.append("Bitcoin Laws screenshot failed/empty")

                return {
                    'send': False,
                    'reason': 'Core components failed',
                    'details': f'Failed: {"; ".join(failed_components)}'
                }

        except Exception as e:
            return {
                'send': False,
                'reason': 'Error evaluating data quality for report sending',
                'details': str(e)
            }

    def validate_btc_data_quality_fixed(self, btc_data: Dict) -> Dict:
        """
        🎯 FIXED: Validate BTC data quality including Pi Cycle
        """
        issues = []

        try:
            if 'error' in btc_data:
                issues.append(f"BTC has error: {btc_data['error']}")
                return {'is_valid': False, 'issues': issues}

            # Check price
            price = btc_data.get('price', 0)
            if not price or price <= 0:
                issues.append(f"Invalid price: {price}")

            # Check indicators
            indicators = btc_data.get('indicators', {})

            mvrv = indicators.get('mvrv', 0)
            if not mvrv or mvrv <= 0:
                issues.append(f"Invalid MVRV: {mvrv}")

            weekly_rsi = indicators.get('weekly_rsi', 0)
            if not weekly_rsi or weekly_rsi <= 0:
                issues.append(f"Invalid Weekly RSI: {weekly_rsi}")

            ema_200 = indicators.get('ema_200', 0)
            if not ema_200 or ema_200 <= 0:
                issues.append(f"Invalid EMA 200: {ema_200}")

            # 🎯 NEW: Validate Pi Cycle data (but don't require it)
            pi_cycle_data = btc_data.get('pi_cycle', {})
            if pi_cycle_data:
                if not pi_cycle_data.get('success'):
                    # Pi Cycle failed, but don't fail the whole validation
                    safe_print(f"⚠️ Pi Cycle validation: {pi_cycle_data.get('error', 'Unknown error')}")
                else:
                    # Pi Cycle succeeded, validate basic structure
                    current_values = pi_cycle_data.get('current_values', {})
                    if not current_values.get('gap_percentage'):
                        safe_print("⚠️ Pi Cycle missing gap percentage")
                    else:
                        safe_print(f"✅ Pi Cycle validation: {current_values.get('gap_percentage', 0):.1f}% gap")

            is_valid = len(issues) == 0
            return {'is_valid': is_valid, 'issues': issues}

        except Exception as e:
            return {'is_valid': False, 'issues': [f"Validation error: {str(e)}"]}

    def validate_mstr_data_quality(self, mstr_data: Dict) -> Dict:
        """Validate MSTR data quality (unchanged)"""
        issues = []

        try:
            if not mstr_data.get('success'):
                issues.append(f"Collection failed: {mstr_data.get('error', 'Unknown error')}")
                return {'is_valid': False, 'issues': issues}

            # Check price
            price = mstr_data.get('price', 0)
            if not price or price <= 0:
                issues.append(f"Invalid price: {price}")

            # Check indicators
            indicators = mstr_data.get('indicators', {})

            model_price = indicators.get('model_price', 0)
            if not model_price or model_price <= 0 or not (1 < model_price < 10000):
                issues.append(f"Invalid model price: {model_price}")

            deviation_pct = indicators.get('deviation_pct', None)
            if deviation_pct is None:
                issues.append("Missing deviation percentage")

            # IV validation
            iv = indicators.get('iv', 0)
            if iv == 0:
                issues.append("Missing main IV (Implied Volatility) data")

            is_valid = len(issues) == 0
            return {'is_valid': is_valid, 'issues': issues}

        except Exception as e:
            return {'is_valid': False, 'issues': [f"Validation error: {str(e)}"]}

    def generate_alerts(self, data: Dict) -> List[Dict]:
        """Generate alerts based on asset data (simplified version)"""
        alerts = []

        for asset, asset_data in data['assets'].items():
            if 'error' in asset_data:
                alerts.append({
                    'type': 'data_error',
                    'asset': asset,
                    'message': f"Failed to collect data for {asset}: {asset_data['error']}",
                    'severity': 'high'
                })

        return alerts

    def print_summary_fixed(self, collected_data: Dict, monetary_data: Dict):
        """
        🎯 FIXED: Print summary including Pi Cycle information
        """
        safe_print("\n" + "=" * 80)
        safe_print("📊 MARKET ANALYSIS SUMMARY")
        safe_print("=" * 80)

        # BTC Summary
        btc_data = collected_data.get('BTC', {})
        if btc_data.get('success'):
            price = btc_data.get('price', 0)
            indicators = btc_data.get('indicators', {})
            mvrv = indicators.get('mvrv', 0)
            rsi = indicators.get('weekly_rsi', 0)
            ema_200 = indicators.get('ema_200', 0)

            safe_print(f"💰 BTC: ${price:,.2f}")
            safe_print(f"   📊 MVRV: {mvrv:.2f}")
            safe_print(f"   📈 Weekly RSI: {rsi:.1f}")
            safe_print(f"   📉 EMA 200: ${ema_200:,.2f}")
            safe_print(f"   🎯 Market: {'🐂 Bull' if price >= ema_200 else '🐻 Bear'}")

            # 🎯 NEW: Pi Cycle Summary
            pi_cycle_data = btc_data.get('pi_cycle', {})
            if pi_cycle_data and pi_cycle_data.get('success'):
                status = pi_cycle_data.get('signal_status', {})
                values = pi_cycle_data.get('current_values', {})
                proximity = status.get('proximity_level', 'UNKNOWN')
                gap = values.get('gap_percentage', 0)
                safe_print(f"   🥧 Pi Cycle: {proximity} ({gap:.1f}% gap)")
            else:
                safe_print(f"   🥧 Pi Cycle: ❌ Failed")

        # MSTR Summary
        mstr_data = collected_data.get('MSTR', {})
        if mstr_data.get('success'):
            price = mstr_data.get('price', 0)
            indicators = mstr_data.get('indicators', {})
            model_price = indicators.get('model_price', 0)
            deviation = indicators.get('deviation_pct', 0)
            iv = indicators.get('iv', 0)

            safe_print(f"\n📈 MSTR: ${price:.2f}")
            safe_print(f"   🎯 Model: ${model_price:.2f}")
            safe_print(f"   📊 Deviation: {deviation:+.1f}%")
            safe_print(f"   🎭 IV: {iv:.1f}%")

        # Monetary Summary
        if monetary_data and monetary_data.get('success'):
            data_date = monetary_data.get('data_date', 'Unknown')
            days_old = monetary_data.get('days_old', 0)
            fixed_rates = monetary_data.get('fixed_rates', {})

            safe_print(f"\n🏦 Monetary Data: {data_date} ({days_old} days old)")
            if 'fed_funds' in fixed_rates:
                safe_print(f"   📊 Fed Funds: {fixed_rates['fed_funds']:.2f}%")
            if 'real_rate' in fixed_rates:
                safe_print(f"   📊 Real Rate: {fixed_rates['real_rate']:.1f}%")

        safe_print("\n✅ Analysis complete! Check your email for the full report WITH Pi Cycle data.")
        safe_print("=" * 80)


def main():
    """Main function to run the manual market monitor"""
    safe_print("📊 Manual Bitcoin Market Monitor")
    safe_print("🚀 Starting on-demand market analysis...")

    try:
        monitor = ManualMarketMonitor()
        success = monitor.run_market_analysis()

        if success:
            safe_print("\n🎉 SUCCESS: Market analysis completed and email sent!")
            sys.exit(0)
        else:
            safe_print("\n⚠️ PARTIAL SUCCESS: Analysis completed but report not sent due to data issues")
            sys.exit(1)

    except KeyboardInterrupt:
        safe_print("\n🛑 Analysis cancelled by user")
        sys.exit(1)
    except Exception as e:
        safe_print(f"\n💥 FATAL ERROR: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
