#!/usr/bin/env python3
"""
P/BYD Calculator - Price-to-Bitcoin-Yield-Delta Calculation
Pure math functions for calculating annualized Bitcoin yield and P/BYD ratio
"""

import math
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Tuple


class PBYDCalculator:
    """Pure math functions for P/BYD calculation"""

    @staticmethod
    def find_historical_btc_holdings(btc_data: Dict[str, Dict[str, int]],
                                     reference_date: datetime) -> Dict[str, Any]:
        """
        Find BTC holdings at least 365 days ago from reference date

        Args:
            btc_data: Dict with date keys and BTC holdings
            reference_date: Date to calculate 365 days back from

        Returns:
            Dict with 'success', 'btc_amount', 'date', 'days_ago', 'reason'
        """
        try:
            if not btc_data:
                return {
                    'success': False,
                    'btc_amount': None,
                    'date': None,
                    'days_ago': None,
                    'reason': 'No BTC holdings data available'
                }

            # Calculate target date (365 days ago)
            target_date = reference_date - timedelta(days=365)

            # Find dates that are >= 365 days ago (i.e., <= target_date)
            valid_dates = []
            for date_str in btc_data.keys():
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    if date_obj <= target_date:
                        days_ago = (reference_date - date_obj).days
                        valid_dates.append((date_str, date_obj, days_ago))
                except ValueError:
                    logging.warning(f"Invalid date format in BTC data: {date_str}")
                    continue

            if not valid_dates:
                return {
                    'success': False,
                    'btc_amount': None,
                    'date': None,
                    'days_ago': None,
                    'reason': 'No historical data ≥365 days ago'
                }

            # Sort by date descending to get the most recent date that's still ≥365 days ago
            valid_dates.sort(key=lambda x: x[1], reverse=True)

            best_date_str, best_date_obj, actual_days_ago = valid_dates[0]
            btc_amount = btc_data[best_date_str].get('btc')

            if btc_amount is None or btc_amount <= 0:
                return {
                    'success': False,
                    'btc_amount': None,
                    'date': best_date_str,
                    'days_ago': actual_days_ago,
                    'reason': f'Invalid BTC amount for date {best_date_str}'
                }

            return {
                'success': True,
                'btc_amount': btc_amount,
                'date': best_date_str,
                'days_ago': actual_days_ago,
                'reason': None
            }

        except Exception as e:
            return {
                'success': False,
                'btc_amount': None,
                'date': None,
                'days_ago': None,
                'reason': f'Error finding historical data: {str(e)}'
            }

    @staticmethod
    def calculate_annualized_yield(current_holdings: float,
                                   historical_holdings: float,
                                   actual_days: int) -> Dict[str, Any]:
        """
        Calculate annualized Bitcoin yield

        Formula: ((current_holdings/historical_holdings)^(365/actual_days)) - 1

        Args:
            current_holdings: Current BTC holdings
            historical_holdings: Historical BTC holdings
            actual_days: Actual days between measurements

        Returns:
            Dict with 'success', 'yield', 'reason'
        """
        try:
            if current_holdings <= 0:
                return {
                    'success': False,
                    'yield': None,
                    'reason': 'Invalid current BTC holdings (≤0)'
                }

            if historical_holdings <= 0:
                return {
                    'success': False,
                    'yield': None,
                    'reason': 'Invalid historical BTC holdings (≤0)'
                }

            if actual_days <= 0:
                return {
                    'success': False,
                    'yield': None,
                    'reason': 'Invalid time period (≤0 days)'
                }

            # Calculate growth ratio
            growth_ratio = current_holdings / historical_holdings

            if growth_ratio <= 0:
                return {
                    'success': False,
                    'yield': None,
                    'reason': 'Invalid growth ratio (≤0)'
                }

            # Annualize the ratio
            annualization_factor = 365.0 / actual_days

            try:
                annualized_ratio = math.pow(growth_ratio, annualization_factor)
                annualized_yield = annualized_ratio - 1.0

                return {
                    'success': True,
                    'yield': annualized_yield,
                    'reason': None
                }

            except (OverflowError, ValueError) as e:
                return {
                    'success': False,
                    'yield': None,
                    'reason': f'Math error in yield calculation: {str(e)}'
                }

        except Exception as e:
            return {
                'success': False,
                'yield': None,
                'reason': f'Error calculating yield: {str(e)}'
            }

    @staticmethod
    def calculate_pbyd_ratio(mnav: float, annualized_yield: float) -> Dict[str, Any]:
        """
        Calculate P/BYD ratio

        Formula: log(mNAV) / log(1 + annualized_yield)

        Args:
            mnav: Market NAV ratio
            annualized_yield: Annualized Bitcoin yield

        Returns:
            Dict with 'success', 'pbyd', 'reason'
        """
        try:
            if mnav <= 0:
                return {
                    'success': False,
                    'pbyd': None,
                    'reason': 'Invalid mNAV value (≤0)'
                }

            # Check if 1 + yield is positive (needed for log)
            yield_plus_one = 1.0 + annualized_yield

            if yield_plus_one <= 0:
                return {
                    'success': False,
                    'pbyd': None,
                    'reason': f'Invalid yield for log calculation (1+yield={yield_plus_one:.6f})'
                }

            try:
                log_mnav = math.log(mnav)
                log_yield = math.log(yield_plus_one)

                if log_yield == 0:
                    return {
                        'success': False,
                        'pbyd': None,
                        'reason': 'Division by zero (log(1+yield)=0)'
                    }

                pbyd_ratio = log_mnav / log_yield

                return {
                    'success': True,
                    'pbyd': pbyd_ratio,
                    'reason': None
                }

            except (ValueError, OverflowError) as e:
                return {
                    'success': False,
                    'pbyd': None,
                    'reason': f'Math error in log calculation: {str(e)}'
                }

        except Exception as e:
            return {
                'success': False,
                'pbyd': None,
                'reason': f'Error calculating P/BYD: {str(e)}'
            }

    @staticmethod
    def calculate_full_pbyd(current_btc_holdings: float,
                            mnav: float,
                            btc_data: Dict[str, Dict[str, int]],
                            reference_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Complete P/BYD calculation pipeline

        Args:
            current_btc_holdings: Current BTC holdings
            mnav: Current mNAV ratio
            btc_data: Historical BTC holdings data
            reference_date: Date to calculate from (default: today)

        Returns:
            Dict with 'value', 'reason', 'debug_info'
        """
        if reference_date is None:
            reference_date = datetime.now()

        debug_info = {
            'reference_date': reference_date.strftime('%Y-%m-%d'),
            'current_btc_holdings': current_btc_holdings,
            'mnav': mnav
        }

        try:
            # Step 1: Validate inputs
            if current_btc_holdings <= 0:
                return {
                    'value': 'N/A',
                    'reason': 'Missing current BTC holdings',
                    'debug_info': debug_info
                }

            if mnav <= 0:
                return {
                    'value': 'N/A',
                    'reason': 'Missing mNAV data',
                    'debug_info': debug_info
                }

            # Step 2: Find historical BTC holdings
            historical_result = PBYDCalculator.find_historical_btc_holdings(btc_data, reference_date)
            debug_info['historical_lookup'] = historical_result

            if not historical_result['success']:
                return {
                    'value': 'N/A',
                    'reason': historical_result['reason'],
                    'debug_info': debug_info
                }

            # Step 3: Calculate annualized yield
            yield_result = PBYDCalculator.calculate_annualized_yield(
                current_btc_holdings,
                historical_result['btc_amount'],
                historical_result['days_ago']
            )
            debug_info['yield_calculation'] = yield_result

            if not yield_result['success']:
                return {
                    'value': 'N/A',
                    'reason': yield_result['reason'],
                    'debug_info': debug_info
                }

            # Step 4: Calculate P/BYD ratio
            pbyd_result = PBYDCalculator.calculate_pbyd_ratio(mnav, yield_result['yield'])
            debug_info['pbyd_calculation'] = pbyd_result

            if not pbyd_result['success']:
                return {
                    'value': 'N/A',
                    'reason': pbyd_result['reason'],
                    'debug_info': debug_info
                }

            # Step 5: Format result
            pbyd_value = pbyd_result['pbyd']
            formatted_value = f"{pbyd_value:.2f}"

            debug_info['final_value'] = formatted_value

            return {
                'value': formatted_value,
                'reason': None,
                'debug_info': debug_info
            }

        except Exception as e:
            return {
                'value': 'N/A',
                'reason': f'Unexpected error: {str(e)}',
                'debug_info': debug_info
            }


# Test function
def test_pbyd_calculator():
    """Test the P/BYD calculator with sample data"""
    print("🧪 Testing P/BYD Calculator")
    print("=" * 50)

    # Sample data
    btc_data = {
        "2024-07-21": {"btc": 226331},
        "2024-06-20": {"btc": 220000},
        "2023-07-21": {"btc": 152333}
    }

    current_holdings = 607770
    mnav = 2.5
    reference_date = datetime(2025, 7, 21)

    result = PBYDCalculator.calculate_full_pbyd(
        current_holdings, mnav, btc_data, reference_date
    )

    print(f"Result: {result['value']}")
    if result['reason']:
        print(f"Reason: {result['reason']}")

    print("\nDebug Info:")
    for key, value in result['debug_info'].items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    test_pbyd_calculator()
