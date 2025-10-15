# Snowflake Integration Guide

## 🏔️ Overview

This guide will help you integrate Snowflake data warehouse with your Financial Trading ETL Pipeline.

---

## 📋 Prerequisites

1. **Snowflake Account**
   - Active Snowflake account
   - Account URL (e.g., `xyz12345.snowflakecomputing.com`)
   - Username and password

2. **Python Packages** (Already in requirements.txt)
   ```
   snowflake-connector-python==3.6.0
   snowflake-sqlalchemy==1.5.1
   ```

3. **Processed Data**
   - Financial data processed and stored in Parquet format
   - Either in local `data/` folder or in S3 bucket

---

## ⚙️ Configuration

### Step 1: Configure Snowflake Credentials

Edit `config.json` and add your Snowflake credentials:

```json
{
  "snowflake": {
    "account": "your-account.snowflakecomputing.com",
    "username": "your_username",
    "password": "your_password",
    "role": "SYSADMIN",
    "warehouse": "FINANCIAL_WH",
    "database": "FINANCIAL_DB",
    "schema": "CORE"
  }
}
```

**Finding your Snowflake account URL:**
- Log into Snowflake web UI
- Look at the URL: `https://xyz12345.snowflakecomputing.com`
- Your account is: `xyz12345.snowflakecomputing.com`

### Step 2: Enable Snowflake in User Config

Edit `user_config.py`:

```python
# Snowflake Data Warehouse settings
ENABLE_SNOWFLAKE = True            # Enable Snowflake integration
SNOWFLAKE_WAREHOUSE = "FINANCIAL_WH"  # Warehouse name
SNOWFLAKE_DATABASE = "FINANCIAL_DB"   # Database name
SNOWFLAKE_SCHEMA = "CORE"             # Schema name
SNOWFLAKE_LOAD_INTERVAL_MINUTES = 15  # Load frequency
```

---

## 🏗️ Setting Up Snowflake

### Option 1: Automatic Setup (Recommended)

The loader script will automatically create all required objects:

```bash
python scripts/snowflake_data_loader.py
```

This will:
- Create database `FINANCIAL_DB`
- Create schemas: `STAGING`, `CORE`, `MARTS`
- Create tables: `STOCK_DATA`, `CRYPTO_DATA`
- Load data from your data source

### Option 2: Manual Setup

Run the SQL script in Snowflake UI:

```bash
# Copy the SQL file to your clipboard or use SnowSQL
snowsql -a your-account -u your-username -f sql/snowflake_financial_schema.sql
```

---

## 📊 Database Schema

### Stock Data Table

```sql
FINANCIAL_DB.CORE.STOCK_DATA
├── symbol           (STRING)          -- Stock ticker
├── timestamp        (TIMESTAMP_NTZ)   -- Data timestamp
├── open_price       (DECIMAL)         -- Opening price
├── high_price       (DECIMAL)         -- High price
├── low_price        (DECIMAL)         -- Low price
├── close_price      (DECIMAL)         -- Closing price
├── volume           (INTEGER)         -- Trading volume
├── sma_20/50/200    (DECIMAL)         -- Moving averages
├── ema_12/26        (DECIMAL)         -- Exponential MAs
├── rsi              (DECIMAL)         -- RSI indicator
├── macd             (DECIMAL)         -- MACD indicator
└── load_timestamp   (TIMESTAMP_NTZ)   -- ETL load time
```

### Crypto Data Table

```sql
FINANCIAL_DB.CORE.CRYPTO_DATA
├── symbol              (STRING)          -- Crypto ticker
├── timestamp           (TIMESTAMP_NTZ)   -- Data timestamp
├── price_usd           (DECIMAL)         -- Price in USD
├── market_cap          (DECIMAL)         -- Market capitalization
├── volume_24h          (DECIMAL)         -- 24h volume
├── percent_change_1h   (DECIMAL)         -- 1h change %
├── percent_change_24h  (DECIMAL)         -- 24h change %
├── percent_change_7d   (DECIMAL)         -- 7d change %
├── sma_20/50           (DECIMAL)         -- Moving averages
└── load_timestamp      (TIMESTAMP_NTZ)   -- ETL load time
```

