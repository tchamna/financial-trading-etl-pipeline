"""
Minute Data S3 Uploader
======================

Author: Shck Tchamna (tchamna@gmail.com)

Upload minute-level crypto data to S3 with proper partitioning in both JSON and Parquet formats.
"""

import boto3
import json
import gzip
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime
from pathlib import Path
import sys
import os
from io import BytesIO

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config


def check_s3_file_exists(s3_client, bucket_name, key):
    """Check if a file already exists in S3"""
    try:
        s3_client.head_object(Bucket=bucket_name, Key=key)
        return True
    except:
        return False


def upload_minute_data_to_s3(filename=None):
    """
    Upload minute data based on storage configuration (local/S3, JSON/Parquet)
    
    Args:
        filename: Specific filename to upload, or None to auto-detect latest file
    """
    
    config = get_config()
    
    print("💾 DATA STORAGE MANAGER")
    print("=" * 40)
    
    # Check storage configuration
    storage_config = config.storage
    s3_config = config.s3
    
    print(f"📍 Local Storage: {'✅ Enabled' if storage_config.enable_local_storage else '❌ Disabled'}")
    print(f"☁️ S3 Storage: {'✅ Enabled' if storage_config.enable_s3_storage and s3_config.enabled else '❌ Disabled'}")
    print(f"📄 JSON Format: {'✅' if storage_config.save_json_format else '❌'}")
    print(f"📊 Parquet Format: {'✅' if storage_config.save_parquet_format else '❌'}")
    
    # Auto-detect latest file if not specified
    if filename is None:
        # Look for the latest financial minute data file (new format) or crypto minute data file (legacy)
        data_dir = Path("data") if Path("data").exists() else Path(".")
        
        # Try new format first
        json_files = list(data_dir.glob("financial_minute_data_*.json"))
        
        # Fallback to legacy format if new format not found
        if not json_files:
            json_files = list(data_dir.glob("crypto_minute_data_*.json"))
        
        if not json_files:
            print(f"\n❌ No financial/crypto minute data files found in {data_dir}")
            return None
        
        # Get the most recent file
        filename = max(json_files, key=lambda p: p.stat().st_mtime)
        print(f"\n📁 Auto-detected latest file: {filename.name}")
    else:
        filename = Path(filename)
    
    try:
        with open(str(filename), 'r') as f:
            data = json.load(f)
        
        # Handle both list and dict formats
        if isinstance(data, list):
            # If it's a list, take the first element which should be the data dict
            if len(data) > 0:
                data = data[0]
            else:
                print(f"\n❌ Empty data list in {filename}")
                return None
        
        print(f"\n📄 Loaded: {filename}")
        
        # Check if crypto_data exists (support both old format with just crypto_data and new format with crypto_data + stock_data)
        if 'crypto_data' not in data and 'stock_data' not in data:
            print(f"\n[ERROR] No 'crypto_data' or 'stock_data' key found in {filename}")
            return None
            
        # Count records
        crypto_count = len(data.get('crypto_data', []))
        stock_count = len(data.get('stock_data', []))
        total_count = crypto_count + stock_count
        print(f"📊 Records: {total_count} (crypto: {crypto_count}, stock: {stock_count})")
        
        upload_results = {}
        
        # S3 Upload (if enabled)
        if storage_config.enable_s3_storage and s3_config.enabled:
            print(f"\n☁️ UPLOADING TO S3...")
            
            # Connect to S3
            s3_client = boto3.client(
                's3',
                aws_access_key_id=s3_config.access_key_id,
                aws_secret_access_key=s3_config.secret_access_key,
                region_name=s3_config.region
            )
            
            # Prepare data for upload
            # Support both 'target_date' and 'collection_date' keys
            target_date = data.get('target_date') or data.get('collection_date') or datetime.now().strftime('%Y-%m-%d')
            year, month, day = target_date.split('-')
            
            # Check if files already exist to avoid redundant uploads
            json_key = f"{year}/processed/financial-minute/json/month={month}/financial_minute_data_{target_date.replace('-', '')}.json.gz"
            parquet_key = f"{year}/processed/financial-minute/parquet/month={month}/financial_minute_data_{target_date.replace('-', '')}.parquet"
            
            json_exists = check_s3_file_exists(s3_client, s3_config.bucket_name, json_key)
            parquet_exists = check_s3_file_exists(s3_client, s3_config.bucket_name, parquet_key)
            
            if json_exists and parquet_exists:
                print(f"\n⏭️  Files already exist in S3 - skipping redundant upload")
                print(f"   📄 JSON: {json_key}")
                print(f"   📊 Parquet: {parquet_key}")
                print(f"   💡 Tip: Data for {target_date} has already been collected")
                upload_results['json'] = json_key
                upload_results['parquet'] = parquet_key
                upload_results['skipped'] = True
            else:
                # Upload JSON format (if enabled and doesn't exist)
                if storage_config.save_json_format and not json_exists:
                    print(f"\n📄 Uploading JSON format...")
                    json_key = upload_json_format(s3_client, data, s3_config.bucket_name, year, month, day, target_date)
                    upload_results['json'] = json_key
                elif json_exists:
                    print(f"\n⏭️  JSON already exists - skipping")
                    upload_results['json'] = json_key
                
                # Upload Parquet format (if enabled and doesn't exist)
                if storage_config.save_parquet_format and not parquet_exists:
                    print(f"\n📊 Uploading Parquet format...")
                    # Combine crypto and stock data for parquet upload
                    combined_data = data.get('crypto_data', []) + data.get('stock_data', [])
                    parquet_key = upload_parquet_format(s3_client, combined_data, s3_config.bucket_name, year, month, day, target_date)
                    upload_results['parquet'] = parquet_key
                elif parquet_exists:
                    print(f"\n⏭️  Parquet already exists - skipping")
                    upload_results['parquet'] = parquet_key
            
                print(f"\n✅ S3 uploads completed!")
            
            print(f"🗂️ Bucket: {s3_config.bucket_name}")
        else:
            print(f"\n⚠️ S3 upload skipped (disabled in configuration)")
        
        # Local Storage Management
        if storage_config.enable_local_storage:
            print(f"\n📁 LOCAL STORAGE MANAGEMENT...")
            manage_local_storage(storage_config, data, str(filename))
        else:
            print(f"\n⚠️ Local storage disabled - removing local file...")
            if os.path.exists(str(filename)):
                os.remove(str(filename))
                print(f"   🗑️ Removed: {filename}")
        
        return upload_results
        
    except Exception as e:
        print(f"❌ Storage operation failed: {e}")
        return None


