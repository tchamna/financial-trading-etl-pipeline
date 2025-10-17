#!/usr/bin/env python3
"""
Manual Pipeline Runner
Author: Tyler Chamberlain
Email: tyler.chamberlain@example.com

Simple script to manually run the data collection pipeline for testing.
"""

import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from automation.daily_data_collection import DailyDataPipeline

def main():
    """Run the pipeline manually."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Manual data collection pipeline for stocks and crypto.',
        epilog='Example: python automation/run_manual.py 2025-10-15'
    )
    parser.add_argument(
        'date',
        nargs='?',
        default=None,
        help='Target date in YYYY-MM-DD format (default: yesterday).'
    )
    args = parser.parse_args()

    print("🚀 Starting Manual Data Collection Pipeline...")
    if args.date:
        print(f"🎯 Target Date: {args.date}")
    else:
        print("🎯 Target Date: Yesterday (default)")
    print("=" * 50)
    
    pipeline = DailyDataPipeline()
    result = pipeline.run_daily_pipeline(target_date=args.date)
    
    print("\n" + "=" * 50)
    if result['status'] == 'success':
        print("✅ Pipeline completed successfully!")
        print(f"📁 Data file: {result['data_file']}")
        print(f"📊 Analysis file: {result['analysis_file']}")
        print(f"💾 S3 Upload: {'✅ Success' if result['upload_success'] else '❌ Failed'}")
        print(f"❄️ Snowflake Load: {'✅ Success' if result.get('snowflake_success') else '❌ Failed or Skipped'}")
        print(f"⏱️ Duration: {result['duration']}")
    else:
        print(f"❌ Pipeline failed: {result['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main()