---

## 🚀 Loading Data

### Load Data Manually

```bash
python scripts/snowflake_data_loader.py
```

### Load Data from S3

If you have data in S3, the loader will automatically use the S3 external stage:

```bash
# Make sure S3 is configured in config.json
python scripts/snowflake_data_loader.py
```

### Load Data from Local Files

```bash
# Loader will read from data/ directory
python scripts/snowflake_data_loader.py
```

### Automated Loading with Airflow

The Airflow DAG (`dags/airflow_financial_pipeline.py`) includes a Snowflake loading task that runs every 15 minutes.

---

## 📈 Querying Your Data

### Basic Queries

```sql
-- Latest stock prices
SELECT symbol, timestamp, close_price, volume
FROM FINANCIAL_DB.CORE.STOCK_DATA
WHERE timestamp >= DATEADD(day, -7, CURRENT_TIMESTAMP())
ORDER BY timestamp DESC;

-- Top crypto by market cap
SELECT 
    symbol,
    MAX(market_cap) as max_market_cap,
    MAX(price_usd) as latest_price
FROM FINANCIAL_DB.CORE.CRYPTO_DATA
WHERE timestamp >= DATEADD(day, -1, CURRENT_TIMESTAMP())
GROUP BY symbol
ORDER BY max_market_cap DESC;

-- Moving average crossover signals
SELECT 
    symbol,
    timestamp,
    close_price,
    sma_20,
    sma_50,
    CASE 
        WHEN sma_20 > sma_50 THEN 'BULLISH'
        WHEN sma_20 < sma_50 THEN 'BEARISH'
        ELSE 'NEUTRAL'
    END as signal
FROM FINANCIAL_DB.CORE.STOCK_DATA
WHERE timestamp >= DATEADD(day, -30, CURRENT_TIMESTAMP())
ORDER BY timestamp DESC;
```

### Advanced Analytics

```sql
-- Daily returns analysis
SELECT 
    symbol,
    DATE(timestamp) as trade_date,
    AVG(close_price) as avg_price,
    SUM(volume) as total_volume,
    (MAX(close_price) - MIN(close_price)) / MIN(close_price) * 100 as daily_range_pct
FROM FINANCIAL_DB.CORE.STOCK_DATA
WHERE timestamp >= DATEADD(day, -30, CURRENT_TIMESTAMP())
GROUP BY symbol, DATE(timestamp)
ORDER BY trade_date DESC, symbol;

-- Volatility ranking
SELECT 
    symbol,
    AVG(volatility_20d) as avg_volatility,
    STDDEV(price_change_pct) as price_std_dev,
    RANK() OVER (ORDER BY AVG(volatility_20d) DESC) as volatility_rank
FROM FINANCIAL_DB.CORE.STOCK_DATA
WHERE timestamp >= DATEADD(day, -30, CURRENT_TIMESTAMP())
GROUP BY symbol
ORDER BY avg_volatility DESC;
```

---

## 🔄 Data Pipeline Flow

```
1. Data Collection (scripts/crypto_minute_collector.py)
   ↓
2. Data Processing (spark/financial_data_transformation.py)
   ↓
3. Storage (Local/S3 in Parquet format)
   ↓
4. Snowflake Loading (scripts/snowflake_data_loader.py)
   ↓
5. Analytics & BI Tools (Snowflake, Tableau, Power BI)
```

---

## 🔧 Troubleshooting

### Connection Issues

**Problem:** `Failed to connect to Snowflake`

**Solutions:**
1. Check credentials in `config.json`
2. Verify account URL format
3. Ensure network access (firewall, VPN)
4. Test with SnowSQL: `snowsql -a your-account -u your-username`

### Table Not Found

**Problem:** `Table STOCK_DATA does not exist`

**Solution:**
```bash
# Run the schema creation SQL
python scripts/snowflake_data_loader.py
```

### No Data Loaded

**Problem:** `0 rows loaded`

**Solutions:**
1. Check if processed data exists in `data/` folder
2. Verify Parquet files are valid
3. Check S3 bucket permissions if loading from S3
4. Run data collection first: `python scripts/crypto_minute_collector.py`

