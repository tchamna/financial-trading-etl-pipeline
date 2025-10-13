"""
Financial Data Transformation Pipeline
Processes real-time market data from multiple sources and creates dimensional models
Author: Shck Tchamna
Email: tchamna@gmail.com
Date: 2025
"""

import sys
import logging
from decimal import Decimal
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField, StringType, DecimalType, 
    TimestampType, IntegerType, DoubleType
)
from pyspark.sql.functions import (
    col, lit, row_number, broadcast, when, isnan, isnull,
    regexp_replace, to_timestamp, round as spark_round,
    avg, stddev, min as spark_min, max as spark_max,
    lag, lead, expr, coalesce, current_timestamp
)
from pyspark.sql.window import Window

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class FinancialDataTransformer:
    """
    Main class for transforming financial market data
    """
    
    def __init__(self):
        self.spark = self.create_spark_session()
        
    def create_spark_session(self):
        """Create optimized Spark session for financial data processing"""
        logger.info("Creating Spark session...")
        
        spark = SparkSession.builder \
            .appName("FinancialDataTransformation") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .config("spark.sql.adaptive.skewJoin.enabled", "true") \
            .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
            .getOrCreate()
            
        # Set log level to reduce noise
        spark.sparkContext.setLogLevel("WARN")
        
        logger.info("Spark session created successfully.")
        return spark
    
    def get_stock_schema(self):
        """Define schema for stock market data"""
        return StructType([
            StructField("timestamp", TimestampType(), True),
            StructField("symbol", StringType(), False),
            StructField("open", DecimalType(18, 4), True),
            StructField("high", DecimalType(18, 4), True),
            StructField("low", DecimalType(18, 4), True),
            StructField("close", DecimalType(18, 4), True),
            StructField("volume", IntegerType(), True)
        ])
    
    def get_crypto_schema(self):
        """Define schema for cryptocurrency data"""
        return StructType([
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
    
    def read_data(self, input_path, schema=None, data_format="csv"):
        """Read data from S3 with error handling"""
        logger.info(f"Reading data from {input_path}...")
        
        try:
            if data_format == "csv":
                df = self.spark.read \
                    .options(header='True', inferSchema='False') \
                    .schema(schema) \
                    .csv(input_path)
            elif data_format == "parquet":
                df = self.spark.read.parquet(input_path)
            elif data_format == "json":
                df = self.spark.read \
                    .schema(schema) \
                    .json(input_path)
            else:
                raise ValueError(f"Unsupported data format: {data_format}")
            
            record_count = df.count()
            logger.info(f"Successfully read {record_count} records from {input_path}")
            
            # Basic data validation
            if record_count == 0:
                logger.warning(f"No records found in {input_path}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error reading data from {input_path}: {str(e)}")
            raise
    
    def clean_stock_data(self, df):
        """Clean and standardize stock market data"""
        logger.info("Cleaning stock market data...")
        
        # Remove null symbols and invalid prices
        df_clean = df.filter(
            col("symbol").isNotNull() &
            col("close").isNotNull() &
            (col("close") > 0) &
            col("volume").isNotNull() &
            (col("volume") >= 0)
        )
        
        # Handle missing OHLC data by using close price
        df_clean = df_clean \
            .withColumn("open", coalesce(col("open"), col("close"))) \
            .withColumn("high", coalesce(col("high"), col("close"))) \
            .withColumn("low", coalesce(col("low"), col("close")))
        
        # Add data quality flags
        df_clean = df_clean \
            .withColumn("is_valid_ohlc", 
                       when((col("high") >= col("low")) & 
                            (col("high") >= col("open")) & 
                            (col("high") >= col("close")) &
                            (col("low") <= col("open")) & 
                            (col("low") <= col("close")), True).otherwise(False)) \
            .withColumn("processed_timestamp", current_timestamp())
        
        logger.info(f"Stock data cleaning completed. Records after cleaning: {df_clean.count()}")
        return df_clean
    
    def clean_crypto_data(self, df):
        """Clean and standardize cryptocurrency data"""
        logger.info("Cleaning cryptocurrency data...")
        
        # Remove invalid records
        df_clean = df.filter(
            col("symbol").isNotNull() &
            col("current_price").isNotNull() &
            (col("current_price") > 0) &
            col("market_cap").isNotNull()
        )
        
        # Standardize symbol format (uppercase)
        df_clean = df_clean.withColumn("symbol", expr("upper(symbol)"))
        
        # Add market cap categories
        df_clean = df_clean \
            .withColumn("market_cap_category",
                       when(col("market_cap") >= 10000000000, "Large Cap")
                       .when(col("market_cap") >= 1000000000, "Mid Cap")
                       .when(col("market_cap") >= 100000000, "Small Cap")
                       .otherwise("Micro Cap")) \
            .withColumn("processed_timestamp", current_timestamp())
        
        logger.info(f"Crypto data cleaning completed. Records after cleaning: {df_clean.count()}")
        return df_clean
    
    def create_asset_dimension(self, stock_df, crypto_df):
        """Create unified asset dimension table"""
        logger.info("Creating asset dimension table...")
        
        # Stock assets
        stock_assets = stock_df.select(
            col("symbol").alias("asset_symbol"),
            lit("Stock").alias("asset_type"),
            lit(None).cast(StringType()).alias("asset_name"),
            lit("USD").alias("base_currency")
        ).distinct()
        
        # Crypto assets
        crypto_assets = crypto_df.select(
            col("symbol").alias("asset_symbol"),
            lit("Cryptocurrency").alias("asset_type"),
            col("name").alias("asset_name"),
            lit("USD").alias("base_currency")
        ).distinct()
        
        # Union and add surrogate key
        assets_dim = stock_assets.union(crypto_assets) \
            .withColumn("asset_id", 
                       row_number().over(Window.orderBy("asset_symbol", "asset_type"))) \
            .withColumn("created_date", current_timestamp()) \
            .withColumn("is_active", lit(True))
        
        logger.info(f"Asset dimension created with {assets_dim.count()} assets")
        return assets_dim
    
    def create_time_dimension(self, df):
        """Create time dimension for temporal analysis"""
        logger.info("Creating time dimension table...")
        
        # Extract unique timestamps
        time_dim = df.select("timestamp").distinct() \
            .withColumn("date_key", expr("date_format(timestamp, 'yyyyMMdd')").cast(IntegerType())) \
            .withColumn("year", expr("year(timestamp)")) \
            .withColumn("quarter", expr("quarter(timestamp)")) \
            .withColumn("month", expr("month(timestamp)")) \
            .withColumn("week", expr("weekofyear(timestamp)")) \
            .withColumn("day", expr("day(timestamp)")) \
            .withColumn("hour", expr("hour(timestamp)")) \
            .withColumn("day_of_week", expr("dayofweek(timestamp)")) \
            .withColumn("day_name", expr("date_format(timestamp, 'EEEE')")) \
            .withColumn("month_name", expr("date_format(timestamp, 'MMMM')")) \
            .withColumn("is_weekend", 
                       when(col("day_of_week").isin([1, 7]), True).otherwise(False)) \
            .withColumn("is_market_hours",
                       when((col("hour") >= 9) & (col("hour") <= 16) & 
                            ~col("is_weekend"), True).otherwise(False))
        
        logger.info(f"Time dimension created with {time_dim.count()} records")
        return time_dim
    
    def calculate_technical_indicators(self, df):
        """Calculate technical indicators for trading analysis"""
        logger.info("Calculating technical indicators...")
        
        # Window specifications
        window_5 = Window.partitionBy("symbol").orderBy("timestamp").rowsBetween(-4, 0)
        window_20 = Window.partitionBy("symbol").orderBy("timestamp").rowsBetween(-19, 0)
        window_50 = Window.partitionBy("symbol").orderBy("timestamp").rowsBetween(-49, 0)
        
        # Moving averages
        df_with_ma = df \
            .withColumn("sma_5", avg(col("close")).over(window_5)) \
            .withColumn("sma_20", avg(col("close")).over(window_20)) \
            .withColumn("sma_50", avg(col("close")).over(window_50))
        
        # Price change and volatility
        df_with_indicators = df_with_ma \
            .withColumn("price_change", 
                       col("close") - lag("close", 1).over(
                           Window.partitionBy("symbol").orderBy("timestamp"))) \
            .withColumn("price_change_pct",
                       (col("close") - lag("close", 1).over(
                           Window.partitionBy("symbol").orderBy("timestamp"))) / 
                       lag("close", 1).over(Window.partitionBy("symbol").orderBy("timestamp")) * 100) \
            .withColumn("volatility_20d", 
                       stddev(col("close")).over(window_20))
        
        # Trading signals
        df_final = df_with_indicators \
            .withColumn("golden_cross_signal",
                       when((col("sma_5") > col("sma_20")) & 
                            (lag("sma_5", 1).over(Window.partitionBy("symbol").orderBy("timestamp")) <= 
                             lag("sma_20", 1).over(Window.partitionBy("symbol").orderBy("timestamp"))), 
                            "BUY").otherwise(None)) \
            .withColumn("death_cross_signal",
                       when((col("sma_5") < col("sma_20")) & 
                            (lag("sma_5", 1).over(Window.partitionBy("symbol").orderBy("timestamp")) >= 
                             lag("sma_20", 1).over(Window.partitionBy("symbol").orderBy("timestamp"))), 
                            "SELL").otherwise(None))
        
        logger.info("Technical indicators calculation completed")
        return df_final
    
    def create_market_fact_table(self, stock_df, crypto_df, assets_dim, time_dim):
        """Create fact table for market data"""
        logger.info("Creating market fact table...")
        
        # Prepare stock facts
        stock_facts = stock_df \
            .join(broadcast(assets_dim.filter(col("asset_type") == "Stock")), 
                  col("symbol") == col("asset_symbol")) \
            .join(broadcast(time_dim), "timestamp") \
            .select(
                col("asset_id"),
                col("date_key"),
                col("timestamp"),
                col("open"),
                col("high"),
                col("low"),
                col("close"),
                col("volume"),
                col("sma_5"),
                col("sma_20"),
                col("sma_50"),
                col("price_change"),
                col("price_change_pct"),
                col("volatility_20d"),
                col("golden_cross_signal"),
                col("death_cross_signal"),
                lit("Stock").alias("fact_type")
            )
        
        # Prepare crypto facts (adapt structure to match stocks)
        crypto_facts = crypto_df \
            .join(broadcast(assets_dim.filter(col("asset_type") == "Cryptocurrency")), 
                  col("symbol") == col("asset_symbol")) \
            .withColumn("timestamp", col("last_updated")) \
            .join(broadcast(time_dim), "timestamp") \
            .select(
                col("asset_id"),
                col("date_key"),
                col("timestamp"),
                col("current_price").alias("close"),
                lit(None).cast(DecimalType(18,4)).alias("open"),
                lit(None).cast(DecimalType(18,4)).alias("high"),
                lit(None).cast(DecimalType(18,4)).alias("low"),
                col("total_volume").cast(IntegerType()).alias("volume"),
                lit(None).cast(DecimalType(18,4)).alias("sma_5"),
                lit(None).cast(DecimalType(18,4)).alias("sma_20"),
                lit(None).cast(DecimalType(18,4)).alias("sma_50"),
                col("price_change_24h").alias("price_change"),
                col("price_change_percentage_24h").alias("price_change_pct"),
                lit(None).cast(DecimalType(18,4)).alias("volatility_20d"),
                lit(None).cast(StringType()).alias("golden_cross_signal"),
                lit(None).cast(StringType()).alias("death_cross_signal"),
                lit("Cryptocurrency").alias("fact_type")
            )
        
        # Union fact tables
        market_facts = stock_facts.union(crypto_facts) \
            .withColumn("fact_id", 
                       row_number().over(Window.orderBy("timestamp", "asset_id"))) \
            .withColumn("created_timestamp", current_timestamp())
        
        logger.info(f"Market fact table created with {market_facts.count()} records")
        return market_facts
    
    def write_data(self, df, output_path, data_format="parquet", mode="overwrite"):
        """Write processed data to S3"""
        logger.info(f"Writing data to {output_path} in {data_format} format...")
        
        try:
            if data_format == "parquet":
                df.coalesce(10).write \
                    .mode(mode) \
                    .option("compression", "snappy") \
                    .parquet(output_path)
            elif data_format == "csv":
                df.coalesce(5).write \
                    .mode(mode) \
                    .option("header", "true") \
                    .csv(output_path)
            else:
                raise ValueError(f"Unsupported output format: {data_format}")
            
            logger.info(f"Successfully wrote data to {output_path}")
            
        except Exception as e:
            logger.error(f"Error writing data to {output_path}: {str(e)}")
            raise

def main():
    """Main ETL execution function"""
    transformer = FinancialDataTransformer()
    
    try:
        # S3 paths (replace with your actual bucket paths)
        base_input_path = "s3a://financial-trading-data-lake/raw"
        base_output_path = "s3a://financial-trading-data-lake/processed"
        
        # Read raw data
        stock_schema = transformer.get_stock_schema()
        crypto_schema = transformer.get_crypto_schema()
        
        stock_df = transformer.read_data(f"{base_input_path}/stocks/", stock_schema)
        crypto_df = transformer.read_data(f"{base_input_path}/crypto/", crypto_schema)
        
        # Clean data
        stock_clean = transformer.clean_stock_data(stock_df)
        crypto_clean = transformer.clean_crypto_data(crypto_df)
        
        # Calculate technical indicators for stocks
        stock_with_indicators = transformer.calculate_technical_indicators(stock_clean)
        
        # Create dimensions
        assets_dim = transformer.create_asset_dimension(stock_clean, crypto_clean)
        time_dim = transformer.create_time_dimension(stock_clean)
        
        # Create fact table
        market_facts = transformer.create_market_fact_table(
            stock_with_indicators, crypto_clean, assets_dim, time_dim
        )
        
        # Write processed data
        transformer.write_data(assets_dim, f"{base_output_path}/dimensions/assets")
        transformer.write_data(time_dim, f"{base_output_path}/dimensions/time")
        transformer.write_data(market_facts, f"{base_output_path}/facts/market_data")
        
        # Write cleaned raw data for audit
        transformer.write_data(stock_with_indicators, f"{base_output_path}/cleaned/stocks")
        transformer.write_data(crypto_clean, f"{base_output_path}/cleaned/crypto")
        
        logger.info("Financial data transformation pipeline completed successfully!")
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {str(e)}")
        raise
    finally:
        transformer.spark.stop()

if __name__ == "__main__":
    main()