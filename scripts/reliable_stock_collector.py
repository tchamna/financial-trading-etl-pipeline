"""
Reliable Multi-Source Stock Data Collector
Fallback hierarchy for production-grade reliability:
1. Polygon.io (best quality, requires free API key)
2. Alpha Vantage (free tier, 25/day limit)
3. Yahoo Finance (unlimited but unreliable)
4. Finnhub (free tier, good reliability)
"""

import os
import sys
import json
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StockDataSource:
    """Base class for stock data sources"""
    
    def __init__(self, name: str):
        self.name = name
    
    def fetch_minute_data(self, symbol: str, target_date: str) -> Tuple[List[Dict], bool]:
        """
        Fetch minute-level stock data for a symbol on target date.
        
        Returns:
            (data_list, success): List of minute data records and success status
        """
        raise NotImplementedError
    
    def is_available(self) -> bool:
        """Check if this data source is configured and available"""
        raise NotImplementedError


class PolygonDataSource(StockDataSource):
    """
    Polygon.io - BEST QUALITY, FREE TIER AVAILABLE
    - Free: 5 API calls/minute
    - Historical data: Up to 2 years
    - Minute data: Available
    - Reliability: ★★★★★ (Excellent)
    
    Get free API key: https://polygon.io/dashboard/signup
    """
    
    def __init__(self, api_key: str = None):
        super().__init__("Polygon.io")
        self.api_key = api_key or os.getenv('POLYGON_API_KEY')
        self.base_url = "https://api.polygon.io/v2/aggs/ticker"
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def fetch_minute_data(self, symbol: str, target_date: str) -> Tuple[List[Dict], bool]:
        if not self.is_available():
            return [], False
        
        logger.info(f"   🔷 Polygon.io: Fetching {symbol} for {target_date}...")
        
        try:
            # Parse target date
            target_dt = datetime.strptime(target_date, '%Y-%m-%d')
            
            # Polygon API uses millisecond timestamps
            from_date = target_dt.strftime('%Y-%m-%d')
            to_date = target_dt.strftime('%Y-%m-%d')
            
            url = f"{self.base_url}/{symbol}/range/1/minute/{from_date}/{to_date}"
            params = {
                'adjusted': 'true',
                'sort': 'asc',
                'limit': 50000,
                'apiKey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 429:
                logger.warning(f"      ⚠️  Polygon rate limit reached")
                return [], False
            
            if response.status_code != 200:
                logger.warning(f"      ⚠️  Polygon error: {response.status_code}")
                return [], False
            
            data = response.json()
            
            if data.get('status') != 'OK' or not data.get('results'):
                logger.warning(f"      ⚠️  No data from Polygon for {symbol}")
                return [], False
            
            # Convert to standard format
            records = []
            for bar in data['results']:
                timestamp = datetime.fromtimestamp(bar['t'] / 1000)
                
                # Only include data for target date
                if timestamp.strftime('%Y-%m-%d') != target_date:
                    continue
                
                records.append({
                    'symbol': symbol,
                    'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'open': bar['o'],
                    'high': bar['h'],
                    'low': bar['l'],
                    'close': bar['c'],
                    'volume': bar['v'],
                    'source': 'polygon'
                })
            
            logger.info(f"      ✅ Polygon: {len(records)} bars")
            return records, True
            
        except Exception as e:
            logger.warning(f"      ⚠️  Polygon error: {e}")
            return [], False


class AlphaVantageDataSource(StockDataSource):
    """
    Alpha Vantage - RATE LIMITED but FREE
    - Free: 25 requests/day
    - Historical data: Available
    - Minute data: Last 30 days
    - Reliability: ★★★☆☆ (Rate limit issue)
    """
    
    def __init__(self, api_key: str = None):
        super().__init__("Alpha Vantage")
        # Try environment variable first, then config.json
        self.api_key = api_key or os.getenv('ALPHA_VANTAGE_API_KEY')
        
        if not self.api_key:
            try:
                import json
                from pathlib import Path
                config_path = Path(__file__).parent.parent / 'config.json'
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        self.api_key = config.get('api', {}).get('alpha_vantage_api_key')
            except:
                pass
        
        self.base_url = "https://www.alphavantage.co/query"
        self.daily_requests = 0
        self.max_daily_requests = 25
    
    def is_available(self) -> bool:
        return bool(self.api_key) and self.daily_requests < self.max_daily_requests
    
    def fetch_minute_data(self, symbol: str, target_date: str) -> Tuple[List[Dict], bool]:
        if not self.is_available():
            return [], False
        
        logger.info(f"   🔶 Alpha Vantage: Fetching {symbol} for {target_date}...")
        
        try:
            params = {
                'function': 'TIME_SERIES_INTRADAY',
                'symbol': symbol,
                'interval': '1min',
                'outputsize': 'full',
                'apikey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=15)
            self.daily_requests += 1
            
            if response.status_code != 200:
                logger.warning(f"      ⚠️  Alpha Vantage HTTP error: {response.status_code}")
                return [], False
            
            data = response.json()
            
            # Check for rate limit
            if 'Information' in data:
                logger.warning(f"      ⚠️  Alpha Vantage rate limit: {data['Information']}")
                return [], False
            
            # Check for error
            if 'Error Message' in data:
                logger.warning(f"      ⚠️  Alpha Vantage error: {data['Error Message']}")
                return [], False
            
            time_series = data.get('Time Series (1min)', {})
            
            if not time_series:
                logger.warning(f"      ⚠️  No data from Alpha Vantage for {symbol}")
                return [], False
            
            # Convert to standard format
            records = []
            for timestamp_str, bar in time_series.items():
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                
                # Only include data for target date
                if timestamp.strftime('%Y-%m-%d') != target_date:
                    continue
                
                records.append({
                    'symbol': symbol,
                    'timestamp': timestamp_str,
                    'open': float(bar['1. open']),
                    'high': float(bar['2. high']),
                    'low': float(bar['3. low']),
                    'close': float(bar['4. close']),
                    'volume': int(bar['5. volume']),
                    'source': 'alpha_vantage'
                })
            
            logger.info(f"      ✅ Alpha Vantage: {len(records)} bars (Request {self.daily_requests}/{self.max_daily_requests})")
            return records, True
            
        except Exception as e:
            logger.warning(f"      ⚠️  Alpha Vantage error: {e}")
            return [], False


class YahooFinanceDataSource(StockDataSource):
    """
    Yahoo Finance via yfinance - UNLIMITED but UNRELIABLE
    - Free: Unlimited
    - Historical data: 7 days for 1-min data
    - Reliability: ★★☆☆☆ (Intermittent failures)
    """
    
    def __init__(self):
        super().__init__("Yahoo Finance")
        try:
            import yfinance as yf
            self.yf = yf
            self._available = True
        except ImportError:
            self._available = False
    
    def is_available(self) -> bool:
        return self._available
    
    def fetch_minute_data(self, symbol: str, target_date: str) -> Tuple[List[Dict], bool]:
        if not self.is_available():
            return [], False
        
        logger.info(f"   🟡 Yahoo Finance: Fetching {symbol} for {target_date}...")
        
        try:
            target_dt = datetime.strptime(target_date, '%Y-%m-%d')
            is_today = target_dt.date() == datetime.now().date()
            
            # Set date range
            if is_today:
                start_date = target_dt - timedelta(days=7)
                end_date = datetime.now() + timedelta(days=1)
            else:
                start_date = target_dt - timedelta(days=1)
                end_date = target_dt + timedelta(days=2)
            
            ticker = self.yf.Ticker(symbol)
            df = ticker.history(
                interval='1m',
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                prepost=False
            )
            
            if df.empty:
                logger.warning(f"      ⚠️  No data from Yahoo for {symbol}")
                return [], False
            
            # Convert to standard format
            records = []
            for timestamp, row in df.iterrows():
                timestamp_date = timestamp.strftime('%Y-%m-%d')
                
                if timestamp_date != target_date:
                    continue
                
                records.append({
                    'symbol': symbol,
                    'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume']),
                    'source': 'yahoo'
                })
            
            logger.info(f"      ✅ Yahoo: {len(records)} bars")
            return records, True
            
        except Exception as e:
            logger.warning(f"      ⚠️  Yahoo error: {e}")
            return [], False


