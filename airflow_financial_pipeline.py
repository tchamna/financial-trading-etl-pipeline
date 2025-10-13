import logging
import boto3
from datetime import datetime, timedelta
from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.providers.amazon.aws.operators.emr import EmrCreateJobFlowOperator
from airflow.providers.amazon.aws.operators.emr import EmrTerminateJobFlowOperator
from airflow.providers.amazon.aws.operators.emr import EmrAddStepsOperator
from airflow.providers.amazon.aws.sensors.emr import EmrStepSensor
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from airflow.providers.http.sensors.http import HttpSensor
from airflow.operators.email_operator import EmailOperator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default arguments
default_args = {
    "owner": "DataEngineering",
    "start_date": days_ago(1),
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email": ["tchamna@gmail.com"]  # Add your email for notifications
}

# Define the DAG
dag = DAG(
    dag_id="FINANCIAL_TRADING_ETL_PIPELINE",
    default_args=default_args,
    description="Real-time financial market data ETL pipeline",
    schedule_interval=timedelta(hours=1),  # Run hourly during market hours
    catchup=False,
    max_active_runs=1,
    tags=["finance", "trading", "real-time", "analytics"]
)

# EMR Cluster configuration for financial data processing
JOB_FLOW_OVERRIDES = {
    'Name': 'financial-trading-data-processing',
    'ReleaseLabel': 'emr-6.15.0',  # Latest EMR version
    'Instances': {
        'InstanceGroups': [
            {
                'Name': "Master",
                'Market': 'SPOT',  # Cost optimization with spot instances
                'InstanceRole': 'MASTER',
                'InstanceType': 'm5.xlarge',
                'InstanceCount': 1,
            },
            {
                'Name': "Workers",
                'Market': 'SPOT',
                'InstanceRole': 'CORE',
                'InstanceType': 'm5.2xlarge',
                'InstanceCount': 3,  # Increased for better performance
            }
        ],
        'Ec2KeyName': 'your-ec2-key',  # Replace with your EC2 Key
        'KeepJobFlowAliveWhenNoSteps': False,  # Cost optimization
        'TerminationProtected': False,
        'Ec2SubnetId': 'subnet-your-subnet-id',  # Replace with your subnet
    },
    'LogUri': 's3://financial-trading-etl-logs/',
    'BootstrapActions': [
        {
            'Name': 'Install Additional Python Packages',
            'ScriptBootstrapAction': {
                'Path': 's3://financial-trading-etl-scripts/bootstrap/install_packages.sh'
            }
        }
    ],
    'VisibleToAllUsers': True,
    'JobFlowRole': 'EMR_EC2_DefaultRole',
    'ServiceRole': 'EMR_DefaultRole',
    'Applications': [
        {'Name': 'Spark'},
        {'Name': 'Hive'},
        {'Name': 'Kafka'},
        {'Name': 'Zeppelin'}  # For interactive analysis
    ],
    'Configurations': [
        {
            'Classification': 'spark-defaults',
            'Properties': {
                'spark.sql.adaptive.enabled': 'true',
                'spark.sql.adaptive.coalescePartitions.enabled': 'true',
                'spark.dynamicAllocation.enabled': 'true',
                'spark.dynamicAllocation.minExecutors': '1',
                'spark.dynamicAllocation.maxExecutors': '10'
            }
        }
    ]
}

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
    import great_expectations as ge
    
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
    
    # Check if market is open (optional - can add market hours logic)
    market_hours_check = HttpSensor(
        task_id='check_market_hours',
        http_conn_id='market_data_api',
        endpoint='market/status',
        timeout=20,
        poke_interval=60,
        mode='poke'
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
    
    # Create EMR Cluster for processing
    create_emr_cluster = EmrCreateJobFlowOperator(
        task_id='create_emr_cluster',
        job_flow_overrides=JOB_FLOW_OVERRIDES,
        aws_conn_id='aws_default',
    )
    
    # Run data quality tests on EMR
    data_quality_step = EmrAddStepsOperator(
        task_id='run_data_quality_tests',
        job_flow_id=create_emr_cluster.output,
        steps=[
            {
                'Name': 'Data Quality Tests',
                'ActionOnFailure': 'TERMINATE_CLUSTER',
                'HadoopJarStep': {
                    'Jar': 'command-runner.jar',
                    'Args': [
                        'spark-submit',
                        '--deploy-mode', 'cluster',
                        '--class', 'com.trading.DataQualityTests',
                        's3://financial-trading-etl-scripts/jars/data-quality-tests.jar'
                    ],
                },
            }
        ],
        aws_conn_id='aws_default',
    )
    
    # Wait for data quality tests
    wait_for_quality_tests = EmrStepSensor(
        task_id='wait_for_data_quality_tests',
        job_flow_id=create_emr_cluster.output,
        step_id=data_quality_step.output,
        aws_conn_id='aws_default',
    )
    
    # Run Spark transformation job
    transformation_step = EmrAddStepsOperator(
        task_id='run_spark_transformation',
        job_flow_id=create_emr_cluster.output,
        steps=[
            {
                'Name': 'Financial Data Transformation',
                'ActionOnFailure': 'CONTINUE',
                'HadoopJarStep': {
                    'Jar': 'command-runner.jar',
                    'Args': [
                        'spark-submit',
                        '--master', 'yarn',
                        '--deploy-mode', 'cluster',
                        '--num-executors', '6',
                        '--executor-memory', '4g',
                        '--executor-cores', '2',
                        '--conf', 'spark.sql.shuffle.partitions=200',
                        's3://financial-trading-etl-scripts/spark/financial_data_transformation.py'
                    ],
                },
            }
        ],
        aws_conn_id='aws_default',
    )
    
    # Wait for transformation to complete
    wait_for_transformation = EmrStepSensor(
        task_id='wait_for_transformation',
        job_flow_id=create_emr_cluster.output,
        step_id=transformation_step.output,
        aws_conn_id='aws_default',
    )
    
    # Calculate technical indicators (RSI, MACD, Bollinger Bands)
    technical_indicators_step = EmrAddStepsOperator(
        task_id='calculate_technical_indicators',
        job_flow_id=create_emr_cluster.output,
        steps=[
            {
                'Name': 'Technical Indicators Calculation',
                'ActionOnFailure': 'CONTINUE',
                'HadoopJarStep': {
                    'Jar': 'command-runner.jar',
                    'Args': [
                        'spark-submit',
                        '--master', 'yarn',
                        '--deploy-mode', 'cluster',
                        's3://financial-trading-etl-scripts/spark/technical_indicators.py'
                    ],
                },
            }
        ],
        aws_conn_id='aws_default',
    )
    
    # Wait for technical indicators calculation
    wait_for_indicators = EmrStepSensor(
        task_id='wait_for_technical_indicators',
        job_flow_id=create_emr_cluster.output,
        step_id=technical_indicators_step.output,
        aws_conn_id='aws_default',
    )
    
    # Terminate EMR Cluster (cost optimization)
    terminate_emr_cluster = EmrTerminateJobFlowOperator(
        task_id='terminate_emr_cluster',
        job_flow_id=create_emr_cluster.output,
        aws_conn_id='aws_default',
    )
    
    # Fetch SQL from S3 for Snowflake loading
    fetch_sql_task = PythonOperator(
        task_id='fetch_sql_from_s3',
        python_callable=get_sql_from_s3,
        provide_context=True
    )
    
    # Load processed data into Snowflake
    snowflake_load = SnowflakeOperator(
        task_id="load_data_to_snowflake",
        sql="{{ ti.xcom_pull(task_ids='fetch_sql_from_s3', key='sql_content') }}",
        snowflake_conn_id="snowflake_financial_db",
        warehouse="FINANCIAL_WH",
        database="FINANCIAL_DB",
        schema="TRADING_SCHEMA"
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

# Task dependencies - Complex workflow with parallel processing
market_hours_check >> fetch_data_task >> validate_quality_task

# EMR cluster processing branch
validate_quality_task >> create_emr_cluster
create_emr_cluster >> data_quality_step >> wait_for_quality_tests
wait_for_quality_tests >> [transformation_step, technical_indicators_step]
transformation_step >> wait_for_transformation
technical_indicators_step >> wait_for_indicators
[wait_for_transformation, wait_for_indicators] >> terminate_emr_cluster

# Snowflake loading branch  
terminate_emr_cluster >> fetch_sql_task >> snowflake_load

# Final tasks
snowflake_load >> update_catalog >> notify_completion
snowflake_load >> notify_failure