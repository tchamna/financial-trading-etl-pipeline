-- Financial Trading Data Warehouse Schema
-- Snowflake DDL and DML for loading processed financial market data
-- Author: Shck Tchamna
-- Email: tchamna@gmail.com
-- Date: 2025

-- ========================================
-- DATABASE AND SCHEMA SETUP
-- ========================================

USE ROLE SYSADMIN;
USE WAREHOUSE FINANCIAL_WH;

-- Create database and schemas
CREATE DATABASE IF NOT EXISTS FINANCIAL_DB
    COMMENT = 'Financial trading data warehouse for market analytics';

CREATE SCHEMA IF NOT EXISTS FINANCIAL_DB.STAGING
    COMMENT = 'Staging area for raw financial data ingestion';

CREATE SCHEMA IF NOT EXISTS FINANCIAL_DB.CORE
    COMMENT = 'Core dimensional model for financial data';

CREATE SCHEMA IF NOT EXISTS FINANCIAL_DB.MARTS
    COMMENT = 'Data marts for business intelligence and analytics';

-- ========================================
-- STAGING TABLES
-- ========================================

USE SCHEMA FINANCIAL_DB.STAGING;

-- Staging table for stock data from S3
CREATE OR REPLACE TABLE STG_STOCK_DATA (
    load_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    file_name STRING,
    symbol STRING,
    timestamp TIMESTAMP_NTZ,
    open_price DECIMAL(18,4),
    high_price DECIMAL(18,4),
    low_price DECIMAL(18,4),
    close_price DECIMAL(18,4),
    volume INTEGER,
    sma_5 DECIMAL(18,4),
    sma_20 DECIMAL(18,4),
    sma_50 DECIMAL(18,4),
    price_change DECIMAL(18,4),
    price_change_pct DECIMAL(10,4),
    volatility_20d DECIMAL(18,4),
    golden_cross_signal STRING,
    death_cross_signal STRING
) COMMENT = 'Staging table for stock market data from Spark processing';

-- Staging table for cryptocurrency data
CREATE OR REPLACE TABLE STG_CRYPTO_DATA (
    load_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    file_name STRING,
    crypto_id STRING,
    symbol STRING,
    name STRING,
    current_price DECIMAL(18,8),
    market_cap BIGINT,
    total_volume BIGINT,
    price_change_24h DECIMAL(18,4),
    price_change_percentage_24h DECIMAL(10,4),
    market_cap_category STRING,
    last_updated TIMESTAMP_NTZ
) COMMENT = 'Staging table for cryptocurrency data';

-- ========================================
-- CORE DIMENSIONAL MODEL
-- ========================================

USE SCHEMA FINANCIAL_DB.CORE;

-- Asset Dimension (Type 2 SCD)
CREATE OR REPLACE TABLE DIM_ASSET (
    asset_key INTEGER AUTOINCREMENT PRIMARY KEY,
    asset_id INTEGER NOT NULL,
    asset_symbol STRING NOT NULL,
    asset_type STRING NOT NULL CHECK (asset_type IN ('Stock', 'Cryptocurrency')),
    asset_name STRING,
    base_currency STRING DEFAULT 'USD',
    sector STRING,
    industry STRING,
    market_exchange STRING,
    is_active BOOLEAN DEFAULT TRUE,
    valid_from TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    valid_to TIMESTAMP_NTZ DEFAULT '9999-12-31 23:59:59',
    created_date TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_date TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
) COMMENT = 'Type 2 slowly changing dimension for financial assets';

-- Time Dimension
CREATE OR REPLACE TABLE DIM_TIME (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL,
    timestamp TIMESTAMP_NTZ NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name STRING NOT NULL,
    week INTEGER NOT NULL,
    day INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_name STRING NOT NULL,
    hour INTEGER NOT NULL,
    is_weekend BOOLEAN NOT NULL,
    is_market_hours BOOLEAN NOT NULL,
    is_holiday BOOLEAN DEFAULT FALSE,
    fiscal_year INTEGER,
    fiscal_quarter INTEGER,
    created_date TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
) COMMENT = 'Time dimension with market hours and business calendar info';

