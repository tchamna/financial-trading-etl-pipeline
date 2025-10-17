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
import time

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
            with open('config.json', 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                self.snowflake_config = config_data.get('snowflake', {})
        except Exception as e:
            logger.error(f"Failed to load Snowflake config: {e}")
            raise
        
        # User preferences from user_config.py
        try:
            self.enabled = self.config.snowflake.enabled
            self.warehouse = self.config.snowflake.warehouse
            self.database = self.config.snowflake.database
            self.schema = self.config.snowflake.schema
        except AttributeError:
            logger.warning("Snowflake settings not found in configuration, using defaults")
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
            # Connect without specifying warehouse initially
            self.connection = snowflake.connector.connect(
                account=self.snowflake_config.get('account'),
                user=self.snowflake_config.get('username'),
                password=self.snowflake_config.get('password'),
                role=self.snowflake_config.get('role', 'SYSADMIN')
            )
            self.cursor = self.connection.cursor(DictCursor)
            
            # Create warehouse if it doesn't exist
            try:
                self.cursor.execute(f"""
                    CREATE WAREHOUSE IF NOT EXISTS {self.warehouse}
                    WITH WAREHOUSE_SIZE = 'X-SMALL'
                    AUTO_SUSPEND = 60
                    AUTO_RESUME = TRUE
                    COMMENT = 'Warehouse for financial data processing'
                """)
                logger.info(f"✅ Warehouse {self.warehouse} created/verified")
            except Exception as e:
                logger.warning(f"Warehouse creation: {e}")
            
            # Now use the warehouse
            self.cursor.execute(f"USE WAREHOUSE {self.warehouse}")
            
            # Create database if it doesn't exist
            try:
                self.cursor.execute(f"""
                    CREATE DATABASE IF NOT EXISTS {self.database}
                    COMMENT = 'Financial trading data warehouse'
                """)
                logger.info(f"✅ Database {self.database} created/verified")
            except Exception as e:
                logger.warning(f"Database creation: {e}")
            
            # Use the database
            self.cursor.execute(f"USE DATABASE {self.database}")
            
            # Create schema if it doesn't exist
            self.create_schema_if_not_exists()
            
            # Create tables if they don't exist
            self.create_crypto_table()
            self.create_stock_table()
            
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
            
            -- Date and Time columns for better querying
            date DATE,
            time TIME,
            hour INT,
            minute INT,
            
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
            ingestion_timestamp TIMESTAMP_TZ,
            source STRING DEFAULT 'ETL_PIPELINE',
            
            -- Primary key
            CONSTRAINT pk_stock_data PRIMARY KEY (symbol, timestamp)
        )
        COMMENT = 'Historical stock market data with technical indicators and date/time components'
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
        
        # Create crypto minute data table for OHLCV intraday data
        sql_minute = f"""
        CREATE TABLE IF NOT EXISTS {self.database}.{self.schema}.CRYPTO_MINUTE_DATA (
            -- Identification
            symbol STRING NOT NULL,
            timestamp TIMESTAMP_NTZ NOT NULL,
            
            -- Date and Time columns for better querying
            date DATE,
            time TIME,
            hour INT,
            minute INT,
            
            -- OHLCV data
            open DECIMAL(18,8),
            high DECIMAL(18,8),
            low DECIMAL(18,8),
            close DECIMAL(18,8),
            volume DECIMAL(20,2),
            
            -- Metadata
            api_source STRING,
            interval STRING,
            load_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
            ingestion_timestamp TIMESTAMP_TZ,
            
            -- Primary key
            CONSTRAINT pk_crypto_minute_data PRIMARY KEY (symbol, timestamp)
        )
        COMMENT = 'Minute-level cryptocurrency OHLCV data with date/time components'
        """
        
        self.execute_sql(sql_minute)
        logger.info(f"✅ Crypto minute data table created/verified")
    
    def load_parquet_from_local(self, file_path: str, table_name: str) -> int:
        """
        Load data from local Parquet file into Snowflake (batched via write_pandas)
        
        Args:
            file_path: Path to Parquet file
            table_name: Target Snowflake table
            
        Returns:
            Number of rows loaded
        """
        try:
            start_time = time.time()
            
            # Read Parquet file
            df = pd.read_parquet(file_path)
            
            if df.empty:
                logger.warning(f"No data in {file_path}")
                return 0
            
            nrows_total = len(df)
            logger.info(f"📄 Read {nrows_total:,} rows from {file_path}")
            
            # Convert timestamp columns to datetime
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Bulk write with explicit chunk size (16MB chunks, ~10k rows typical)
            logger.info(f"📤 Uploading to {table_name} (batched)...")
            success, nchunks, nrows, _ = write_pandas(
                conn=self.connection,
                df=df,
                table_name=table_name.upper(),
                database=self.database,
                schema=self.schema,
                auto_create_table=False,  # We already created the table
                overwrite=False,  # Append mode
                chunk_size=10000  # Upload 10k rows per batch
            )
            
            elapsed = time.time() - start_time
            rate = nrows / elapsed if elapsed > 0 else 0
            
            if success:
                logger.info(f"✅ Loaded {nrows:,} rows from {file_path} to {table_name}")
                logger.info(f"   ⏱️  Time: {elapsed:.2f}s | Rate: {rate:,.0f} rows/sec | Chunks: {nchunks}")
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
    
    def load_data_file(self, file_path: str) -> Dict[str, int]:
        """
        Load data from a specific JSON file (batched via DataFrame + write_pandas)
        
        Args:
            file_path: Path to JSON file containing crypto/stock minute data
            
        Returns:
            Dictionary with load statistics
        """
        import json
        from pathlib import Path
        
        stats = {
            'stock_rows': 0,
            'crypto_rows': 0,
            'files_processed': 0,
            'errors': 0
        }
        
        try:
            # Ensure connection is established
            if not self.connection:
                if not self.connect():
                    logger.error("Failed to connect to Snowflake - cannot load data")
                    stats['errors'] = 1
                    return stats
            
            file_path = Path(file_path)
            start_time = time.time()
            
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                stats['errors'] = 1
                return stats
            
            filename = file_path.name.lower()
            
            # Route to Parquet handler if Parquet file
            if filename.endswith('.parquet'):
                logger.info(f"📥 Detected Parquet file: {filename}")
                try:
                    df = pd.read_parquet(file_path)
                    if df.empty:
                        logger.warning(f"No data in {file_path}")
                        return stats
                    
                    # Drop 'datetime' column if it exists (redundant with timestamp, and it's a reserved keyword)
                    if 'datetime' in df.columns:
                        df = df.drop('datetime', axis=1)
                    
                    logger.info(f"📄 Read {len(df):,} rows from {file_path}")
                    logger.info(f"   Columns: {list(df.columns)}")
                    
                    # Convert timestamp columns
                    if 'timestamp' in df.columns:
                        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
                    
                    # Use CRYPTO_MINUTE_DATA for Parquet files (more general table)
                    # Or detect based on filename/content
                    table_name = 'CRYPTO_MINUTE_DATA' if ('crypto' in filename or 'minute' in filename) else 'CRYPTO_MINUTE_DATA'
                    
                    rows_inserted = self._bulk_insert_dataframe(df, table_name)
                    stats['crypto_rows'] += rows_inserted
                    stats['files_processed'] = 1
                    
                    elapsed = time.time() - start_time
                    logger.info(f"✅ Parquet file processed in {elapsed:.2f}s")
                    return stats
                except Exception as e:
                    logger.error(f"Error loading Parquet file: {e}")
                    stats['errors'] = 1
                    return stats
            
            # Load JSON data
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            filename = file_path.name.lower()
            
            # Process combined financial_minute_data structure (crypto_data + stock_data)
            if isinstance(data, dict) and ('crypto_data' in data or 'stock_data' in data):
                crypto_records = data.get('crypto_data', []) or []
                stock_records = data.get('stock_data', []) or []
                
                # Load crypto data (batched)
                if crypto_records:
                    logger.info(f"📥 Processing {len(crypto_records):,} crypto records...")
                    crypto_df = self._records_to_dataframe(
                        crypto_records, 
                        table_type='CRYPTO_MINUTE_DATA'
                    )
                    if not crypto_df.empty:
                        rows_inserted = self._bulk_insert_dataframe(
                            crypto_df, 
                            'CRYPTO_MINUTE_DATA'
                        )
                        stats['crypto_rows'] += rows_inserted
                
                # Load stock data (batched)
                if stock_records:
                    logger.info(f"📥 Processing {len(stock_records):,} stock records...")
                    stock_df = self._records_to_dataframe(
                        stock_records, 
                        table_type='STOCK_DATA'
                    )
                    if not stock_df.empty:
                        rows_inserted = self._bulk_insert_dataframe(
                            stock_df, 
                            'STOCK_DATA'
                        )
                        stats['stock_rows'] += rows_inserted
            else:
                # Legacy structure handling
                if isinstance(data, list):
                    records = data
                elif isinstance(data, dict) and 'data' in data:
                    records = data['data']
                else:
                    records = [data]
                
                if not records:
                    logger.warning(f"No data found in {file_path}")
                    return stats
                
                # Heuristic: minute crypto files usually include 'minute' or 'crypto' in filename
                table_name = 'CRYPTO_MINUTE_DATA' if ('crypto' in filename or 'minute' in filename) else 'STOCK_DATA'
                logger.info(f"📥 Processing {len(records):,} {table_name} records...")
                
                df = self._records_to_dataframe(records, table_type=table_name)
                if not df.empty:
                    rows_inserted = self._bulk_insert_dataframe(df, table_name)
                    if table_name == 'CRYPTO_MINUTE_DATA':
                        stats['crypto_rows'] += rows_inserted
                    else:
                        stats['stock_rows'] += rows_inserted
            
            stats['files_processed'] = 1
            elapsed = time.time() - start_time
            total_rows = stats['crypto_rows'] + stats['stock_rows']
            rate = total_rows / elapsed if elapsed > 0 else 0
            logger.info(f"✅ Loaded {total_rows:,} rows from {file_path} in {elapsed:.2f}s ({rate:,.0f} rows/sec)")
            
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {e}")
            stats['errors'] += 1
        
        return stats
    
    def _records_to_dataframe(self, records: List[Dict], table_type: str) -> pd.DataFrame:
        """
        Convert a list of records to a properly typed DataFrame for bulk insert
        
        Args:
            records: List of record dictionaries
            table_type: Type of table ('CRYPTO_MINUTE_DATA' or 'STOCK_DATA')
            
        Returns:
            pandas DataFrame ready for write_pandas
        """
        rows = []
        for i, record in enumerate(records):
            try:
                if not isinstance(record, dict):
                    logger.warning(f"Skipping non-dict record at index {i}")
                    continue
                
                ts_value = record.get('datetime') or record.get('timestamp')
                
                if table_type == 'CRYPTO_MINUTE_DATA':
                    row = {
                        'SYMBOL': record.get('symbol'),
                        'TIMESTAMP': ts_value,
                        'OPEN': float(record.get('open', 0)),
                        'HIGH': float(record.get('high', 0)),
                        'LOW': float(record.get('low', 0)),
                        'CLOSE': float(record.get('close', 0)),
                        'VOLUME': float(record.get('volume', 0)),
                        'API_SOURCE': record.get('api_source'),
                        'INTERVAL': record.get('interval')
                    }
                else:  # STOCK_DATA
                    row = {
                        'SYMBOL': record.get('symbol'),
                        'TIMESTAMP': ts_value,
                        'OPEN': float(record.get('open', 0)),
                        'HIGH': float(record.get('high', 0)),
                        'LOW': float(record.get('low', 0)),
                        'CLOSE': float(record.get('close', 0)),
                        'VOLUME': float(record.get('volume', 0))
                    }
                
                rows.append(row)
            
            except Exception as e:
                logger.warning(f"Skipping record {i}: {e}")
                if i < 3:
                    logger.debug(f"   Record: {record}")
                continue
        
        if not rows:
            logger.warning(f"No valid records converted for {table_type}")
            return pd.DataFrame()
        
        df = pd.DataFrame(rows)
        # Convert timestamp to datetime
        if 'TIMESTAMP' in df.columns:
            df['TIMESTAMP'] = pd.to_datetime(df['TIMESTAMP'], errors='coerce')
        
        logger.info(f"   ✓ Converted {len(df):,} records to DataFrame")
        return df
    
    def _bulk_insert_direct(self, df: pd.DataFrame, table_name: str) -> int:
        """
        Bulk insert DataFrame directly using batch INSERT VALUES (bypasses S3 staging)
        Used as fallback when write_pandas S3 staging fails
        
        Args:
            df: DataFrame to insert
            table_name: Target Snowflake table
            
        Returns:
            Number of rows inserted
        """
        try:
            if df.empty:
                return 0
            
            start_time = time.time()
            logger.info(f"   📤 Direct bulk inserting {len(df):,} rows to {table_name}...")
            
            # Convert datetime columns to strings for Snowflake
            df_copy = df.copy()
            for col in df_copy.columns:
                if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
                    df_copy[col] = df_copy[col].astype(str)
            
            # Build multi-row INSERT with batched VALUES
            # Use unquoted column names (converted to uppercase by Snowflake)
            # They will map to uppercase table column names correctly
            col_names = ', '.join(df_copy.columns)
            total_inserted = 0
            batch_size = 100  # Smaller batches for VALUES inserts
            
            cursor = self.connection.cursor()
            
            for batch_idx in range(0, len(df_copy), batch_size):
                batch_df = df_copy.iloc[batch_idx:batch_idx+batch_size]
                
                # Build VALUES clause for this batch
                rows_values = []
                for _, row in batch_df.iterrows():
                    row_values = ', '.join([
                        f"'{str(val).replace(chr(39), chr(39)+chr(39))}'"  # Escape single quotes
                        if pd.notna(val) and not isinstance(val, (int, float))
                        else str(val) if pd.notna(val) else 'NULL'
                        for val in row
                    ])
                    rows_values.append(f"({row_values})")
                
                values_clause = ', '.join(rows_values)
                insert_sql = f"INSERT INTO {self.database}.{self.schema}.{table_name.upper()} ({col_names}) VALUES {values_clause}"
                
                # Debug: print first row SQL
                if batch_idx == 0:
                    first_sql = insert_sql[:200]  # First 200 chars
                    logger.info(f"   DEBUG: SQL preview: {first_sql}...")
                
                cursor.execute(insert_sql)
                total_inserted += len(batch_df)
                logger.info(f"   ✓ Inserted batch: {batch_idx//batch_size + 1} ({len(batch_df)} rows)")
            
            self.connection.commit()
            elapsed = time.time() - start_time
            rate = total_inserted / elapsed if elapsed > 0 else 0
            
            logger.info(f"   ✅ Direct inserted {total_inserted:,} rows in {elapsed:.2f}s ({rate:,.0f} rows/sec)")
            return total_inserted
        
        except Exception as e:
            logger.warning(f"Direct insert failed: {e}")
            return 0
    
    def _bulk_insert_dataframe(self, df: pd.DataFrame, table_name: str) -> int:
        """
        Bulk insert DataFrame into Snowflake using write_pandas (with fallback to direct insert)
        
        Args:
            df: DataFrame to insert
            table_name: Target Snowflake table
            
        Returns:
            Number of rows inserted
        """
        try:
            start_time = time.time()
            logger.info(f"   📤 Bulk inserting {len(df):,} rows to {table_name}...")
            
            success, nchunks, nrows, _ = write_pandas(
                conn=self.connection,
                df=df,
                table_name=table_name.upper(),
                database=self.database,
                schema=self.schema,
                auto_create_table=False,
                overwrite=False,
                chunk_size=10000,  # 10k rows per batch
                use_logical_type=True  # Handle timezone-aware datetimes correctly
            )
            
            elapsed = time.time() - start_time
            rate = nrows / elapsed if elapsed > 0 else 0
            
            if success:
                logger.info(f"   ✅ Inserted {nrows:,} rows in {elapsed:.2f}s ({rate:,.0f} rows/sec) via {nchunks} batches")
                return nrows
            else:
                logger.error(f"   ❌ write_pandas failed for {table_name}")
                return 0
        
        except Exception as e:
            logger.warning(f"write_pandas error (likely S3 cert issue): {e}")
            logger.info("Attempting fallback direct INSERT method...")
            try:
                return self._bulk_insert_direct(df, table_name)
            except Exception as e2:
                logger.error(f"Direct insert also failed: {e2}")
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
            # Use Snowflake's MERGE to keep only the latest record for each symbol/timestamp combination
            # Note: Since tables don't have updated_at, we'll just keep first occurrence
            sql = f"""
            CREATE OR REPLACE TEMPORARY TABLE {table_name}_temp AS
            SELECT * FROM {self.database}.{self.schema}.{table_name}
            QUALIFY ROW_NUMBER() OVER (PARTITION BY symbol, timestamp ORDER BY timestamp) = 1
            """
            self.execute_sql(sql)
            
            # Replace original table with deduplicated data
            sql2 = f"""
            CREATE OR REPLACE TABLE {self.database}.{self.schema}.{table_name} LIKE {table_name}_temp
            """
            self.execute_sql(sql2)
            
            sql3 = f"""
            INSERT INTO {self.database}.{self.schema}.{table_name}
            SELECT * FROM {table_name}_temp
            """
            self.execute_sql(sql3)
            
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
        
        # Use the database
        loader.cursor.execute(f"USE DATABASE {loader.database}")
        
        # Create schemas and tables
        print("\n🏗️  Creating schemas and tables...")
        loader.create_schema_if_not_exists()
        loader.create_stock_table()
        loader.create_crypto_table()
        
        # Load data
        print("\n📥 Loading data...")
        import sys
        if len(sys.argv) > 1:
            # Load specific file from command line
            file_path = sys.argv[1]
            print(f"   Loading from: {file_path}")
            stats = loader.load_data_file(file_path)
        else:
            # Load latest data from data directory
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
