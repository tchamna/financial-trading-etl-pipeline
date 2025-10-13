#!/usr/bin/env python3
"""
Financial Trading ETL Pipeline - Integration Test
Tests all pipeline components: APIs, Database, Data Processing, Docker Services
"""

import os
import sys
import time
import requests
import pandas as pd
import psycopg2
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class PipelineIntegrationTester:
    """Complete integration testing for the financial trading ETL pipeline"""
    
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
        print("🚀 Financial Trading ETL Pipeline - Integration Test")
        print("=" * 60)
        print(f"🕒 Test started at: {self.start_time}")
        print()
    
    def test_docker_services(self):
        """Test Docker services connectivity"""
        print("🐳 Testing Docker Services")
        print("-" * 30)
        
        services_tested = 0
        services_passed = 0
        
        # Test PostgreSQL
        try:
            print("🔍 Testing PostgreSQL...")
            conn = psycopg2.connect(
                host='localhost', 
                port=5433, 
                database='airflow', 
                user='airflow', 
                password='airflow'
            )
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"   ✅ PostgreSQL connected - {version[:30]}...")
            conn.close()
            services_passed += 1
        except Exception as e:
            print(f"   ❌ PostgreSQL failed: {str(e)}")
        services_tested += 1
        
        # Test Redis
        try:
            print("🔍 Testing Redis...")
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            r.ping()
            info = r.info()
            print(f"   ✅ Redis connected - version {info['redis_version']}")
            services_passed += 1
        except Exception as e:
            print(f"   ❌ Redis failed: {str(e)}")
        services_tested += 1
        
        # Test Jupyter
        try:
            print("🔍 Testing Jupyter Lab...")
            response = requests.get('http://localhost:8888/api', timeout=5)
            if response.status_code in [200, 401]:  # 401 is expected without token
                print(f"   ✅ Jupyter Lab accessible - status {response.status_code}")
                services_passed += 1
            else:
                print(f"   ❌ Jupyter Lab unexpected status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Jupyter Lab failed: {str(e)}")
        services_tested += 1
        
        print(f"\n📊 Docker Services: {services_passed}/{services_tested} passed")
        return services_passed, services_tested
    
    def test_api_connectivity(self):
        """Test financial APIs"""
        print("\n🌐 Testing Financial APIs")
        print("-" * 30)
        
        apis_tested = 0
        apis_passed = 0
        
        # Test Alpha Vantage
        try:
            print("🔍 Testing Alpha Vantage...")
            api_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'TIME_SERIES_INTRADAY',
                'symbol': 'AAPL',
                'interval': '5min',
                'apikey': api_key
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'Time Series (5min)' in data:
                records = len(data['Time Series (5min)'])
                print(f"   ✅ Alpha Vantage working - {records} records")
                apis_passed += 1
            else:
                print(f"   ❌ Alpha Vantage failed - {data.get('Information', 'No data')}")
        except Exception as e:
            print(f"   ❌ Alpha Vantage error: {str(e)}")
        apis_tested += 1
        
        # Test CoinGecko
        try:
            print("🔍 Testing CoinGecko...")
            url = "https://api.coingecko.com/api/v3/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': 5,
                'page': 1
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                btc_price = next((coin['current_price'] for coin in data if coin['symbol'] == 'btc'), 'N/A')
                print(f"   ✅ CoinGecko working - BTC: ${btc_price}")
                apis_passed += 1
            else:
                print(f"   ❌ CoinGecko failed - invalid response")
        except Exception as e:
            print(f"   ❌ CoinGecko error: {str(e)}")
        apis_tested += 1
        
        print(f"\n📊 API Tests: {apis_passed}/{apis_tested} passed")
        return apis_passed, apis_tested
    
    def test_data_processing(self):
        """Test core data processing capabilities"""
        print("\n⚙️ Testing Data Processing")
        print("-" * 30)
        
        processing_tests = 0
        processing_passed = 0
        
        # Test Pandas DataFrame operations
        try:
            print("🔍 Testing Pandas operations...")
            # Create sample financial data
            dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
            df = pd.DataFrame({
                'date': dates,
                'symbol': 'AAPL',
                'price': 150 + pd.Series(range(100)).apply(lambda x: x * 0.5 + (x % 7) * 2),
                'volume': 1000000 + pd.Series(range(100)) * 10000
            })
            
            # Basic transformations
            df['sma_10'] = df['price'].rolling(window=10).mean()
            df['price_change'] = df['price'].pct_change()
            df['high_volume'] = df['volume'] > df['volume'].median()
            
            # Validation
            assert len(df) == 100, "DataFrame length incorrect"
            assert df['sma_10'].notna().sum() >= 90, "SMA calculation failed"
            assert not df['price_change'].isna().all(), "Price change calculation failed"
            
            print(f"   ✅ Pandas processing - {len(df)} records processed")
            processing_passed += 1
        except Exception as e:
            print(f"   ❌ Pandas processing failed: {str(e)}")
        processing_tests += 1
        
        # Test financial calculations
        try:
            print("🔍 Testing financial calculations...")
            prices = [100, 102, 98, 105, 103, 107, 104, 109, 106, 110]
            
            # RSI calculation (simplified)
            def calculate_rsi(prices, period=14):
                if len(prices) < period + 1:
                    period = len(prices) - 1
                
                gains = []
                losses = []
                
                for i in range(1, len(prices)):
                    change = prices[i] - prices[i-1]
                    if change > 0:
                        gains.append(change)
                        losses.append(0)
                    else:
                        gains.append(0)
                        losses.append(abs(change))
                
                avg_gain = sum(gains[-period:]) / period if gains else 0
                avg_loss = sum(losses[-period:]) / period if losses else 0.01
                
                rs = avg_gain / avg_loss if avg_loss > 0 else 0
                rsi = 100 - (100 / (1 + rs))
                return rsi
            
            rsi = calculate_rsi(prices)
            volatility = pd.Series(prices).pct_change().std() * 100
            
            assert 0 <= rsi <= 100, "RSI out of valid range"
            assert volatility >= 0, "Volatility calculation invalid"
            
            print(f"   ✅ Financial calculations - RSI: {rsi:.2f}, Vol: {volatility:.2f}%")
            processing_passed += 1
        except Exception as e:
            print(f"   ❌ Financial calculations failed: {str(e)}")
        processing_tests += 1
        
        print(f"\n📊 Processing Tests: {processing_passed}/{processing_tests} passed")
        return processing_passed, processing_tests
    
    def test_database_operations(self):
        """Test database operations"""
        print("\n💾 Testing Database Operations")
        print("-" * 30)
        
        db_tests = 0
        db_passed = 0
        
        try:
            print("🔍 Testing database schema creation...")
            
            conn = psycopg2.connect(
                host='localhost', 
                port=5433, 
                database='airflow', 
                user='airflow', 
                password='airflow'
            )
            cursor = conn.cursor()
            
            # Create test table
            cursor.execute("""
                DROP TABLE IF EXISTS test_financial_data;
                CREATE TABLE test_financial_data (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(10) NOT NULL,
                    price DECIMAL(10,2) NOT NULL,
                    volume BIGINT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Insert test data
            test_data = [
                ('AAPL', 150.00, 1000000),
                ('GOOGL', 2800.50, 800000),
                ('TSLA', 220.75, 1200000)
            ]
            
            cursor.executemany(
                "INSERT INTO test_financial_data (symbol, price, volume) VALUES (%s, %s, %s)",
                test_data
            )
            
            # Query data
            cursor.execute("SELECT COUNT(*) FROM test_financial_data;")
            count = cursor.fetchone()[0]
            
            cursor.execute("SELECT symbol, price FROM test_financial_data ORDER BY price DESC;")
            results = cursor.fetchall()
            
            conn.commit()
            conn.close()
            
            assert count == 3, f"Expected 3 records, got {count}"
            assert results[0][0] == 'GOOGL', "Sorting failed"
            
            print(f"   ✅ Database operations - {count} records created and queried")
            db_passed += 1
            
        except Exception as e:
            print(f"   ❌ Database operations failed: {str(e)}")
        db_tests += 1
        
        print(f"\n📊 Database Tests: {db_passed}/{db_tests} passed")
        return db_passed, db_tests
    
    def test_pipeline_simulation(self):
        """Simulate end-to-end pipeline execution"""
        print("\n🔄 Testing Pipeline Simulation")
        print("-" * 30)
        
        pipeline_tests = 0
        pipeline_passed = 0
        
        try:
            print("🔍 Running end-to-end simulation...")
            
            # 1. Fetch market data (simulated)
            market_data = {
                'AAPL': {'price': 150.25, 'change': 2.1},
                'GOOGL': {'price': 2801.75, 'change': -0.8},
                'TSLA': {'price': 221.30, 'change': 1.5}
            }
            
            # 2. Process data
            processed_data = []
            for symbol, data in market_data.items():
                processed_data.append({
                    'symbol': symbol,
                    'price': data['price'],
                    'change_pct': data['change'],
                    'signal': 'BUY' if data['change'] > 0 else 'SELL',
                    'processed_at': datetime.now().isoformat()
                })
            
            # 3. Store in database
            conn = psycopg2.connect(
                host='localhost', 
                port=5433, 
                database='airflow', 
                user='airflow', 
                password='airflow'
            )
            cursor = conn.cursor()
            
            cursor.execute("DROP TABLE IF EXISTS pipeline_test_results;")
            cursor.execute("""
                CREATE TABLE pipeline_test_results (
                    symbol VARCHAR(10),
                    price DECIMAL(10,2),
                    change_pct DECIMAL(5,2),
                    signal VARCHAR(10),
                    processed_at TIMESTAMP
                );
            """)
            
            for record in processed_data:
                cursor.execute(
                    "INSERT INTO pipeline_test_results VALUES (%s, %s, %s, %s, %s)",
                    (record['symbol'], record['price'], record['change_pct'], 
                     record['signal'], record['processed_at'])
                )
            
            conn.commit()
            
            # 4. Validate results
            cursor.execute("SELECT COUNT(*) FROM pipeline_test_results;")
            total_records = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM pipeline_test_results WHERE signal = 'BUY';")
            buy_signals = cursor.fetchone()[0]
            
            conn.close()
            
            # 5. Generate summary
            success_rate = (len([d for d in processed_data if d['signal'] == 'BUY']) / len(processed_data)) * 100
            
            print(f"   📊 Market data processed: {len(market_data)} symbols")
            print(f"   📊 Records stored: {total_records}")
            print(f"   📊 Buy signals: {buy_signals}")
            print(f"   📊 Success rate: {success_rate:.1f}%")
            print(f"   ✅ Pipeline simulation completed successfully")
            
            pipeline_passed += 1
            
        except Exception as e:
            print(f"   ❌ Pipeline simulation failed: {str(e)}")
        pipeline_tests += 1
        
        print(f"\n📊 Pipeline Tests: {pipeline_passed}/{pipeline_tests} passed")
        return pipeline_passed, pipeline_tests
    
    def run_all_tests(self):
        """Run complete integration test suite"""
        print("🧪 Starting Complete Integration Test Suite")
        print("=" * 60)
        
        # Run all test categories
        docker_passed, docker_total = self.test_docker_services()
        api_passed, api_total = self.test_api_connectivity()
        processing_passed, processing_total = self.test_data_processing()
        db_passed, db_total = self.test_database_operations()
        pipeline_passed, pipeline_total = self.test_pipeline_simulation()
        
        # Calculate totals
        total_passed = docker_passed + api_passed + processing_passed + db_passed + pipeline_passed
        total_tests = docker_total + api_total + processing_total + db_total + pipeline_total
        
        # Generate final report
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        print("\n" + "=" * 60)
        print("📊 INTEGRATION TEST SUMMARY")
        print("=" * 60)
        
        test_categories = [
            ("🐳 Docker Services", docker_passed, docker_total),
            ("🌐 Financial APIs", api_passed, api_total),
            ("⚙️ Data Processing", processing_passed, processing_total),
            ("💾 Database Operations", db_passed, db_total),
            ("🔄 Pipeline Simulation", pipeline_passed, pipeline_total)
        ]
        
        for category, passed, total in test_categories:
            status = "✅" if passed == total else "❌"
            percentage = (passed/total)*100 if total > 0 else 0
            print(f"{status} {category}: {passed}/{total} ({percentage:.1f}%)")
        
        overall_percentage = (total_passed/total_tests)*100 if total_tests > 0 else 0
        print(f"\n🎯 Overall Success Rate: {total_passed}/{total_tests} ({overall_percentage:.1f}%)")
        print(f"⏱️ Total Duration: {duration.total_seconds():.1f} seconds")
        
        if total_passed == total_tests:
            print("\n🎉 ALL TESTS PASSED! Your financial trading ETL pipeline is ready!")
            print("\n📝 Next Steps:")
            print("   1. 🌐 Access Jupyter Lab: http://localhost:8888")
            print("      Token: financial_pipeline_2024")
            print("   2. 🚀 Start Airflow: docker-compose up airflow-standalone")
            print("   3. ☁️ Deploy to AWS: Set up EMR and S3 buckets")
            print("   4. 🏢 Connect Snowflake: Update .env with credentials")
        else:
            print(f"\n⚠️ {total_tests - total_passed} tests failed. Review the output above.")
        
        return total_passed == total_tests

def main():
    """Run integration tests"""
    tester = PipelineIntegrationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()