-- Market Fact Table
CREATE OR REPLACE TABLE FACT_MARKET_DATA (
    fact_id INTEGER AUTOINCREMENT PRIMARY KEY,
    asset_key INTEGER NOT NULL,
    date_key INTEGER NOT NULL,
    timestamp TIMESTAMP_NTZ NOT NULL,
    open_price DECIMAL(18,8),
    high_price DECIMAL(18,8),
    low_price DECIMAL(18,8),
    close_price DECIMAL(18,8) NOT NULL,
    volume BIGINT,
    market_cap BIGINT,
    
    -- Technical indicators
    sma_5 DECIMAL(18,8),
    sma_20 DECIMAL(18,8),
    sma_50 DECIMAL(18,8),
    sma_200 DECIMAL(18,8),
    rsi_14 DECIMAL(10,4),
    macd DECIMAL(18,8),
    bollinger_upper DECIMAL(18,8),
    bollinger_lower DECIMAL(18,8),
    
    -- Price changes
    price_change DECIMAL(18,8),
    price_change_pct DECIMAL(10,4),
    volume_change_pct DECIMAL(10,4),
    
    -- Volatility measures
    volatility_20d DECIMAL(18,8),
    volatility_60d DECIMAL(18,8),
    
    -- Trading signals
    golden_cross_signal STRING,
    death_cross_signal STRING,
    rsi_signal STRING,
    
    -- Audit fields
    fact_type STRING NOT NULL CHECK (fact_type IN ('Stock', 'Cryptocurrency')),
    data_source STRING NOT NULL,
    load_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    -- Foreign key constraints
    FOREIGN KEY (asset_key) REFERENCES DIM_ASSET(asset_key),
    FOREIGN KEY (date_key) REFERENCES DIM_TIME(date_key)
) COMMENT = 'Fact table for market data with technical indicators and trading signals';

-- ========================================
-- DATA LOADING PROCEDURES
-- ========================================

-- Procedure to load asset dimension from S3
CREATE OR REPLACE PROCEDURE LOAD_ASSET_DIMENSION(
    S3_STAGE STRING
)
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
    records_inserted INTEGER DEFAULT 0;
    records_updated INTEGER DEFAULT 0;
BEGIN
    
    -- Create temporary table for S3 data
    CREATE OR REPLACE TEMPORARY TABLE temp_assets AS
    SELECT 
        asset_id,
        asset_symbol,
        asset_type,
        asset_name,
        base_currency,
        CURRENT_TIMESTAMP() as load_time
    FROM @FINANCIAL_DB.CORE.S3_STAGE/processed/dimensions/assets/;
    
    -- Type 2 SCD Logic - Close expired records
    UPDATE FINANCIAL_DB.CORE.DIM_ASSET 
    SET 
        valid_to = CURRENT_TIMESTAMP(),
        is_active = FALSE,
        updated_date = CURRENT_TIMESTAMP()
    WHERE asset_key IN (
        SELECT da.asset_key
        FROM FINANCIAL_DB.CORE.DIM_ASSET da
        JOIN temp_assets ta ON da.asset_id = ta.asset_id
        WHERE da.is_active = TRUE
        AND (
            da.asset_symbol != ta.asset_symbol OR
            da.asset_name != ta.asset_name OR
            da.base_currency != ta.base_currency
        )
    );
    
    GET DIAGNOSTICS records_updated = ROW_COUNT;
    
    -- Insert new and changed records
    INSERT INTO FINANCIAL_DB.CORE.DIM_ASSET (
        asset_id, asset_symbol, asset_type, asset_name, base_currency
    )
    SELECT 
        ta.asset_id,
        ta.asset_symbol,
        ta.asset_type,
        ta.asset_name,
        ta.base_currency
    FROM temp_assets ta
    LEFT JOIN FINANCIAL_DB.CORE.DIM_ASSET da 
        ON ta.asset_id = da.asset_id 
        AND da.is_active = TRUE
    WHERE da.asset_id IS NULL;
    
    GET DIAGNOSTICS records_inserted = ROW_COUNT;
    
    RETURN 'Assets loaded successfully. Inserted: ' || records_inserted || ', Updated: ' || records_updated;
    
EXCEPTION
    WHEN OTHER THEN
        RETURN 'Error loading assets: ' || SQLERRM;
END;
$$;

-- Procedure to load time dimension
CREATE OR REPLACE PROCEDURE LOAD_TIME_DIMENSION(
    S3_STAGE STRING
)
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
    records_inserted INTEGER DEFAULT 0;
BEGIN
    
    -- Insert new time records (ignore duplicates)
    INSERT INTO FINANCIAL_DB.CORE.DIM_TIME (
        date_key, full_date, timestamp, year, quarter, month, month_name,
        week, day, day_of_week, day_name, hour, is_weekend, is_market_hours
    )
    SELECT 
        date_key,
        DATE(timestamp) as full_date,
        timestamp,
        year,
        quarter,
        month,
        month_name,
        week,
        day,
        day_of_week,
        day_name,
        hour,
        is_weekend,
        is_market_hours
    FROM @FINANCIAL_DB.CORE.S3_STAGE/processed/dimensions/time/
    WHERE date_key NOT IN (SELECT date_key FROM FINANCIAL_DB.CORE.DIM_TIME);
    
    GET DIAGNOSTICS records_inserted = ROW_COUNT;
    
    RETURN 'Time dimension loaded successfully. Inserted: ' || records_inserted || ' records';
    
