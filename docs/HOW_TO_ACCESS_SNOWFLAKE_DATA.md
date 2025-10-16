# 🎯 How to Access Your Data in Snowflake

## ✅ Your Data is Successfully Loaded!

**Location:** `FINANCIAL_DB.CORE.CRYPTO_MINUTE_DATA`  
**Rows:** 27,600 records  
**Date Range:** October 9-11, 2025  
**Symbols:** 8 cryptocurrencies (BTC, ETH, SOL, ADA, DOT, LINK, UNI, AVAX)

---

## 🌐 Method 1: Snowflake Web UI (Easiest)

### Step 1: Login to Snowflake
1. Go to: **https://app.snowflake.com/**
2. Enter your credentials:
   - **Account Identifier:** `NRKCIJJ-RPC47451`
   - **Username:** `tchamna`
   - **Password:** [Your Snowflake password]

### Step 2: Navigate to Worksheets
1. After logging in, click **"Worksheets"** in the left navigation menu
2. Click **"+ Worksheet"** to create a new worksheet

### Step 3: Set the Context
Copy and paste this into your worksheet:

```sql
-- Set the warehouse (compute resources)
USE WAREHOUSE FINANCIAL_WH;

-- Set the database
USE DATABASE FINANCIAL_DB;

-- Set the schema
USE SCHEMA CORE;
```

Click **"Run All"** or press `Ctrl+Enter`

### Step 4: Query Your Data

Now you can run queries! Try these:

#### See all your data (first 100 rows):
```sql
SELECT * 
FROM CRYPTO_MINUTE_DATA 
LIMIT 100;
```

#### Count records by symbol:
```sql
SELECT 
    symbol,
    COUNT(*) as total_records,
    MIN(timestamp) as earliest_data,
    MAX(timestamp) as latest_data
FROM CRYPTO_MINUTE_DATA
GROUP BY symbol
ORDER BY total_records DESC;
```

#### Get the latest data:
```sql
SELECT *
FROM CRYPTO_MINUTE_DATA
ORDER BY timestamp DESC
LIMIT 20;
```

#### See Bitcoin data only:
```sql
SELECT *
FROM CRYPTO_MINUTE_DATA
WHERE symbol = 'BITCOIN'
ORDER BY timestamp DESC
LIMIT 50;
```

---

## 💻 Method 2: SnowSQL Command Line

If you have SnowSQL installed, you can access it via terminal:

```bash
snowsql -a NRKCIJJ-RPC47451 -u tchamna

# Then run:
USE WAREHOUSE FINANCIAL_WH;
USE DATABASE FINANCIAL_DB;
USE SCHEMA CORE;

SELECT COUNT(*) FROM CRYPTO_MINUTE_DATA;
```

---

## 🐍 Method 3: Python (What We're Using)

Your pipeline is already using this method! Here's how it works:

```python
import snowflake.connector

conn = snowflake.connector.connect(
    user='tchamna',
    password='your_password',
    account='NRKCIJJ-RPC47451',
    warehouse='FINANCIAL_WH',
    database='FINANCIAL_DB',
    schema='CORE'
)

cursor = conn.cursor()
cursor.execute("SELECT * FROM CRYPTO_MINUTE_DATA LIMIT 10")
results = cursor.fetchall()

for row in results:
    print(row)

conn.close()
```

---

## 🗂️ Database Structure

Your Snowflake database has this structure:

```
FINANCIAL_DB (Database)
├── CORE (Schema) ← YOUR DATA IS HERE
│   ├── CRYPTO_MINUTE_DATA ✅ 27,600 rows
│   ├── CRYPTO_DATA (empty)
│   └── STOCK_DATA (empty)
├── PUBLIC (Schema) - empty
├── STAGING (Schema) - empty
└── MARTS (Schema) - empty
```

---

## 📊 Understanding Your Data

The `CRYPTO_MINUTE_DATA` table contains:

