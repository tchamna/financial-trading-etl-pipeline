# 📊 Financial Trading ETL Pipeline

> A production-ready, cloud-native ETL pipeline for automated cryptocurrency data collection, processing, and storage with AWS S3 integration and Snowflake data warehouse support.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![AWS S3](https://img.shields.io/badge/AWS-S3-orange.svg)](https://aws.amazon.com/s3/)
[![Snowflake](https://img.shields.io/badge/Snowflake-Ready-blue.svg)](https://www.snowflake.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ Features

### 🔄 **Data Collection**
- **Minute-Level Precision**: Collects cryptocurrency market data at 1-minute intervals
- **Multi-Source Resilience**: Automatic fallback between Binance → CryptoCompare → Kraken
- **8 Major Cryptocurrencies**: BTC, ETH, SOL, ADA, DOT, LINK, UNI, AVAX
- **9,600+ Records/Day**: 1,200 minutes × 8 symbols = comprehensive intraday coverage
- **Historical Data**: Collect data for any past date with strict `YYYY-MM-DD` validation

### ☁️ **Cloud Storage (AWS S3)**
- **Dual Format Storage**: JSON (compressed) + Parquet (analytics-optimized)
- **92% Compression**: 3MB JSON → 240KB Parquet
- **Smart Partitioning**: `s3://bucket/YYYY/processed/crypto/month=MM/`
- **Lifecycle Policies**: Automatic tiering (S3 → Glacier) for cost optimization
- **Optimized for Analytics**: Dictionary encoding, statistics, pushdown predicates

### 🏢 **Data Warehouse (Snowflake)**
- **Optional Integration**: Seamless Snowflake data warehouse loading
- **Auto Schema Management**: Table creation and updates
- **Deduplication**: Built-in data quality checks
- **Stage Loading**: Efficient bulk loading from S3

### 📈 **Analytics & Processing**
- **Technical Analysis**: Performance metrics, volatility, volume analysis
- **Real-time Insights**: Best/worst performers, price ranges, API source tracking
- **Configurable Storage**: Local + Cloud with retention policies
- **Comprehensive Logging**: Full audit trail for monitoring and debugging

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Data Collection Layer                         │
│  Binance API → CryptoCompare API → Kraken API (Fallback)       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Processing & Storage Layer                     │
│  • JSON Format (Human-Readable)                                 │
│  • Parquet Format (Analytics-Ready)                             │
│  • Technical Analysis (RSI, SMA, Volatility)                    │
└────────────┬──────────────────────────────┬─────────────────────┘
             │                               │
             ↓                               ↓
┌─────────────────────────┐    ┌───────────────────────────────┐
│     AWS S3 Storage      │    │    Local Storage (Optional)   │
│  • Raw Data (JSON.gz)   │    │  • 7-day retention            │
│  • Processed (Parquet)  │    │  • JSON + Parquet formats     │
│  • Year/Month Partition │    │                               │
└────────────┬────────────┘    └───────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────────────────────────────┐
│              Snowflake Data Warehouse (Optional)                 │
│  • Schema: FINANCIAL_DB.CORE.CRYPTO_MINUTE_DATA                 │
│  • Deduplication & Quality Checks                               │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
financial-trading-etl-pipeline/
├── 📂 automation/                      # Automated daily collection
│   ├── daily_data_collection.py       # Main pipeline orchestrator
│   ├── setup_scheduler.ps1            # Windows Task Scheduler
│   └── setup_cron.sh                  # Linux/Mac cron jobs
│
├── 📂 scripts/                         # Core data scripts
│   ├── crypto_minute_collector.py     # Multi-source data collection
│   ├── upload_minute_data.py          # S3 storage manager
│   ├── snowflake_data_loader.py       # Snowflake integration
│   └── s3_data_uploader.py            # Generic S3 uploader
│
├── 📂 utilities/                       # Tools & helpers
│   ├── setup/                         # Configuration utilities
│   │   ├── snowflake_quick_setup.py   # Interactive Snowflake setup
│   │   ├── check_s3_access.py         # S3 connection validator
│   │   └── create_s3_bucket.py        # Bucket creator
│   ├── testing/                       # Consolidated test suites
│   │   ├── full_pipeline_test.py      # End-to-end tests (recommended)
│   │   ├── test_parquet_s3.py         # Format validation
│   │   ├── test_api_connections.py    # API connectivity
│   │   └── integration_test.py        # Integration tests
│   └── analysis/                      # Data analyzers
│
├── 📂 docs/                            # All documentation
│   ├── CONFIGURATION_GUIDE.md         # Setup instructions
│   ├── DATE_COLLECTION_GUIDE.md       # Usage examples
│   ├── S3_INTEGRATION_GUIDE.md        # AWS S3 guide
│   ├── SNOWFLAKE_INTEGRATION_GUIDE.md # Data warehouse guide
│   ├── PROJECT_DOCUMENTATION.md       # Architecture
│   ├── SETUP.md                       # Installation steps
│   ├── USAGE_EXAMPLES.md              # Code recipes
│   └── USER_GUIDE.md                  # User manual
│
├── 📂 data/                            # Data storage (local)
├── config.py                           # Configuration loader
├── user_config.py                      # User settings
├── config.example.json                 # Template
├── README.md                           # This file (only .md in root)
└── requirements.txt                    # Dependencies
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+**
- **AWS Account** (for S3 storage)
- **Snowflake Account** (optional, for data warehouse)
- **API Keys**: CoinGecko, CryptoCompare (free tiers available)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/tchamna/financial-trading-etl-pipeline.git
cd financial-trading-etl-pipeline

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# 1. Copy example configuration
cp config.example.json config.json

# 2. Edit config.json with your credentials
# Add AWS credentials, API keys, and database settings

# 3. Review user_config.py for preferences
# Customize symbols, intervals, storage options
```

### Usage

#### Option 1: Collect Data for Specific Date

```bash
# Collect data for any past date
python automation/daily_data_collection.py 2025-10-13

# Or using flag
python automation/daily_data_collection.py --date 2025-10-13

# Or with short flag
python automation/daily_data_collection.py -d 2025-10-13

# Collect data for yesterday (default)
python automation/daily_data_collection.py
```

#### Option 2: Test the Pipeline

```bash
# Run comprehensive pipeline test
python utilities/testing/full_pipeline_test.py

# Test Parquet creation and S3 upload
python utilities/testing/test_parquet_s3.py
```

#### Option 3: Standalone Collection

```bash
# Collect data without S3 upload
python scripts/crypto_minute_collector.py 2025-10-13
```

---

## 📊 What It Does

### Daily Automated Collection

✅ **Collects**: Minute-level OHLCV data for 8 major cryptocurrencies  
✅ **Processes**: Converts to both JSON (human-readable) and Parquet (analytics-optimized)  
✅ **Compresses**: Achieves 92% compression (3MB → 240KB)  
✅ **Uploads**: Stores to AWS S3 with intelligent partitioning  
✅ **Analyzes**: Calculates performance, volatility, volume metrics  
✅ **Maintains**: 7-day local retention with automatic cleanup  
✅ **Logs**: Complete audit trail for monitoring

### Data Collection Output

```
💾 COLLECTION SUMMARY:
==============================
   💰 Total minute records: 9,600
   🪙 Unique symbols: 8
   📄 Saved to: crypto_minute_data_20251013.json
   📊 BTC: 1,200 minutes
   📊 ETH: 1,200 minutes
   📊 SOL: 1,200 minutes
   ... (5 more symbols)

☁️ S3 UPLOAD:
   ✅ JSON uploaded: 218 KB (92.7% compressed)
   ✅ Parquet uploaded: 241 KB (analytics-optimized)
   📁 Bucket: financial-trading-data-lake
```

---

## 🗂️ S3 Path Structure

Data is organized in S3 with year and month partitioning for easy querying:

```
s3://financial-trading-data-lake/
├── 2025/
│   ├── raw/
│   │   └── crypto/
│   │       └── month=10/
│   │           ├── crypto_minute_data_20251010.json
│   │           ├── crypto_minute_data_20251011.json
│   │           └── crypto_minute_data_20251012.json
│   │
│   └── processed/
│       └── crypto-minute/
│           ├── json/
│           │   └── month=10/
│           │       ├── crypto_minute_data_20251010.json.gz
│           │       ├── crypto_minute_data_20251011.json.gz
│           │       └── crypto_minute_data_20251012.json.gz
│           │
│           └── parquet/
│               └── month=10/
│                   ├── crypto_minute_data_20251010.parquet
│                   ├── crypto_minute_data_20251011.parquet
│                   └── crypto_minute_data_20251012.parquet
```

**Benefits:**
- All files for the same month are grouped together
- Easy to query specific date ranges
- Optimized for analytics tools (Athena, Spark, Snowflake)
- Filename contains full date for identification  

---

## ⚙️ Configuration

### User Settings (`user_config.py`)

```python
# Crypto symbols to collect
CRYPTO_SYMBOLS = ['BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'LINK', 'UNI', 'AVAX']

# Data collection interval
DATA_COLLECTION_INTERVAL_MINUTES = 5

# Storage configuration
ENABLE_LOCAL_STORAGE = True       # Save files locally
ENABLE_S3_STORAGE = True          # Upload to AWS S3
SAVE_JSON_FORMAT = True           # Save as JSON
SAVE_PARQUET_FORMAT = True        # Save as Parquet
KEEP_LOCAL_DAYS = 7               # Local retention period

# S3 settings
S3_BUCKET_NAME = "financial-trading-data-lake"
S3_REGION = "us-east-1"

# Snowflake (optional)
ENABLE_SNOWFLAKE = False          # Enable Snowflake loading
```

### Credentials (`config.json`)

```json
{
  "api": {
    "alpha_vantage_api_key": "YOUR_ALPHA_VANTAGE_KEY",
    "coingecko_base_url": "https://api.coingecko.com/api/v3"
  },
  "s3": {
    "enabled": true,
    "access_key_id": "YOUR_AWS_ACCESS_KEY",
    "secret_access_key": "YOUR_AWS_SECRET_KEY",
    "region": "us-east-1"
  },
  "snowflake": {
    "account": "YOUR_ACCOUNT.snowflakecomputing.com",
    "username": "YOUR_USERNAME",
    "password": "YOUR_PASSWORD",
    "warehouse": "FINANCIAL_WH",
    "database": "FINANCIAL_DB",
    "schema": "CORE"
  }
}
```

---

## � Documentation

### Essential Guides

- **[Configuration Guide](docs/CONFIGURATION_GUIDE.md)** - Complete setup instructions
- **[Date Collection Guide](docs/DATE_COLLECTION_GUIDE.md)** - Usage examples and date formats
- **[S3 Integration Guide](docs/S3_INTEGRATION_GUIDE.md)** - AWS S3 setup and best practices
- **[Snowflake Integration Guide](docs/SNOWFLAKE_INTEGRATION_GUIDE.md)** - Data warehouse setup

### Additional Resources

- **[Project Documentation](docs/PROJECT_DOCUMENTATION.md)** - Architecture and design
- **[Setup Guide](docs/SETUP.md)** - Installation and configuration steps
- **[Usage Examples](docs/USAGE_EXAMPLES.md)** - Common use cases and recipes
- **[User Guide](docs/USER_GUIDE.md)** - Comprehensive user manual

---

## 🧪 Testing

### Run All Tests

```bash
# Comprehensive end-to-end test
python utilities/testing/full_pipeline_test.py
```

**Test Coverage:**
- ✅ Configuration validation
- ✅ Data collection (9,600 records)
- ✅ File creation (JSON + Parquet)
- ✅ S3 upload verification
- ✅ Snowflake integration (optional)
- ✅ Pipeline flow validation

**Expected Output:**
```
======================================================================
  TEST SUMMARY
======================================================================

📋 Results:
   ✅ PASS   - Configuration
   ✅ PASS   - Data Collection
   ✅ PASS   - Data Files
   ✅ PASS   - S3 Upload
   ✅ PASS   - Snowflake
   ✅ PASS   - Pipeline Flow

📊 Score: 6/6 tests passed

🎉 ALL TESTS PASSED! Your pipeline is fully functional!
```

---

## 📈 Performance Metrics

### Data Efficiency

| Metric | Value |
|--------|-------|
| **Records/Day** | 9,600 (1,200 min × 8 symbols) |
| **JSON Size** | ~3.0 MB |
| **Parquet Size** | ~240 KB |
| **Compression** | 92% reduction |
| **Collection Time** | ~2-3 minutes |
| **Upload Time** | ~5-10 seconds |

### Storage Costs (Example)

| Storage | Monthly Cost (10 days) |
|---------|----------------------|
| **S3 Standard** | ~$0.01 (2.4 MB × 10 days) |
| **S3 Glacier** | ~$0.004 (after 30 days) |
| **Snowflake** | Pay-per-query |

---

## 🔧 Advanced Usage

### Backfilling Historical Data

```bash
# Collect data for multiple days
python automation/daily_data_collection.py 2025-10-01
python automation/daily_data_collection.py 2025-10-02
python automation/daily_data_collection.py 2025-10-03

# Or use a PowerShell loop
$dates = @('2025-10-01', '2025-10-02', '2025-10-03', '2025-10-04')
foreach ($date in $dates) {
    python automation/daily_data_collection.py $date
}
```

### Querying Parquet with Python

```python
import pandas as pd

# Read from local file
df = pd.read_parquet('data/crypto_minute_data_20251013.parquet')

# Filter specific symbol
btc_data = df[df['symbol'] == 'BITCOIN']

# Calculate hourly averages
hourly_avg = df.groupby(df['timestamp'].dt.hour)['close'].mean()
```

### Snowflake Queries

```sql
-- Query crypto data in Snowflake
SELECT 
    symbol,
    DATE_TRUNC('hour', timestamp) as hour,
    AVG(close) as avg_price,
    MAX(high) as max_price,
    MIN(low) as min_price,
    SUM(volume) as total_volume
FROM FINANCIAL_DB.CORE.CRYPTO_MINUTE_DATA
WHERE DATE(timestamp) = '2025-10-13'
GROUP BY symbol, hour
ORDER BY symbol, hour;
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests before committing
python utilities/testing/full_pipeline_test.py
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Shck Tchamna**
- Email: tchamna@gmail.com
- GitHub: [@tchamna](https://github.com/tchamna)

---

## 🙏 Acknowledgments

- **Alpha Vantage** - Financial data API
- **CoinGecko** - Cryptocurrency data
- **CryptoCompare** - Market data provider
- **AWS S3** - Cloud storage
- **Snowflake** - Data warehouse platform

---

## � Support

For issues, questions, or suggestions:
1. Check the [Documentation](#-documentation)
2. Review [Configuration Guide](docs/CONFIGURATION_GUIDE.md)
3. Open an issue on GitHub
4. Contact: tchamna@gmail.com

---

<div align="center">

**⭐ Star this repo if you find it helpful!**

Made with ❤️ by Shck Tchamna

</div>