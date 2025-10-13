# Financial Trading Database - Data Access Guide

## Database Connection Information
- **Host:** localhost
- **Port:** 5432
- **Database:** financial_trading_db
- **Username:** postgres
- **Password:** deusiar

## Available Tables
1. **real_stock_data** - Live stock market data (AAPL, GOOGL, MSFT, TSLA, AMZN)
2. **real_crypto_data** - Cryptocurrency data (BTC, ETH, ADA, SOL, DOT)
3. **portfolio_positions** - Portfolio management data
4. **technical_analysis** - Technical indicators and analysis

## Python Connection Example
```python
import psycopg2
import pandas as pd

# Database connection
conn = psycopg2.connect(
    host='localhost',
    port='5432',
    database='financial_trading_db',
    user='postgres',
    password='deusiar'
)

# Load stock data
stock_df = pd.read_sql("SELECT * FROM real_stock_data", conn)
print(f"Stock records: {len(stock_df)}")

# Load crypto data  
crypto_df = pd.read_sql("SELECT * FROM real_crypto_data", conn)
print(f"Crypto records: {len(crypto_df)}")

conn.close()
```

## Direct SQL Connection
```bash
psql -h localhost -p 5432 -U postgres -d financial_trading_db
```

## Sample Queries for Data Scientists

### Stock Analysis
```sql
-- Top performing stocks by market cap
SELECT symbol, company_name, close_price, market_cap 
FROM real_stock_data 
ORDER BY market_cap DESC;

-- Stock price and volume analysis
SELECT symbol, close_price, volume, 
       (close_price * volume) as trading_value
FROM real_stock_data;
```

### Crypto Analysis
```sql
-- Crypto market rankings
SELECT name, symbol, current_price, market_cap_rank, 
       price_change_percentage_24h
FROM real_crypto_data 
ORDER BY market_cap_rank;

-- Top gainers/losers
SELECT name, symbol, price_change_percentage_24h
FROM real_crypto_data 
ORDER BY price_change_percentage_24h DESC;
```

## Tools & Integrations
- **Jupyter Notebooks:** Use psycopg2 + pandas for analysis
- **Power BI / Tableau:** Direct PostgreSQL connector
- **R:** RPostgreSQL package
- **DBeaver:** GUI database tool for exploration
- **pgAdmin:** Web-based PostgreSQL administration

## Data Formats Available
- **SQL Dump:** Complete database backup/restore
- **CSV Files:** Individual table exports for Excel/analysis
- **JSON:** API-friendly format for web applications

## Data Update Schedule
- **Real-time:** Live API connections
- **Batch Updates:** Every 15 minutes via ETL pipeline
- **Historical Data:** Stored with timestamps for trend analysis
