"""
Intraday Historical Data Collector - Minute Level
================================================

Author: Shck Tchamna (tchamna@gmail.com)

This script collects minute-by-minute historical data for yesterday
from financial APIs for detailed intraday analysis.
"""

import requests
import json
from datetime import datetime, timedelta, timezone
import time
import sys
import os
import pandas as pd

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config


def get_intraday_stock_data(symbol: str, api_key: str, date: str):
    """Get minute-level stock data for a specific date"""
    print(f"📈 Fetching minute data for {symbol} on {date}...")
    
    try:
        # Use Alpha Vantage INTRADAY endpoint for minute data
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': symbol,
            'interval': '1min',
            'apikey': api_key,
            'outputsize': 'full',  # Get full day of data
            'datatype': 'json'
        }
        
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        if 'Time Series (1min)' in data:
            time_series = data['Time Series (1min)']
            
            # Filter for yesterday's data only
            target_date = date
            results = []
            
            for timestamp, values in time_series.items():
                # Check if timestamp is from target date
                if timestamp.startswith(target_date):
                    results.append({
                        'symbol': symbol,
                        'timestamp': timestamp,
                        'datetime': datetime.fromisoformat(timestamp.replace(' ', 'T')),
                        'open': float(values['1. open']),
                        'high': float(values['2. high']), 
                        'low': float(values['3. low']),
                        'close': float(values['4. close']),
                        'volume': int(values['5. volume']),
                        'api_source': 'Alpha Vantage',
                        'interval': '1min'
                    })
            
            # Sort by timestamp
            results.sort(key=lambda x: x['timestamp'])
            
            print(f"   ✅ {symbol}: {len(results)} minute data points for {date}")
            return results
            
        else:
            print(f"   ⚠️  API Response keys: {list(data.keys())}")
            if 'Note' in data:
                print(f"   📝 API Note: {data['Note']}")
            return []
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []


def get_crypto_minute_data(crypto_id: str, date: str):
    """Get minute-level crypto data using CoinGecko (limited historical minute data)"""
    print(f"🪙 Fetching minute data for {crypto_id} on {date}...")
    
    try:
        # CoinGecko has limited minute-level historical data
        # Use hourly data as closest available for historical dates
        yesterday = datetime.strptime(date, '%Y-%m-%d')
        days_ago = (datetime.now() - yesterday).days
        
        url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}/market_chart"
        params = {
            'vs_currency': 'usd',
            'days': days_ago + 1,
            'interval': 'hourly' if days_ago > 1 else 'minutely'
        }
        
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        if 'prices' in data:
            prices = data['prices']
            volumes = data.get('total_volumes', [])
            
            results = []
            target_timestamp_start = int(yesterday.timestamp() * 1000)
            target_timestamp_end = int((yesterday + timedelta(days=1)).timestamp() * 1000)
            
            for i, price_data in enumerate(prices):
                timestamp_ms = price_data[0]
                price = price_data[1]
                
                # Filter for target date
                if target_timestamp_start <= timestamp_ms < target_timestamp_end:
                    dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
                    volume = volumes[i][1] if i < len(volumes) else 0
                    
                    results.append({
                        'symbol': crypto_id.upper(),
                        'timestamp': dt.strftime('%Y-%m-%d %H:%M:%S'),
                        'datetime': dt,
                        'price': price,
                        'volume': volume,
                        'api_source': 'CoinGecko',
                        'interval': 'hourly' if days_ago > 1 else 'minutely'
                    })
            
            results.sort(key=lambda x: x['timestamp'])
            print(f"   ✅ {crypto_id}: {len(results)} data points for {date}")
            return results
            
        else:
            print(f"   ⚠️  No price data available for {crypto_id}")
            return []
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []


def collect_yesterday_minute_data():
    """Collect minute-level data for yesterday"""
    
    config = get_config()
    
    # Calculate yesterday's date
    yesterday = datetime.now() - timedelta(days=1)
    target_date = yesterday.strftime('%Y-%m-%d')
    
    print("📊 INTRADAY HISTORICAL DATA COLLECTION")
    print("=" * 60)
    print(f"🎯 Target Date: {target_date} (Yesterday)")
    print(f"📈 Resolution: Minute-level data")
    
    all_data = {
        'collection_time': datetime.now(timezone.utc).isoformat(),
        'target_date': target_date,
        'resolution': 'minute',
        'stocks': [],
        'crypto': []
    }
    
    # Collect stock minute data (limited to avoid API limits)
    print(f"\n📈 Collecting Stock Minute Data for {target_date}...")
    stock_symbols = ['AAPL', 'TSLA', 'MSFT']  # Limited for API rate limits
    
    for symbol in stock_symbols:
        stock_data = get_intraday_stock_data(symbol, config.api.alpha_vantage_api_key, target_date)
        all_data['stocks'].extend(stock_data)
        time.sleep(12)  # Alpha Vantage rate limit: 5 calls per minute
        
        if not stock_data:  # If no data, likely hit rate limit
            print("   ⚠️  Rate limit reached or no data available")
            break
    
    # Collect crypto data (hourly resolution for historical dates)
    print(f"\n🪙 Collecting Crypto Data for {target_date}...")
    crypto_symbols = ['bitcoin', 'ethereum', 'cardano']
    
    for crypto_id in crypto_symbols:
        crypto_data = get_crypto_minute_data(crypto_id, target_date)
        all_data['crypto'].extend(crypto_data)
        time.sleep(1.2)  # CoinGecko rate limiting
    
    # Save results
    filename = f"intraday_data_{target_date.replace('-', '')}.json"
    with open(filename, 'w') as f:
        json.dump(all_data, f, indent=2, default=str)
    
    print(f"\n💾 COLLECTION SUMMARY:")
    print(f"   📈 Stock minute records: {len(all_data['stocks'])}")
    print(f"   🪙 Crypto records: {len(all_data['crypto'])}")
    print(f"   📄 Saved to: {filename}")
    
    return all_data, filename


