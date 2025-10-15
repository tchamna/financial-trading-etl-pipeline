# Date-Specific Data Collection Guide

This guide explains how to collect crypto minute data for any specific date using the pipeline.

## 📅 Date Format Requirement

**All dates must be in the format: `YYYY-MM-DD`**

✅ **Valid Examples:**
- `2025-10-12` (October 12, 2025)
- `2025-01-05` (January 5, 2025)
- `2024-12-31` (December 31, 2024)

❌ **Invalid Examples:**
- `10-12-2025` (MM-DD-YYYY format - NOT accepted)
- `12/10/2025` (MM/DD/YYYY format - NOT accepted)
- `2025/10/12` (Wrong separator - NOT accepted)
- `20251012` (No separators - NOT accepted)

## 🚀 Usage

### Option 1: Crypto Minute Collector (Standalone)

Collect minute-level crypto data for a specific date:

```powershell
# Collect data for yesterday (default)
python scripts\crypto_minute_collector.py

# Collect data for a specific date
python scripts\crypto_minute_collector.py --date 2025-10-12
python scripts\crypto_minute_collector.py -d 2025-10-01
```

**What it does:**
- ✅ Collects minute-level OHLCV data for all configured crypto symbols
- ✅ Saves data to `data/crypto_minute_data_YYYYMMDD.json`
- ✅ Displays performance analysis and volatility metrics
- ❌ Does NOT upload to S3 or process the data further

### Option 2: Daily Data Collection Pipeline (Full Pipeline)

Run the complete automated pipeline including S3 upload:

```powershell
# Run pipeline for yesterday (default)
python automation\daily_data_collection.py

# Run pipeline for a specific date
python automation\daily_data_collection.py --date 2025-10-12
python automation\daily_data_collection.py -d 2025-10-01
```

**What it does:**
- ✅ Collects minute-level crypto data
- ✅ Saves JSON and Parquet formats locally
- ✅ Uploads to S3 (if enabled in config)
- ✅ Performs technical analysis
- ✅ Cleans up old data files
- ✅ Logs all operations to `automation/daily_collection.log`

## 📊 Output

### File Naming Convention
Data files are automatically named using the date:

```
data/crypto_minute_data_20251012.json   # JSON format
data/crypto_minute_data_20251012.parquet # Parquet format
```

### S3 Path Structure
Files are uploaded to S3 with year-based partitioning:

```
s3://financial-trading-data-lake/
├── 2025/
│   ├── raw/
│   │   └── crypto/month=10/day=12/crypto_minute_data_20251012.json
│   └── processed/
│       └── crypto/month=10/day=12/crypto_minute_data_20251012.parquet
```

## ⚠️ Validation Rules

The scripts enforce strict validation:

1. **Date Format**: Must be exactly `YYYY-MM-DD`
   - ❌ Error: "Invalid date format: '10-12-2025'. Must be YYYY-MM-DD"

2. **Future Dates**: Cannot collect data for future dates
   - ❌ Error: "Date 2025-12-31 is in the future. Please provide a past or current date."

3. **Invalid Dates**: Date must be real (e.g., no February 30)
   - ❌ Error: "Invalid date: day is out of range for month"

## 💡 Tips

### Backfilling Historical Data
To collect data for multiple historical dates:

```powershell
# Windows PowerShell loop
$dates = @('2025-10-01', '2025-10-02', '2025-10-03', '2025-10-04', '2025-10-05')
foreach ($date in $dates) {
    python automation\daily_data_collection.py --date $date
}
```

### Default Behavior (Yesterday)
If you don't specify a date, both scripts default to **yesterday**:

```powershell
# These are equivalent to running with --date <yesterday>
python scripts\crypto_minute_collector.py
python automation\daily_data_collection.py
```

### Checking What Date Would Be Used
To see what date would be collected without actually collecting:

```powershell
python -c "from datetime import datetime, timedelta; print((datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'))"
```

## 📋 Configuration

The data collection respects your settings in `user_config.py`:

- **Crypto Symbols**: `CRYPTO_SYMBOLS` (default: BTC, ETH, SOL, ADA, DOT, LINK, UNI, AVAX)
- **Local Storage**: `ENABLE_LOCAL_STORAGE` (default: True)
- **S3 Upload**: `ENABLE_S3_STORAGE` (default: True)
- **JSON Format**: `SAVE_JSON_FORMAT` (default: True)
- **Parquet Format**: `SAVE_PARQUET_FORMAT` (default: True)
- **Data Retention**: `KEEP_LOCAL_DAYS` (default: 7 days)

## 🔍 Troubleshooting

### Error: Invalid date format
**Problem**: You used the wrong date format
```
❌ Error: Invalid date format: '10-12-2025'. Must be YYYY-MM-DD
```

**Solution**: Use YYYY-MM-DD format
```powershell
# Wrong
python scripts\crypto_minute_collector.py --date 10-12-2025

# Correct
python scripts\crypto_minute_collector.py --date 2025-10-12
```

### Error: Date is in the future
**Problem**: You tried to collect data for a future date
```
❌ Error: Date 2025-12-31 is in the future
```

**Solution**: Only use past or current dates (remember: default is yesterday)

### No data collected
**Problem**: API might be down or rate-limited

**Solution**: Check logs and try again later. The scripts use multiple free APIs as backup.

## 📚 Related Documentation

- `CONFIGURATION_GUIDE.md` - System configuration details
- `USAGE_EXAMPLES.md` - More usage examples
- `S3_INTEGRATION_GUIDE.md` - S3 setup and configuration
- `SNOWFLAKE_INTEGRATION_GUIDE.md` - Snowflake data warehouse setup

## 🤝 Support

For issues or questions:
1. Check the error message for specific guidance
2. Review configuration in `user_config.py`
3. Check logs in `automation/daily_collection.log`
4. Ensure API keys are configured in `config.json`
