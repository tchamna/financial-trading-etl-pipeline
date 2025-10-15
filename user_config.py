"""
User Configuration for Financial Trading ETL Pipeline
====================================================

✅ THIS IS THE FILE YOU SHOULD EDIT!

This file contains ALL the settings you need to customize your pipeline:
- Symbols to track (stocks & crypto)
- Data collection intervals
- Storage preferences
- Analysis features
- Alerts and notifications

📝 These settings are the SINGLE SOURCE OF TRUTH for user preferences.
   They are NOT duplicated in config.json (which only contains credentials
   and technical system settings).

For advanced system configurations, see config.py

Author: Shck Tchamna
Email: tchamna@gmail.com
"""

# ============================================================================
# SYMBOLS TO TRACK
# ============================================================================

# Stock symbols you want to collect data for
# Add or remove stock symbols as needed (use ticker symbols like AAPL, GOOGL)
STOCK_SYMBOLS = [
    "AAPL",     # Apple Inc.
    "GOOGL",    # Alphabet Inc. (Google)
    "MSFT",     # Microsoft Corporation
    "TSLA",     # Tesla Inc.
    "AMZN",     # Amazon.com Inc.
    "NVDA",     # NVIDIA Corporation
    "META"      # Meta Platforms Inc. (Facebook)
]

# Cryptocurrency symbols you want to collect data for
# Add or remove crypto symbols as needed (use standard tickers like BTC, ETH)
CRYPTO_SYMBOLS = [
    "BTC",      # Bitcoin
    "ETH",      # Ethereum
    "SOL",      # Solana
    "ADA",      # Cardano
    "DOT",      # Polkadot
    "LINK",     # Chainlink
    "UNI",      # Uniswap
    "AVAX"      # Avalanche
    # Add more crypto symbols here as needed
    # "MATIC",    # Polygon
    # "LTC",      # Litecoin
]

# ============================================================================
# DATA COLLECTION SETTINGS
# ============================================================================

# How often to collect data (in minutes)
# Options: 1, 5, 15, 30, 60 (1 minute is most detailed but uses more resources)
COLLECTION_INTERVAL_MINUTES = 5

# Time granularity for historical data collection
# Options: "1min", "5min", "15min", "30min", "1hour", "1day"
DATA_GRANULARITY = "1min"

# How many days of historical data to collect when starting
HISTORICAL_DAYS = 30

# ============================================================================
# STORAGE PREFERENCES
# ============================================================================

# Where to store your data
ENABLE_LOCAL_STORAGE = True    # Save files to your computer
ENABLE_S3_STORAGE = True       # Upload to AWS S3 cloud storage

# Data formats to save
SAVE_JSON_FORMAT = True        # Human-readable format
SAVE_PARQUET_FORMAT = True     # Compressed, efficient format for analysis

# Local storage settings
LOCAL_DATA_DIRECTORY = "data"  # Folder name for local data files
KEEP_LOCAL_FILES_DAYS = 7      # How many days to keep local files

# ============================================================================
# ANALYSIS FEATURES
# ============================================================================

# Enable technical analysis indicators
ENABLE_TECHNICAL_ANALYSIS = True

# Moving average periods (in days)
SIMPLE_MOVING_AVERAGES = [20, 50, 200]    # SMA periods
EXPONENTIAL_MOVING_AVERAGES = [12, 26]    # EMA periods

# Portfolio tracking
ENABLE_PORTFOLIO_TRACKING = True
DEFAULT_PORTFOLIO_NAME = "my_portfolio"

# ============================================================================
# ALERT SETTINGS
# ============================================================================

# Price change alert threshold (percentage)
# Set to 0 to disable price change alerts
PRICE_ALERT_THRESHOLD = 10.0  # Alert if any asset moves more than 10%

# Email notifications
ENABLE_EMAIL_ALERTS = True
EMAIL_ADDRESSES = [
    "tchamna@gmail.com"  # Add your email addresses here
]

# ============================================================================
# SCHEDULE SETTINGS (for automated collection)
# ============================================================================

