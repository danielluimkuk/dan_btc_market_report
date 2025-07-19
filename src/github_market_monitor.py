#!/usr/bin/env python3
"""
Enhanced GitHub Actions Market Monitor - Updated with Monetary Analysis Features + Pi Cycle
Includes the new True Inflation Rate and Monetary Reality insights + Pi Cycle Top Indicator
"""

import os
import sys
import logging
from datetime import datetime, timezone
import traceback
from typing import Dict, List, Any

# Add current directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import your existing modules (these now include our enhancements!)
from asset_data_collector import UpdatedAssetDataCollector as AssetDataCollector
from enhanced_notification_handler import EnhancedNotificationHandler
from data_storage import DataStorage
from mstr_analyzer import collect_mstr_data_with_retry
from bitcoin_laws_scraper import capture_bitcoin_laws_screenshot
from monetary_analyzer import MonetaryAnalyzer


def setup_logging():
    """Setup enhanced logging for GitHub Actions"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    """
    Enhanced main function with improved monetary analysis integration + Pi Cycle
    """
    setup_logging()
    logging.info('🚀 Enhanced GitHub Actions Market Monitor started at %s', datetime.utcnow())
    logging.info('✨ Now includes True Inflation Rate, Monetary Reality insights, and Pi Cycle Top Indicator!')

    try:
        # Initialize components (enhanced notification handler has our new features)
        collector = AssetDataCollector()
        notification_handler = EnhancedNotificationHandler()
        data_storage = DataStorage()
        monetary_analyzer = MonetaryAnalyzer(storage=data_storage)

        # Define assets to monitor
        assets_config = {
            'BTC': {
                'type': 'crypto',
                'sources': ['polygon', 'tradingview_mvrv', 'pi_cycle']  # 🎯 Updated to include Pi Cycle
            },
            'MSTR': {
                'type': 'stock',
                'sources': ['ballistic', 'volatility']
            }
        }

        # Collect data for all assets
        logging.info(f'📊 Collecting data for assets: {list(assets_config.keys())}')
        collected_data = {}

        for asset, config in assets_config.items():
            logging.info(f'🔄 Processing {asset}...')

            if asset == 'BTC':
                asset_data = collector.collect_asset_data(asset, config)
                
                # 🎯 DEBUG: Log Pi Cycle data presence in collected data
                pi_cycle_data = asset_data.get('pi_cycle', {})
                if pi_cycle_data.get('success'):
                    proximity_level = pi_cycle_data.get('signal_status', {}).get('proximity_level', 'UNKNOWN')
                    gap_percentage = pi_cycle_data.get('current_values', {}).get('gap_percentage', 0)
                    logging.info(f"🎯 BTC Pi Cycle collected: {proximity_level} ({gap_percentage:.1f}% gap)")
                else:
                    logging.warning(f"⚠️ BTC Pi Cycle collection issue: {pi_cycle_data.get('error', 'No Pi Cycle data')}")
                    
            elif asset == 'MSTR':
                btc_price = None
                if 'BTC' in collected_data and collected_data['BTC'].get('success'):
                    btc_price = collected_data['BTC'].get('price', 95000)
                else:
                    btc_price = 95000

                logging.info(f'📈 Collecting MSTR data with retry mechanism using BTC price: ${btc_price:,.2f}')
                asset_data = collect_mstr_data_with_retry(btc_price, max_attempts=3)
            else:
                asset_data = {'success': False, 'error': f'Unknown asset: {asset}'}

            collected_data[asset] = asset_data
            logging.info(f'{asset} collection result: {"✅ SUCCESS" if asset_data.get("success") else "❌ FAILED"}')

        # 🎯 ENHANCED: Collect monetary analysis with new features
        logging.info("🏦 Collecting enhanced monetary policy data...")
        monetary_data = monetary_analyzer.get_monetary_analysis()

        if monetary_data.get('success'):
            data_date = monetary_data.get('data_date', 'Unknown')
            days_old = monetary_data.get('days_old', 0)
            
            # 🎯 NEW: Log the enhanced monetary features
            true_inflation = monetary_data.get('true_inflation_rate')
            m2_growth = monetary_data.get('m2_20y_growth')
            
            logging.info(f"✅ Monetary data collected: {data_date} ({days_old} days old)")
            
            if true_inflation is not None:
                logging.info(f"💰 True Inflation Rate (20Y M2 CAGR): {true_inflation:.1f}%")
                breakeven_roi = true_inflation / (1 - 0.25)  # 25% tax assumption
                logging.info(f"📊 Breakeven ROI (after-tax): {breakeven_roi:.1f}%")
                logging.info(f"🎯 M2 20Y Growth: {m2_growth:.1f}%")
                logging.info("✨ Enhanced 'Monetary Reality' insight will be included in report")
            else:
                logging.warning("⚠️ True inflation rate calculation not available (may need more M2 historical data)")
                
        else:
            logging.warning(f"⚠️ Monetary data collection failed: {monetary_data.get('error')}")

        # Capture Bitcoin Laws screenshot
        logging.info("⚖️ Capturing Bitcoin Laws screenshot...")
        # bitcoin_laws_screenshot = capture_bitcoin_laws_screenshot(verbose=True) disabled for now
        bitcoin_laws_screenshot = ""
        
        if bitcoin_laws_screenshot:
            logging.info("✅ Bitcoin Laws screenshot captured successfully")
        else:
            logging.warning("⚠️ Bitcoin Laws screenshot failed")

        # Process and analyze data
        processed_data = process_asset_data_enhanced(collected_data)  # 🎯 Use enhanced function
        processed_data['monetary'] = monetary_data

        # Store data
        logging.info('💾 Storing processed data')
        data_storage.store_daily_data(processed_data)

        # 🎯 ENHANCED: Check if we should send the report (with monetary validation)
        should_send_report = should_send_daily_report_enhanced(
            processed_data, collected_data, bitcoin_laws_screenshot, monetary_data
        )

        if should_send_report['send']:
            logging.info('📧 All components ready - generating enhanced report with monetary insights and Pi Cycle')
            
            # Generate alerts
            alerts = generate_alerts(processed_data, data_storage)
            
            # 🎯 ENHANCED: Send report with new monetary features + Pi Cycle
            notification_handler.send_daily_report(processed_data, alerts, bitcoin_laws_screenshot)
            
            # Log what enhanced features were included
            if monetary_data.get('success') and monetary_data.get('true_inflation_rate'):
                logging.info('✨ Report includes enhanced monetary analysis:')
                logging.info(f'   💰 True Inflation Rate: {monetary_data["true_inflation_rate"]:.1f}%')
                logging.info('   📝 Additional "Monetary Reality" insight section')
                logging.info('   🎯 Bitcoin investment thesis strengthened by monetary debasement data')
            
            # 🎯 NEW: Log Pi Cycle inclusion status
            btc_pi_cycle = processed_data.get('assets', {}).get('BTC', {}).get('pi_cycle', {})
            if btc_pi_cycle.get('success'):
                proximity_level = btc_pi_cycle.get('signal_status', {}).get('proximity_level', 'UNKNOWN')
                gap_percentage = btc_pi_cycle.get('current_values', {}).get('gap_percentage', 0)
                logging.info(f'✨ Report includes Pi Cycle Top Indicator: {proximity_level} ({gap_percentage:.1f}% gap)')
            else:
                logging.warning(f'⚠️ Pi Cycle not included in report: {btc_pi_cycle.get("error", "No data")}')
            
            logging.info('✅ Enhanced Market Monitor completed successfully')
            return True
        else:
            logging.warning(f'📧 Report not sent: {should_send_report["reason"]}')
            
            # 🎯 ENHANCED: Include monetary status in error report
            monetary_status = "✅ SUCCESS" if monetary_data.get('success') else "❌ FAILED"
            if monetary_data.get('success') and monetary_data.get('true_inflation_rate'):
                monetary_status += f" (True Inflation: {monetary_data['true_inflation_rate']:.1f}%)"
            
            # 🎯 NEW: Include Pi Cycle status in error report
            btc_data = collected_data.get('BTC', {})
            pi_cycle_status = "❌ NOT COLLECTED"
            if btc_data.get('success'):
                pi_cycle_data = btc_data.get('pi_cycle', {})
                if pi_cycle_data.get('success'):
                    proximity_level = pi_cycle_data.get('signal_status', {}).get('proximity_level', 'UNKNOWN')
                    gap_percentage = pi_cycle_data.get('current_values', {}).get('gap_percentage', 0)
                    pi_cycle_status = f"✅ SUCCESS ({proximity_level} - {gap_percentage:.1f}% gap)"
                else:
                    pi_cycle_status = f"❌ FAILED ({pi_cycle_data.get('error', 'Unknown error')})"
            
            error_message = f"""
