"""
Comprehensive test suite for Financial Data Transformation Pipeline
Tests data quality, transformations, and business logic
"""

import pytest
import sys
from decimal import Decimal
from datetime import datetime, timedelta
from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import col, lit
from financial_data_transformation import FinancialDataTransformer

class TestFinancialDataTransformer:
    """Test suite for financial data transformation pipeline"""
    
    @pytest.fixture(scope="class")
    def spark(self):
        """Create Spark session for testing"""
        spark = SparkSession.builder \
            .appName("FinancialDataTest") \
            .master("local[2]") \
            .config("spark.sql.shuffle.partitions", "2") \
            .getOrCreate()
        
        yield spark
        spark.stop()
    
    @pytest.fixture
    def transformer(self, spark):
        """Create transformer instance"""
        return FinancialDataTransformer()
    
    @pytest.fixture
    def sample_stock_data(self, spark):
        """Create sample stock data for testing"""
        schema = StructType([
            StructField("timestamp", TimestampType(), True),
            StructField("symbol", StringType(), False),
            StructField("open", DecimalType(18, 4), True),
            StructField("high", DecimalType(18, 4), True),
            StructField("low", DecimalType(18, 4), True),
            StructField("close", DecimalType(18, 4), True),
            StructField("volume", IntegerType(), True)
        ])
        
        data = [
            (datetime(2024, 1, 1, 9, 30), "AAPL", Decimal("150.00"), Decimal("155.00"), 
             Decimal("149.00"), Decimal("154.00"), 1000000),
            (datetime(2024, 1, 1, 10, 30), "AAPL", Decimal("154.00"), Decimal("156.00"), 
             Decimal("153.00"), Decimal("155.50"), 1200000),
            (datetime(2024, 1, 1, 9, 30), "GOOGL", Decimal("2800.00"), Decimal("2850.00"), 
             Decimal("2790.00"), Decimal("2820.00"), 800000),
            # Invalid data for testing
            (datetime(2024, 1, 1, 11, 30), "INVALID", None, None, None, None, None),
            (datetime(2024, 1, 1, 12, 30), "TSLA", Decimal("200.00"), Decimal("190.00"),  # Invalid OHLC
             Decimal("210.00"), Decimal("195.00"), 500000)
        ]
        
        return spark.createDataFrame(data, schema)
    
    @pytest.fixture
    def sample_crypto_data(self, spark):
        """Create sample cryptocurrency data for testing"""
        schema = StructType([
            StructField("id", StringType(), False),
            StructField("symbol", StringType(), False),
            StructField("name", StringType(), True),
            StructField("current_price", DecimalType(18, 8), True),
            StructField("market_cap", IntegerType(), True),
            StructField("total_volume", IntegerType(), True),
            StructField("price_change_24h", DecimalType(18, 4), True),
            StructField("price_change_percentage_24h", DecimalType(10, 4), True),
            StructField("last_updated", TimestampType(), True)
        ])
        
        data = [
            ("bitcoin", "btc", "Bitcoin", Decimal("45000.50000000"), 900000000000, 
             25000000000, Decimal("1250.25"), Decimal("2.85"), datetime(2024, 1, 1, 12, 0)),
            ("ethereum", "eth", "Ethereum", Decimal("3200.75000000"), 400000000000, 
             15000000000, Decimal("-85.50"), Decimal("-2.60"), datetime(2024, 1, 1, 12, 0)),
            # Invalid data for testing
            ("invalid-coin", "inv", "Invalid Coin", None, None, None, None, None, None)
        ]
        
        return spark.createDataFrame(data, schema)
    
    def test_stock_data_cleaning(self, transformer, sample_stock_data):
        """Test stock data cleaning functionality"""
        cleaned_df = transformer.clean_stock_data(sample_stock_data)
        
        # Check that invalid records are filtered out
        assert cleaned_df.count() == 3  # Should remove 2 invalid records
        
        # Check that all remaining records have valid symbols and prices
        invalid_count = cleaned_df.filter(
            col("symbol").isNull() | 
            col("close").isNull() | 
            (col("close") <= 0)
        ).count()
        assert invalid_count == 0
        
        # Check that data quality flag is added
        assert "is_valid_ohlc" in cleaned_df.columns
        assert "processed_timestamp" in cleaned_df.columns
        
        # Check OHLC validation logic
        valid_ohlc_count = cleaned_df.filter(col("is_valid_ohlc") == True).count()
        assert valid_ohlc_count >= 2  # At least 2 valid OHLC records
    
    def test_crypto_data_cleaning(self, transformer, sample_crypto_data):
        """Test cryptocurrency data cleaning functionality"""
        cleaned_df = transformer.clean_crypto_data(sample_crypto_data)
        
        # Check that invalid records are filtered out
        assert cleaned_df.count() == 2  # Should remove 1 invalid record
        
        # Check that symbols are uppercase
        symbols = [row['symbol'] for row in cleaned_df.select("symbol").collect()]
        assert all(symbol.isupper() for symbol in symbols)
        
        # Check market cap categories
        assert "market_cap_category" in cleaned_df.columns
        categories = [row['market_cap_category'] for row in cleaned_df.select("market_cap_category").collect()]
        assert "Large Cap" in categories  # Bitcoin should be large cap
    
    def test_asset_dimension_creation(self, transformer, sample_stock_data, sample_crypto_data):
        """Test asset dimension table creation"""
        stock_clean = transformer.clean_stock_data(sample_stock_data)
        crypto_clean = transformer.clean_crypto_data(sample_crypto_data)
        
        assets_dim = transformer.create_asset_dimension(stock_clean, crypto_clean)
        
        # Check that both stock and crypto assets are included
        asset_types = [row['asset_type'] for row in assets_dim.select("asset_type").collect()]
        assert "Stock" in asset_types
        assert "Cryptocurrency" in asset_types
        
        # Check that asset_id is generated
        assert "asset_id" in assets_dim.columns
        
        # Check unique constraint on symbol + asset_type combination
        distinct_count = assets_dim.select("asset_symbol", "asset_type").distinct().count()
        assert distinct_count == assets_dim.count()
    
    def test_time_dimension_creation(self, transformer, sample_stock_data):
        """Test time dimension table creation"""
        time_dim = transformer.create_time_dimension(sample_stock_data)
        
        # Check required columns exist
        required_cols = ["date_key", "year", "month", "day", "hour", 
                        "is_weekend", "is_market_hours", "day_name"]
        for col_name in required_cols:
            assert col_name in time_dim.columns
        
        # Check date_key format (YYYYMMDD)
        date_keys = [row['date_key'] for row in time_dim.select("date_key").collect()]
        assert all(len(str(key)) == 8 for key in date_keys)
        
        # Check market hours logic (9 AM - 4 PM weekdays)
        market_hours_data = time_dim.filter(col("is_market_hours") == True).collect()
        for row in market_hours_data:
            assert 9 <= row['hour'] <= 16
            assert not row['is_weekend']
    
    def test_technical_indicators_calculation(self, transformer, sample_stock_data):
        """Test technical indicators calculation"""
        stock_clean = transformer.clean_stock_data(sample_stock_data)
        stock_with_indicators = transformer.calculate_technical_indicators(stock_clean)
        
        # Check that indicator columns are added
        indicator_cols = ["sma_5", "sma_20", "price_change", "price_change_pct"]
        for col_name in indicator_cols:
            assert col_name in stock_with_indicators.columns
        
        # Check that SMA calculation is reasonable
        aapl_data = stock_with_indicators.filter(col("symbol") == "AAPL").collect()
        assert len(aapl_data) > 0
        
        # For the second AAPL record, price change should be positive
        if len(aapl_data) >= 2:
            second_record = aapl_data[1]
            assert second_record['price_change'] > 0  # Price went from 154 to 155.5
    
    def test_market_fact_table_creation(self, transformer, sample_stock_data, sample_crypto_data):
        """Test market fact table creation"""
        stock_clean = transformer.clean_stock_data(sample_stock_data)
        crypto_clean = transformer.clean_crypto_data(sample_crypto_data)
        stock_with_indicators = transformer.calculate_technical_indicators(stock_clean)
        
        assets_dim = transformer.create_asset_dimension(stock_clean, crypto_clean)
        time_dim = transformer.create_time_dimension(stock_clean)
        
        market_facts = transformer.create_market_fact_table(
            stock_with_indicators, crypto_clean, assets_dim, time_dim
        )
        
        # Check that fact table has records
        assert market_facts.count() > 0
        
        # Check required columns
        required_cols = ["asset_id", "date_key", "timestamp", "close", "fact_type"]
        for col_name in required_cols:
            assert col_name in market_facts.columns
        
        # Check that both stock and crypto facts are included
        fact_types = [row['fact_type'] for row in market_facts.select("fact_type").collect()]
        assert "Stock" in fact_types
        assert "Cryptocurrency" in fact_types
        
        # Check foreign key relationships
        asset_ids_in_facts = set([row['asset_id'] for row in market_facts.select("asset_id").collect()])
        asset_ids_in_dim = set([row['asset_id'] for row in assets_dim.select("asset_id").collect()])
        assert asset_ids_in_facts.issubset(asset_ids_in_dim)
    
    def test_data_quality_validations(self, transformer, sample_stock_data):
        """Test data quality validation rules"""
        # Test with completely invalid data
        invalid_schema = StructType([
            StructField("symbol", StringType(), True),
            StructField("close", DecimalType(18, 4), True),
            StructField("volume", IntegerType(), True)
        ])
        
        invalid_data = [
            (None, None, None),  # All nulls
            ("", Decimal("-100.00"), -1000),  # Negative values
            ("VALID", Decimal("100.00"), 1000)  # One valid record
        ]
        
        invalid_df = transformer.spark.createDataFrame(invalid_data, invalid_schema)
        
        # Add timestamp for cleaning function
        invalid_df = invalid_df.withColumn("timestamp", lit(datetime.now()))
        invalid_df = invalid_df.withColumn("open", col("close"))
        invalid_df = invalid_df.withColumn("high", col("close"))
        invalid_df = invalid_df.withColumn("low", col("close"))
        
        cleaned_df = transformer.clean_stock_data(invalid_df)
        
        # Should only have 1 valid record after cleaning
        assert cleaned_df.count() == 1
        assert cleaned_df.first()['symbol'] == "VALID"
    
    def test_schema_validation(self, transformer):
        """Test schema definitions"""
        stock_schema = transformer.get_stock_schema()
        crypto_schema = transformer.get_crypto_schema()
        
        # Check required fields exist
        stock_field_names = [field.name for field in stock_schema.fields]
        assert "symbol" in stock_field_names
        assert "close" in stock_field_names
        assert "volume" in stock_field_names
        
        crypto_field_names = [field.name for field in crypto_schema.fields]
        assert "symbol" in crypto_field_names
        assert "current_price" in crypto_field_names
        assert "market_cap" in crypto_field_names
    
    def test_performance_and_memory(self, transformer, sample_stock_data):
        """Test pipeline performance with larger dataset"""
        # Create a larger dataset by repeating sample data
        large_df = sample_stock_data
        for i in range(5):  # Repeat data 5 times
            large_df = large_df.union(sample_stock_data)
        
        # Test that cleaning still works with larger dataset
        cleaned_df = transformer.clean_stock_data(large_df)
        assert cleaned_df.count() > 0
        
        # Test partitioning
        partitions = cleaned_df.rdd.getNumPartitions()
        assert partitions > 0