# Automated collection schedule
# Format: "minute hour day_of_month month day_of_week"
# Examples:
#   "0 9 * * 1-5"    = Every weekday at 9:00 AM
#   "*/5 9-17 * * 1-5" = Every 5 minutes during market hours (9 AM - 5 PM), weekdays only
#   "0 */1 * * *"    = Every hour
COLLECTION_SCHEDULE = "*/5 9-17 * * 1-5"  # Every 5 minutes during market hours

# Enable weekend collection for crypto (crypto markets are 24/7)
CRYPTO_WEEKEND_COLLECTION = True

# ============================================================================
# ADVANCED SETTINGS (Modify with caution)
# ============================================================================

# API request settings
API_REQUESTS_PER_MINUTE = 5
MAX_API_RETRIES = 3

# S3 settings
S3_BUCKET_NAME = "financial-trading-data-lake"  # Your S3 bucket name
AWS_REGION = "us-east-1"
S3_STORAGE_CLASS = "STANDARD"

# Snowflake Data Warehouse settings
ENABLE_SNOWFLAKE = True            # Enable Snowflake data warehouse integration
SNOWFLAKE_WAREHOUSE = "FINANCIAL_WH"  # Snowflake warehouse name
SNOWFLAKE_DATABASE = "FINANCIAL_DB"   # Snowflake database name
SNOWFLAKE_SCHEMA = "CORE"             # Snowflake schema name
SNOWFLAKE_LOAD_INTERVAL_MINUTES = 15  # How often to load data to Snowflake

# Cron schedule for data collection (e.g., "*/5 * * * *" for every 5 minutes)
COLLECTION_SCHEDULE = "*/5 * * * *"


def get_user_config():
    """
    Collects all user-defined configurations into a dictionary.
    
    This function makes it easy for the main configuration system (config.py)
    to load and apply these user-specific settings.
    
    Returns:
        dict: A dictionary containing all user-defined settings.
    """
    return {
        # Symbols to track
        "stock_symbols": STOCK_SYMBOLS,
        "crypto_symbols": CRYPTO_SYMBOLS,
        
        # Data collection settings
        "collection_interval_minutes": COLLECTION_INTERVAL_MINUTES,
        "data_granularity": DATA_GRANULARITY,
        "historical_days": HISTORICAL_DAYS,
        
        # Storage preferences
        "enable_local_storage": ENABLE_LOCAL_STORAGE,
        "enable_s3_storage": ENABLE_S3_STORAGE,
        "save_json_format": SAVE_JSON_FORMAT,
        "save_parquet_format": SAVE_PARQUET_FORMAT,
        "local_data_directory": LOCAL_DATA_DIRECTORY,
        "keep_local_files_days": KEEP_LOCAL_FILES_DAYS,
        
        # Analysis features
        "enable_technical_analysis": ENABLE_TECHNICAL_ANALYSIS,
        "simple_moving_averages": SIMPLE_MOVING_AVERAGES,
        "exponential_moving_averages": EXPONENTIAL_MOVING_AVERAGES,
        "enable_portfolio_tracking": ENABLE_PORTFOLIO_TRACKING,
        "default_portfolio_name": DEFAULT_PORTFOLIO_NAME,
        
        # Alert settings
        "price_alert_threshold": PRICE_ALERT_THRESHOLD,
        "enable_email_alerts": ENABLE_EMAIL_ALERTS,
        "email_addresses": EMAIL_ADDRESSES,
        
        # Advanced settings
        "api_requests_per_minute": API_REQUESTS_PER_MINUTE,
        "max_api_retries": MAX_API_RETRIES,
        "s3_bucket_name": S3_BUCKET_NAME,
        "aws_region": AWS_REGION,
        "s3_storage_class": S3_STORAGE_CLASS,
        "collection_schedule": COLLECTION_SCHEDULE,
        
        # Snowflake settings
        "enable_snowflake": ENABLE_SNOWFLAKE,
        "snowflake_warehouse": SNOWFLAKE_WAREHOUSE,
        "snowflake_database": SNOWFLAKE_DATABASE,
        "snowflake_schema": SNOWFLAKE_SCHEMA,
        "snowflake_load_interval_minutes": SNOWFLAKE_LOAD_INTERVAL_MINUTES,
    }