Enhanced GitHub Actions Daily Report - Component Status

Reason: {should_send_report['reason']}

COMPONENT STATUS:
- BTC: {'✅ SUCCESS' if collected_data.get('BTC', {}).get('success') else '❌ FAILED'}
- MSTR: {'✅ SUCCESS' if collected_data.get('MSTR', {}).get('success') else '❌ FAILED'}  
- Bitcoin Laws Screenshot: {'✅ SUCCESS' if bitcoin_laws_screenshot else '❌ FAILED'}
- Monetary Data: {monetary_status}
- Pi Cycle Indicator: {pi_cycle_status}

ENHANCED FEATURES STATUS:
- True Inflation Rate: {'✅ CALCULATED' if monetary_data.get('true_inflation_rate') else '❌ NOT AVAILABLE'}
- Monetary Reality Insight: {'✅ READY' if monetary_data.get('true_inflation_rate') else '❌ REQUIRES TRUE INFLATION DATA'}
- Pi Cycle Top Indicator: {pi_cycle_status}

DETAILS:
{should_send_report.get('details', 'No additional details')}
            """
            notification_handler.send_error_notification(error_message)
            logging.info('📧 Enhanced error notification sent instead of daily report')
            return False

    except Exception as e:
        logging.error(f'❌ Critical error in enhanced market monitor: {str(e)}')
        logging.error(traceback.format_exc())

        try:
            error_handler = EnhancedNotificationHandler()
            error_handler.send_error_notification(f"Enhanced GitHub Actions Error: {str(e)}")
        except Exception as error_ex:
            logging.error(f'❌ Failed to send error notification: {str(error_ex)}')
        
        return False


# =============================================================================
# ENHANCED FUNCTIONS (Updated to better handle new monetary features + Pi Cycle)
# =============================================================================

def should_send_daily_report_enhanced(processed_data: Dict, collected_data: Dict,
                                      bitcoin_laws_screenshot: str = "", monetary_data: Dict = None) -> Dict:
    """
    Enhanced report sending logic with improved monetary data validation + Pi Cycle
    """
    try:
        # Core component checks (unchanged)
        btc_success = collected_data.get('BTC', {}).get('success', False)
        mstr_success = collected_data.get('MSTR', {}).get('success', False)
        screenshot_success = bool(bitcoin_laws_screenshot and len(bitcoin_laws_screenshot) > 100)

        # 🎯 ENHANCED: More detailed monetary data validation
        monetary_success = monetary_data.get('success', False) if monetary_data else False
        has_enhanced_features = False
        
        if monetary_success and monetary_data:
            true_inflation = monetary_data.get('true_inflation_rate')
            m2_growth = monetary_data.get('m2_20y_growth')
            has_enhanced_features = (true_inflation is not None and m2_growth is not None)

        # 🎯 NEW: Pi Cycle validation
        pi_cycle_success = False
        pi_cycle_status = "not_collected"
        
        if btc_success:
            btc_data = collected_data.get('BTC', {})
            pi_cycle_data = btc_data.get('pi_cycle', {})
            pi_cycle_success = pi_cycle_data.get('success', False)
            
            if pi_cycle_success:
                proximity_level = pi_cycle_data.get('signal_status', {}).get('proximity_level', 'UNKNOWN')
                gap_percentage = pi_cycle_data.get('current_values', {}).get('gap_percentage', 0)
                pi_cycle_status = f"success_{proximity_level.lower()}_{gap_percentage:.1f}pct"
            else:
                pi_cycle_status = f"failed_{pi_cycle_data.get('error', 'unknown')}"

        # Validate data quality
        btc_data_quality = validate_btc_data_quality_enhanced(processed_data.get('assets', {}).get('BTC', {}))
        mstr_data_quality = validate_mstr_data_quality(collected_data.get('MSTR', {}))

        # Core components must succeed
        core_components_ready = (
                btc_success and btc_data_quality['is_valid'] and
                mstr_success and mstr_data_quality['is_valid'] and
                screenshot_success
        )

        if core_components_ready:
            if monetary_success:
                if has_enhanced_features:
                    if pi_cycle_success:
                        return {
                            'send': True,
                            'reason': 'ALL components successful with FULL enhanced features + Pi Cycle',
                            'details': f'Complete report with True Inflation ({monetary_data["true_inflation_rate"]:.1f}%), Monetary Reality insights, and Pi Cycle ({pi_cycle_status})'
                        }
                    else:
                        return {
                            'send': True,
                            'reason': 'ALL components successful with enhanced monetary features (Pi Cycle failed)',
                            'details': f'Monetary data with True Inflation ({monetary_data["true_inflation_rate"]:.1f}%) available, Pi Cycle status: {pi_cycle_status}'
                        }
                else:
                    if pi_cycle_success:
                        return {
                            'send': True,
                            'reason': 'ALL components successful with basic monetary data + Pi Cycle',
                            'details': f'Basic monetary data available, Pi Cycle working ({pi_cycle_status}), but enhanced features (True Inflation) not calculated'
                        }
                    else:
                        return {
                            'send': True,
                            'reason': 'ALL components successful with basic monetary data',
                            'details': f'Monetary data available but enhanced features (True Inflation) not calculated, Pi Cycle status: {pi_cycle_status}'
                        }
            else:
                if pi_cycle_success:
                    return {
                        'send': True,
                        'reason': 'Core components successful + Pi Cycle (proceeding without monetary data)',
                        'details': f'BTC + MSTR + Bitcoin Laws + Pi Cycle ({pi_cycle_status}) working. Monetary error: {monetary_data.get("error", "Unknown") if monetary_data else "Not attempted"}'
                    }
                else:
                    return {
                        'send': True,
                        'reason': 'Core components successful (BTC + MSTR + Bitcoin Laws) - proceeding without monetary/Pi Cycle data',
                        'details': f'Monetary error: {monetary_data.get("error", "Unknown") if monetary_data else "Not attempted"}. Pi Cycle status: {pi_cycle_status}'
                    }
        else:
            # Determine what failed
            failed_components = []

            if not btc_success:
                failed_components.append("BTC collection failed")
            elif not btc_data_quality['is_valid']:
                failed_components.append(f"BTC data quality issues: {'; '.join(btc_data_quality['issues'])}")

            if not mstr_success:
                failed_components.append("MSTR collection failed")
            elif not mstr_data_quality['is_valid']:
                failed_components.append(f"MSTR data quality issues: {'; '.join(mstr_data_quality['issues'])}")

            if not screenshot_success:
                failed_components.append("Bitcoin Laws screenshot failed/empty")

            return {
                'send': False,
                'reason': 'Core components failed - cannot send report',
                'details': f'Failed components: {"; ".join(failed_components)}. Pi Cycle status: {pi_cycle_status}'
            }

    except Exception as e:
        logging.error(f'❌ Error in enhanced report evaluation: {str(e)}')
        return {
            'send': False,
            'reason': 'Error evaluating enhanced data quality for report sending',
            'details': str(e)
        }


def validate_btc_data_quality_enhanced(btc_data: Dict) -> Dict:
    """🎯 ENHANCED BTC data quality validation including Pi Cycle"""
    issues = []

    try:
        if 'error' in btc_data:
            issues.append(f"BTC has error: {btc_data['error']}")
            return {'is_valid': False, 'issues': issues}

        # Check price
        price = btc_data.get('price', 0)
        if not price or price <= 0:
            issues.append(f"Invalid price: {price}")
        elif price < 10000 or price > 1000000:  # Sanity check
            issues.append(f"Price outside reasonable range: ${price:,.2f}")

        # Check indicators
        indicators = btc_data.get('indicators', {})

        mvrv = indicators.get('mvrv', 0)
        if not mvrv or mvrv <= 0:
            issues.append(f"Invalid MVRV: {mvrv}")
        elif mvrv > 10:  # Sanity check
            issues.append(f"MVRV unusually high: {mvrv}")

        weekly_rsi = indicators.get('weekly_rsi', 0)
        if not weekly_rsi or weekly_rsi <= 0:
            issues.append(f"Invalid Weekly RSI: {weekly_rsi}")
        elif weekly_rsi > 100:  # Sanity check
            issues.append(f"Weekly RSI above 100: {weekly_rsi}")

        ema_200 = indicators.get('ema_200', 0)
        if not ema_200 or ema_200 <= 0:
            issues.append(f"Invalid EMA 200: {ema_200}")
        elif ema_200 < 1000 or ema_200 > 500000:  # Sanity check
            issues.append(f"EMA 200 outside reasonable range: ${ema_200:,.2f}")

        # 🎯 NEW: Check Pi Cycle data quality (but don't fail validation if missing)
        pi_cycle_data = btc_data.get('pi_cycle', {})
        if pi_cycle_data.get('success'):
            current_values = pi_cycle_data.get('current_values', {})
            ma_111 = current_values.get('ma_111', 0)
            ma_350_x2 = current_values.get('ma_350_x2', 0)
            gap_percentage = current_values.get('gap_percentage', None)
            
            if ma_111 <= 0:
                issues.append(f"Pi Cycle: Invalid 111-day MA: {ma_111}")
            if ma_350_x2 <= 0:
                issues.append(f"Pi Cycle: Invalid 350-day MA x2: {ma_350_x2}")
            if gap_percentage is None:
                issues.append("Pi Cycle: Missing gap percentage")
            elif abs(gap_percentage) > 100:
                issues.append(f"Pi Cycle: Gap percentage seems extreme: {gap_percentage:.1f}%")
                
            logging.info(f"🎯 Pi Cycle quality check passed: {current_values.get('gap_percentage', 0):.1f}% gap")
        else:
            # Pi Cycle failure is logged but doesn't fail overall validation
            logging.warning(f"⚠️ Pi Cycle data quality check: {pi_cycle_data.get('error', 'Not available')}")

        is_valid = len(issues) == 0
        return {'is_valid': is_valid, 'issues': issues}

    except Exception as e:
        return {'is_valid': False, 'issues': [f"Validation error: {str(e)}"]}


def validate_mstr_data_quality(mstr_data: Dict) -> Dict:
    """Enhanced MSTR data quality validation"""
    issues = []

    try:
        if not mstr_data.get('success'):
            issues.append(f"Collection failed: {mstr_data.get('error', 'Unknown error')}")
            return {'is_valid': False, 'issues': issues}

        # Check price
        price = mstr_data.get('price', 0)
        if not price or price <= 0:
            issues.append(f"Invalid price: {price}")
        elif price < 10 or price > 10000:  # Sanity check for MSTR
            issues.append(f"MSTR price outside reasonable range: ${price:.2f}")

        # Check indicators
        indicators = mstr_data.get('indicators', {})

        model_price = indicators.get('model_price', 0)
        if not model_price or model_price <= 0:
            issues.append(f"Invalid model price: {model_price}")
        elif not (1 < model_price < 10000):
            issues.append(f"Model price outside reasonable range: ${model_price:.2f}")

        deviation_pct = indicators.get('deviation_pct', None)
        if deviation_pct is None:
            issues.append("Missing deviation percentage")
        elif abs(deviation_pct) > 200:  # Sanity check
            issues.append(f"Deviation percentage seems extreme: {deviation_pct:.1f}%")

        # IV validation - enhanced
        iv = indicators.get('iv', 0)
        if iv == 0:
            issues.append("Missing main IV (Implied Volatility) data")
        elif iv < 10 or iv > 500:  # Sanity check for IV
            issues.append(f"IV outside reasonable range: {iv:.1f}%")

        # 🎯 NEW: Check for options strategy analysis
        analysis = mstr_data.get('analysis', {})
        if analysis and 'options_strategy' in analysis:
            strategy = analysis['options_strategy']
            if not strategy.get('primary_strategy'):
                issues.append("Options strategy analysis incomplete")

        is_valid = len(issues) == 0
        return {'is_valid': is_valid, 'issues': issues}

    except Exception as e:
        return {'is_valid': False, 'issues': [f"Validation error: {str(e)}"]}


def process_asset_data_enhanced(collected_data: Dict) -> Dict:
    """🎯 ENHANCED asset data processing with Pi Cycle preservation"""
    processed = {
        'timestamp': datetime.utcnow().isoformat(),
        'assets': {},
        'summary': {
            'total_assets': len(collected_data),
            'successful_collections': 0,
            'failed_collections': 0,
            'enhanced_features_available': False,  # Track if enhanced features are working
            'pi_cycle_available': False  # 🎯 NEW: Track Pi Cycle availability
        }
    }

    for asset, data in collected_data.items():
        if data.get('success', False):
            processed['summary']['successful_collections'] += 1

            if asset == 'BTC':
                # 🎯 ENHANCED: Preserve Pi Cycle data with debug logging
                pi_cycle_data = data.get('pi_cycle', {})
                
                processed['assets'][asset] = {
                    'type': data.get('type', 'crypto'),
                    'price': data.get('price', 0),
                    'indicators': data.get('indicators', {}),
                    'metadata': data.get('metadata', {}),
                    'last_updated': data.get('timestamp'),
                    'pi_cycle': pi_cycle_data  # 🎯 CRITICAL: Preserve Pi Cycle data
                }
                
                # 🎯 DEBUG: Log Pi Cycle data preservation
                if pi_cycle_data.get('success'):
                    proximity_level = pi_cycle_data.get('signal_status', {}).get('proximity_level', 'UNKNOWN')
                    gap_percentage = pi_cycle_data.get('current_values', {}).get('gap_percentage', 0)
                    logging.info(f"🎯 Pi Cycle data preserved in processed_data: {proximity_level} ({gap_percentage:.1f}% gap)")
                    processed['summary']['pi_cycle_available'] = True
                else:
                    logging.warning(f"⚠️ Pi Cycle data not preserved: {pi_cycle_data.get('error', 'No data')}")
                    
            elif asset == 'MSTR':
                analysis = data.get('analysis', {})
                # 🎯 ENHANCED: Track if options strategy is available
                has_options_strategy = bool(analysis.get('options_strategy'))
                if has_options_strategy:
                    processed['summary']['enhanced_features_available'] = True
                
                processed['assets'][asset] = {
                    'type': data.get('type', 'stock'),
                    'price': data.get('price', 0),
                    'indicators': data.get('indicators', {}),
                    'analysis': analysis,  # Include enhanced MSTR analysis with options strategy
                    'metadata': data.get('metadata', {}),
                    'last_updated': data.get('timestamp'),
                    'attempts_made': data.get('attempts_made', 1),
                    'has_options_strategy': has_options_strategy
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
                'attempts_made': data.get('attempts_made', 1),
                'pi_cycle': data.get('pi_cycle', {'success': False, 'error': 'Asset collection failed'}) if asset == 'BTC' else None  # 🎯 Preserve failed Pi Cycle
            }

    # 🎯 DEBUG: Final summary of processed data
    logging.info(f"📊 Processed data summary: {processed['summary']['successful_collections']}/{processed['summary']['total_assets']} assets successful")
    logging.info(f"🎯 Enhanced features available: {processed['summary']['enhanced_features_available']}")
    logging.info(f"🥧 Pi Cycle available: {processed['summary']['pi_cycle_available']}")

    return processed


def generate_alerts(data: Dict, storage: DataStorage) -> List[Dict]:
    """Enhanced alert generation with monetary features + Pi Cycle"""
    alerts = []

    # 🎯 ENHANCED: Check for monetary data alerts
    monetary_data = data.get('monetary', {})
    if monetary_data.get('success'):
        true_inflation = monetary_data.get('true_inflation_rate')
        if true_inflation and true_inflation > 8.0:  # High inflation alert
            alerts.append({
                'type': 'high_monetary_inflation',
                'asset': 'MONETARY',
                'message': f"True monetary inflation rate is high at {true_inflation:.1f}% (20Y M2 CAGR)",
                'severity': 'medium'
            })

    # Asset-specific alerts
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
            alerts.extend(generate_btc_alerts_enhanced(asset_data, storage))
        elif asset == 'MSTR':
            alerts.extend(generate_mstr_alerts(asset_data, storage))

    return alerts


def generate_btc_alerts_enhanced(btc_data: Dict, storage: DataStorage) -> List[Dict]:
    """🎯 ENHANCED Bitcoin-specific alerts including Pi Cycle"""
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

    # 🎯 NEW: Pi Cycle alerts
    pi_cycle_data = btc_data.get('pi_cycle', {})
    if pi_cycle_data.get('success'):
        signal_status = pi_cycle_data.get('signal_status', {})
        proximity_level = signal_status.get('proximity_level', 'UNKNOWN')
        gap_percentage = pi_cycle_data.get('current_values', {}).get('gap_percentage', 0)
        
        if proximity_level == 'ACTIVE':
            alerts.append({
                'type': 'pi_cycle_active',
                'asset': 'BTC',
                'message': f"🚨 PI CYCLE TOP SIGNAL ACTIVE - Cycle top likely imminent!",
                'severity': 'critical'
            })
        elif proximity_level == 'IMMINENT':
            alerts.append({
                'type': 'pi_cycle_imminent',
                'asset': 'BTC',
                'message': f"⚠️ Pi Cycle signal imminent - {gap_percentage:.1f}% gap remaining",
                'severity': 'high'
            })
        elif proximity_level == 'VERY_CLOSE':
            alerts.append({
                'type': 'pi_cycle_close',
                'asset': 'BTC',
                'message': f"📢 Pi Cycle signal very close - {gap_percentage:.1f}% gap remaining",
                'severity': 'medium'
            })

    return alerts


def generate_mstr_alerts(mstr_data: Dict, storage: DataStorage) -> List[Dict]:
    """Enhanced MSTR-specific alerts with options strategy insights"""
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

    # 🎯 ENHANCED: Options strategy alerts
    options_strategy = analysis.get('options_strategy', {})
    if options_strategy:
        strategy = options_strategy.get('primary_strategy', '')
        confidence = options_strategy.get('confidence', 'medium')
        
        if strategy in ['long_calls', 'moderate_bullish'] and confidence == 'high':
            alerts.append({
                'type': 'mstr_bullish_options',
                'asset': 'MSTR',
                'message': f"High confidence bullish options signal: {options_strategy.get('message', '')}",
                'severity': 'medium'
            })
        elif strategy in ['long_puts', 'moderate_bearish'] and confidence == 'high':
            alerts.append({
                'type': 'mstr_bearish_options',
                'asset': 'MSTR',
                'message': f"High confidence bearish options signal: {options_strategy.get('message', '')}",
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
