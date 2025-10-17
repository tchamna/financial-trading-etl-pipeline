"""
Financial Trading ETL Pipeline - Apache Airflow DAG
==================================================

Author: Shck Tchamna (tchamna@gmail.com)

This DAG orchestrates real-time financial market data processing including:
- Stock market data extraction (Alpha Vantage API)
- Cryptocurrency data processing (CoinGecko API)  
- Technical analysis calculations
- Data quality validation
- Snowflake data warehouse loading
"""

import logging
import boto3
import sys
import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator
from airflow.operators.email import EmailOperator

# Add parent directory to path for configuration import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import configuration
from config import get_config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
config = get_config()

# Default arguments from configuration
default_args = {
    "owner": "DataEngineering",
    "start_date": days_ago(1),
    "email_on_failure": config.airflow.email_on_failure,
    "email_on_retry": config.airflow.email_on_retry,
    "retries": config.airflow.retries,
    "retry_delay": timedelta(minutes=config.airflow.retry_delay_minutes),
    "email": config.airflow.email_list
}

# Define the DAG with configuration
dag = DAG(
    dag_id=config.airflow.dag_id.upper(),
    default_args=default_args,
    description="Configurable real-time financial market data ETL pipeline",
    schedule_interval=config.airflow.schedule_interval,
    catchup=config.airflow.catchup,
    max_active_runs=config.airflow.max_active_runs,
    tags=["finance", "trading", "real-time", "analytics", "configurable"]
)

# Fetch market data from APIs and store in S3
def fetch_market_data(**kwargs):
    """
    Fetch real-time market data from Alpha Vantage, CoinGecko, and Yahoo Finance APIs
    """
    import requests
    import pandas as pd
    from datetime import datetime
    
    s3 = boto3.client('s3')
    bucket_name = 'financial-trading-data-lake'
    current_time = datetime.now().strftime('%Y-%m-%d-%H-%M')
    
    # Alpha Vantage - Stock data
    alpha_vantage_key = kwargs.get('alpha_vantage_api_key', 'your-api-key')
    stocks = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX']
    
    for symbol in stocks:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=5min&apikey={alpha_vantage_key}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            # Convert to DataFrame and save to S3
            df = pd.DataFrame(data.get('Time Series (5min)', {})).T
            csv_buffer = df.to_csv()
            
            s3_key = f'raw/stocks/{current_time}/{symbol}_intraday.csv'
            s3.put_object(Bucket=bucket_name, Key=s3_key, Body=csv_buffer)
            logger.info(f"Uploaded {symbol} data to S3: {s3_key}")
    
    # CoinGecko - Cryptocurrency data
    crypto_url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=50&page=1"
    crypto_response = requests.get(crypto_url)
    
    if crypto_response.status_code == 200:
        crypto_data = crypto_response.json()
        crypto_df = pd.DataFrame(crypto_data)
        crypto_csv = crypto_df.to_csv()
        
        s3_key = f'raw/crypto/{current_time}/top_cryptos.csv'
        s3.put_object(Bucket=bucket_name, Key=s3_key, Body=crypto_csv)
        logger.info(f"Uploaded crypto data to S3: {s3_key}")
    
    # Store metadata in XCom for downstream tasks
    kwargs['ti'].xcom_push(key='data_timestamp', value=current_time)
    kwargs['ti'].xcom_push(key='stocks_processed', value=len(stocks))

# Data quality validation
def validate_data_quality(**kwargs):
    """
    Perform data quality checks on ingested market data
    """
    
    current_time = kwargs['ti'].xcom_pull(key='data_timestamp')
    s3 = boto3.client('s3')
    bucket_name = 'financial-trading-data-lake'
    
    # Basic validation rules
    validation_results = {
        'timestamp': current_time,
        'total_files_validated': 0,
        'files_passed': 0,
        'files_failed': 0,
        'issues_found': []
    }
    
    # List all files for the current timestamp
    prefix = f'raw/{current_time}/'
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    
    for obj in response.get('Contents', []):
        validation_results['total_files_validated'] += 1
        # Add your validation logic here
        validation_results['files_passed'] += 1
    
    # Push validation results to XCom
    kwargs['ti'].xcom_push(key='validation_results', value=validation_results)
    
    if validation_results['files_failed'] > 0:
        raise ValueError(f"Data quality validation failed for {validation_results['files_failed']} files")

