#!/usr/bin/env python3
"""
API Connectivity Test Script
Tests connectivity to financial data APIs and validates responses
"""

import os
import sys
import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class APIConnectivityTester:
    """Test connectivity to financial APIs"""
    
    def __init__(self):
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        self.test_results = []
        
    def test_alpha_vantage_api(self) -> Tuple[bool, str, Dict]:
        """Test Alpha Vantage API connectivity"""
        print("🔍 Testing Alpha Vantage API...")
        
        try:
            # Test intraday data endpoint
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'TIME_SERIES_INTRADAY',
                'symbol': 'AAPL',
                'interval': '5min',
                'apikey': self.alpha_vantage_key
            }
            
            start_time = time.time()
            response = requests.get(url, params=params, timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for API limit message
                if 'Note' in data:
                    return False, f"API Rate Limited: {data['Note']}", {}
                
                # Check for error message
                if 'Error Message' in data:
                    return False, f"API Error: {data['Error Message']}", {}
                
                # Check for valid data
                if 'Time Series (5min)' in data:
                    time_series = data['Time Series (5min)']
                    record_count = len(time_series)
                    
                    metrics = {
                        'response_time': response_time,
                        'record_count': record_count,
                        'latest_timestamp': list(time_series.keys())[0] if time_series else None
                    }
                    
                    return True, f"✅ Alpha Vantage API working - {record_count} records", metrics
                else:
                    return False, "❌ No time series data in response", {'response': data}
            else:
                return False, f"❌ HTTP {response.status_code}: {response.text}", {}
                
        except requests.exceptions.RequestException as e:
            return False, f"❌ Connection error: {str(e)}", {}
        except Exception as e:
            return False, f"❌ Unexpected error: {str(e)}", {}
    
    def test_coingecko_api(self) -> Tuple[bool, str, Dict]:
        """Test CoinGecko API connectivity"""
        print("🔍 Testing CoinGecko API...")
        
        try:
            # Test markets endpoint
            url = "https://api.coingecko.com/api/v3/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': 10,
                'page': 1
            }
            
            start_time = time.time()
            response = requests.get(url, params=params, timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    coin = data[0]
                    required_fields = ['id', 'symbol', 'current_price', 'market_cap']
                    
                    if all(field in coin for field in required_fields):
                        metrics = {
                            'response_time': response_time,
                            'coin_count': len(data),
                            'top_coin': coin['name'],
                            'top_coin_price': coin['current_price']
                        }
                        
                        return True, f"✅ CoinGecko API working - {len(data)} coins", metrics
                    else:
                        missing = [f for f in required_fields if f not in coin]
                        return False, f"❌ Missing required fields: {missing}", {}
                else:
                    return False, "❌ Empty or invalid response format", {'response': data}
            else:
                return False, f"❌ HTTP {response.status_code}: {response.text}", {}
                
        except requests.exceptions.RequestException as e:
            return False, f"❌ Connection error: {str(e)}", {}
        except Exception as e:
            return False, f"❌ Unexpected error: {str(e)}", {}
    
    def test_yahoo_finance_connectivity(self) -> Tuple[bool, str, Dict]:
        """Test Yahoo Finance connectivity using yfinance"""
        print("🔍 Testing Yahoo Finance connectivity...")
        
        try:
            import yfinance as yf
            
            # Test fetching data for a popular stock
            ticker = yf.Ticker("AAPL")
            
            start_time = time.time()
            # Get recent data
            hist = ticker.history(period="1d", interval="5m")
            response_time = time.time() - start_time
            
            if not hist.empty:
                metrics = {
                    'response_time': response_time,
                    'record_count': len(hist),
                    'latest_price': hist['Close'].iloc[-1] if len(hist) > 0 else None,
                    'date_range': f"{hist.index[0]} to {hist.index[-1]}" if len(hist) > 0 else None
                }
                
                return True, f"✅ Yahoo Finance working - {len(hist)} records", metrics
            else:
                return False, "❌ No data returned from Yahoo Finance", {}
                
        except ImportError:
            return False, "❌ yfinance package not installed", {}
        except Exception as e:
            return False, f"❌ Yahoo Finance error: {str(e)}", {}
    
    def test_network_connectivity(self) -> Tuple[bool, str, Dict]:
        """Test basic network connectivity"""
        print("🔍 Testing network connectivity...")
        
        test_urls = [
            "https://www.google.com",
            "https://api.github.com",
            "https://httpbin.org/get"
        ]
        
        results = []
        for url in test_urls:
            try:
                start_time = time.time()
                response = requests.get(url, timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    results.append({
                        'url': url,
                        'status': 'success',
                        'response_time': response_time
                    })
                else:
                    results.append({
                        'url': url,
                        'status': 'failed',
                        'status_code': response.status_code
                    })
            except Exception as e:
                results.append({
                    'url': url,
                    'status': 'error',
                    'error': str(e)
                })
        
        success_count = sum(1 for r in results if r['status'] == 'success')
        
        if success_count == len(test_urls):
            avg_response_time = sum(r.get('response_time', 0) for r in results) / len(results)
            return True, f"✅ Network connectivity OK - avg response: {avg_response_time:.2f}s", {'results': results}
        else:
            return False, f"❌ Network issues - {success_count}/{len(test_urls)} successful", {'results': results}
    
    def run_all_tests(self) -> List[Dict]:
        """Run all API connectivity tests"""
        print("🚀 Starting API Connectivity Tests")
        print("=" * 50)
        
        tests = [
            ("Network Connectivity", self.test_network_connectivity),
            ("Alpha Vantage API", self.test_alpha_vantage_api),
            ("CoinGecko API", self.test_coingecko_api),
            ("Yahoo Finance", self.test_yahoo_finance_connectivity)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n📋 {test_name}")
            print("-" * 30)
            
            success, message, metrics = test_func()
            
            result = {
                'test_name': test_name,
                'success': success,
                'message': message,
                'metrics': metrics,
                'timestamp': datetime.now().isoformat()
            }
            
            results.append(result)
            print(f"   {message}")
            
            if metrics:
                for key, value in metrics.items():
                    print(f"   📊 {key}: {value}")
        
        return results
    
    def print_summary(self, results: List[Dict]):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n🚨 Failed Tests:")
            for result in results:
                if not result['success']:
                    print(f"   • {result['test_name']}: {result['message']}")
        
        # Save results to file
        results_file = f"api_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to: {results_file}")
        
        return passed_tests == total_tests

def main():
    """Main function"""
    print("🔧 Financial Trading ETL Pipeline - API Connectivity Test")
    print(f"🕒 Test started at: {datetime.now()}")
    
    # Check environment variables
    if not os.getenv('ALPHA_VANTAGE_API_KEY'):
        print("⚠️  Warning: ALPHA_VANTAGE_API_KEY not set, using demo key")
    
    tester = APIConnectivityTester()
    results = tester.run_all_tests()
    success = tester.print_summary(results)
    
    if success:
        print("\n🎉 All API connectivity tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Check the results above.")
        sys.exit(1)

if __name__ == "__main__":
    main()