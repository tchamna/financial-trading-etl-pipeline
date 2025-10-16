"""
Load crypto minute data from S3 to Snowflake
Supports both direct COPY INTO and download+bulk insert approaches
"""

import sys
from pathlib import Path
import json
import time
import tempfile
import os

# Add the scripts directory to path
sys.path.append(str(Path(__file__).parent / 'scripts'))

from snowflake_data_loader import SnowflakeLoader
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_from_s3_copy_into(loader, s3_path, aws_key_id=None, aws_secret_key=None):
    """
    Use Snowflake's COPY INTO command to load directly from S3 (fastest method)
    
    Args:
        loader: SnowflakeLoader instance
        s3_path: S3 path like 's3://bucket-name/path/to/files/'
        aws_key_id: AWS Access Key ID (optional if using IAM roles)
        aws_secret_key: AWS Secret Access Key (optional if using IAM roles)
    """
    try:
        logger.info(f"Loading data from S3 using COPY INTO: {s3_path}")
        
        # Create file format for JSON parsing
        logger.info("Creating file format for JSON parsing...")
        create_format_sql = """
        CREATE OR REPLACE FILE FORMAT CRYPTO_JSON_FORMAT
        TYPE = 'JSON'
        STRIP_OUTER_ARRAY = FALSE
        """
        loader.cursor.execute(create_format_sql)
        
        # Build COPY INTO command
        if aws_key_id and aws_secret_key:
            credentials = f"""
            CREDENTIALS = (
                AWS_KEY_ID = '{aws_key_id}'
                AWS_SECRET_KEY = '{aws_secret_key}'
            )
            """
        else:
            # Use IAM role or instance profile
            credentials = ""
        
        copy_sql = f"""
        COPY INTO {loader.database}.{loader.schema}.CRYPTO_MINUTE_DATA
        (symbol, timestamp, open, high, low, close, volume, api_source, interval)
        FROM (
            SELECT 
                $1:symbol::STRING,
                REPLACE($1:timestamp::STRING, ' UTC', ''),
                $1:open::FLOAT,
                $1:high::FLOAT,
                $1:low::FLOAT,
                $1:close::FLOAT,
                $1:volume::FLOAT,
                $1:api_source::STRING,
                $1:interval::STRING
            FROM @~/{s3_path}
        )
        FILE_FORMAT = (FORMAT_NAME = 'CRYPTO_JSON_FORMAT')
        {credentials}
        ON_ERROR = 'CONTINUE'
        """
        
        logger.info("Executing COPY INTO command...")
        start_time = time.time()
        loader.cursor.execute(copy_sql)
        result = loader.cursor.fetchone()
        elapsed = time.time() - start_time
        
        logger.info(f"✅ COPY INTO completed in {elapsed:.2f}s")
        logger.info(f"   Rows loaded: {result['ROWS_LOADED']}")
        logger.info(f"   Rows parsed: {result['ROWS_PARSED']}")
        logger.info(f"   Errors: {result['ERRORS_SEEN']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error loading from S3 with COPY INTO: {e}")
        import traceback
        traceback.print_exc()
        return False

