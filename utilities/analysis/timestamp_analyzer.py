"""
Timestamp Analysis Tool
======================

Author: Shck Tchamna (tchamna@gmail.com)

This script analyzes the timestamps from collected data
to understand timezone patterns and collection timing.
"""

import json
from datetime import datetime, timezone
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def analyze_timestamps():
    """Analyze timestamp patterns from the collected data"""
    
    print("🕐 TIMESTAMP ANALYSIS")
    print("=" * 50)
    
    # Load the most recent data file
    filename = "historical_batch_data_20251013_191555.json"
    
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        
        print(f"📄 Analyzing data from: {filename}")
        print(f"🕐 Collection time: {data['collection_time']}")
        
        # Parse collection time
        collection_dt = datetime.fromisoformat(data['collection_time'])
        print(f"📅 Collection date: {collection_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"🌍 Timezone: {collection_dt.tzinfo}")
        
        print(f"\n🪙 CRYPTO TIMESTAMP ANALYSIS:")
        print("-" * 40)
        
        if data['crypto']:
            # Group by symbol
            crypto_symbols = set(record['symbol'] for record in data['crypto'])
            
            for symbol in sorted(crypto_symbols):
                symbol_data = [r for r in data['crypto'] if r['symbol'] == symbol]
                print(f"\n{symbol}:")
                
                for i, record in enumerate(symbol_data[:3]):  # Show first 3
                    timestamp = record['timestamp']
                    dt = datetime.fromisoformat(timestamp)
                    print(f"  Day {i+1}: {record['date']} | {dt.strftime('%H:%M:%S %Z')} | Price: ${record['price']:,.2f}")
                
                # Check if all timestamps are identical
                times = [datetime.fromisoformat(r['timestamp']).time() for r in symbol_data]
                unique_times = set(times)
                
                if len(unique_times) == 1:
                    print(f"  ✅ All timestamps identical: {list(unique_times)[0]}")
                else:
                    print(f"  ⚠️  Different timestamps: {len(unique_times)} unique times")
        
        print(f"\n📊 TIMESTAMP SUMMARY:")
        print("-" * 30)
        print(f"🌍 All timestamps in UTC (Universal Coordinated Time)")
        print(f"🕐 CoinGecko daily data: 00:00:00 UTC (midnight)")
        print(f"📈 This represents daily close prices at UTC midnight")
        print(f"⏰ Your collection happened at: {collection_dt.strftime('%H:%M:%S UTC')}")
        
        # Calculate how recent the data is
        if data['crypto']:
            latest_crypto = max(data['crypto'], key=lambda x: x['date'])
            latest_date = datetime.fromisoformat(latest_crypto['timestamp'])
            days_ago = (collection_dt - latest_date).days
            print(f"📅 Most recent data: {latest_date.strftime('%Y-%m-%d')} ({days_ago} days ago)")
        
    except FileNotFoundError:
        print(f"❌ File {filename} not found")
    except Exception as e:
        print(f"❌ Error: {e}")


def compare_api_timing():
    """Compare timing patterns between the two APIs"""
    
    print(f"\n🔄 API TIMING COMPARISON:")
    print("=" * 40)
    
    print(f"🪙 CoinGecko (Crypto):")
    print(f"   🕐 Timestamps: Always 00:00:00 UTC")
    print(f"   📅 Frequency: Daily snapshots")
    print(f"   🎯 Represents: End-of-day prices")
    print(f"   ✅ Consistent: All symbols same timestamp")
    
    print(f"\n📈 Alpha Vantage (Stocks):")
    print(f"   🕐 Timestamps: Market close time (varies by exchange)")
    print(f"   📅 Frequency: Trading days only (Mon-Fri)")
    print(f"   🎯 Represents: Market closing prices")
    print(f"   ⚠️  Variable: Different exchanges, different times")
    print(f"   🏢 NYSE/NASDAQ: 16:00 EST (21:00 UTC)")
    
    print(f"\n💡 KEY INSIGHTS:")
    print("-" * 20)
    print(f"1️⃣ Crypto markets: 24/7 trading, UTC timestamps")
    print(f"2️⃣ Stock markets: Business hours only, exchange-specific")
    print(f"3️⃣ Weekend issue: Stocks don't trade Sat/Sun")
    print(f"4️⃣ Best collection time: Weekday mornings UTC")


if __name__ == "__main__":
    analyze_timestamps()
    compare_api_timing()