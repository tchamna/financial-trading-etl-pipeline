# AWS S3 Data Lake Integration

## Overview
The Financial Trading ETL Pipeline now includes comprehensive AWS S3 integration for cloud-native data storage and processing. This enables scalable data lake architecture with proper partitioning, compression, and integration with other AWS services.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Data Sources  │    │   Local Storage  │    │    AWS S3 Data Lake │
│                 │    │                  │    │                     │
│ • Alpha Vantage │───▶│ • PostgreSQL DB  │───▶│ • Raw Data Layer    │
│ • CoinGecko API │    │ • Real-time data │    │ • Processed Layer   │
│ • Yahoo Finance │    │ • Local backup   │    │ • Analytics Layer   │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
                                                            │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┘
│  Analytics      │    │   Processing     │    │
│                 │    │                  │    │
│ • AWS Athena    │◀───│ • AWS EMR        │◀───┘
│ • Snowflake     │    │ • Apache Spark   │
│ • Tableau       │    │ • AWS Glue       │
└─────────────────┘    └──────────────────┘
```

## S3 Bucket Structure

```
financial-trading-data-lake/
├── raw/
│   ├── stocks/
│   │   └── year=2025/month=10/day=13/hour=14/
│   │       └── stock_data_20251013_143022.json.gz
│   └── crypto/
│       └── year=2025/month=10/day=13/hour=14/
│           └── crypto_data_20251013_143022.json.gz
├── processed/
│   ├── stocks/
│   │   ├── json/
│   │   │   └── year=2025/month=10/day=13/hour=14/
│   │   │       └── stock_data_20251013_143022.json.gz
│   │   └── parquet/
│   │       └── stock_data.parquet
│   ├── crypto/
│   │   ├── json/
│   │   └── parquet/
│   ├── technical_analysis/
│   │   └── stocks/year=2025/month=10/day=13/
│   └── portfolios/
│       └── tech_growth/year=2025/month=10/day=13/
└── analytics/
    ├── aggregations/
    ├── ml_features/
    └── reports/
```

## Features

### 🔄 **Automated Data Upload**
- Dual storage: PostgreSQL (real-time queries) + S3 (analytics)
- Automatic compression with gzip for cost optimization
- Partitioned by date and asset type for query performance
- Multiple formats: JSON (flexibility) + Parquet (performance)

### 📊 **Data Lake Architecture**
- **Raw Layer**: Unprocessed data from APIs
- **Processed Layer**: Cleaned and transformed data
- **Analytics Layer**: Aggregated data for BI tools

### ⚡ **Performance Optimizations**
- S3 Intelligent Tiering for cost optimization
- Lifecycle policies (Standard → IA → Glacier)
- Columnar Parquet format for analytics workloads
- Proper partitioning for query pruning

### 🔧 **Integration Ready**
- **AWS EMR**: For Spark processing at scale
- **AWS Athena**: Serverless SQL queries
- **AWS Glue**: Data catalog and ETL jobs
- **Snowflake**: Direct S3 integration
- **Tableau/Power BI**: BI tool connectivity

## Setup Instructions

### 1. AWS Account Setup
```bash
# Create AWS account and IAM user
# Attach policies: S3FullAccess, EMRFullAccess
```

### 2. Environment Configuration
```bash
# Copy and update environment file
cp .env.example .env

# Add your AWS credentials
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key_here
AWS_DEFAULT_REGION=us-east-1
AWS_S3_BUCKET_NAME=financial-trading-data-lake
```

### 3. Install Dependencies
```bash
# Install AWS libraries
pip install boto3 botocore s3fs

# Or install all requirements
pip install -r requirements.txt
```

### 4. Test S3 Integration
```bash
# Run S3 integration tests
make test-s3

# Or run directly
python scripts/test_s3_integration.py
```

## Usage Examples

### Manual Data Upload
```python
from scripts.s3_data_uploader import create_s3_uploader_from_env

# Initialize uploader
uploader = create_s3_uploader_from_env()

# Upload stock data
stock_data = [{"symbol": "AAPL", "price": 245.40, ...}]
s3_path = uploader.upload_stock_data(stock_data)
print(f"Uploaded to: {s3_path}")

