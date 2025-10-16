# 🚀 Power BI Quick Start Guide
## From Zero to Your First Dashboard in 30 Minutes

---

## ✅ Prerequisites Checklist

Before starting, make sure you have:
- [x] Power BI Desktop installed ([Download here](https://powerbi.microsoft.com/desktop/))
- [x] Snowflake account with data loaded (You have 10,920 stock + 11,520 crypto records)
- [x] Snowflake connection details:
  - Account: `NRKCIJJ-RPC47451.snowflakecomputing.com`
  - Warehouse: `FINANCIAL_WH`
  - Database: `FINANCIAL_DB`
  - Schema: `CORE`

---

## 📋 STEP 1: Connect to Snowflake (5 minutes)

### 1.1 Open Power BI Desktop
- Launch Power BI Desktop
- Click **Home** → **Get Data** → **More...**

### 1.2 Connect to Snowflake
1. Search for "Snowflake" in the connector list
2. Click **Connect**
3. Enter connection details:
   ```
   Server: NRKCIJJ-RPC47451.snowflakecomputing.com
   Warehouse: FINANCIAL_WH
   ```
4. Click **OK**
5. Select **Database** authentication
6. Enter your Snowflake username and password
7. Click **Connect**

### 1.3 Navigate to Your Data
1. Expand `FINANCIAL_DB` → `CORE`
2. You'll see three tables:
   - ✅ `STOCK_DATA` (10,920 records)
   - ✅ `CRYPTO_DATA` (0 records - not used for minute data)
   - ✅ `CRYPTO_MINUTE_DATA` (11,520 records)

---

## 📊 STEP 2: Import Your First Dataset (5 minutes)

### Option A: Quick Start - Last 7 Days Stock Data

**Copy this query into Power BI:**

```sql
-- Quick Start: 7 Days of Stock Data
SELECT 
    SYMBOL,
    TIMESTAMP,
    OPEN_PRICE,
    HIGH_PRICE,
    LOW_PRICE,
    CLOSE_PRICE,
    VOLUME,
    
    -- Time Dimensions
    DATE(TIMESTAMP) as TRADE_DATE,
    HOUR(TIMESTAMP) as TRADE_HOUR,
    DAYOFWEEK(TIMESTAMP) as DAY_OF_WEEK,
    DAYNAME(TIMESTAMP) as DAY_NAME,
    
    -- Calculated Fields
    (CLOSE_PRICE - OPEN_PRICE) as PRICE_CHANGE,
    ROUND(((CLOSE_PRICE - OPEN_PRICE) / OPEN_PRICE) * 100, 2) as RETURN_PCT,
    (HIGH_PRICE - LOW_PRICE) as DAILY_RANGE,
    
    -- Trading Session
    CASE 
        WHEN HOUR(TIMESTAMP) BETWEEN 9 AND 16 THEN 'Market Hours'
        WHEN HOUR(TIMESTAMP) < 9 THEN 'Pre-Market'
        ELSE 'After-Hours'
    END as TRADING_SESSION

FROM FINANCIAL_DB.CORE.STOCK_DATA
WHERE TIMESTAMP >= DATEADD(day, -7, CURRENT_DATE())
ORDER BY TIMESTAMP DESC
```

**Expected Result:** ~7,560 rows (7 symbols × 1,080 minutes/day)

### How to Use This Query:

1. In Power BI, instead of selecting a table, click **Advanced options**
2. Paste the SQL query above into the **SQL statement** box
3. Click **OK**
4. Wait for data to load (should take 10-30 seconds)
5. Click **Load** (NOT "Transform Data" yet)

---

## 🎨 STEP 3: Create Your First Dashboard (20 minutes)

### 3.1 Create KPI Cards (5 minutes)

**A. Latest Apple Stock Price**
1. Click **Visualizations** → **Card** icon
2. Drag `CLOSE_PRICE` to **Fields**
3. Click dropdown on `CLOSE_PRICE` → **Maximum**
4. Add filter: `SYMBOL` = "AAPL"
5. Resize and position at top-left

**Repeat for:**
- B. Daily Return % (use `RETURN_PCT` → Average)
- C. Total Volume (use `VOLUME` → Sum)
- D. Day's High Price (use `HIGH_PRICE` → Maximum)

**Your screen should now have 4 KPI cards at the top!**

### 3.2 Create Price Line Chart (5 minutes)

1. Click **Line Chart** icon in Visualizations
2. **X-axis**: Drag `TIMESTAMP`
3. **Y-axis**: Drag `CLOSE_PRICE`
4. **Legend**: Drag `SYMBOL`
5. Resize to fill center of page

**🎯 What you see:** All 7 stock prices over time, color-coded by symbol

### 3.3 Create Volume Bar Chart (5 minutes)

1. Click **Clustered Bar Chart** icon
2. **Y-axis**: Drag `SYMBOL`
3. **X-axis**: Drag `VOLUME` (ensure it's SUM)
4. **Data labels**: Turn ON
5. Position below the line chart

**🎯 What you see:** Trading volume comparison across all symbols

### 3.4 Create Top Performers Table (5 minutes)

1. Click **Table** icon in Visualizations
2. Add columns in this order:
   - `SYMBOL`
   - `CLOSE_PRICE` (Maximum)
   - `RETURN_PCT` (Average)
   - `VOLUME` (Sum)
3. Click on `RETURN_PCT` header → **Sort Descending**
4. Position on the right side

**🎯 What you see:** Ranked list of stocks by performance

---

## 🎉 CONGRATULATIONS! Your First Dashboard is Complete!

You now have:
- ✅ 4 KPI cards showing key metrics
- ✅ Interactive line chart showing price trends
- ✅ Volume comparison bar chart
- ✅ Top performers ranking table

### 💡 Try This:
- Click on a symbol in the legend → Watch all visuals filter to that stock!
- Click on a bar in the volume chart → Everything updates!
- This is the power of **interactive filtering** in Power BI

---

## 🚀 NEXT STEPS (After Your First Dashboard)

### Immediate Enhancements (Today):

**1. Add Date Slicer**
- Insert → **Slicer** visualization
- Add `TRADE_DATE` field
- Change to **Between** mode in Format pane
- Now you can filter by date range!

**2. Add Symbol Filter**
- Insert → **Slicer**
- Add `SYMBOL` field
- Format as dropdown or tiles
- Select specific stocks to analyze

**3. Add Conditional Formatting**
- In the table, select `RETURN_PCT` column
- Home → **Conditional Formatting** → **Background Color**
- Set rule: Red for negative, Green for positive

### This Week:

**4. Add Crypto Data**
Import crypto data using this query:
```sql
SELECT 
    SYMBOL,
    TIMESTAMP,
    OPEN,
    HIGH,
    LOW,
    CLOSE,
    VOLUME
FROM FINANCIAL_DB.CORE.CRYPTO_MINUTE_DATA
WHERE TIMESTAMP >= DATEADD(day, -7, CURRENT_DATE())
```

**5. Create Second Page**
- Add new page: **Technical Analysis**
- Include candlestick charts
- Add moving average lines
- Show RSI indicators

**6. Set Up Scheduled Refresh**
- Publish to Power BI Service
- Configure refresh: After Airflow runs (12 AM, 6 AM, 12 PM, 6 PM)
- Your dashboard auto-updates!

### Advanced (Next Week):

**7. Add DAX Measures**
Create calculated metrics:
```dax
Current Price = MAX(STOCK_DATA[CLOSE_PRICE])
Daily Return % = DIVIDE(
    MAX(STOCK_DATA[CLOSE_PRICE]) - MIN(STOCK_DATA[OPEN_PRICE]),
    MIN(STOCK_DATA[OPEN_PRICE])
) * 100
```

**8. Create Drill-Through Pages**
- Detail page for each symbol
- Right-click → Drill through
- See deep analysis of individual stocks

**9. Add Tooltips**
- Custom tooltips showing:
  - Mini candlestick chart
  - Volume trend
  - Technical indicators

---

## 📚 Learning Resources

### Official Documentation:
- [Power BI Documentation](https://docs.microsoft.com/power-bi/)
- [DAX Functions Reference](https://dax.guide/)
- [Snowflake Connector Guide](https://docs.snowflake.com/en/user-guide/ecosystem-powerbi)

### Video Tutorials:
- [Power BI for Beginners](https://www.youtube.com/watch?v=AGrl-H87pRU) (2 hours)
- [Financial Dashboard in Power BI](https://www.youtube.com/results?search_query=power+bi+financial+dashboard)
- [DAX in 20 Minutes](https://www.youtube.com/watch?v=N7PECiKT9qo)

### Sample Dashboards:
- [Power BI Gallery](https://community.powerbi.com/t5/Data-Stories-Gallery/bd-p/DataStoriesGallery)
- Financial Templates: Search "stock market" in Power BI Service

---

## 🆘 Troubleshooting

### Issue 1: Connection Timeout
**Problem:** Query takes too long  
**Solution:** 
- Reduce date range (last 3 days instead of 7)
- Use DirectQuery instead of Import mode
- Add WHERE clause to filter symbols

### Issue 2: Data Not Updating
**Problem:** Dashboard shows old data  
**Solution:**
- Click **Home** → **Refresh**
- Check Airflow ran successfully
- Verify Snowflake has new data

### Issue 3: Wrong Timezone
**Problem:** Times don't match your timezone  
**Solution:**
- Add timezone conversion in SQL:
```sql
CONVERT_TIMEZONE('America/New_York', TIMESTAMP) as LOCAL_TIME
```

### Issue 4: Out of Memory
**Problem:** Power BI Desktop crashes  
**Solution:**
- Reduce data volume (fewer days or symbols)
- Use aggregations (hourly instead of minute data)
- Switch to DirectQuery mode

---

## 🎯 Success Metrics

After completing this guide, you should have:

- ✅ Power BI Desktop installed and connected to Snowflake
- ✅ First dashboard with 4 visualizations (cards, line, bar, table)
- ✅ Understanding of Import vs DirectQuery
- ✅ Basic interactivity (click-to-filter)
- ✅ Data refreshing from Snowflake
- ✅ Confidence to build more complex dashboards

**Time Investment:** 30 minutes initial setup, then 15 min/day to refine

---

## 💬 Need Help?

1. **Check the main guide:** `docs/POWER_BI_SETUP_GUIDE.md`
2. **Review sample queries:** `docs/POWER_BI_SAMPLE_QUERIES.sql`
3. **Verify data:** Run `utilities/setup/check_snowflake_timestamps.py`
4. **Community:** [Power BI Community Forums](https://community.powerbi.com/)

---

## 🎊 You're Ready!

You now have everything you need to start building professional financial dashboards. 

**Remember:** Start simple, iterate, and add complexity gradually. Your first dashboard doesn't need to be perfect—it just needs to show insights!

**Good luck! 🚀📊**
