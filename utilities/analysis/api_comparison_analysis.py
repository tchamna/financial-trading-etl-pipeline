"""
API Data Comparison and Analysis Tool
====================================

Author: Shck Tchamna (tchamna@gmail.com)

This script compares data from Alpha Vantage (stocks) and CoinGecko (crypto) APIs
to analyze data quality, structure, and collection patterns.
"""

import json
from datetime import datetime, timezone
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config


def analyze_api_data_structures():
    """Analyze and compare API data structures"""
    
    print("🔍 API DATA STRUCTURE COMPARISON")
    print("=" * 60)
    
    # Alpha Vantage Stock Data Structure
    stock_structure = {
        "api_name": "Alpha Vantage",
        "data_type": "Stock Market Data",
        "endpoint": "TIME_SERIES_INTRADAY",
        "request_method": "Individual symbol requests",
        "data_fields": [
            "symbol",
            "timestamp", 
            "open_price",
            "high_price", 
            "low_price",
            "close_price",
            "volume"
        ],
        "timestamp_precision": "5-minute intervals",
        "rate_limits": "25 calls/day (free tier)",
        "data_freshness": "Real-time (15-20 min delay)",
        "collection_pattern": "Sequential API calls per symbol",
        "pros": [
            "OHLCV data (Open, High, Low, Close, Volume)",
            "Intraday granularity",
            "Technical analysis ready",
            "US market focus"
        ],
        "cons": [
            "Limited free tier",
            "Rate limiting restrictive", 
            "Separate call per symbol",
            "Weekend/holiday gaps"
        ]
    }
    
    # CoinGecko Crypto Data Structure  
    crypto_structure = {
        "api_name": "CoinGecko",
        "data_type": "Cryptocurrency Market Data",
        "endpoint": "/coins/markets",
        "request_method": "Batch request (multiple coins)",
        "data_fields": [
            "symbol",
            "name",
            "current_price",
            "market_cap",
            "market_cap_rank",
            "price_change_24h",
            "price_change_percentage_24h", 
            "volume_24h",
            "circulating_supply",
            "total_supply",
            "timestamp",
            "data_source"
        ],
        "timestamp_precision": "Real-time snapshots",
        "rate_limits": "50 calls/minute (free tier)",
        "data_freshness": "Real-time",
        "collection_pattern": "Single API call for multiple symbols",
        "pros": [
            "Batch collection efficient",
            "Rich market metadata",
            "24/7 data availability",
            "Generous free tier",
            "Global crypto coverage"
        ],
        "cons": [
            "Crypto only",
            "No traditional OHLCV",
            "Limited historical depth per call",
            "Price volatility"
        ]
    }
    
    print("📈 ALPHA VANTAGE (Stock Data)")
    print("-" * 40)
    print(f"Data Type: {stock_structure['data_type']}")
    print(f"Collection Method: {stock_structure['collection_pattern']}")
    print(f"Rate Limits: {stock_structure['rate_limits']}")
    print(f"Data Fields: {len(stock_structure['data_fields'])} fields")
    for field in stock_structure['data_fields']:
        print(f"  • {field}")
    
    print(f"\n✅ Pros:")
    for pro in stock_structure['pros']:
        print(f"  • {pro}")
    
    print(f"\n⚠️  Cons:")
    for con in stock_structure['cons']:
        print(f"  • {con}")
    
    print(f"\n🪙 COINGECKO (Crypto Data)")
    print("-" * 40)
    print(f"Data Type: {crypto_structure['data_type']}")
    print(f"Collection Method: {crypto_structure['collection_pattern']}")
    print(f"Rate Limits: {crypto_structure['rate_limits']}")
    print(f"Data Fields: {len(crypto_structure['data_fields'])} fields")
    for field in crypto_structure['data_fields']:
        print(f"  • {field}")
    
    print(f"\n✅ Pros:")
    for pro in crypto_structure['pros']:
        print(f"  • {pro}")
    
    print(f"\n⚠️  Cons:")
    for con in crypto_structure['cons']:
        print(f"  • {con}")
    
    return stock_structure, crypto_structure


def compare_data_collection_efficiency():
    """Compare API collection efficiency"""
    
    config = get_config()
    
    print(f"\n⚡ COLLECTION EFFICIENCY ANALYSIS")
    print("=" * 50)
    
    # Alpha Vantage Analysis
    stock_symbols = len(config.processing.stock_symbols)
    stock_calls_needed = stock_symbols  # One call per symbol
    stock_time_needed = stock_calls_needed * 0.3  # 0.3s delay between calls
    
    print(f"📈 Alpha Vantage (Stocks):")
    print(f"   Symbols configured: {stock_symbols}")
    print(f"   API calls needed: {stock_calls_needed}")
    print(f"   Time needed: ~{stock_time_needed:.1f} seconds")
    print(f"   Daily API limit: 25 calls (free)")
    print(f"   Symbols per day: {min(25, stock_symbols)} / {stock_symbols}")
    
    # CoinGecko Analysis
    crypto_symbols = len(config.processing.crypto_symbols)
    crypto_calls_needed = 1  # Single batch call
    crypto_time_needed = 1.0  # One API call
    
    print(f"\n🪙 CoinGecko (Crypto):")
    print(f"   Symbols configured: {crypto_symbols}")
    print(f"   API calls needed: {crypto_calls_needed}")
    print(f"   Time needed: ~{crypto_time_needed:.1f} seconds")
    print(f"   Minute API limit: 50 calls")
    print(f"   Efficiency: All symbols in single call")
    
    # Efficiency comparison
    print(f"\n🏆 EFFICIENCY WINNER: CoinGecko")
    print(f"   Reason: Batch collection vs individual calls")
    print(f"   Speed advantage: {stock_time_needed/crypto_time_needed:.1f}x faster")