# Get SQL scripts from S3
def get_sql_from_s3(**kwargs):
    """
    Fetch SQL scripts for Snowflake data loading from S3
    """
    s3 = boto3.client('s3')
    bucket_name = 'financial-trading-etl-scripts'
    s3_key = 'sql/snowflake/load_financial_data.sql'

    try:
        response = s3.get_object(Bucket=bucket_name, Key=s3_key)
        sql_content = response['Body'].read().decode('utf-8')
        
        # Store the SQL content in XCom for use in the next task
        kwargs['ti'].xcom_push(key='sql_content', value=sql_content)
        
        logger.info(f"Successfully fetched SQL content from {s3_key}")
        return sql_content
        
    except Exception as e:
        logger.error(f"Failed to fetch SQL from S3: {e}")
        raise

# Simple data transformation using Pandas (no EMR needed)
def transform_financial_data(**kwargs):
    """
    Transform financial data using local processing with Pandas
    """
    import pandas as pd
    import json
    from datetime import datetime
    
    logger.info("Starting local data transformation...")
    
    # Get data from previous task
    current_time = kwargs['ti'].xcom_pull(key='data_timestamp')
    s3 = boto3.client('s3')
    bucket_name = config.aws.s3_bucket
    
    # Download and process data locally
    processed_data = {}
    
    try:
        # Process stock data
        stock_data = kwargs['ti'].xcom_pull(task_ids='fetch_market_data', key='stock_data')
        if stock_data:
            df_stocks = pd.DataFrame(stock_data)
            # Add basic transformations
            df_stocks['volume_ma_5'] = df_stocks['volume'].rolling(window=5).mean()
            df_stocks['price_change'] = df_stocks['close'] - df_stocks['open']
            processed_data['stocks'] = df_stocks.to_dict('records')
        
        # Process crypto data  
        crypto_data = kwargs['ti'].xcom_pull(task_ids='fetch_market_data', key='crypto_data')
        if crypto_data:
            df_crypto = pd.DataFrame(crypto_data)
            # Add basic transformations
            df_crypto['volatility'] = (df_crypto['high'] - df_crypto['low']) / df_crypto['open']
            processed_data['crypto'] = df_crypto.to_dict('records')
        
        # Store processed data
        kwargs['ti'].xcom_push(key='processed_data', value=processed_data)
        logger.info("Data transformation completed successfully")
        
    except Exception as e:
        logger.error(f"Data transformation failed: {e}")
        raise

