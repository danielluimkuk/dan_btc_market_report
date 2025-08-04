#!/usr/bin/env python3
"""
Multi-Period P/BYD Calculator - 30-day, 90-day, and 365-day P/BYD ratios
Extends the existing PBYDCalculator for multiple time periods
"""

import math
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from pbyd_calculator import PBYDCalculator


class MultiPeriodPBYDCalculator:
    """Multi-period P/BYD calculation for 30, 90, and 365 days"""

    @staticmethod
    def calculate_multi_period_pbyd(current_btc_holdings: float,
                                    mnav: float,
                                    btc_data: Dict[str, Dict[str, int]],
                                    reference_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Calculate P/BYD for 30, 90, and 365 day periods

        Args:
            current_btc_holdings: Current BTC holdings
            mnav: Current mNAV ratio
            btc_data: Historical BTC holdings data
            reference_date: Date to calculate from (default: today)

        Returns:
            Dict with P/BYD values for each period and debug info
        """
        if reference_date is None:
            reference_date = datetime.now()

        results = {
            'success': True,
            'timestamp': reference_date.strftime('%Y-%m-%d'),
            'current_btc_holdings': current_btc_holdings,
            'mnav': mnav,
            'periods': {},
            'debug_info': {}
        }

        # Calculate for each period
        periods = [30, 90, 365]
        
        for period_days in periods:
            period_name = f"pbyd_{period_days}d"
            
            try:
                # Find historical data for this period
                historical_result = MultiPeriodPBYDCalculator._find_historical_btc_holdings_for_period(
                    btc_data, reference_date, period_days
                )
                
                if not historical_result['success']:
                    results['periods'][period_name] = {
                        'value': 'N/A',
                        'reason': historical_result['reason'],
                        'period_days': period_days
                    }
                    continue

                # Calculate annualized yield for this period
                yield_result = PBYDCalculator.calculate_annualized_yield(
                    current_btc_holdings,
                    historical_result['btc_amount'],
                    historical_result['days_ago']
                )

                if not yield_result['success']:
                    results['periods'][period_name] = {
                        'value': 'N/A',
                        'reason': yield_result['reason'],
                        'period_days': period_days
                    }
                    continue

                # Calculate P/BYD ratio for this period
                pbyd_result = PBYDCalculator.calculate_pbyd_ratio(mnav, yield_result['yield'])

                if pbyd_result['success']:
                    results['periods'][period_name] = {
                        'value': f"{pbyd_result['pbyd']:.2f}",
                        'reason': None,
                        'period_days': period_days,
                        'historical_date': historical_result['date'],
                        'actual_days': historical_result['days_ago'],
                        'annualized_yield': yield_result['yield']
                    }
                else:
                    results['periods'][period_name] = {
                        'value': 'N/A',
                        'reason': pbyd_result['reason'],
                        'period_days': period_days
                    }

            except Exception as e:
                results['periods'][period_name] = {
                    'value': 'N/A',
                    'reason': f'Calculation error: {str(e)}',
                    'period_days': period_days
                }

        # Check if all periods failed
        successful_periods = sum(1 for p in results['periods'].values() if p['value'] != 'N/A')
        if successful_periods == 0:
            results['success'] = False
            results['reason'] = 'All P/BYD period calculations failed'

        return results

    @staticmethod
    def _find_historical_btc_holdings_for_period(btc_data: Dict[str, Dict[str, int]],
                                                  reference_date: datetime,
                                                  target_period_days: int) -> Dict[str, Any]:
        """
        Find BTC holdings for a specific period (30, 90, or 365 days ago)
        
        Args:
            btc_data: Dict with date keys and BTC holdings
            reference_date: Date to calculate back from
            target_period_days: Number of days to look back (30, 90, 365)
            
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

            # Calculate target date
            target_date = reference_date - timedelta(days=target_period_days)
            
            # Find dates that are at least target_period_days ago
            valid_dates = []
            for date_str in btc_data.keys():
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    # We want dates that are >= target_period_days ago (i.e., <= target_date)
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
                    'reason': f'No historical data ≥{target_period_days} days ago'
                }

            # Sort by date descending to get the most recent date that's still >= target_period_days ago
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
    def format_pbyd_results(results: Dict[str, Any]) -> Dict[str, str]:
        """
        Format P/BYD results for display in MSTR indicators
        
        Args:
            results: Results from calculate_multi_period_pbyd()
            
        Returns:
            Dict with formatted P/BYD values for each period
        """
        if not results.get('success') or not results.get('periods'):
            return {
                'pbyd_30d': 'N/A',
                'pbyd_90d': 'N/A', 
                'pbyd_365d': 'N/A'
            }
        
        formatted = {}
        periods = results.get('periods', {})
        
        for period_key in ['pbyd_30d', 'pbyd_90d', 'pbyd_365d']:
            period_data = periods.get(period_key, {})
            formatted[period_key] = period_data.get('value', 'N/A')
            
        return formatted


# Test function
def test_multi_period_pbyd():
    """Test the multi-period P/BYD calculator with sample data"""
    print("🧪 Testing Multi-Period P/BYD Calculator")
    print("=" * 60)

    # Sample data with multiple historical points
    btc_data = {
        "2025-07-21": {"btc": 607770},   # Current (reference date)
        "2025-06-21": {"btc": 580000},   # ~30 days ago
        "2025-04-22": {"btc": 550000},   # ~90 days ago  
        "2024-07-21": {"btc": 226331},   # ~365 days ago
        "2024-06-20": {"btc": 220000},   # Even older data
        "2023-07-21": {"btc": 152333}    # Much older data
    }

    current_holdings = 607770
    mnav = 2.5  
    reference_date = datetime(2025, 7, 21)

    # Test multi-period calculation
    results = MultiPeriodPBYDCalculator.calculate_multi_period_pbyd(
        current_holdings, mnav, btc_data, reference_date
    )

    print(f"Overall Success: {results['success']}")
    print(f"Reference Date: {results['timestamp']}")
    print(f"Current Holdings: {results['current_btc_holdings']:,} BTC")
    print(f"mNAV: {results['mnav']}")
    print()

    # Display results for each period
    periods = results.get('periods', {})
    
    for period_name in ['pbyd_30d', 'pbyd_90d', 'pbyd_365d']:
        if period_name in periods:
            period_data = periods[period_name]
            print(f"📊 {period_name.upper()}:")
            print(f"  Value: {period_data['value']}")
            if period_data.get('reason'):
                print(f"  Reason: {period_data['reason']}")
            else:
                print(f"  Historical Date: {period_data.get('historical_date')}")
                print(f"  Actual Days: {period_data.get('actual_days')}")
                print(f"  Annualized Yield: {period_data.get('annualized_yield', 0):.4f}")
            print()

    # Test formatting function
    print("🎨 Formatted Results:")
    formatted = MultiPeriodPBYDCalculator.format_pbyd_results(results)
    for key, value in formatted.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    test_multi_period_pbyd()
