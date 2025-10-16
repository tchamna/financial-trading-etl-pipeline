# Power BI Setup Guide for Financial Trading Pipeline

## 📊 Overview
This guide will help you connect Power BI to your Snowflake data warehouse and create powerful financial dashboards.

---

## 🔌 Step 1: Install Snowflake Connector for Power BI

### Option A: Power BI Desktop (Recommended)
1. Open **Power BI Desktop**
2. Go to **File → Options and Settings → Options**
3. Navigate to **Security → Custom Data Connectors**
4. Check "Allow loading any extension without validation"
5. Restart Power BI Desktop

### Option B: Download ODBC Driver
If the native connector doesn't work:
1. Download **Snowflake ODBC Driver**: https://docs.snowflake.com/en/user-guide/odbc-download.html
2. Install the driver
3. Restart Power BI Desktop

---

## 🔗 Step 2: Connect to Snowflake

### Get Connection Details from Your Project:
```
Account: NRKCIJJ-RPC47451
User: (Your Snowflake username)
Password: (Your Snowflake password)
Warehouse: FINANCIAL_WH
Database: FINANCIAL_DB
Schema: CORE
```

### Connection Steps:
1. Open **Power BI Desktop**
2. Click **Get Data → More...**
3. Search for **"Snowflake"**
4. Select **Snowflake** connector
5. Enter connection details:
   - **Server**: `NRKCIJJ-RPC47451.snowflakecomputing.com`
   - **Warehouse**: `FINANCIAL_WH`
   - Click **OK**
6. Enter credentials:
   - **Username**: Your Snowflake username
   - **Password**: Your Snowflake password
7. Select **FINANCIAL_DB → CORE** schema
8. You'll see three tables:
   - ✅ **STOCK_DATA** (5,460+ rows)
   - ✅ **CRYPTO_MINUTE_DATA** (39,120+ rows)
   - ✅ **CRYPTO_DATA** (0 rows - for daily aggregates)

---

## 📊 Step 3: Import Data with Custom Queries

Instead of loading entire tables, use optimized queries for better performance.

### Query 1: Stock Data (Last 30 Days)
```sql
SELECT 
    symbol,
    timestamp,
    open_price,
    high_price,
    low_price,
    close_price,
    volume,
    source,
    
    -- Calculated fields
    (close_price - open_price) / open_price * 100 as price_change_pct,
    (high_price - low_price) / open_price * 100 as volatility_pct,
    
    -- Time dimensions
    DATE(timestamp) as trade_date,
    HOUR(timestamp) as trade_hour,
    MINUTE(timestamp) as trade_minute,
    DAYOFWEEK(timestamp) as day_of_week,
    DAYNAME(timestamp) as day_name,
    
    -- Session indicators (market hours)
    CASE 
        WHEN HOUR(timestamp) BETWEEN 9 AND 16 THEN 'Market Hours'
        WHEN HOUR(timestamp) < 9 THEN 'Pre-Market'
        ELSE 'After-Hours'
    END as trading_session
    
FROM FINANCIAL_DB.CORE.STOCK_DATA
WHERE timestamp >= DATEADD(day, -30, CURRENT_DATE())
ORDER BY symbol, timestamp
```

### Query 2: Crypto Data (Last 7 Days)
```sql
SELECT 
    symbol,
    timestamp,
    open,
    high,
    low,
    close,
    volume,
    api_source,
    interval,
    
    -- Calculated fields
    (close - open) / open * 100 as price_change_pct,
    (high - low) / open * 100 as volatility_pct,
    
    -- Time dimensions
    DATE(timestamp) as trade_date,
    HOUR(timestamp) as trade_hour,
    DAYOFWEEK(timestamp) as day_of_week,
    
    -- 24/7 market indicator
    CASE 
        WHEN DAYOFWEEK(timestamp) IN (1, 7) THEN 'Weekend'
        ELSE 'Weekday'
    END as day_type
    
FROM FINANCIAL_DB.CORE.CRYPTO_MINUTE_DATA
WHERE timestamp >= DATEADD(day, -7, CURRENT_DATE())
ORDER BY symbol, timestamp
```