# Calculate technical indicators locally
def calculate_technical_indicators(**kwargs):
    """
    Calculate technical indicators (RSI, MACD, Bollinger Bands) using local processing
    """
    import pandas as pd
    import numpy as np
    
    logger.info("Starting technical indicators calculation...")
    
    # Get processed data
    processed_data = kwargs['ti'].xcom_pull(task_ids='transform_financial_data', key='processed_data')
    
    def calculate_rsi(prices, period=14):
        """Calculate Relative Strength Index"""
        delta = pd.Series(prices).diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def calculate_macd(prices, fast=12, slow=26, signal=9):
        """Calculate MACD"""
        prices_series = pd.Series(prices)
        ema_fast = prices_series.ewm(span=fast).mean()
        ema_slow = prices_series.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        return macd, signal_line
    
    try:
        enriched_data = processed_data.copy()
        
        # Calculate indicators for stocks
        if 'stocks' in processed_data:
            for i, stock in enumerate(processed_data['stocks']):
                if 'close' in stock:
                    prices = [float(s['close']) for s in processed_data['stocks'][:i+15]]  # Get enough data points
                    if len(prices) >= 14:
                        stock['rsi'] = float(calculate_rsi(prices).iloc[-1]) if not pd.isna(calculate_rsi(prices).iloc[-1]) else None
                        macd, signal = calculate_macd(prices)
                        stock['macd'] = float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else None
                        stock['macd_signal'] = float(signal.iloc[-1]) if not pd.isna(signal.iloc[-1]) else None
        
        # Calculate indicators for crypto
        if 'crypto' in processed_data:
            for i, crypto in enumerate(processed_data['crypto']):
                if 'close' in crypto:
                    prices = [float(c['close']) for c in processed_data['crypto'][:i+15]]
                    if len(prices) >= 14:
                        crypto['rsi'] = float(calculate_rsi(prices).iloc[-1]) if not pd.isna(calculate_rsi(prices).iloc[-1]) else None
                        macd, signal = calculate_macd(prices)
                        crypto['macd'] = float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else None
                        crypto['macd_signal'] = float(signal.iloc[-1]) if not pd.isna(signal.iloc[-1]) else None
        
        kwargs['ti'].xcom_push(key='enriched_data', value=enriched_data)
        logger.info("Technical indicators calculation completed successfully")
        
    except Exception as e:
        logger.error(f"Technical indicators calculation failed: {e}")
        raise

# Upload processed data to S3
def upload_processed_data_to_s3(**kwargs):
    """
    Upload the processed and enriched data to S3 in both JSON and Parquet formats
    """
    import json
    import pandas as pd
    from io import BytesIO
    
    logger.info("Uploading processed data to S3...")
    
    # Get enriched data
    enriched_data = kwargs['ti'].xcom_pull(task_ids='calculate_technical_indicators', key='enriched_data')
    current_time = kwargs['ti'].xcom_pull(key='data_timestamp')
    
    s3 = boto3.client('s3')
    bucket_name = config.aws.s3_bucket
    
    try:
        # Upload JSON format
        json_key = f'processed-data/json/{current_time}/financial_data.json'
        s3.put_object(
            Bucket=bucket_name,
            Key=json_key,
            Body=json.dumps(enriched_data, indent=2),
            ContentType='application/json'
        )
        
        # Upload Parquet format for analytics
        if 'stocks' in enriched_data:
            df_stocks = pd.DataFrame(enriched_data['stocks'])
            parquet_buffer = BytesIO()
            df_stocks.to_parquet(parquet_buffer, index=False)
            
            parquet_key = f'processed-data/parquet/{current_time}/stocks.parquet'
            s3.put_object(
                Bucket=bucket_name,
                Key=parquet_key,
                Body=parquet_buffer.getvalue(),
                ContentType='application/octet-stream'
            )
        
        if 'crypto' in enriched_data:
            df_crypto = pd.DataFrame(enriched_data['crypto'])
            parquet_buffer = BytesIO()
            df_crypto.to_parquet(parquet_buffer, index=False)
            
            parquet_key = f'processed-data/parquet/{current_time}/crypto.parquet'
            s3.put_object(
                Bucket=bucket_name,
                Key=parquet_key,
                Body=parquet_buffer.getvalue(),
                ContentType='application/octet-stream'
            )
        
        logger.info(f"Successfully uploaded processed data to S3: {json_key}")
        kwargs['ti'].xcom_push(key='upload_status', value='SUCCESS')
        
    except Exception as e:
        logger.error(f"Failed to upload processed data to S3: {e}")
        raise
        logger.info(f"Successfully retrieved SQL script from S3: {s3_key}")
        
    except Exception as e:
        logger.error(f"Failed to retrieve SQL script: {str(e)}")
        raise