EXCEPTION
    WHEN OTHER THEN
        RETURN 'Error loading time dimension: ' || SQLERRM;
END;
$$;

-- Procedure to load market facts
CREATE OR REPLACE PROCEDURE LOAD_MARKET_FACTS(
    S3_STAGE STRING
)
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
    records_inserted INTEGER DEFAULT 0;
BEGIN
    
    -- Load market facts with proper joins to dimensions
    INSERT INTO FINANCIAL_DB.CORE.FACT_MARKET_DATA (
        asset_key, date_key, timestamp, open_price, high_price, low_price, 
        close_price, volume, sma_5, sma_20, sma_50, price_change, price_change_pct,
        volatility_20d, golden_cross_signal, death_cross_signal, fact_type, data_source
    )
    SELECT 
        da.asset_key,
        dt.date_key,
        mf.timestamp,
        mf.open_price,
        mf.high_price,
        mf.low_price,
        mf.close_price,
        mf.volume,
        mf.sma_5,
        mf.sma_20,
        mf.sma_50,
        mf.price_change,
        mf.price_change_pct,
        mf.volatility_20d,
        mf.golden_cross_signal,
        mf.death_cross_signal,
        mf.fact_type,
        'Spark_ETL_Pipeline' as data_source
    FROM @FINANCIAL_DB.CORE.S3_STAGE/processed/facts/market_data/ mf
    JOIN FINANCIAL_DB.CORE.DIM_ASSET da 
        ON mf.asset_id = da.asset_id 
        AND da.is_active = TRUE
    JOIN FINANCIAL_DB.CORE.DIM_TIME dt 
        ON mf.date_key = dt.date_key;
    
    GET DIAGNOSTICS records_inserted = ROW_COUNT;
    
    RETURN 'Market facts loaded successfully. Inserted: ' || records_inserted || ' records';
    
EXCEPTION
    WHEN OTHER THEN
        RETURN 'Error loading market facts: ' || SQLERRM;
END;
$$;

-- ========================================
-- DATA MARTS AND BUSINESS VIEWS
-- ========================================

USE SCHEMA FINANCIAL_DB.MARTS;

-- Daily market summary view
CREATE OR REPLACE VIEW VW_DAILY_MARKET_SUMMARY AS
SELECT 
    dt.full_date,
    da.asset_symbol,
    da.asset_type,
    da.asset_name,
    
    -- OHLC data
    MAX(CASE WHEN dt.hour = 9 THEN fmd.close_price END) as opening_price,
    MAX(fmd.high_price) as daily_high,
    MIN(fmd.low_price) as daily_low,
    MAX(CASE WHEN dt.hour = 16 THEN fmd.close_price END) as closing_price,
    
    -- Volume and market cap
    SUM(fmd.volume) as daily_volume,
    MAX(fmd.market_cap) as market_cap,
    
    -- Price changes
    MAX(CASE WHEN dt.hour = 16 THEN fmd.close_price END) - 
    MAX(CASE WHEN dt.hour = 9 THEN fmd.close_price END) as daily_price_change,
    
    ((MAX(CASE WHEN dt.hour = 16 THEN fmd.close_price END) - 
      MAX(CASE WHEN dt.hour = 9 THEN fmd.close_price END)) /
      MAX(CASE WHEN dt.hour = 9 THEN fmd.close_price END)) * 100 as daily_change_pct,
    
    -- Technical indicators (end of day)
    MAX(CASE WHEN dt.hour = 16 THEN fmd.sma_20 END) as sma_20_eod,
    MAX(CASE WHEN dt.hour = 16 THEN fmd.rsi_14 END) as rsi_14_eod,
    MAX(CASE WHEN dt.hour = 16 THEN fmd.volatility_20d END) as volatility_20d,
    
    -- Trading signals
    LISTAGG(DISTINCT fmd.golden_cross_signal, ',') as golden_cross_signals,
    LISTAGG(DISTINCT fmd.death_cross_signal, ',') as death_cross_signals,
    
    COUNT(*) as intraday_records
FROM FINANCIAL_DB.CORE.FACT_MARKET_DATA fmd
JOIN FINANCIAL_DB.CORE.DIM_ASSET da ON fmd.asset_key = da.asset_key
JOIN FINANCIAL_DB.CORE.DIM_TIME dt ON fmd.date_key = dt.date_key
WHERE dt.is_market_hours = TRUE
GROUP BY dt.full_date, da.asset_symbol, da.asset_type, da.asset_name;

