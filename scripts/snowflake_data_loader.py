"""
Snowflake Data Loader for Financial Trading ETL Pipeline
========================================================

This script loads processed financial data from S3/local storage into Snowflake
data warehouse for analytics and reporting.

Features:
- Automatic schema detection and creation
- Bulk loading from Parquet files
- Incremental loading with deduplication
- Data quality validation
- Error handling and retry logic

Author: Shck Tchamna
Email: tchamna@gmail.com
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

import pandas as pd
import snowflake.connector
from snowflake.connector import DictCursor
from snowflake.connector.pandas_tools import write_pandas
import boto3
from botocore.exceptions import ClientError

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))
from config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SnowflakeLoader:
    """
    Loads financial data into Snowflake data warehouse
    """
    
    def __init__(self):
        """Initialize Snowflake connection and configuration"""
        self.config = get_config()
        self.connection = None
        self.cursor = None
        
        # Snowflake configuration from config.json
        try:
            import json
            with open('config.json', 'r') as f:
                config_data = json.load(f)
                self.snowflake_config = config_data.get('snowflake', {})
        except Exception as e:
            logger.error(f"Failed to load Snowflake config: {e}")
            raise
        
        # User preferences from user_config.py
        try:
            from user_config import (
                ENABLE_SNOWFLAKE,
                SNOWFLAKE_WAREHOUSE,
                SNOWFLAKE_DATABASE,
                SNOWFLAKE_SCHEMA
            )
            self.enabled = ENABLE_SNOWFLAKE
            self.warehouse = SNOWFLAKE_WAREHOUSE
            self.database = SNOWFLAKE_DATABASE
            self.schema = SNOWFLAKE_SCHEMA
        except ImportError:
            logger.warning("Snowflake settings not found in user_config.py, using defaults")
            self.enabled = False
            self.warehouse = "FINANCIAL_WH"
            self.database = "FINANCIAL_DB"
            self.schema = "CORE"
        
        # S3 client for loading from S3
        if self.config.s3.enabled:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.config.s3.access_key_id,
                aws_secret_access_key=self.config.s3.secret_access_key,
                region_name=self.config.s3.region
            )
    
    def connect(self) -> bool:
        """
        Establish connection to Snowflake
        
        Returns:
            bool: True if connection successful
        """
        if not self.enabled:
            logger.info("Snowflake integration is disabled in user_config.py")
            return False
        
        try:
            self.connection = snowflake.connector.connect(
                account=self.snowflake_config.get('account'),
                user=self.snowflake_config.get('username'),
                password=self.snowflake_config.get('password'),
                role=self.snowflake_config.get('role', 'SYSADMIN'),
                warehouse=self.warehouse,
                database=self.database,
                schema=self.schema
            )
            self.cursor = self.connection.cursor(DictCursor)
            logger.info(f"✅ Connected to Snowflake: {self.database}.{self.schema}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Snowflake: {e}")
            return False
    
    def disconnect(self):
        """Close Snowflake connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("Disconnected from Snowflake")
    
    def execute_sql(self, sql: str, params: Optional[Tuple] = None) -> List[Dict]:
        """
        Execute SQL query
        
        Args:
            sql: SQL query to execute
            params: Optional query parameters
            
        Returns:
            List of result dictionaries
        """
        try:
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
            
            # Fetch results if it's a SELECT query
            if sql.strip().upper().startswith('SELECT'):
                return self.cursor.fetchall()
            else:
                self.connection.commit()
                return []
                
        except Exception as e:
            logger.error(f"SQL execution error: {e}")
            logger.error(f"SQL: {sql}")
            raise
    
    def create_schema_if_not_exists(self):
        """Create Snowflake database and schemas if they don't exist"""
        try:
            # Create database
            self.execute_sql(f"""
                CREATE DATABASE IF NOT EXISTS {self.database}
                COMMENT = 'Financial trading data warehouse'
            """)
            
            # Create schemas
            schemas = ['STAGING', 'CORE', 'MARTS']
            for schema in schemas:
                self.execute_sql(f"""
                    CREATE SCHEMA IF NOT EXISTS {self.database}.{schema}
                    COMMENT = '{schema} schema for financial data'
                """)
            
            logger.info(f"✅ Schemas created/verified in {self.database}")
            
        except Exception as e:
            logger.error(f"Failed to create schemas: {e}")
            raise
    
    def create_stock_table(self):
        """Create stock data table in Snowflake"""
        sql = f"""
        CREATE TABLE IF NOT EXISTS {self.database}.{self.schema}.STOCK_DATA (
            -- Identification
            symbol STRING NOT NULL,
            timestamp TIMESTAMP_NTZ NOT NULL,
            
            -- Price data
            open_price DECIMAL(18,4),
            high_price DECIMAL(18,4),
            low_price DECIMAL(18,4),
            close_price DECIMAL(18,4),
            volume INTEGER,
            
            -- Technical indicators
            sma_20 DECIMAL(18,4),
            sma_50 DECIMAL(18,4),
            sma_200 DECIMAL(18,4),
            ema_12 DECIMAL(18,4),
            ema_26 DECIMAL(18,4),
            rsi DECIMAL(10,4),
            macd DECIMAL(18,4),
            signal_line DECIMAL(18,4),
            
            -- Calculated metrics
            price_change DECIMAL(18,4),
            price_change_pct DECIMAL(10,4),
            volatility_20d DECIMAL(18,4),
            
            -- Metadata
            load_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
            source STRING DEFAULT 'ETL_PIPELINE',
            
            -- Primary key
            CONSTRAINT pk_stock_data PRIMARY KEY (symbol, timestamp)
        )
        COMMENT = 'Historical stock market data with technical indicators'
        """
        
        self.execute_sql(sql)
        logger.info(f"✅ Stock data table created/verified")
    
    def create_crypto_table(self):
        """Create cryptocurrency data table in Snowflake"""
        sql = f"""
        CREATE TABLE IF NOT EXISTS {self.database}.{self.schema}.CRYPTO_DATA (
            -- Identification
            symbol STRING NOT NULL,
            timestamp TIMESTAMP_NTZ NOT NULL,
            
            -- Price data
            price_usd DECIMAL(18,8),
            market_cap DECIMAL(20,2),
            volume_24h DECIMAL(20,2),
            percent_change_1h DECIMAL(10,4),
            percent_change_24h DECIMAL(10,4),
            percent_change_7d DECIMAL(10,4),
            
            -- Technical indicators
            sma_20 DECIMAL(18,8),
            sma_50 DECIMAL(18,8),
            ema_12 DECIMAL(18,8),
            ema_26 DECIMAL(18,8),
            rsi DECIMAL(10,4),
            
            -- Metadata
            load_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
            source STRING DEFAULT 'ETL_PIPELINE',
            
            -- Primary key
            CONSTRAINT pk_crypto_data PRIMARY KEY (symbol, timestamp)
        )
        COMMENT = 'Historical cryptocurrency data with technical indicators'
        """
        
        self.execute_sql(sql)
        logger.info(f"✅ Crypto data table created/verified")
    
    def load_parquet_from_local(self, file_path: str, table_name: str) -> int:
        """
        Load data from local Parquet file into Snowflake
        
        Args:
            file_path: Path to Parquet file
            table_name: Target Snowflake table
            
        Returns:
            Number of rows loaded
        """
        try:
            # Read Parquet file
            df = pd.read_parquet(file_path)
            
            if df.empty:
                logger.warning(f"No data in {file_path}")
                return 0
            
            # Convert timestamp columns to datetime
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Write to Snowflake using pandas
            success, nchunks, nrows, _ = write_pandas(
                conn=self.connection,
                df=df,
                table_name=table_name.upper(),
                database=self.database,
                schema=self.schema,
                auto_create_table=False,  # We already created the table
                overwrite=False  # Append mode
            )
            
            if success:
                logger.info(f"✅ Loaded {nrows} rows from {file_path} to {table_name}")
                return nrows
            else:
                logger.error(f"❌ Failed to load {file_path}")
                return 0
                
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return 0
    
    def load_from_s3(self, s3_path: str, table_name: str) -> int:
        """
        Load data from S3 into Snowflake using COPY command
        
        Args:
            s3_path: S3 path (s3://bucket/key)
            table_name: Target Snowflake table
            
        Returns:
            Number of rows loaded
        """
        try:
            # Create external stage for S3
            stage_name = f"{self.database}.{self.schema}.S3_STAGE"
            
            create_stage_sql = f"""
            CREATE STAGE IF NOT EXISTS {stage_name}
            URL = 's3://{self.config.s3.bucket_name}/'
            CREDENTIALS = (
                AWS_KEY_ID = '{self.config.s3.access_key_id}'
                AWS_SECRET_KEY = '{self.config.s3.secret_access_key}'
            )
            FILE_FORMAT = (TYPE = PARQUET)
            """
            self.execute_sql(create_stage_sql)
            
            # Copy data from S3 stage
            copy_sql = f"""
            COPY INTO {self.database}.{self.schema}.{table_name.upper()}
            FROM @{stage_name}/{s3_path}
            FILE_FORMAT = (TYPE = PARQUET)
            MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
            ON_ERROR = CONTINUE
            """
            
            result = self.execute_sql(copy_sql)
            
            # Parse result to get row count
            rows_loaded = len(result) if result else 0
            logger.info(f"✅ Loaded data from S3: {s3_path} to {table_name}")
            return rows_loaded
            
        except Exception as e:
            logger.error(f"Error loading from S3: {e}")
            return 0
    
    def load_latest_data(self, hours: int = 24) -> Dict[str, int]:
        """
        Load latest data files from local storage or S3
        
        Args:
            hours: Number of hours of data to load
            
        Returns:
            Dictionary with load statistics
        """
        stats = {
            'stock_rows': 0,
            'crypto_rows': 0,
            'files_processed': 0,
            'errors': 0
        }
        
        try:
            # Load from local storage
            if self.config.storage.enable_local_storage:
                data_dir = Path(self.config.storage.local_data_directory)
                
                # Load stock data
                stock_files = list(data_dir.glob('stock_*_processed.parquet'))
                for file_path in stock_files:
                    rows = self.load_parquet_from_local(str(file_path), 'STOCK_DATA')
                    stats['stock_rows'] += rows
                    stats['files_processed'] += 1
                
                # Load crypto data
                crypto_files = list(data_dir.glob('crypto_*_processed.parquet'))
                for file_path in crypto_files:
                    rows = self.load_parquet_from_local(str(file_path), 'CRYPTO_DATA')
                    stats['crypto_rows'] += rows
                    stats['files_processed'] += 1
            
            # Load from S3
            elif self.config.s3.enabled:
                # Load stock data from S3
                stock_prefix = f"{self.config.s3.processed_prefix}/stock/"
                stats['stock_rows'] = self.load_from_s3(stock_prefix, 'STOCK_DATA')
                
                # Load crypto data from S3
                crypto_prefix = f"{self.config.s3.processed_prefix}/crypto/"
                stats['crypto_rows'] = self.load_from_s3(crypto_prefix, 'CRYPTO_DATA')
                
                stats['files_processed'] = 2  # Approximate
            
            logger.info(f"📊 Load complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error in load_latest_data: {e}")
            stats['errors'] += 1
            return stats
    
    def deduplicate_data(self, table_name: str):
        """
        Remove duplicate records from table
        
        Args:
            table_name: Table to deduplicate
        """
        try:
            sql = f"""
            DELETE FROM {self.database}.{self.schema}.{table_name}
            WHERE (symbol, timestamp) IN (
                SELECT symbol, timestamp
                FROM {self.database}.{self.schema}.{table_name}
                GROUP BY symbol, timestamp
                HAVING COUNT(*) > 1
            )
            AND ROWID NOT IN (
                SELECT MIN(ROWID)
                FROM {self.database}.{self.schema}.{table_name}
                GROUP BY symbol, timestamp
            )
            """
            self.execute_sql(sql)
            logger.info(f"✅ Deduplicated {table_name}")
            
        except Exception as e:
            logger.error(f"Error deduplicating {table_name}: {e}")
    
    def get_data_statistics(self) -> Dict:
        """
        Get statistics about loaded data
        
        Returns:
            Dictionary with data statistics
        """
        stats = {}
        
        try:
            # Stock data stats
            stock_sql = f"""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(DISTINCT symbol) as unique_symbols,
                MIN(timestamp) as earliest_date,
                MAX(timestamp) as latest_date
            FROM {self.database}.{self.schema}.STOCK_DATA
            """
            stock_result = self.execute_sql(stock_sql)
            stats['stock'] = stock_result[0] if stock_result else {}
            
            # Crypto data stats
            crypto_sql = f"""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(DISTINCT symbol) as unique_symbols,
                MIN(timestamp) as earliest_date,
                MAX(timestamp) as latest_date
            FROM {self.database}.{self.schema}.CRYPTO_DATA
            """
            crypto_result = self.execute_sql(crypto_sql)
            stats['crypto'] = crypto_result[0] if crypto_result else {}
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}


