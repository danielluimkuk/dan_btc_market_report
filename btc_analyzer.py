"""
BTC Analyzer Module
Handles Bitcoin buy/sell signal analysis and state management
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple
from data_storage import DataStorage


class BTCAnalyzer:
    """
    Analyzes Bitcoin market signals and manages signal state persistence
    """

    def __init__(self, storage: DataStorage = None):
        self.storage = storage or DataStorage()

    def analyze_btc_signals(self, btc_data: Dict) -> Dict:
        """
        Main method to analyze Bitcoin signals

        Args:
            btc_data: Dictionary containing BTC price and indicators

        Returns:
            Dictionary with complete signal analysis
        """
        try:
            # Extract BTC metrics
            price = btc_data.get('price', 0)
            indicators = btc_data.get('indicators', {})
            ema_200 = indicators.get('ema_200', 0)
            weekly_rsi = indicators.get('weekly_rsi', 0)
            mvrv = indicators.get('mvrv', 0)

            # Determine market status
            is_bull_market = price >= ema_200
            market_status = "bull" if is_bull_market else "bear"

            # Calculate current signal conditions
            signal_conditions = self._calculate_signal_conditions(weekly_rsi, mvrv, is_bull_market)

            # Get and update signal state
            current_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            signal_state = self._get_signal_state()
            updated_state = self._update_signal_state(
                signal_state,
                signal_conditions,
                current_date
            )

            # Save updated state
            self._save_signal_state(updated_state)

            # Determine overall signal status
            signal_status = self._determine_signal_status(updated_state, signal_conditions)

            return {
                'market_status': market_status,
                'is_bull_market': is_bull_market,
                'price': price,
                'ema_200': ema_200,
                'price_vs_ema_pct': ((price - ema_200) / ema_200 * 100) if ema_200 > 0 else 0,
                'indicators': {
                    'mvrv': mvrv,
                    'weekly_rsi': weekly_rsi
                },
                'signal_conditions': signal_conditions,
                'signal_state': updated_state,
                'signal_status': signal_status,
                'analysis_timestamp': datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logging.error(f"Error analyzing BTC signals: {str(e)}")
            return {
                'error': str(e),
                'analysis_timestamp': datetime.now(timezone.utc).isoformat()
            }

    def _calculate_signal_conditions(self, weekly_rsi: float, mvrv: float, is_bull_market: bool) -> Dict:
        """Calculate whether signal conditions are met"""

        if is_bull_market:
            # Bull market: sell signal conditions
            mvrv_condition = mvrv > 3.0
            rsi_condition = weekly_rsi > 70
            signal_type = "SELL"

            mvrv_status = {
                'value': mvrv,
                'condition_met': mvrv_condition,
                'threshold': 3.0,
                'operator': '>',
                'description': 'Need >3.0 for sell signal' if not mvrv_condition else 'Sell signal condition met'
            }

            rsi_status = {
                'value': weekly_rsi,
                'condition_met': rsi_condition,
                'threshold': 70,
                'operator': '>',
                'description': 'Need >70 for sell signal' if not rsi_condition else 'Sell signal condition met'
            }
        else:
            # Bear market: buy signal conditions
            mvrv_condition = mvrv < 1.0
            rsi_condition = weekly_rsi < 30
            signal_type = "BUY"

            mvrv_status = {
                'value': mvrv,
                'condition_met': mvrv_condition,
                'threshold': 1.0,
                'operator': '<',
                'description': 'Need <1.0 for buy signal' if not mvrv_condition else 'Buy signal condition met'
            }

            rsi_status = {
                'value': weekly_rsi,
                'condition_met': rsi_condition,
                'threshold': 30,
                'operator': '<',
                'description': 'Need <30 for buy signal' if not rsi_condition else 'Buy signal condition met'
            }

        both_conditions_met = mvrv_condition and rsi_condition

        return {
            'signal_type': signal_type,
            'both_conditions_met': both_conditions_met,
            'mvrv': mvrv_status,
            'rsi': rsi_status,
            'market_type': 'bull' if is_bull_market else 'bear'
        }

    def _get_signal_state(self) -> Dict:
        """Get current signal state from storage"""
        try:
            if not self.storage.table_service:
                return self._get_default_signal_state()

            # Query for signal state
            entities = self.storage.table_service.query_entities(
                'systemhealth',
                filter="PartitionKey eq 'SIGNAL_STATE' and RowKey eq 'CURRENT'"
            )

            for entity in entities:
                return {
                    'active': getattr(entity, 'active', False),
                    'signal_type': getattr(entity, 'signal_type', ''),
                    'start_date': getattr(entity, 'start_date', ''),
                    'end_date': getattr(entity, 'end_date', ''),
                    'conditions_failing_since': getattr(entity, 'conditions_failing_since', ''),
                    'last_updated': getattr(entity, 'last_updated', ''),
                    'days_active': self._calculate_days_active(
                        getattr(entity, 'start_date', ''),
                        getattr(entity, 'end_date', '')
                    )
                }

            return self._get_default_signal_state()

        except Exception as e:
            logging.error(f"Error getting signal state: {str(e)}")
            return self._get_default_signal_state()

    def _get_default_signal_state(self) -> Dict:
        """Get default signal state"""
        return {
            'active': False,
            'signal_type': '',
            'start_date': '',
            'end_date': '',
            'conditions_failing_since': '',
            'last_updated': '',
            'days_active': 0
        }

    def _update_signal_state(self, current_state: Dict, signal_conditions: Dict, current_date: str) -> Dict:
        """Update signal state based on current conditions"""

        updated_state = current_state.copy()
        updated_state['last_updated'] = current_date

        both_conditions_met = signal_conditions['both_conditions_met']
        signal_type = signal_conditions['signal_type']

        if both_conditions_met:
            # Both conditions met
            if not updated_state['active']:
                # Signal is turning ON
                updated_state['active'] = True
                updated_state['signal_type'] = signal_type
                updated_state['start_date'] = current_date
                updated_state['end_date'] = ''
                updated_state['conditions_failing_since'] = ''
                logging.info(f"🚨 {signal_type} signal activated on {current_date}")
            else:
                # Signal remains active, clear any failing conditions
                if updated_state['conditions_failing_since']:
                    logging.info(f"✅ {signal_type} signal conditions restored")
                updated_state['conditions_failing_since'] = ''
        else:
            # At least one condition not met
            if updated_state['active']:
                # Signal was active, now conditions are failing
                if not updated_state['conditions_failing_since']:
                    # First day of failing conditions
                    updated_state['conditions_failing_since'] = current_date
                    logging.info(
                        f"⚠️ {updated_state['signal_type']} signal weakening - conditions failing since {current_date}")
                else:
                    # Check if failing for more than 30 days
                    failing_since = datetime.strptime(updated_state['conditions_failing_since'], '%Y-%m-%d')
                    current_dt = datetime.strptime(current_date, '%Y-%m-%d')
                    days_failing = (current_dt - failing_since).days

                    if days_failing > 30:
                        # Turn signal OFF
                        updated_state['active'] = False
                        updated_state['end_date'] = current_date
                        updated_state['conditions_failing_since'] = ''
                        logging.info(
                            f"🔴 {updated_state['signal_type']} signal deactivated after {days_failing} days of failing conditions")

        # Update days active
        updated_state['days_active'] = self._calculate_days_active(
            updated_state['start_date'],
            updated_state['end_date']
        )

        return updated_state

    def _calculate_days_active(self, start_date: str, end_date: str) -> int:
        """Calculate how many days a signal has been active"""
        if not start_date:
            return 0

        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')

            if end_date:
                # Signal ended
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                return (end_dt - start_dt).days
            else:
                # Signal still active
                current_dt = datetime.now(timezone.utc)
                return (current_dt - start_dt.replace(tzinfo=timezone.utc)).days

        except Exception as e:
            logging.error(f"Error calculating days active: {str(e)}")
            return 0

    def _save_signal_state(self, signal_state: Dict) -> None:
        """Save signal state to storage"""
        try:
            if not self.storage.table_service:
                logging.warning("No storage service available - signal state not persisted")
                return

            from azure.cosmosdb.table.models import Entity

            entity = Entity()
            entity.PartitionKey = 'SIGNAL_STATE'
            entity.RowKey = 'CURRENT'
            entity.active = signal_state['active']
            entity.signal_type = signal_state['signal_type']
            entity.start_date = signal_state['start_date']
            entity.end_date = signal_state['end_date']
            entity.conditions_failing_since = signal_state['conditions_failing_since']
            entity.last_updated = signal_state['last_updated']
            entity.days_active = signal_state['days_active']

            self.storage.table_service.insert_or_replace_entity('systemhealth', entity)

        except Exception as e:
            logging.error(f"Error saving signal state: {str(e)}")

    def _determine_signal_status(self, signal_state: Dict, signal_conditions: Dict) -> Dict:
        """Determine the overall signal status for display"""

        if signal_state['active']:
            if signal_conditions['both_conditions_met']:
                # Signal active and conditions still met
                status = 'active'
                message = f"{signal_state['signal_type']} SIGNAL ACTIVE"
                emoji = "🔴" if signal_state['signal_type'] == 'SELL' else "🟢"

                # Calculate timing prediction
                if signal_state['signal_type'] == 'SELL':
                    prediction = "Top is likely to be reached within 1-3 months"
                else:
                    prediction = "Bottom is likely to be in 4-6 months"

            else:
                # Signal active but conditions weakening
                status = 'weakening'
                message = f"{signal_state['signal_type']} SIGNAL WEAKENING"
                emoji = "🟡"
                prediction = "One parameter no longer met - signal may turn off if continues >30 days"

        elif signal_state['end_date']:
            # Signal recently turned off
            status = 'recently_off'
            message = f"{signal_state['signal_type']} SIGNAL OFF"
            emoji = "🟡"
            prediction = f"Was active: {signal_state['start_date']} to {signal_state['end_date']}"

        else:
            # No signal
            status = 'none'
            message = ""
            emoji = ""
            prediction = ""

        return {
            'status': status,
            'message': message,
            'emoji': emoji,
            'prediction': prediction,
            'days_active': signal_state.get('days_active', 0),
            'start_date': signal_state.get('start_date', ''),
            'end_date': signal_state.get('end_date', '')
        }

    def get_signal_history(self, days: int = 90) -> Dict:
        """Get historical signal data for analysis"""
        try:
            if not self.storage.table_service:
                return {'error': 'Storage not available'}

            # This could be expanded to track signal history over time
            # For now, return current state
            current_state = self._get_signal_state()

            return {
                'current_signal': current_state,
                'period_days': days,
                'history_available': bool(current_state['start_date'])
            }

        except Exception as e:
            logging.error(f"Error getting signal history: {str(e)}")
            return {'error': str(e)}

    def reset_signal_state(self) -> bool:
        """Reset signal state (for testing/maintenance)"""
        try:
            default_state = self._get_default_signal_state()
            default_state['last_updated'] = datetime.now(timezone.utc).strftime('%Y-%m-%d')

            self._save_signal_state(default_state)
            logging.info("Signal state reset to default")
            return True

        except Exception as e:
            logging.error(f"Error resetting signal state: {str(e)}")
            return False