"""
Multi-Source Crypto Minute Data Collector
=========================================

Author: Shck Tchamna (tchamna@gmail.com)

This collector uses multiple free APIs to get minute-level crypto data
for yesterday, working around API limitations.
"""

import requests
import json
from datetime import datetime, timedelta, timezone
import time
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PipelineConfig

# Initialize pipeline configuration
pipeline_config = PipelineConfig()
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config


def get_binance_minute_data(symbol: str, target_date: str):
    """Get minute data from Binance API (free, unlimited)"""
    print(f"🔸 Binance: Fetching {symbol} minute data for {target_date}...")
    
    try:
        # Use centralized symbol mappings from config
        binance_symbol = pipeline_config.crypto_mappings.get_binance_symbol(symbol)
        
        if binance_symbol is None:
            print(f"   ⚠️  {symbol} not available on Binance")
            return []
        
        # Calculate timestamp range for target date
        target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        start_time = int(target_dt.timestamp() * 1000)
        end_time = int((target_dt + timedelta(days=1)).timestamp() * 1000)
        
        url = "https://api.binance.com/api/v3/klines"
        params = {
            'symbol': binance_symbol,
            'interval': '1m',  # 1-minute intervals
            'startTime': start_time,
            'endTime': end_time,
            'limit': 1440  # Max 1440 minutes in a day
        }
        
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        if isinstance(data, list):
            results = []
            for kline in data:
                timestamp_ms = kline[0]
                dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
                
                results.append({
                    'symbol': symbol.upper(),
                    'timestamp': dt.strftime('%Y-%m-%d %H:%M:%S UTC'),
                    'datetime': dt,
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5]),
                    'api_source': 'Binance',
                    'interval': '1min'
                })
            
            print(f"   ✅ Binance: {len(results)} minute data points")
            return results
        
        else:
            print(f"   ❌ Binance error: {data}")
            return []
            
    except Exception as e:
        print(f"   ❌ Binance error: {e}")
        return []


def get_cryptocompare_minute_data(symbol: str, target_date: str):
    """Get minute data from CryptoCompare API (free backup)"""
    print(f"🔹 CryptoCompare: Fetching {symbol} data for {target_date}...")
    
    try:
        # Use centralized symbol mappings from config
        cc_symbol = pipeline_config.crypto_mappings.get_cryptocompare_symbol(symbol)
        
        if cc_symbol is None:
            print(f"   ⚠️  {symbol} not available on CryptoCompare")
            return []
        
        # Calculate how many days ago the target date was
        target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        days_ago = (datetime.now().date() - target_dt.date()).days
        
        url = "https://min-api.cryptocompare.com/data/v2/histominute"
        params = {
            'fsym': cc_symbol,
            'tsym': 'USD',
            'limit': 1440,  # 1440 minutes = 24 hours
            'toTs': int((target_dt + timedelta(days=1)).timestamp())
        }
        
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        if data.get('Response') == 'Success':
            hist_data = data['Data']['Data']
            
            results = []
            for point in hist_data:
                timestamp = point['time']
                dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                
                # Filter for target date
                if dt.date() == target_dt.date():
                    results.append({
                        'symbol': symbol.upper(),
                        'timestamp': dt.strftime('%Y-%m-%d %H:%M:%S UTC'),
                        'datetime': dt,
                        'open': float(point['open']),
                        'high': float(point['high']),
                        'low': float(point['low']),
                        'close': float(point['close']),
                        'volume': float(point.get('volumeto', 0)),
                        'api_source': 'CryptoCompare',
                        'interval': '1min'
                    })
            
            print(f"   ✅ CryptoCompare: {len(results)} minute data points")
            return results
            
        else:
            print(f"   ❌ CryptoCompare error: {data.get('Message', 'Unknown error')}")
            return []
            
    except Exception as e:
        print(f"   ❌ CryptoCompare error: {e}")
        return []