def validate_user_config():
    """Validate user configuration settings"""
    errors = []
    
    # Check symbols
    if not STOCK_SYMBOLS:
        errors.append("At least one stock symbol must be specified")
    
    if not CRYPTO_SYMBOLS:
        errors.append("At least one crypto symbol must be specified")
    
    # Check intervals
    if COLLECTION_INTERVAL_MINUTES not in [1, 5, 15, 30, 60]:
        errors.append("Collection interval must be 1, 5, 15, 30, or 60 minutes")
    
    if DATA_GRANULARITY not in ["1min", "5min", "15min", "30min", "1hour", "1day"]:
        errors.append("Data granularity must be one of: 1min, 5min, 15min, 30min, 1hour, 1day")
    
    # Check storage
    if not ENABLE_LOCAL_STORAGE and not ENABLE_S3_STORAGE:
        errors.append("At least one storage option (local or S3) must be enabled")
    
    # Check email format (basic validation)
    if ENABLE_EMAIL_ALERTS:
        for email in EMAIL_ADDRESSES:
            if "@" not in email or "." not in email:
                errors.append(f"Invalid email address: {email}")
    
    return errors

def print_user_config_summary():
    """Print a summary of current user configuration"""
    print("=" * 60)
    print("USER CONFIGURATION SUMMARY")
    print("=" * 60)
    
    print(f"\n📊 SYMBOLS TO TRACK:")
    print(f"   Stocks ({len(STOCK_SYMBOLS)}): {', '.join(STOCK_SYMBOLS[:3])}{'...' if len(STOCK_SYMBOLS) > 3 else ''}")
    print(f"   Crypto ({len(CRYPTO_SYMBOLS)}): {', '.join(CRYPTO_SYMBOLS[:3])}{'...' if len(CRYPTO_SYMBOLS) > 3 else ''}")
    
    print(f"\n⏰ DATA COLLECTION:")
    print(f"   Interval: Every {COLLECTION_INTERVAL_MINUTES} minutes")
    print(f"   Granularity: {DATA_GRANULARITY}")
    print(f"   Historical: {HISTORICAL_DAYS} days")
    
    print(f"\n💾 STORAGE:")
    print(f"   Local: {'✅' if ENABLE_LOCAL_STORAGE else '❌'}")
    print(f"   S3 Cloud: {'✅' if ENABLE_S3_STORAGE else '❌'}")
    print(f"   Formats: {'JSON ' if SAVE_JSON_FORMAT else ''}{'Parquet ' if SAVE_PARQUET_FORMAT else ''}")
    
    print(f"\n📈 ANALYSIS:")
    print(f"   Technical Analysis: {'✅' if ENABLE_TECHNICAL_ANALYSIS else '❌'}")
    print(f"   Portfolio Tracking: {'✅' if ENABLE_PORTFOLIO_TRACKING else '❌'}")
    
    print(f"\n🔔 ALERTS:")
    print(f"   Price Alerts: {'✅' if PRICE_ALERT_THRESHOLD > 0 else '❌'} ({PRICE_ALERT_THRESHOLD}% threshold)")
    print(f"   Email Notifications: {'✅' if ENABLE_EMAIL_ALERTS else '❌'}")
    
    print(f"\n⚙️ SCHEDULE:")
    print(f"   Collection: {COLLECTION_SCHEDULE}")
    print(f"   Crypto Weekends: {'✅' if CRYPTO_WEEKEND_COLLECTION else '❌'}")
    print("=" * 60)

if __name__ == "__main__":
    """Run validation and show summary when file is executed directly"""
    print("Financial Trading ETL - User Configuration")
    print_user_config_summary()
    
    print("\n🔍 VALIDATING CONFIGURATION...")
    errors = validate_user_config()
    
    if errors:
        print("❌ Configuration Errors Found:")
        for error in errors:
            print(f"   - {error}")
    else:
        print("✅ Configuration is valid!")
    
    print(f"\n📝 To modify settings, edit: user_config.py")
    print(f"🔧 For advanced settings, see: config.py")