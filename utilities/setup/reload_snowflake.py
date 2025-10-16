#!/usr/bin/env python3
"""
Reload Snowflake with Fixed Data
Clears corrupted data and reloads from the fixed Parquet files
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config import PipelineConfig
import snowflake.connector

def reload_snowflake_data():
    """Clear corrupted data and reload from S3/Parquet."""
    
    print("\n🔄 RELOADING SNOWFLAKE DATA")
    print("=" * 80)
    
    # Load configuration
    config = PipelineConfig()
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
    
    print("\n⚠️  STEP 1: Checking current data...")
    cursor.execute("SELECT COUNT(*) FROM STOCK_DATA")
    stock_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM CRYPTO_DATA")
    crypto_count = cursor.fetchone()[0]
    
    print(f"   Current STOCK_DATA records: {stock_count:,}")
    print(f"   Current CRYPTO_DATA records: {crypto_count:,}")
    
    # Ask for confirmation
    response = input("\n⚠️  Do you want to CLEAR ALL data and reload? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Cancelled by user")
        cursor.close()
        conn.close()
        return False
    
    print("\n🗑️  STEP 2: Clearing corrupted data...")
    cursor.execute("TRUNCATE TABLE STOCK_DATA")
    print("   ✅ STOCK_DATA cleared")
    
    cursor.execute("TRUNCATE TABLE CRYPTO_DATA")
    print("   ✅ CRYPTO_DATA cleared")
    
    print("\n📥 STEP 3: Reloading data from Parquet files...")
    print("   Run the snowflake data loader to reload from S3/Parquet")
    print("   Command: python scripts/snowflake_data_loader.py")
    
    print("\n" + "=" * 80)
    print("✅ Database cleared - ready for reload!")
    print("=" * 80 + "\n")
    
    cursor.close()
    conn.close()
    return True

if __name__ == "__main__":
    reload_snowflake_data()
