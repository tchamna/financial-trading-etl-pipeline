# Testing and Deployment Guide

## 🧪 Testing Strategy

### Prerequisites
Before testing, ensure you have:
- Python 3.9+ installed
- Docker Desktop running
- AWS CLI configured
- Git repository cloned

### 1. Local Development Setup

First, let's set up your development environment:

```bash
# Navigate to project directory
cd c:\Users\tcham\OneDrive\Documents\Workspace_Codes\PORTFOLIO\etl-end-to-end\financial-trading-etl-pipeline

# Create Python virtual environment
python -m venv venv
venv\Scripts\activate  # Windows PowerShell

# Install dependencies
pip install -r requirements.txt

# Copy environment template
copy .env.example .env
# Edit .env file with your actual credentials
```

### 2. Unit Testing

Run the comprehensive test suite:

```bash
# Install test dependencies
pip install pytest pytest-spark pytest-cov great-expectations

# Run all tests with coverage
pytest tests/ -v --cov=spark --cov=airflow --cov-report=html

# Run specific test categories
pytest tests/test_financial_transformation.py -v  # Spark tests
pytest tests/test_airflow_dag.py -v              # Airflow tests
pytest tests/test_data_quality.py -v             # Data quality tests

# Run performance tests
pytest tests/test_performance.py -v --benchmark-only
```

### 3. Integration Testing with Docker

Test the complete pipeline locally:

```bash
# Start local infrastructure
docker-compose up -d

# Wait for services to be healthy (2-3 minutes)
docker-compose ps

# Check Airflow is running
# Open browser: http://localhost:8080
# Username: admin, Password: admin

# Run integration tests
pytest tests/test_integration.py -v --docker

# Check logs
docker-compose logs airflow-webserver
docker-compose logs airflow-scheduler
```

### 4. Data Quality Testing

```bash
# Run data quality validation
python scripts/validate_data_quality.py --config tests/data_quality_config.yaml

# Run schema validation
python scripts/validate_schemas.py --input-path data/sample/

# Test API connectivity
python scripts/test_api_connections.py
```

## 🚀 Deployment Guide

### Phase 1: AWS Infrastructure Setup

#### 1.1 Configure AWS Credentials
```bash
# Configure AWS CLI
aws configure
# Enter your: Access Key ID, Secret Access Key, Region (us-east-1), Output format (json)

# Verify configuration
aws sts get-caller-identity
```

#### 1.2 Create S3 Buckets
```bash
# Create required S3 buckets
aws s3 mb s3://financial-trading-data-lake-raw --region us-east-1
aws s3 mb s3://financial-trading-data-lake-processed --region us-east-1  
aws s3 mb s3://financial-trading-etl-logs --region us-east-1
aws s3 mb s3://financial-trading-etl-scripts --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning --bucket financial-trading-data-lake-raw --versioning-configuration Status=Enabled
aws s3api put-bucket-versioning --bucket financial-trading-data-lake-processed --versioning-configuration Status=Enabled

# Set up lifecycle policies
aws s3api put-bucket-lifecycle-configuration --bucket financial-trading-data-lake-raw --lifecycle-configuration file://config/s3-lifecycle-raw.json
```

#### 1.3 Upload Scripts to S3
```bash
# Upload Spark scripts
aws s3 cp spark/ s3://financial-trading-etl-scripts/spark/ --recursive

# Upload SQL scripts  
aws s3 cp sql/ s3://financial-trading-etl-scripts/sql/ --recursive

# Upload test data
aws s3 cp tests/data/ s3://financial-trading-data-lake-raw/test/ --recursive
```

### Phase 2: Snowflake Setup

#### 2.1 Create Snowflake Resources
```sql
-- Connect to Snowflake and run these commands:

-- Create warehouse
CREATE WAREHOUSE IF NOT EXISTS FINANCIAL_WH 
WITH WAREHOUSE_SIZE = 'SMALL' AUTO_SUSPEND = 300 AUTO_RESUME = TRUE;

-- Create database and schemas
USE WAREHOUSE FINANCIAL_WH;
CREATE DATABASE IF NOT EXISTS FINANCIAL_DB;
CREATE SCHEMA IF NOT EXISTS FINANCIAL_DB.STAGING;
CREATE SCHEMA IF NOT EXISTS FINANCIAL_DB.CORE;
CREATE SCHEMA IF NOT EXISTS FINANCIAL_DB.MARTS;

-- Run the full schema creation
-- Execute the contents of sql/snowflake_financial_schema.sql
```

#### 2.2 Create Snowflake External Stage
```sql
-- Create external stage for S3 integration
CREATE OR REPLACE STAGE FINANCIAL_DB.CORE.S3_STAGE
URL = 's3://financial-trading-data-lake-processed/'
CREDENTIALS = (AWS_KEY_ID = 'your-access-key' AWS_SECRET_KEY = 'your-secret-key')
FILE_FORMAT = (TYPE = 'PARQUET');
```

### Phase 3: Airflow Deployment

#### 3.1 Production Airflow Setup
```bash
# For AWS managed Airflow (MWAA)
# Create MWAA environment through AWS Console or CLI

# For self-managed EC2 deployment:
# Launch EC2 instance (t3.large recommended)
ssh -i your-key.pem ec2-user@your-ec2-ip

# Install Docker on EC2
sudo yum update -y
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone repository and deploy
git clone https://github.com/yourusername/financial-trading-etl-pipeline.git
cd financial-trading-etl-pipeline
docker-compose -f docker-compose.prod.yml up -d
```

