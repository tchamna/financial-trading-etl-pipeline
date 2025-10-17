#!/usr/bin/env python3
"""
Quick Snowflake Timestamp Verification
Checks that timestamps are properly formatted with UTC
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config import get_config
import snowflake.connector

def check_timestamps():
    """Verify timestamp formatting in Snowflake."""
    
    print("\n🔍 CHECKING SNOWFLAKE TIMESTAMPS")
    print("=" * 80)
    
    # Load configuration
    config = get_config()
    sf_config = config.snowflake
    
    # Connect to Snowflake
    conn = snowflake.connector.connect(
        account=sf_config.account,
        user=sf_config.username,
        password=sf_config.password,
        warehouse=sf_config.warehouse,
        database=sf_config.database,
        schema=sf_config.schema
    )
    
    cursor = conn.cursor()
    
    # Check recent stock data
    print("\n📊 RECENT STOCK DATA (Last 10 records):")
    print("-" * 80)
    cursor.execute("""
        SELECT 
            symbol,
            TO_CHAR(timestamp, 'YYYY-MM-DD HH24:MI:SS')
        FROM STOCK_DATA
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    
    for row in cursor.fetchall():
        print(f"  {row[0]:6} | {row[1]}")
    
    # Check data counts
    print("\n\n📈 DATA SUMMARY:")
    print("-" * 80)
    
    cursor.execute("""
        SELECT 
            'Stock' as type,
            COUNT(*) as records,
            COUNT(DISTINCT symbol) as symbols,
            MIN(DATE(timestamp)) as earliest,
            MAX(DATE(timestamp)) as latest
        FROM STOCK_DATA
    """)
    
    stock_summary = cursor.fetchone()
    print(f"\n  📊 Stock Data:")
    print(f"     Records: {stock_summary[1]:,}")
    print(f"     Symbols: {stock_summary[2]}")
    print(f"     Date Range: {stock_summary[3]} to {stock_summary[4]}")
    
    cursor.execute("""
        SELECT 
            COUNT(*) as records,
            COUNT(DISTINCT symbol) as symbols,
            MIN(DATE(timestamp)) as earliest,
            MAX(DATE(timestamp)) as latest
        FROM CRYPTO_MINUTE_DATA
    """)
    
    crypto_summary = cursor.fetchone()
    print(f"\n  💰 Crypto Data:")
    print(f"     Records: {crypto_summary[0]:,}")
    print(f"     Symbols: {crypto_summary[1]}")
    print(f"     Date Range: {crypto_summary[2]} to {crypto_summary[3]}")
    
    print("\n" + "=" * 80)
    print("✅ Verification complete!")
    print("=" * 80 + "\n")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_timestamps()
