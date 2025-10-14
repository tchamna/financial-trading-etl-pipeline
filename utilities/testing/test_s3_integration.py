#!/usr/bin/env python3
"""
S3 Integration Test for Financial Trading ETL Pipeline
====================================================

Author: Shck Tchamna (tchamna@gmail.com)
Tests AWS S3 data upload functionality with real financial data

This script demonstrates:
1. Connection to AWS S3
2. Data upload in multiple formats (JSON, Parquet)
3. Proper data partitioning by date and asset type
4. Compression and storage optimization
5. Data lake architecture implementation
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime, timezone
from dotenv import load_dotenv

# Add scripts directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from s3_data_uploader import create_s3_uploader_from_env
except ImportError as e:
    print(f"❌ Failed to import S3 uploader: {e}")
    sys.exit(1)

class S3IntegrationTest:
    """Test S3 integration with financial data"""
    
    def __init__(self):
        load_dotenv()
        
        print("☁️  AWS S3 INTEGRATION TEST")
        print("=" * 50)
        
        # Initialize S3 uploader
        try:
            self.s3_uploader = create_s3_uploader_from_env()
            print("✅ S3 connection established")
        except Exception as e:
            print(f"❌ S3 connection failed: {e}")
            print("\n📋 Required Environment Variables:")
            print("   - AWS_S3_BUCKET_NAME")
            print("   - AWS_ACCESS_KEY_ID")
            print("   - AWS_SECRET_ACCESS_KEY")
            print("   - AWS_DEFAULT_REGION (optional)")
            raise
    
    def generate_sample_data(self):
        """Generate sample financial data for testing"""
        print("\n📊 Generating sample financial data...")
        
        # Sample stock data
        self.stock_data = [
            {
                "symbol": "AAPL",
                "company_name": "Apple Inc.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "open_price": 245.10,
                "high_price": 246.80,
                "low_price": 244.50,
                "close_price": 245.40,
                "volume": 1500000,
                "market_cap": 3800000000000,
                "sector": "Technology",
                "pe_ratio": 28.5,
                "data_source": "Alpha Vantage API"
            },
            {
                "symbol": "GOOGL", 
                "company_name": "Alphabet Inc.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "open_price": 235.20,
                "high_price": 236.90,
                "low_price": 234.80,
                "close_price": 235.77,
                "volume": 1200000,
                "market_cap": 2900000000000,
                "sector": "Technology",
                "pe_ratio": 24.2,
                "data_source": "Alpha Vantage API"
            },
            {
                "symbol": "TSLA",
                "company_name": "Tesla Inc.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "open_price": 248.30,
                "high_price": 250.10,
                "low_price": 247.80,
                "close_price": 248.95,
                "volume": 2100000,
                "market_cap": 790000000000,
                "sector": "Automotive",
                "pe_ratio": 65.8,
                "data_source": "Alpha Vantage API"
            }
        ]
        
        # Sample crypto data
        self.crypto_data = [
            {
                "symbol": "BTC",
                "name": "Bitcoin",
                "current_price": 114823.45,
                "market_cap": 2274000000000,
                "market_cap_rank": 1,
                "price_change_24h": 2847.23,
                "price_change_percentage_24h": 2.56,
                "volume_24h": 45600000000,
                "circulating_supply": 19750000,
                "total_supply": 21000000,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data_source": "CoinGecko API"
            },
            {
                "symbol": "ETH",
                "name": "Ethereum", 
                "current_price": 4172.89,
                "market_cap": 501800000000,
                "market_cap_rank": 2,
                "price_change_24h": -45.67,
                "price_change_percentage_24h": -1.08,
                "volume_24h": 23400000000,
                "circulating_supply": 120280000,
                "total_supply": 120280000,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data_source": "CoinGecko API"
            },
            {
                "symbol": "ADA",
                "name": "Cardano",
                "current_price": 0.892,
                "market_cap": 31240000000,
                "market_cap_rank": 8,
                "price_change_24h": 0.023,
                "price_change_percentage_24h": 2.64,
                "volume_24h": 1890000000,
                "circulating_supply": 35020000000,
                "total_supply": 45000000000,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data_source": "CoinGecko API"
            }
        ]
        
        # Technical analysis data
        self.technical_data = [
            {
                "symbol": "AAPL",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "rsi_14": 58.2,
                "sma_20": 243.80,
                "sma_50": 238.90,
                "sma_200": 225.60,
                "macd": 1.23,
                "bollinger_upper": 248.50,
                "bollinger_lower": 240.20,
                "volatility_20d": 0.285,
                "golden_cross_signal": "NEUTRAL",
                "trading_signal": "BUY",
                "confidence": 0.72
            }
        ]
        
        print(f"✅ Generated {len(self.stock_data)} stock records")
        print(f"✅ Generated {len(self.crypto_data)} crypto records")
        print(f"✅ Generated {len(self.technical_data)} technical analysis records")
    
    def test_json_uploads(self):
        """Test uploading data in JSON format"""
        print("\n🔄 Testing JSON Data Uploads...")
        print("-" * 40)
        
        try:
            # Upload stock data
            stock_path = self.s3_uploader.upload_stock_data(
                self.stock_data,
                data_type='processed',
                compress=True
            )
            print(f"📈 Stock data: {stock_path}")
            
            # Upload crypto data
            crypto_path = self.s3_uploader.upload_crypto_data(
                self.crypto_data,
                data_type='processed',
                compress=True
            )
            print(f"🪙 Crypto data: {crypto_path}")
            
            # Upload technical analysis
            technical_path = self.s3_uploader.upload_technical_analysis(
                self.technical_data,
                asset_type='stocks',
                compress=True
            )
            print(f"📊 Technical analysis: {technical_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ JSON upload failed: {e}")
            return False
    
    def test_parquet_uploads(self):
        """Test uploading data in Parquet format"""
        print("\n🔄 Testing Parquet Data Uploads...")
        print("-" * 40)
        
        try:
            # Convert to DataFrames and upload as Parquet
            stock_df = pd.DataFrame(self.stock_data)
            parquet_path = self.s3_uploader.upload_parquet_data(
                stock_df,
                "processed/stocks/parquet/stock_data",
                compression='snappy'
            )
            print(f"📈 Stock Parquet: {parquet_path}")
            
            crypto_df = pd.DataFrame(self.crypto_data)
            crypto_parquet_path = self.s3_uploader.upload_parquet_data(
                crypto_df,
                "processed/crypto/parquet/crypto_data",
                compression='snappy'
            )
            print(f"🪙 Crypto Parquet: {crypto_parquet_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ Parquet upload failed: {e}")
            return False
    
    def test_portfolio_upload(self):
        """Test portfolio data upload"""
        print("\n🔄 Testing Portfolio Data Upload...")
        print("-" * 40)
        
        portfolio_data = {
            "portfolio_name": "Tech_Growth_Portfolio",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_value": 125000.00,
            "holdings": [
                {
                    "symbol": "AAPL",
                    "quantity": 100,
                    "avg_cost": 230.50,
                    "current_value": 24540.00,
                    "allocation_pct": 19.6
                },
                {
                    "symbol": "GOOGL",
                    "quantity": 50,
                    "avg_cost": 220.00,
                    "current_value": 11788.50,
                    "allocation_pct": 9.4
                }
            ],
            "performance_metrics": {
                "total_return_pct": 12.5,
                "sharpe_ratio": 1.35,
                "max_drawdown": -8.2,
                "beta": 1.15
            }
        }
        
        try:
            portfolio_path = self.s3_uploader.upload_portfolio_data(
                portfolio_data,
                portfolio_name="tech_growth",
                compress=True
            )
            print(f"💼 Portfolio: {portfolio_path}")
            return True
            
        except Exception as e:
            print(f"❌ Portfolio upload failed: {e}")
            return False
    
    def test_data_listing(self):
        """Test listing uploaded data"""
        print("\n🔄 Testing Data Listing...")
        print("-" * 40)
        
        try:
            # List processed data
            processed_objects = self.s3_uploader.list_objects(
                prefix='processed/',
                max_objects=20
            )
            
            print(f"📁 Found {len(processed_objects)} objects in 'processed/' prefix:")
            for obj in processed_objects[:5]:  # Show first 5
                size_kb = obj['size'] / 1024
                print(f"   📄 {obj['key']} ({size_kb:.2f} KB)")
            
            if len(processed_objects) > 5:
                print(f"   ... and {len(processed_objects) - 5} more objects")
            
            return True
            
        except Exception as e:
            print(f"❌ Data listing failed: {e}")
            return False
    
    def test_storage_metrics(self):
        """Test storage metrics collection"""
        print("\n🔄 Testing Storage Metrics...")
        print("-" * 40)
        
        try:
            metrics = self.s3_uploader.get_storage_metrics()
            
            print(f"📊 Storage Metrics for bucket: {metrics.get('bucket_name')}")
            print(f"   📈 Total objects: {metrics.get('total_objects', 0)}")
            print(f"   💾 Total size: {metrics.get('total_size_mb', 0):.2f} MB")
            
            print("\n📋 By data type:")
            for data_type, stats in metrics.get('by_data_type', {}).items():
                print(f"   {data_type}: {stats['count']} objects, {stats['size_mb']:.2f} MB")
            
            return True
            
        except Exception as e:
            print(f"❌ Storage metrics failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run complete S3 integration test suite"""
        print("\n🚀 Starting S3 Integration Test Suite...")
        
        results = []
        
        # Generate test data
        self.generate_sample_data()
        
        # Run tests
        test_methods = [
            ("JSON Uploads", self.test_json_uploads),
            ("Parquet Uploads", self.test_parquet_uploads), 
            ("Portfolio Upload", self.test_portfolio_upload),
            ("Data Listing", self.test_data_listing),
            ("Storage Metrics", self.test_storage_metrics)
        ]
        
        for test_name, test_method in test_methods:
            try:
                result = test_method()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ Test '{test_name}' crashed: {e}")
                results.append((test_name, False))
        
        # Print results summary
        print("\n" + "=" * 50)
        print("📋 S3 INTEGRATION TEST RESULTS")
        print("=" * 50)
        
        passed = 0
        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\n📊 Summary: {passed}/{len(results)} tests passed")
        
        if passed == len(results):
            print("🎉 All S3 integration tests PASSED!")
            print("✅ Your pipeline is ready for cloud deployment!")
        else:
            print("⚠️  Some tests failed - check AWS configuration")
            
        return passed == len(results)

if __name__ == "__main__":
    """Run S3 integration tests"""
    
    try:
        tester = S3IntegrationTest()
        success = tester.run_all_tests()
        
        if success:
            print("\n🚀 Next Steps:")
            print("   1. Your financial data is now stored in AWS S3")
            print("   2. Set up AWS EMR for Spark processing")
            print("   3. Configure Snowflake S3 integration") 
            print("   4. Enable AWS Athena for SQL queries")
            print("   5. Set up AWS Glue Data Catalog")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        sys.exit(1)