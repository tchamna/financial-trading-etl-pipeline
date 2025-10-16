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


def collect_multi_source_crypto_minutes(symbols=None, target_date=None):
    """
    Collect minute data using multiple free APIs
    
    Args:
        symbols: List of crypto symbols to collect (uses config if None)
        target_date: Date string in 'YYYY-MM-DD' format (uses yesterday if None)
    """
    
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
    
    # Use provided date or default to yesterday
    if target_date is None:
        yesterday = datetime.now() - timedelta(days=1)
        target_date = yesterday.strftime('%Y-%m-%d')
    else:
        # Strictly validate date format: YYYY-MM-DD
        try:
            # Check format with regex first
            import re
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', target_date):
                raise ValueError(f"Invalid date format: '{target_date}'. Must be YYYY-MM-DD (e.g., 2025-10-12)")
            
            # Validate it's a real date
            parsed_date = datetime.strptime(target_date, '%Y-%m-%d')
            
            # Check if date is not in the future
            if parsed_date.date() > datetime.now().date():
                raise ValueError(f"Date {target_date} is in the future. Please provide a past or current date.")
                
        except ValueError as e:
            raise ValueError(f"Invalid date: {str(e)}")
    
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
    
    # NOTE: File saving moved to main() function to support combined crypto+stock data
    # This function now just returns data for the caller to handle
    
    print(f"\n💾 COLLECTION SUMMARY:")
    print("=" * 30)
    total_records = len(all_data['crypto_data'])
    unique_symbols = len(set(r['symbol'] for r in all_data['crypto_data']))
    
    print(f"   💰 Total minute records: {total_records}")
    print(f"   🪙 Unique symbols: {unique_symbols}")
    
    # Show breakdown by symbol
    for symbol in set(r['symbol'] for r in all_data['crypto_data']):
        count = sum(1 for r in all_data['crypto_data'] if r['symbol'] == symbol)
        print(f"   📊 {symbol}: {count} minutes")
    
    return all_data  # Return data only, file saving happens in main() or caller


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


def main(target_date=None):
    """
    Main execution for multi-source crypto + stock minute collection
    
    Args:
        target_date: Date string in 'YYYY-MM-DD' format (uses yesterday if None)
    """
    
    # Display the date being collected
    if target_date:
        print(f"⏰ COLLECTING FINANCIAL DATA (CRYPTO + STOCKS) FOR {target_date}")
    else:
        print("⏰ COLLECTING FINANCIAL DATA (CRYPTO + STOCKS) FOR YESTERDAY")
    print("=" * 70)
    
    # Use yesterday if no date provided
    if target_date is None:
        from datetime import datetime, timedelta
        yesterday = datetime.now() - timedelta(days=1)
        target_date = yesterday.strftime('%Y-%m-%d')
    
    # Collect crypto data
    print("\n🪙 COLLECTING CRYPTOCURRENCY DATA...")
    crypto_data = collect_multi_source_crypto_minutes(target_date=target_date)
    
    # Collect stock data
    print("\n📈 COLLECTING STOCK DATA...")
    try:
        # Import stock collector
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from scripts.stock_minute_collector import collect_stock_minute_data
        
        # Get config for API key and symbols
        config = get_config()
        stock_data_result = collect_stock_minute_data(
            symbols=config.processing.stock_symbols,
            api_key=config.api.alpha_vantage_api_key,
            target_date=target_date
        )
        stock_data = stock_data_result['stocks']
        print(f"✅ Stock collection complete: {len(stock_data)} records")
    except Exception as e:
        print(f"⚠️  Stock collection failed: {e}")
        print("   (This is normal if markets are closed or API limits reached)")
        stock_data = []
        stock_data_result = {'stocks': [], 'total_records': 0, 'successful_symbols': [], 'failed_symbols': []}
    
    # Combine data into new format
    combined_data = {
        'collection_date': target_date,
        'crypto_data': crypto_data if isinstance(crypto_data, list) else crypto_data.get('crypto_data', []),
        'stock_data': stock_data,
        'summary': {
            'crypto_records': len(crypto_data) if isinstance(crypto_data, list) else len(crypto_data.get('crypto_data', [])),
            'stock_records': len(stock_data),
            'total_records': (len(crypto_data) if isinstance(crypto_data, list) else len(crypto_data.get('crypto_data', []))) + len(stock_data),
            'crypto_symbols': len(config.processing.crypto_symbols),
            'stock_symbols_successful': len(stock_data_result['successful_symbols']),
            'stock_symbols_failed': stock_data_result['failed_symbols']
        }
    }
    
    # Save combined data with NEW filename format
    data_dir = config.storage.local_data_directory
    os.makedirs(data_dir, exist_ok=True)
    
    filename = f"financial_minute_data_{target_date.replace('-', '')}.json"
    filepath = os.path.join(data_dir, filename)
    
    with open(filepath, 'w') as f:
        import json
        json.dump(combined_data, f, indent=2, default=str)
    
    # Analyze crypto data
    analyze_minute_crypto_data(crypto_data if isinstance(crypto_data, list) else crypto_data.get('crypto_data', []))
    
    # Success summary
    print(f"\n🎉 SUCCESS! Financial Data Collection Complete")
    print("=" * 60)
    print(f"� File: {filename}")
    print(f"�📊 Summary:")
    print(f"   🪙 Crypto: {combined_data['summary']['crypto_records']:,} records from {combined_data['summary']['crypto_symbols']} coins")
    print(f"   📈 Stocks: {combined_data['summary']['stock_records']:,} records from {len(stock_data_result['successful_symbols'])} stocks")
    print(f"   💰 Total: {combined_data['summary']['total_records']:,} minute-level data points!")
    
    if stock_data_result['failed_symbols']:
        print(f"\n⚠️  Failed stocks: {', '.join(stock_data_result['failed_symbols'])}")
        print("   (Normal if markets closed or API limits reached)")
    
    # Next steps
    print(f"\n🚀 NEXT STEPS:")
    print("1️⃣ Data saved to both JSON and will be uploaded to S3")
    print("2️⃣ Airflow will run this automatically every 6 hours")
    print("3️⃣ Stock data available during market hours (Mon-Fri 9:30-4PM EST)")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Collect minute-level crypto data from multiple free APIs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Collect data for yesterday (default)
  python crypto_minute_collector.py
  
  # Collect data for a specific date (multiple ways)
  python crypto_minute_collector.py 2025-10-12
  python crypto_minute_collector.py --date 2025-10-12
  python crypto_minute_collector.py -d 2025-10-01
        '''
    )
    
    parser.add_argument(
        'date',
        nargs='?',
        default=None,
        help='Target date in YYYY-MM-DD format (default: yesterday)'
    )
    
    parser.add_argument(
        '-d', '--date-flag',
        dest='date_flag',
        type=str,
        default=None,
        help='Alternative: Target date in YYYY-MM-DD format (default: yesterday)'
    )
    
    args = parser.parse_args()
    
    # Use positional argument if provided, otherwise use flag argument
    target_date = args.date or args.date_flag
    
    try:
        main(target_date=target_date)
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        print("Please use date format: YYYY-MM-DD (e.g., 2025-10-12)")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)