# Usage Examples

This guide shows how to use the Financial Trading ETL Pipeline for various scenarios.

## Data Collection

### Crypto Minute Data Collection

#### Collect Yesterday's Data (Default)
```bash
# Collect crypto minute data for yesterday
python scripts/crypto_minute_collector.py
```

#### Collect Data for a Specific Date
```bash
# Collect data for October 12, 2025
python scripts/crypto_minute_collector.py --date 2025-10-12

# Short form
python scripts/crypto_minute_collector.py -d 2025-10-12

# Collect data for a week ago
python scripts/crypto_minute_collector.py -d 2025-10-07
```

#### View Help
```bash
python scripts/crypto_minute_collector.py --help
```

### Automated Data Collection

#### Schedule Daily Collection (Windows)
```powershell
# Run the scheduler setup
.\automation\setup_scheduler.ps1
```

#### Schedule Daily Collection (Linux/Mac)
```bash
# Run the cron setup
./automation/setup_cron.sh
```

## Data Upload to S3

### Upload Specific Files
```python
# Python script to upload data
python scripts/upload_minute_data.py
```

### Test S3 Upload
```bash
# Test Parquet creation and S3 upload
python utilities/testing/test_parquet_s3.py
```

## Full Pipeline Test

### Run Complete Pipeline Test
```bash
# Test all components (collection, storage, S3, Snowflake)
python utilities/testing/full_pipeline_test.py
```

## Working with Different Date Ranges

### Collect Historical Data
```bash
# Collect data for multiple dates
python scripts/crypto_minute_collector.py -d 2025-10-01
python scripts/crypto_minute_collector.py -d 2025-10-02
python scripts/crypto_minute_collector.py -d 2025-10-03
```

### Automated Loop for Date Range (PowerShell)
```powershell
# Collect data for a date range
$startDate = Get-Date "2025-10-01"
$endDate = Get-Date "2025-10-10"

for ($date = $startDate; $date -le $endDate; $date = $date.AddDays(1)) {
    $dateStr = $date.ToString("yyyy-MM-dd")
    Write-Host "Collecting data for $dateStr..."
    python scripts/crypto_minute_collector.py -d $dateStr
    Start-Sleep -Seconds 2
}
```

### Automated Loop for Date Range (Bash)
```bash
# Collect data for a date range
start_date="2025-10-01"
end_date="2025-10-10"

current_date="$start_date"
while [ "$current_date" != $(date -I -d "$end_date + 1 day") ]; do
    echo "Collecting data for $current_date..."
    python scripts/crypto_minute_collector.py -d "$current_date"
    sleep 2
    current_date=$(date -I -d "$current_date + 1 day")
done
```

## S3 Path Structure

Data is stored in S3 with the following structure:

```
financial-trading-data-lake/
├── 2025/
│   ├── raw/
│   │   └── crypto/
│   │       └── month=10/
│   │           └── day=12/
│   │               ├── crypto_minute_data_20251012.json
│   │               └── crypto_minute_data_20251012.parquet
│   └── processed/
│       └── crypto/
│           └── month=10/
│               └── day=13/
│                   └── crypto_minute_data_20251013.parquet
```

### Benefits of This Structure:
- **Year as top-level partition** - Easy to query by year
- **Separate raw/processed folders** - Clear data lifecycle management
- **Month/day partitions** - Efficient data filtering
- **Both JSON and Parquet formats** - Human-readable and analytics-optimized

## Programmatic Usage

### Use in Python Scripts

```python
from scripts.crypto_minute_collector import collect_multi_source_crypto_minutes

# Collect data for yesterday (default)
data, filename = collect_multi_source_crypto_minutes()

# Collect data for a specific date
data, filename = collect_multi_source_crypto_minutes(target_date='2025-10-12')

# Collect data for specific symbols
data, filename = collect_multi_source_crypto_minutes(
    symbols=['bitcoin', 'ethereum'],
    target_date='2025-10-12'
)
```

### Upload to S3 Programmatically

```python
from scripts.s3_data_uploader import S3DataUploader
from config import get_config
import pandas as pd

config = get_config()
uploader = S3DataUploader(
    bucket_name=config.s3.bucket_name,
    aws_access_key_id=config.s3.access_key_id,
    aws_secret_access_key=config.s3.secret_access_key,
    region_name=config.s3.region
)

# Upload DataFrame as Parquet
df = pd.read_json('data/crypto_minute_data_20251012.json')
s3_path = uploader.upload_parquet_data(
    df=df,
    s3_key='2025/processed/crypto/month=10/day=12/data.parquet'
)
print(f"Uploaded to: {s3_path}")
```

## Configuration

### User Settings
Edit `user_config.py` for:
- Symbols to collect
- Storage preferences (JSON, Parquet, Local, S3)
- Collection intervals
- Data retention policies

### System Settings
Edit `config.json` for:
- API credentials
- Database credentials
- S3 credentials
- Snowflake credentials

See `CONFIGURATION_GUIDE.md` for detailed configuration options.

## Troubleshooting

### Check S3 Connection
```bash
python utilities/setup/check_s3_access.py
```

### Check Database Connection
```bash
python utilities/setup/check_real_database.py
```

### Verify Configuration
```bash
python utilities/testing/full_pipeline_test.py
```

## Next Steps

1. **Schedule automated collection** - Use Windows Task Scheduler or cron
2. **Set up Snowflake** - Follow `SNOWFLAKE_INTEGRATION_GUIDE.md`
3. **Create dashboards** - Connect BI tools to your data warehouse
4. **Add more symbols** - Edit `CRYPTO_SYMBOLS` in `user_config.py`
5. **Implement alerts** - Set up monitoring with Slack/email notifications
