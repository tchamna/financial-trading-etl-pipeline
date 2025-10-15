"""
Test Data Upload - Creates Parquet and uploads to S3
====================================================

Quick script to test Parquet creation and S3 upload functionality
"""

import sys
import os
from pathlib import Path
import json
import pandas as pd
import boto3
from datetime import datetime

# Add project root to path (works in both script and notebook mode)
try:
    # When running as a script
    project_root = Path(__file__).parent.parent.parent
except NameError:
    # When running in notebook/interactive mode
    project_root = Path.cwd()
    
sys.path.insert(0, str(project_root))

from config import get_config

def test_upload():
    """Test creating Parquet and uploading to S3"""
    
    print("=" * 70)
    print("🧪 TEST: PARQUET CREATION & S3 UPLOAD")
    print("=" * 70)
    
    config = get_config()
    
    print(f"\n📋 Configuration:")
    print(f"   Save Parquet: {config.storage.save_parquet_format}")
    print(f"   Enable S3 Storage: {config.storage.enable_s3_storage}")
    print(f"   S3 Enabled (technical): {config.s3.enabled}")
    print(f"   S3 Bucket: {config.s3.bucket_name}")
    
    # Find latest JSON file
    data_dir = Path("data")
    json_files = list(data_dir.glob("crypto_minute_data_*.json"))
    
    if not json_files:
        print("\n❌ No JSON files found in data/")
        return
    
    latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
    print(f"\n📄 Latest file: {latest_file.name}")
    
    # Load JSON data
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list and dict formats
    if isinstance(data, list):
        data = data[0] if len(data) > 0 else {}
    
    crypto_data = data.get('crypto_data', [])
    print(f"📊 Records: {len(crypto_data)}")
    
    if not crypto_data:
        print("❌ No data to process")
        return
    
    # Create Parquet file
    if config.storage.save_parquet_format:
        print(f"\n📊 Creating Parquet file...")
        
        df = pd.DataFrame(crypto_data)
        parquet_file = latest_file.with_suffix('.parquet')
        
        df.to_parquet(parquet_file, compression='snappy', index=False)
        
        file_size = parquet_file.stat().st_size / 1024  # KB
        print(f"✅ Parquet created: {parquet_file.name}")
        print(f"   Size: {file_size:.2f} KB")
        print(f"   Rows: {len(df)}")
        print(f"   Columns: {len(df.columns)}")
    
    # Upload to S3
    if config.storage.enable_s3_storage and config.s3.enabled:
        print(f"\n☁️  Uploading to S3...")
        
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=config.s3.access_key_id,
                aws_secret_access_key=config.s3.secret_access_key,
                region_name=config.s3.region
            )
            
            # Upload JSON to: year/raw/crypto/month=MM/
            if config.storage.save_json_format:
                target_date = data.get('target_date', datetime.now().strftime('%Y-%m-%d'))
                year, month, day = target_date.split('-')
                
                json_key = f"{year}/{config.s3.raw_prefix}/crypto/month={month}/{latest_file.name}"
                
                s3_client.upload_file(
                    str(latest_file),
                    config.s3.bucket_name,
                    json_key
                )
                print(f"✅ JSON uploaded: s3://{config.s3.bucket_name}/{json_key}")
            
            # Upload Parquet to: year/processed/crypto/month=MM/
            if config.storage.save_parquet_format and parquet_file.exists():
                parquet_key = f"{year}/{config.s3.processed_prefix}/crypto/month={month}/{parquet_file.name}"
                
                s3_client.upload_file(
                    str(parquet_file),
                    config.s3.bucket_name,
                    parquet_key
                )
                print(f"✅ Parquet uploaded: s3://{config.s3.bucket_name}/{parquet_key}")
            
            print(f"\n🎉 Upload successful!")
            
        except Exception as e:
            print(f"\n❌ S3 upload failed: {e}")
            print(f"\n💡 Check:")
            print(f"   - AWS credentials in config.json")
            print(f"   - S3 bucket exists: {config.s3.bucket_name}")
            print(f"   - IAM permissions for S3 access")
    else:
        print(f"\n⚠️  S3 upload skipped (disabled in configuration)")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    test_upload()