### Query 3: Daily Aggregated Stock Performance
```sql
SELECT 
    symbol,
    DATE(timestamp) as trade_date,
    
    -- OHLCV
    MIN(CASE WHEN MINUTE(timestamp) = 0 AND HOUR(timestamp) = 9 THEN open_price END) as day_open,
    MAX(high_price) as day_high,
    MIN(low_price) as day_low,
    MAX(CASE WHEN MINUTE(timestamp) = 59 AND HOUR(timestamp) = 15 THEN close_price END) as day_close,
    SUM(volume) as day_volume,
    
    -- Daily calculations
    (MAX(CASE WHEN MINUTE(timestamp) = 59 AND HOUR(timestamp) = 15 THEN close_price END) - 
     MIN(CASE WHEN MINUTE(timestamp) = 0 AND HOUR(timestamp) = 9 THEN open_price END)) / 
     MIN(CASE WHEN MINUTE(timestamp) = 0 AND HOUR(timestamp) = 9 THEN open_price END) * 100 as daily_return_pct,
    
    STDDEV(close_price) as daily_volatility,
    COUNT(*) as minute_bars
    
FROM FINANCIAL_DB.CORE.STOCK_DATA
WHERE timestamp >= DATEADD(day, -90, CURRENT_DATE())
GROUP BY symbol, DATE(timestamp)
ORDER BY symbol, trade_date DESC
```

---

## 🎨 Step 4: Create DAX Measures

After importing data, create these calculated measures in Power BI:

### Price Measures
```dax
// Current Price
Current_Price = MAX(STOCK_DATA[close_price])

// Opening Price
Opening_Price = MIN(STOCK_DATA[open_price])

// Daily Return %
Daily_Return_Pct = 
DIVIDE(
    MAX(STOCK_DATA[close_price]) - MIN(STOCK_DATA[open_price]),
    MIN(STOCK_DATA[open_price])
) * 100

// Price Change (Dollar Amount)
Price_Change = MAX(STOCK_DATA[close_price]) - MIN(STOCK_DATA[open_price])
```

### Volume Measures
```dax
// Total Volume
Total_Volume = SUM(STOCK_DATA[volume])

// Average Volume
Avg_Volume = AVERAGE(STOCK_DATA[volume])

// Volume Z-Score (Unusual Volume Detection)
Volume_ZScore = 
VAR CurrentVolume = SUM(STOCK_DATA[volume])
VAR AvgVolume = CALCULATE(AVERAGE(STOCK_DATA[volume]), ALL(STOCK_DATA[timestamp]))
VAR StdDevVolume = CALCULATE(STDEV.P(STOCK_DATA[volume]), ALL(STOCK_DATA[timestamp]))
RETURN
    DIVIDE(CurrentVolume - AvgVolume, StdDevVolume)
```

### Technical Indicators
```dax
// Simple Moving Average (20 periods)
SMA_20 = 
CALCULATE(
    AVERAGE(STOCK_DATA[close_price]),
    WINDOW(
        -19, REL,
        0, REL,
        ORDERBY(STOCK_DATA[timestamp], ASC)
    )
)

// Exponential Moving Average (12 periods)
EMA_12 = 
VAR K = 2 / (12 + 1)
RETURN
    CALCULATE(
        SUMX(
            WINDOW(-11, REL, 0, REL, ORDERBY(STOCK_DATA[timestamp], ASC)),
            STOCK_DATA[close_price] * POWER(1 - K, [RowNum])
        ) / SUMX(
            WINDOW(-11, REL, 0, REL),
            POWER(1 - K, [RowNum])
        ),
        ADDCOLUMNS(
            WINDOW(-11, REL, 0, REL, ORDERBY(STOCK_DATA[timestamp], ASC)),
            "RowNum", ROWNUMBER(ORDERBY(STOCK_DATA[timestamp], ASC))
        )
    )

// Volatility (Standard Deviation)
Price_Volatility = STDEV.P(STOCK_DATA[close_price])

// RSI (14 periods - Simplified)
RSI_14 = 
VAR PriceChanges = 
    ADDCOLUMNS(
        WINDOW(-13, REL, 0, REL, ORDERBY(STOCK_DATA[timestamp], ASC)),
        "Change", STOCK_DATA[close_price] - EARLIER(STOCK_DATA[close_price])
    )
VAR AvgGain = AVERAGEX(FILTER(PriceChanges, [Change] > 0), [Change])
VAR AvgLoss = ABS(AVERAGEX(FILTER(PriceChanges, [Change] < 0), [Change]))
VAR RS = DIVIDE(AvgGain, AvgLoss, 50)
RETURN
    100 - (100 / (1 + RS))
```

