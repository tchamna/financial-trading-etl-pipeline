"""
Simple Historical Data Fetcher
==============================

Author: Shck Tchamna (tchamna@gmail.com)

This script fetches available historical data from both APIs
and provides batch collection capabilities.
"""

import requests
import json
from datetime import datetime, timedelta, timezone
import time
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config


def get_stock_weekly_data(symbol: str, api_key: str):
    """Get weekly stock data (works around daily API limits)"""
    print(f"📈 Fetching weekly data for {symbol}...")
    
    try:
        # Use WEEKLY endpoint for better historical coverage
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'TIME_SERIES_WEEKLY',
            'symbol': symbol,
            'apikey': api_key
        }
        
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        if 'Weekly Time Series' in data:
            weekly_series = data['Weekly Time Series']
            # Get the most recent week's data
            recent_dates = sorted(weekly_series.keys(), reverse=True)[:3]
            
            results = []
            for date in recent_dates:
                week_data = weekly_series[date]
                results.append({
                    'symbol': symbol,
                    'date': date,
                    'open': float(week_data['1. open']),
                    'high': float(week_data['2. high']),
                    'low': float(week_data['3. low']),
                    'close': float(week_data['4. close']),
                    'volume': int(week_data['5. volume']),
                    'period': 'weekly',
                    'api_source': 'Alpha Vantage'
                })
            
            print(f"   ✅ {symbol}: {len(results)} weeks of data")
            return results
        
        else:
            print(f"   ⚠️  API Response: {list(data.keys())}")
            return []
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []


def get_crypto_price_history(crypto_id: str, days: int = 7):
    """Get crypto price history using CoinGecko market chart"""
    print(f"🪙 Fetching {days} days of {crypto_id} data...")
    
    try:
        # Use market_chart endpoint for historical prices
        url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}/market_chart"
        params = {
            'vs_currency': 'usd',
            'days': days,
            'interval': 'daily' if days > 1 else 'hourly'
        }
        
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        if 'prices' in data:
            prices = data['prices']
            volumes = data.get('total_volumes', [])
            market_caps = data.get('market_caps', [])
            
            results = []
            for i, price_data in enumerate(prices[-7:]):  # Last 7 data points
                timestamp = price_data[0]
                price = price_data[1]
                
                # Convert timestamp to readable date
                date = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
                
                volume = volumes[i][1] if i < len(volumes) else 0
                market_cap = market_caps[i][1] if i < len(market_caps) else 0
                
                results.append({
                    'symbol': crypto_id.upper(),
                    'date': date.strftime('%Y-%m-%d'),
                    'timestamp': date.isoformat(),
                    'price': price,
                    'volume_24h': volume,
                    'market_cap': market_cap,
                    'api_source': 'CoinGecko'
                })
            
            print(f"   ✅ {crypto_id}: {len(results)} days of data")
            return results
        
        else:
            print(f"   ⚠️  No price data found for {crypto_id}")
            return []
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []


def collect_batch_historical_data():
    """Collect batch historical data from both APIs"""
    
    config = get_config()
    
    print("🚀 BATCH HISTORICAL DATA COLLECTION")
    print("=" * 60)
    
    all_data = {
        'collection_time': datetime.now(timezone.utc).isoformat(),
        'stocks': [],
        'crypto': []
    }
    
    # Collect stock data (limited to avoid API limits)
    print("\n📈 Collecting Stock Historical Data...")
    stock_symbols = ['AAPL', 'MSFT', 'GOOGL']  # Limited sample
    
    for symbol in stock_symbols:
        stock_data = get_stock_weekly_data(symbol, config.api.alpha_vantage_api_key)
        all_data['stocks'].extend(stock_data)
        time.sleep(1)  # Rate limiting
    
    # Collect crypto data
    print(f"\n🪙 Collecting Crypto Historical Data...")
    crypto_symbols = ['bitcoin', 'ethereum', 'cardano']  # Limited sample
    
    for crypto_id in crypto_symbols:
        crypto_data = get_crypto_price_history(crypto_id, days=7)
        all_data['crypto'].extend(crypto_data)
        time.sleep(1.2)  # CoinGecko rate limiting
    
    # Save results
    filename = f"historical_batch_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(all_data, f, indent=2)
    
    print(f"\n💾 COLLECTION SUMMARY:")
    print(f"   📈 Stock records: {len(all_data['stocks'])}")
    print(f"   🪙 Crypto records: {len(all_data['crypto'])}")
    print(f"   📄 Saved to: {filename}")
    
    return all_data, filename


def analyze_collected_data(data):
    """Analyze the collected historical data"""
    
    print(f"\n📊 DATA ANALYSIS")
    print("=" * 40)
    
    # Analyze stock data
    if data['stocks']:
        print(f"📈 Stock Data Analysis:")
        symbols = set(record['symbol'] for record in data['stocks'])
        print(f"   Symbols: {', '.join(symbols)}")
        
        for symbol in symbols:
            symbol_data = [r for r in data['stocks'] if r['symbol'] == symbol]
            if symbol_data:
                latest = symbol_data[0]
                print(f"   {symbol}: ${latest['close']:.2f} (Week ending {latest['date']})")
    
    # Analyze crypto data
    if data['crypto']:
        print(f"\n🪙 Crypto Data Analysis:")
        symbols = set(record['symbol'] for record in data['crypto'])
        print(f"   Symbols: {', '.join(symbols)}")
        
        for symbol in symbols:
            symbol_data = [r for r in data['crypto'] if r['symbol'] == symbol]
            if symbol_data:
                # Calculate price change over period
                symbol_data.sort(key=lambda x: x['date'])
                if len(symbol_data) >= 2:
                    oldest = symbol_data[0]
                    newest = symbol_data[-1]
                    change = newest['price'] - oldest['price']
                    change_pct = (change / oldest['price']) * 100
                    print(f"   {symbol}: ${newest['price']:.2f} ({change_pct:+.2f}% over {len(symbol_data)} days)")


def main():
    """Main execution function"""
    
    print("🎯 HISTORICAL DATA COLLECTION & COMPARISON")
    print("=" * 70)
    
    # Collect data
    data, filename = collect_batch_historical_data()
    
    # Analyze data
    analyze_collected_data(data)
    
    # API comparison summary
    print(f"\n🔍 API COMPARISON SUMMARY:")
    print("=" * 40)
    print("📈 Alpha Vantage (Stocks):")
    print("   ✅ Rich OHLCV data")
    print("   ⚠️  Limited free tier (25 calls/day)")
    print("   📊 Best for: Technical analysis, trading algorithms")
    
    print(f"\n🪙 CoinGecko (Crypto):")
    print("   ✅ Batch collection efficient")
    print("   ✅ Generous free tier (50 calls/min)")
    print("   📊 Best for: Market analysis, portfolio tracking")
    
    print(f"\n🎉 Historical data collection complete!")
    print(f"📄 Data saved in: {filename}")


if __name__ == "__main__":
    main()