def manage_local_storage(storage_config, data, filename):
    """Manage local storage based on configuration"""
    
    # Ensure local directory exists
    local_dir = Path(storage_config.local_data_directory)
    local_dir.mkdir(exist_ok=True)
    
    # Move file to local directory if not already there
    if not filename.startswith(str(local_dir)):
        local_filename = local_dir / Path(filename).name
        if Path(filename).exists():
            # Remove existing file if it exists
            if local_filename.exists():
                local_filename.unlink()
            Path(filename).rename(local_filename)
            print(f"   📁 Moved to: {local_filename}")
        filename = str(local_filename)
    
    # Save Parquet format locally if enabled
    if storage_config.save_parquet_format:
        parquet_filename = local_dir / Path(filename).stem
        parquet_filename = parquet_filename.with_suffix('.parquet')
        
        # Convert to DataFrame and save as Parquet (combine crypto and stock data)
        combined_data = data.get('crypto_data', []) + data.get('stock_data', [])
        df = pd.DataFrame(combined_data)
        
        # Parse timestamps with mixed formats (crypto has " UTC" suffix, stocks don't)
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed', utc=True)
        
        # Standardize column names (crypto uses 'api_source', stocks use 'source')
        if 'source' in df.columns and 'api_source' not in df.columns:
            df['api_source'] = df['source']
            df = df.drop('source', axis=1)
        
        # Optimize data types
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Add date and time columns for better querying and partitioning
        df['date'] = df['timestamp'].dt.date  # Date only (YYYY-MM-DD)
        df['time'] = df['timestamp'].dt.time  # Time only (HH:MM:SS)
        df['hour'] = df['timestamp'].dt.hour  # Hour for additional partitioning
        df['minute'] = df['timestamp'].dt.minute  # Minute for granular analysis
        df['ingestion_timestamp'] = pd.Timestamp.now(tz='UTC')  # When data was processed
        
        df.to_parquet(parquet_filename, compression='snappy')
        print(f"   📊 Saved Parquet: {parquet_filename} ({len(combined_data)} records)")
    
    # Clean up old files
    cleanup_old_files(local_dir, storage_config.keep_local_days)


