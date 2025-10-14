#!/usr/bin/env python3
"""
Real PostgreSQL Database Pipeline
Connects to actual PostgreSQL installation on your computer instead of Docker
"""

import os
import requests
import pandas as pd
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

class RealDatabasePipeline:
    """Pipeline that uses real PostgreSQL database on your computer"""
    
    def __init__(self):
        load_dotenv()
        
        # Database configuration for real PostgreSQL
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),  # Standard PostgreSQL port
            'database': os.getenv('DB_DATABASE', 'financial_trading_db'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres123')
        }
        
        print("🗄️  REAL POSTGRESQL DATABASE PIPELINE")
        print("=" * 60)
        print(f"🔗 Connecting to: {self.db_config['host']}:{self.db_config['port']}")
        print(f"📊 Database: {self.db_config['database']}")
        print(f"👤 User: {self.db_config['user']}")
        print()
    
    def test_connection(self):
        """Test connection to real PostgreSQL database"""
        print("🔍 Testing Real PostgreSQL Connection...")
        print("-" * 40)
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Get PostgreSQL version
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            # Get database size
            cursor.execute(f"""
                SELECT pg_size_pretty(pg_database_size('{self.db_config['database']}'));
            """)
            db_size = cursor.fetchone()[0]
            
            # Get current database location
            cursor.execute("SHOW data_directory;")
            data_dir = cursor.fetchone()[0]
            
            conn.close()
            
            print(f"✅ Connection successful!")
            print(f"📊 PostgreSQL Version: {version[:50]}...")
            print(f"💾 Database Size: {db_size}")
            print(f"📁 Data Directory: {data_dir}")
            
            return True
            
        except psycopg2.OperationalError as e:
            print(f"❌ Connection failed: {str(e)}")
            print("\n💡 Possible solutions:")
            print("   1. Install PostgreSQL: https://www.postgresql.org/download/")
            print("   2. Check if PostgreSQL service is running")
            print("   3. Verify credentials in .env file")
            print("   4. Create database 'financial_trading_db'")
            
            return False
        
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            return False
    
    def create_real_database_schema(self):
        """Create database and tables in real PostgreSQL"""
        print("\n🏗️  Creating Real Database Schema...")
        print("-" * 40)
        
        try:
            # First connect to default postgres database
            temp_config = self.db_config.copy()
            temp_config['database'] = 'postgres'
            
            conn = psycopg2.connect(**temp_config)
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Create database if it doesn't exist
            cursor.execute(f"""
                SELECT 1 FROM pg_database 
                WHERE datname = '{self.db_config['database']}';
            """)
            
            if not cursor.fetchone():
                print(f"📊 Creating database: {self.db_config['database']}")
                cursor.execute(f"CREATE DATABASE {self.db_config['database']};")
                print("✅ Database created successfully!")
            else:
                print(f"📊 Database '{self.db_config['database']}' already exists")
            
            conn.close()
            
            # Now connect to our specific database
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Create financial data schema
            print("🗂️  Creating tables...")
            
            # Stocks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS real_stock_data (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(10) NOT NULL,
                    company_name VARCHAR(100),
                    timestamp TIMESTAMP NOT NULL,
                    open_price DECIMAL(12,4),
                    high_price DECIMAL(12,4),
                    low_price DECIMAL(12,4),
                    close_price DECIMAL(12,4),
                    volume BIGINT,
                    market_cap BIGINT,
                    pe_ratio DECIMAL(8,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, timestamp)
                );
            """)
            
            # Crypto table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS real_crypto_data (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    name VARCHAR(100),
                    current_price DECIMAL(18,8),
                    market_cap BIGINT,
                    market_cap_rank INTEGER,
                    price_change_24h DECIMAL(10,4),
                    price_change_percentage_24h DECIMAL(8,4),
                    volume_24h BIGINT,
                    circulating_supply BIGINT,
                    total_supply BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Technical analysis table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS technical_analysis (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    asset_type VARCHAR(10) NOT NULL, -- 'stock' or 'crypto'
                    rsi_14 DECIMAL(6,2),
                    sma_20 DECIMAL(12,4),
                    sma_50 DECIMAL(12,4),
                    sma_200 DECIMAL(12,4),
                    macd DECIMAL(10,6),
                    bollinger_upper DECIMAL(12,4),
                    bollinger_lower DECIMAL(12,4),
                    volatility_30d DECIMAL(8,4),
                    trading_signal VARCHAR(20),
                    signal_strength DECIMAL(3,1), -- 1-10 scale
                    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Portfolio tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_positions (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    asset_type VARCHAR(10) NOT NULL,
                    position_size DECIMAL(18,8),
                    average_cost DECIMAL(12,4),
                    current_value DECIMAL(15,2),
                    unrealized_pnl DECIMAL(15,2),
                    realized_pnl DECIMAL(15,2),
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_stock_symbol_timestamp ON real_stock_data(symbol, timestamp);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_crypto_symbol ON real_crypto_data(symbol);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_technical_symbol ON technical_analysis(symbol, analysis_date);")
            
            conn.commit()
            
            # Verify table creation
            cursor.execute("""
                SELECT table_name, 
                       (SELECT COUNT(*) FROM information_schema.columns 
                        WHERE table_name = t.table_name) as column_count
                FROM information_schema.tables t
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            
            tables = cursor.fetchall()
            
            print("✅ Schema created successfully!")
            print("📋 Created tables:")
            for table_name, col_count in tables:
                print(f"   • {table_name}: {col_count} columns")
            
            # Show actual file location
            cursor.execute("SHOW data_directory;")
            data_dir = cursor.fetchone()[0]
            
            cursor.execute("SELECT oid FROM pg_database WHERE datname = %s;", (self.db_config['database'],))
            db_oid = cursor.fetchone()[0]
            
            print(f"\n📁 Your database files are physically located at:")
            print(f"   {data_dir}\\base\\{db_oid}\\")
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Schema creation failed: {str(e)}")
            return False
    
    def insert_sample_data(self):
        """Insert sample financial data to test the real database"""
        print("\n📊 Inserting Sample Data into Real Database...")
        print("-" * 40)
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Sample stock data
            stock_samples = [
                ('AAPL', 'Apple Inc.', '2025-10-13 16:00:00', 245.40, 246.50, 244.80, 245.40, 1500000, 3800000000000, 28.5),
                ('GOOGL', 'Alphabet Inc.', '2025-10-13 16:00:00', 235.77, 237.20, 234.50, 235.77, 1200000, 2900000000000, 22.3),
                ('MSFT', 'Microsoft Corporation', '2025-10-13 16:00:00', 511.51, 513.80, 510.20, 511.51, 800000, 3700000000000, 31.2),
                ('TSLA', 'Tesla Inc.', '2025-10-13 16:00:00', 248.95, 252.10, 247.30, 248.95, 2100000, 790000000000, 65.8),
                ('AMZN', 'Amazon.com Inc.', '2025-10-13 16:00:00', 178.25, 179.90, 177.40, 178.25, 950000, 1850000000000, 45.2)
            ]
            
            print("📈 Inserting stock data...")
            for stock in stock_samples:
                cursor.execute("""
                    INSERT INTO real_stock_data 
                    (symbol, company_name, timestamp, open_price, high_price, low_price, close_price, volume, market_cap, pe_ratio)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (symbol, timestamp) DO UPDATE SET
                    close_price = EXCLUDED.close_price,
                    volume = EXCLUDED.volume;
                """, stock)
            
            # Sample crypto data
            crypto_samples = [
                ('BTC', 'Bitcoin', 114823.50, 2285574599733, 1, 0.63, 0.63, 84226702991, 19750000, 21000000),
                ('ETH', 'Ethereum', 4172.18, 503097873558, 2, 1.59, 1.59, 50233125131, 120500000, None),
                ('SOL', 'Solana', 199.72, 108967438770, 5, 3.07, 3.07, 11032021558, 545000000, None),
                ('ADA', 'Cardano', 0.72, 26125311398, 9, 4.13, 4.13, 2276699402, 36000000000, 45000000000),
                ('LINK', 'Chainlink', 19.61, 13651416421, 11, 2.32, 2.32, 1589687525, 626000000, 1000000000)
            ]
            
            print("🪙 Inserting crypto data...")
            for crypto in crypto_samples:
                cursor.execute("""
                    INSERT INTO real_crypto_data 
                    (symbol, name, current_price, market_cap, market_cap_rank, price_change_24h, 
                     price_change_percentage_24h, volume_24h, circulating_supply, total_supply)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, crypto)
            
            conn.commit()
            
            # Verify insertion
            cursor.execute("SELECT COUNT(*) FROM real_stock_data;")
            stock_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM real_crypto_data;")
            crypto_count = cursor.fetchone()[0]
            
            print(f"✅ Data inserted successfully!")
            print(f"   📈 Stock records: {stock_count}")
            print(f"   🪙 Crypto records: {crypto_count}")
            
            # Show sample queries
            print("\n🔍 Sample data verification:")
            cursor.execute("""
                SELECT symbol, close_price, volume, 
                       TO_CHAR(market_cap, 'FM999,999,999,999,999') as market_cap_formatted
                FROM real_stock_data 
                ORDER BY market_cap DESC 
                LIMIT 3;
            """)
            
            top_stocks = cursor.fetchall()
            print("📊 Top stocks by market cap:")
            for symbol, price, volume, mcap in top_stocks:
                print(f"   {symbol}: ${price:.2f} | Volume: {volume:,} | MCap: ${mcap}")
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Data insertion failed: {str(e)}")
            return False
    
    def show_database_location(self):
        """Show exactly where your data is stored on disk"""
        print("\n📁 Real Database File Locations")
        print("-" * 40)
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Get data directory
            cursor.execute("SHOW data_directory;")
            data_dir = cursor.fetchone()[0]
            
            # Get database OID
            cursor.execute("SELECT oid FROM pg_database WHERE datname = %s;", (self.db_config['database'],))
            db_oid = cursor.fetchone()[0]
            
            # Get table file locations
            cursor.execute("""
                SELECT schemaname, tablename, 
                       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
            """)
            
            tables = cursor.fetchall()
            
            print(f"🗂️  Database Location:")
            print(f"   📁 Data Directory: {data_dir}")
            print(f"   📊 Database Files: {data_dir}\\base\\{db_oid}\\")
            print(f"   🔧 Config File: {data_dir}\\postgresql.conf")
            print(f"   📝 Log Files: {data_dir}\\log\\")
            
            print(f"\n📋 Table Sizes:")
            for schema, table, size in tables:
                print(f"   {table}: {size}")
            
            # Show connection info
            cursor.execute("SELECT inet_server_addr(), inet_server_port();")
            server_info = cursor.fetchone()
            
            print(f"\n🔗 Connection Details:")
            print(f"   Host: {self.db_config['host']}")
            print(f"   Port: {self.db_config['port']}")
            print(f"   Database: {self.db_config['database']}")
            print(f"   Server: {server_info[0] or 'localhost'}:{server_info[1]}")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Error getting location info: {str(e)}")
    
    def run_real_database_setup(self):
        """Complete setup for real PostgreSQL database"""
        print("🚀 SETTING UP REAL POSTGRESQL DATABASE")
        print("=" * 60)
        
        start_time = datetime.now()
        
        # Test connection
        if not self.test_connection():
            print("\n💡 Next Steps:")
            print("1. Install PostgreSQL from: https://www.postgresql.org/download/")
            print("2. Update .env file with your credentials")
            print("3. Run this script again")
            return False
        
        # Create schema
        if not self.create_real_database_schema():
            return False
        
        # Insert sample data
        if not self.insert_sample_data():
            return False
        
        # Show locations
        self.show_database_location()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n🎉 REAL DATABASE SETUP COMPLETE!")
        print(f"⏱️  Setup Time: {duration.total_seconds():.2f} seconds")
        print(f"✅ Your financial data is now stored in a real PostgreSQL database!")
        
        return True

if __name__ == "__main__":
    pipeline = RealDatabasePipeline()
    pipeline.run_real_database_setup()