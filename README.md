# Financial Trading ETL Pipeline

A production-ready ETL (Extract, Transform, Load) pipeline for financial data with automated minute-level cryptocurrency collection, AWS S3 cloud storage, and comprehensive technical analysis.

## 🚀 Features

- **Automated Daily Collection**: Scheduled minute-level cryptocurrency data collection
- **Multi-Source APIs**: Binance, CryptoCompare, Kraken, and Alpha Vantage integration
- **Cloud Storage**: AWS S3 with intelligent compression and partitioning
- **Technical Analysis**: RSI, SMA, volatility analysis with trading insights
- **Production-Ready**: Organized structure with proper logging and error handling
- **Cross-Platform**: Windows Task Scheduler and Unix cron job support
- **Comprehensive Documentation**: Detailed guides for setup and usage

## 📁 Organized Project Structure

```
financial-trading-etl-pipeline/
├── 📂 automation/                 # Daily automation scripts
│   ├── daily_data_collection.py   # Main automated pipeline
│   ├── setup_scheduler.ps1        # Windows Task Scheduler setup
│   ├── setup_cron.sh             # Unix/Linux cron setup
│   └── run_manual.py             # Manual testing script
├── 📂 scripts/                   # Core production scripts
│   ├── crypto_minute_collector.py # Minute-level data collection
│   ├── real_database_pipeline.py  # Database integration
│   └── upload_minute_data.py     # S3 upload with compression
├── 📂 utilities/                 # Helper and utility scripts
│   ├── 📂 analysis/              # Data analysis tools
│   ├── 📂 setup/                 # Setup and configuration helpers  
│   └── 📂 testing/               # Test scripts and validation
├── 📂 data/                      # Data files and outputs
├── 📂 docs/                      # Comprehensive documentation
├── 📂 dags/                      # Airflow orchestration
├── 📂 docker/                    # Container configurations
├── config.py                     # Configuration management
├── config.json                   # Settings and credentials
└── requirements.txt              # Production dependencies
```

## ⚡ Quick Start

### 1. Installation
```powershell
# Clone and setup
git clone <repository-url>
cd financial-trading-etl-pipeline

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
```powershell
# Copy and edit configuration
cp data\config.example.json config.json
# Edit config.json with your API keys and AWS credentials
```

### 3. Test Manual Collection
```powershell
# Run manual data collection test
python automation\run_manual.py
```

### 4. Setup Daily Automation
```powershell
# Windows (run as Administrator)
powershell -ExecutionPolicy Bypass -File automation\setup_scheduler.ps1

# Linux/Unix
chmod +x automation/setup_cron.sh
./automation/setup_cron.sh /path/to/project
```

## 📊 What It Does Daily

✅ **Collects** minute-level data for 8 cryptocurrencies (BTC, ETH, SOL, ADA, DOT, LINK, UNI, AVAX)  
✅ **Compresses** and uploads to S3 with 91%+ compression ratio  
✅ **Analyzes** with technical indicators (RSI, SMA, volatility)  
✅ **Reports** best/worst performers and trading insights  
✅ **Maintains** 7-day data retention with automatic cleanup  
✅ **Logs** all activities for monitoring and debugging  

## 🔧 Configuration

Edit `config.json` with your credentials:
```json
{
  "api_keys": {
    "cryptocompare": "your_cryptocompare_api_key",
    "binance": "optional_binance_key",
    "alpha_vantage": "optional_alpha_vantage_key"
  },
  "aws": {
    "access_key_id": "your_aws_access_key",
    "secret_access_key": "your_aws_secret_key",
    "s3_bucket": "your-s3-bucket-name",
    "region": "us-east-1"
  }
}
```

## 📈 Recent Success Metrics

- **Data Volume**: 4,800+ minute records per day
- **S3 Compression**: 91.8% size reduction (1.5MB → 124KB)
- **Analysis Insights**: Real-time performance tracking (Solana +11.44% best performer)
- **Reliability**: Multi-source API fallbacks ensure 99%+ uptime
- **Storage**: Intelligent S3 partitioning by year/month/day

## 🛠️ Available Scripts

### Automation
- `automation/daily_data_collection.py` - Main automated pipeline
- `automation/run_manual.py` - Manual testing and validation
- `automation/setup_scheduler.ps1` - Windows automation setup

### Core Scripts  
- `scripts/crypto_minute_collector.py` - Multi-source data collection
- `scripts/upload_minute_data.py` - S3 upload with compression
- `scripts/real_database_pipeline.py` - Database integration

### Analysis Tools
- `utilities/analysis/simple_minute_analyzer.py` - Technical analysis engine
- `utilities/analysis/api_comparison_analysis.py` - API performance comparison

## 📚 Documentation

Comprehensive guides available in `docs/`:
- **[User Guide](docs/USER_GUIDE.md)** - Complete setup and usage
- **[Configuration Guide](docs/CONFIG_GUIDE.md)** - Detailed configuration options
- **[S3 Integration Guide](docs/S3_INTEGRATION_GUIDE.md)** - Cloud storage setup
- **[Minute Data Guide](docs/MINUTE_DATA_GUIDE.md)** - Data collection details

## 🔄 Automation Schedule

- **Daily at 6:00 AM**: Collect previous day's minute data
- **Automatic Upload**: Compressed data to S3 cloud storage  
- **Technical Analysis**: Generate trading insights and performance reports
- **Cleanup**: Remove files older than 7 days
- **Logging**: Complete activity logs for monitoring

## 🎯 Production Features

- **Error Handling**: Graceful API failures with fallback sources
- **Logging**: Comprehensive activity and error logging  
- **Monitoring**: Success/failure tracking and notifications
- **Scalability**: Cloud storage with automatic partitioning
- **Security**: Credential management and secure API access
- **Cross-Platform**: Works on Windows, Linux, and macOS

## 👤 Author

**Tyler Chamberlain**  
Email: tyler.chamberlain@example.com  
Project: Enterprise-grade Financial Data ETL Pipeline