#### 3.2 Configure Airflow Connections
```python
# In Airflow UI (Admin -> Connections), create:

# AWS Connection
Connection Id: aws_default
Connection Type: Amazon Web Services
Extra: {
  "aws_access_key_id": "your-key",
  "aws_secret_access_key": "your-secret",
  "region_name": "us-east-1"
}

# Snowflake Connection  
Connection Id: snowflake_financial_db
Connection Type: Snowflake
Host: your-account.snowflakecomputing.com
Schema: CORE
Login: your-username
Password: your-password
Extra: {
  "account": "your-account",
  "warehouse": "FINANCIAL_WH",
  "database": "FINANCIAL_DB"
}
```

### Phase 4: Testing Deployment

#### 4.1 End-to-End Pipeline Test
```bash
# Trigger the DAG manually in Airflow UI
# Or via CLI:
docker exec -it airflow-webserver airflow dags trigger FINANCIAL_TRADING_ETL_PIPELINE

# Monitor execution
docker exec -it airflow-webserver airflow dags state FINANCIAL_TRADING_ETL_PIPELINE 2024-10-13

# Check logs
docker exec -it airflow-webserver airflow tasks log FINANCIAL_TRADING_ETL_PIPELINE fetch_market_data_from_apis 2024-10-13
```

#### 4.2 Data Validation
```bash
# Validate data in Snowflake
snowsql -c your-connection -q "SELECT COUNT(*) FROM FINANCIAL_DB.CORE.FACT_MARKET_DATA;"

# Run data quality checks
python scripts/validate_production_data.py --environment production
```

## 🔧 Production Configuration

### Environment-Specific Settings

#### Development (.env.dev)
```bash
# Smaller resources for development
EMR_CORE_INSTANCE_COUNT=1
SPARK_EXECUTOR_MEMORY=2g
DEBUG_MODE=true
LOG_LEVEL=DEBUG
```

#### Production (.env.prod)  
```bash
# Production optimized settings
EMR_CORE_INSTANCE_COUNT=3
SPARK_EXECUTOR_MEMORY=4g
DEBUG_MODE=false
LOG_LEVEL=INFO
ENABLE_MONITORING=true
```

### Monitoring Setup

#### 4.1 CloudWatch Integration
```bash
# Create CloudWatch log groups
aws logs create-log-group --log-group-name /financial-trading-etl/airflow
aws logs create-log-group --log-group-name /financial-trading-etl/spark
aws logs create-log-group --log-group-name /financial-trading-etl/application

# Set up CloudWatch alarms
aws cloudwatch put-metric-alarm \
  --alarm-name "Financial-ETL-Pipeline-Failures" \
  --alarm-description "Alert on pipeline failures" \
  --metric-name TaskFailedCount \
  --namespace Custom/FinancialETL \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold
```

#### 4.2 Prometheus Metrics
```bash
# Deploy monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Access dashboards:
# Grafana: http://your-server:3000 (admin/admin)
# Prometheus: http://your-server:9090
```

## 🚦 CI/CD Pipeline

### GitHub Actions Workflow
Create `.github/workflows/ci-cd.yml`:

```yaml
name: Financial Trading ETL CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
        
    - name: Run tests
      run: |
        pytest tests/ --cov=./ --cov-report=xml
        
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1
        
    - name: Deploy to S3
      run: |
        aws s3 sync spark/ s3://financial-trading-etl-scripts/spark/
        aws s3 sync sql/ s3://financial-trading-etl-scripts/sql/
```

## 🔍 Troubleshooting

### Common Issues and Solutions

#### 1. Spark Job Failures
```bash
# Check EMR cluster logs
aws emr describe-cluster --cluster-id j-xxxxxxxxxxxxx
aws s3 ls s3://financial-trading-etl-logs/j-xxxxxxxxxxxxx/ --recursive

# Debug Spark applications
# SSH to EMR master node and check:
yarn logs -applicationId application_xxxxxxxxxxxxx_xxxx
```

#### 2. API Rate Limits
```bash
# Monitor API usage in CloudWatch
# Implement exponential backoff in API calls
# Use multiple API keys with rotation
```

#### 3. Data Quality Issues
```bash
# Run data profiling
python scripts/profile_data.py --input-path s3://financial-trading-data-lake-raw/

# Check for schema drift
python scripts/check_schema_evolution.py
```

## 📊 Performance Optimization

### Spark Tuning
```python
# Optimal Spark configuration for financial data
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true") 
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
spark.conf.set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
```

### Cost Optimization
```bash
# Use spot instances (60-70% cost savings)
# Enable auto-termination for EMR clusters
# Implement S3 lifecycle policies
# Use compression (Snappy for Parquet)
```

## 🎯 Success Metrics

Monitor these KPIs to ensure successful deployment:

- **Pipeline Success Rate**: >99%
- **End-to-End Latency**: <2 minutes
- **Data Quality Score**: >95%
- **Cost per GB Processed**: <$0.10
- **API Success Rate**: >99.5%
- **Uptime**: >99.9%

## 📞 Support and Maintenance

### Regular Maintenance Tasks
- Weekly: Review pipeline performance metrics
- Monthly: Update dependencies and security patches  
- Quarterly: Review and optimize costs
- Annually: Architecture review and capacity planning

This comprehensive guide ensures your financial trading ETL pipeline is production-ready and maintainable! 🚀