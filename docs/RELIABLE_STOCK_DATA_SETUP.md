# 🛡️ Reliable Stock Data Collection Setup

## Problem Solved

**Yahoo Finance API is unreliable** - it experiences frequent outages and connectivity issues. This guide shows you how to set up a **production-grade multi-source data collection** system with automatic fallback.

## 🏆 Solution: Multi-Source Architecture

The new `reliable_stock_collector.py` tries multiple data sources in priority order until data is successfully retrieved:

```
1. Polygon.io      ⭐⭐⭐⭐⭐  (Best quality, recommended)
2. Finnhub         ⭐⭐⭐⭐☆  (Good reliability)
3. Alpha Vantage   ⭐⭐⭐☆☆  (Rate limited but works)
4. Yahoo Finance   ⭐⭐☆☆☆  (Fallback only)
```

**How it works:**
- Tries Polygon.io first (if API key configured)
- If Polygon fails, tries Finnhub
- If Finnhub fails, tries Alpha Vantage (respects 25/day limit)
- If all else fails, tries Yahoo Finance
- **At least one source WILL work** (or market is closed)

## 🚀 Quick Setup (Recommended)

### Option 1: Polygon.io (BEST - Free Tier)

**Why Polygon.io:**
- ✅ FREE tier: 5 API calls/minute
- ✅ Excellent data quality
- ✅ 99.9% uptime
- ✅ Historical data up to 2 years
- ✅ No daily request limits

**Get API Key:**
1. Go to https://polygon.io/dashboard/signup
2. Sign up for FREE account
3. Copy your API key
4. Add to environment:

```bash
# Windows PowerShell
$env:POLYGON_API_KEY = "your_api_key_here"

# Linux/Mac
export POLYGON_API_KEY="your_api_key_here"
```

**Add to Docker:**
```yaml
# docker-compose-airflow.yml
environment:
  - POLYGON_API_KEY=${POLYGON_API_KEY}
```

### Option 2: Finnhub (Good Alternative)

**Why Finnhub:**
- ✅ FREE tier: 60 API calls/minute
- ✅ Good reliability
- ✅ Real-time data

**Get API Key:**
1. Go to https://finnhub.io/register
2. Sign up for FREE account
3. Copy your API key
4. Add to environment:

```bash
$env:FINNHUB_API_KEY = "your_api_key_here"
```

### Option 3: Keep Alpha Vantage (Already Have)

You already have Alpha Vantage configured:
- ✅ Already working in config.json
- ⚠️ Rate limit: 25 requests/day
- ✅ Good as fallback source

## 📋 Complete Setup Steps

### 1. Get API Keys (Choose at least ONE)

| Source | Free Tier | Best For | Link |
|--------|-----------|----------|------|
| **Polygon.io** ⭐ | 5 calls/min | Production use | https://polygon.io/dashboard/signup |
| **Finnhub** | 60 calls/min | Backup | https://finnhub.io/register |
| Alpha Vantage | 25 calls/day | Already have ✅ | - |
| Yahoo Finance | Unlimited | Emergency fallback | No key needed |

### 2. Add to Environment Variables

**Windows (PowerShell):**
```powershell
$env:POLYGON_API_KEY = "your_polygon_key"
$env:FINNHUB_API_KEY = "your_finnhub_key"
$env:ALPHA_VANTAGE_API_KEY = "your_existing_av_key"
```

**Linux/Mac:**
```bash
export POLYGON_API_KEY="your_polygon_key"
export FINNHUB_API_KEY="your_finnhub_key"
export ALPHA_VANTAGE_API_KEY="your_existing_av_key"
```

### 3. Update Docker Compose

Edit `docker-compose-airflow.yml`:

```yaml
x-airflow-common:
  &airflow-common
  image: financial-etl-airflow:latest
  environment:
    # ... existing vars ...
    - POLYGON_API_KEY=${POLYGON_API_KEY}
    - FINNHUB_API_KEY=${FINNHUB_API_KEY}
    - ALPHA_VANTAGE_API_KEY=${ALPHA_VANTAGE_API_KEY}
```

### 4. Restart Docker