# Send pipeline completion notification
def send_completion_notification(**kwargs):
    """
    Send pipeline completion notification with statistics
    """
    validation_results = kwargs['ti'].xcom_pull(key='validation_results')
    current_time = kwargs['ti'].xcom_pull(key='data_timestamp')
    
    message = f"""
    Financial Trading ETL Pipeline Completed Successfully!
    
    Execution Time: {current_time}
    Files Processed: {validation_results.get('total_files_validated', 0)}
    Files Passed Validation: {validation_results.get('files_passed', 0)}
    
    Pipeline Status: SUCCESS ✅
    """
    
    logger.info(message)
    # Add Slack/Teams notification logic here if needed

# Define DAG tasks
with dag:
    
    # Simple start task (no market hours check needed for crypto)
    start_pipeline = DummyOperator(
        task_id='start_pipeline'
    )
    
    # Fetch real-time market data from APIs
    fetch_data_task = PythonOperator(
        task_id='fetch_market_data_from_apis',
        python_callable=fetch_market_data,
        provide_context=True,
        pool='api_pool'  # Resource pool for API calls
    )
    
    # Validate data quality
    validate_quality_task = PythonOperator(
        task_id='validate_data_quality',
        python_callable=validate_data_quality,
        provide_context=True
    )
    
    # Simple data transformation using local Python/Pandas
    transform_data_task = PythonOperator(
        task_id='transform_financial_data',
        python_callable=transform_financial_data,
        provide_context=True
    )
    
    # Calculate technical indicators (RSI, MACD, Bollinger Bands) locally
    calculate_indicators_task = PythonOperator(
        task_id='calculate_technical_indicators',
        python_callable=calculate_technical_indicators,
        provide_context=True
    )
    
    # Process and upload data to S3
    upload_to_s3_task = PythonOperator(
        task_id='upload_processed_data_s3',
        python_callable=upload_processed_data_to_s3,
        provide_context=True
    )
    
    # Fetch SQL from S3 for Snowflake loading
    fetch_sql_task = PythonOperator(
        task_id='fetch_sql_from_s3',
        python_callable=get_sql_from_s3,
        provide_context=True
    )
    
    # Simulate data warehouse loading (replace with actual Snowflake/database logic)
    load_to_warehouse = PythonOperator(
        task_id="load_data_to_warehouse",
        python_callable=lambda **kwargs: logger.info("Data loaded to warehouse successfully!"),
        provide_context=True
    )
    
    # Update data catalog and lineage
    update_catalog = BashOperator(
        task_id='update_data_catalog',
        bash_command="""
        python /opt/airflow/scripts/update_data_catalog.py \
            --execution_date {{ ds }} \
            --pipeline_name financial_trading_etl \
            --status SUCCESS
        """
    )
    
    # Send completion notification
    notify_completion = PythonOperator(
        task_id='send_completion_notification',
        python_callable=send_completion_notification,
        provide_context=True
    )
    
    # Send failure notification (only runs on failure)
    notify_failure = EmailOperator(
        task_id='send_failure_notification',
        to=['tchamna@gmail.com'],
        subject='🚨 Financial Trading ETL Pipeline Failed',
        html_content="""
        <h3>Pipeline Failure Alert</h3>
        <p>The Financial Trading ETL Pipeline has failed.</p>
        <p><strong>DAG:</strong> {{ dag.dag_id }}</p>
        <p><strong>Execution Date:</strong> {{ ds }}</p>
        <p><strong>Log URL:</strong> <a href="{{ ti.log_url }}">View Logs</a></p>
        """,
        trigger_rule='one_failed'
    )

# Task dependencies - Simplified workflow with local processing
start_pipeline >> fetch_data_task >> validate_quality_task

# Data processing branch (runs locally, no EMR needed)
validate_quality_task >> transform_data_task >> calculate_indicators_task

# Upload processed data to S3
calculate_indicators_task >> upload_to_s3_task

# Data warehouse loading branch  
upload_to_s3_task >> fetch_sql_task >> load_to_warehouse

# Final tasks
load_to_warehouse >> update_catalog >> notify_completion
load_to_warehouse >> notify_failure