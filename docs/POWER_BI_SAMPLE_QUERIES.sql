-- =========================================================================
-- POWER BI SAMPLE QUERIES FOR FINANCIAL TRADING PIPELINE
-- =========================================================================
-- Copy these queries directly into Power BI's "Get Data → Snowflake → SQL"
-- =========================================================================

-- =========================================================================
-- QUERY 1: STOCK DATA - Last 30 Days (PRIMARY DASHBOARD)
-- =========================================================================
-- Use this for your main stock analysis dashboard
-- Returns: ~2,730 rows per day × 30 days = ~82,000 rows
-- =========================================================================

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
    (close_price - open_price) / NULLIF(open_price, 0) * 100 as price_change_pct,
    (high_price - low_price) / NULLIF(open_price, 0) * 100 as volatility_pct,
    
    -- Time dimensions (for grouping/filtering)
    DATE(timestamp) as trade_date,
    HOUR(timestamp) as trade_hour,
    MINUTE(timestamp) as trade_minute,
    DAYOFWEEK(timestamp) as day_of_week,
    DAYNAME(timestamp) as day_name,
    
    -- Trading session classification
    CASE 
        WHEN HOUR(timestamp) = 9 AND MINUTE(timestamp) < 30 THEN 'Market Open'
        WHEN HOUR(timestamp) BETWEEN 9 AND 15 THEN 'Regular Hours'
        WHEN HOUR(timestamp) = 15 AND MINUTE(timestamp) < 60 THEN 'Market Close'
        ELSE 'After Hours'
    END as trading_session
    
FROM FINANCIAL_DB.CORE.STOCK_DATA
WHERE timestamp >= DATEADD(day, -30, CURRENT_DATE())
ORDER BY symbol, timestamp;


-- =========================================================================
-- QUERY 2: CRYPTO DATA - Last 7 Days (24/7 MARKET)
-- =========================================================================
-- Use this for cryptocurrency analysis
-- Returns: ~11,520 rows per day × 7 days = ~80,000 rows
-- =========================================================================

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
    (close - open) / NULLIF(open, 0) * 100 as price_change_pct,
    (high - low) / NULLIF(open, 0) * 100 as volatility_pct,
    
    -- Time dimensions
    DATE(timestamp) as trade_date,
    HOUR(timestamp) as trade_hour,
    DAYOFWEEK(timestamp) as day_of_week,
    DAYNAME(timestamp) as day_name,
    
    -- Weekend vs Weekday (crypto-specific)
    CASE 
        WHEN DAYOFWEEK(timestamp) IN (1, 7) THEN 'Weekend'
        ELSE 'Weekday'
    END as day_type
    
FROM FINANCIAL_DB.CORE.CRYPTO_MINUTE_DATA
WHERE timestamp >= DATEADD(day, -7, CURRENT_DATE())
ORDER BY symbol, timestamp;


-- =========================================================================
-- QUERY 3: DAILY STOCK SUMMARY (AGGREGATED)
-- =========================================================================
-- Pre-aggregated daily data for faster performance
-- Use this for multi-month trend analysis
-- Returns: ~7 symbols × 90 days = ~630 rows
-- =========================================================================