```bash
docker-compose -f docker-compose-airflow.yml down
docker-compose -f docker-compose-airflow.yml up -d
```

## 🧪 Test the Setup

```bash
# Test which sources are available
docker exec financial-trading-etl-pipeline-airflow-scheduler-1 python -c "
from scripts.reliable_stock_collector import ReliableStockCollector
collector = ReliableStockCollector()
print('Available sources:', [s.name for s in collector.available_sources])
"

# Test actual data collection
docker exec financial-trading-etl-pipeline-airflow-scheduler-1 python -c "
from scripts.reliable_stock_collector import collect_stock_minute_data_reliable
result = collect_stock_minute_data_reliable(['AAPL', 'MSFT'], '2025-10-14')
print(f'Records: {result[\"total_records\"]}')
print(f'Sources used: {result[\"sources_used\"]}')
"
```

## 📊 How It Works in Production

### Automatic Fallback Flow

```
Symbol: AAPL, Date: 2025-10-15

1. Try Polygon.io...
   ✅ SUCCESS: 390 bars collected
   → Use Polygon data
   
OR

1. Try Polygon.io...
   ❌ Rate limit reached
2. Try Finnhub...
   ✅ SUCCESS: 390 bars collected
   → Use Finnhub data

OR

1. Try Polygon.io...
   ❌ No API key configured
2. Try Finnhub...
   ❌ No API key configured
3. Try Alpha Vantage...
   ✅ SUCCESS: 390 bars collected (19/25 requests today)
   → Use Alpha Vantage data

OR (worst case)

1-3. All premium sources exhausted...
4. Try Yahoo Finance...
   ✅ SUCCESS: 390 bars collected
   → Use Yahoo data
```

### Daily Request Planning

**With Polygon.io (Recommended):**
- 5 calls/minute = 300 calls/hour
- 7 stock symbols × 4 runs/day = 28 calls needed
- **Plenty of capacity** ✅

**With Finnhub:**
- 60 calls/minute
- 7 symbols × 4 runs = 28 calls needed
- **Plenty of capacity** ✅

**With Alpha Vantage only:**
- 25 calls/day
- 7 symbols × 1 run = 7 calls
- **Can do 3 full runs per day** ✅

## 🎯 Recommended Configuration

**Best Setup (Production-Ready):**
```bash
# Primary: Polygon.io (free tier is enough)
POLYGON_API_KEY=your_polygon_key

# Backup: Finnhub (in case Polygon has issues)
FINNHUB_API_KEY=your_finnhub_key

# Already have: Alpha Vantage
ALPHA_VANTAGE_API_KEY=your_existing_key

# Automatic: Yahoo Finance (no key needed, last resort)
```

This gives you **4 layers of redundancy**!

## 📈 Monitoring

Check which sources are being used:

```python
# View in Airflow logs
INFO - Sources Used:
   - Polygon.io: 7 symbols  ✅  (All from primary source!)
   
OR

INFO - Sources Used:
   - Polygon.io: 5 symbols
   - Finnhub: 2 symbols      ✅  (Fallback worked!)
```

## ⚡ Zero Configuration Option

**Don't want to set up API keys right now?**

The collector will automatically use:
1. Your existing Alpha Vantage key (25/day)
2. Yahoo Finance as fallback (unlimited)

**This works out of the box**, but we recommend adding at least Polygon.io for better reliability.

## 🎓 Summary

| Setup Level | Configuration | Reliability |
|-------------|---------------|-------------|
| **Minimal** | Alpha Vantage + Yahoo | ⭐⭐☆☆☆ |
| **Good** | + Polygon.io | ⭐⭐⭐⭐☆ |
| **Best** | + Polygon.io + Finnhub | ⭐⭐⭐⭐⭐ |

**Bottom Line:** With **just Polygon.io free tier**, you get production-grade reliability. Add Finnhub as backup, and you're virtually guaranteed 100% uptime.

## 🔧 Next Steps

1. **Sign up for Polygon.io** (2 minutes, free)
2. **Add API key to environment**
3. **Restart Docker containers**
4. **Test collection**
5. **Never worry about Yahoo Finance failures again!** 🎉