def get_kraken_minute_data(symbol: str, target_date: str):
    """Get minute data from Kraken API (free alternative)"""
    print(f"🔷 Kraken: Fetching {symbol} data for {target_date}...")
    
    try:
        # Use centralized symbol mappings from config
        kraken_symbol = pipeline_config.crypto_mappings.get_kraken_symbol(symbol)
        
        if kraken_symbol is None:
            print(f"   ⚠️  {symbol} not available on Kraken")
            return []
        
        # Kraken uses different time windows
        target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        since_timestamp = int(target_dt.timestamp())
        
        url = "https://api.kraken.com/0/public/OHLC"
        params = {
            'pair': kraken_symbol,
            'interval': 1,  # 1-minute intervals
            'since': since_timestamp
        }
        
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        if 'error' not in data or not data['error']:
            result_key = list(data['result'].keys())[0]  # First key is the pair data
            ohlc_data = data['result'][result_key]
            
            results = []
            for ohlc in ohlc_data:
                timestamp = ohlc[0]
                dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                
                # Filter for target date
                if dt.date() == target_dt.date():
                    results.append({
                        'symbol': symbol.upper(),
                        'timestamp': dt.strftime('%Y-%m-%d %H:%M:%S UTC'),
                        'datetime': dt,
                        'open': float(ohlc[1]),
                        'high': float(ohlc[2]),
                        'low': float(ohlc[3]),
                        'close': float(ohlc[4]),
                        'volume': float(ohlc[6]),
                        'api_source': 'Kraken',
                        'interval': '1min'
                    })
            
            print(f"   ✅ Kraken: {len(results)} minute data points")
            return results[:1440]  # Limit to 1 day
            
        else:
            print(f"   ❌ Kraken error: {data.get('error', 'Unknown error')}")
            return []
            
    except Exception as e:
        print(f"   ❌ Kraken error: {e}")
        return []


def collect_multi_source_crypto_minutes(symbols=None):
    """Collect minute data using multiple free APIs"""
    
    # Get symbols from config if not provided
    if symbols is None:
        configured_symbols = pipeline_config.processing.crypto_symbols
        
        # Use centralized symbol mappings from config
        crypto_symbols = []
        for ticker in configured_symbols:
            api_symbol = pipeline_config.crypto_mappings.get_api_symbol(ticker)
            if api_symbol:
                crypto_symbols.append(api_symbol)
            else:
                print(f"⚠️ Unknown symbol mapping for {ticker}, skipping...")
        
        print(f"📊 Configured symbols: {configured_symbols}")
        print(f"🔄 API symbols: {crypto_symbols}")
    else:
        crypto_symbols = symbols
    
    # Calculate yesterday's date
    yesterday = datetime.now() - timedelta(days=1)
    target_date = yesterday.strftime('%Y-%m-%d')
    
    print("🎯 MULTI-SOURCE CRYPTO MINUTE DATA COLLECTOR")
    print("=" * 70)
    print(f"📅 Target Date: {target_date}")
    print(f"🎯 Goal: 1,440 minutes of data (24 hours)")
    print(f"🔄 Using multiple free APIs to maximize coverage")
    print(f"🪙 Symbols to collect: {len(crypto_symbols)}")
    
    all_data = {
        'collection_time': datetime.now(timezone.utc).isoformat(),
        'target_date': target_date,
        'resolution': 'minute',
        'data_sources': ['Binance', 'CryptoCompare', 'Kraken'],
        'crypto_data': []
    }
    
    print(f"\n🪙 Collecting Minute Data from Multiple Sources...")
    print("-" * 60)
    
    for symbol in crypto_symbols:
        print(f"\n💰 Processing {symbol.upper()}:")
        
        # Try each API source
        symbol_data = []
        
        # Source 1: Binance (usually best)
        binance_data = get_binance_minute_data(symbol, target_date)
        if binance_data:
            symbol_data.extend(binance_data)
        
        time.sleep(0.5)  # Rate limiting
        
        # Source 2: CryptoCompare (backup)
        if len(symbol_data) < 100:  # If Binance didn't provide enough data
            cc_data = get_cryptocompare_minute_data(symbol, target_date)
            if cc_data:
                symbol_data.extend(cc_data)
        
        time.sleep(0.5)
        
        # Source 3: Kraken (alternative)
        if len(symbol_data) < 100:  # If still not enough data
            kraken_data = get_kraken_minute_data(symbol, target_date)
            if kraken_data:
                symbol_data.extend(kraken_data)
        
        # Add to main collection
        all_data['crypto_data'].extend(symbol_data)
        
        print(f"   📊 Total collected for {symbol}: {len(symbol_data)} minutes")
        
        time.sleep(1)  # Be nice to APIs
    
    # Save results
    filename = f"crypto_minute_data_{target_date.replace('-', '')}.json"
    with open(filename, 'w') as f:
        json.dump(all_data, f, indent=2, default=str)
    
    print(f"\n💾 COLLECTION SUMMARY:")
    print("=" * 30)
    total_records = len(all_data['crypto_data'])
    unique_symbols = len(set(r['symbol'] for r in all_data['crypto_data']))
    
    print(f"   💰 Total minute records: {total_records}")
    print(f"   🪙 Unique symbols: {unique_symbols}")
    print(f"   📄 Saved to: {filename}")
    
    # Show breakdown by symbol
    for symbol in set(r['symbol'] for r in all_data['crypto_data']):
        count = len([r for r in all_data['crypto_data'] if r['symbol'] == symbol])
        print(f"   📊 {symbol}: {count} minutes")
    
    return all_data, filename


