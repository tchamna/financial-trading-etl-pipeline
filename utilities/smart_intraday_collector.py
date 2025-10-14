"""
Smart Intraday Data Collector
============================

Author: Shck Tchamna (tchamna@gmail.com)

This script intelligently collects minute-level data by:
1. Checking if target date was a trading day
2. Using the most recent trading day if weekend
3. Providing multiple data sources and intervals
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


def is_trading_day(date):
    """Check if a date was likely a trading day (Mon-Fri, basic check)"""
    weekday = date.weekday()  # Monday = 0, Sunday = 6
    return weekday < 5  # Monday through Friday


def get_last_trading_day():
    """Get the most recent trading day"""
    date = datetime.now().date()
    while not is_trading_day(date):
        date -= timedelta(days=1)
    return date


def get_recent_intraday_data(symbol: str, api_key: str):
    """Get recent intraday data (last available trading day)"""
    print(f"📈 Fetching recent intraday data for {symbol}...")
    
    try:
        # Use Alpha Vantage INTRADAY with recent data
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': symbol,
            'interval': '5min',  # 5-minute intervals (more data points)
            'apikey': api_key,
            'outputsize': 'compact',  # Recent data only
            'datatype': 'json'
        }
        
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        if 'Time Series (5min)' in data:
            time_series = data['Time Series (5min)']
            
            results = []
            for timestamp, values in list(time_series.items())[:50]:  # Last 50 data points
                results.append({
                    'symbol': symbol,
                    'timestamp': timestamp,
                    'datetime': timestamp,
                    'open': float(values['1. open']),
                    'high': float(values['2. high']), 
                    'low': float(values['3. low']),
                    'close': float(values['4. close']),
                    'volume': int(values['5. volume']),
                    'api_source': 'Alpha Vantage',
                    'interval': '5min'
                })
            
            # Sort by timestamp (most recent first)
            results.sort(key=lambda x: x['timestamp'], reverse=True)
            
            print(f"   ✅ {symbol}: {len(results)} recent 5-minute intervals")
            return results
            
        elif 'Information' in data:
            print(f"   ⚠️  Rate limit: {data['Information']}")
            return []
        else:
            print(f"   ⚠️  Unexpected response: {list(data.keys())}")
            return []
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []


def get_crypto_recent_data(crypto_id: str):
    """Get recent crypto data with minute-level resolution"""
    print(f"🪙 Fetching recent {crypto_id} data...")
    
    try:
        # Use CoinGecko with 1-day chart for minute-level data
        url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}/market_chart"
        params = {
            'vs_currency': 'usd',
            'days': '1',  # Last 24 hours
            'interval': 'minutely'
        }
        
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        if 'prices' in data:
            prices = data['prices']
            volumes = data.get('total_volumes', [])
            
            results = []
            # Get last 100 data points (about 1.5 hours of minute data)
            for i, price_data in enumerate(prices[-100:]):
                timestamp_ms = price_data[0]
                price = price_data[1]
                
                dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
                volume = volumes[-(100-i)][1] if i < len(volumes) else 0
                
                results.append({
                    'symbol': crypto_id.upper(),
                    'timestamp': dt.strftime('%Y-%m-%d %H:%M:%S UTC'),
                    'datetime': dt,
                    'price': price,
                    'volume': volume,
                    'api_source': 'CoinGecko',
                    'interval': 'minutely'
                })
            
            results.sort(key=lambda x: x['datetime'], reverse=True)
            print(f"   ✅ {crypto_id}: {len(results)} minute data points")
            return results
            
        else:
            print(f"   ⚠️  No price data for {crypto_id}")
            return []
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []


def collect_smart_intraday_data():
    """Smart collection that adapts to market conditions"""
    
    config = get_config()
    
    # Determine target date
    yesterday = datetime.now().date() - timedelta(days=1)
    last_trading_day = get_last_trading_day()
    
    print("🧠 SMART INTRADAY DATA COLLECTOR")
    print("=" * 60)
    print(f"📅 Yesterday: {yesterday} ({'Trading Day' if is_trading_day(yesterday) else 'Weekend/Holiday'})")
    print(f"📈 Last Trading Day: {last_trading_day}")
    
    if yesterday != last_trading_day:
        print(f"⚠️  Yesterday was not a trading day, using {last_trading_day}")
    
    all_data = {
        'collection_time': datetime.now(timezone.utc).isoformat(),
        'target_date': str(yesterday),
        'actual_data_date': str(last_trading_day),
        'is_weekend_data': yesterday != last_trading_day,
        'stocks': [],
        'crypto': []
    }
    
    # Collect recent stock data
    print(f"\n📈 Collecting Recent Stock Data...")
    stock_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
    
    for symbol in stock_symbols:
        stock_data = get_recent_intraday_data(symbol, config.api.alpha_vantage_api_key)
        all_data['stocks'].extend(stock_data)
        time.sleep(12)  # Rate limiting
        
        if not stock_data:
            print("   ⚠️  Stopping due to rate limits")
            break
    
    # Collect recent crypto data (works 24/7)
    print(f"\n🪙 Collecting Recent Crypto Data...")
    crypto_symbols = ['bitcoin', 'ethereum', 'cardano', 'solana']
    
    for crypto_id in crypto_symbols:
        crypto_data = get_crypto_recent_data(crypto_id)
        all_data['crypto'].extend(crypto_data)
        time.sleep(2)  # Conservative rate limiting
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"smart_intraday_data_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(all_data, f, indent=2, default=str)
    
    print(f"\n💾 COLLECTION SUMMARY:")
    print(f"   📈 Stock records: {len(all_data['stocks'])}")
    print(f"   🪙 Crypto records: {len(all_data['crypto'])}")
    print(f"   📄 Saved to: {filename}")
    
    return all_data, filename


def analyze_minute_patterns(data):
    """Analyze minute-level trading patterns"""
    
    print(f"\n📊 MINUTE-LEVEL PATTERN ANALYSIS")
    print("=" * 45)
    
    # Stock analysis
    if data['stocks']:
        print(f"📈 Stock Intraday Patterns:")
        
        for symbol in set(record['symbol'] for record in data['stocks']):
            symbol_data = [r for r in data['stocks'] if r['symbol'] == symbol]
            symbol_data.sort(key=lambda x: x['timestamp'])
            
            if len(symbol_data) >= 10:  # Need sufficient data
                latest = symbol_data[-1]
                oldest = symbol_data[0]
                
                # Calculate recent performance
                change = latest['close'] - oldest['close']
                change_pct = (change / oldest['close']) * 100
                
                # Volume analysis
                avg_volume = sum(r['volume'] for r in symbol_data) / len(symbol_data)
                
                # Volatility (price range)
                highs = [r['high'] for r in symbol_data]
                lows = [r['low'] for r in symbol_data]
                volatility = (max(highs) - min(lows)) / oldest['close'] * 100
                
                print(f"\n   {symbol} ({len(symbol_data)} intervals):")
                print(f"     Recent Change: {change_pct:+.2f}% (${change:+.2f})")
                print(f"     Price Range: ${min(lows):.2f} - ${max(highs):.2f}")
                print(f"     Volatility: {volatility:.2f}%")
                print(f"     Avg Volume/5min: {avg_volume:,.0f}")
                print(f"     Latest: {latest['timestamp']} @ ${latest['close']:.2f}")
    
    # Crypto analysis
    if data['crypto']:
        print(f"\n🪙 Crypto Minute Patterns:")
        
        for symbol in set(record['symbol'] for record in data['crypto']):
            symbol_data = [r for r in data['crypto'] if r['symbol'] == symbol]
            symbol_data.sort(key=lambda x: x['datetime'])
            
            if len(symbol_data) >= 10:
                latest = symbol_data[-1]
                oldest = symbol_data[0]
                
                change = latest['price'] - oldest['price']
                change_pct = (change / oldest['price']) * 100
                
                # Price volatility
                prices = [r['price'] for r in symbol_data]
                volatility = (max(prices) - min(prices)) / oldest['price'] * 100
                
                print(f"\n   {symbol} ({len(symbol_data)} minutes):")
                print(f"     Recent Change: {change_pct:+.2f}% (${change:+.2f})")
                print(f"     Price Range: ${min(prices):.2f} - ${max(prices):.2f}")
                print(f"     Volatility: {volatility:.2f}%")
                print(f"     Latest: {latest['timestamp']} @ ${latest['price']:.2f}")


def main():
    """Main execution with intelligent data collection"""
    
    print("🎯 MINUTE-LEVEL DATA COLLECTION FOR TRADING ANALYSIS")
    print("=" * 70)
    
    # Collect data intelligently
    data, filename = collect_smart_intraday_data()
    
    # Analyze patterns
    analyze_minute_patterns(data)
    
    # Provide recommendations
    print(f"\n💡 RECOMMENDATIONS FOR MINUTE-LEVEL DATA:")
    print("=" * 50)
    
    print("🎯 For True Yesterday Minute Data:")
    print("   1️⃣ Run on weekdays (Mon-Fri) for stock minute data")
    print("   2️⃣ Use premium Alpha Vantage for historical minute data")
    print("   3️⃣ Consider Polygon.io or IEX Cloud for minute history")
    
    print(f"\n🚀 For Real-Time Minute Streams:")
    print("   1️⃣ WebSocket connections during market hours")
    print("   2️⃣ Scheduled collection every minute during 9:30-16:00 ET")
    print("   3️⃣ Store in time-series database (InfluxDB, TimescaleDB)")
    
    print(f"\n📊 Current Data Quality:")
    if data.get('is_weekend_data'):
        print("   ⚠️  Weekend data - showing last trading day instead")
    print(f"   📈 Stock intervals: 5-minute resolution")
    print(f"   🪙 Crypto intervals: 1-minute resolution")
    
    print(f"\n🎉 Smart intraday collection complete!")
    print(f"📄 Data file: {filename}")


if __name__ == "__main__":
    main()