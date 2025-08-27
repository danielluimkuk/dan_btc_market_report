import time
import requests
import logging
from typing import Optional


class MVRVScraper:
    """
    MVRV data collector using BitBo.io free API
    Replaces web scraping with reliable API calls
    
    BitBo API: https://charts.bitbo.io/api/v1/
    - No API key required
    - Free tier with hourly updates
    - Simple JSON response format
    - Reliable MVRV ratio data
    """
    
    def __init__(self):
        self.base_url = "https://charts.bitbo.io/api/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BTC-MVRV-Collector/1.0'
        })
        
    def get_mvrv_from_bitbo(self) -> Optional[float]:
        """
        Get MVRV ratio from BitBo.io free API
        """
        try:
            # First try the MVRV ratio endpoint
            url = f"{self.base_url}/mvrv/"
            params = {'latest': 'true'}
            
            logging.info("Fetching MVRV ratio from BitBo.io API...")
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse BitBo response format: {"data": [["2025-05-07", "2.1963"]]}
            if 'data' in data and data['data'] and len(data['data']) > 0:
                latest_entry = data['data'][-1]  # Get the latest entry
                if len(latest_entry) >= 2:
                    mvrv_value = float(latest_entry[1])
                    date_str = latest_entry[0]
                    
                    logging.info(f"Successfully retrieved MVRV ratio: {mvrv_value:.3f} (Date: {date_str})")
                    return mvrv_value
                    
            logging.error("BitBo API returned data in unexpected format")
            return None
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Network error fetching MVRV from BitBo: {str(e)}")
            return None
        except (KeyError, ValueError, TypeError, IndexError) as e:
            logging.error(f"Data parsing error for MVRV: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error fetching MVRV: {str(e)}")
            return None

    def get_mvrv_zscore_from_bitbo(self) -> Optional[float]:
        """
        Fallback: Get MVRV Z-Score from BitBo.io and convert to approximate MVRV ratio
        MVRV Z-Score is normalized, but we can derive insights from it
        """
        try:
            url = f"{self.base_url}/mvrv-z/"
            params = {'latest': 'true'}
            
            logging.info("Fetching MVRV Z-Score from BitBo.io as fallback...")
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' in data and data['data'] and len(data['data']) > 0:
                latest_entry = data['data'][-1]
                if len(latest_entry) >= 2:
                    zscore = float(latest_entry[1])
                    date_str = latest_entry[0]
                    
                    # Convert Z-Score to approximate MVRV ratio
                    # This is an approximation based on historical patterns
                    # Z-Score of 0 ≈ MVRV of ~1.0, Z-Score of 2 ≈ MVRV of ~2.5
                    approximate_mvrv = max(0.1, 1.0 + (zscore * 0.75))
                    
                    logging.info(f"MVRV Z-Score: {zscore:.3f}, Approximate MVRV: {approximate_mvrv:.3f} (Date: {date_str})")
                    return approximate_mvrv
                    
            logging.error("BitBo Z-Score API returned data in unexpected format")
            return None
            
        except Exception as e:
            logging.error(f"Error fetching MVRV Z-Score: {str(e)}")
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
            print("Fetching MVRV using BitBo.io free API...")
            
        try:
            # Primary: Try to get MVRV ratio directly
            mvrv_value = self.get_mvrv_from_bitbo()
            
            if mvrv_value is not None:
                if verbose:
                    print(f"Success with MVRV ratio: {mvrv_value:.3f}")
                return mvrv_value
            else:
                if verbose:
                    print("MVRV ratio endpoint failed, trying Z-Score...")
                
                # Secondary: Try MVRV Z-Score as fallback
                zscore_mvrv = self.get_mvrv_zscore_from_bitbo()
                
                if zscore_mvrv is not None:
                    if verbose:
                        print(f"Success with Z-Score conversion: {zscore_mvrv:.3f}")
                    return zscore_mvrv
                else:
                    if verbose:
                        print("Both BitBo endpoints failed")
                    
        except Exception as e:
            logging.error(f"Error in get_mvrv_value: {str(e)}")
            if verbose:
                print(f"Error: {str(e)}")
        
        # Apply rate limiting pause (respect BitBo's free tier)
        time.sleep(6)
        
        # Fallback: return same default value as original scraper
        if verbose:
            print("All methods failed, returning fallback value: 2.1")
        logging.warning("MVRV collection failed, using fallback value: 2.1")
        
        return 2.1

    def test_api_connection(self) -> bool:
        """
        Test if BitBo.io API is accessible
        
        Returns:
            bool: True if API is working, False otherwise
        """
        try:
            # Test the MVRV Z-Score endpoint (most likely to work)
            url = f"{self.base_url}/mvrv-z/"
            params = {'latest': 'true'}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Check if response contains expected data structure
            if 'data' in data and len(data['data']) > 0:
                logging.info("BitBo.io API connection test successful")
                return True
            else:
                logging.error("BitBo API test failed: unexpected response format")
                return False
                
        except Exception as e:
            logging.error(f"BitBo API connection test failed: {str(e)}")
            return False


# Test the scraper (maintains original test structure)
if __name__ == "__main__":
    # Set up logging for testing
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("Testing BitBo MVRV Collector...")
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
            
        # Additional test: Try both endpoints individually
        print("\n3. Testing individual endpoints...")
        
        print("   Testing MVRV ratio endpoint...")
        mvrv_ratio = scraper.get_mvrv_from_bitbo()
        if mvrv_ratio:
            print(f"   ✅ MVRV Ratio: {mvrv_ratio:.3f}")
        else:
            print("   ❌ MVRV Ratio endpoint failed")
            
        print("   Testing MVRV Z-Score endpoint...")
        zscore_mvrv = scraper.get_mvrv_zscore_from_bitbo()
        if zscore_mvrv:
            print(f"   ✅ Z-Score derived MVRV: {zscore_mvrv:.3f}")
        else:
            print("   ❌ Z-Score endpoint failed")
            
    else:
        print("\n⚠️ Skipping MVRV test due to connection failure")
        
    print("\n" + "=" * 50)
    print("Test completed")
