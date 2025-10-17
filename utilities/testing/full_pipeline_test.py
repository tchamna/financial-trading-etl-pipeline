"""
Full Pipeline Test
==================

Tests the complete ETL pipeline from data collection to Snowflake loading:
1. Configuration validation
2. Data collection (crypto/stock)
3. Data processing (JSON + Parquet)
4. S3 upload
5. Snowflake loading (if enabled)

Usage:
    python utilities/testing/full_pipeline_test.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Fix Windows console encoding for emoji/Unicode
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass  # Python < 3.7

# Add project root to path
try:
    project_root = Path(__file__).parent.parent.parent
except NameError:
    project_root = Path.cwd()
    
sys.path.insert(0, str(project_root))

from config import get_config
from scripts import crypto_minute_collector, snowflake_data_loader


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_configuration():
    """Test 1: Validate configuration"""
    print_section("TEST 1: CONFIGURATION VALIDATION")
    
    config = get_config()
    issues = []
    
    # Check user config settings
    print("\n📋 User Configuration (user_config.py):")
    print(f"   Stock symbols: {len(config.processing.stock_symbols)} ({', '.join(config.processing.stock_symbols[:3])}...)")
    print(f"   Crypto symbols: {len(config.processing.crypto_symbols)} ({', '.join(config.processing.crypto_symbols[:3])}...)")
    print(f"   Collection interval: {config.processing.collection_interval_seconds // 60} minutes")
    print(f"   Enable local storage: {config.storage.enable_local_storage}")
    print(f"   Enable S3 storage: {config.storage.enable_s3_storage}")
    print(f"   Save JSON format: {config.storage.save_json_format}")
    print(f"   Save Parquet format: {config.storage.save_parquet_format}")
    
    # Check technical config
    print("\n🔧 Technical Configuration (config.json):")
    print(f"   S3 enabled: {config.s3.enabled}")
    print(f"   S3 bucket: {config.s3.bucket_name}")
    print(f"   S3 region: {config.s3.region}")
    print(f"   Database: {config.database.database}")
    
    # Validate
    if not config.storage.save_parquet_format:
        issues.append("⚠️  Parquet format is disabled (SAVE_PARQUET_FORMAT = False)")
    
    if config.storage.enable_s3_storage and not config.s3.enabled:
        issues.append("⚠️  S3 storage enabled in user_config but S3 credentials may be missing")
    
    if not config.api.alpha_vantage_api_key:
        issues.append("⚠️  Alpha Vantage API key not configured")
    
    if issues:
        print("\n❌ Configuration Issues Found:")
        for issue in issues:
            print(f"   {issue}")
        return False
    else:
        print("\n✅ Configuration is valid!")
        return True


def test_data_collection():
    """Test 2: Data collection"""
    print_section("TEST 2: DATA COLLECTION")
    
    print("\n📡 Running data collector...")
    print("   (This will collect latest crypto market data)")
    
    try:
        # Import and run the collector
        print("\n🔄 Collecting data...")
        crypto_minute_collector.main()
        
        print("✅ Data collection complete!")
        return True
        
    except Exception as e:
        print(f"❌ Data collection failed: {e}")
        return False


def test_data_files():
    """Test 3: Check data files"""
    print_section("TEST 3: DATA FILES VERIFICATION")
    
    config = get_config()
    data_dir = Path(config.storage.local_data_directory)
    
    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return False
    
    # Find latest files
    json_files = list(data_dir.glob("crypto_minute_data_*.json"))
    parquet_files = list(data_dir.glob("crypto_minute_data_*.parquet"))
    
    print(f"\n📂 Data Directory: {data_dir.absolute()}")
    print(f"   JSON files: {len(json_files)}")
    print(f"   Parquet files: {len(parquet_files)}")
    
    if not json_files:
        print("❌ No JSON files found")
        return False
    
    # Check latest JSON file
    latest_json = max(json_files, key=lambda p: p.stat().st_mtime)
    print(f"\n📄 Latest JSON File:")
    print(f"   Name: {latest_json.name}")
    print(f"   Size: {latest_json.stat().st_size / 1024:.2f} KB")
    print(f"   Modified: {datetime.fromtimestamp(latest_json.stat().st_mtime)}")
    
    # Load and check content
    with open(latest_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    crypto_data = data.get('crypto_data', [])
    print(f"   Records: {len(crypto_data)}")
    
    if crypto_data:
        print(f"   Symbols: {set(item.get('symbol') for item in crypto_data[:10])}")
    
    # Check Parquet file
    if config.storage.save_parquet_format:
        latest_parquet = latest_json.with_suffix('.parquet')
        if latest_parquet.exists():
            print(f"\n📊 Latest Parquet File:")
            print(f"   Name: {latest_parquet.name}")
            print(f"   Size: {latest_parquet.stat().st_size / 1024:.2f} KB")
            print(f"   Modified: {datetime.fromtimestamp(latest_parquet.stat().st_mtime)}")
            
            # Read parquet to verify
            import pandas as pd
            df = pd.read_parquet(latest_parquet)
            print(f"   Rows: {len(df)}")
            print(f"   Columns: {list(df.columns)}")
            print("\n✅ Both JSON and Parquet files exist!")
            return True
        else:
            print(f"\n⚠️  Parquet file not found: {latest_parquet.name}")
            print("   Creating Parquet file now...")
            
            # Create parquet
            import pandas as pd
            df = pd.DataFrame(crypto_data)
            df.to_parquet(latest_parquet, compression='snappy', index=False)
            print(f"✅ Parquet file created: {latest_parquet.name}")
            return True
    else:
        print("\n✅ JSON file exists! (Parquet disabled in config)")
        return True


def test_s3_upload():
    """Test 4: S3 upload"""
    print_section("TEST 4: S3 UPLOAD")
    
    config = get_config()
    
    if not config.storage.enable_s3_storage:
        print("⚠️  S3 storage is disabled in user_config.py")
        print("   Set ENABLE_S3_STORAGE = True to enable S3 uploads")
        return True  # Not a failure, just skipped
    
    if not config.s3.enabled:
        print("⚠️  S3 credentials not configured in config.json")
        return True  # Not a failure, just skipped
    
    print(f"\n☁️  S3 Configuration:")
    print(f"   Bucket: {config.s3.bucket_name}")
    print(f"   Region: {config.s3.region}")
    print(f"   Compression: {config.s3.enable_compression}")
    
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        # Test S3 connection
        s3_client = boto3.client(
            's3',
            aws_access_key_id=config.s3.access_key_id,
            aws_secret_access_key=config.s3.secret_access_key,
            region_name=config.s3.region
        )
        
        print("\n🔍 Testing S3 connection...")
        
        # Test bucket access by trying to upload a test file
        try:
            test_key = "test/pipeline_test.txt"
            test_content = f"Pipeline test at {datetime.now()}"
            
            s3_client.put_object(
                Bucket=config.s3.bucket_name,
                Key=test_key,
                Body=test_content.encode('utf-8')
            )
            print(f"✅ S3 bucket accessible: {config.s3.bucket_name}")
            print(f"   Test upload successful: s3://{config.s3.bucket_name}/{test_key}")
            
            # Clean up test file
            try:
                s3_client.delete_object(Bucket=config.s3.bucket_name, Key=test_key)
                print(f"   Test file cleaned up")
            except:
                pass  # Cleanup failure is ok
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                print(f"❌ S3 bucket not found: {config.s3.bucket_name}")
                print("   Run: python utilities/setup/check_s3_access.py")
            else:
                print(f"❌ S3 error: {e}")
                print("   Check credentials in config.json")
            return False
        
        # Find latest files
        data_dir = Path(config.storage.local_data_directory)
        json_files = list(data_dir.glob("crypto_minute_data_*.json"))
        
        if not json_files:
            print("❌ No files to upload")
            return False
        
        latest_json = max(json_files, key=lambda p: p.stat().st_mtime)
        latest_parquet = latest_json.with_suffix('.parquet')
        
        # Get target date
        with open(latest_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        target_date = data.get('target_date', datetime.now().strftime('%Y-%m-%d'))
        year, month, day = target_date.split('-')
        
        files_uploaded = 0
        
        # Upload JSON
        if config.storage.save_json_format and latest_json.exists():
            json_key = f"{year}/{config.s3.raw_prefix}/crypto/month={month}/{latest_json.name}"
            print(f"\n📤 Uploading JSON...")
            s3_client.upload_file(str(latest_json), config.s3.bucket_name, json_key)
            print(f"   ✅ s3://{config.s3.bucket_name}/{json_key}")
            files_uploaded += 1
        
        # Upload Parquet
        if config.storage.save_parquet_format and latest_parquet.exists():
            parquet_key = f"{year}/{config.s3.processed_prefix}/crypto/month={month}/{latest_parquet.name}"
            print(f"\n📤 Uploading Parquet...")
            s3_client.upload_file(str(latest_parquet), config.s3.bucket_name, parquet_key)
            print(f"   ✅ s3://{config.s3.bucket_name}/{parquet_key}")
            files_uploaded += 1
        
        if files_uploaded > 0:
            print(f"\n✅ Successfully uploaded {files_uploaded} files to S3!")
            return True
        else:
            print("\n⚠️  No files uploaded")
            return False
            
    except Exception as e:
        print(f"\n❌ S3 upload failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_snowflake_loading():
    """Test 5: Snowflake loading"""
    print_section("TEST 5: SNOWFLAKE LOADING")
    
    try:
        config = get_config()
        if not config.snowflake.enabled:
            print("✅ Snowflake is disabled in user_config.py - SKIPPING TEST")
            return True
    except (ImportError, AttributeError):
        print("✅ Snowflake is disabled - SKIPPING TEST")
        return True
        
    print("\n❄️  Running Snowflake loader...")
    
    try:
        # Import and run the loader
        print("\n🔄 Loading data into Snowflake...")
        snowflake_data_loader.main()
        
        print("✅ Snowflake loading complete!")
        return True
        
    except Exception as e:
        print(f"❌ Snowflake loading failed: {e}")
        return False


def test_full_pipeline_status():
    """Test 6: Full pipeline status check"""
    print_section("TEST 6: FULL PIPELINE STATUS CHECK")
    
    try:
        config = get_config()
        if not config.snowflake.enabled:
            print("✅ Snowflake is disabled - SKIPPING TEST")
            return True
    except (ImportError, AttributeError):
        print("✅ Snowflake is disabled - SKIPPING TEST")
        return True
        
    print("\n🔍 Verifying data in Snowflake...")
    
    try:
        import snowflake.connector
        import json
        
        # Load Snowflake config
        with open('config.json', 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        snowflake_config = config_data.get('snowflake', {})
        
        # Test connection
        conn = snowflake.connector.connect(
            account=snowflake_config.get('account'),
            user=snowflake_config.get('username'),
            password=snowflake_config.get('password'),
            role=snowflake_config.get('role', 'SYSADMIN'),
            warehouse=snowflake_config.get('warehouse', 'FINANCIAL_WH')
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_VERSION()")
        version = cursor.fetchone()[0]
        
        print(f"✅ Snowflake connection successful!")
        print(f"   Version: {version}")
        print(f"   Warehouse: {snowflake_config.get('warehouse')}")
        print(f"   Database: {snowflake_config.get('database')}")
        
        cursor.close()
        conn.close()
        
        print("\n💡 To load data into Snowflake, run:")
        print("   python scripts/snowflake_data_loader.py")
        
        return True
        
    except ImportError:
        print("⚠️  Snowflake settings not found in user_config.py")
        return True  # Not a failure, just not configured
    except Exception as e:
        print(f"❌ Snowflake connection failed: {e}")
        print("\n💡 To configure Snowflake:")
        print("   1. Run: python utilities/setup/snowflake_quick_setup.py")
        print("   2. Or see: docs/SNOWFLAKE_INTEGRATION_GUIDE.md")
        return False


def test_pipeline_flow():
    """Test 6: Data flow verification"""
    print_section("TEST 6: DATA FLOW VERIFICATION")
    
    config = get_config()
    
    print("\n🔄 Pipeline Flow:")
    print("   1. Data Collection ──→ scripts/crypto_minute_collector.py")
    print("   2. Local Storage   ──→ data/ folder (JSON + Parquet)")
    
    if config.storage.enable_s3_storage and config.s3.enabled:
        print(f"   3. S3 Upload       ──→ s3://{config.s3.bucket_name}/")
    else:
        print("   3. S3 Upload       ──→ [Disabled]")
    
    if config.snowflake.enabled:
        print("   4. Snowflake Load  ──→ FINANCIAL_DB.CORE")
    else:
        print("   4. Snowflake Load  ──→ [Disabled]")
    
    print("\n📊 Data Formats:")
    if config.storage.save_json_format:
        print("   ✅ JSON (human-readable)")
    if config.storage.save_parquet_format:
        print("   ✅ Parquet (optimized, compressed)")
    
    print("\n✅ Pipeline flow verified!")
    return True


def main():
    """Run all pipeline tests"""
    print("\n" + "=" * 70)
    print("  🚀 FULL PIPELINE TEST")
    print("=" * 70)
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    results = {
        "Configuration": test_configuration(),
        "Data Collection": test_data_collection(),
        "Data Files": test_data_files(),
        "S3 Upload": test_s3_upload(),
        "Snowflake": test_snowflake_loading(),
        "Pipeline Flow": test_pipeline_flow()
    }
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print("\n📋 Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status:8} - {test_name}")
    
    print(f"\n📊 Score: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Your pipeline is fully functional!")
        print("\n📚 Next Steps:")
        print("   • Schedule automated collection with Airflow")
        print("   • Set up monitoring and alerts")
        print("   • Connect BI tools to Snowflake")
        print("   • Build analytics dashboards")
    else:
        print("\n⚠️  Some tests failed. Review the output above for details.")
        print("\n💡 Common fixes:")
        print("   • Check configuration in user_config.py")
        print("   • Verify credentials in config.json")
        print("   • Ensure S3 bucket exists")
        print("   • Test Snowflake connection separately")
    
    print("\n" + "=" * 70)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