# Integration tests
class TestFinancialPipelineIntegration:
    """Integration tests for the complete pipeline"""
    
    @pytest.fixture(scope="class")
    def spark(self):
        spark = SparkSession.builder \
            .appName("FinancialPipelineIntegrationTest") \
            .master("local[2]") \
            .getOrCreate()
        yield spark
        spark.stop()
    
    def test_end_to_end_pipeline(self, spark):
        """Test complete pipeline execution"""
        transformer = FinancialDataTransformer()
        
        # Create comprehensive test datasets
        stock_data = self._create_comprehensive_stock_data(spark)
        crypto_data = self._create_comprehensive_crypto_data(spark)
        
        # Run complete transformation pipeline
        stock_clean = transformer.clean_stock_data(stock_data)
        crypto_clean = transformer.clean_crypto_data(crypto_data)
        stock_with_indicators = transformer.calculate_technical_indicators(stock_clean)
        
        assets_dim = transformer.create_asset_dimension(stock_clean, crypto_clean)
        time_dim = transformer.create_time_dimension(stock_clean)
        market_facts = transformer.create_market_fact_table(
            stock_with_indicators, crypto_clean, assets_dim, time_dim
        )
        
        # Validate end-to-end results
        assert stock_clean.count() > 0
        assert crypto_clean.count() > 0
        assert assets_dim.count() > 0
        assert time_dim.count() > 0
        assert market_facts.count() > 0
        
        # Check data integrity
        self._validate_data_integrity(assets_dim, time_dim, market_facts)
    
    def _create_comprehensive_stock_data(self, spark):
        """Create comprehensive stock data for testing"""
        schema = StructType([
            StructField("timestamp", TimestampType(), True),
            StructField("symbol", StringType(), False),
            StructField("open", DecimalType(18, 4), True),
            StructField("high", DecimalType(18, 4), True),
            StructField("low", DecimalType(18, 4), True),
            StructField("close", DecimalType(18, 4), True),
            StructField("volume", IntegerType(), True)
        ])
        
        # Generate time series data for multiple stocks
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]
        data = []
        
        for i in range(20):  # 20 time periods
            timestamp = datetime(2024, 1, 1, 9, 30) + timedelta(minutes=30*i)
            for symbol in symbols:
                base_price = {"AAPL": 150, "GOOGL": 2800, "MSFT": 350, "TSLA": 200}[symbol]
                price_variation = base_price * 0.02 * (i % 3 - 1)  # Small price movements
                
                close_price = Decimal(str(base_price + price_variation))
                open_price = close_price - Decimal("0.5")
                high_price = close_price + Decimal("1.0")
                low_price = close_price - Decimal("1.5")
                volume = 1000000 + (i * 50000)
                
                data.append((timestamp, symbol, open_price, high_price, low_price, close_price, volume))
        
        return spark.createDataFrame(data, schema)
    
    def _create_comprehensive_crypto_data(self, spark):
        """Create comprehensive crypto data for testing"""
        schema = StructType([
            StructField("id", StringType(), False),
            StructField("symbol", StringType(), False),
            StructField("name", StringType(), True),
            StructField("current_price", DecimalType(18, 8), True),
            StructField("market_cap", IntegerType(), True),
            StructField("total_volume", IntegerType(), True),
            StructField("price_change_24h", DecimalType(18, 4), True),
            StructField("price_change_percentage_24h", DecimalType(10, 4), True),
            StructField("last_updated", TimestampType(), True)
        ])
        
        data = [
            ("bitcoin", "btc", "Bitcoin", Decimal("45000.50000000"), 900000000000, 
             25000000000, Decimal("1250.25"), Decimal("2.85"), datetime(2024, 1, 1, 12, 0)),
            ("ethereum", "eth", "Ethereum", Decimal("3200.75000000"), 400000000000, 
             15000000000, Decimal("-85.50"), Decimal("-2.60"), datetime(2024, 1, 1, 12, 0)),
            ("cardano", "ada", "Cardano", Decimal("0.75000000"), 25000000000, 
             500000000, Decimal("0.05"), Decimal("7.15"), datetime(2024, 1, 1, 12, 0)),
        ]
        
        return spark.createDataFrame(data, schema)
    
    def _validate_data_integrity(self, assets_dim, time_dim, market_facts):
        """Validate referential integrity between dimensions and facts"""
        # Check that all asset_ids in facts exist in assets dimension
        fact_asset_ids = set([row['asset_id'] for row in market_facts.select("asset_id").distinct().collect()])
        dim_asset_ids = set([row['asset_id'] for row in assets_dim.select("asset_id").collect()])
        assert fact_asset_ids.issubset(dim_asset_ids), "Referential integrity violation: asset_id"
        
        # Check that all date_keys in facts exist in time dimension
        fact_date_keys = set([row['date_key'] for row in market_facts.select("date_key").distinct().collect()])
        dim_date_keys = set([row['date_key'] for row in time_dim.select("date_key").collect()])
        assert fact_date_keys.issubset(dim_date_keys), "Referential integrity violation: date_key"

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])