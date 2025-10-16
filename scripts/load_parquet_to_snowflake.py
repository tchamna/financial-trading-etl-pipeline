"""
Load Parquet Data to Snowflake
===============================

Load the combined crypto+stock parquet file directly to Snowflake tables.
"""

import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config

def load_parquet_to_snowflake(parquet_file):
    """
    Load a combined parquet file (crypto + stock data) to Snowflake
    
    Args:
        parquet_file: Path to the parquet file
    """
    
    config = get_config()
    
    print(f"📊 Loading Parquet to Snowflake")
    print(f"=" * 60)
    print(f"📁 File: {parquet_file}")
    
    # Read the parquet file
    df = pd.read_parquet(parquet_file)
    print(f"✅ Loaded {len(df)} records from Parquet")
    
    # Define stock symbols
    stock_symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'NVDA', 'META']
    
    # Split into stock and crypto dataframes
    stock_df = df[df['symbol'].isin(stock_symbols)].copy()
    crypto_df = df[~df['symbol'].isin(stock_symbols)].copy()
    
    print(f"📈 Stock records: {len(stock_df)}")
    print(f"💎 Crypto records: {len(crypto_df)}")
    
    # Connect to Snowflake
    print(f"\n🔌 Connecting to Snowflake...")
    conn = snowflake.connector.connect(
        account=config.snowflake.account,
        user=config.snowflake.username,
        password=config.snowflake.password,
        warehouse=config.snowflake.warehouse,
        database=config.snowflake.database,
        schema=config.snowflake.schema
    )
    
    cursor = conn.cursor()
    
    try:
        # Prepare stock data
        if len(stock_df) > 0:
            print(f"\n📊 Loading STOCK_DATA...")
            
            # Standardize column names (make lowercase first, then apply mapping, then uppercase for Snowflake)
            stock_df.columns = [col.lower() for col in stock_df.columns]
            
            # Map to Snowflake table schema (open -> open_price, etc.)
            column_mapping = {
                'open': 'OPEN_PRICE',
                'high': 'HIGH_PRICE',
                'low': 'LOW_PRICE',
                'close': 'CLOSE_PRICE',
                'symbol': 'SYMBOL',
                'timestamp': 'TIMESTAMP',
                'volume': 'VOLUME',
                'source': 'SOURCE'
            }
            
            # Apply column mapping
            stock_df = stock_df.rename(columns=column_mapping)
            
            # Ensure required columns exist
            required_cols = ['SYMBOL', 'TIMESTAMP', 'OPEN_PRICE', 'HIGH_PRICE', 'LOW_PRICE', 'CLOSE_PRICE', 'VOLUME']
            for col in required_cols:
                if col not in stock_df.columns:
                    print(f"⚠️ Missing required column: {col}")
                    return
            
            # Select only the columns that match the table schema (minimal set)
            stock_cols = ['SYMBOL', 'TIMESTAMP', 'OPEN_PRICE', 'HIGH_PRICE', 'LOW_PRICE', 'CLOSE_PRICE', 'VOLUME', 'SOURCE']
            stock_df = stock_df[[col for col in stock_cols if col in stock_df.columns]]
            
            # Write to Snowflake using write_pandas
            success, nchunks, nrows, _ = write_pandas(
                conn,
                stock_df,
                'STOCK_DATA',
                database=config.snowflake.database,
                schema=config.snowflake.schema,
                auto_create_table=False,
                overwrite=False
            )
            
            if success:
                print(f"✅ Loaded {nrows} rows to STOCK_DATA")
            else:
                print(f"❌ Failed to load STOCK_DATA")
        
        # Prepare crypto data
        if len(crypto_df) > 0:
            print(f"\n💎 Loading CRYPTO_DATA...")
            
            # Standardize column names (make lowercase first, then uppercase for Snowflake)
            # CRYPTO_MINUTE_DATA uses: open, high, low, close (not open_price, etc.)
            crypto_df.columns = [col.lower() for col in crypto_df.columns]
            
            # Map to Snowflake table schema (keep open, high, low, close as-is, just uppercase)
            column_mapping = {
                'symbol': 'SYMBOL',
                'timestamp': 'TIMESTAMP',
                'open': 'OPEN',
                'high': 'HIGH',
                'low': 'LOW',
                'close': 'CLOSE',
                'volume': 'VOLUME',
                'api_source': 'API_SOURCE',
                'interval': 'INTERVAL'
            }
            
            # Apply column mapping
            crypto_df = crypto_df.rename(columns=column_mapping)
            
            # Select only the columns that match the table schema
            crypto_cols = ['SYMBOL', 'TIMESTAMP', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME', 'API_SOURCE', 'INTERVAL']
            crypto_df = crypto_df[[col for col in crypto_cols if col in crypto_df.columns]]
            
            # Write to Snowflake (use CRYPTO_MINUTE_DATA for minute-level OHLCV data)
            success, nchunks, nrows, _ = write_pandas(
                conn,
                crypto_df,
                'CRYPTO_MINUTE_DATA',
                database=config.snowflake.database,
                schema=config.snowflake.schema,
                auto_create_table=False,
                overwrite=False
            )
            
            if success:
                print(f"✅ Loaded {nrows} rows to CRYPTO_MINUTE_DATA")
            else:
                print(f"❌ Failed to load CRYPTO_MINUTE_DATA")
        
        # Verify the load
        print(f"\n🔍 Verifying data in Snowflake...")
        
        cursor.execute(f"""
            SELECT COUNT(*) as count, COUNT(DISTINCT symbol) as symbols
            FROM {config.snowflake.database}.{config.snowflake.schema}.STOCK_DATA
        """)
        stock_count, stock_symbols_count = cursor.fetchone()
        print(f"📊 STOCK_DATA: {stock_count} rows, {stock_symbols_count} symbols")
        
        cursor.execute(f"""
            SELECT COUNT(*) as count, COUNT(DISTINCT symbol) as symbols
            FROM {config.snowflake.database}.{config.snowflake.schema}.CRYPTO_MINUTE_DATA
        """)
        crypto_count, crypto_symbols_count = cursor.fetchone()
        print(f"💎 CRYPTO_MINUTE_DATA: {crypto_count} rows, {crypto_symbols_count} symbols")
        
        print(f"\n✅ Load complete!")
        
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        parquet_file = sys.argv[1]
    else:
        # Default to the latest financial minute data parquet file
        data_dir = Path("data")
        parquet_files = list(data_dir.glob("financial_minute_data_*.parquet"))
        if not parquet_files:
            print("❌ No financial_minute_data_*.parquet files found in data directory")
            sys.exit(1)
        
        parquet_file = max(parquet_files, key=lambda p: p.stat().st_mtime)
        print(f"📁 Auto-detected: {parquet_file}")
    
    load_parquet_to_snowflake(parquet_file)
