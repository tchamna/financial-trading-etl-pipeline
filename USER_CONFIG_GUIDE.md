# User Configuration Guide
## Simple Setup for Financial Trading ETL Pipeline

### 🎯 **Quick Start**

The pipeline now has **two configuration files**:
- **`user_config.py`** ← **YOU EDIT THIS ONE** (simple, user-friendly)
- **`config.py`** ← System configuration (advanced users only)

### 📝 **How to Customize Your Data Collection**

1. **Open `user_config.py` in any text editor**
2. **Modify the settings you want to change**
3. **Save the file**
4. **Run your pipeline** - it will automatically use your settings!

### 🔧 **Common Customizations**

#### **Change Which Stocks/Cryptos to Track**
```python
# Edit these lists in user_config.py
STOCK_SYMBOLS = [
    "AAPL",     # Apple
    "GOOGL",    # Google
    "TSLA",     # Tesla
    "YOUR_STOCK_HERE"  # Add any stock symbol
]

# 📈 40+ SUPPORTED CRYPTOCURRENCIES 📈
# Choose from these verified symbols (all APIs supported):

CRYPTO_SYMBOLS = [
    # === MAJOR CRYPTOCURRENCIES (Top 10 by Market Cap) ===
    "BTC",      # Bitcoin - The original cryptocurrency
    "ETH",      # Ethereum - Smart contract platform
    "USDT",     # Tether - Stablecoin
    "BNB",      # Binance Coin - Exchange token
    "SOL",      # Solana - High-performance blockchain
    "USDC",     # USD Coin - Regulated stablecoin
    "XRP",      # Ripple - Cross-border payments
    "DOGE",     # Dogecoin - Popular meme coin
    "ADA",      # Cardano - Proof-of-stake blockchain
    "TRX",      # Tron - Content sharing platform
    
    # === LAYER 1 BLOCKCHAINS ===
    "AVAX",     # Avalanche - Fast consensus protocol
    "DOT",      # Polkadot - Interoperability protocol
    "MATIC",    # Polygon - Ethereum scaling solution
    "ALGO",     # Algorand - Pure proof-of-stake
    "ATOM",     # Cosmos - Internet of blockchains
    "NEAR",     # NEAR Protocol - Developer-friendly blockchain
    "FTM",      # Fantom - High-speed blockchain
    
    # === DEFI TOKENS ===
    "UNI",      # Uniswap - Decentralized exchange
    "LINK",     # Chainlink - Oracle network
    "AAVE",     # Aave - Lending protocol
    "CRV",      # Curve - Stablecoin exchange
    "COMP",     # Compound - Lending protocol
    "SUSHI",    # SushiSwap - DEX and DeFi platform
    "1INCH",    # 1inch - DEX aggregator
    
    # === LEGACY/ESTABLISHED COINS ===
    "LTC",      # Litecoin - Silver to Bitcoin's gold
    "BCH",      # Bitcoin Cash - Bitcoin fork
    "ETC",      # Ethereum Classic - Original Ethereum
    "XMR",      # Monero - Privacy coin
    "ZEC",      # Zcash - Privacy coin
    "DASH",     # Dash - Digital cash
    
    # === LAYER 2 & SCALING SOLUTIONS ===
    "ARB",      # Arbitrum - Ethereum Layer 2
    "OP",       # Optimism - Ethereum Layer 2
    
    # === GAMING & NFT TOKENS ===
    "SAND",     # The Sandbox - Virtual world
    "MANA",     # Decentraland - Virtual reality platform
    "AXS",      # Axie Infinity - Play-to-earn game
    
    # === AI & TECHNOLOGY TOKENS ===
    "FET",      # Fetch.ai - AI and machine learning
    "RENDER",   # Render Token - Distributed GPU rendering
    
    # === MEME COINS (Popular Trading) ===
    "SHIB",     # Shiba Inu - Dogecoin competitor
    "PEPE",     # Pepe - Meme coin phenomenon
    
    # === EXCHANGE TOKENS ===
    "KCS",      # KuCoin Shares - KuCoin exchange token
    "CRO",      # Crypto.com Coin - Crypto.com token
]
```