# Upload as Parquet for analytics
import pandas as pd
df = pd.DataFrame(stock_data)
parquet_path = uploader.upload_parquet_data(df, "processed/stocks/parquet/aapl_data")
```

### Automated Pipeline
```bash
# Extract data to both PostgreSQL and S3
make extract

# The pipeline automatically:
# 1. Extracts live data from APIs
# 2. Stores in PostgreSQL for real-time access
# 3. Uploads to S3 for analytics and backup
```

### Query S3 Data with Athena
```sql
-- Create external table in Athena
CREATE EXTERNAL TABLE financial_stocks (
  symbol string,
  timestamp string,
  close_price double,
  volume bigint
)
PARTITIONED BY (
  year string,
  month string,
  day string
)
STORED AS JSON
LOCATION 's3://financial-trading-data-lake/processed/stocks/json/'

-- Query the data
SELECT symbol, AVG(close_price) as avg_price
FROM financial_stocks
WHERE year = '2025' AND month = '10'
GROUP BY symbol
ORDER BY avg_price DESC;
```

## Cost Optimization

### Lifecycle Policies
- **Standard Storage**: First 30 days (frequent access)
- **Infrequent Access**: 30-90 days (occasional queries)
- **Glacier**: 90+ days (archive/compliance)

### Compression Benefits
- **Raw JSON**: ~50% size reduction with gzip
- **Parquet**: ~80% size reduction vs uncompressed JSON
- **Estimated monthly cost**: $5-20 for typical workloads

## Monitoring & Metrics

### Storage Metrics
```python
# Get storage statistics
metrics = uploader.get_storage_metrics()
print(f"Total objects: {metrics['total_objects']}")
print(f"Total size: {metrics['total_size_mb']:.2f} MB")
```

### CloudWatch Integration
- S3 request metrics
- Storage class analysis
- Data transfer monitoring
- Cost allocation tags

## Integration with Other Services

### Snowflake Integration
```sql
-- Create S3 stage in Snowflake
CREATE STAGE financial_s3_stage
URL = 's3://financial-trading-data-lake/processed/'
CREDENTIALS = (AWS_KEY_ID = 'your_key' AWS_SECRET_KEY = 'your_secret');

-- Load data from S3
COPY INTO financial_stocks
FROM @financial_s3_stage/stocks/
FILE_FORMAT = (TYPE = JSON);
```

### EMR Spark Processing
```python
# PySpark on EMR
spark.read.json("s3://financial-trading-data-lake/raw/stocks/") \
     .filter(col("volume") > 1000000) \
     .groupBy("symbol") \
     .agg(avg("close_price").alias("avg_price")) \
     .write.parquet("s3://financial-trading-data-lake/processed/aggregations/")
```

## Security Best Practices

### IAM Policies
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::financial-trading-data-lake/*"
    }
  ]
}
```

### Encryption
- S3 Server-Side Encryption (SSE-S3)
- KMS encryption for sensitive data
- VPC endpoints for private access

## Troubleshooting

### Common Issues

**Authentication Error**
```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify environment variables
echo $AWS_ACCESS_KEY_ID
```

**Bucket Access Denied**
```bash
# Check bucket permissions
aws s3 ls s3://your-bucket-name

# Test bucket creation
aws s3 mb s3://test-bucket-unique-name
```

**Upload Failures**
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Tuning
- Use multipart uploads for large files
- Enable transfer acceleration for global access
- Use CloudFront for data distribution
- Implement retry logic with exponential backoff

## Next Steps

1. **Set up AWS EMR cluster** for Spark processing
2. **Configure Snowflake** S3 integration
3. **Create Athena tables** for SQL analytics
4. **Set up Glue Data Catalog** for metadata management
5. **Implement monitoring** with CloudWatch and DataDog
6. **Add ML pipelines** with SageMaker

---

**Author**: Shck Tchamna (tchamna@gmail.com)  
**Last Updated**: October 2025  
**AWS Architecture**: Data Lake + Analytics Platform