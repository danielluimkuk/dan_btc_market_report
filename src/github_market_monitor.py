#!/usr/bin/env python3
"""
GitHub Actions Market Monitor - Converted from Azure Function
Runs the same logic as function_app.py but without Azure Functions wrapper
"""

import os
import sys
import logging
from datetime import datetime, timezone
import traceback
from typing import Dict, List, Any

# Add current directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import your existing modules (no changes needed to these!)
from asset_data_collector import UpdatedAssetDataCollector as AssetDataCollector
from enhanced_notification_handler import EnhancedNotificationHandler
from data_storage import DataStorage
from mstr_analyzer import collect_mstr_data_with_retry
from bitcoin_laws_scraper import capture_bitcoin_laws_screenshot
from monetary_analyzer import MonetaryAnalyzer


def setup_logging():
    """Setup logging for GitHub Actions"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    """
    Main function - this is essentially your asset_monitor_timer function
    from function_app.py but adapted for GitHub Actions
    """
    setup_logging()
    logging.info('🚀 GitHub Actions Market Monitor started at %s', datetime.utcnow())

    try:
        # Initialize components (same as your Azure Function)
        collector = AssetDataCollector()
        notification_handler = EnhancedNotificationHandler()
        data_storage = DataStorage()
        monetary_analyzer = MonetaryAnalyzer(storage=data_storage)

        # Define assets to monitor (unchanged from your function_app.py)
        assets_config = {
            'BTC': {
                'type': 'crypto',
                'sources': ['polygon', 'tradingview_mvrv']
            },
            'MSTR': {
                'type': 'stock',
                'sources': ['ballistic', 'volatility']
            }
        }

        # Collect data for all assets (same logic as your Azure Function)
        logging.info(f'Collecting data for assets: {list(assets_config.keys())}')
        collected_data = {}

        for asset, config in assets_config.items():
            logging.info(f'Processing {asset}...')

            if asset == 'BTC':
                asset_data = collector.collect_asset_data(asset, config)
            elif asset == 'MSTR':
                btc_price = None
                if 'BTC' in collected_data and collected_data['BTC'].get('success'):
                    btc_price = collected_data['BTC'].get('price', 95000)
                else:
                    btc_price = 95000

                logging.info(f'Collecting MSTR data with retry mechanism using BTC price: ${btc_price:,.2f}')
                asset_data = collect_mstr_data_with_retry(btc_price, max_attempts=3)
            else:
                asset_data = {'success': False, 'error': f'Unknown asset: {asset}'}

            collected_data[asset] = asset_data
            logging.info(f'{asset} collection result: {"SUCCESS" if asset_data.get("success") else "FAILED"}')

        # Collect monetary analysis (same as your Azure Function)
        logging.info("Collecting monetary policy data...")
        monetary_data = monetary_analyzer.get_monetary_analysis()

        if monetary_data.get('success'):
            logging.info(f"✅ Monetary data collected: {monetary_data.get('data_date')} ({monetary_data.get('days_old')} days old)")
        else:
            logging.warning(f"⚠️ Monetary data failed: {monetary_data.get('error')}")

        # Capture Bitcoin Laws screenshot (same as your Azure Function)
        logging.info("Capturing Bitcoin Laws screenshot...")
        bitcoin_laws_screenshot = capture_bitcoin_laws_screenshot(verbose=True)

        if bitcoin_laws_screenshot:
            logging.info("✅ Bitcoin Laws screenshot captured successfully")
        else:
            logging.warning("⚠️ Bitcoin Laws screenshot failed")

        # Process and analyze data (use your existing functions from function_app.py)
        processed_data = process_asset_data(collected_data)
        processed_data['monetary'] = monetary_data

        # Store data (same as your Azure Function)
        logging.info('Storing processed data')
        data_storage.store_daily_data(processed_data)

        # Check if we should send the report (use your existing function)
        should_send_report = should_send_daily_report_enhanced(
            processed_data, collected_data, bitcoin_laws_screenshot, monetary_data
        )

        if should_send_report['send']:
            logging.info('All components successful - generating and sending enhanced report')
            alerts = generate_alerts(processed_data, data_storage)
            notification_handler.send_daily_report(processed_data, alerts, bitcoin_laws_screenshot)
            logging.info('✅ Enhanced Market Monitor completed successfully')
            return True
        else:
            logging.warning(f'Report not sent: {should_send_report["reason"]}')
            error_message = f"""
GitHub Actions Daily Report - Component Status

Reason: {should_send_report['reason']}