### Duplicate Data

**Problem:** `Duplicate key error`

**Solution:**
The loader automatically deduplicates data, but you can manually run:
```sql
-- Remove duplicates
DELETE FROM FINANCIAL_DB.CORE.STOCK_DATA
WHERE ROWID NOT IN (
    SELECT MIN(ROWID)
    FROM FINANCIAL_DB.CORE.STOCK_DATA
    GROUP BY symbol, timestamp
);
```

---

## 📊 Monitoring

### Check Load Status

```sql
-- Count records by date
SELECT 
    DATE(timestamp) as load_date,
    COUNT(*) as records,
    COUNT(DISTINCT symbol) as symbols
FROM FINANCIAL_DB.CORE.STOCK_DATA
GROUP BY DATE(timestamp)
ORDER BY load_date DESC;

-- Recent loads
SELECT 
    symbol,
    MAX(load_timestamp) as last_load,
    COUNT(*) as records
FROM FINANCIAL_DB.CORE.STOCK_DATA
WHERE load_timestamp >= DATEADD(hour, -1, CURRENT_TIMESTAMP())
GROUP BY symbol;
```

### Data Quality Checks

```sql
-- Check for nulls
SELECT 
    COUNT(*) as total_records,
    SUM(CASE WHEN close_price IS NULL THEN 1 ELSE 0 END) as null_prices,
    SUM(CASE WHEN volume IS NULL THEN 1 ELSE 0 END) as null_volumes
FROM FINANCIAL_DB.CORE.STOCK_DATA
WHERE timestamp >= DATEADD(day, -1, CURRENT_TIMESTAMP());

-- Check for outliers
SELECT symbol, timestamp, close_price
FROM FINANCIAL_DB.CORE.STOCK_DATA
WHERE price_change_pct > 50 OR price_change_pct < -50
ORDER BY timestamp DESC;
```

---

## 🔐 Security Best Practices

1. **Use Environment Variables**
   ```bash
   # Instead of hardcoding in config.json
   export SNOWFLAKE_PASSWORD="your_password"
   ```

2. **Use Key Pair Authentication** (Advanced)
   ```sql
   -- Generate key pair and configure in Snowflake
   ALTER USER your_username SET RSA_PUBLIC_KEY='MII...';
   ```

3. **Limit Permissions**
   ```sql
   -- Create read-only role for BI tools
   CREATE ROLE FINANCIAL_READER;
   GRANT USAGE ON WAREHOUSE FINANCIAL_WH TO ROLE FINANCIAL_READER;
   GRANT USAGE ON DATABASE FINANCIAL_DB TO ROLE FINANCIAL_READER;
   GRANT SELECT ON ALL TABLES IN SCHEMA FINANCIAL_DB.CORE TO ROLE FINANCIAL_READER;
   ```

4. **Use `.gitignore`**
   ```
   # Never commit credentials
   config.json
   .env
   ```

---

## 🎯 Next Steps

1. ✅ Configure Snowflake credentials
2. ✅ Enable Snowflake in user_config.py
3. ✅ Run snowflake_data_loader.py
4. ✅ Verify data loaded successfully
5. 📊 Connect BI tool (Tableau, Power BI, Looker)
6. 📈 Create dashboards and reports
7. 🔄 Schedule automated loads with Airflow

---

## 📚 Additional Resources

- [Snowflake Documentation](https://docs.snowflake.com/)
- [Snowflake Python Connector](https://docs.snowflake.com/en/user-guide/python-connector.html)
- [Loading Data into Snowflake](https://docs.snowflake.com/en/user-guide/data-load-overview.html)
- [Snowflake Best Practices](https://docs.snowflake.com/en/user-guide/ui-snowsight-best-practices.html)

---

## 🆘 Support

If you encounter issues:

1. Check logs: `logs/pipeline.log`
2. Run with verbose logging: `python -v scripts/snowflake_data_loader.py`
3. Test connection: `snowsql -a your-account -u your-username`
4. Review Snowflake query history in web UI

---

**Happy Analyzing! 📊🏔️**