def analyze_intraday_data(data):
    """Analyze the collected intraday data"""
    
    print(f"\n📊 INTRADAY DATA ANALYSIS")
    print("=" * 40)
    
    target_date = data['target_date']
    
    # Analyze stock minute data
    if data['stocks']:
        print(f"📈 Stock Minute Data Analysis for {target_date}:")
        
        for symbol in set(record['symbol'] for record in data['stocks']):
            symbol_data = [r for r in data['stocks'] if r['symbol'] == symbol]
            symbol_data.sort(key=lambda x: x['timestamp'])
            
            if symbol_data:
                first = symbol_data[0]
                last = symbol_data[-1]
                
                # Calculate day's performance
                day_change = last['close'] - first['open']
                day_change_pct = (day_change / first['open']) * 100
                
                # Get high/low for the day
                day_high = max(r['high'] for r in symbol_data)
                day_low = min(r['low'] for r in symbol_data)
                day_volume = sum(r['volume'] for r in symbol_data)
                
                print(f"\n   {symbol} ({len(symbol_data)} minutes):")
                print(f"     Open: ${first['open']:.2f} → Close: ${last['close']:.2f}")
                print(f"     Change: {day_change_pct:+.2f}% (${day_change:+.2f})")
                print(f"     Range: ${day_low:.2f} - ${day_high:.2f}")
                print(f"     Volume: {day_volume:,} shares")
                print(f"     First: {first['timestamp']}")
                print(f"     Last: {last['timestamp']}")
    
    else:
        print(f"📈 No stock minute data available for {target_date}")
        print("   ⚠️  Possible reasons:")
        print("   - Weekend (markets closed)")
        print("   - Holiday (markets closed)")
        print("   - API rate limits reached")
    
    # Analyze crypto data
    if data['crypto']:
        print(f"\n🪙 Crypto Data Analysis for {target_date}:")
        
        for symbol in set(record['symbol'] for record in data['crypto']):
            symbol_data = [r for r in data['crypto'] if r['symbol'] == symbol]
            symbol_data.sort(key=lambda x: x['timestamp'])
            
            if len(symbol_data) >= 2:
                first = symbol_data[0]
                last = symbol_data[-1]
                
                day_change = last['price'] - first['price']
                day_change_pct = (day_change / first['price']) * 100
                
                print(f"\n   {symbol} ({len(symbol_data)} data points):")
                print(f"     Start: ${first['price']:.2f} → End: ${last['price']:.2f}")
                print(f"     Change: {day_change_pct:+.2f}% (${day_change:+.2f})")
                print(f"     Interval: {symbol_data[0].get('interval', 'hourly')}")


def main():
    """Main execution function"""
    
    print("⏰ MINUTE-LEVEL HISTORICAL DATA COLLECTOR")
    print("=" * 70)
    print("🎯 Collecting every minute of yesterday's trading data")
    
    # Collect data
    data, filename = collect_yesterday_minute_data()
    
    # Analyze data
    analyze_intraday_data(data)
    
    # API limitations explanation
    print(f"\n📋 IMPORTANT NOTES:")
    print("=" * 25)
    print("📈 Alpha Vantage (Stocks):")
    print("   ✅ True minute-level data available")
    print("   ⚠️  Rate limit: 5 calls/minute (25/day free tier)")
    print("   🎯 Best for: Recent trading days (not weekends)")
    
    print(f"\n🪙 CoinGecko (Crypto):")
    print("   ⚠️  Limited minute history (recent data only)")
    print("   ✅ Hourly resolution for historical dates")
    print("   🎯 24/7 data available (no market hours)")
    
    print(f"\n💡 FOR TRUE MINUTE DATA:")
    print("- Run during market hours for real-time minute data")
    print("- Use premium APIs for extensive historical minute data")
    print("- Consider WebSocket streams for live minute updates")
    
    print(f"\n🎉 Intraday data collection complete!")
    print(f"📄 Data saved in: {filename}")


if __name__ == "__main__":
    main()