SELECT 
    symbol,
    DATE(timestamp) as trade_date,
    
    -- Daily OHLCV
    FIRST_VALUE(open_price) OVER (PARTITION BY symbol, DATE(timestamp) ORDER BY timestamp) as day_open,
    MAX(high_price) as day_high,
    MIN(low_price) as day_low,
    LAST_VALUE(close_price) OVER (PARTITION BY symbol, DATE(timestamp) ORDER BY timestamp ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as day_close,
    SUM(volume) as day_volume,
    
    -- Daily metrics
    STDDEV(close_price) as intraday_volatility,
    COUNT(*) as minute_bars,
    
    -- Price range
    MAX(high_price) - MIN(low_price) as daily_range,
    (MAX(high_price) - MIN(low_price)) / NULLIF(FIRST_VALUE(open_price) OVER (PARTITION BY symbol, DATE(timestamp) ORDER BY timestamp), 0) * 100 as range_pct
    
FROM FINANCIAL_DB.CORE.STOCK_DATA
WHERE timestamp >= DATEADD(day, -90, CURRENT_DATE())
GROUP BY symbol, DATE(timestamp), timestamp
ORDER BY symbol, trade_date DESC;


-- =========================================================================
-- QUERY 4: TOP PERFORMERS - Last 24 Hours
-- =========================================================================
-- Quick summary of best/worst performers
-- Returns: ~7 rows (one per symbol)
-- =========================================================================

WITH price_changes AS (
    SELECT 
        symbol,
        FIRST_VALUE(close_price) OVER (PARTITION BY symbol ORDER BY timestamp) as start_price,
        LAST_VALUE(close_price) OVER (PARTITION BY symbol ORDER BY timestamp ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as end_price,
        SUM(volume) as total_volume,
        COUNT(*) as data_points
    FROM FINANCIAL_DB.CORE.STOCK_DATA
    WHERE timestamp >= DATEADD(hour, -24, CURRENT_TIMESTAMP())
    GROUP BY symbol, close_price, timestamp
)
SELECT DISTINCT
    symbol,
    start_price,
    end_price,
    (end_price - start_price) / NULLIF(start_price, 0) * 100 as change_pct,
    end_price - start_price as change_amount,
    total_volume,
    data_points
FROM price_changes
ORDER BY change_pct DESC;


-- =========================================================================
-- QUERY 5: INTRADAY VOLATILITY RANKING
-- =========================================================================
-- Find which symbols are most volatile (for day trading)
-- Returns: ~7 rows (one per symbol per day)
-- =========================================================================

SELECT 
    symbol,
    DATE(timestamp) as trade_date,
    
    -- Volatility metrics
    STDDEV(close_price) as price_stddev,
    MAX(high_price) - MIN(low_price) as price_range,
    (MAX(high_price) - MIN(low_price)) / NULLIF(AVG(close_price), 0) * 100 as normalized_range_pct,
    
    -- Price info
    AVG(close_price) as avg_price,
    MIN(low_price) as day_low,
    MAX(high_price) as day_high,
    
    -- Volume
    SUM(volume) as total_volume,
    AVG(volume) as avg_volume
    
FROM FINANCIAL_DB.CORE.STOCK_DATA
WHERE timestamp >= DATEADD(day, -7, CURRENT_DATE())
GROUP BY symbol, DATE(timestamp)
ORDER BY normalized_range_pct DESC;


-- =========================================================================
-- QUERY 6: HOUR-BY-HOUR TRADING PATTERN
-- =========================================================================
-- Analyze which hours have highest volume/volatility
-- Returns: ~7 symbols × 7 hours × 7 days = ~340 rows
-- =========================================================================

SELECT 
    symbol,
    HOUR(timestamp) as trading_hour,
    
    -- Aggregated metrics by hour
    AVG(close_price) as avg_price,
    AVG(volume) as avg_volume,
    STDDEV(close_price) as price_volatility,
    
    -- Price movement
    AVG((close_price - open_price) / NULLIF(open_price, 0) * 100) as avg_return_pct,
    
    -- Count
    COUNT(*) as minute_bars
    
FROM FINANCIAL_DB.CORE.STOCK_DATA
WHERE timestamp >= DATEADD(day, -7, CURRENT_DATE())
    AND HOUR(timestamp) BETWEEN 9 AND 16  -- Market hours only
GROUP BY symbol, HOUR(timestamp)
ORDER BY symbol, trading_hour;


-- =========================================================================
-- QUERY 7: CORRELATION DATA (For Heatmap)
-- =========================================================================
-- Calculate correlation between symbols
-- Note: Run this in Power BI with DAX for better performance
-- Returns: ~49 rows (7×7 matrix)
-- =========================================================================

WITH symbol_prices AS (
    SELECT 
        timestamp,
        symbol,
        close_price,
        (close_price - AVG(close_price) OVER (PARTITION BY symbol)) / 
            NULLIF(STDDEV(close_price) OVER (PARTITION BY symbol), 0) as z_score
    FROM FINANCIAL_DB.CORE.STOCK_DATA
    WHERE timestamp >= DATEADD(day, -30, CURRENT_DATE())
)
SELECT 
    a.symbol as symbol_1,
    b.symbol as symbol_2,
    CORR(a.z_score, b.z_score) as correlation
FROM symbol_prices a
CROSS JOIN symbol_prices b
WHERE a.timestamp = b.timestamp
GROUP BY a.symbol, b.symbol
ORDER BY a.symbol, b.symbol;


-- =========================================================================
-- QUERY 8: VOLUME ANOMALY DETECTION
-- =========================================================================
-- Detect unusual volume spikes (> 2 standard deviations)
-- Returns: Variable (only anomalies)
-- =========================================================================

WITH volume_stats AS (
    SELECT 
        symbol,
        AVG(volume) as avg_volume,
        STDDEV(volume) as stddev_volume
    FROM FINANCIAL_DB.CORE.STOCK_DATA
    WHERE timestamp >= DATEADD(day, -30, CURRENT_DATE())
    GROUP BY symbol
)
SELECT 
    s.symbol,
    s.timestamp,
    s.volume,
    s.close_price,
    vs.avg_volume,
    (s.volume - vs.avg_volume) / NULLIF(vs.stddev_volume, 0) as volume_z_score,
    
    CASE 
        WHEN (s.volume - vs.avg_volume) / NULLIF(vs.stddev_volume, 0) > 3 THEN '🔴 Extreme High'
        WHEN (s.volume - vs.avg_volume) / NULLIF(vs.stddev_volume, 0) > 2 THEN '🟠 High'
        WHEN (s.volume - vs.avg_volume) / NULLIF(vs.stddev_volume, 0) < -2 THEN '🔵 Low'
        ELSE '⚪ Normal'
    END as volume_alert
    
FROM FINANCIAL_DB.CORE.STOCK_DATA s
JOIN volume_stats vs ON s.symbol = vs.symbol
WHERE s.timestamp >= DATEADD(day, -7, CURRENT_DATE())
    AND ABS((s.volume - vs.avg_volume) / NULLIF(vs.stddev_volume, 0)) > 2
ORDER BY volume_z_score DESC;


-- =========================================================================
-- QUERY 9: MOVING AVERAGES (Pre-calculated for Speed)
-- =========================================================================
-- Calculate SMA and EMA for technical analysis
-- Returns: Same as Query 1, but with MA columns
-- =========================================================================

SELECT 
    symbol,
    timestamp,
    close_price,
    
    -- 20-period Simple Moving Average
    AVG(close_price) OVER (
        PARTITION BY symbol 
        ORDER BY timestamp 
        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) as sma_20,
    
    -- 50-period Simple Moving Average
    AVG(close_price) OVER (
        PARTITION BY symbol 
        ORDER BY timestamp 
        ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
    ) as sma_50,
    
    -- Volume moving average
    AVG(volume) OVER (
        PARTITION BY symbol 
        ORDER BY timestamp 
        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) as volume_ma_20,
    
    -- Trend signal
    CASE 
        WHEN close_price > AVG(close_price) OVER (
            PARTITION BY symbol 
            ORDER BY timestamp 
            ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
        ) THEN 'Above SMA20'
        ELSE 'Below SMA20'
    END as trend_position
    
FROM FINANCIAL_DB.CORE.STOCK_DATA
WHERE timestamp >= DATEADD(day, -30, CURRENT_DATE())
ORDER BY symbol, timestamp;


-- =========================================================================
-- QUERY 10: REAL-TIME LATEST PRICES
-- =========================================================================
-- Use with DirectQuery for live dashboard
-- Returns: ~7 rows (latest price for each symbol)
-- =========================================================================

WITH latest_prices AS (
    SELECT 
        symbol,
        timestamp,
        close_price,
        volume,
        ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY timestamp DESC) as rn
    FROM FINANCIAL_DB.CORE.STOCK_DATA
    WHERE timestamp >= DATEADD(hour, -2, CURRENT_TIMESTAMP())
)
SELECT 
    symbol,
    timestamp as last_update,
    close_price as current_price,
    volume as last_volume,
    
    -- Compare to 1 hour ago
    LAG(close_price, 60) OVER (PARTITION BY symbol ORDER BY timestamp) as price_1h_ago,
    (close_price - LAG(close_price, 60) OVER (PARTITION BY symbol ORDER BY timestamp)) / 
        NULLIF(LAG(close_price, 60) OVER (PARTITION BY symbol ORDER BY timestamp), 0) * 100 as change_1h_pct
    
FROM latest_prices
WHERE rn = 1
ORDER BY symbol;


-- =========================================================================
-- PARAMETER QUERIES (For Dynamic Date Ranges)
-- =========================================================================
-- In Power BI, create parameters: StartDate, EndDate
-- Then use them in WHERE clauses like this:
-- =========================================================================

-- Example with parameters:
/*
SELECT 
    symbol,
    timestamp,
    close_price,
    volume
FROM FINANCIAL_DB.CORE.STOCK_DATA
WHERE timestamp >= @StartDate 
    AND timestamp < @EndDate
ORDER BY symbol, timestamp;
*/


-- =========================================================================
-- NOTES:
-- =========================================================================
-- 1. All timestamps are in UTC timezone
-- 2. Market hours: 9:30 AM - 4:00 PM EST (14:30 - 21:00 UTC)
-- 3. Crypto data is 24/7 (including weekends)
-- 4. Stock data: Monday-Friday only (market days)
-- 5. Each stock has ~390 minutes of data per day
-- 6. Each crypto has ~1,440 minutes of data per day
--
-- Performance Tips:
-- - Use WHERE clause to limit date range
-- - Pre-aggregate data when possible
-- - Use Import mode for historical data
-- - Use DirectQuery only for real-time needs
-- - Create Snowflake views for complex queries
--
-- =========================================================================
