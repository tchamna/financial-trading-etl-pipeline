"""
Fast bulk loader for crypto minute data into Snowflake
Uses batch inserts with executemany() for maximum performance
"""

import sys
from pathlib import Path
import json
import time

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

def load_crypto_file_fast(loader, json_file):
    """
    Load crypto minute data using fast batch inserts
    """
    stats = {
        'crypto_rows': 0,
        'files_processed': 0,
        'errors': 0
    }
    
    # Check if we have a valid connection
    if not loader.connection or not loader.cursor:
        logger.error("No valid Snowflake connection available")
        stats['errors'] = 1
        return stats
    
    try:
        start_time = time.time()
        
        # Load JSON data
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract the crypto_data array
        if isinstance(data, list) and len(data) > 0:
            data_container = data[0]
            if isinstance(data_container, dict) and 'crypto_data' in data_container:
                records = data_container['crypto_data']
                logger.info(f"Found {len(records):,} records in {json_file.name}")
                logger.info(f"  Collection time: {data_container.get('collection_time')}")
                logger.info(f"  Target date: {data_container.get('target_date')}")
                logger.info(f"  Data sources: {', '.join(data_container.get('data_sources', []))}")
            else:
                logger.error(f"Invalid data structure - no crypto_data field found")
                stats['errors'] = 1
                return stats
        else:
            logger.error(f"Invalid data structure - expected list with data")
            stats['errors'] = 1
            return stats
        
        # Prepare all rows for batch insert
        batch_data = []
        skipped = 0
        
        for record in records:
            try:
                # Validate record
                if not isinstance(record, dict):
                    skipped += 1
                    continue
                
                # Convert timestamp format
                timestamp_str = record.get('timestamp', '').replace(' UTC', '')
                
                # Validate required fields
                if not record.get('symbol') or not timestamp_str:
                    skipped += 1
                    continue
                
                # Create tuple of values in the correct order
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
                continue
        
        if not batch_data:
            logger.warning("No valid data to insert")
            return stats
        
        logger.info(f"  Prepared {len(batch_data):,} rows for insertion ({skipped} skipped)")
        
        # Use executemany for fast bulk insert
        sql = f"""
        INSERT INTO {loader.database}.{loader.schema}.CRYPTO_MINUTE_DATA
        (symbol, timestamp, open, high, low, close, volume, api_source, interval)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        insert_start = time.time()
        logger.info("  Executing bulk insert...")
        
        # Insert in chunks of 10,000 rows
        chunk_size = 10000
        total_inserted = 0
        
        for i in range(0, len(batch_data), chunk_size):
            chunk = batch_data[i:i+chunk_size]
            loader.cursor.executemany(sql, chunk)
            total_inserted += len(chunk)
            logger.info(f"    Inserted {total_inserted:,}/{len(batch_data):,} rows...")
        
        # Commit all inserts
        loader.connection.commit()
        
        insert_time = time.time() - insert_start
        total_time = time.time() - start_time
        
        stats['crypto_rows'] = len(batch_data)
        stats['files_processed'] = 1
        
        logger.info(f"✅ Successfully loaded {len(batch_data):,} rows from {json_file.name}")
        logger.info(f"   Insert time: {insert_time:.2f}s | Total time: {total_time:.2f}s")
        logger.info(f"   Speed: {len(batch_data)/total_time:.0f} rows/second")
        
    except Exception as e:
        logger.error(f"Error loading file {json_file}: {e}")
        import traceback
        traceback.print_exc()
        stats['errors'] += 1
    
    return stats

def main():
    # Initialize Snowflake loader
    logger.info("Initializing Snowflake loader...")
    loader = SnowflakeLoader()
    
    # Connect to Snowflake
    logger.info("Connecting to Snowflake...")
    if not loader.connect():
        logger.error("❌ Failed to connect to Snowflake")
        return
    
    logger.info("✅ Connected to Snowflake successfully")
    
    try:
        # Get all crypto minute data JSON files
        data_dir = Path(__file__).parent / 'data'
        json_files = sorted(data_dir.glob('crypto_minute_data_*.json'))
        
        if not json_files:
            logger.warning("No crypto minute data JSON files found")
            return
        
        logger.info(f"\nFound {len(json_files)} crypto minute data files to load")
        logger.info("="*70)
        
        # Load each file
        total_stats = {
            'crypto_rows': 0,
            'files_processed': 0,
            'errors': 0
        }
        
        overall_start = time.time()
        
        for json_file in json_files:
            logger.info(f"\n📁 Processing: {json_file.name}")
            logger.info("-"*70)
            
            stats = load_crypto_file_fast(loader, json_file)
            
            total_stats['crypto_rows'] += stats.get('crypto_rows', 0)
            total_stats['files_processed'] += stats.get('files_processed', 0)
            total_stats['errors'] += stats.get('errors', 0)
        
        overall_time = time.time() - overall_start
        
        # Print summary
        logger.info("\n" + "="*70)
        logger.info("📊 LOAD SUMMARY")
        logger.info("="*70)
        logger.info(f"✅ Files processed: {total_stats['files_processed']}/{len(json_files)}")
        logger.info(f"✅ Total crypto rows loaded: {total_stats['crypto_rows']:,}")
        logger.info(f"⚠️  Errors encountered: {total_stats['errors']}")
        logger.info(f"⏱️  Total time: {overall_time:.2f} seconds")
        logger.info(f"🚀 Overall speed: {total_stats['crypto_rows']/overall_time:.0f} rows/second")
        logger.info("="*70)
        
        # Verify in Snowflake
        try:
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
                logger.info("\n" + "="*70)
                logger.info("🔍 SNOWFLAKE DATA VERIFICATION")
                logger.info("="*70)
                logger.info(f"Total rows in CRYPTO_MINUTE_DATA: {row['TOTAL_ROWS']:,}")
                logger.info(f"Unique symbols: {row['UNIQUE_SYMBOLS']}")
                logger.info(f"Date range: {row['EARLIEST_TIMESTAMP']} to {row['LATEST_TIMESTAMP']}")
                logger.info("="*70)
                
                # Show sample by symbol
                logger.info("\n" + "="*70)
                logger.info("📋 RECORDS BY SYMBOL")
                logger.info("="*70)
                
                symbol_query = f"""
                SELECT 
                    symbol,
                    COUNT(*) as row_count,
                    MIN(timestamp) as earliest,
                    MAX(timestamp) as latest
                FROM {loader.database}.{loader.schema}.CRYPTO_MINUTE_DATA
                GROUP BY symbol
                ORDER BY symbol
                """
                
                loader.cursor.execute(symbol_query)
                for row in loader.cursor.fetchall():
                    logger.info(f"{row['SYMBOL']:20} | {row['ROW_COUNT']:6,} rows | {row['EARLIEST']} to {row['LATEST']}")
                
                logger.info("="*70)
        except Exception as e:
            logger.error(f"Error verifying data in Snowflake: {e}")
    
    finally:
        loader.disconnect()
        logger.info("\n✅ Disconnected from Snowflake")

if __name__ == "__main__":
    main()
