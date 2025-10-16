# 📊 Power BI Analysis Types Reference
## Complete Guide to Financial Market Analysis

---

## 🎯 Quick Navigation

| Analysis Type | Complexity | Time to Build | Business Value |
|--------------|------------|---------------|----------------|
| [Executive Summary](#1-executive-summary-dashboard) | ⭐ Easy | 15 min | ⭐⭐⭐⭐⭐ |
| [Intraday Trading](#2-intraday-trading-dashboard) | ⭐⭐ Medium | 30 min | ⭐⭐⭐⭐ |
| [Technical Analysis](#3-technical-analysis-dashboard) | ⭐⭐⭐ Hard | 60 min | ⭐⭐⭐⭐⭐ |
| [Correlation Matrix](#4-correlation-analysis) | ⭐⭐ Medium | 30 min | ⭐⭐⭐⭐ |
| [Risk & Volatility](#5-risk-volatility-dashboard) | ⭐⭐⭐ Hard | 45 min | ⭐⭐⭐⭐⭐ |
| [Crypto 24/7 Monitoring](#6-crypto-247-monitoring) | ⭐⭐ Medium | 30 min | ⭐⭐⭐⭐ |
| [Volume Analysis](#7-volume-anomaly-detection) | ⭐⭐ Medium | 25 min | ⭐⭐⭐ |
| [Predictive Analytics](#8-predictive-forecasting) | ⭐⭐⭐⭐ Expert | 90 min | ⭐⭐⭐⭐⭐ |

---

## 1. Executive Summary Dashboard
### 🎯 Purpose: High-level overview for management

### Visualizations:

**KPI Cards (Top Row):**
- Total Portfolio Value
- Daily Return %
- Best Performer (symbol + %)
- Worst Performer (symbol + %)
- Total Volume Traded
- Number of Symbols Tracked

**Main Chart (Center):**
- **Multi-line chart**: All stock/crypto prices over time
- X-axis: Timestamp (last 7 days)
- Y-axis: Close Price
- Legend: Symbol (color-coded)
- Tooltips: OHLC data

**Supporting Visuals:**
- **Bar Chart**: Top 5 performers by % change
- **Table**: All symbols ranked by return
- **Donut Chart**: Volume distribution by symbol
- **Gauge**: Portfolio vs benchmark performance

### DAX Measures Needed:
```dax
Portfolio Value = 
    SUMX(
        VALUES(STOCK_DATA[SYMBOL]),
        CALCULATE(MAX(STOCK_DATA[CLOSE_PRICE]))
    )

Daily Return = 
    VAR MaxClose = MAX(STOCK_DATA[CLOSE_PRICE])
    VAR MinOpen = MIN(STOCK_DATA[OPEN_PRICE])
    RETURN DIVIDE(MaxClose - MinOpen, MinOpen) * 100

Best Performer = 
    TOPN(1, 
        SUMMARIZE(STOCK_DATA, STOCK_DATA[SYMBOL], "Return", [Daily Return]),
        [Return], DESC
    )
```

### Interactivity:
- Date slicer (range selector)
- Symbol filter (multi-select dropdown)
- Click any chart to cross-filter all visuals

**Use Case:** Daily morning briefing, executive presentations

---

## 2. Intraday Trading Dashboard
### 🎯 Purpose: Real-time trading decisions

### Visualizations:

**Price Action (Main):**
- **Candlestick Chart**: 
  - Open/High/Low/Close for selected symbol
  - Color: Green (up), Red (down)
  - X-axis: Time (minute-by-minute)
  
**Volume Profile:**
- **Column Chart**: Volume by minute
- Sync with candlestick chart
- Highlight unusual volume spikes

**Market Hours Analysis:**
- **Area Chart**: Price movement across sessions
  - Pre-market (4-9:30 AM)
  - Regular hours (9:30 AM - 4 PM)
  - After-hours (4-8 PM)

**Price Levels:**
- **Line Chart with Reference Lines**:
  - Day's High (red dashed)
  - Day's Low (green dashed)
  - Opening price (blue dashed)
  - Current price (bold black)

### DAX Measures:
```dax
Intraday High = MAX(STOCK_DATA[HIGH_PRICE])
Intraday Low = MIN(STOCK_DATA[LOW_PRICE])
Opening Price = CALCULATE(
    FIRSTNONBLANK(STOCK_DATA[OPEN_PRICE], 1),
    FILTER(ALL(STOCK_DATA), STOCK_DATA[TRADE_HOUR] = 9)
)

Volume Z-Score = 
    VAR AvgVolume = AVERAGE(STOCK_DATA[VOLUME])
    VAR StdDev = STDEV.P(STOCK_DATA[VOLUME])
    RETURN DIVIDE([Total Volume] - AvgVolume, StdDev)
```

### Filters:
- Symbol selector (single-select)
- Time range slider (hour-by-hour)
- Trading session filter

**Use Case:** Active traders, day trading decisions

---

## 3. Technical Analysis Dashboard
### 🎯 Purpose: Technical indicators and signals

### Visualizations:

**Main Price Chart:**
- **Combo Chart**:
  - Candlesticks (primary axis)
  - SMA 20, 50, 200 (overlay lines)
  - Volume bars (secondary axis)

**Momentum Indicators:**
- **RSI Chart** (0-100 scale):
  - Overbought line (70)
  - Oversold line (30)
  - RSI value (line chart)

**MACD Indicator:**
- **Combo Chart**:
  - MACD line (blue)
  - Signal line (red)
  - Histogram (bars)

**Signal Table:**
| Symbol | Current Price | SMA20 | SMA50 | RSI | Signal |
|--------|--------------|-------|-------|-----|--------|
| AAPL   | $175.50      | ↑     | ↑     | 68  | BUY    |
| TSLA   | $265.30      | ↓     | ↑     | 35  | HOLD   |

### DAX Measures:
```dax
SMA_20 = 
    CALCULATE(
        AVERAGE(STOCK_DATA[CLOSE_PRICE]),
        DATESINPERIOD(STOCK_DATA[TIMESTAMP], LASTDATE(STOCK_DATA[TIMESTAMP]), -20, DAY)
    )

RSI_14 = 
    VAR GainDays = CALCULATE(
        AVERAGE(STOCK_DATA[PRICE_CHANGE]),
        STOCK_DATA[PRICE_CHANGE] > 0
    )
    VAR LossDays = CALCULATE(
        AVERAGE(STOCK_DATA[PRICE_CHANGE]),
        STOCK_DATA[PRICE_CHANGE] < 0
    )
    VAR RS = DIVIDE(GainDays, ABS(LossDays))
    RETURN 100 - (100 / (1 + RS))

Trading Signal = 
    SWITCH(TRUE(),
        [RSI_14] > 70, "SELL - Overbought",
        [RSI_14] < 30, "BUY - Oversold",
        [Current Price] > [SMA_50] && [SMA_20] > [SMA_50], "BUY - Bullish",
        [Current Price] < [SMA_50] && [SMA_20] < [SMA_50], "SELL - Bearish",
        "HOLD - Neutral"
    )
```

**Use Case:** Technical traders, swing trading strategies

---

## 4. Correlation Analysis
### 🎯 Purpose: Understand asset relationships

### Visualizations:

**Correlation Heatmap:**
- **Matrix Visual**:
  - Rows: Symbols
  - Columns: Symbols
  - Values: Correlation coefficient (-1 to 1)
  - Conditional formatting: Red (negative) to Green (positive)

**Scatter Plot:**
- Compare two symbols directly
- X-axis: Symbol 1 price change %
- Y-axis: Symbol 2 price change %
- Trend line showing correlation
- R² value displayed

**Correlation Over Time:**
- **Line Chart**: Rolling 30-day correlation
- Shows if relationships are stable or changing

### SQL Query for Correlation Data:
```sql
-- Correlation Matrix Data
WITH price_changes AS (
    SELECT 
        DATE(timestamp) as trade_date,
        symbol,
        (MAX(close_price) - MIN(open_price)) / MIN(open_price) * 100 as daily_return
    FROM FINANCIAL_DB.CORE.STOCK_DATA
    WHERE timestamp >= DATEADD(day, -30, CURRENT_DATE())
    GROUP BY DATE(timestamp), symbol
)
SELECT 
    a.symbol as symbol_1,
    b.symbol as symbol_2,
    CORR(a.daily_return, b.daily_return) as correlation
FROM price_changes a
JOIN price_changes b ON a.trade_date = b.trade_date
WHERE a.symbol <> b.symbol
GROUP BY a.symbol, b.symbol
```

**Use Case:** Portfolio diversification, hedge strategies

---

## 5. Risk & Volatility Dashboard
### 🎯 Purpose: Risk assessment and management

### Visualizations:

**Volatility Ranking:**
- **Bar Chart**: Symbols ranked by volatility
- Standard deviation of returns
- Color scale: High (red) to Low (green)

**Value at Risk (VaR):**
- **Gauge Chart**: Portfolio VaR
- 95% confidence level
- Estimated maximum loss

**Beta Analysis:**
- **Scatter Plot**: 
  - X-axis: Market return
  - Y-axis: Stock return
  - Slope = Beta
  - R² = Explained variance

**Risk-Return Profile:**
- **Bubble Chart**:
  - X-axis: Volatility (risk)
  - Y-axis: Return
  - Bubble size: Market cap or volume
  - Quadrants: Low-risk/High-return (ideal)

### DAX Measures:
```dax
Volatility_20D = STDEV.P(STOCK_DATA[RETURN_PCT])

Value_at_Risk = 
    VAR AvgReturn = AVERAGE(STOCK_DATA[RETURN_PCT])
    VAR StdDev = [Volatility_20D]
    RETURN AvgReturn - (1.65 * StdDev)  // 95% confidence

Sharpe_Ratio = 
    VAR RiskFreeRate = 0.05  // 5% annual
    VAR AvgReturn = AVERAGE(STOCK_DATA[RETURN_PCT])
    VAR StdDev = [Volatility_20D]
    RETURN DIVIDE(AvgReturn - RiskFreeRate, StdDev)

Beta = 
    DIVIDE(
        COVARIANCE.P(STOCK_DATA[RETURN_PCT], MARKET[RETURN_PCT]),
        VAR.P(MARKET[RETURN_PCT])
    )
```

**Use Case:** Risk managers, portfolio managers

---

## 6. Crypto 24/7 Monitoring
### 🎯 Purpose: Cryptocurrency market tracking

### Visualizations:

**24-Hour Price Movement:**
- **Line Chart**: Continuous (no market close)
- Highlight weekend vs weekday patterns
- Show volatility during different times

**Global Market Hours:**
- **Heat Map**: Activity by hour and timezone
  - Asia: 12 AM - 8 AM EST
  - Europe: 3 AM - 11 AM EST
  - US: 9 AM - 5 PM EST
  - After-hours: 5 PM - 12 AM EST

**Crypto vs Stock Comparison:**
- **Dual-axis Chart**:
  - Crypto prices (24/7 data)
  - Stock prices (market hours only)
  - Show correlation during overlap hours

**Weekend Performance:**
- **Table**: Crypto performance Sat-Sun
- Stock market closed comparison

### SQL Query:
```sql
-- Crypto 24/7 Activity Pattern
SELECT 
    HOUR(timestamp) as hour_of_day,
    DAYNAME(timestamp) as day_name,
    symbol,
    AVG(volume) as avg_volume,
    AVG((high - low) / low * 100) as avg_volatility,
    COUNT(*) as data_points
FROM FINANCIAL_DB.CORE.CRYPTO_MINUTE_DATA
WHERE timestamp >= DATEADD(day, -7, CURRENT_DATE())
GROUP BY HOUR(timestamp), DAYNAME(timestamp), symbol
ORDER BY hour_of_day
```

**Use Case:** Crypto traders, global market analysis

---

## 7. Volume Anomaly Detection
### 🎯 Purpose: Identify unusual trading activity

### Visualizations:

**Volume Z-Score:**
- **Column Chart**: Daily volume vs average
- Highlight bars where Z-score > 2 (unusual)
- Color code: Red (high), Blue (normal)

**Anomaly Table:**
| Date | Symbol | Volume | Avg Volume | Z-Score | Alert |
|------|--------|--------|------------|---------|-------|
| 10/14 | NVDA | 125M | 85M | 3.2 | 🔴 High |
| 10/14 | AAPL | 92M | 95M | -0.3 | 🟢 Normal |

**Volume Trend:**
- **Area Chart**: 30-day volume trend
- Moving average overlay
- Highlight spike days

**Price Impact Analysis:**
- **Scatter Plot**:
  - X-axis: Volume change %
  - Y-axis: Price change %
  - Identify volume-driven moves

### DAX Measures:
```dax
Volume_ZScore = 
    VAR AvgVolume = CALCULATE(
        AVERAGE(STOCK_DATA[VOLUME]),
        DATESINPERIOD(STOCK_DATA[TIMESTAMP], LASTDATE(STOCK_DATA[TIMESTAMP]), -30, DAY)
    )
    VAR StdDev = CALCULATE(
        STDEV.P(STOCK_DATA[VOLUME]),
        DATESINPERIOD(STOCK_DATA[TIMESTAMP], LASTDATE(STOCK_DATA[TIMESTAMP]), -30, DAY)
    )
    RETURN DIVIDE([Total Volume] - AvgVolume, StdDev)

Anomaly_Alert = 
    IF(
        ABS([Volume_ZScore]) > 2,
        "🔴 ALERT - Unusual Activity",
        "🟢 Normal"
    )
```

**Use Case:** Detect insider trading, news events, market manipulation

---

## 8. Predictive Forecasting
### 🎯 Purpose: Price predictions and trends

### Visualizations:

**Price Forecast:**
- **Line Chart with Forecast**:
  - Historical prices (solid line)
  - Predicted prices (dashed line)
  - Confidence interval (shaded area)
  - 7-day forecast

**Trend Strength:**
- **Gauge**: Trend confidence (0-100%)
- Bullish/Bearish indicator
- Based on recent patterns

**Pattern Recognition:**
- **Table**: Detected patterns
  - Head & Shoulders
  - Double Top/Bottom
  - Triangles
  - Breakouts

**Seasonality Analysis:**
- **Heat Map**: Performance by day/month
- Identify recurring patterns
- Best/worst trading days

### Advanced Analytics (Python/R Integration):

```python
# In Power BI Python visual
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

# Fit ARIMA model
model = ARIMA(dataset['CLOSE_PRICE'], order=(1,1,1))
model_fit = model.fit()

# Forecast next 7 days
forecast = model_fit.forecast(steps=7)
```

**Use Case:** Algorithmic trading, investment planning

---

## 📊 Dashboard Design Best Practices

### Layout Principles:

**1. F-Pattern Layout:**
```
[KPI Cards across top row]
[Main chart - largest visual]
[Supporting charts below]
[Detailed table at bottom]
```

**2. Color Scheme:**
- Green: Positive returns, buy signals
- Red: Negative returns, sell signals
- Blue: Neutral, informational
- Yellow: Warnings, alerts

**3. Mobile-First:**
- Design for phone layout
- Stack verticals on mobile
- Larger touch targets
- Simplified tables

**4. Performance:**
- Limit to 15-20 visuals per page
- Use aggregations where possible
- Avoid nested calculations
- DirectQuery for large datasets

---

## 🎯 Recommended Implementation Order

### Week 1: Foundation
1. ✅ Executive Summary (Day 1-2)
2. ✅ Intraday Trading (Day 3-4)
3. ✅ Basic filters and slicers (Day 5)

### Week 2: Technical
4. ✅ Technical Analysis (Day 1-3)
5. ✅ Volume Analysis (Day 4-5)

### Week 3: Advanced
6. ✅ Correlation Analysis (Day 1-2)
7. ✅ Risk & Volatility (Day 3-4)
8. ✅ Crypto 24/7 Monitoring (Day 5)

### Week 4: Predictive
9. ✅ Forecasting (Day 1-3)
10. ✅ Refinements and polish (Day 4-5)

---

## 💡 Pro Tips

### Performance Optimization:
- Use **aggregated tables** for historical data
- Implement **incremental refresh** (last 7 days only)
- Enable **query folding** for Snowflake operations
- Use **DirectQuery** for real-time, **Import** for historical

### Data Refresh Strategy:
```
Airflow runs: 12 AM, 6 AM, 12 PM, 6 PM (every 6 hours)
Power BI refresh: 7 AM, 1 PM, 7 PM (1 hour after data collection)
```

### Mobile Optimization:
- Create dedicated mobile layouts
- Use **phone portrait** layout mode
- Simplify visuals (fewer on mobile)
- Test on actual devices

---

## 📚 Next Steps

1. **Start with Quick Start Guide:** `POWER_BI_QUICK_START.md`
2. **Review SQL Queries:** `POWER_BI_SAMPLE_QUERIES.sql`
3. **Check Data Status:** Run `check_snowflake_timestamps.py`
4. **Build Dashboard:** Follow Week 1 plan above
5. **Iterate:** Add complexity based on feedback

**Remember:** Start simple, validate with stakeholders, then add complexity!

---

## 🆘 Support Resources

- Main Setup Guide: `docs/POWER_BI_SETUP_GUIDE.md`
- Sample Queries: `docs/POWER_BI_SAMPLE_QUERIES.sql`
- Project Summary: `docs/COMPLETION_SUMMARY.md`
- Troubleshooting: Check main setup guide Section 9

**Happy Analyzing! 📊🚀**