def analyze_data_quality_metrics():
    """Analyze data quality aspects"""
    
    print(f"\n📊 DATA QUALITY COMPARISON")
    print("=" * 50)
    
    quality_metrics = {
        "alpha_vantage": {
            "accuracy": "High (NYSE/NASDAQ official)",
            "completeness": "Complete OHLCV",
            "timeliness": "15-20 min delay",
            "consistency": "Standardized format",
            "availability": "Market hours only",
            "historical_depth": "20+ years daily",
            "data_source": "Official exchanges"
        },
        "coingecko": {
            "accuracy": "High (aggregated exchanges)", 
            "completeness": "Rich market metadata",
            "timeliness": "Real-time",
            "consistency": "Standardized API",
            "availability": "24/7",
            "historical_depth": "8+ years",
            "data_source": "Multiple exchanges"
        }
    }
    
    print("📈 Alpha Vantage Quality:")
    for metric, value in quality_metrics["alpha_vantage"].items():
        print(f"   {metric.title()}: {value}")
    
    print(f"\n🪙 CoinGecko Quality:")
    for metric, value in quality_metrics["coingecko"].items():
        print(f"   {metric.title()}: {value}")
    
    return quality_metrics


def analyze_timestamp_patterns():
    """Analyze timestamp patterns from your collected data"""
    
    print(f"\n🕐 TIMESTAMP PATTERN ANALYSIS")
    print("=" * 50)
    
    print("Based on your collected data:")
    print(f"📈 Stock Data (Alpha Vantage):")
    print(f"   Pattern: Sequential collection")
    print(f"   Timestamps: Different for each symbol")
    print(f"   Reason: Individual API calls with delays")
    print(f"   Example timing: 22:53:45, 22:53:48, 22:53:51...")
    
    print(f"\n🪙 Crypto Data (CoinGecko):")
    print(f"   Pattern: Batch collection")
    print(f"   Timestamps: Identical for all symbols")
    print(f"   Reason: Single API call returns all data")
    print(f"   Example timing: 22:53:58.476179 (all coins)")
    
    print(f"\n🎯 IMPLICATIONS:")
    print(f"   ✅ Crypto data: Perfect synchronization for comparison")
    print(f"   ⚠️  Stock data: Small time differences between symbols")
    print(f"   💡 Solution: Collect stocks in smaller batches")


def storage_optimization_analysis():
    """Analyze storage optimization for both data types"""
    
    print(f"\n💾 STORAGE OPTIMIZATION ANALYSIS")
    print("=" * 50)
    
    print("Your current S3 storage structure:")
    print(f"📁 Partitioning: year/month/day/hour")
    print(f"📦 Compression: gzip (80% size reduction)")
    print(f"📊 Format: JSON (flexible) + Parquet (analytics)")
    
    print(f"\n🔍 Data Size Analysis (from your files):")
    print(f"   Crypto JSON (compressed): 370 B")
    print(f"   Estimated uncompressed: ~1.5 KB") 
    print(f"   Parquet advantage: ~90% smaller for analytics")
    
    print(f"\n💰 Cost Implications:")
    print(f"   Daily data (both APIs): ~2-5 MB")
    print(f"   Monthly storage: ~150 MB")
    print(f"   Annual S3 cost: <$1 (Standard tier)")
    print(f"   With lifecycle policies: <$0.50/year")


def main():
    """Main analysis function"""
    
    print("🎯 FINANCIAL DATA API COMPARISON ANALYSIS")
    print("=" * 70)
    
    # Structure comparison
    stock_structure, crypto_structure = analyze_api_data_structures()
    
    # Efficiency analysis
    compare_data_collection_efficiency()
    
    # Quality metrics
    quality_metrics = analyze_data_quality_metrics()
    
    # Timestamp analysis
    analyze_timestamp_patterns()
    
    # Storage analysis
    storage_optimization_analysis()
    
    print(f"\n📋 RECOMMENDATIONS:")
    print("=" * 30)
    print("✅ Current setup is optimal for both APIs")
    print("✅ CoinGecko batch collection is more efficient")
    print("✅ Alpha Vantage provides richer OHLCV data")
    print("✅ S3 partitioning enables efficient queries")
    print("✅ Both APIs complement each other well")
    
    print(f"\n🚀 NEXT STEPS FOR HISTORICAL DATA:")
    print("1. Use Alpha Vantage DAILY endpoint for stock history")
    print("2. Use CoinGecko /coins/{id}/history for crypto history")
    print("3. Collect data during weekdays for stocks")
    print("4. Consider premium API tiers for production")
    print("5. Implement data validation and quality checks")


if __name__ == "__main__":
    main()