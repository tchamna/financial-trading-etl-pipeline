#!/usr/bin/env python3
"""
Simple Direct Loader for Snowflake
Loads only the essential columns from Parquet files
"""

import sys
from pathlib import Path
import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

# Add project root to path
sys.path.append('/opt/airflow')
from config import PipelineConfig

def load_data_to_snowflake(parquet_file):
    """Load data from Parquet file to Snowflake."""
    
    print(f"\n📥 Loading data from: {parquet_file}")
    print("=" * 80)
    
    # Load configuration
    config = PipelineConfig()
    sf_config = config.snowflake
    
    # Read Parquet file
    df = pd.read_parquet(parquet_file)
    print(f"📊 Read {len(df)} records from Parquet")
    
    # Define stock symbols
    stock_symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'NVDA', 'META']
    
    # Prepare stock data with only the columns that exist in the table
    stock_df = df[df['symbol'].isin(stock_symbols)].copy()
    stock_df = stock_df[['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume']]
    stock_df.columns = ['SYMBOL', 'TIMESTAMP', 'OPEN_PRICE', 'HIGH_PRICE', 'LOW_PRICE', 'CLOSE_PRICE', 'VOLUME']
    stock_df = stock_df.reset_index(drop=True)
    
    # Prepare crypto data (uses different column names than stock data)
    crypto_df = df[~df['symbol'].isin(stock_symbols)].copy()
    crypto_df = crypto_df[['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume']]
    crypto_df.columns = ['SYMBOL', 'TIMESTAMP', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME']
    crypto_df = crypto_df.reset_index(drop=True)
    
    # Connect to Snowflake
    print("\n🔗 Connecting to Snowflake...")
    conn = snowflake.connector.connect(
        account=sf_config.account,
        user=sf_config.username,
        password=sf_config.password,
        warehouse=sf_config.warehouse,
        database=sf_config.database,
        schema=sf_config.schema
    )
    
    try:
        # Load stock data
        if len(stock_df) > 0:
            print(f"\n📊 Loading {len(stock_df)} stock records...")
            success, nchunks, nrows, _ = write_pandas(
                conn, 
                stock_df, 
                'STOCK_DATA',
                auto_create_table=False,
                use_logical_type=True,
                overwrite=False
            )
            print(f"   ✅ Loaded {nrows} stock records")
        
        # Load crypto data to CRYPTO_MINUTE_DATA table (not CRYPTO_DATA which is for daily aggregates)
        if len(crypto_df) > 0:
            print(f"\n💰 Loading {len(crypto_df)} crypto records...")
            success, nchunks, nrows, _ = write_pandas(
                conn, 
                crypto_df, 
                'CRYPTO_MINUTE_DATA',
                auto_create_table=False,
                use_logical_type=True,
                overwrite=False
            )
            print(f"   ✅ Loaded {nrows} crypto records")
        
        # Verify the data
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), COUNT(DISTINCT symbol) FROM STOCK_DATA")
        stock_count, stock_symbols_count = cursor.fetchone()
        cursor.execute("SELECT COUNT(*), COUNT(DISTINCT symbol) FROM CRYPTO_MINUTE_DATA")
        crypto_count, crypto_symbols_count = cursor.fetchone()
        
        print("\n📈 FINAL COUNTS IN SNOWFLAKE:")
        print("=" * 80)
        print(f"   📊 Stock Data: {stock_count:,} records, {stock_symbols_count} symbols")
        print(f"   💰 Crypto Minute Data: {crypto_count:,} records, {crypto_symbols_count} symbols")
        
        cursor.close()
        
    finally:
        conn.close()
        print("\n✅ Load complete!")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        parquet_file = sys.argv[1]
    else:
        parquet_file = "/opt/airflow/data/financial_minute_data_20251015.parquet"
    
    load_data_to_snowflake(parquet_file)
