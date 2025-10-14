# Configuration Management Guide

## Overview
The Financial Trading ETL Pipeline uses a comprehensive configuration system that allows you to control all aspects of the pipeline behavior without modifying code. This includes database connections, API settings, S3 integration, processing parameters, and Airflow orchestration.

## Configuration Files

### 1. config.py
The main configuration module that defines all configuration classes and handles loading from multiple sources:
- JSON configuration files
- Environment variables  
- Default values

### 2. config.example.json
Template configuration file showing all available options with example values. Copy this to `config.json` and customize for your environment.

### 3. config.json (ignored by git)
Your actual configuration file containing real credentials and settings. This file is excluded from version control for security.

## Configuration Sections

### Database Configuration
```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "database": "financial_data",
    "username": "postgres",
    "password": "your_password_here",
    "schema": "public"
  }
}
```

### S3 Configuration  
```json
{
  "s3": {
    "enabled": true,
    "bucket_name": "financial-trading-data-lake",
    "region": "us-east-1",
    "access_key_id": "your_aws_key",
    "secret_access_key": "your_aws_secret",
    "enable_compression": true,
    "enable_partitioning": true
  }
}
```

### API Configuration
```json
{
  "api": {
    "alpha_vantage_api_key": "your_api_key",
    "requests_per_minute": 5,
    "max_retries": 3
  }
}
```

### Processing Configuration
```json
{
  "processing": {
    "stock_symbols": ["AAPL", "GOOGL", "MSFT", "TSLA"],
    "crypto_symbols": ["bitcoin", "ethereum", "cardano"],
    "collection_interval_seconds": 300,
    "enable_technical_analysis": true,
    "enable_portfolio_tracking": true
  }
}
```

## Usage Examples

### Basic Usage
```python
from config import get_config

# Get configuration instance
config = get_config()

# Access configuration values
symbols = config.processing.stock_symbols
db_conn = config.database.connection_string
s3_enabled = config.s3.enabled
```

### Check S3 Status
```python
from config import is_s3_enabled

if is_s3_enabled():
    print("S3 integration is enabled")
    # Upload data to S3
else:
    print("S3 integration is disabled")
    # Use local storage only
```

### Validate Configuration
```python
config = get_config()
issues = config.validate()

if issues:
    print("Configuration issues found:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("Configuration is valid!")
```

## Environment Variable Override

Configuration values can be overridden using environment variables:

### Database
- `DB_HOST` → database.host
- `DB_PORT` → database.port  
- `DB_NAME` → database.database
- `DB_USER` → database.username
- `DB_PASSWORD` → database.password

### S3
- `S3_ENABLED` → s3.enabled (true/false)
- `AWS_S3_BUCKET_NAME` → s3.bucket_name
- `AWS_DEFAULT_REGION` → s3.region
- `AWS_ACCESS_KEY_ID` → s3.access_key_id
- `AWS_SECRET_ACCESS_KEY` → s3.secret_access_key

### Processing
- `STOCK_SYMBOLS` → processing.stock_symbols (comma-separated)
- `CRYPTO_SYMBOLS` → processing.crypto_symbols (comma-separated)
- `COLLECTION_INTERVAL_SECONDS` → processing.collection_interval_seconds

### API
- `ALPHA_VANTAGE_API_KEY` → api.alpha_vantage_api_key

## Setup Instructions

### 1. Create Configuration File
```bash
# Copy the example configuration
cp config.example.json config.json

# Edit with your settings
nano config.json  # or use your preferred editor
```

### 2. Set Environment Variables (Optional)
```bash
# Set in .env file or environment
export DB_PASSWORD="your_db_password"
export ALPHA_VANTAGE_API_KEY="your_api_key"
export S3_ENABLED="true"
export AWS_S3_BUCKET_NAME="your-bucket-name"
```

### 3. Validate Configuration
```bash
# Validate configuration
python config.py validate

# View configuration summary
python config.py summary

# Save current configuration to file
python config.py save config-backup.json
```

## Configuration Priority

Configuration values are loaded in this order (later values override earlier ones):

1. **Default values** (defined in config.py)
2. **Configuration file** (config.json)
3. **Environment variables** (highest priority)

This allows you to:
- Use config.json for most settings
- Override sensitive values with environment variables
- Have sensible defaults for development

## Security Best Practices

### 1. Never Commit Secrets
- Always use `config.json` for local development
- Use environment variables in production
- Never commit API keys or passwords to version control

### 2. Use Different Configs per Environment
```bash
# Development
export PIPELINE_CONFIG_FILE="config.dev.json"

# Staging
export PIPELINE_CONFIG_FILE="config.staging.json" 

# Production
export PIPELINE_CONFIG_FILE="config.prod.json"
```

### 3. Validate Before Running
Always validate configuration before running the pipeline:
```python
config = get_config()
issues = config.validate()
if issues:
    raise ValueError(f"Configuration issues: {issues}")
```

## Integration with Pipeline Components

### Real Database Pipeline
The `real_database_pipeline.py` automatically uses configuration for:
- Database connections
- Stock/crypto symbols to fetch
- S3 upload settings
- API endpoints and keys

### S3 Data Uploader
The `s3_data_uploader.py` uses configuration for:
- S3 bucket and region settings
- Compression and partitioning options
- Storage class and lifecycle policies

### Airflow DAG
The Airflow DAG uses configuration for:
- Schedule interval
- Email notifications
- Retry settings
- DAG naming

## Troubleshooting

### Common Issues

**Configuration file not found**
```bash
# Check if config.json exists
ls -la config.json

# Create from template if missing
cp config.example.json config.json
```

**Validation errors**
```bash
# Run validation to see specific issues
python config.py validate

# Common fixes:
# - Add missing API keys
# - Set correct database credentials
# - Configure S3 settings if enabled
```

**S3 not working**
```bash
# Check S3 configuration
python -c "from config import get_config; print(get_config().s3.enabled)"

# Test AWS credentials
aws sts get-caller-identity
```

### Debug Mode
Enable debug logging to see configuration loading:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

from config import get_config
config = get_config()
```

## Advanced Configuration

### Custom Configuration Files
```python
from config import PipelineConfig

# Load specific config file
config = PipelineConfig('my-custom-config.json')

# Use programmatically
config.s3.enabled = True
config.processing.stock_symbols = ['AAPL', 'MSFT']
```

### Dynamic Configuration Updates
```python
config = get_config()

# Update configuration at runtime
config.processing.collection_interval_seconds = 60

# Save updated configuration
config.save_to_file('updated-config.json')
```

### Configuration Templates
Create different configuration templates for different use cases:

**Minimal Local Development** (`config.local.json`)
```json
{
  "s3": {"enabled": false},
  "processing": {
    "stock_symbols": ["AAPL", "MSFT"],
    "crypto_symbols": ["bitcoin"]
  }
}
```

**Production Cloud** (`config.prod.json`) 
```json
{
  "s3": {"enabled": true},
  "processing": {
    "stock_symbols": ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA", "META"],
    "collection_interval_seconds": 300
  }
}
```

---

**Author**: Shck Tchamna (tchamna@gmail.com)  
**Last Updated**: October 2025