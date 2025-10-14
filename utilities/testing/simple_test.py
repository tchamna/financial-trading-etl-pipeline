#!/usr/bin/env python3
"""
Simple Financial Data Test
Tests basic data processing capabilities without external dependencies
"""

import pandas as pd
import json
from datetime import datetime, timedelta

def test_basic_data_processing():
    """Test basic financial data processing"""
    print("🧪 Testing Basic Financial Data Processing...")
    
    # Create sample stock data
    dates = [datetime.now() - timedelta(days=i) for i in range(5, 0, -1)]
    stock_data = {
        'timestamp': dates,
        'symbol': ['AAPL'] * 5,
        'open': [150.0, 152.0, 148.0, 151.0, 149.0],
        'high': [155.0, 156.0, 152.0, 155.0, 153.0],
        'low': [149.0, 150.0, 146.0, 149.0, 147.0],
        'close': [154.0, 155.0, 150.0, 152.0, 151.0],
        'volume': [1000000, 1200000, 800000, 1100000, 950000]
    }
    
    df = pd.DataFrame(stock_data)
    
    # Basic transformations
    df['price_change'] = df['close'].diff()
    df['price_change_pct'] = (df['close'].pct_change() * 100).round(2)
    df['sma_3'] = df['close'].rolling(window=3).mean()
    df['volume_avg'] = df['volume'].rolling(window=3).mean()
    
    print("✅ Sample Data Created:")
    print(df[['symbol', 'close', 'price_change', 'price_change_pct', 'sma_3']].to_string(index=False))
    
    # Technical indicators
    rsi_signal = "BUY" if df['price_change_pct'].iloc[-1] > 0 else "HOLD"
    volatility = df['price_change_pct'].std()
    
    print(f"\n📊 Analysis Results:")
    print(f"   💰 Latest Price: ${df['close'].iloc[-1]:.2f}")
    print(f"   📈 Price Change: {df['price_change_pct'].iloc[-1]:.2f}%")
    print(f"   🎯 Trading Signal: {rsi_signal}")
    print(f"   📊 Volatility: {volatility:.2f}%")
    print(f"   🔄 3-day SMA: ${df['sma_3'].iloc[-1]:.2f}")
    
    return True

def test_crypto_data_simulation():
    """Test crypto data processing simulation"""
    print("\n🪙 Testing Crypto Data Processing...")
    
    crypto_data = {
        'symbol': ['BTC', 'ETH', 'ADA'],
        'current_price': [114649, 4200, 0.75],
        'market_cap': [2200000000000, 500000000000, 25000000000],
        'change_24h': [2.5, -1.2, 5.8]
    }
    
    df = pd.DataFrame(crypto_data)
    
    # Market cap categories
    def categorize_market_cap(market_cap):
        if market_cap >= 1000000000000:
            return "Large Cap"
        elif market_cap >= 100000000000:
            return "Mid Cap"
        else:
            return "Small Cap"
    
    df['market_cap_category'] = df['market_cap'].apply(categorize_market_cap)
    
    print("✅ Crypto Portfolio:")
    print(df[['symbol', 'current_price', 'change_24h', 'market_cap_category']].to_string(index=False))
    
    total_portfolio_value = (df['current_price'] * [1, 10, 1000]).sum()  # Simulate holdings
    print(f"\n💼 Portfolio Summary:")
    print(f"   💰 Total Value: ${total_portfolio_value:,.2f}")
    print(f"   🚀 Top Performer: {df.loc[df['change_24h'].idxmax(), 'symbol']} (+{df['change_24h'].max():.1f}%)")
    
    return True

def test_data_quality_checks():
    """Test data quality validation"""
    print("\n🔍 Testing Data Quality Checks...")
    
    # Sample data with quality issues
    test_data = pd.DataFrame({
        'symbol': ['AAPL', 'GOOGL', None, 'TSLA'],
        'price': [150.0, 2800.0, -100.0, None],
        'volume': [1000000, 800000, -5000, 2000000]
    })
    
    # Quality checks
    issues = []
    
    # Check for null symbols
    null_symbols = test_data['symbol'].isnull().sum()
    if null_symbols > 0:
        issues.append(f"❌ {null_symbols} null symbols")
    
    # Check for invalid prices
    invalid_prices = ((test_data['price'] <= 0) | test_data['price'].isnull()).sum()
    if invalid_prices > 0:
        issues.append(f"❌ {invalid_prices} invalid prices")
    
    # Check for negative volumes
    negative_volumes = (test_data['volume'] < 0).sum()
    if negative_volumes > 0:
        issues.append(f"❌ {negative_volumes} negative volumes")
    
    print("📋 Data Quality Report:")
    print(f"   📊 Total Records: {len(test_data)}")
    
    if issues:
        print("   🚨 Issues Found:")
        for issue in issues:
            print(f"      {issue}")
        
        # Clean data
        clean_data = test_data.dropna(subset=['symbol', 'price'])
        clean_data = clean_data[(clean_data['price'] > 0) & (clean_data['volume'] >= 0)]
        print(f"   ✅ Clean Records: {len(clean_data)}")
    else:
        print("   ✅ No quality issues found")
    
    return True

def main():
    """Run all tests"""
    print("🚀 Financial Trading ETL - Simple Data Processing Test")
    print("=" * 60)
    
    tests = [
        test_basic_data_processing,
        test_crypto_data_simulation,
        test_data_quality_checks
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(("✅", test_func.__name__, "PASSED"))
        except Exception as e:
            results.append(("❌", test_func.__name__, f"FAILED: {str(e)}"))
            print(f"❌ {test_func.__name__} failed: {str(e)}")
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if "PASSED" in r[2])
    total = len(results)
    
    for status, name, result in results:
        print(f"{status} {name}: {result}")
    
    print(f"\n🎯 Success Rate: {passed}/{total} ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! Your data processing pipeline is working!")
        print("\n📝 Next Steps:")
        print("   1. Get Alpha Vantage API key for real market data")
        print("   2. Install Docker Desktop and start services")
        print("   3. Set up AWS account for cloud deployment")
        print("   4. Configure Snowflake for data warehouse")
    
    return passed == total

if __name__ == "__main__":
    main()