COMPONENT STATUS:
- BTC: {'✅ SUCCESS' if collected_data.get('BTC', {}).get('success') else '❌ FAILED'}
- MSTR: {'✅ SUCCESS' if collected_data.get('MSTR', {}).get('success') else '❌ FAILED'}  
- Bitcoin Laws Screenshot: {'✅ SUCCESS' if bitcoin_laws_screenshot else '❌ FAILED'}
- Monetary Data: {'✅ SUCCESS' if monetary_data.get('success') else '❌ FAILED'}

DETAILS:
{should_send_report.get('details', 'No additional details')}
            """
            notification_handler.send_error_notification(error_message)
            logging.info('Error notification sent instead of daily report')
            return False

    except Exception as e:
        logging.error(f'Error in market monitor: {str(e)}')
        logging.error(traceback.format_exc())

        try:
            error_handler = EnhancedNotificationHandler()
            error_handler.send_error_notification(f"GitHub Actions Error: {str(e)}")
        except Exception as error_ex:
            logging.error(f'Failed to send error notification: {str(error_ex)}')
        
        return False


# =============================================================================
# COPIED FUNCTIONS FROM function_app.py
# =============================================================================

def should_send_daily_report_enhanced(processed_data: Dict, collected_data: Dict,
                                      bitcoin_laws_screenshot: str = "", monetary_data: Dict = None) -> Dict:
    """
    Enhanced version that includes monetary data check
    """
    try:
        # Original checks
        btc_success = collected_data.get('BTC', {}).get('success', False)
        mstr_success = collected_data.get('MSTR', {}).get('success', False)
        screenshot_success = bool(bitcoin_laws_screenshot and len(bitcoin_laws_screenshot) > 100)

        # NEW: Monetary data check (less strict - it's OK if it fails occasionally)
        monetary_success = monetary_data.get('success', False) if monetary_data else False

        # Validate data quality
        btc_data_quality = validate_btc_data_quality(processed_data.get('assets', {}).get('BTC', {}))
        mstr_data_quality = validate_mstr_data_quality(collected_data.get('MSTR', {}))

        # Core components must succeed (unchanged policy)
        core_components_ready = (
                btc_success and btc_data_quality['is_valid'] and
                mstr_success and mstr_data_quality['is_valid'] and
                screenshot_success
        )

        if core_components_ready:
            if monetary_success:
                return {
                    'send': True,
                    'reason': 'ALL components successful: BTC + MSTR + Bitcoin Laws + Monetary Data',
                    'details': 'Complete enhanced report ready with all data sources'
                }
            else:
                return {
                    'send': True,
                    'reason': 'Core components successful: BTC + MSTR + Bitcoin Laws (Monetary data failed but proceeding)',
                    'details': f'Monetary error: {monetary_data.get("error", "Unknown") if monetary_data else "Not attempted"}'
                }
        else:
            # Determine what failed
            failed_components = []

            if not btc_success:
                failed_components.append(f"BTC collection failed")
            elif not btc_data_quality['is_valid']:
                failed_components.append(f"BTC data quality poor")

            if not mstr_success:
                failed_components.append(f"MSTR collection failed")
            elif not mstr_data_quality['is_valid']:
                failed_components.append(f"MSTR data quality poor")

            if not screenshot_success:
                failed_components.append(f"Bitcoin Laws screenshot failed/empty")

            return {
                'send': False,
                'reason': 'Core components failed',
                'details': f'Failed: {"; ".join(failed_components)}'
            }

    except Exception as e:
        logging.error(f'Error in should_send_daily_report_enhanced: {str(e)}')
        return {
            'send': False,
            'reason': 'Error evaluating data quality for report sending',
            'details': str(e)
        }


def validate_btc_data_quality(btc_data: Dict) -> Dict:
    """Validate BTC data quality"""
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

        is_valid = len(issues) == 0
        return {'is_valid': is_valid, 'issues': issues}

    except Exception as e:
        return {'is_valid': False, 'issues': [f"Validation error: {str(e)}"]}


def validate_mstr_data_quality(mstr_data: Dict) -> Dict:
    """Validate MSTR data quality"""
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

        # IV validation - only require main IV to be valid
        iv = indicators.get('iv', 0)
        if iv == 0:
            issues.append("Missing main IV (Implied Volatility) data")

        is_valid = len(issues) == 0
        return {'is_valid': is_valid, 'issues': issues}

    except Exception as e:
        return {'is_valid': False, 'issues': [f"Validation error: {str(e)}"]}


def process_asset_data(collected_data: Dict) -> Dict:
    """Process and structure collected asset data"""
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
                processed['assets'][asset] = {
                    'type': data.get('type', 'crypto'),
                    'price': data.get('price', 0),
                    'indicators': data.get('indicators', {}),
                    'metadata': data.get('metadata', {}),
                    'last_updated': data.get('timestamp')
                }
            elif asset == 'MSTR':
                processed['assets'][asset] = {
                    'type': data.get('type', 'stock'),
                    'price': data.get('price', 0),
                    'indicators': data.get('indicators', {}),
                    'analysis': data.get('analysis', {}),  # Include MSTR analysis with options strategy
                    'metadata': data.get('metadata', {}),
                    'last_updated': data.get('timestamp'),
                    'attempts_made': data.get('attempts_made', 1)
                }
            else:
                processed['assets'][asset] = {
                    'type': data.get('type', 'unknown'),
                    'price': data.get('price', 0),
                    'indicators': data.get('indicators', {}),
                    'metadata': data.get('metadata', {}),
                    'last_updated': data.get('timestamp')
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


def generate_alerts(data: Dict, storage: DataStorage) -> List[Dict]:
    """Generate alerts based on asset data and thresholds"""
    alerts = []

    for asset, asset_data in data['assets'].items():
        if 'error' in asset_data:
            alerts.append({
                'type': 'data_error',
                'asset': asset,
                'message': f"Failed to collect data for {asset}: {asset_data['error']}",
                'severity': 'high'
            })
            continue

        # Asset-specific alert logic
        if asset == 'BTC':
            alerts.extend(generate_btc_alerts(asset_data, storage))
        elif asset == 'MSTR':
            alerts.extend(generate_mstr_alerts(asset_data, storage))

    return alerts


def generate_btc_alerts(btc_data: Dict, storage: DataStorage) -> List[Dict]:
    """Generate Bitcoin-specific alerts"""
    alerts = []
    indicators = btc_data.get('indicators', {})

    # MVRV alerts
    mvrv = indicators.get('mvrv')
    if mvrv:
        if mvrv > 3.0:
            alerts.append({
                'type': 'mvrv_high',
                'asset': 'BTC',
                'message': f"BTC MVRV is high at {mvrv:.2f} - potential sell signal",
                'severity': 'medium'
            })
        elif mvrv < 1.0:
            alerts.append({
                'type': 'mvrv_low',
                'asset': 'BTC',
                'message': f"BTC MVRV is low at {mvrv:.2f} - potential buy opportunity",
                'severity': 'medium'
            })

    # RSI alerts
    rsi = indicators.get('weekly_rsi')
    if rsi:
        if rsi > 70:
            alerts.append({
                'type': 'rsi_overbought',
                'asset': 'BTC',
                'message': f"BTC Weekly RSI is overbought at {rsi:.1f}",
                'severity': 'medium'
            })
        elif rsi < 30:
            alerts.append({
                'type': 'rsi_oversold',
                'asset': 'BTC',
                'message': f"BTC Weekly RSI is oversold at {rsi:.1f}",
                'severity': 'medium'
            })

    return alerts


def generate_mstr_alerts(mstr_data: Dict, storage: DataStorage) -> List[Dict]:
    """Generate MSTR-specific alerts"""
    alerts = []
    indicators = mstr_data.get('indicators', {})
    analysis = mstr_data.get('analysis', {})

    # Model price vs actual price alerts
    model_price = indicators.get('model_price')
    actual_price = mstr_data.get('price')
    deviation_pct = indicators.get('deviation_pct')

    if model_price and actual_price and deviation_pct is not None:
        if deviation_pct >= 25:
            alerts.append({
                'type': 'mstr_overvalued',
                'asset': 'MSTR',
                'message': f"MSTR is {deviation_pct:.1f}% overvalued (${actual_price:.2f} vs ${model_price:.2f})",
                'severity': 'high'
            })
        elif deviation_pct <= -20:
            alerts.append({
                'type': 'mstr_undervalued',
                'asset': 'MSTR',
                'message': f"MSTR is {abs(deviation_pct):.1f}% undervalued (${actual_price:.2f} vs ${model_price:.2f})",
                'severity': 'medium'
            })

    # Retry attempt tracking
    attempts_made = mstr_data.get('attempts_made', 1)
    if attempts_made > 1:
        alerts.append({
            'type': 'mstr_retry',
            'asset': 'MSTR',
            'message': f"MSTR data required {attempts_made} collection attempts",
            'severity': 'low'
        })

    return alerts


if __name__ == "__main__":
    success = main()
    # Exit with appropriate code for GitHub Actions
    sys.exit(0 if success else 1)
