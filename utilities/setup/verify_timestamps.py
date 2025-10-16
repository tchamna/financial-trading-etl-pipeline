#!/usr/bin/env python3
"""
Verify Timestamp Fix in Snowflake
Checks that stock timestamps now have proper UTC timezone
"""

import snowflake.connector
import os
from datetime import datetime

def verify_timestamps():
    """Check timestamps in Snowflake after the fix."""
    
    print("\n🔍 VERIFYING TIMESTAMP FIX IN SNOWFLAKE")
    print("=" * 80)
    
    # Connect to Snowflake
    conn = snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        warehouse='FINANCIAL_WH',
        database='FINANCIAL_DB',
        schema='CORE'
    )
    
    cursor = conn.cursor()
    
    # Check stock data timestamps
    print("\n📊 STOCK DATA TIMESTAMPS (Sample from Oct 14, 2025):")
    print("-" * 80)
    cursor.execute("""
        SELECT 
            symbol,
            TO_CHAR(timestamp, 'YYYY-MM-DD HH24:MI:SS TZH:TZM') as formatted_timestamp,
            close_price
        FROM STOCK_DATA
        WHERE DATE(timestamp) = '2025-10-14'
        ORDER BY symbol, timestamp
        LIMIT 15
    """)
    
    stock_results = cursor.fetchall()
    if stock_results:
        for row in stock_results:
            print(f"  {row[0]:6} | {row[1]} | ${row[2]:.2f}")
    else:
        print("  ⚠️  No stock data found for Oct 14, 2025")
    
    # Check crypto data timestamps for comparison
    print("\n\n💰 CRYPTO DATA TIMESTAMPS (Sample from Oct 14, 2025):")
    print("-" * 80)
    cursor.execute("""
        SELECT 
            symbol,
            TO_CHAR(timestamp, 'YYYY-MM-DD HH24:MI:SS TZH:TZM') as formatted_timestamp,
            close_price
        FROM CRYPTO_DATA
        WHERE DATE(timestamp) = '2025-10-14'
        ORDER BY symbol, timestamp
        LIMIT 15
    """)
    
    crypto_results = cursor.fetchall()
    if crypto_results:
        for row in crypto_results:
            print(f"  {row[0]:10} | {row[1]} | ${row[2]:.2f}")
    else:
        print("  ⚠️  No crypto data found for Oct 14, 2025")
    
    # Summary statistics
    print("\n\n📈 DATA SUMMARY:")
    print("-" * 80)
    
    cursor.execute("""
        SELECT 
            'Stock' as data_type,
            COUNT(*) as total_records,
            COUNT(DISTINCT symbol) as unique_symbols,
            MIN(DATE(timestamp)) as earliest_date,
            MAX(DATE(timestamp)) as latest_date
        FROM STOCK_DATA
        UNION ALL
        SELECT 
            'Crypto' as data_type,
            COUNT(*) as total_records,
            COUNT(DISTINCT symbol) as unique_symbols,
            MIN(DATE(timestamp)) as earliest_date,
            MAX(DATE(timestamp)) as latest_date
        FROM CRYPTO_DATA
    """)
    
    summary = cursor.fetchall()
    for row in summary:
        print(f"\n  {row[0]} Data:")
        print(f"    📊 Total Records: {row[1]:,}")
        print(f"    🪙 Unique Symbols: {row[2]}")
        print(f"    📅 Date Range: {row[3]} to {row[4]}")
    
    print("\n" + "=" * 80)
    print("✅ Timestamp verification complete!")
    print("=" * 80 + "\n")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    verify_timestamps()