| Column | Description | Example |
|--------|-------------|---------|
| `timestamp` | When the data was recorded | 2025-10-11 23:59:00 |
| `symbol` | Cryptocurrency name | BITCOIN, ETHEREUM |
| `open` | Opening price | 62500.00 |
| `high` | Highest price in minute | 62600.00 |
| `low` | Lowest price in minute | 62400.00 |
| `close` | Closing price | 62550.00 |
| `volume` | Trading volume | 1234.56 |

---

## 🎨 Visualization Tools

You can connect these tools to visualize your data:

### Tableau
1. Click "Connect to Data"
2. Select "Snowflake"
3. Enter:
   - Server: `NRKCIJJ-RPC47451.snowflakecomputing.com`
   - Database: `FINANCIAL_DB`
   - Schema: `CORE`
   - Warehouse: `FINANCIAL_WH`

### Power BI
1. Get Data → Database → Snowflake
2. Server: `NRKCIJJ-RPC47451.snowflakecomputing.com`
3. Warehouse: `FINANCIAL_WH`
4. Database: `FINANCIAL_DB`

### Python with Pandas
```python
import snowflake.connector
import pandas as pd

conn = snowflake.connector.connect(...)
df = pd.read_sql("SELECT * FROM CRYPTO_MINUTE_DATA", conn)
df.plot(x='timestamp', y='close', kind='line')
```

---

## 🔍 Troubleshooting

### "I don't see the database"
- Make sure you selected **FINANCIAL_WH** as your warehouse
- Check that you're looking in **FINANCIAL_DB** database
- Verify you're in the **CORE** schema

### "Table not found"
- Run: `SHOW TABLES IN SCHEMA FINANCIAL_DB.CORE;`
- This will list all available tables

### "No data returned"
- The table has 27,600 rows confirmed
- Try: `SELECT COUNT(*) FROM CRYPTO_MINUTE_DATA;`
- If this returns 0, contact support

### "Warehouse not available"
- The warehouse auto-suspends when not in use
- It will auto-resume when you run a query (takes ~5 seconds)

---

## 📈 Next Steps

1. **Explore your data** - Run the sample queries above
2. **Create visualizations** - Connect Tableau or Power BI
3. **Monitor new data** - Your pipeline runs every 6 hours
4. **Join stock data** - Stock data will appear in the same table during market hours

---

## 🚀 Sample Analysis Queries

### Daily Average Price by Symbol:
```sql
SELECT 
    DATE(timestamp) as date,
    symbol,
    AVG(close) as avg_price,
    MIN(low) as daily_low,
    MAX(high) as daily_high
FROM CRYPTO_MINUTE_DATA
GROUP BY DATE(timestamp), symbol
ORDER BY date DESC, symbol;
```

### Price Volatility:
```sql
SELECT 
    symbol,
    STDDEV(close) as price_volatility,
    AVG(volume) as avg_volume
FROM CRYPTO_MINUTE_DATA
GROUP BY symbol
ORDER BY price_volatility DESC;
```

### Hourly Patterns:
```sql
SELECT 
    HOUR(timestamp) as hour_of_day,
    symbol,
    COUNT(*) as records,
    AVG(volume) as avg_volume
FROM CRYPTO_MINUTE_DATA
GROUP BY HOUR(timestamp), symbol
ORDER BY hour_of_day, symbol;
```

---

## ✅ Quick Reference

**Account:** NRKCIJJ-RPC47451  
**Username:** tchamna  
**Warehouse:** FINANCIAL_WH  
**Database:** FINANCIAL_DB  
**Schema:** CORE  
**Table:** CRYPTO_MINUTE_DATA  
**Rows:** 27,600

**Quick Query:**
```sql
USE WAREHOUSE FINANCIAL_WH;
SELECT * FROM FINANCIAL_DB.CORE.CRYPTO_MINUTE_DATA LIMIT 10;
```

---

**Need Help?** Your pipeline logs show successful data loads every 6 hours. Check Airflow UI at http://localhost:8080 for the latest runs!
