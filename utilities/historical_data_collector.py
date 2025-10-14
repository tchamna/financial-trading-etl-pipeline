"""
Historical Data Collector for Financial Trading ETL Pipeline
===========================================================

Author: Shck Tchamna (tchamna@gmail.com)

This script collects historical financial data for analysis and comparison.
Supports both Alpha Vantage and CoinGecko APIs for comprehensive data collection.
"""

import os
import sys
import requests
import pandas as pd
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import time

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config
from scripts.s3_data_uploader import create_s3_uploader_from_env


class HistoricalDataCollector:
    """Collects historical financial data for analysis and comparison"""
    
    def __init__(self):
        self.config = get_config()
        self.alpha_vantage_key = self.config.api.alpha_vantage_api_key
        
        # Initialize S3 uploader if enabled
        self.s3_uploader = None
        if self.config.s3.enabled:
            try:
                self.s3_uploader = create_s3_uploader_from_env()
                print("✅ S3 uploader initialized")
            except Exception as e:
                print(f"⚠️  S3 uploader failed to initialize: {e}")
    
    def get_yesterday_stock_data(self, symbol: str) -> Optional[Dict]:
        """Get yesterday's stock data from Alpha Vantage"""
        print(f"📈 Fetching yesterday's data for {symbol}...")
        
        try:
            # Use DAILY time series for historical data
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': symbol,
                'apikey': self.alpha_vantage_key,
                'outputsize': 'compact'  # Last 100 days
            }
            
            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            
            if 'Time Series (Daily)' in data:
                time_series = data['Time Series (Daily)']
                
                # Get yesterday's date
                yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                
                # Find the most recent trading day (could be Friday if today is Monday)
                available_dates = sorted(time_series.keys(), reverse=True)
                recent_date = available_dates[0] if available_dates else None
                
                if recent_date:
                    recent_data = time_series[recent_date]
                    return {
                        'symbol': symbol,
                        'date': recent_date,
                        'open': float(recent_data['1. open']),
                        'high': float(recent_data['2. high']),
                        'low': float(recent_data['3. low']),
                        'close': float(recent_data['4. close']),
                        'volume': int(recent_data['5. volume']),
                        'api_source': 'Alpha Vantage',
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
            
            print(f"   ⚠️  No daily data found for {symbol}")
            return None
            
        except Exception as e:
            print(f"   ❌ Error fetching {symbol}: {e}")
            return None
    
    def get_historical_crypto_data(self, days_back: int = 1) -> List[Dict]:
        """Get historical crypto data from CoinGecko"""
        print(f"🪙 Fetching {days_back} days of crypto historical data...")
        
        try:
            # CoinGecko historical data endpoint
            crypto_data = []
            
            for crypto_id in self.config.processing.crypto_symbols:
                print(f"   📊 Processing {crypto_id}...")
                
                url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}/history"
                
                # Get data from yesterday
                yesterday = datetime.now() - timedelta(days=days_back)
                date_param = yesterday.strftime('%d-%m-%Y')
                
                params = {
                    'date': date_param,
                    'localization': 'false'
                }
                
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'market_data' in data:
                        market_data = data['market_data']
                        
                        record = {
                            'symbol': data.get('symbol', '').upper(),
                            'name': data.get('name', ''),
                            'date': date_param,
                            'current_price': market_data.get('current_price', {}).get('usd', 0),
                            'market_cap': market_data.get('market_cap', {}).get('usd', 0),
                            'volume_24h': market_data.get('total_volume', {}).get('usd', 0),
                            'price_change_24h': market_data.get('price_change_24h', {}).get('usd', 0),
                            'price_change_percentage_24h': market_data.get('price_change_percentage_24h', {}).get('usd', 0),
                            'api_source': 'CoinGecko Historical',
                            'timestamp': datetime.now(timezone.utc).isoformat()
                        }
                        
                        crypto_data.append(record)
                        print(f"   ✅ {record['symbol']}: ${record['current_price']:.2f}")
                
                # Rate limiting
                time.sleep(1.2)  # CoinGecko rate limit is 50 calls/minute
            
            return crypto_data
            
        except Exception as e:
            print(f"❌ Error fetching historical crypto data: {e}")
            return []
    
    def get_current_vs_historical_comparison(self) -> Dict:
        """Compare current prices with historical data"""
        print("\n📊 CURRENT vs HISTORICAL COMPARISON")
        print("=" * 60)
        
        comparison_data = {
            'stocks': [],
            'crypto': [],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Get current stock data (limited sample to avoid API limits)
        current_stocks = ['AAPL', 'MSFT', 'GOOGL']
        for symbol in current_stocks:
            # Current data
            current = self.get_current_stock_price(symbol)
            # Historical data
            historical = self.get_yesterday_stock_data(symbol)
            
            if current and historical:
                comparison = {
                    'symbol': symbol,
                    'current_price': current['price'],
                    'historical_price': historical['close'],
                    'price_change': current['price'] - historical['close'],
                    'price_change_percentage': ((current['price'] - historical['close']) / historical['close']) * 100,
                    'current_volume': current.get('volume', 0),
                    'historical_volume': historical['volume'],
                    'current_timestamp': current['timestamp'],
                    'historical_date': historical['date']
                }
                comparison_data['stocks'].append(comparison)
                
                print(f"📈 {symbol}:")
                print(f"   Current: ${current['price']:.2f}")
                print(f"   Historical ({historical['date']}): ${historical['close']:.2f}")
                print(f"   Change: ${comparison['price_change']:.2f} ({comparison['price_change_percentage']:.2f}%)")
            
            time.sleep(0.5)  # Rate limiting
        
        return comparison_data
    
    def get_current_stock_price(self, symbol: str) -> Optional[Dict]:
        """Get current stock price for comparison"""
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.alpha_vantage_key
            }
            
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            if 'Global Quote' in data:
                quote = data['Global Quote']
                return {
                    'symbol': symbol,
                    'price': float(quote['05. price']),
                    'volume': int(quote['06. volume']),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            
        except Exception as e:
            print(f"Error getting current price for {symbol}: {e}")
        
        return None
    
    def collect_batch_historical_data(self, days_back: int = 1) -> Dict:
        """Collect all historical data in one batch"""
        print(f"\n🚀 COLLECTING BATCH HISTORICAL DATA ({days_back} days back)")
        print("=" * 70)
        
        batch_data = {
            'collection_timestamp': datetime.now(timezone.utc).isoformat(),
            'days_back': days_back,
            'stocks': [],
            'crypto': []
        }
        
        # Collect stock data for all configured symbols
        print("\n📈 Collecting Stock Data...")
        for symbol in self.config.processing.stock_symbols[:5]:  # Limit to avoid API limits
            stock_data = self.get_yesterday_stock_data(symbol)
            if stock_data:
                batch_data['stocks'].append(stock_data)
            time.sleep(0.3)  # Rate limiting
        
        # Collect crypto data
        print(f"\n🪙 Collecting Crypto Data...")
        crypto_data = self.get_historical_crypto_data(days_back)
        batch_data['crypto'] = crypto_data
        
        # Save to file
        filename = f"historical_data_{days_back}days_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(batch_data, f, indent=2)
        
        print(f"\n💾 Saved to: {filename}")
        
        # Upload to S3 if enabled
        if self.s3_uploader:
            try:
                s3_path = f"analytics/historical_comparison/{filename}"
                # Convert to list format for S3 uploader
                combined_data = batch_data['stocks'] + batch_data['crypto']
                s3_result = self.s3_uploader.upload_json_data(
                    combined_data, 
                    s3_path, 
                    compress=True
                )
                print(f"☁️  Uploaded to S3: {s3_result}")
            except Exception as e:
                print(f"⚠️  S3 upload failed: {e}")
        
        return batch_data
    
    def api_comparison_analysis(self) -> Dict:
        """Compare data quality and coverage between APIs"""
        print(f"\n🔍 API COMPARISON ANALYSIS")
        print("=" * 50)
        
        analysis = {
            'alpha_vantage': {
                'data_type': 'Stocks',
                'update_frequency': 'Real-time / Daily',
                'rate_limits': '25 calls/day (free), 500/day (premium)',
                'data_fields': ['OHLCV', 'Technical Indicators', 'Fundamental Data'],
                'historical_depth': '20+ years',
                'coverage': '4000+ US stocks, ETFs, mutual funds',
                'pros': ['High accuracy', 'Technical indicators', 'Fundamental data'],
                'cons': ['Rate limited', 'Paid tiers', 'US-focused']
            },
            'coingecko': {
                'data_type': 'Cryptocurrency',
                'update_frequency': 'Real-time',
                'rate_limits': '50 calls/minute (free)',
                'data_fields': ['Price', 'Market Cap', 'Volume', 'Supply', 'Rankings'],
                'historical_depth': '8+ years',
                'coverage': '14000+ cryptocurrencies',
                'pros': ['Free tier generous', 'Global coverage', 'Rich metadata'],
                'cons': ['Crypto only', 'No traditional assets', 'Less technical analysis']
            }
        }
        
        print("📊 Alpha Vantage (Stocks):")
        print(f"   ✅ Coverage: {analysis['alpha_vantage']['coverage']}")
        print(f"   ✅ Historical: {analysis['alpha_vantage']['historical_depth']}")
        print(f"   ⚠️  Rate Limits: {analysis['alpha_vantage']['rate_limits']}")
        
        print("\n🪙 CoinGecko (Crypto):")
        print(f"   ✅ Coverage: {analysis['coingecko']['coverage']}")
        print(f"   ✅ Rate Limits: {analysis['coingecko']['rate_limits']}")
        print(f"   ✅ Historical: {analysis['coingecko']['historical_depth']}")
        
        return analysis


def main():
    """Main execution function"""
    collector = HistoricalDataCollector()
    
    print("🎯 HISTORICAL FINANCIAL DATA COLLECTOR")
    print("=" * 60)
    
    # Collect batch historical data
    historical_data = collector.collect_batch_historical_data(days_back=1)
    
    print(f"\n📊 COLLECTION SUMMARY:")
    print(f"   📈 Stocks collected: {len(historical_data['stocks'])}")
    print(f"   🪙 Crypto collected: {len(historical_data['crypto'])}")
    
    # API comparison
    api_analysis = collector.api_comparison_analysis()
    
    # Current vs Historical comparison (limited sample)
    try:
        comparison = collector.get_current_vs_historical_comparison()
        print(f"\n📈 Price Changes (Current vs Historical):")
        for stock in comparison['stocks']:
            print(f"   {stock['symbol']}: {stock['price_change_percentage']:.2f}%")
    except Exception as e:
        print(f"⚠️  Comparison analysis failed: {e}")
    
    print(f"\n🎉 Historical data collection complete!")


if __name__ == "__main__":
    main()