def analyze_minute_crypto_data(data):
    """Analyze the minute-level crypto data"""
    
    print(f"\n📈 MINUTE-LEVEL CRYPTO ANALYSIS")
    print("=" * 45)
    
    target_date = data['target_date']
    crypto_data = data['crypto_data']
    
    if not crypto_data:
        print("❌ No crypto minute data available")
        return
    
    for symbol in set(record['symbol'] for record in crypto_data):
        symbol_data = [r for r in crypto_data if r['symbol'] == symbol]
        symbol_data.sort(key=lambda x: x['timestamp'])
        
        if len(symbol_data) >= 10:
            first = symbol_data[0]
            last = symbol_data[-1]
            
            # Calculate full day performance
            day_change = last['close'] - first['open']
            day_change_pct = (day_change / first['open']) * 100
            
            # Get high/low for the day
            highs = [r['high'] for r in symbol_data]
            lows = [r['low'] for r in symbol_data] 
            day_high = max(highs)
            day_low = min(lows)
            
            # Volume analysis
            total_volume = sum(r.get('volume', 0) for r in symbol_data)
            avg_volume_per_minute = total_volume / len(symbol_data)
            
            # Volatility
            volatility = (day_high - day_low) / first['open'] * 100
            
            print(f"\n💰 {symbol} ({len(symbol_data)} minutes on {target_date}):")
            print(f"   📊 Day Performance: {day_change_pct:+.2f}% (${day_change:+.2f})")
            print(f"   📈 Price Range: ${day_low:.2f} → ${day_high:.2f}")
            print(f"   ⚡ Volatility: {volatility:.2f}%")
            print(f"   💹 Total Volume: {total_volume:,.0f}")
            print(f"   ⏰ Data Coverage: {first['timestamp']} → {last['timestamp']}")
            print(f"   🔄 API Source: {symbol_data[0]['api_source']}")


def main():
    """Main execution for multi-source crypto minute collection"""
    
    print("⏰ GETTING EVERY MINUTE OF YESTERDAY'S CRYPTO DATA")
    print("=" * 70)
    
    # Collect data
    data, filename = collect_multi_source_crypto_minutes()
    
    # Analyze data
    analyze_minute_crypto_data(data)
    
    # Success summary
    print(f"\n🎉 SUCCESS! Crypto Minute Data Collection Complete")
    print("=" * 55)
    print(f"📄 File: {filename}")
    print(f"💰 You now have minute-by-minute crypto data for yesterday!")
    print(f"📊 Use this for intraday analysis, volatility studies, etc.")
    
    # Next steps
    print(f"\n🚀 NEXT STEPS:")
    print("1️⃣ Analyze the minute patterns in the saved JSON file")
    print("2️⃣ Set up automated collection for ongoing minute data")
    print("3️⃣ For stocks: Wait for weekday or upgrade to premium API")


if __name__ == "__main__":
    main()