#### **Change Collection Frequency**
```python
# Collect data every X minutes
COLLECTION_INTERVAL_MINUTES = 5    # Options: 1, 5, 15, 30, 60

# Data detail level
DATA_GRANULARITY = "1min"          # Options: "1min", "5min", "15min", "30min", "1hour", "1day"
```

#### **Change Storage Options**
```python
# Where to save your data
ENABLE_LOCAL_STORAGE = True        # Save files on your computer
ENABLE_S3_STORAGE = False          # Upload to AWS cloud (set to True if you have AWS)

# What formats to save
SAVE_JSON_FORMAT = True            # Human-readable format
SAVE_PARQUET_FORMAT = True         # Compressed format (recommended)
```

#### **Change Alert Settings**
```python
# Get notified when prices change dramatically
PRICE_ALERT_THRESHOLD = 10.0       # Alert if any asset moves more than 10%

# Email notifications
ENABLE_EMAIL_ALERTS = True
EMAIL_ADDRESSES = [
    "your_email@gmail.com"          # Add your email address
]
```

#### **Change Collection Schedule**
```python
# When to automatically collect data (cron format)
COLLECTION_SCHEDULE = "*/5 9-17 * * 1-5"  # Every 5 minutes during market hours (9 AM - 5 PM), weekdays

# Other examples:
# "0 9 * * 1-5"     = Once per day at 9 AM on weekdays
# "*/15 * * * *"    = Every 15 minutes, 24/7
# "0 */1 * * *"     = Every hour
```

### ✅ **Test Your Configuration**

After making changes, test your configuration:

```bash
# Check if your settings are valid
python user_config.py

# Test data collection with your settings
python scripts/crypto_minute_collector.py 2024-10-13
```

### 📊 **Example: Customize for Day Trading**

If you want to focus on day trading with frequent updates:

```python
# High-frequency collection
COLLECTION_INTERVAL_MINUTES = 1
DATA_GRANULARITY = "1min"

# Focus on volatile stocks
STOCK_SYMBOLS = ["TSLA", "GME", "AMC", "NVDA", "SPY"]
CRYPTO_SYMBOLS = ["BTC", "ETH", "SOL", "MATIC", "UNI", "LINK", "DOGE", "SHIB"]

# Lower alert threshold for more notifications
PRICE_ALERT_THRESHOLD = 5.0

# Collect during extended hours
COLLECTION_SCHEDULE = "*/1 6-20 * * 1-5"  # Every minute from 6 AM to 8 PM
```

### 📊 **Example: Customize for Long-term Investing**

If you want to track long-term investments:

```python
# Less frequent collection
COLLECTION_INTERVAL_MINUTES = 60
DATA_GRANULARITY = "1hour"

# Focus on blue-chip stocks
STOCK_SYMBOLS = ["AAPL", "MSFT", "GOOGL", "AMZN", "BRK-B", "JNJ", "PG"]
CRYPTO_SYMBOLS = ["BTC", "ETH", "AVAX", "DOT"]

# Higher alert threshold
PRICE_ALERT_THRESHOLD = 20.0

# Collect once per day
COLLECTION_SCHEDULE = "0 16 * * 1-5"  # Once per day at 4 PM (market close)
```

### 🆘 **Troubleshooting**

**Configuration Errors?**
```bash
python user_config.py  # This will show any configuration errors
```

**Pipeline Not Using Your Settings?**
1. Make sure you saved `user_config.py` after editing
2. Check for Python syntax errors (missing quotes, commas, etc.)
3. Restart your pipeline application

**Need Advanced Settings?**
- For database connections, API keys, and system settings, edit `config.py`
- See the main documentation for advanced configuration options

### 🎉 **That's It!**

Your pipeline will now automatically use your custom settings. The beauty of this system:

- ✅ **Simple**: Only edit what you need
- ✅ **Safe**: System settings stay protected in `config.py`  
- ✅ **Flexible**: Easy to experiment with different configurations
- ✅ **Powerful**: Still access to all advanced features when needed

Happy trading! 🚀