def load_from_s3_download(loader, s3_bucket, s3_prefix):
    """
    Download files from S3 and use bulk insert method
    More flexible but slower than COPY INTO
    
    Args:
        loader: SnowflakeLoader instance
        s3_bucket: S3 bucket name
        s3_prefix: Prefix/path in S3 (e.g., 'crypto-data/')
    """
    try:
        import boto3
        
        logger.info(f"Downloading files from S3: s3://{s3_bucket}/{s3_prefix}")
        
        # Initialize S3 client
        s3_client = boto3.client('s3')
        
        # List objects in S3
        response = s3_client.list_objects_v2(
            Bucket=s3_bucket,
            Prefix=s3_prefix
        )
        
        if 'Contents' not in response:
            logger.warning("No files found in S3")
            return False
        
        # Filter for crypto minute data JSON files
        json_files = [
            obj for obj in response['Contents']
            if obj['Key'].endswith('.json') and 'crypto_minute_data' in obj['Key']
        ]
        
        logger.info(f"Found {len(json_files)} crypto minute data files in S3")
        
        total_stats = {
            'crypto_rows': 0,
            'files_processed': 0,
            'errors': 0
        }
        
        overall_start = time.time()
        
        # Process each file
        for s3_obj in json_files:
            s3_key = s3_obj['Key']
            file_name = os.path.basename(s3_key)
            
            logger.info(f"\n📁 Processing: {file_name}")
            logger.info("-"*70)
            
            try:
                # Download file to memory
                file_obj = s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
                file_content = file_obj['Body'].read()
                
                # Parse JSON
                data = json.loads(file_content)
                
                # Extract crypto_data array
                if isinstance(data, list) and len(data) > 0:
                    data_container = data[0]
                    if isinstance(data_container, dict) and 'crypto_data' in data_container:
                        records = data_container['crypto_data']
                        logger.info(f"Found {len(records):,} records in {file_name}")
                        logger.info(f"  Collection time: {data_container.get('collection_time')}")
                        logger.info(f"  Target date: {data_container.get('target_date')}")
                    else:
                        logger.error(f"Invalid data structure in {file_name}")
                        total_stats['errors'] += 1
                        continue
                else:
                    logger.error(f"Invalid data structure in {file_name}")
                    total_stats['errors'] += 1
                    continue
                
                # Prepare batch data
                batch_data = []
                skipped = 0
                
                for record in records:
                    try:
                        if not isinstance(record, dict):
                            skipped += 1
                            continue
                        
                        # Convert timestamp
                        timestamp_str = record.get('timestamp', '').replace(' UTC', '')
                        
                        if not record.get('symbol') or not timestamp_str:
                            skipped += 1
                            continue
                        
                        row_tuple = (
                            record.get('symbol'),
                            timestamp_str,
                            float(record.get('open', 0)),
                            float(record.get('high', 0)),
                            float(record.get('low', 0)),
                            float(record.get('close', 0)),
                            float(record.get('volume', 0)),
                            record.get('api_source'),
                            record.get('interval')
                        )
                        
                        batch_data.append(row_tuple)
                        
                    except Exception as e:
                        logger.error(f"Error preparing record: {e}")
                        skipped += 1
                
                if not batch_data:
                    logger.warning(f"No valid data in {file_name}")
                    continue
                
                logger.info(f"  Prepared {len(batch_data):,} rows ({skipped} skipped)")
                
                # Bulk insert
                sql = f"""
                INSERT INTO {loader.database}.{loader.schema}.CRYPTO_MINUTE_DATA
                (symbol, timestamp, open, high, low, close, volume, api_source, interval)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                insert_start = time.time()
                logger.info("  Executing bulk insert...")
                
                # Insert in chunks
                chunk_size = 10000
                total_inserted = 0
                
                for i in range(0, len(batch_data), chunk_size):
                    chunk = batch_data[i:i+chunk_size]
                    loader.cursor.executemany(sql, chunk)
                    total_inserted += len(chunk)
                    logger.info(f"    Inserted {total_inserted:,}/{len(batch_data):,} rows...")
                
                loader.connection.commit()
                
                insert_time = time.time() - insert_start
                logger.info(f"✅ Successfully loaded {len(batch_data):,} rows from {file_name}")
                logger.info(f"   Insert time: {insert_time:.2f}s | Speed: {len(batch_data)/insert_time:.0f} rows/second")
                
                total_stats['crypto_rows'] += len(batch_data)
                total_stats['files_processed'] += 1
                
            except Exception as e:
                logger.error(f"Error processing {file_name}: {e}")
                total_stats['errors'] += 1
        
        overall_time = time.time() - overall_start
        
        # Summary
        logger.info("\n" + "="*70)
        logger.info("📊 S3 LOAD SUMMARY")
        logger.info("="*70)
        logger.info(f"✅ Files processed: {total_stats['files_processed']}/{len(json_files)}")
        logger.info(f"✅ Total rows loaded: {total_stats['crypto_rows']:,}")
        logger.info(f"⚠️  Errors: {total_stats['errors']}")
        logger.info(f"⏱️  Total time: {overall_time:.2f}s")
        logger.info(f"🚀 Overall speed: {total_stats['crypto_rows']/overall_time:.0f} rows/second")
        logger.info("="*70)
        
        return True
        
    except ImportError:
        logger.error("boto3 not installed. Install with: pip install boto3")
        return False
    except Exception as e:
        logger.error(f"Error loading from S3: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Load crypto data from S3 to Snowflake')
    parser.add_argument('--method', choices=['copy', 'download'], default='download',
                       help='Method to use: copy (COPY INTO - fastest) or download (bulk insert)')
    parser.add_argument('--bucket', required=True,
                       help='S3 bucket name (e.g., financial-trading-data)')
    parser.add_argument('--prefix', default='crypto-minute-data/',
                       help='S3 prefix/path (e.g., crypto-minute-data/)')
    parser.add_argument('--aws-key-id', 
                       help='AWS Access Key ID (optional for COPY INTO with IAM)')
    parser.add_argument('--aws-secret-key',
                       help='AWS Secret Access Key (optional for COPY INTO with IAM)')
    
    args = parser.parse_args()
    
    # Initialize Snowflake loader
    logger.info("Initializing Snowflake loader...")
    loader = SnowflakeLoader()
    
    # Connect to Snowflake
    logger.info("Connecting to Snowflake...")
    if not loader.connect():
        logger.error("❌ Failed to connect to Snowflake")
        return
    
    logger.info("✅ Connected to Snowflake successfully\n")
    
    try:
        if args.method == 'copy':
            # Use COPY INTO (fastest but requires specific setup)
            s3_path = f"s3://{args.bucket}/{args.prefix}"
            success = load_from_s3_copy_into(
                loader, 
                s3_path,
                args.aws_key_id,
                args.aws_secret_key
            )
        else:
            # Download and bulk insert (more flexible)
            success = load_from_s3_download(
                loader,
                args.bucket,
                args.prefix
            )
        
        if success:
            # Verify data
            logger.info("\n" + "="*70)
            logger.info("🔍 VERIFYING DATA IN SNOWFLAKE")
            logger.info("="*70)
            
            query = f"""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(DISTINCT symbol) as unique_symbols,
                MIN(timestamp) as earliest_timestamp,
                MAX(timestamp) as latest_timestamp
            FROM {loader.database}.{loader.schema}.CRYPTO_MINUTE_DATA
            """
            
            loader.cursor.execute(query)
            row = loader.cursor.fetchone()
            
            if row:
                logger.info(f"Total rows: {row['TOTAL_ROWS']:,}")
                logger.info(f"Unique symbols: {row['UNIQUE_SYMBOLS']}")
                logger.info(f"Date range: {row['EARLIEST_TIMESTAMP']} to {row['LATEST_TIMESTAMP']}")
                logger.info("="*70)
                
    finally:
        loader.disconnect()
        logger.info("\n✅ Disconnected from Snowflake")

if __name__ == "__main__":
    main()
