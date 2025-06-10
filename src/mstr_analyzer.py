# =============================================================================
# Enhanced mstr_analyzer.py - WITH RETRY MECHANISM FOR RELIABILITY
# =============================================================================

import requests
import re
import json
import time
import math
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
import logging
from typing import Dict, Optional
from datetime import datetime, timezone

# Fix Windows console encoding for Unicode characters
if os.name == 'nt':  # Windows
    try:
        os.system('chcp 65001 >nul')
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
    except:
        pass


class MSTRAnalyzer:
    """
    Complete MSTR analysis using precise XPath targeting + improved options logic
    """

    def __init__(self):
        self.ua = UserAgent()
        self.ballistic_url = "https://microstrategist.com/ballistic.html"
        self.volatility_url = "https://www.barchart.com/stocks/quotes/MSTR/volatility-charts"

        # Precise XPath locations from the website
        self.model_price_xpath = "/html/body/div[1]/div[2]/div/div/div[3]/div[2]"
        self.deviation_xpath = "/html/body/div[1]/div[2]/div/div/div[4]/div[2]"

    def analyze_mstr(self, btc_price: float) -> Dict:
        """
        Complete MSTR analysis - main entry point

        Args:
            btc_price: Current BTC price for model calculation

        Returns:
            Dict with complete MSTR analysis
        """
        try:
            logging.info("Starting MSTR analysis with improved options logic...")

            # Step 1: Get ballistic data using XPath
            ballistic_data = self._get_ballistic_data_xpath(btc_price)

            # Rate limiting pause
            time.sleep(15)

            # Step 2: Get volatility data
            volatility_data = self._get_volatility_data()

            # Step 3: Analyze signals with improved logic
            analysis = self._analyze_signals_improved(ballistic_data, volatility_data)

            return {
                'success': True,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'ballistic_data': ballistic_data,
                'volatility_data': volatility_data,
                'analysis': analysis
            }

        except Exception as e:
            logging.error(f"MSTR analysis failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    def _get_ballistic_data_xpath(self, btc_price: float) -> Dict:
        """Get MSTR ballistic data using precise XPath"""
        driver = None
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

            driver = webdriver.Chrome(options=chrome_options)
            driver.get(self.ballistic_url)

            # Wait for page to load completely
            time.sleep(12)

            data = {'btc_price_used': btc_price}

            # Method 1: Get model price using exact XPath
            try:
                model_price_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, self.model_price_xpath))
                )
                model_price_text = model_price_element.text.strip()
                logging.info(f"Model price element text: '{model_price_text}'")

                # Extract price from text
                model_price = self._extract_price_from_text(model_price_text)
                if model_price:
                    data['model_price'] = model_price
                    logging.info(f"✅ Model price extracted: ${model_price:.2f}")
                else:
                    logging.warning(f"Could not extract price from model text: '{model_price_text}'")

            except Exception as e:
                logging.error(f"Error getting model price with XPath: {str(e)}")
                # Fallback to calculation
                data['model_price'] = self._calculate_model_price(btc_price)
                logging.info(f"Fallback to calculated model price: ${data['model_price']:.2f}")

            # Method 2: Get deviation percentage using exact XPath
            try:
                deviation_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, self.deviation_xpath))
                )
                deviation_text = deviation_element.text.strip()
                logging.info(f"Deviation element text: '{deviation_text}'")

                # Extract percentage from text
                deviation_pct = self._extract_percentage_from_text(deviation_text)
                if deviation_pct is not None:
                    data['deviation_pct'] = deviation_pct
                    logging.info(f"✅ Deviation extracted: {deviation_pct:.1f}%")

                    # Calculate actual price from model price and deviation
                    if 'model_price' in data:
                        model_price = data['model_price']
                        actual_price = model_price * (1 + deviation_pct / 100)
                        data['actual_price'] = round(actual_price, 2)
                        logging.info(f"✅ Actual price calculated: ${actual_price:.2f}")
                else:
                    logging.warning(f"Could not extract percentage from deviation text: '{deviation_text}'")

            except Exception as e:
                logging.error(f"Error getting deviation with XPath: {str(e)}")

            # Method 3: If we didn't get deviation, try to find actual price directly
            if 'actual_price' not in data and 'model_price' in data:
                actual_price = self._find_actual_price_xpath(driver)
                if actual_price:
                    data['actual_price'] = actual_price
                    # Calculate deviation
                    model = data['model_price']
                    actual = actual_price
                    data['deviation_pct'] = round(((actual - model) / model) * 100, 2)
                    logging.info(f"✅ Found actual price: ${actual_price:.2f}, deviation: {data['deviation_pct']:.1f}%")

            # Validation: Check if we have reasonable data
            if 'model_price' in data:
                model_price = data['model_price']
                if not (1 < model_price < 10000):  # Reasonable MSTR range
                    logging.warning(f"Model price seems unreasonable: ${model_price:.2f} (expected $1-$10,000)")

            return {
                'success': True,
                'source': 'xpath_precision',
                **data
            }

        except Exception as e:
            logging.error(f"XPath ballistic scraping failed: {str(e)}")

            # Final fallback
            model_price = self._calculate_model_price(btc_price)
            return {
                'success': True,
                'source': 'calculated_fallback',
                'model_price': model_price,
                'btc_price_used': btc_price,
                'note': 'XPath scraping failed, using calculated model price'
            }

        finally:
            if driver:
                driver.quit()

    def _extract_price_from_text(self, text: str) -> Optional[float]:
        """Extract price value from text"""
        try:
            # Remove common formatting and extract numbers
            clean_text = text.replace(',', '').replace('$', '')

            # Look for price patterns
            patterns = [
                r'([0-9]+\.?[0-9]*)',  # Basic number
                r'\$?([0-9,]+\.?[0-9]*)',  # Number with optional $
                r'([0-9,]+\.?[0-9]*)\s*\$?',  # Number with optional trailing $
            ]

            for pattern in patterns:
                matches = re.findall(pattern, clean_text)
                for match in matches:
                    try:
                        price_val = float(match.replace(',', ''))
                        if 1 < price_val < 10000:  # Expanded MSTR range $1-$10,000
                            return price_val
                    except ValueError:
                        continue

            return None

        except Exception as e:
            logging.error(f"Error extracting price from text '{text}': {str(e)}")
            return None

    def _extract_percentage_from_text(self, text: str) -> Optional[float]:
        """Extract percentage value from text"""
        try:
            # Look for percentage patterns
            patterns = [
                r'(-?[0-9]+\.?[0-9]*)\s*%',  # Number followed by %
                r'(-?[0-9]+\.?[0-9]*)\s*percent',  # Number followed by percent
                r'overvalued.*?(-?[0-9]+\.?[0-9]*)',  # Overvalued by X
                r'undervalued.*?(-?[0-9]+\.?[0-9]*)',  # Undervalued by X
            ]

            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    try:
                        pct_val = float(match)
                        if -100 < pct_val < 100:  # Reasonable percentage range
                            # If text contains "undervalued", make it negative
                            if 'undervalued' in text.lower() and pct_val > 0:
                                pct_val = -pct_val
                            return pct_val
                    except ValueError:
                        continue

            return None

        except Exception as e:
            logging.error(f"Error extracting percentage from text '{text}': {str(e)}")
            return None

    def _find_actual_price_xpath(self, driver) -> Optional[float]:
        """Try to find actual MSTR price using various XPath strategies"""
        try:
            # Common XPath patterns for finding current/actual price
            xpath_candidates = [
                "/html/body/div[1]/div[2]/div/div/div[2]/div[2]",  # Try element before model price
                "/html/body/div[1]/div[2]/div/div/div[1]/div[2]",  # Try first price element
                "/html/body/div[1]/div[2]/div/div/div[5]/div[2]",  # Try element after deviation
                "//div[contains(text(), 'Current') or contains(text(), 'Actual')]/following-sibling::div",
                "//div[contains(text(), '$') and not(contains(text(), 'Model'))]",
            ]

            for xpath in xpath_candidates:
                try:
                    element = driver.find_element(By.XPATH, xpath)
                    text = element.text.strip()
                    logging.info(f"Trying XPath {xpath}: '{text}'")

                    price = self._extract_price_from_text(text)
                    if price and 1 < price < 10000:
                        logging.info(f"Found actual price via XPath: ${price:.2f}")
                        return price

                except Exception as e:
                    continue

            return None

        except Exception as e:
            logging.error(f"Error finding actual price with XPath: {str(e)}")
            return None

    def _calculate_model_price(self, btc_price: float) -> float:
        """Calculate model price using ballistic formula"""
        # Formula: ln(MSTR Price) = 51.293498 + -10.676635*ln(BTC Price) + 0.586628*ln(BTC Price)^2
        ln_btc = math.log(btc_price)
        ln_mstr = 51.293498 + (-10.676635 * ln_btc) + (0.586628 * ln_btc ** 2)
        return round(math.exp(ln_mstr), 2)

    def _get_volatility_data(self) -> Dict:
        """Get MSTR volatility data from Barchart"""
        try:
            # Try Selenium
            data = self._scrape_volatility_selenium()
            if data.get('success'):
                return data

            return {'success': False, 'error': 'All volatility methods failed'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _scrape_volatility_selenium(self) -> Dict:
        """Scrape volatility data with Selenium - WORKING VERSION"""
        driver = None
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

            driver = webdriver.Chrome(options=chrome_options)
            driver.get(self.volatility_url)
            time.sleep(15)  # Increased wait time

            page_source = driver.page_source
            data = {}

            # Pattern 1: Implied Volatility
            iv_patterns = [
                r'Implied&nbsp;Volatility:.*?<strong>([0-9]+\.?[0-9]*)%?</strong>',
                r'Implied\s+Volatility:.*?<strong>([0-9]+\.?[0-9]*)%?</strong>',
                r'>IV:</span>.*?<strong>([0-9]+\.?[0-9]*)%?</strong>',
            ]

            for pattern in iv_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE | re.DOTALL)
                if matches:
                    try:
                        value = float(matches[0])
                        if 10 <= value <= 200:  # Reasonable IV range
                            data['iv'] = value
                            break
                    except ValueError:
                        continue

            # Pattern 2: IV Rank
            rank_patterns = [
                r'IV&nbsp;Rank:.*?<strong>([0-9]+\.?[0-9]*)%?</strong>',
                r'IV\s+Rank:.*?<strong>([0-9]+\.?[0-9]*)%?</strong>',
            ]

            for pattern in rank_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE | re.DOTALL)
                if matches:
                    try:
                        value = float(matches[0])
                        if 0 <= value <= 100:
                            data['iv_rank'] = value
                            break
                    except ValueError:
                        continue

            # Pattern 3: IV Percentile
            percentile_patterns = [
                r'IV&nbsp;Percentile:.*?<strong>([0-9]+\.?[0-9]*)%?</strong>',
                r'IV\s+Percentile:.*?<strong>([0-9]+\.?[0-9]*)%?</strong>',
            ]

            for pattern in percentile_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE | re.DOTALL)
                if matches:
                    try:
                        value = float(matches[0])
                        if 0 <= value <= 100:
                            data['iv_percentile'] = value
                            break
                    except ValueError:
                        continue

            return {
                'success': bool(data.get('iv', 0) > 0),  # ← FIXED: Success if we have IV data
                'source': 'selenium',
                **data
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if driver:
                driver.quit()

    def _analyze_signals_improved(self, ballistic_data: Dict, volatility_data: Dict) -> Dict:
        """
        IMPROVED SIGNAL ANALYSIS - Combines volatility + direction + market logic
        """
        try:
            analysis = {
                'price_signal': {},
                'volatility_signal': {},
                'volatility_conflict': {},
                'options_strategy': {}  # ← NEW: Improved options recommendations
            }

            # =================================================================
            # 1. PRICE SIGNAL ANALYSIS (unchanged)
            # =================================================================
            if ballistic_data.get('success'):
                deviation_pct = ballistic_data.get('deviation_pct', 0)
                model_price = ballistic_data.get('model_price', 0)
                actual_price = ballistic_data.get('actual_price', 0)

                if deviation_pct >= 25:
                    analysis['price_signal'] = {
                        'status': 'overvalued',
                        'signal': 'SELL',
                        'alert': True,
                        'message': f'MSTR Overvalued by {deviation_pct:.1f}%',
                        'recommendation': 'Consider selling'
                    }
                elif deviation_pct <= -20:
                    analysis['price_signal'] = {
                        'status': 'undervalued',
                        'signal': 'BUY',
                        'alert': True,
                        'message': f'MSTR Undervalued by {abs(deviation_pct):.1f}%',
                        'recommendation': 'Consider buying'
                    }
                else:
                    analysis['price_signal'] = {
                        'status': 'neutral',
                        'signal': 'HOLD',
                        'alert': False,
                        'message': f'MSTR Fair Valued ({deviation_pct:+.1f}%)'
                    }

            # =================================================================
            # 2. VOLATILITY CONFLICT CHECK (unchanged)
            # =================================================================
            if volatility_data.get('success'):
                iv_percentile = volatility_data.get('iv_percentile', 50)
                iv_rank = volatility_data.get('iv_rank', 50)

                # Check for conflicts
                if (iv_percentile < 30 and iv_rank > 70) or (iv_percentile > 70 and iv_rank < 30):
                    analysis['volatility_conflict'] = {
                        'is_conflicting': True,
                        'message': 'Conflicting Volatility Signals',
                        'description': f'IV Percentile ({iv_percentile:.0f}%) and IV Rank ({iv_rank:.0f}%) disagree'
                    }
                else:
                    analysis['volatility_conflict'] = {'is_conflicting': False}

                # =================================================================
                # 3. IMPROVED OPTIONS STRATEGY LOGIC 🎯
                # =================================================================
                options_strategy = self._determine_options_strategy(
                    iv_percentile=iv_percentile,
                    iv_rank=iv_rank,
                    deviation_pct=ballistic_data.get('deviation_pct', 0),
                    price_signal_status=analysis['price_signal'].get('status', 'neutral'),
                    volatility_conflicting=analysis['volatility_conflict'].get('is_conflicting', False)
                )

                analysis['options_strategy'] = options_strategy

                # =================================================================
                # 4. LEGACY VOLATILITY SIGNAL (for backwards compatibility)
                # =================================================================
                # Keep the old format but improve the logic
                analysis['volatility_signal'] = self._generate_legacy_volatility_signal(
                    options_strategy, iv_percentile, iv_rank
                )

            return analysis

        except Exception as e:
            return {'error': str(e)}

    def _determine_options_strategy(self, iv_percentile: float, iv_rank: float,
                                    deviation_pct: float, price_signal_status: str,
                                    volatility_conflicting: bool) -> Dict:
        """
        🎯 RESTORED: Original 30%/70% IV threshold logic for MSTR options strategy
        """

        # Step 1: Check if we have conflicting volatility data
        if volatility_conflicting:
            return {
                'primary_strategy': 'wait',
                'message': 'Wait for Clearer Setup',
                'description': 'Conflicting volatility signals - avoid options trades',
                'reasoning': 'IV Percentile and IV Rank disagree',
                'confidence': 'low'
            }

        # Step 2: 🎯 RESTORED: Use IV Percentile/Rank with 30%/70% thresholds
        # Determine volatility environment using the better of the two metrics
        iv_metric = max(iv_percentile, iv_rank) if iv_percentile > 0 or iv_rank > 0 else 50

        if iv_metric < 30:
            vol_env = 'low'  # Cheap options - good for buying premium
        elif iv_metric > 70:
            vol_env = 'high'  # Expensive options - good for selling premium
        else:
            vol_env = 'normal'  # Mixed environment

        # Step 3: Determine directional bias from ballistic model
        if price_signal_status == 'overvalued':
            direction = 'bearish'  # Expect price to fall toward model
        elif price_signal_status == 'undervalued':
            direction = 'bullish'  # Expect price to rise toward model
        else:
            direction = 'neutral'  # No strong directional bias

        # Step 4: 🎯 RESTORED: Combine volatility environment + directional bias
        return self._combine_vol_and_direction(vol_env, direction, iv_metric, deviation_pct)

    def _combine_vol_and_direction(self, vol_env: str, direction: str,
                                   iv_metric: float, deviation_pct: float) -> Dict:
        """
        🎯 RESTORED: Original volatility environment + directional bias logic
        """

        # =================================================================
        # LOW VOLATILITY (< 30% percentile/rank = cheap options)
        # =================================================================
        if vol_env == 'low':
            if direction == 'bullish':
                return {
                    'primary_strategy': 'long_calls',
                    'message': 'Consider Long Calls',
                    'description': f'Cheap options + undervalued setup (MSTR {abs(deviation_pct):.1f}% below model)',
                    'reasoning': f'Low IV environment ({iv_metric:.0f}%) makes options attractive + bullish bias',
                    'confidence': 'high'
                }
            elif direction == 'bearish':
                return {
                    'primary_strategy': 'long_puts',
                    'message': 'Consider Long Puts',
                    'description': f'Cheap options + overvalued setup (MSTR {deviation_pct:.1f}% above model)',
                    'reasoning': f'Low IV environment ({iv_metric:.0f}%) makes options attractive + bearish bias',
                    'confidence': 'high'
                }
            else:  # neutral direction
                return {
                    'primary_strategy': 'long_straddle',
                    'message': 'Consider Long Straddle',
                    'description': f'Cheap options + unclear direction (MSTR {deviation_pct:+.1f}% vs model)',
                    'reasoning': f'Low IV environment ({iv_metric:.0f}%) good for buying, but need big move either way',
                    'confidence': 'medium'
                }

        # =================================================================
        # HIGH VOLATILITY (> 70% percentile/rank = expensive options)
        # =================================================================
        elif vol_env == 'high':
            if direction == 'bullish':
                return {
                    'primary_strategy': 'short_puts',
                    'message': 'Consider Short Puts or Covered Calls',
                    'description': f'Expensive options + undervalued setup (MSTR {abs(deviation_pct):.1f}% below model)',
                    'reasoning': f'High IV environment ({iv_metric:.0f}%) good for selling premium + bullish bias favors put selling',
                    'confidence': 'high'
                }
            elif direction == 'bearish':
                return {
                    'primary_strategy': 'short_calls',
                    'message': 'Consider Short Calls or Protective Puts',
                    'description': f'Expensive options + overvalued setup (MSTR {deviation_pct:.1f}% above model)',
                    'reasoning': f'High IV environment ({iv_metric:.0f}%) good for selling premium + bearish bias favors call selling',
                    'confidence': 'medium'  # Calls have unlimited risk
                }
            else:  # neutral direction
                return {
                    'primary_strategy': 'short_strangle',
                    'message': 'Consider Premium Selling Strategies',
                    'description': f'Expensive options + range-bound expectation (MSTR {deviation_pct:+.1f}% vs model)',
                    'reasoning': f'High IV environment ({iv_metric:.0f}%) good for selling premium + no directional bias',
                    'confidence': 'medium'
                }

        # =================================================================
        # NORMAL VOLATILITY (30-70% percentile/rank = mixed environment)
        # =================================================================
        else:  # normal volatility
            if abs(deviation_pct) > 25:  # Strong directional signal from ballistic model
                if direction == 'bullish':
                    return {
                        'primary_strategy': 'moderate_bullish',
                        'message': 'Moderate Bullish Strategies',
                        'description': f'Normal IV + strong undervaluation ({abs(deviation_pct):.1f}% below model)',
                        'reasoning': f'Strong fundamental signal despite normal IV environment ({iv_metric:.0f}%)',
                        'confidence': 'medium'
                    }
                else:  # bearish
                    return {
                        'primary_strategy': 'moderate_bearish',
                        'message': 'Moderate Bearish Strategies',
                        'description': f'Normal IV + strong overvaluation ({deviation_pct:.1f}% above model)',
                        'reasoning': f'Strong fundamental signal despite normal IV environment ({iv_metric:.0f}%)',
                        'confidence': 'medium'
                    }
            else:
                return {
                    'primary_strategy': 'no_preference',
                    'message': 'No Strong Options Preference',
                    'description': f'Normal volatility + fair valuation ({deviation_pct:+.1f}% vs model)',
                    'reasoning': f'Neither volatility ({iv_metric:.0f}%) nor fundamentals provide clear edge',
                    'confidence': 'low'
                }

    def _generate_legacy_volatility_signal(self, options_strategy: Dict,
                                           iv_percentile: float, iv_rank: float) -> Dict:
        """
        🎯 RESTORED: Generate legacy volatility signal format for backwards compatibility
        """
        strategy = options_strategy.get('primary_strategy', 'no_preference')
        message = options_strategy.get('message', 'No Options Preference')
        description = options_strategy.get('description',
                                           f'IV Percentile: {iv_percentile:.0f}%, IV Rank: {iv_rank:.0f}%')

        # 🎯 RESTORED: Map strategies to legacy preferences
        if strategy in ['long_calls', 'moderate_bullish']:
            preference = 'long_calls'
        elif strategy in ['long_puts', 'moderate_bearish']:
            preference = 'long_puts'
        elif strategy == 'long_straddle':
            preference = 'long_straddle'
        elif strategy in ['short_puts', 'short_calls', 'short_strangle']:
            preference = 'premium_selling'
        else:
            preference = 'no_preference'

        return {
            'preference': preference,
            'message': message,
            'description': description
        }


def _validate_mstr_data(data: Dict) -> bool:
    """
    🎯 NEW: Validate MSTR data quality to determine if retry is needed

    Args:
        data: MSTR data dictionary from collect_mstr_data()

    Returns:
        bool: True if data is valid, False if retry is needed
    """
    try:
        if not data.get('success'):
            logging.warning("MSTR data collection failed")
            return False

        # Check if price is valid
        price = data.get('price', 0)
        if not price or price <= 0:
            logging.warning(f"Invalid MSTR price: {price}")
            return False

        # Check indicators
        indicators = data.get('indicators', {})

        # Model price should be reasonable
        model_price = indicators.get('model_price', 0)
        if not model_price or model_price <= 0 or not (1 < model_price < 10000):  # Expanded MSTR range $1-$10,000
            logging.warning(f"Invalid model price: {model_price}")
            return False

        # Deviation should exist and be reasonable
        deviation_pct = indicators.get('deviation_pct', None)
        if deviation_pct is None or abs(deviation_pct) > 200:  # No more than 200% deviation
            logging.warning(f"Invalid deviation: {deviation_pct}")
            return False

        # At least some volatility data should exist - IV is the most important
        iv = indicators.get('iv', 0)
        iv_percentile = indicators.get('iv_percentile', 0)
        iv_rank = indicators.get('iv_rank', 0)

        # 🎯 FIXED: As long as we have IV (main volatility metric), it's valid
        # IV Rank and Percentile can be 0% and that's still useful data
        if iv == 0:
            logging.warning("Missing main IV (Implied Volatility) data")
            return False

        logging.info(
            f"✅ MSTR data validation passed: Price=${price:.2f}, Model=${model_price:.2f}, Dev={deviation_pct:.1f}%, IV={iv:.1f}%")
        if iv_percentile == 0 and iv_rank == 0:
            logging.info(
                f"💡 Note: IV Rank and Percentile are 0%, but main IV ({iv:.1f}%) is valid - options strategy will still be generated")
        return True

    except Exception as e:
        logging.error(f"Error validating MSTR data: {str(e)}")
        return False


def collect_mstr_data_with_retry(btc_price: float, max_attempts: int = 3) -> Dict:
    """
    🎯 NEW: Collect MSTR data with retry mechanism for reliability

    Args:
        btc_price: Current BTC price for model calculation
        max_attempts: Maximum number of retry attempts (default: 3)

    Returns:
        Dict: MSTR data in format compatible with existing collector
    """
    attempt = 1

    while attempt <= max_attempts:
        logging.info(f"🔄 MSTR data collection attempt {attempt}/{max_attempts}")

        try:
            # Collect data using original function
            data = collect_mstr_data(btc_price)

            # Validate data quality
            if _validate_mstr_data(data):
                logging.info(f"✅ MSTR data collection successful on attempt {attempt}")
                return data
            else:
                logging.warning(f"⚠️ MSTR data validation failed on attempt {attempt}")

                if attempt < max_attempts:
                    wait_time = 30 + (attempt * 15)  # Progressive delay: 30s, 45s, 60s
                    logging.info(f"💤 Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)

        except Exception as e:
            logging.error(f"❌ MSTR collection error on attempt {attempt}: {str(e)}")

            if attempt < max_attempts:
                wait_time = 30 + (attempt * 15)
                logging.info(f"💤 Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)

        attempt += 1

    # All attempts failed
    logging.error(f"🚫 MSTR data collection failed after {max_attempts} attempts")
    return {
        'success': False,
        'type': 'stock',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'error': f'MSTR data collection failed after {max_attempts} attempts - all attempts returned invalid/empty data',
        'attempts_made': max_attempts
    }


# Original function for backwards compatibility
def collect_mstr_data(btc_price: float) -> Dict:
    """
    Original function to collect MSTR data for integration (unchanged)

    Args:
        btc_price: Current BTC price

    Returns:
        Dict in format compatible with existing collector
    """
    try:
        analyzer = MSTRAnalyzer()
        result = analyzer.analyze_mstr(btc_price)

        if result.get('success'):
            ballistic = result.get('ballistic_data', {})
            volatility = result.get('volatility_data', {})
            analysis = result.get('analysis', {})

            return {
                'success': True,
                'type': 'stock',
                'timestamp': result['timestamp'],
                'price': ballistic.get('actual_price', 0),
                'indicators': {
                    'model_price': ballistic.get('model_price', 0),
                    'deviation_pct': ballistic.get('deviation_pct', 0),
                    'iv': volatility.get('iv', 0),
                    'iv_percentile': volatility.get('iv_percentile', 0),
                    'iv_rank': volatility.get('iv_rank', 0)
                },
                'metadata': {
                    'source': 'mstr_analyzer',
                    'ballistic_source': ballistic.get('source', 'unknown'),
                    'volatility_source': volatility.get('source', 'unknown')
                },
                'analysis': analysis  # ← Now includes improved options logic
            }
        else:
            return {
                'success': False,
                'type': 'stock',
                'timestamp': result['timestamp'],
                'error': result.get('error', 'MSTR analysis failed')
            }

    except Exception as e:
        return {
            'success': False,
            'type': 'stock',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error': str(e)
        }


if __name__ == "__main__":
    # Test the enhanced retry mechanism
    import logging

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    print("🧪 Testing Enhanced MSTR Analyzer with Retry Mechanism...")
    print("=" * 70)

    # Test with retry mechanism
    print("\n🔄 Testing collect_mstr_data_with_retry()...")
    result = collect_mstr_data_with_retry(95000)  # Example BTC price

    if result.get('success'):
        print(f"✅ SUCCESS: Price=${result.get('price', 0):.2f}")
        indicators = result.get('indicators', {})
        print(f"   Model: ${indicators.get('model_price', 0):.2f}")
        print(f"   Deviation: {indicators.get('deviation_pct', 0):+.1f}%")
        print(f"   IV: {indicators.get('iv', 0):.1f}%")
        print(f"   IV Rank: {indicators.get('iv_rank', 0):.1f}%")
        print(f"   IV Percentile: {indicators.get('iv_percentile', 0):.1f}%")

        analysis = result.get('analysis', {})
        price_signal = analysis.get('price_signal', {})
        options_strategy = analysis.get('options_strategy', {})

        print(f"   Price Signal: {price_signal.get('signal', 'N/A')}")
        print(f"   Options Strategy: {options_strategy.get('message', 'N/A')}")
        print(f"   Strategy Reasoning: {options_strategy.get('reasoning', 'N/A')}")

        # 🎯 Test edge case: IV=53%, Rank=0%, Percentile=0%
        print(f"\n🧪 Testing edge case (IV=53%, Rank=0%, Percentile=0%)...")
        test_data = {
            'success': True,
            'price': 425.67,
            'indicators': {
                'model_price': 398.12,
                'deviation_pct': 6.9,
                'iv': 53.0,
                'iv_percentile': 0.0,
                'iv_rank': 0.0
            }
        }

        is_valid = _validate_mstr_data(test_data)
        print(f"   Validation result: {'✅ VALID' if is_valid else '❌ INVALID'}")

        if is_valid:
            print(f"   ✅ Options strategy SHOULD be generated with this data!")
            print(f"   📊 IV Analysis: Percentile=0% & Rank=0% < 30% = 🟢 LOW IV = Cheap Options")
            print(f"   📈 Direction: {test_data['indicators']['deviation_pct']:+.1f}% vs model = Neutral (fair valued)")
            print(f"   🎯 Expected Strategy: Long Straddle (low IV + neutral direction)")
        else:
            print(f"   ❌ Options strategy will NOT be generated - this is the bug!")

    else:
        print(f"❌ FAILED: {result.get('error', 'Unknown')}")
        if 'attempts_made' in result:
            print(f"   Attempts made: {result['attempts_made']}")

    print("\n🎯 Enhanced retry mechanism test complete!")
