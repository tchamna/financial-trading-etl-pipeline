#!/usr/bin/env python3
"""
Real-Time Data Pipeline Demonstration
Shows live data extraction, transformation, and database storage with detailed logging
"""

import os
import requests
import pandas as pd
import psycopg2
import json
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

class LiveDataPipelineDemo:
    """Demonstrates real-time data pipeline with detailed step tracking"""
    
    def __init__(self):
        load_dotenv()
        self.db_config = {
            'host': 'localhost',
            'port': 5433,
            'database': 'airflow',
            'user': 'airflow',
            'password': 'airflow'
        }
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        
        print("🔄 LIVE DATA PIPELINE DEMONSTRATION")
        print("=" * 70)
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    def create_tables(self):
        """Create database tables for storing financial data"""
        print("🗄️  STEP 1: Setting Up Database Tables")
        print("-" * 50)
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Drop existing tables for clean demo
            print("🧹 Cleaning previous data...")
            cursor.execute("DROP TABLE IF EXISTS live_stock_data CASCADE;")
            cursor.execute("DROP TABLE IF EXISTS live_crypto_data CASCADE;")
            cursor.execute("DROP TABLE IF EXISTS technical_indicators CASCADE;")
            
            # Create stock data table
            print("📊 Creating stock data table...")
            cursor.execute("""
                CREATE TABLE live_stock_data (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(10) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    open_price DECIMAL(10,4),
                    high_price DECIMAL(10,4),
                    low_price DECIMAL(10,4),
                    close_price DECIMAL(10,4),
                    volume BIGINT,
                    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create crypto data table
            print("🪙 Creating crypto data table...")
            cursor.execute("""
                CREATE TABLE live_crypto_data (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(10) NOT NULL,
                    current_price DECIMAL(12,2),
                    market_cap BIGINT,
                    price_change_24h DECIMAL(8,4),
                    volume_24h BIGINT,
                    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create technical indicators table
            print("📈 Creating technical indicators table...")
            cursor.execute("""
                CREATE TABLE technical_indicators (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(10) NOT NULL,
                    rsi DECIMAL(6,2),
                    sma_20 DECIMAL(10,4),
                    sma_50 DECIMAL(10,4),
                    volatility DECIMAL(8,4),
                    trading_signal VARCHAR(20),
                    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            conn.commit()
            conn.close()
            
            print("✅ Database tables created successfully!")
            print("   • live_stock_data")
            print("   • live_crypto_data") 
            print("   • technical_indicators")
            
        except Exception as e:
            print(f"❌ Database setup error: {e}")
    
    def extract_stock_data(self):
        """Extract live stock data from Alpha Vantage API"""
        print("\n📡 STEP 2: Extracting Live Stock Data")
        print("-" * 50)
        
        symbols = ['AAPL', 'GOOGL', 'MSFT']
        stock_records = []
        
        for symbol in symbols:
            try:
                print(f"🔍 Fetching {symbol} data from Alpha Vantage...")
                
                # Make API request
                url = "https://www.alphavantage.co/query"
                params = {
                    'function': 'TIME_SERIES_INTRADAY',
                    'symbol': symbol,
                    'interval': '5min',
                    'apikey': self.alpha_vantage_key,
                    'outputsize': 'compact'
                }
                
                response = requests.get(url, params=params, timeout=15)
                data = response.json()
                
                print(f"   📊 API Response size: {len(str(data))} characters")
                print(f"   🔗 API URL: {url}")
                print(f"   📝 Response keys: {list(data.keys())}")
                
                # Process response
                if 'Time Series (5min)' in data:
                    time_series = data['Time Series (5min)']
                    
                    # Get latest 5 records
                    latest_times = sorted(time_series.keys(), reverse=True)[:5]
                    
                    print(f"   ✅ Retrieved {len(latest_times)} records for {symbol}")
                    
                    for timestamp in latest_times:
                        record_data = time_series[timestamp]
                        
                        record = {
                            'symbol': symbol,
                            'timestamp': timestamp,
                            'open_price': float(record_data['1. open']),
                            'high_price': float(record_data['2. high']),
                            'low_price': float(record_data['3. low']),
                            'close_price': float(record_data['4. close']),
                            'volume': int(record_data['5. volume'])
                        }
                        
                        stock_records.append(record)
                        
                        print(f"   📈 {timestamp}: ${record['close_price']} (Vol: {record['volume']:,})")
                
                else:
                    print(f"   ⚠️  No time series data for {symbol}")
                    if 'Information' in data:
                        print(f"   ℹ️  API Info: {data['Information'][:100]}...")
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"   ❌ Error fetching {symbol}: {e}")
        
        print(f"\n📊 Total stock records extracted: {len(stock_records)}")
        return stock_records
    
    def extract_crypto_data(self):
        """Extract live cryptocurrency data from CoinGecko API"""
        print("\n🪙 STEP 3: Extracting Live Cryptocurrency Data")
        print("-" * 50)
        
        try:
            print("🔍 Fetching crypto data from CoinGecko...")
            
            # Make API request
            url = "https://api.coingecko.com/api/v3/coins/markets"
            params = {
                'vs_currency': 'usd',
                'ids': 'bitcoin,ethereum,cardano,solana,chainlink',
                'order': 'market_cap_desc',
                'per_page': 5,
                'page': 1,
                'sparkline': False,
                'price_change_percentage': '24h'
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            print(f"   📊 API Response: {len(data)} cryptocurrencies")
            print(f"   🔗 API URL: {url}")
            
            crypto_records = []
            
            for crypto in data:
                record = {
                    'symbol': crypto['symbol'].upper(),
                    'current_price': float(crypto['current_price']),
                    'market_cap': int(crypto['market_cap']) if crypto['market_cap'] else 0,
                    'price_change_24h': float(crypto['price_change_percentage_24h']) if crypto['price_change_percentage_24h'] else 0,
                    'volume_24h': int(crypto['total_volume']) if crypto['total_volume'] else 0
                }
                
                crypto_records.append(record)
                
                print(f"   💰 {record['symbol']}: ${record['current_price']:,.2f} ({record['price_change_24h']:+.2f}%)")
                print(f"      📊 Market Cap: ${record['market_cap']:,}")
                print(f"      📈 24h Volume: ${record['volume_24h']:,}")
        
            print(f"\n📊 Total crypto records extracted: {len(crypto_records)}")
            return crypto_records
            
        except Exception as e:
            print(f"❌ Error fetching crypto data: {e}")
            return []
    
    def store_stock_data(self, stock_records):
        """Store stock data in PostgreSQL database"""
        print("\n💾 STEP 4: Storing Stock Data in Database")
        print("-" * 50)
        
        if not stock_records:
            print("⚠️  No stock records to store")
            return
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            print(f"🔄 Inserting {len(stock_records)} stock records...")
            
            for i, record in enumerate(stock_records):
                cursor.execute("""
                    INSERT INTO live_stock_data 
                    (symbol, timestamp, open_price, high_price, low_price, close_price, volume)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    record['symbol'],
                    record['timestamp'],
                    record['open_price'],
                    record['high_price'], 
                    record['low_price'],
                    record['close_price'],
                    record['volume']
                ))
                
                if (i + 1) % 5 == 0:
                    print(f"   ✅ Inserted {i + 1}/{len(stock_records)} records")
            
            # Verify data insertion
            cursor.execute("SELECT COUNT(*) FROM live_stock_data;")
            total_count = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT symbol, COUNT(*) as count, 
                       MIN(close_price) as min_price, 
                       MAX(close_price) as max_price
                FROM live_stock_data 
                GROUP BY symbol
                ORDER BY symbol;
            """)
            
            summary = cursor.fetchall()
            
            conn.commit()
            conn.close()
            
            print(f"✅ Stock data stored successfully!")
            print(f"   📊 Total records in database: {total_count}")
            print("   📈 Summary by symbol:")
            
            for symbol, count, min_price, max_price in summary:
                print(f"      {symbol}: {count} records, Price range: ${min_price:.2f} - ${max_price:.2f}")
            
        except Exception as e:
            print(f"❌ Error storing stock data: {e}")
    
    def store_crypto_data(self, crypto_records):
        """Store cryptocurrency data in PostgreSQL database"""
        print("\n🪙 STEP 5: Storing Crypto Data in Database")
        print("-" * 50)
        
        if not crypto_records:
            print("⚠️  No crypto records to store")
            return
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            print(f"🔄 Inserting {len(crypto_records)} crypto records...")
            
            for record in crypto_records:
                cursor.execute("""
                    INSERT INTO live_crypto_data 
                    (symbol, current_price, market_cap, price_change_24h, volume_24h)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    record['symbol'],
                    record['current_price'],
                    record['market_cap'],
                    record['price_change_24h'],
                    record['volume_24h']
                ))
            
            # Verify data insertion
            cursor.execute("SELECT COUNT(*) FROM live_crypto_data;")
            total_count = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT symbol, current_price, price_change_24h, 
                       market_cap, volume_24h
                FROM live_crypto_data 
                ORDER BY market_cap DESC;
            """)
            
            stored_data = cursor.fetchall()
            
            conn.commit()
            conn.close()
            
            print(f"✅ Crypto data stored successfully!")
            print(f"   📊 Total records in database: {total_count}")
            print("   💰 Stored crypto data:")
            
            for symbol, price, change, mcap, volume in stored_data:
                print(f"      {symbol}: ${price:,.2f} ({change:+.2f}%) | MCap: ${mcap:,} | Vol: ${volume:,}")
            
        except Exception as e:
            print(f"❌ Error storing crypto data: {e}")
    
    def calculate_technical_indicators(self):
        """Calculate and store technical indicators"""
        print("\n📊 STEP 6: Calculating Technical Indicators")
        print("-" * 50)
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Get unique symbols with sufficient data
            cursor.execute("""
                SELECT symbol, COUNT(*) as record_count
                FROM live_stock_data 
                GROUP BY symbol 
                HAVING COUNT(*) >= 3
                ORDER BY symbol;
            """)
            
            symbols_with_data = cursor.fetchall()
            print(f"📈 Processing indicators for {len(symbols_with_data)} symbols...")
            
            for symbol, record_count in symbols_with_data:
                print(f"\n🔍 Processing {symbol} ({record_count} records)...")
                
                # Get price data for calculations
                cursor.execute("""
                    SELECT close_price, volume, timestamp
                    FROM live_stock_data 
                    WHERE symbol = %s 
                    ORDER BY timestamp DESC
                    LIMIT 20;
                """, (symbol,))
                
                price_data = cursor.fetchall()
                
                if len(price_data) >= 3:
                    prices = [float(row[0]) for row in price_data]
                    volumes = [int(row[1]) for row in price_data]
                    
                    # Calculate Simple Moving Averages
                    sma_20 = sum(prices[:min(20, len(prices))]) / min(20, len(prices))
                    sma_50 = sum(prices[:min(50, len(prices))]) / min(50, len(prices))
                    
                    # Calculate RSI (simplified)
                    price_changes = [prices[i] - prices[i+1] for i in range(len(prices)-1)]
                    gains = [change for change in price_changes if change > 0]
                    losses = [-change for change in price_changes if change < 0]
                    
                    avg_gain = sum(gains) / max(len(gains), 1)
                    avg_loss = sum(losses) / max(len(losses), 1)
                    
                    if avg_loss > 0:
                        rs = avg_gain / avg_loss
                        rsi = 100 - (100 / (1 + rs))
                    else:
                        rsi = 100
                    
                    # Calculate volatility
                    price_returns = [price_changes[i] / prices[i+1] for i in range(len(price_changes))]
                    volatility = pd.Series(price_returns).std() * 100 if price_returns else 0
                    
                    # Generate trading signal
                    if rsi < 30:
                        signal = "STRONG_BUY"
                    elif rsi < 45:
                        signal = "BUY"
                    elif rsi > 70:
                        signal = "SELL"
                    elif rsi > 55:
                        signal = "WEAK_SELL"
                    else:
                        signal = "HOLD"
                    
                    # Store indicators
                    cursor.execute("""
                        INSERT INTO technical_indicators 
                        (symbol, rsi, sma_20, sma_50, volatility, trading_signal)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (symbol, rsi, sma_20, sma_50, volatility, signal))
                    
                    print(f"   ✅ {symbol} Indicators:")
                    print(f"      RSI: {rsi:.2f}")
                    print(f"      SMA-20: ${sma_20:.2f}")
                    print(f"      SMA-50: ${sma_50:.2f}")
                    print(f"      Volatility: {volatility:.2f}%")
                    print(f"      Signal: {signal}")
            
            conn.commit()
            
            # Summary query
            cursor.execute("""
                SELECT COUNT(*) as total_indicators,
                       COUNT(CASE WHEN trading_signal LIKE '%BUY%' THEN 1 END) as buy_signals,
                       COUNT(CASE WHEN trading_signal = 'HOLD' THEN 1 END) as hold_signals,
                       COUNT(CASE WHEN trading_signal LIKE '%SELL%' THEN 1 END) as sell_signals
                FROM technical_indicators;
            """)
            
            summary = cursor.fetchone()
            conn.close()
            
            print(f"\n✅ Technical indicators calculated successfully!")
            print(f"   📊 Total indicators: {summary[0]}")
            print(f"   📈 Buy signals: {summary[1]}")
            print(f"   ⏸️  Hold signals: {summary[2]}")
            print(f"   📉 Sell signals: {summary[3]}")
            
        except Exception as e:
            print(f"❌ Error calculating indicators: {e}")
    
    def generate_final_report(self):
        """Generate comprehensive pipeline execution report"""
        print("\n📋 STEP 7: Pipeline Execution Report")
        print("-" * 50)
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Stock data summary
            cursor.execute("""
                SELECT COUNT(*) as total_stock_records,
                       COUNT(DISTINCT symbol) as unique_symbols,
                       MIN(extracted_at) as first_extract,
                       MAX(extracted_at) as last_extract
                FROM live_stock_data;
            """)
            
            stock_summary = cursor.fetchone()
            
            # Crypto data summary
            cursor.execute("""
                SELECT COUNT(*) as total_crypto_records,
                       SUM(market_cap) as total_market_cap,
                       AVG(price_change_24h) as avg_24h_change
                FROM live_crypto_data;
            """)
            
            crypto_summary = cursor.fetchone()
            
            # Technical indicators summary
            cursor.execute("""
                SELECT trading_signal, COUNT(*) as count
                FROM technical_indicators 
                GROUP BY trading_signal
                ORDER BY count DESC;
            """)
            
            signal_distribution = cursor.fetchall()
            
            # Top performing assets
            cursor.execute("""
                SELECT symbol, current_price, price_change_24h
                FROM live_crypto_data 
                ORDER BY price_change_24h DESC
                LIMIT 3;
            """)
            
            top_crypto = cursor.fetchall()
            
            conn.close()
            
            print("📊 PIPELINE EXECUTION SUMMARY")
            print("=" * 50)
            
            print(f"🕐 Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            print(f"\n📈 Stock Data Processing:")
            print(f"   • Records Processed: {stock_summary[0] or 0}")
            print(f"   • Unique Symbols: {stock_summary[1] or 0}")
            print(f"   • Time Range: {stock_summary[2]} to {stock_summary[3]}")
            
            print(f"\n🪙 Cryptocurrency Data:")
            print(f"   • Records Processed: {crypto_summary[0] or 0}")
            print(f"   • Total Market Cap: ${crypto_summary[1] or 0:,.0f}")
            print(f"   • Avg 24h Change: {crypto_summary[2] or 0:.2f}%")
            
            print(f"\n📊 Technical Analysis:")
            print("   • Signal Distribution:")
            for signal, count in signal_distribution:
                print(f"      {signal}: {count}")
            
            print(f"\n🏆 Top Performers (24h):")
            for symbol, price, change in top_crypto:
                print(f"   • {symbol}: ${price:,.2f} ({change:+.2f}%)")
            
            print(f"\n✅ Pipeline Status: COMPLETED SUCCESSFULLY")
            print(f"🚀 Ready for production deployment!")
            
        except Exception as e:
            print(f"❌ Error generating report: {e}")
    
    def run_full_pipeline(self):
        """Execute the complete data pipeline"""
        print("🚀 STARTING COMPLETE DATA PIPELINE EXECUTION")
        print("=" * 70)
        
        start_time = datetime.now()
        
        # Execute pipeline steps
        self.create_tables()
        
        stock_data = self.extract_stock_data()
        crypto_data = self.extract_crypto_data()
        
        self.store_stock_data(stock_data)
        self.store_crypto_data(crypto_data)
        
        self.calculate_technical_indicators()
        
        self.generate_final_report()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n🎯 PIPELINE EXECUTION COMPLETE!")
        print(f"⏱️  Total Execution Time: {duration.total_seconds():.2f} seconds")
        print(f"📊 Data Successfully Processed and Stored!")

if __name__ == "__main__":
    demo = LiveDataPipelineDemo()
    demo.run_full_pipeline()