class IEXCloudDataSource(StockDataSource):
    """
    IEX Cloud - BEST FREE TIER!
    - Free: 50,000 requests/month (1,667/day)
    - Historical data: Excellent coverage
    - Minute data: Available
    - Reliability: ★★★★★ (Excellent)
    
    Get free API key: https://iexcloud.io/
    """
    
    def __init__(self, api_key: str = None):
        super().__init__("IEX Cloud")
        self.api_key = api_key or os.getenv('IEX_CLOUD_API_KEY')
        self.base_url = "https://cloud.iexapis.com/stable/stock"
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def fetch_minute_data(self, symbol: str, target_date: str) -> Tuple[List[Dict], bool]:
        if not self.is_available():
            return [], False
        
        logger.info(f"   🔵 IEX Cloud: Fetching {symbol} for {target_date}...")
        
        try:
            # IEX Cloud endpoint for intraday data
            url = f"{self.base_url}/{symbol}/intraday-prices"
            params = {
                'token': self.api_key,
                'chartIEXOnly': 'false'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 429:
                logger.warning(f"      ⚠️  IEX Cloud rate limit reached")
                return [], False
            
            if response.status_code != 200:
                logger.warning(f"      ⚠️  IEX Cloud error: {response.status_code}")
                return [], False
            
            data = response.json()
            
            if not data:
                logger.warning(f"      ⚠️  No data from IEX Cloud for {symbol}")
                return [], False
            
            # Convert to standard format
            records = []
            for bar in data:
                if not bar.get('date') or not bar.get('minute'):
                    continue
                
                # Combine date and minute
                timestamp_str = f"{bar['date']} {bar['minute']}"
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M')
                
                # Only include data for target date
                if timestamp.strftime('%Y-%m-%d') != target_date:
                    continue
                
                records.append({
                    'symbol': symbol,
                    'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'open': bar.get('open', bar.get('close')),
                    'high': bar.get('high', bar.get('close')),
                    'low': bar.get('low', bar.get('close')),
                    'close': bar['close'],
                    'volume': bar.get('volume', 0),
                    'source': 'iex_cloud'
                })
            
            logger.info(f"      ✅ IEX Cloud: {len(records)} bars")
            return records, True
            
        except Exception as e:
            logger.warning(f"      ⚠️  IEX Cloud error: {e}")
            return [], False


class TwelveDataSource(StockDataSource):
    """
    Twelve Data - EXCELLENT FREE TIER
    - Free: 800 API calls/day
    - Historical data: Excellent
    - Minute data: Available
    - Reliability: ★★★★★ (Excellent)
    
    Get free API key: https://twelvedata.com/
    """
    
    def __init__(self, api_key: str = None):
        super().__init__("Twelve Data")
        self.api_key = api_key or os.getenv('TWELVE_DATA_API_KEY')
        self.base_url = "https://api.twelvedata.com/time_series"
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def fetch_minute_data(self, symbol: str, target_date: str) -> Tuple[List[Dict], bool]:
        if not self.is_available():
            return [], False
        
        logger.info(f"   🟦 Twelve Data: Fetching {symbol} for {target_date}...")
        
        try:
            target_dt = datetime.strptime(target_date, '%Y-%m-%d')
            
            params = {
                'symbol': symbol,
                'interval': '1min',
                'outputsize': 390,  # One trading day
                'apikey': self.api_key,
                'date': target_date
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 429:
                logger.warning(f"      ⚠️  Twelve Data rate limit reached")
                return [], False
            
            if response.status_code != 200:
                logger.warning(f"      ⚠️  Twelve Data error: {response.status_code}")
                return [], False
            
            data = response.json()
            
            if 'values' not in data or not data['values']:
                logger.warning(f"      ⚠️  No data from Twelve Data for {symbol}")
                return [], False
            
            # Convert to standard format
            records = []
            for bar in data['values']:
                timestamp = datetime.strptime(bar['datetime'], '%Y-%m-%d %H:%M:%S')
                
                # Only include data for target date
                if timestamp.strftime('%Y-%m-%d') != target_date:
                    continue
                
                records.append({
                    'symbol': symbol,
                    'timestamp': bar['datetime'],
                    'open': float(bar['open']),
                    'high': float(bar['high']),
                    'low': float(bar['low']),
                    'close': float(bar['close']),
                    'volume': int(bar['volume']),
                    'source': 'twelve_data'
                })
            
            logger.info(f"      ✅ Twelve Data: {len(records)} bars")
            return records, True
            
        except Exception as e:
            logger.warning(f"      ⚠️  Twelve Data error: {e}")
            return [], False


class FinancialModelingPrepDataSource(StockDataSource):
    """
    Financial Modeling Prep - EXCELLENT FOR ANALYSIS
    - Free: 250 API calls/day
    - Historical data: 30 years
    - Minute data: Available
    - Reliability: ★★★★☆ (Very Good)
    
    Get free API key: https://financialmodelingprep.com/
    """
    
    def __init__(self, api_key: str = None):
        super().__init__("Financial Modeling Prep")
        self.api_key = api_key or os.getenv('FMP_API_KEY')
        self.base_url = "https://financialmodelingprep.com/api/v3/historical-chart/1min"
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def fetch_minute_data(self, symbol: str, target_date: str) -> Tuple[List[Dict], bool]:
        if not self.is_available():
            return [], False
        
        logger.info(f"   🟪 FMP: Fetching {symbol} for {target_date}...")
        
        try:
            url = f"{self.base_url}/{symbol}"
            params = {
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 429:
                logger.warning(f"      ⚠️  FMP rate limit reached")
                return [], False
            
            if response.status_code != 200:
                logger.warning(f"      ⚠️  FMP error: {response.status_code}")
                return [], False
            
            data = response.json()
            
            if not data:
                logger.warning(f"      ⚠️  No data from FMP for {symbol}")
                return [], False
            
            # Convert to standard format
            records = []
            for bar in data:
                timestamp = datetime.strptime(bar['date'], '%Y-%m-%d %H:%M:%S')
                
                # Only include data for target date
                if timestamp.strftime('%Y-%m-%d') != target_date:
                    continue
                
                records.append({
                    'symbol': symbol,
                    'timestamp': bar['date'],
                    'open': float(bar['open']),
                    'high': float(bar['high']),
                    'low': float(bar['low']),
                    'close': float(bar['close']),
                    'volume': int(bar['volume']),
                    'source': 'fmp'
                })
            
            logger.info(f"      ✅ FMP: {len(records)} bars")
            return records, True
            
        except Exception as e:
            logger.warning(f"      ⚠️  FMP error: {e}")
            return [], False


class FinnhubDataSource(StockDataSource):
    """
    Finnhub - GOOD FREE TIER
    - Free: 60 API calls/minute
    - Historical data: Limited on free tier
    - Reliability: ★★★★☆ (Good)
    
    Get free API key: https://finnhub.io/register
    """
    
    def __init__(self, api_key: str = None):
        super().__init__("Finnhub")
        self.api_key = api_key or os.getenv('FINNHUB_API_KEY')
        self.base_url = "https://finnhub.io/api/v1/stock/candle"
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def fetch_minute_data(self, symbol: str, target_date: str) -> Tuple[List[Dict], bool]:
        if not self.is_available():
            return [], False
        
        logger.info(f"   🔹 Finnhub: Fetching {symbol} for {target_date}...")
        
        try:
            target_dt = datetime.strptime(target_date, '%Y-%m-%d')
            
            # Finnhub uses Unix timestamps
            from_ts = int(target_dt.timestamp())
            to_ts = int((target_dt + timedelta(days=1)).timestamp())
            
            params = {
                'symbol': symbol,
                'resolution': '1',  # 1-minute resolution
                'from': from_ts,
                'to': to_ts,
                'token': self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 429:
                logger.warning(f"      ⚠️  Finnhub rate limit reached")
                return [], False
            
            if response.status_code != 200:
                logger.warning(f"      ⚠️  Finnhub error: {response.status_code}")
                return [], False
            
            data = response.json()
            
            if data.get('s') != 'ok' or not data.get('t'):
                logger.warning(f"      ⚠️  No data from Finnhub for {symbol}")
                return [], False
            
            # Convert to standard format
            records = []
            for i in range(len(data['t'])):
                timestamp = datetime.fromtimestamp(data['t'][i])
                
                # Only include data for target date
                if timestamp.strftime('%Y-%m-%d') != target_date:
                    continue
                
                records.append({
                    'symbol': symbol,
                    'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'open': data['o'][i],
                    'high': data['h'][i],
                    'low': data['l'][i],
                    'close': data['c'][i],
                    'volume': data['v'][i],
                    'source': 'finnhub'
                })
            
            logger.info(f"      ✅ Finnhub: {len(records)} bars")
            return records, True
            
        except Exception as e:
            logger.warning(f"      ⚠️  Finnhub error: {e}")
            return [], False


class ReliableStockCollector:
    """
    Multi-source stock data collector with automatic fallback.
    Tries sources in priority order until data is found.
    """
    
    def __init__(self):
        # Initialize all available sources in priority order
        # Yahoo Finance removed per user request - unreliable
        self.sources = [
            TwelveDataSource(),              # ⭐ Excellent: 800/day (ACTIVE)
            FinancialModelingPrepDataSource(), # 🔥 Great: 250/day (ACTIVE)
            FinnhubDataSource(),             # ⭐ Good: 60/min (ACTIVE)
            IEXCloudDataSource(),           # 🏆 Best: 50,000/month (not configured yet)
            PolygonDataSource(),             # ⭐ Good: 5/min (not configured yet)
            AlphaVantageDataSource(),        # ⚠️ Limited: 25/day (have key, rate-limited)
        ]
        
        # Filter to only available sources
        self.available_sources = [s for s in self.sources if s.is_available()]
        
        logger.info(f"\n🔧 Reliable Stock Collector Initialized")
        logger.info(f"📊 Available sources: {[s.name for s in self.available_sources]}")
        
        if not self.available_sources:
            logger.warning("⚠️  WARNING: No data sources configured!")
            logger.warning("   Add API keys to environment:")
            logger.warning("   - POLYGON_API_KEY (recommended)")
            logger.warning("   - FINNHUB_API_KEY (recommended)")
            logger.warning("   - ALPHA_VANTAGE_API_KEY (has rate limit)")
    
    def collect_stock_minute_data(self, symbols: List[str], target_date: str = None) -> Dict[str, Any]:
        """
        Collect minute-level stock data with automatic fallback.
        
        Args:
            symbols: List of stock symbols (e.g., ['AAPL', 'MSFT'])
            target_date: Date in 'YYYY-MM-DD' format (default: today)
        
        Returns:
            {
                'stocks': [...],
                'successful_symbols': [...],
                'failed_symbols': [...],
                'total_records': int,
                'sources_used': {...}
            }
        """
        if target_date is None:
            target_date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"\n📈 RELIABLE MULTI-SOURCE STOCK COLLECTOR")
        logger.info(f"{'=' * 60}")
        logger.info(f"📅 Target Date: {target_date}")
        logger.info(f"📊 Symbols: {len(symbols)}")
        logger.info(f"🔄 Available sources: {len(self.available_sources)}")
        logger.info("")
        
        all_stock_data = []
        successful_symbols = []
        failed_symbols = []
        sources_used = {}
        
        for i, symbol in enumerate(symbols, 1):
            logger.info(f"💼 ({i}/{len(symbols)}) Processing {symbol}:")
            
            data_found = False
            
            # Try each source until we get data
            for source in self.available_sources:
                records, success = source.fetch_minute_data(symbol, target_date)
                
                if success and records:
                    all_stock_data.extend(records)
                    successful_symbols.append(symbol)
                    data_found = True
                    
                    # Track which source was used
                    source_name = source.name
                    sources_used[source_name] = sources_used.get(source_name, 0) + 1
                    
                    logger.info(f"      ✅ SUCCESS via {source.name}: {len(records)} bars")
                    break
                
                # Small delay between API attempts
                time.sleep(0.5)
            
            if not data_found:
                failed_symbols.append(symbol)
                logger.warning(f"      ❌ FAILED: All sources exhausted for {symbol}")
            
            logger.info("")
        
        # Summary
        logger.info(f"💾 COLLECTION SUMMARY:")
        logger.info(f"{'=' * 60}")
        logger.info(f"   💼 Total stock records: {len(all_stock_data)}")
        logger.info(f"   ✅ Successful symbols: {len(successful_symbols)}")
        logger.info(f"   ❌ Failed symbols: {len(failed_symbols)}")
        
        if sources_used:
            logger.info(f"\n📊 Sources Used:")
            for source, count in sources_used.items():
                logger.info(f"   - {source}: {count} symbols")
        
        if failed_symbols:
            logger.info(f"\n⚠️  Failed symbols: {', '.join(failed_symbols)}")
        
        return {
            'stocks': all_stock_data,
            'successful_symbols': successful_symbols,
            'failed_symbols': failed_symbols,
            'total_records': len(all_stock_data),
            'sources_used': sources_used
        }


def collect_stock_minute_data_reliable(symbols: List[str], target_date: str = None) -> Dict[str, Any]:
    """
    Main entry point for reliable stock data collection.
    
    Usage:
        result = collect_stock_minute_data_reliable(['AAPL', 'MSFT'], '2025-10-15')
    """
    collector = ReliableStockCollector()
    return collector.collect_stock_minute_data(symbols, target_date)


if __name__ == "__main__":
    # Test with sample symbols
    result = collect_stock_minute_data_reliable(['AAPL', 'MSFT'], '2025-10-14')
    print(f"\n✅ Collected {result['total_records']} records")
    print(f"✅ Successful: {result['successful_symbols']}")
    print(f"❌ Failed: {result['failed_symbols']}")
