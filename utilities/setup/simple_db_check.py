#!/usr/bin/env python3
"""
Simple Database Check - See what's in your real PostgreSQL database
"""

import os
import psycopg2
from dotenv import load_dotenv

def simple_database_check():
    """Simple check of your real PostgreSQL database"""
    load_dotenv()
    
    # Connect to database
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_DATABASE', 'financial_trading_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD')
        )
        
        cursor = conn.cursor()
        
        print("🗄️  YOUR REAL POSTGRESQL DATABASE")
        print("=" * 50)
        
        # Basic database info
        cursor.execute("SELECT current_database(), current_user;")
        db_info = cursor.fetchone()
        
        cursor.execute("SELECT pg_database_size(current_database());")
        db_size = cursor.fetchone()[0]
        
        print(f"📊 Database: {db_info[0]}")
        print(f"👤 User: {db_info[1]}")
        print(f"💾 Size: {db_size / 1024:.1f} KB")
        print(f"📁 Location: C:/Program Files/PostgreSQL/17/data/")
        
        # List all tables
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            ORDER BY tablename;
        """)
        
        tables = cursor.fetchall()
        
        print(f"\n📋 TABLES ({len(tables)} total):")
        for table in tables:
            table_name = table[0]
            
            # Count records
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            
            print(f"   📊 {table_name}: {count} records")
            
            # Show sample data if exists
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
                rows = cursor.fetchall()
                
                # Get column names
                cursor.execute(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}' 
                    ORDER BY ordinal_position;
                """)
                columns = [col[0] for col in cursor.fetchall()]
                
                print(f"      Columns: {', '.join(columns[:5])}{'...' if len(columns) > 5 else ''}")
                
                for i, row in enumerate(rows[:2]):
                    # Show first few values
                    sample_values = []
                    for j, value in enumerate(row[:4]):
                        if j < len(columns):
                            if isinstance(value, (int, float)):
                                if abs(value) > 1000000:
                                    sample_values.append(f"{columns[j]}: {value:,.0f}")
                                else:
                                    sample_values.append(f"{columns[j]}: {value}")
                            else:
                                str_val = str(value)
                                if len(str_val) > 20:
                                    str_val = str_val[:20] + "..."
                                sample_values.append(f"{columns[j]}: {str_val}")
                    
                    print(f"      Row {i+1}: {', '.join(sample_values)}")
        
        # Show recent activity
        print(f"\n🕐 RECENT ACTIVITY:")
        
        # Check for recent stock data
        try:
            cursor.execute("""
                SELECT COUNT(*), MAX(created_at)
                FROM real_stock_data 
                WHERE created_at > NOW() - INTERVAL '1 hour';
            """)
            recent_stocks = cursor.fetchone()
            if recent_stocks[0] > 0:
                print(f"   📈 {recent_stocks[0]} stock records in last hour (latest: {recent_stocks[1]})")
        except:
            pass
        
        # Check for recent crypto data
        try:
            cursor.execute("""
                SELECT COUNT(*), MAX(created_at)
                FROM real_crypto_data 
                WHERE created_at > NOW() - INTERVAL '1 hour';
            """)
            recent_crypto = cursor.fetchone()
            if recent_crypto[0] > 0:
                print(f"   🪙 {recent_crypto[0]} crypto records in last hour (latest: {recent_crypto[1]})")
        except:
            pass
        
        # Calculate total market value if possible
        try:
            cursor.execute("SELECT SUM(market_cap) FROM real_crypto_data WHERE market_cap IS NOT NULL;")
            total_mcap = cursor.fetchone()[0]
            if total_mcap:
                print(f"\n💰 Total Crypto Market Cap: ${total_mcap:,}")
        except:
            pass
        
        print(f"\n✅ YOUR FINANCIAL DATA IS STORED HERE!")
        print(f"🔗 Connect: psql -h localhost -p 5432 -U postgres -d financial_trading_db")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error connecting: {e}")

if __name__ == "__main__":
    simple_database_check()