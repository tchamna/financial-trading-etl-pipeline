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
    print("🚀 Starting Manual Data Collection Pipeline...")
    print("=" * 50)
    
    pipeline = DailyDataPipeline()
    result = pipeline.run_daily_pipeline()
    
    print("\n" + "=" * 50)
    if result['status'] == 'success':
        print("✅ Pipeline completed successfully!")
        print(f"📁 Data file: {result['data_file']}")
        print(f"📊 Analysis file: {result['analysis_file']}")
        print(f"💾 Data Storage: {'✅ Success' if result['upload_success'] else '❌ Failed'}")
        print(f"⏱️ Duration: {result['duration']}")
    else:
        print(f"❌ Pipeline failed: {result['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main()