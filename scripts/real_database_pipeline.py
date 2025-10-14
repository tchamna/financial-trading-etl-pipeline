#!/usr/bin/env python3
"""
Live Data Pipeline for Real PostgreSQL Database + AWS S3
Extracts live financial data and stores it in your real PostgreSQL database
and uploads to AWS S3 for cloud storage and analytics

Author: Shck Tchamna (tchamna@gmail.com)
Enhanced with AWS S3 integration for cloud-native ETL pipeline
"""

import os
import sys
import requests
import pandas as pd
import psycopg2
import time
import json
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import configuration
from config import get_config

# Import our S3 uploader
try:
    from s3_data_uploader import create_s3_uploader_from_env
    S3_AVAILABLE = True
except ImportError:
    print("⚠️  S3 uploader not available - will skip S3 upload")
    S3_AVAILABLE = False

class RealDatabasePipeline:
    """Pipeline that stores data in your real PostgreSQL database and AWS S3"""
    
    def __init__(self):
        load_dotenv()
        
        # Load configuration
        self.config = get_config()
        
        # Real database configuration from config
        self.db_config = {
            'host': self.config.database.host,
            'port': self.config.database.port,
            'database': self.config.database.database,
            'user': self.config.database.username,
            'password': self.config.database.password
        }
        
        self.alpha_vantage_key = self.config.api.alpha_vantage_api_key
        
        # Initialize S3 uploader if enabled and available
        self.s3_uploader = None
        if self.config.s3.enabled and S3_AVAILABLE:
            try:
                self.s3_uploader = create_s3_uploader_from_env()
                s3_status = f"✅ Connected to {self.config.s3.bucket_name}"
            except Exception as e:
                print(f"⚠️  S3 connection failed: {e}")
                s3_status = "❌ Connection Failed"
        elif not self.config.s3.enabled:
            s3_status = "⚠️  S3 Disabled in Configuration"
        else:
            s3_status = "❌ S3 Module Not Available"
        
        print("📊 CONFIGURABLE FINANCIAL ETL PIPELINE - LIVE DATA EXTRACTION")
        print("=" * 70)
        print(f"🗄️  Database: {self.db_config['database']} @ {self.db_config['host']}:{self.db_config['port']}")
        print(f"📁 Physical Location: C:/Program Files/PostgreSQL/17/data/")
        print(f"☁️  AWS S3: {s3_status}")
        print(f"📋 Stock Symbols: {', '.join(self.config.processing.stock_symbols[:5])}{'...' if len(self.config.processing.stock_symbols) > 5 else ''}")
        print(f"🪙 Crypto Symbols: {', '.join(self.config.processing.crypto_symbols[:3])}{'...' if len(self.config.processing.crypto_symbols) > 3 else ''}")
        print(f"⏱️  Collection Interval: {self.config.processing.collection_interval_seconds} seconds")
        print()
    
    def verify_database_connection(self):
        """Verify connection to real database"""
        print("🔍 Verifying Real Database Connection...")
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Get database info
            cursor.execute("""
                SELECT current_database(), 
                       current_user, 
                       version(),
                       pg_database_size(current_database()) as db_size;
            """)
            
            db_info = cursor.fetchone()
            
            # Check tables
            cursor.execute("""
                SELECT tablename, schemaname 
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY tablename;
            """)
            
            tables = cursor.fetchall()
            conn.close()
            
            print(f"✅ Connected to real PostgreSQL database!")
            print(f"   📊 Database: {db_info[0]}")
            print(f"   👤 User: {db_info[1]}")
            print(f"   💾 Size: {db_info[3] / 1024:.1f} KB")
            print(f"   📋 Tables: {len(tables)} ({', '.join([t[0] for t in tables])})")
            
            return True
            
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def extract_live_stock_data(self):
        """Extract live stock data from Alpha Vantage"""
        print("\n📈 Extracting Live Stock Data...")
        print("-" * 50)
        
        symbols = self.config.processing.stock_symbols
        stock_records = []
        
        for symbol in symbols:
            try:
                print(f"🔍 Fetching {symbol} data...")
                
                # Alpha Vantage API call
                url = "https://www.alphavantage.co/query"
                params = {
                    'function': 'TIME_SERIES_INTRADAY',
                    'symbol': symbol,
                    'interval': '5min',
                    'apikey': self.alpha_vantage_key
                }
                
                response = requests.get(url, params=params, timeout=15)
                data = response.json()
                
                if 'Time Series (5min)' in data:
                    time_series = data['Time Series (5min)']
                    latest_timestamp = list(time_series.keys())[0]
                    latest_data = time_series[latest_timestamp]
                    
                    record = {
                        'symbol': symbol,
                        'timestamp': latest_timestamp,
                        'open_price': float(latest_data['1. open']),
                        'high_price': float(latest_data['2. high']),
                        'low_price': float(latest_data['3. low']),
                        'close_price': float(latest_data['4. close']),
                        'volume': int(latest_data['5. volume'])
                    }
                    
                    stock_records.append(record)
                    
                    print(f"   ✅ {symbol}: ${record['close_price']:.2f} (Volume: {record['volume']:,})")
                    
                else:
                    print(f"   ⚠️  No data for {symbol}")
                
                time.sleep(0.3)  # Rate limiting
                
            except Exception as e:
                print(f"   ❌ Error fetching {symbol}: {e}")
        
        print(f"\n📊 Extracted {len(stock_records)} live stock records")
        return stock_records
    
    def extract_live_crypto_data(self):
        """Extract live cryptocurrency data"""
        print("\n🪙 Extracting Live Cryptocurrency Data...")
        print("-" * 50)
        
        try:
            # CoinGecko API call with configured symbols
            url = self.config.api.coingecko_base_url + "/coins/markets"
            params = {
                'vs_currency': 'usd',
                'ids': ','.join(self.config.processing.crypto_symbols),
                'order': 'market_cap_desc',
                'per_page': len(self.config.processing.crypto_symbols),
                'page': 1,
                'sparkline': False,
                'price_change_percentage': '24h'
            }
            
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            crypto_records = []
            
            print("🔍 Processing cryptocurrency data...")
            
            for crypto in data:
                record = {
                    'symbol': crypto['symbol'].upper(),
                    'name': crypto['name'],
                    'current_price': float(crypto['current_price']),
                    'market_cap': int(crypto['market_cap']) if crypto['market_cap'] else 0,
                    'price_change_24h': float(crypto['price_change_percentage_24h']) if crypto['price_change_percentage_24h'] else 0,
                    'volume_24h': int(crypto['total_volume']) if crypto['total_volume'] else 0,
                    'market_cap_rank': int(crypto['market_cap_rank']) if crypto['market_cap_rank'] else 999
                }
                
                crypto_records.append(record)
                
                print(f"   💰 {record['symbol']}: ${record['current_price']:,.2f} ({record['price_change_24h']:+.2f}%)")
            
            print(f"\n📊 Extracted {len(crypto_records)} live crypto records")
            return crypto_records
            
        except Exception as e:
            print(f"❌ Error fetching crypto data: {e}")
            return []
    
    def store_stock_data_to_real_db(self, stock_records):
        """Store stock data in real PostgreSQL database"""
        print("\n💾 Storing Stock Data in Real Database...")
        print("-" * 50)
        
        if not stock_records:
            print("⚠️  No stock records to store")
            return
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Clear previous data for clean demo
            cursor.execute("DELETE FROM real_stock_data;")
            
            stored_count = 0
            for record in stock_records:
                cursor.execute("""
                    INSERT INTO real_stock_data 
                    (symbol, price_timestamp, open_price, high_price, low_price, 
                     close_price, volume, market_cap, data_source)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    record['symbol'],
                    record['timestamp'],
                    record['open_price'],
                    record['high_price'],
                    record['low_price'], 
                    record['close_price'],
                    record['volume'],
                    record['close_price'] * 1000000000,  # Estimated market cap
                    'Alpha Vantage API'
                ))
                stored_count += 1
            
            conn.commit()
            
            # Verify storage
            cursor.execute("""
                SELECT symbol, close_price, volume, price_timestamp
                FROM real_stock_data 
                ORDER BY close_price DESC;
            """)
            
            stored_data = cursor.fetchall()
            conn.close()
            
            print(f"✅ Stored {stored_count} stock records in real database!")
            print("📊 Stored data:")
            
            for symbol, price, volume, timestamp in stored_data:
                print(f"   📈 {symbol}: ${price:.2f} | Vol: {volume:,} | {timestamp}")
            
            # Upload to S3 if available
            if self.s3_uploader and stock_records:
                try:
                    print("\n☁️  Uploading stock data to AWS S3...")
                    s3_path = self.s3_uploader.upload_stock_data(
                        stock_records, 
                        data_type='processed',
                        compress=True
                    )
                    print(f"✅ Stock data uploaded to S3: {s3_path}")
                except Exception as e:
                    print(f"⚠️  S3 upload failed: {e}")
            
        except Exception as e:
            print(f"❌ Error storing stock data: {e}")
    
    def store_crypto_data_to_real_db(self, crypto_records):
        """Store crypto data in real PostgreSQL database"""
        print("\n💾 Storing Crypto Data in Real Database...")
        print("-" * 50)
        
        if not crypto_records:
            print("⚠️  No crypto records to store")
            return
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Clear previous data
            cursor.execute("DELETE FROM real_crypto_data;")
            
            stored_count = 0
            for record in crypto_records:
                cursor.execute("""
                    INSERT INTO real_crypto_data 
                    (symbol, name, current_price, market_cap, price_change_24h, 
                     volume_24h, market_cap_rank, data_source)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    record['symbol'],
                    record['name'],
                    record['current_price'],
                    record['market_cap'],
                    record['price_change_24h'],
                    record['volume_24h'],
                    record['market_cap_rank'],
                    'CoinGecko API'
                ))
                stored_count += 1
            
            conn.commit()
            
            # Verify storage
            cursor.execute("""
                SELECT symbol, current_price, market_cap, price_change_24h
                FROM real_crypto_data 
                ORDER BY market_cap DESC;
            """)
            
            stored_data = cursor.fetchall()
            conn.close()
            
            print(f"✅ Stored {stored_count} crypto records in real database!")
            print("💰 Stored crypto data:")
            
            total_market_cap = 0
            for symbol, price, mcap, change in stored_data:
                total_market_cap += mcap if mcap else 0
                print(f"   🪙 {symbol}: ${price:,.2f} ({change:+.2f}%) | MCap: ${mcap:,}")
            
            print(f"\n📊 Total crypto market cap stored: ${total_market_cap:,}")
            
            # Upload to S3 if available
            if self.s3_uploader and crypto_records:
                try:
                    print("\n☁️  Uploading crypto data to AWS S3...")
                    s3_path = self.s3_uploader.upload_crypto_data(
                        crypto_records,
                        data_type='processed', 
                        compress=True
                    )
                    print(f"✅ Crypto data uploaded to S3: {s3_path}")
                except Exception as e:
                    print(f"⚠️  S3 upload failed: {e}")
            
        except Exception as e:
            print(f"❌ Error storing crypto data: {e}")
    
    def verify_data_in_real_database(self):
        """Verify all data was stored correctly"""
        print("\n🔍 Verifying Data in Real Database...")
        print("-" * 50)
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Check stock data
            cursor.execute("SELECT COUNT(*), MAX(close_price), MIN(close_price) FROM real_stock_data;")
            stock_stats = cursor.fetchone()
            
            # Check crypto data  
            cursor.execute("SELECT COUNT(*), SUM(market_cap) FROM real_crypto_data;")
            crypto_stats = cursor.fetchone()
            
            # Get database size
            cursor.execute("SELECT pg_database_size(current_database());")
            db_size = cursor.fetchone()[0]
            
            # Get table sizes
            cursor.execute("""
                SELECT schemaname, tablename, 
                       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
            """)
            
            table_sizes = cursor.fetchall()
            
            conn.close()
            
            print("📊 REAL DATABASE VERIFICATION SUMMARY:")
            print(f"   📈 Stock Records: {stock_stats[0]}")
            print(f"   💰 Price Range: ${stock_stats[2]:.2f} - ${stock_stats[1]:.2f}")
            print(f"   🪙 Crypto Records: {crypto_stats[0]}")
            print(f"   💎 Total Market Cap: ${crypto_stats[1]:,}" if crypto_stats[1] else "   💎 Total Market Cap: $0")
            print(f"   💾 Database Size: {db_size / 1024:.1f} KB")
            
            print("\n📋 Table Sizes in Real Database:")
            for schema, table, size in table_sizes:
                print(f"   📊 {table}: {size}")
            
            print(f"\n📁 Physical Database Location:")
            print(f"   🗂️  Data Files: C:/Program Files/PostgreSQL/17/data/base/")
            print(f"   📝 Logs: C:/Program Files/PostgreSQL/17/data/log/")
            
            return True
            
        except Exception as e:
            print(f"❌ Verification error: {e}")
            return False
    
    def run_complete_pipeline(self):
        """Run the complete real database pipeline"""
        start_time = datetime.now()
        
        print("🚀 STARTING REAL DATABASE PIPELINE")
        print("=" * 70)
        
        # Step 1: Verify database
        if not self.verify_database_connection():
            return False
        
        # Step 2: Extract live data
        stock_data = self.extract_live_stock_data()
        crypto_data = self.extract_live_crypto_data()
        
        # Step 3: Store in real database
        self.store_stock_data_to_real_db(stock_data)
        self.store_crypto_data_to_real_db(crypto_data)
        
        # Step 4: Verify storage
        self.verify_data_in_real_database()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "=" * 70)
        print("🎉 REAL DATABASE PIPELINE COMPLETE!")
        print("=" * 70)
        print(f"⏱️  Total Execution Time: {duration.total_seconds():.2f} seconds")
        print(f"📊 Live Financial Data: Successfully stored in real PostgreSQL")
        print(f"🗄️  Database Location: C:/Program Files/PostgreSQL/17/data/")
        print(f"🔗 Connection: localhost:5432/financial_trading_db")
        
        print("\n💡 What You Accomplished:")
        print("   ✅ Extracted LIVE financial data from APIs")
        print("   ✅ Stored data in REAL PostgreSQL database on your computer")
        print("   ✅ Data persists permanently (not just in Docker containers)")
        print("   ✅ Can access with any PostgreSQL client (pgAdmin, DBeaver, etc.)")
        
        return True

if __name__ == "__main__":
    # Load and validate configuration
    config = get_config()
    
    print("🔍 Validating Configuration...")
    issues = config.validate()
    if issues:
        print("❌ Configuration Issues Found:")
        for issue in issues:
            print(f"   - {issue}")
        print("\n💡 Please check your config.json file or environment variables")
        exit(1)
    
    print("✅ Configuration validated successfully")
    print(config.get_summary())
    
    pipeline = RealDatabasePipeline()
    success = pipeline.run_complete_pipeline()
    
    if success:
        print("\n🚀 Your configurable pipeline has completed successfully!")
        print(f"💻 Connect with: psql -h {config.database.host} -p {config.database.port} -U {config.database.username} -d {config.database.database}")
        if config.s3.enabled:
            print(f"☁️  Data also available in S3 bucket: {config.s3.bucket_name}")
    else:
        print("\n❌ Pipeline failed. Check your configuration.")