# Configuration Guide

## 📝 Where to Change Settings

### For Most Users: Use `user_config.py` ✅

**This is the ONLY file you should edit!** It contains all user settings in a simple, easy-to-understand format.

```python
# Example: Edit these values in user_config.py
STOCK_SYMBOLS = ["AAPL", "GOOGL", "MSFT"]
SAVE_PARQUET_FORMAT = True
COLLECTION_INTERVAL_MINUTES = 5
```

### Configuration Files Explained

| File | Purpose | Who Should Edit It | Contains |
|------|---------|-------------------|----------|
| **`user_config.py`** | User preferences | **👉 YOU!** | Symbols, intervals, storage, alerts |
| `config.json` | System config only | Developers/DevOps | API keys, DB credentials, technical settings |
| `config.py` | Configuration code | Developers only | Python code that loads configs |

### 🎯 No Duplicate Settings!

Each setting lives in **ONE place only**:
- User settings (symbols, intervals, storage formats) → **`user_config.py`** only
- Credentials and API keys → **`config.json`** only
- No confusion about which value is used!

## 🎯 Configuration Priority Order

The system loads settings in this order (later values override earlier ones):

1. **`config.json`** - Base system defaults
2. **`user_config.py`** - Your custom settings ⭐ (overrides config.json)
3. **Environment Variables** - Server/deployment settings (highest priority)

## 🔧 What You Can Change in `user_config.py`

### Symbols to Track
```python
STOCK_SYMBOLS = ["AAPL", "GOOGL", "MSFT", "TSLA"]
CRYPTO_SYMBOLS = ["BTC", "ETH", "SOL", "ADA"]
```

### Data Collection
```python
COLLECTION_INTERVAL_MINUTES = 5  # How often to collect data
HISTORICAL_DAYS = 30  # Days of historical data to fetch
```

### Storage Options
```python
ENABLE_LOCAL_STORAGE = True
ENABLE_S3_STORAGE = True
SAVE_JSON_FORMAT = True
SAVE_PARQUET_FORMAT = True  # ← You changed this to True!
```

### Analysis Features
```python
ENABLE_TECHNICAL_ANALYSIS = True
SIMPLE_MOVING_AVERAGES = [20, 50, 200]
ENABLE_PORTFOLIO_TRACKING = True
```

### Alerts
```python
PRICE_ALERT_THRESHOLD = 10.0  # Alert on 10% price change
ENABLE_EMAIL_ALERTS = True
EMAIL_ADDRESSES = ["your@email.com"]
```

## ✅ How to Apply Your Changes

1. Edit `user_config.py`
2. Save the file
3. Restart your pipeline/application

That's it! Your settings will automatically be loaded.

## 🔍 Verify Your Configuration

Run this command to see your current settings:

```bash
python user_config.py
```

This will show a summary and validate your configuration.

## ⚠️ Don't Edit These (Unless You're a Developer)

- `config.json` - Contains sensitive credentials and system defaults
- `config.py` - Advanced system configuration code

## 💡 Pro Tips

1. **Keep it simple**: Only change what you need in `user_config.py`
2. **Check the comments**: Each setting has helpful comments explaining what it does
3. **Validate first**: Run `python user_config.py` to check for errors before starting the pipeline
4. **Backup your changes**: Keep a copy of your customized `user_config.py`

## 🆘 Need Help?

If you're confused about a setting:
1. Check the comments in `user_config.py` - they explain each option
2. Look at the default values - they're good starting points
3. Run `python user_config.py` to validate your changes