def cleanup_old_files(directory, keep_days):
    """Remove files older than specified days"""
    cutoff_date = datetime.now() - pd.Timedelta(days=keep_days)
    
    removed_count = 0
    for file_path in Path(directory).glob("*"):
        if file_path.is_file():
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            if file_time < cutoff_date:
                file_path.unlink()
                removed_count += 1
    
    if removed_count > 0:
        print(f"   🗑️ Cleaned up {removed_count} old files (older than {keep_days} days)")


def upload_json_format(s3_client, data, bucket_name, year, month, day, target_date):
    """Upload data in compressed JSON format"""
    
    # Create compressed JSON
    json_content = json.dumps(data, indent=2, default=str)
    compressed_content = gzip.compress(json_content.encode('utf-8'))
    
    # S3 key with partitioning - use financial_minute_data for combined crypto+stock data
    s3_key = f"{year}/processed/financial-minute/json/month={month}/financial_minute_data_{target_date.replace('-', '')}.json.gz"
    
    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=compressed_content,
        ContentType='application/json',
        ContentEncoding='gzip',
        Metadata={
            'data-type': 'financial-minute',
            'format': 'json',
            'resolution': 'minute',
            'crypto-records': str(len(data.get('crypto_data', []))),
            'stock-records': str(len(data.get('stock_data', []))),
            'total-records': str(data.get('summary', {}).get('total_records', 0)),
            'date': target_date
        }
    )
    
    # Calculate compression stats
    original_size = len(json_content.encode('utf-8'))
    compressed_size = len(compressed_content)
    compression_ratio = (1 - compressed_size / original_size) * 100
    
    print(f"   ✅ JSON uploaded: {compressed_size:,} bytes ({compression_ratio:.1f}% compressed)")
    print(f"   📁 Key: {s3_key}")
    
    return s3_key


def upload_parquet_format(s3_client, crypto_data, bucket_name, year, month, day, target_date):
    """Upload data in Parquet format for analytics"""
    
    # Convert to DataFrame
    df = pd.DataFrame(crypto_data)
    
    # Optimize data types for Parquet
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Handle OHLCV data structure
    numeric_columns = ['open', 'high', 'low', 'close', 'volume']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Add date and time columns for better querying and partitioning
    df['date'] = df['timestamp'].dt.date  # Date only (YYYY-MM-DD)
    df['time'] = df['timestamp'].dt.time  # Time only (HH:MM:SS)
    df['hour'] = df['timestamp'].dt.hour  # Hour for additional partitioning
    df['minute'] = df['timestamp'].dt.minute  # Minute for granular analysis
    df['ingestion_timestamp'] = pd.Timestamp.now(tz='UTC')  # When data was processed
    
    # Add partitioning columns
    df['year'] = df['timestamp'].dt.year
    df['month'] = df['timestamp'].dt.month
    df['day'] = df['timestamp'].dt.day
    df['symbol'] = df['symbol'].astype('category')  # Optimize string storage
    
    # Create Parquet file in memory
    parquet_buffer = BytesIO()
    
    # Convert to PyArrow table for better compression
    table = pa.Table.from_pandas(df)
    
    # Write with optimal settings for analytics
    pq.write_table(
        table, 
        parquet_buffer,
        compression='snappy',  # Fast compression/decompression
        use_dictionary=True,   # Optimize repeated values
        write_statistics=True  # Enable pushdown predicates
    )
    
    parquet_content = parquet_buffer.getvalue()
    
    # S3 key with partitioning - use financial_minute_data for combined crypto+stock data
    s3_key = f"{year}/processed/financial-minute/parquet/month={month}/financial_minute_data_{target_date.replace('-', '')}.parquet"
    
    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=parquet_content,
        ContentType='application/octet-stream',
        Metadata={
            'data-type': 'financial-minute',
            'format': 'parquet',
            'resolution': 'minute',
            'records': str(len(crypto_data)),
            'date': target_date,
            'compression': 'snappy'
        }
    )
    
    parquet_size = len(parquet_content)
    print(f"   ✅ Parquet uploaded: {parquet_size:,} bytes (analytics-optimized)")
    print(f"   📁 Key: {s3_key}")
    print(f"   🚀 Features: Snappy compression, dictionary encoding, statistics")
    
    return s3_key

if __name__ == "__main__":
    upload_minute_data_to_s3()