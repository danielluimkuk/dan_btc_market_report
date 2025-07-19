# =============================================================================
# pi_cycle_indicator.py - UPDATED VERSION with Improved Convergence Logic
# =============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import logging
from typing import Dict, Optional, List, Any
import requests
import json


class PiCycleTopIndicator:
    """
    🥧 UPDATED Pi Cycle Top Indicator for Bitcoin Market Monitor

    ✅ FINAL IMPROVEMENTS:
    - Relative gap closure calculation instead of absolute dollars
    - REFINED thresholds based on realistic Bitcoin $10k-$20k monthly progression:
      * Rapidly Converging: < -0.8% daily gap closure
      * Converging: -0.4% to -0.8% daily gap closure
      * Stable: ±0.2% daily gap change
      * Diverging: > +0.2% daily gap expansion
    - UPDATED gap size alerts for realistic timelines:
      * IMMINENT: ≤ 1.0% (days to weeks)
      * VERY_CLOSE: ≤ 4.0% (weeks to months)
      * APPROACHING: ≤ 10.0% (2-4 months)
      * MODERATE: ≤ 20.0% (4-8 months)
      * FAR: > 20.0% (>8 months)
    - Proper JSON serialization safety
    - Robust error handling
    """

    def __init__(self, polygon_api_key: str = None):
        self.polygon_api_key = polygon_api_key
        self.ma_111_period = 111
        self.ma_350_period = 350
        self.multiplier = 2

    def get_pi_cycle_analysis(self, current_btc_price: float = None) -> Dict:
        """
        Main method to get complete Pi Cycle Top analysis
        """
        try:
            logging.info("🥧 Collecting Pi Cycle Top indicator data...")

            # Get historical price data
            price_data = self._get_historical_btc_prices()

            if not price_data or len(price_data) < self.ma_350_period:
                logging.warning(f"⚠️ Insufficient data for Pi Cycle: {len(price_data) if price_data else 0} days")
                return self._get_fallback_analysis(current_btc_price)

            # Calculate analysis
            analysis = self._calculate_pi_cycle_analysis(price_data, current_btc_price)

            # CRITICAL: Convert all numpy types to Python types
            safe_analysis = self._ensure_json_serializable(analysis)

            logging.info(f"✅ Pi Cycle analysis complete: {safe_analysis['signal_status']['proximity_level']}")
            return safe_analysis

        except Exception as e:
            logging.error(f"❌ Error in Pi Cycle analysis: {str(e)}")
            return self._get_fallback_analysis(current_btc_price, error=str(e))

    def _get_historical_btc_prices(self) -> List[float]:
        """Get historical BTC prices for Pi Cycle calculation"""
        try:
            if not self.polygon_api_key:
                logging.warning("No Polygon API key - using fallback")
                return []

            end_date = datetime.now()
            start_date = end_date - timedelta(days=420)

            url = f"https://api.polygon.io/v2/aggs/ticker/X:BTCUSD/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"

            response = requests.get(url, params={'apikey': self.polygon_api_key}, timeout=15)
            response.raise_for_status()

            data = response.json()

            if data.get('status') in ['OK', 'DELAYED'] and 'results' in data:
                prices = [float(bar['c']) for bar in data['results']]  # Ensure Python float
                logging.info(f"📊 Retrieved {len(prices)} days of BTC price data")
                return prices
            else:
                logging.warning("Polygon API returned no results")
                return []

        except Exception as e:
            logging.error(f"Error fetching prices: {str(e)}")
            return []

    def _calculate_pi_cycle_analysis(self, price_data: List[float], current_btc_price: float = None) -> Dict:
        """
        🎯 UPDATED: Complete Pi Cycle calculation implementation with improved convergence logic
        """
        try:
            # Convert to pandas DataFrame
            df = pd.DataFrame({'price': price_data})

            # Calculate moving averages
            df['ma_111'] = df['price'].rolling(window=self.ma_111_period).mean()
            df['ma_350'] = df['price'].rolling(window=self.ma_350_period).mean()
            df['ma_350_x2'] = df['ma_350'] * self.multiplier

            # Get current values (latest available)
            current_111dma = float(df['ma_111'].iloc[-1])
            current_350dma_x2 = float(df['ma_350_x2'].iloc[-1])
            current_price = float(current_btc_price or df['price'].iloc[-1])

            # Calculate gap
            gap_absolute = float(current_350dma_x2 - current_111dma)
            gap_percentage = float((gap_absolute / current_350dma_x2) * 100) if current_350dma_x2 > 0 else 0.0

            # Determine signal status
            signal_status = self._determine_signal_status(
                current_111dma, current_350dma_x2, gap_absolute, gap_percentage
            )

            # Analyze trend with IMPROVED convergence logic
            trend_analysis = self._analyze_convergence_trend(df)

            # Build result with Python native types only
            result = {
                'success': True,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'current_values': {
                    'btc_price': round(current_price, 2),
                    'ma_111': round(current_111dma, 2),
                    'ma_350_x2': round(current_350dma_x2, 2),
                    'gap_absolute': round(gap_absolute, 2),
                    'gap_percentage': round(gap_percentage, 2)
                },
                'signal_status': signal_status,
                'trend_analysis': trend_analysis,
                'pi_ratio': {
                    'calculated': round(self.ma_350_period / self.ma_111_period, 6),
                    'pi_actual': 3.141593,
                    'difference': round(abs((self.ma_350_period / self.ma_111_period) - 3.141593), 6)
                },
                'interpretation': self._generate_interpretation(signal_status, gap_percentage, trend_analysis),
                'source': 'polygon_historical_data'
            }

            return result

        except Exception as e:
            logging.error(f"Error calculating Pi Cycle: {str(e)}")
            raise

    def _determine_signal_status(self, ma_111: float, ma_350_x2: float,
                                 gap_absolute: float, gap_percentage: float) -> Dict:
        """Determine Pi Cycle signal status with UPDATED realistic thresholds"""
        is_crossed = ma_111 >= ma_350_x2

        if is_crossed:
            return {
                'status': 'SIGNAL_ACTIVE',
                'proximity_level': 'ACTIVE',
                'message': 'PI CYCLE TOP SIGNAL ACTIVE',
                'description': 'Bitcoin cycle top is likely imminent or occurring now',
                'color': '#dc3545',
                'urgency': 'CRITICAL'
            }

        # UPDATED: Determine proximity based on realistic gap percentages
        if gap_percentage <= 1.0:
            return {
                'status': 'SIGNAL_IMMINENT',
                'proximity_level': 'IMMINENT',
                'message': 'PI CYCLE TOP SIGNAL IMMINENT',
                'description': 'Signal could trigger within days to weeks - prepare for cycle top',
                'color': '#ff6b35',
                'urgency': 'VERY_HIGH'
            }
        elif gap_percentage <= 4.0:
            return {
                'status': 'VERY_CLOSE',
                'proximity_level': 'VERY_CLOSE',
                'message': 'PI CYCLE VERY CLOSE',
                'description': 'Signal likely within weeks to months - monitor closely',
                'color': '#ffc107',
                'urgency': 'HIGH'
            }
        elif gap_percentage <= 10.0:
            return {
                'status': 'APPROACHING',
                'proximity_level': 'APPROACHING',
                'message': 'PI CYCLE APPROACHING',
                'description': 'Signal possible within 2-4 months - early alert phase',
                'color': '#28a745',
                'urgency': 'MEDIUM'
            }
        elif gap_percentage <= 20.0:
            return {
                'status': 'MODERATE_DISTANCE',
                'proximity_level': 'MODERATE',
                'message': 'PI CYCLE MODERATE DISTANCE',
                'description': 'Signal in development - 4-8 months timeline',
                'color': '#17a2b8',
                'urgency': 'LOW'
            }
        else:
            return {
                'status': 'FAR_FROM_SIGNAL',
                'proximity_level': 'FAR',
                'message': 'PI CYCLE FAR FROM SIGNAL',
                'description': 'Moving averages distant - timeline >8 months',
                'color': '#6c757d',
                'urgency': 'NONE'
            }

    def _analyze_convergence_trend(self, df: pd.DataFrame) -> Dict:
        """
        🎯 UPDATED: Analyze convergence trend using RELATIVE gap closure

        Uses REFINED thresholds based on realistic Bitcoin $10k-$20k monthly progression:
        - rapidly_converging: < -0.8% daily gap closure
        - converging: -0.8% to -0.2% daily gap closure
        - stable: ±0.2% daily gap change
        - diverging: > +0.2% daily gap expansion
        """
        try:
            # Calculate recent gaps (ma_350_x2 - ma_111)
            recent_gaps = df['ma_350_x2'] - df['ma_111']

            if len(recent_gaps) < 30:
                return {
                    'trend': 'insufficient_data',
                    'trend_description': 'Insufficient data for trend analysis',
                    'daily_rate': 0.0,
                    'is_converging': False
                }

            recent_gaps_30d = recent_gaps.tail(30)

            # Calculate daily changes in gap
            daily_changes = recent_gaps_30d.diff().dropna()

            # Get current gap for relative calculation
            current_gap = recent_gaps.iloc[-1]

            if current_gap <= 0:
                # Signal already triggered or invalid data
                return {
                    'trend': 'signal_active_or_invalid',
                    'trend_description': 'Signal active or invalid gap data',
                    'daily_rate': 0.0,
                    'is_converging': True
                }

            # 🎯 UPDATED: Calculate RELATIVE gap closure rate
            relative_daily_changes = (daily_changes / current_gap) * 100
            avg_gap_closure_pct = float(relative_daily_changes.mean())

            # 🎯 UPDATED: Apply REFINED thresholds based on realistic Bitcoin progression
            if avg_gap_closure_pct < -0.8:
                trend = 'rapidly_converging'
                trend_description = 'Rapidly converging - signal acceleration'
            elif avg_gap_closure_pct < -0.2:
                trend = 'converging'
                trend_description = 'Steadily converging toward signal'
            elif abs(avg_gap_closure_pct) <= 0.2:
                trend = 'stable'
                trend_description = 'Stable - minimal change in gap'
            else:
                trend = 'diverging'
                trend_description = 'Diverging - signal moving away'

            return {
                'trend': trend,
                'trend_description': trend_description,
                'daily_rate': round(avg_gap_closure_pct, 3),
                'is_converging': bool(avg_gap_closure_pct < 0)
            }

        except Exception as e:
            logging.error(f"Error analyzing trend: {str(e)}")
            return {
                'trend': 'error',
                'trend_description': 'Unable to determine trend',
                'daily_rate': 0.0,
                'is_converging': False
            }

    def _generate_interpretation(self, signal_status: Dict, gap_percentage: float,
                                 trend_analysis: Dict) -> Dict:
        """Generate interpretation"""
        proximity_level = signal_status['proximity_level']

        interpretations = {
            'ACTIVE': {
                'summary': 'Bitcoin cycle top signal is ACTIVE',
                'action': 'Consider taking profits immediately',
                'timeframe': 'Peak likely within days',
                'confidence': 'Very High (95%+ historical accuracy)'
            },
            'IMMINENT': {
                'summary': 'Signal could trigger within days',
                'action': 'Prepare exit strategy and monitor hourly',
                'timeframe': 'Days to weeks',
                'confidence': 'High'
            },
            'VERY_CLOSE': {
                'summary': 'Moving averages very close to crossing',
                'action': 'Begin considering profit-taking strategy',
                'timeframe': 'Weeks to months',
                'confidence': 'High'
            },
            'APPROACHING': {
                'summary': 'Early warning phase - signal developing',
                'action': 'Monitor weekly and plan exit strategies',
                'timeframe': 'Months',
                'confidence': 'Medium'
            },
            'MODERATE': {
                'summary': 'Signal in early development',
                'action': 'Continue normal strategy with awareness',
                'timeframe': 'Several months',
                'confidence': 'Medium'
            },
            'FAR': {
                'summary': 'No immediate signal concern',
                'action': 'Continue accumulation/holding strategy',
                'timeframe': 'No immediate timeframe',
                'confidence': 'Low concern'
            }
        }

        return interpretations.get(proximity_level, interpretations['FAR'])

    def _get_fallback_analysis(self, current_btc_price: float = None, error: str = None) -> Dict:
        """Fallback analysis when data collection fails"""
        return {
            'success': False,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error': error or 'Unable to collect historical price data',
            'current_values': {
                'btc_price': float(current_btc_price or 0),
                'ma_111': 0.0,
                'ma_350_x2': 0.0,
                'gap_absolute': 0.0,
                'gap_percentage': 0.0
            },
            'signal_status': {
                'status': 'DATA_UNAVAILABLE',
                'proximity_level': 'UNKNOWN',
                'message': 'PI CYCLE DATA UNAVAILABLE',
                'description': 'Unable to calculate Pi Cycle indicator',
                'color': '#6c757d',
                'urgency': 'NONE'
            },
            'interpretation': {
                'summary': 'Pi Cycle analysis unavailable',
                'action': 'Rely on other technical indicators',
                'timeframe': 'N/A',
                'confidence': 'N/A'
            },
            'source': 'fallback'
        }

    def _ensure_json_serializable(self, data: Any) -> Any:
        """
        🎯 CRITICAL FIX: Ensure all data is JSON serializable
        """
        if isinstance(data, dict):
            return {key: self._ensure_json_serializable(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._ensure_json_serializable(item) for item in data]
        elif isinstance(data, tuple):
            return tuple(self._ensure_json_serializable(item) for item in data)
        elif isinstance(data, (np.integer, np.int64, np.int32)):
            return int(data)
        elif isinstance(data, (np.floating, np.float64, np.float32)):
            return float(data)
        elif isinstance(data, np.bool_):
            return bool(data)
        elif isinstance(data, np.ndarray):
            return data.tolist()
        elif isinstance(data, pd.Series):
            return data.tolist()
        elif isinstance(data, pd.DataFrame):
            return data.to_dict()
        elif pd.isna(data):
            return None
        else:
            return data


# Quick test to verify the updated logic
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    logging.basicConfig(level=logging.INFO)

    print("🧪 Testing UPDATED Pi Cycle Indicator with REFINED Convergence Logic")
    print("=" * 70)

    pi_cycle = PiCycleTopIndicator(polygon_api_key=os.getenv('POLYGON_API_KEY'))
    result = pi_cycle.get_pi_cycle_analysis(current_btc_price=108000)

    # Test JSON serialization
    try:
        json_str = json.dumps(result, indent=2)
        print("✅ JSON serialization successful!")

        if result.get('success'):
            values = result['current_values']
            status = result['signal_status']
            trend = result['trend_analysis']

            print(f"📊 Status: {status['proximity_level']}")
            print(f"💰 BTC: ${values['btc_price']:,.2f}")
            print(f"📈 Gap: {values['gap_percentage']:.1f}%")
            print(f"🎯 Trend: {trend['trend']} ({trend['daily_rate']:.3f}% daily)")
            print(f"📝 Description: {trend['trend_description']}")
        else:
            print(f"⚠️ Fallback mode: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")

    print(f"\n🎯 UPDATED CONVERGENCE THRESHOLDS:")
    print(f"   🚀 Rapidly Converging: < -0.8% daily gap closure")
    print(f"   📈 Converging: -0.4% to -0.8% daily gap closure")
    print(f"   ⚖️  Stable: ±0.2% daily gap change")
    print(f"   📉 Diverging: > +0.2% daily gap expansion")
    print(f"\n🎯 UPDATED GAP SIZE THRESHOLDS:")
    print(f"   🚨 IMMINENT: ≤ 1.0% gap (days to weeks)")
    print(f"   ⚠️  VERY_CLOSE: ≤ 4.0% gap (weeks to months)")
    print(f"   📢 APPROACHING: ≤ 10.0% gap (2-4 months)")
    print(f"   📊 MODERATE: ≤ 20.0% gap (4-8 months)")
    print(f"   📍 FAR: > 20.0% gap (>8 months)")
