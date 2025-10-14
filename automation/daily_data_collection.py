#!/usr/bin/env python3
"""
Daily Automated Data Collection Pipeline
Author: Tyler Chamberlain
Email: tyler.chamberlain@example.com

This script automates the daily collection of minute-level cryptocurrency data,
uploads it to S3, and performs technical analysis.
"""

import sys
import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from config import PipelineConfig
from scripts.crypto_minute_collector import collect_multi_source_crypto_minutes
from scripts.upload_minute_data import upload_minute_data_to_s3
from utilities.analysis.simple_minute_analyzer import SimpleMinuteAnalyzer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation/daily_collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DailyDataPipeline:
    """Automated daily data collection and processing pipeline."""
    
    def __init__(self):
        """Initialize the pipeline with configuration."""
        self.config = PipelineConfig()
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
    def collect_yesterday_data(self):
        """Collect minute-level data for yesterday."""
        yesterday = datetime.now() - timedelta(days=1)
        date_str = yesterday.strftime('%Y%m%d')
        
        # Get symbols from configuration
        symbols = self.config.processing.crypto_symbols
        logger.info(f"Starting data collection for {yesterday.strftime('%Y-%m-%d')}")
        logger.info(f"Collecting data for symbols: {', '.join(symbols)}")
        
        # Use the existing multi-source collector function
        # Note: Currently collects data for predefined symbols
        # TODO: Update crypto_minute_collector.py to accept configurable symbols
        all_data = collect_multi_source_crypto_minutes()
        
        # Save to file
        filename = f"crypto_minute_data_{date_str}.json"
        filepath = self.data_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(all_data, f, indent=2, default=str)
            
        if 'crypto_data' in all_data:
            record_count = len(all_data['crypto_data'])
        else:
            record_count = len(all_data) if isinstance(all_data, list) else 0
            
        logger.info(f"Collected {record_count} minute records")
        logger.info(f"Data saved to {filepath}")
        
        return filepath
        
    def upload_to_s3(self, filepath):
        """Handle data storage based on configuration (local/S3)."""
        logger.info("Starting data storage management...")
        
        try:
            # Use the enhanced storage function
            results = upload_minute_data_to_s3()
            
            if results:
                logger.info("Data storage completed successfully")
                
                # Log what was stored
                storage_config = self.config.storage
                if storage_config.enable_local_storage:
                    logger.info(f"Local storage: Enabled (keeping {storage_config.keep_local_days} days)")
                if storage_config.enable_s3_storage and self.config.s3.enabled:
                    logger.info("S3 storage: Completed")
                    if 'json' in results:
                        logger.info("  - JSON format uploaded")
                    if 'parquet' in results:
                        logger.info("  - Parquet format uploaded")
                        
                return True
            else:
                logger.error("Data storage failed")
                return False
                
        except Exception as e:
            logger.error(f"Storage error: {str(e)}")
            return False
        
    def analyze_data(self, filepath):
        """Perform technical analysis on collected data."""
        logger.info("Starting technical analysis...")
        
        try:
            analyzer = SimpleMinuteAnalyzer(str(filepath))
            
            # Generate analysis report
            analysis_results = analyzer.comprehensive_analysis()
            
            # Save analysis report
            yesterday = datetime.now() - timedelta(days=1)
            date_str = yesterday.strftime('%Y%m%d')
            analysis_filename = f"minute_analysis_{date_str}_{datetime.now().strftime('%H%M%S')}.json"
            analysis_filepath = self.data_dir / analysis_filename
            
            with open(analysis_filepath, 'w') as f:
                json.dump(analysis_results, f, indent=2, default=str)
                
            logger.info(f"Analysis completed and saved to {analysis_filepath}")
            
            # Log key insights
            if 'performance_summary' in analysis_results:
                performance = analysis_results['performance_summary']
                logger.info(f"Best performer: {performance.get('best_performer', 'N/A')}")
                logger.info(f"Worst performer: {performance.get('worst_performer', 'N/A')}")
                
            return analysis_filepath
            
        except Exception as e:
            logger.warning(f"Technical analysis failed: {str(e)}")
            logger.info("Skipping analysis step - data collection and S3 upload were successful")
            return None
        
    def cleanup_old_data(self, days_to_keep=7):
        """Clean up data files older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        for file in self.data_dir.glob("*.json"):
            if file.stat().st_mtime < cutoff_date.timestamp():
                logger.info(f"Removing old file: {file}")
                file.unlink()
                
    def run_daily_pipeline(self):
        """Run the complete daily data pipeline."""
        try:
            logger.info("=== Starting Daily Data Collection Pipeline ===")
            start_time = datetime.now()
            
            # Step 1: Collect data
            data_file = self.collect_yesterday_data()
            
            # Step 2: Store data (local/S3 based on config)
            upload_success = self.upload_to_s3(data_file)
            
            # Step 3: Analyze data
            analysis_file = self.analyze_data(data_file)
            
            # Step 4: Cleanup old files
            self.cleanup_old_data()
            
            duration = datetime.now() - start_time
            logger.info(f"=== Pipeline completed successfully in {duration} ===")
            
            return {
                'status': 'success',
                'duration': str(duration),
                'data_file': str(data_file),
                'analysis_file': str(analysis_file) if analysis_file else "Analysis skipped due to error",
                'upload_success': upload_success
            }
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

def main():
    """Main entry point for daily pipeline."""
    pipeline = DailyDataPipeline()
    result = pipeline.run_daily_pipeline()
    
    if result['status'] == 'error':
        sys.exit(1)
    else:
        logger.info("Daily pipeline completed successfully")

if __name__ == "__main__":
    main()