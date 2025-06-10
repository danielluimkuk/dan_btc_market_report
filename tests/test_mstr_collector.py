"""Test MSTR data collection"""
import sys
import os

sys.path.append('..')  # Add parent directory to path

from dotenv import load_dotenv

load_dotenv()


def test_mstr_collection():
    """Test MSTR ballistic model + volatility collection"""
    print("🧪 Testing MSTR Data Collection...")
    print("⏳ This may take 30-60 seconds due to web scraping...")

    from mstr_analyzer import collect_mstr_data

    # Use sample BTC price
    btc_price = 95000.0
    print(f"📊 Using BTC price: ${btc_price:,.2f}")

    result = collect_mstr_data(btc_price)

    print(f"✅ MSTR Result: {result}")

    if result.get('success'):
        indicators = result.get('indicators', {})
        print(f"✅ Model Price: ${indicators.get('model_price', 0):,.2f}")
        print(f"✅ Actual Price: ${result.get('price', 0):,.2f}")
        print(f"✅ Deviation: {indicators.get('deviation_pct', 0):+.1f}%")
        print(f"✅ IV Percentile: {indicators.get('iv_percentile', 0):.0f}%")
        print(f"✅ IV Rank: {indicators.get('iv_rank', 0):.0f}%")
        print("✅ MSTR Collection Test PASSED")
    else:
        print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        print("⚠️ MSTR Collection Test FAILED (This is normal if websites are blocking scraping)")


if __name__ == "__main__":
    test_mstr_collection()