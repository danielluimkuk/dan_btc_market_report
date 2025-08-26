import time
import requests
import logging
from typing import Optional


class MVRVScraper:
    """
    MVRV data collector using CoinMetrics Community API
    Replaces web scraping with reliable API calls
    
    Community API: https://community-api.coinmetrics.io/v4
    - No API key required
    - 10 requests per 6 seconds rate limit
    - Creative Commons license
    - Authoritative MVRV data source
    """
    
    def __init__(self):
        self.base_url = "https://community-api.coinmetrics.io/v4"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BTC-MVRV-Collector/1.0'
        })
        
    def get_mvrv_from_coinmetrics(self) -> Optional[float]:
        """
        Get MVRV ratio from CoinMetrics Community API
        MVRV = Market Cap (CapMktCurUSD) / Realized Cap (CapRealUSD)
        """
        try:
            # Single API call to get both Market Cap and Realized Cap
            url = f"{self.base_url}/timeseries/asset-metrics"
            params = {
                'assets': 'btc',
                'metrics': 'CapMktCurUSD,CapRealUSD',
                'frequency': '1d',
                'limit': 1,  # Get only the latest value
                'pretty': 'true'
            }
            
            logging.info("Fetching MVRV data from CoinMetrics Community API...")
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse the response
            if 'data' not in data or not data['data']:
                logging.error("No data returned from CoinMetrics API")
                return None
                
            # Get the latest data point
            latest_data = data['data'][0]  # Should be the most recent
            
            market_cap = None
            realized_cap = None
            
            # Extract market cap and realized cap values
            if 'CapMktCurUSD' in latest_data:
                market_cap = float(latest_data['CapMktCurUSD'])
                
            if 'CapRealUSD' in latest_data:
                realized_cap = float(latest_data['CapRealUSD'])
                
            # Validate we got both values
            if market_cap is None or realized_cap is None:
                logging.error(f"Missing data: MarketCap={market_cap}, RealizedCap={realized_cap}")
                return None
                
            if realized_cap <= 0:
                logging.error(f"Invalid realized cap value: {realized_cap}")
                return None
                
            # Calculate MVRV ratio
            mvrv_ratio = market_cap / realized_cap
            
            # Validate MVRV is in reasonable range
            if not (0.1 <= mvrv_ratio <= 10.0):
                logging.warning(f"MVRV value outside expected range: {mvrv_ratio}")
                
            logging.info(f"Successfully calculated MVRV: {mvrv_ratio:.3f} (MarketCap: ${market_cap:,.0f}, RealizedCap: ${realized_cap:,.0f})")
            
            return mvrv_ratio
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Network error fetching MVRV from CoinMetrics: {str(e)}")
            return None
        except (KeyError, ValueError, TypeError) as e:
            logging.error(f"Data parsing error for MVRV: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error fetching MVRV: {str(e)}")
            return None

    def get_mvrv_value(self, verbose=False) -> float:
        """
        Main method to get MVRV value - maintains compatibility with existing code
        
        Args:
            verbose (bool): Enable verbose logging (maintained for compatibility)
            
        Returns:
            float: MVRV ratio, or 2.1 as fallback if all methods fail
        """
        if verbose:
            print("Fetching MVRV using CoinMetrics Community API...")
            
        try:
            # Get MVRV from CoinMetrics API
            mvrv_value = self.get_mvrv_from_coinmetrics()
            
            if mvrv_value is not None:
                if verbose:
                    print(f"Success: MVRV = {mvrv_value:.3f}")
                return mvrv_value
            else:
                if verbose:
                    print("CoinMetrics API returned None")
                    
        except Exception as e:
            logging.error(f"Error in get_mvrv_value: {str(e)}")
            if verbose:
                print(f"Error: {str(e)}")
        
        # Apply rate limiting pause (6 seconds for CoinMetrics Community API)
        # This ensures we don't exceed 10 requests per 6 seconds
        time.sleep(6)
        
        # Fallback: return same default value as original scraper
        if verbose:
            print("All methods failed, returning fallback value: 2.1")
        logging.warning("MVRV collection failed, using fallback value: 2.1")
        
        return 2.1

    def test_api_connection(self) -> bool:
        """
        Test if CoinMetrics Community API is accessible
        
        Returns:
            bool: True if API is working, False otherwise
        """
        try:
            url = f"{self.base_url}/catalog/assets"
            params = {'assets': 'btc', 'pretty': 'true'}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Check if response contains expected data structure
            if 'data' in data and len(data['data']) > 0:
                logging.info("CoinMetrics Community API connection test successful")
                return True
            else:
                logging.error("CoinMetrics API test failed: unexpected response format")
                return False
                
        except Exception as e:
            logging.error(f"CoinMetrics API connection test failed: {str(e)}")
            return False


# Test the scraper (maintains original test structure)
if __name__ == "__main__":
    # Set up logging for testing
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("Testing CoinMetrics MVRV Collector...")
    print("=" * 50)
    
    scraper = MVRVScraper()
    
    # Test API connection
    print("\n1. Testing API connection...")
    connection_ok = scraper.test_api_connection()
    print(f"   Connection: {'✅ OK' if connection_ok else '❌ Failed'}")
    
    if connection_ok:
        print("\n2. Testing MVRV collection...")
        mvrv = scraper.get_mvrv_value(verbose=True)
        print(f"\n   Final MVRV value: {mvrv}")
        
        if mvrv != 2.1:  # Not fallback value
            print("   ✅ Successfully retrieved live MVRV data!")
        else:
            print("   ⚠️ Using fallback value - check API status")
    else:
        print("\n⚠️ Skipping MVRV test due to connection failure")
        
    print("\n" + "=" * 50)
    print("Test completed")