### Conditional Formatting Measures
```dax
// Color by Performance (Green = Up, Red = Down)
Price_Color = 
IF(
    [Daily_Return_Pct] > 0,
    "Green",
    IF([Daily_Return_Pct] < 0, "Red", "Gray")
)

// Alert: Unusual Volume
Volume_Alert = 
IF(
    [Volume_ZScore] > 2,
    "🔴 High Volume Alert",
    IF([Volume_ZScore] < -2, "🔵 Low Volume Alert", "")
)

// Trend Indicator
Trend_Signal = 
SWITCH(
    TRUE(),
    [Current_Price] > [SMA_20], "📈 Uptrend",
    [Current_Price] < [SMA_20], "📉 Downtrend",
    "➡️ Neutral"
)
```

---

## 📈 Step 5: Create Dashboard Visualizations

### Dashboard 1: Executive Summary
**Visuals:**
1. **KPI Cards** (Top Row):
   - Current Price
   - Daily Change %
   - Total Volume
   - Number of Symbols

2. **Line Chart** (Main):
   - X-Axis: timestamp
   - Y-Axis: close_price
   - Legend: symbol
   - Add SMA_20 as second line

3. **Bar Chart** (Right):
   - X-Axis: symbol
   - Y-Axis: Daily_Return_Pct
   - Conditional formatting: Green/Red

4. **Table** (Bottom):
   - Columns: Symbol, Current Price, Daily Change %, Volume
   - Sort by: Daily Change % (descending)

### Dashboard 2: Technical Analysis
**Visuals:**
1. **Candlestick Chart** (Main):
   - Use custom visual: "Candlestick by MAQ Software"
   - Open: open_price
   - High: high_price
   - Low: low_price
   - Close: close_price

2. **Volume Bars** (Below candlestick):
   - X-Axis: timestamp
   - Y-Axis: volume
   - Color by price change

3. **Technical Indicators Panel**:
   - Gauge: RSI_14 (Overbought > 70, Oversold < 30)
   - Line: SMA_20, SMA_50
   - Card: Volatility

### Dashboard 3: Correlation Matrix
**Visuals:**
1. **Matrix Heatmap**:
   - Rows: symbol
   - Columns: symbol
   - Values: Correlation coefficient
   - Color scale: -1 (Red) to +1 (Green)

2. **Scatter Plot**:
   - X-Axis: Symbol 1 price change
   - Y-Axis: Symbol 2 price change
   - Play Axis: timestamp

---

## 🔄 Step 6: Set Up Data Refresh

### Scheduled Refresh (Import Mode)
1. Publish your report to **Power BI Service**
2. Go to **Workspace → Datasets → Settings**
3. Expand **Scheduled refresh**
4. Click **Add another time**
5. Set refresh schedule:
   - **Frequency**: Daily
   - **Times**: 7:00 AM, 1:00 PM, 7:00 PM (after Airflow runs at 6 AM, 12 PM, 6 PM)
6. **Time zone**: Your timezone
7. Click **Apply**

### DirectQuery (Real-time)
For live data (slower performance):
1. When connecting, choose **DirectQuery** instead of **Import**
2. Data will always be fresh, queries run on Snowflake
3. Best for: Real-time monitoring dashboards

