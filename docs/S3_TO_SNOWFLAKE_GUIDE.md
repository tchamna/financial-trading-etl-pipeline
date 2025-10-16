# S3 to Snowflake Data Loading Guide

This guide explains how to load crypto minute data from AWS S3 into Snowflake using the `load_s3_to_snowflake.py` script.

## Prerequisites

1. **Install boto3** (AWS SDK for Python):
   ```bash
   pip install boto3
   ```

2. **AWS Credentials** configured (one of):
   - AWS CLI configured (`aws configure`)
   - Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
   - IAM role (if running on EC2/Lambda)

3. **Data in S3**: Crypto minute data JSON files should be uploaded to S3

## Usage

### Method 1: Download and Bulk Insert (Recommended - Most Flexible)

This method downloads files from S3 and uses optimized bulk inserts:

```bash
# Basic usage with default prefix
python load_s3_to_snowflake.py --bucket your-bucket-name

# With custom prefix
python load_s3_to_snowflake.py --bucket your-bucket-name --prefix crypto-data/2025/

# Explicitly specify download method
python load_s3_to_snowflake.py --method download --bucket your-bucket-name
```

**Advantages:**
- Works with standard S3 permissions
- Flexible data transformation
- Good error handling
- ~500-1500 rows/second

### Method 2: COPY INTO (Fastest - Requires Setup)

This method uses Snowflake's native COPY INTO command for direct S3 loading:

```bash
# With AWS credentials
python load_s3_to_snowflake.py \
    --method copy \
    --bucket your-bucket-name \
    --prefix crypto-data/ \
    --aws-key-id YOUR_AWS_KEY \
    --aws-secret-key YOUR_AWS_SECRET

# Using IAM role (no credentials needed)
python load_s3_to_snowflake.py --method copy --bucket your-bucket-name
```

**Advantages:**
- Fastest method (10-20x faster)
- Leverages Snowflake's native capabilities
- Minimal data transfer

**Requirements:**
- Snowflake external stage configured
- Proper IAM permissions on S3 bucket
- May require additional Snowflake setup

## Command-Line Options

| Option | Required | Description |
|--------|----------|-------------|
| `--method` | No | Method to use: `copy` or `download` (default: `download`) |
| `--bucket` | Yes | S3 bucket name (e.g., `financial-trading-data`) |
| `--prefix` | No | S3 path prefix (default: `crypto-minute-data/`) |
| `--aws-key-id` | No | AWS Access Key ID (for COPY INTO method) |
| `--aws-secret-key` | No | AWS Secret Access Key (for COPY INTO method) |

## Examples

### Example 1: Load from Production S3 Bucket
```bash
python load_s3_to_snowflake.py \
    --bucket financial-trading-production \
    --prefix crypto-minute-data/2025/10/
```

### Example 2: Load Historical Data
```bash
python load_s3_to_snowflake.py \
    --bucket financial-trading-archive \
    --prefix historical/crypto-minute/
```

### Example 3: Using COPY INTO with Credentials
```bash
python load_s3_to_snowflake.py \
    --method copy \
    --bucket financial-trading-data \
    --aws-key-id AKIAIOSFODNN7EXAMPLE \
    --aws-secret-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

## S3 Data Structure Expected

The script expects JSON files in this structure:
```
s3://your-bucket/
└── crypto-minute-data/
    ├── crypto_minute_data_20251009.json
    ├── crypto_minute_data_20251010.json
    ├── crypto_minute_data_20251011.json
    └── ...
```

Each JSON file should have the format:
```json
[
  {
    "collection_time": "2025-10-15T03:27:12.214693+00:00",
    "target_date": "2025-10-14",
    "data_sources": ["Binance", "CryptoCompare", "Kraken"],
    "crypto_data": [
      {
        "symbol": "BITCOIN",
        "timestamp": "2025-10-14 03:27:00 UTC",
        "open": 113460.63,
        "high": 113478.56,
        "low": 113452.86,
        "close": 113477.51,
        "volume": 1581631.09,
        "api_source": "CryptoCompare",
        "interval": "1min"
      },
      ...
    ]
  },
  "crypto_minute_data_20251014.json"
]
```

## Performance Benchmarks

| Method | Speed | Use Case |
|--------|-------|----------|
| Download + Bulk Insert | 500-1500 rows/sec | General use, flexible transformations |
| COPY INTO | 5000-10000+ rows/sec | Large volumes, pre-formatted data |

## Comparison: Local vs S3 Loading

### Local File Loading (`load_crypto_fast.py`)
```bash
python load_crypto_fast.py
```
- Best for: Development, testing, small datasets
- Speed: ~500-1500 rows/second
- Requires: Files in local `data/` directory

### S3 Loading (`load_s3_to_snowflake.py`)
```bash
python load_s3_to_snowflake.py --bucket your-bucket
```
- Best for: Production, large datasets, automated pipelines
- Speed: 500-10000+ rows/second (method dependent)
- Requires: Data uploaded to S3, AWS credentials

## Troubleshooting

### Issue: "boto3 not installed"
**Solution:**
```bash
pip install boto3
```

### Issue: "Access Denied" error from S3
**Solution:** 
- Verify AWS credentials are configured
- Check S3 bucket permissions
- Ensure IAM user/role has `s3:GetObject` and `s3:ListBucket` permissions

### Issue: COPY INTO fails
**Solution:**
- Verify Snowflake has access to S3 bucket
- Check if external stage is configured
- Try the `download` method instead

### Issue: Slow performance
**Solution:**
- Use `--method copy` for fastest loading
- Check network connection to S3
- Increase Snowflake warehouse size
- Verify S3 and Snowflake are in the same AWS region

## Integration with Pipeline

### Automated Daily Load from S3
Add to your cron job or scheduler:

```bash
# Collect data
python automation/daily_data_collection.py

# Upload to S3
python scripts/s3_data_uploader.py

# Load to Snowflake
python load_s3_to_snowflake.py --bucket financial-trading-data
```

### Airflow DAG Integration
```python
from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG('crypto_data_pipeline') as dag:
    collect_data = BashOperator(
        task_id='collect_data',
        bash_command='python automation/daily_data_collection.py'
    )
    
    upload_s3 = BashOperator(
        task_id='upload_s3',
        bash_command='python scripts/s3_data_uploader.py'
    )
    
    load_snowflake = BashOperator(
        task_id='load_snowflake',
        bash_command='python load_s3_to_snowflake.py --bucket financial-trading-data'
    )
    
    collect_data >> upload_s3 >> load_snowflake
```

## Security Best Practices

1. **Never commit AWS credentials** to git
2. **Use IAM roles** when possible (EC2, Lambda, ECS)
3. **Use environment variables** for credentials
4. **Restrict S3 bucket access** to specific IAM users/roles
5. **Enable S3 bucket encryption** at rest
6. **Use VPC endpoints** for private S3 access from Snowflake

## Next Steps

- Set up automated S3 uploads with `scripts/s3_data_uploader.py`
- Configure Snowflake external stages for COPY INTO method
- Implement data retention policies in S3
- Set up CloudWatch monitoring for S3 access patterns
