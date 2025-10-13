#!/usr/bin/env python3
"""
Real Database Verification - Check what's actually in your PostgreSQL database
"""

import os
import psycopg2
from dotenv import load_dotenv

def verify_real_database():
    """Verify what's in your real PostgreSQL database"""
    load_dotenv()
    
    # Database connection
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_DATABASE', 'financial_trading_db'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD')
    }
    
    print("🔍 REAL DATABASE VERIFICATION")
    print("=" * 50)
    print(f"🗄️  Database: {db_config['database']}")
    print(f"📁 Location: C:/Program Files/PostgreSQL/17/data/")
    print()
    
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # 1. Show database info
        cursor.execute("""
            SELECT current_database(), 
                   current_user,
                   pg_database_size(current_database()) as size_bytes;
        """)
        db_info = cursor.fetchone()
        
        print("📊 DATABASE INFO:")
        print(f"   Database: {db_info[0]}")
        print(f"   User: {db_info[1]}")
        print(f"   Size: {db_info[2] / 1024:.1f} KB")
        
        # 2. Show all tables and their columns
        cursor.execute("""
            SELECT t.table_name, 
                   array_agg(c.column_name ORDER BY c.ordinal_position) as columns
            FROM information_schema.tables t
            JOIN information_schema.columns c ON t.table_name = c.table_name
            WHERE t.table_schema = 'public' 
            AND t.table_type = 'BASE TABLE'
            GROUP BY t.table_name
            ORDER BY t.table_name;
        """)
        
        tables_info = cursor.fetchall()
        
        print(f"\n📋 TABLES ({len(tables_info)} total):")
        for table_name, columns in tables_info:
            print(f"\n📊 {table_name}:")
            print(f"   Columns: {', '.join(columns)}")
        
        # 3. Show actual data in each table
        print(f"\n💾 ACTUAL DATA IN TABLES:")
        
        for table_name, _ in tables_info:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            
            if count > 0:
                print(f"\n📈 {table_name} ({count} records):")
                
                # Get some sample data
                if table_name == 'real_stock_data':
                    cursor.execute("""
                        SELECT symbol, close_price, volume, extracted_at 
                        FROM real_stock_data 
                        ORDER BY close_price DESC 
                        LIMIT 5;
                    """)
                    
                    for row in cursor.fetchall():
                        print(f"   📊 {row[0]}: ${row[1]:.2f} | Vol: {row[2]:,} | {row[3]}")
                
                elif table_name == 'real_crypto_data':
                    cursor.execute("""
                        SELECT symbol, current_price, market_cap, extracted_at
                        FROM real_crypto_data 
                        ORDER BY market_cap DESC NULLS LAST
                        LIMIT 5;
                    """)
                    
                    for row in cursor.fetchall():
                        mcap_str = f"${row[2]:,}" if row[2] else "N/A"
                        print(f"   🪙 {row[0]}: ${row[1]:.2f} | MCap: {mcap_str} | {row[3]}")
                
                else:
                    # Generic data display
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
                    for row in cursor.fetchall():
                        print(f"   • {row}")
            else:
                print(f"\n📊 {table_name}: Empty (0 records)")
        
        # 4. Show database file locations
        cursor.execute("SELECT setting FROM pg_settings WHERE name = 'data_directory';")
        data_dir = cursor.fetchone()[0]
        
        cursor.execute("SHOW log_directory;")
        log_dir = cursor.fetchone()[0]
        
        print(f"\n📁 DATABASE FILES:")
        print(f"   🗂️  Data Directory: {data_dir}")
        print(f"   📝 Logs Directory: {data_dir}/{log_dir}")
        print(f"   ⚙️  Config File: {data_dir}/postgresql.conf")
        
        # 5. Calculate total data
        total_records = 0
        total_market_value = 0
        
        for table_name, _ in tables_info:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            total_records += count
            
            # Calculate market values
            if table_name == 'real_crypto_data':
                cursor.execute("SELECT SUM(market_cap) FROM real_crypto_data WHERE market_cap IS NOT NULL;")
                crypto_mcap = cursor.fetchone()[0]
                if crypto_mcap:
                    total_market_value += crypto_mcap
        
        conn.close()
        
        print(f"\n🎯 SUMMARY:")
        print(f"   📊 Total Records: {total_records}")
        print(f"   💰 Total Market Value: ${total_market_value:,}" if total_market_value else "   💰 Market Value: Not calculated")
        print(f"   🏢 This is YOUR real PostgreSQL database!")
        print(f"   🔗 Connect: psql -h localhost -p 5432 -U postgres -d financial_trading_db")
        
        print(f"\n✅ Your financial data is permanently stored in:")
        print(f"   {data_dir}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verify_real_database()