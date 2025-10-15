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
        # Look for the latest crypto minute data file
        data_dir = Path("data") if Path("data").exists() else Path(".")
        json_files = list(data_dir.glob("crypto_minute_data_*.json"))
        
        if not json_files:
            print(f"\n❌ No crypto minute data files found in {data_dir}")
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
        
        # Check if crypto_data exists
        if 'crypto_data' not in data:
            print(f"\n❌ No 'crypto_data' key found in {filename}")
            return None
            
        print(f"📊 Records: {len(data['crypto_data'])}")
        
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
            target_date = data.get('target_date', datetime.now().strftime('%Y-%m-%d'))
            year, month, day = target_date.split('-')
            
            # Upload JSON format (if enabled)
            if storage_config.save_json_format:
                print(f"\n📄 Uploading JSON format...")
                json_key = upload_json_format(s3_client, data, s3_config.bucket_name, year, month, day, target_date)
                upload_results['json'] = json_key
            
            # Upload Parquet format (if enabled)
            if storage_config.save_parquet_format:
                print(f"\n📊 Uploading Parquet format...")
                parquet_key = upload_parquet_format(s3_client, data['crypto_data'], s3_config.bucket_name, year, month, day, target_date)
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
        
        # Convert to DataFrame and save as Parquet
        df = pd.DataFrame(data['crypto_data'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Optimize data types
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df.to_parquet(parquet_filename, compression='snappy')
        print(f"   📊 Saved Parquet: {parquet_filename}")
    
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
    
    # S3 key with partitioning
    s3_key = f"{year}/processed/crypto-minute/json/month={month}/crypto_minute_data_{target_date.replace('-', '')}.json.gz"
    
    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=compressed_content,
        ContentType='application/json',
        ContentEncoding='gzip',
        Metadata={
            'data-type': 'crypto-minute',
            'format': 'json',
            'resolution': 'minute',
            'records': str(len(data['crypto_data'])),
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
    
    # S3 key with partitioning
    s3_key = f"{year}/processed/crypto-minute/parquet/month={month}/crypto_minute_data_{target_date.replace('-', '')}.parquet"
    
    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=parquet_content,
        ContentType='application/octet-stream',
        Metadata={
            'data-type': 'crypto-minute',
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