### Hybrid (Recommended)
Best of both worlds:
1. Import historical data (older than today)
2. DirectQuery for today's data
3. Go to **Home → Transform data → Advanced Editor**
4. Add filter logic:
```m
let
    Source = Snowflake.Databases("NRKCIJJ-RPC47451.snowflakecomputing.com","FINANCIAL_WH"),
    FINANCIAL_DB = Source{[Name="FINANCIAL_DB"]}[Data],
    CORE = FINANCIAL_DB{[Name="CORE"]}[Data],
    
    // Import historical data
    HistoricalData = Sql.Database(..., "SELECT * FROM STOCK_DATA WHERE timestamp < CURRENT_DATE()"),
    
    // DirectQuery for today
    TodayData = Sql.Database(..., "SELECT * FROM STOCK_DATA WHERE timestamp >= CURRENT_DATE()", [Mode="DirectQuery"]),
    
    CombinedData = Table.Combine({HistoricalData, TodayData})
in
    CombinedData
```

---

## 🎯 Step 7: Performance Optimization Tips

### 1. **Use Query Folding**
- Let Snowflake do the heavy lifting
- Avoid complex Power Query transformations
- Push filtering, sorting, grouping to SQL

### 2. **Limit Date Range**
```sql
-- Instead of loading all data
WHERE timestamp >= DATEADD(day, -30, CURRENT_DATE())

-- Or use parameters
WHERE timestamp >= @StartDate AND timestamp < @EndDate
```

### 3. **Aggregations**
- Pre-aggregate data in SQL for summary views
- Use SUMMARIZE in DAX for further aggregation

### 4. **Incremental Refresh** (Power BI Premium)
1. Add RangeStart and RangeEnd parameters
2. Filter data: `timestamp >= RangeStart AND timestamp < RangeEnd`
3. Configure incremental refresh in dataset settings
4. Refresh only last 7 days, keep 90 days

---

## 📱 Step 8: Mobile Layout (Optional)

Create mobile-friendly dashboards:
1. Go to **View → Mobile layout**
2. Drag visuals to mobile canvas
3. Resize for phone screen
4. Prioritize: KPIs, top performers, alerts

---

## 🔒 Step 9: Row-Level Security (Optional)

If sharing with multiple users:
1. Go to **Modeling → Manage roles**
2. Create role: "StockViewer"
3. Add filter:
   ```dax
   [symbol] IN {"AAPL", "GOOGL", "MSFT"}
   ```
4. Test role before publishing

---

## 🚨 Troubleshooting

### Issue: "Cannot connect to Snowflake"
**Solution:**
- Check firewall/VPN settings
- Verify account name format: `NRKCIJJ-RPC47451.snowflakecomputing.com`
- Try using ODBC driver instead

### Issue: "Query timeout"
**Solution:**
- Reduce date range in WHERE clause
- Use DirectQuery instead of Import
- Increase Snowflake warehouse size

### Issue: "Slow refresh"
**Solution:**
- Enable query folding (check "View Native Query")
- Remove complex Power Query transformations
- Create Snowflake views for complex logic

### Issue: "Timestamp shows wrong timezone"
**Solution:**
- All timestamps are in UTC
- Convert in DAX:
  ```dax
  Local_Timestamp = [timestamp] + TIME(your_offset, 0, 0)
  ```

---

## 📚 Additional Resources

- **Power BI Documentation**: https://docs.microsoft.com/power-bi/
- **Snowflake Connector**: https://docs.snowflake.com/en/user-guide/power-bi
- **DAX Guide**: https://dax.guide/
- **Sample Reports**: See `/docs/sample_powerbi_reports/`

---

## ✅ Quick Start Checklist

- [ ] Install Power BI Desktop
- [ ] Install Snowflake connector/ODBC
- [ ] Connect to Snowflake (NRKCIJJ-RPC47451)
- [ ] Import Stock Data query (last 30 days)
- [ ] Import Crypto Data query (last 7 days)
- [ ] Create basic DAX measures (Price, Volume, Returns)
- [ ] Build Executive Summary dashboard
- [ ] Set up scheduled refresh (7 AM, 1 PM, 7 PM)
- [ ] Test on mobile device
- [ ] Publish to Power BI Service

---

**🎉 You're now ready to analyze your financial data in Power BI!**

For questions or issues, refer to the project documentation or Snowflake/Power BI support.