-- Top performers view
CREATE OR REPLACE VIEW VW_TOP_PERFORMERS AS
SELECT 
    da.asset_symbol,
    da.asset_type,
    da.asset_name,
    fmd.close_price as current_price,
    fmd.price_change_pct as change_24h_pct,
    fmd.volume as volume_24h,
    fmd.market_cap,
    fmd.volatility_20d,
    
    -- Performance ranking
    ROW_NUMBER() OVER (PARTITION BY da.asset_type ORDER BY fmd.price_change_pct DESC) as performance_rank,
    
    -- Volume ranking
    ROW_NUMBER() OVER (PARTITION BY da.asset_type ORDER BY fmd.volume DESC) as volume_rank,
    
    fmd.timestamp as last_update
FROM FINANCIAL_DB.CORE.FACT_MARKET_DATA fmd
JOIN FINANCIAL_DB.CORE.DIM_ASSET da ON fmd.asset_key = da.asset_key
JOIN FINANCIAL_DB.CORE.DIM_TIME dt ON fmd.date_key = dt.date_key
WHERE dt.full_date = CURRENT_DATE()
AND fmd.timestamp = (
    SELECT MAX(timestamp) 
    FROM FINANCIAL_DB.CORE.FACT_MARKET_DATA fmd2 
    WHERE fmd2.asset_key = fmd.asset_key
);

-- Portfolio analytics view
CREATE OR REPLACE VIEW VW_PORTFOLIO_ANALYTICS AS
SELECT 
    da.asset_type,
    COUNT(DISTINCT da.asset_symbol) as total_assets,
    AVG(fmd.price_change_pct) as avg_change_pct,
    STDDEV(fmd.price_change_pct) as volatility,
    SUM(fmd.volume * fmd.close_price) as total_dollar_volume,
    
    -- Risk metrics
    PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY fmd.price_change_pct) as var_5pct,
    COUNT(CASE WHEN fmd.price_change_pct > 0 THEN 1 END) * 100.0 / COUNT(*) as win_rate,
    
    -- Technical analysis
    COUNT(CASE WHEN fmd.golden_cross_signal = 'BUY' THEN 1 END) as golden_cross_count,
    COUNT(CASE WHEN fmd.death_cross_signal = 'SELL' THEN 1 END) as death_cross_count,
    
    MAX(fmd.timestamp) as last_update
FROM FINANCIAL_DB.CORE.FACT_MARKET_DATA fmd
JOIN FINANCIAL_DB.CORE.DIM_ASSET da ON fmd.asset_key = da.asset_key
JOIN FINANCIAL_DB.CORE.DIM_TIME dt ON fmd.date_key = dt.date_key
WHERE dt.full_date >= CURRENT_DATE() - 30  -- Last 30 days
GROUP BY da.asset_type;

-- ========================================
-- INDEXES AND PERFORMANCE OPTIMIZATION
-- ========================================

-- Clustering keys for better query performance
ALTER TABLE FINANCIAL_DB.CORE.FACT_MARKET_DATA 
CLUSTER BY (date_key, asset_key);

ALTER TABLE FINANCIAL_DB.CORE.DIM_TIME 
CLUSTER BY (date_key);

-- ========================================
-- DATA QUALITY AND MONITORING
-- ========================================

-- Data quality checks
CREATE OR REPLACE VIEW VW_DATA_QUALITY_METRICS AS
SELECT 
    'FACT_MARKET_DATA' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN close_price IS NULL THEN 1 END) as null_prices,
    COUNT(CASE WHEN volume < 0 THEN 1 END) as negative_volumes,
    COUNT(CASE WHEN high_price < low_price THEN 1 END) as invalid_ohlc,
    MIN(timestamp) as earliest_record,
    MAX(timestamp) as latest_record,
    MAX(load_timestamp) as last_load_time
FROM FINANCIAL_DB.CORE.FACT_MARKET_DATA

UNION ALL

SELECT 
    'DIM_ASSET' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN asset_symbol IS NULL THEN 1 END) as null_symbols,
    0 as negative_volumes,
    0 as invalid_ohlc,
    MIN(created_date) as earliest_record,
    MAX(updated_date) as latest_record,
    MAX(updated_date) as last_load_time
FROM FINANCIAL_DB.CORE.DIM_ASSET;

-- ========================================
-- EXECUTE MAIN LOADING PROCEDURES
-- ========================================

-- Call procedures to load all data
CALL FINANCIAL_DB.CORE.LOAD_ASSET_DIMENSION('@FINANCIAL_DB.CORE.S3_STAGE');
CALL FINANCIAL_DB.CORE.LOAD_TIME_DIMENSION('@FINANCIAL_DB.CORE.S3_STAGE');
CALL FINANCIAL_DB.CORE.LOAD_MARKET_FACTS('@FINANCIAL_DB.CORE.S3_STAGE');

-- Verify data quality
SELECT * FROM FINANCIAL_DB.MARTS.VW_DATA_QUALITY_METRICS;