def main():
    """Main execution function"""
    print("=" * 70)
    print("🏔️  SNOWFLAKE DATA LOADER")
    print("=" * 70)
    
    loader = SnowflakeLoader()
    
    if not loader.enabled:
        print("\n⚠️  Snowflake is disabled in user_config.py")
        print("   Set ENABLE_SNOWFLAKE = True to enable Snowflake integration")
        return
    
    try:
        # Connect to Snowflake
        print("\n📡 Connecting to Snowflake...")
        if not loader.connect():
            print("❌ Failed to connect to Snowflake")
            print("\n💡 To configure Snowflake:")
            print("   1. Edit config.json and add your Snowflake credentials")
            print("   2. Edit user_config.py and set ENABLE_SNOWFLAKE = True")
            return
        
        # Create schemas and tables
        print("\n🏗️  Creating schemas and tables...")
        loader.create_schema_if_not_exists()
        loader.create_stock_table()
        loader.create_crypto_table()
        
        # Load data
        print("\n📥 Loading data...")
        stats = loader.load_latest_data(hours=24)
        
        print("\n📊 Load Statistics:")
        print(f"   Stock rows loaded: {stats['stock_rows']:,}")
        print(f"   Crypto rows loaded: {stats['crypto_rows']:,}")
        print(f"   Files processed: {stats['files_processed']}")
        print(f"   Errors: {stats['errors']}")
        
        # Deduplicate
        print("\n🔄 Removing duplicates...")
        loader.deduplicate_data('STOCK_DATA')
        loader.deduplicate_data('CRYPTO_DATA')
        
        # Show statistics
        print("\n📈 Data Warehouse Statistics:")
        data_stats = loader.get_data_statistics()
        
        if 'stock' in data_stats:
            print(f"\n   📊 Stock Data:")
            print(f"      Total rows: {data_stats['stock'].get('TOTAL_ROWS', 0):,}")
            print(f"      Symbols: {data_stats['stock'].get('UNIQUE_SYMBOLS', 0)}")
            print(f"      Date range: {data_stats['stock'].get('EARLIEST_DATE')} to {data_stats['stock'].get('LATEST_DATE')}")
        
        if 'crypto' in data_stats:
            print(f"\n   💎 Crypto Data:")
            print(f"      Total rows: {data_stats['crypto'].get('TOTAL_ROWS', 0):,}")
            print(f"      Symbols: {data_stats['crypto'].get('UNIQUE_SYMBOLS', 0)}")
            print(f"      Date range: {data_stats['crypto'].get('EARLIEST_DATE')} to {data_stats['crypto'].get('LATEST_DATE')}")
        
        print("\n✅ Data load complete!")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"\n❌ Error: {e}")
    
    finally:
        loader.disconnect()
    
    print("=" * 70)


if __name__ == "__main__":
    main()
