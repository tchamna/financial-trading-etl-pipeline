"""
Integration tests for the complete Financial Trading ETL Pipeline
Tests end-to-end functionality including API calls, processing, and data loading
"""

import pytest
import requests
import time
import os
from datetime import datetime, timedelta
import pandas as pd
import boto3
from moto import mock_s3
from unittest.mock import patch, MagicMock

class TestFinancialPipelineIntegration:
    """Integration tests for the complete pipeline"""
    
    @pytest.fixture(scope="class")
    def aws_credentials(self):
        """Mock AWS Credentials for testing"""
        os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
        os.environ['AWS_SECURITY_TOKEN'] = 'testing'
        os.environ['AWS_SESSION_TOKEN'] = 'testing'
        os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

    @mock_s3
    def test_api_data_ingestion(self, aws_credentials):
        """Test API data ingestion and S3 storage"""
        # Create mock S3 bucket
        s3 = boto3.client('s3', region_name='us-east-1')
        bucket_name = 'financial-trading-data-lake-test'
        s3.create_bucket(Bucket=bucket_name)
        
        # Mock API responses
        with patch('requests.get') as mock_get:
            # Mock Alpha Vantage response
            mock_alpha_response = {
                'Time Series (5min)': {
                    '2024-01-01 09:30:00': {
                        '1. open': '150.0000',
                        '2. high': '155.0000', 
                        '3. low': '149.0000',
                        '4. close': '154.0000',
                        '5. volume': '1000000'
                    }
                }
            }
            
            # Mock CoinGecko response
            mock_crypto_response = [{
                'id': 'bitcoin',
                'symbol': 'btc',
                'name': 'Bitcoin',
                'current_price': 45000.50,
                'market_cap': 900000000000,
                'total_volume': 25000000000
            }]
            
            mock_get.side_effect = [
                MagicMock(status_code=200, json=lambda: mock_alpha_response),
                MagicMock(status_code=200, json=lambda: mock_crypto_response)
            ]
            
            # Import and test the data ingestion function
            from airflow_financial_pipeline import fetch_market_data
            
            # Create mock context
            mock_context = {
                'ti': MagicMock(),
                'alpha_vantage_api_key': 'test-key'
            }
            
            # Test data fetching
            fetch_market_data(**mock_context)
            
            # Verify S3 uploads were attempted
            mock_context['ti'].xcom_push.assert_called()

    def test_spark_transformation_logic(self):
        """Test Spark transformation logic with sample data"""
        from pyspark.sql import SparkSession
        from spark.financial_data_transformation import FinancialDataTransformer
        
        spark = SparkSession.builder.appName("IntegrationTest").master("local[1]").getOrCreate()
        
        try:
            transformer = FinancialDataTransformer()
            
            # Create sample stock data
            sample_data = [
                ('2024-01-01 09:30:00', 'AAPL', 150.00, 155.00, 149.00, 154.00, 1000000),
                ('2024-01-01 10:00:00', 'AAPL', 154.00, 156.00, 153.00, 155.50, 1200000),
                ('2024-01-01 10:30:00', 'AAPL', 155.50, 157.00, 154.50, 156.25, 1100000)
            ]
            
            df = spark.createDataFrame(sample_data, 
                ['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume'])
            
            # Convert timestamp column
            from pyspark.sql.functions import col, to_timestamp
            df = df.withColumn('timestamp', to_timestamp(col('timestamp')))
            
            # Test cleaning
            cleaned_df = transformer.clean_stock_data(df)
            assert cleaned_df.count() == 3
            
            # Test technical indicators
            df_with_indicators = transformer.calculate_technical_indicators(cleaned_df)
            assert 'sma_5' in df_with_indicators.columns
            assert 'price_change' in df_with_indicators.columns
            
            # Verify calculations
            results = df_with_indicators.collect()
            assert results[1]['price_change'] > 0  # Price increased from first to second record
            
        finally:
            spark.stop()

    def test_airflow_dag_structure(self):
        """Test Airflow DAG structure and dependencies"""
        from airflow_financial_pipeline import dag
        
        # Test DAG properties
        assert dag.dag_id == "FINANCIAL_TRADING_ETL_PIPELINE"
        assert dag.schedule_interval is not None
        assert len(dag.tags) > 0
        
        # Test task dependencies
        task_ids = [task.task_id for task in dag.tasks]
        required_tasks = [
            'fetch_market_data_from_apis',
            'validate_data_quality', 
            'create_emr_cluster',
            'run_spark_transformation',
            'load_data_to_snowflake'
        ]
        
        for required_task in required_tasks:
            assert required_task in task_ids, f"Required task {required_task} not found in DAG"

    @pytest.mark.skipif(not os.getenv('RUN_LIVE_TESTS'), reason="Live API tests disabled")
    def test_live_api_connectivity(self):
        """Test actual API connectivity (only run if RUN_LIVE_TESTS=1)"""
        # Test Alpha Vantage API
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=AAPL&interval=5min&apikey={api_key}"
        
        response = requests.get(url, timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        assert 'Time Series (5min)' in data or 'Note' in data  # Note appears for demo key
        
        # Test CoinGecko API
        crypto_url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=1&page=1"
        crypto_response = requests.get(crypto_url, timeout=30)
        assert crypto_response.status_code == 200
        
        crypto_data = crypto_response.json()
        assert len(crypto_data) == 1
        assert 'current_price' in crypto_data[0]

    def test_data_quality_validation(self):
        """Test data quality validation framework"""
        import pandas as pd
        
        # Create test data with quality issues
        test_data = pd.DataFrame({
            'symbol': ['AAPL', 'GOOGL', None, 'INVALID'],  # Null symbol
            'close': [150.0, 2800.0, -100.0, None],        # Negative and null prices
            'volume': [1000000, 800000, -5000, 2000000],   # Negative volume
            'timestamp': ['2024-01-01 09:30', '2024-01-01 09:30', 
                         '2024-01-01 09:30', '2024-01-01 09:30']
        })
        
        # Test data quality rules
        quality_issues = []
        
        # Check for null symbols
        null_symbols = test_data['symbol'].isnull().sum()
        if null_symbols > 0:
            quality_issues.append(f"Found {null_symbols} null symbols")
        
        # Check for invalid prices
        invalid_prices = (test_data['close'] <= 0).sum() + test_data['close'].isnull().sum()
        if invalid_prices > 0:
            quality_issues.append(f"Found {invalid_prices} invalid prices")
            
        # Check for negative volumes
        negative_volumes = (test_data['volume'] < 0).sum()
        if negative_volumes > 0:
            quality_issues.append(f"Found {negative_volumes} negative volumes")
        
        # Assert we detected the issues
        assert len(quality_issues) == 3, f"Expected 3 quality issues, found: {quality_issues}"

    def test_performance_benchmarks(self):
        """Test performance benchmarks for the pipeline"""
        from pyspark.sql import SparkSession
        from spark.financial_data_transformation import FinancialDataTransformer
        import time
        
        spark = SparkSession.builder.appName("PerformanceTest").master("local[2]").getOrCreate()
        
        try:
            transformer = FinancialDataTransformer()
            
            # Generate larger dataset for performance testing
            large_data = []
            symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA'] * 1000  # 5000 records
            
            for i, symbol in enumerate(symbols):
                timestamp = f'2024-01-01 {9 + (i % 8):02d}:30:00'
                large_data.append((timestamp, symbol, 150.0, 155.0, 149.0, 154.0, 1000000))
            
            df = spark.createDataFrame(large_data, 
                ['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume'])
            
            # Convert timestamp
            from pyspark.sql.functions import col, to_timestamp
            df = df.withColumn('timestamp', to_timestamp(col('timestamp')))
            
            # Benchmark cleaning performance
            start_time = time.time()
            cleaned_df = transformer.clean_stock_data(df)
            cleaning_time = time.time() - start_time
            
            # Benchmark technical indicators
            start_time = time.time()
            df_with_indicators = transformer.calculate_technical_indicators(cleaned_df)
            df_with_indicators.count()  # Force computation
            indicators_time = time.time() - start_time
            
            # Performance assertions (adjust thresholds as needed)
            assert cleaning_time < 10.0, f"Data cleaning took too long: {cleaning_time:.2f}s"
            assert indicators_time < 30.0, f"Technical indicators took too long: {indicators_time:.2f}s"
            
            print(f"Performance results:")
            print(f"  Data cleaning: {cleaning_time:.2f}s for {df.count()} records")
            print(f"  Technical indicators: {indicators_time:.2f}s")
            
        finally:
            spark.stop()

    @mock_s3  
    def test_s3_data_lifecycle(self, aws_credentials):
        """Test S3 data operations and lifecycle"""
        s3 = boto3.client('s3', region_name='us-east-1')
        bucket_name = 'financial-trading-data-lifecycle-test'
        s3.create_bucket(Bucket=bucket_name)
        
        # Test file upload
        test_content = "symbol,timestamp,close\nAAPL,2024-01-01,150.0\nGOOGL,2024-01-01,2800.0"
        s3.put_object(Bucket=bucket_name, Key='raw/stocks/2024-01-01/AAPL.csv', Body=test_content)
        
        # Test file exists
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix='raw/stocks/')
        assert response['KeyCount'] == 1
        
        # Test file retrieval
        obj = s3.get_object(Bucket=bucket_name, Key='raw/stocks/2024-01-01/AAPL.csv')
        content = obj['Body'].read().decode('utf-8')
        assert 'AAPL' in content
        assert 'GOOGL' in content

    def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms"""
        from spark.financial_data_transformation import FinancialDataTransformer
        from pyspark.sql import SparkSession
        
        spark = SparkSession.builder.appName("ErrorTest").master("local[1]").getOrCreate()
        
        try:
            transformer = FinancialDataTransformer()
            
            # Test handling of empty dataset
            empty_df = spark.createDataFrame([], transformer.get_stock_schema())
            cleaned_empty = transformer.clean_stock_data(empty_df)
            assert cleaned_empty.count() == 0
            
            # Test handling of all-null dataset
            null_data = [(None, None, None, None, None, None, None)]
            null_df = spark.createDataFrame(null_data, 
                ['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume'])
            
            cleaned_null = transformer.clean_stock_data(null_df)
            assert cleaned_null.count() == 0  # Should filter out invalid records
            
        except Exception as e:
            pytest.fail(f"Error handling failed: {str(e)}")
        finally:
            spark.stop()

if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short"])