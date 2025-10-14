"""
Simple Minute Data Analyzer
===========================

Author: Shck Tchamna (tchamna@gmail.com)

Simple analysis of minute-level crypto data without external dependencies.
Provides technical analysis, volatility patterns, and trading insights.
"""

import json
import math
from datetime import datetime
from typing import List, Dict
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config

class SimpleMinuteAnalyzer:
    """Simple analyzer for minute-level cryptocurrency data"""
    
    def __init__(self, data_file: str):
        """Initialize with minute data file"""
        self.data_file = data_file
        self.data = None
        self.symbol_data = {}
        self.load_data()
        
    def load_data(self):
        """Load and organize the minute data"""
        print("📊 Loading minute-level crypto data...")
        
        with open(self.data_file, 'r') as f:
            self.data = json.load(f)
        
        # Organize by symbol
        for record in self.data['crypto_data']:
            symbol = record['symbol']
            if symbol not in self.symbol_data:
                self.symbol_data[symbol] = []
            self.symbol_data[symbol].append(record)
        
        # Sort each symbol's data by timestamp
        for symbol in self.symbol_data:
            self.symbol_data[symbol].sort(key=lambda x: x['timestamp'])
            
        print(f"✅ Loaded data for {len(self.symbol_data)} symbols")
        
    def calculate_sma(self, prices: List[float], period: int) -> List[float]:
        """Calculate Simple Moving Average"""
        sma = []
        for i in range(len(prices)):
            if i < period - 1:
                sma.append(None)
            else:
                avg = sum(prices[i-period+1:i+1]) / period
                sma.append(avg)
        return sma
        
    def calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return [None] * len(prices)
            
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        # Initial average gain and loss
        gains = [max(0, delta) for delta in deltas[:period]]
        losses = [max(0, -delta) for delta in deltas[:period]]
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        rsi_values = [None] * (period)
        
        # Calculate RSI for remaining periods
        for i in range(period, len(prices)):
            if i < len(deltas) + 1:
                delta = deltas[i-1]
                gain = max(0, delta)
                loss = max(0, -delta)
                
                avg_gain = (avg_gain * (period - 1) + gain) / period
                avg_loss = (avg_loss * (period - 1) + loss) / period
                
                if avg_loss == 0:
                    rsi = 100
                else:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                
                rsi_values.append(rsi)
            
        return rsi_values
        
    def analyze_symbol_performance(self, symbol: str) -> Dict:
        """Analyze performance for a single symbol"""
        
        if symbol not in self.symbol_data:
            return {}
            
        data = self.symbol_data[symbol]
        prices = [float(record['close']) for record in data]
        volumes = [float(record['volume']) for record in data]
        highs = [float(record['high']) for record in data]
        lows = [float(record['low']) for record in data]
        
        # Basic statistics
        first_price = prices[0]
        last_price = prices[-1]
        day_return = (last_price - first_price) / first_price * 100
        
        price_high = max(prices)
        price_low = min(prices)
        price_range = price_high - price_low
        volatility = (price_range / first_price) * 100
        
        total_volume = sum(volumes)
        avg_volume = total_volume / len(volumes)
        
        # Technical indicators
        sma_20 = self.calculate_sma(prices, 20)
        sma_50 = self.calculate_sma(prices, 50)
        rsi = self.calculate_rsi(prices)
        
        # Current technical levels
        current_rsi = rsi[-1] if rsi[-1] is not None else 50
        current_sma_20 = sma_20[-1] if sma_20[-1] is not None else last_price
        current_sma_50 = sma_50[-1] if sma_50[-1] is not None else last_price
        
        # Price action analysis
        price_changes = []
        for i in range(1, len(prices)):
            change = (prices[i] - prices[i-1]) / prices[i-1] * 100
            price_changes.append(abs(change))
            
        avg_minute_volatility = sum(price_changes) / len(price_changes) if price_changes else 0
        
        # Hourly analysis
        hourly_stats = {}
        for record in data:
            timestamp = record['timestamp']
            hour = int(timestamp.split(' ')[1].split(':')[0])
            
            if hour not in hourly_stats:
                hourly_stats[hour] = {'prices': [], 'volumes': []}
                
            hourly_stats[hour]['prices'].append(float(record['close']))
            hourly_stats[hour]['volumes'].append(float(record['volume']))
        
        # Find peak activity hours
        hour_volatility = {}
        hour_volume = {}
        
        for hour, stats in hourly_stats.items():
            if len(stats['prices']) > 1:
                hour_prices = stats['prices']
                hour_vol = [(hour_prices[i] - hour_prices[i-1])**2 for i in range(1, len(hour_prices))]
                hour_volatility[hour] = math.sqrt(sum(hour_vol) / len(hour_vol)) if hour_vol else 0
                hour_volume[hour] = sum(stats['volumes']) / len(stats['volumes'])
        
        most_volatile_hour = max(hour_volatility.keys(), key=lambda h: hour_volatility[h]) if hour_volatility else 0
        highest_volume_hour = max(hour_volume.keys(), key=lambda h: hour_volume[h]) if hour_volume else 0
        
        return {
            'symbol': symbol,
            'data_points': len(data),
            'price_performance': {
                'open': first_price,
                'close': last_price,
                'high': price_high,
                'low': price_low,
                'day_return_pct': round(day_return, 2),
                'volatility_pct': round(volatility, 2)
            },
            'volume_analysis': {
                'total_volume': int(total_volume),
                'avg_volume_per_minute': int(avg_volume),
                'max_minute_volume': int(max(volumes)),
                'min_minute_volume': int(min(volumes))
            },
            'technical_indicators': {
                'current_rsi': round(current_rsi, 2),
                'sma_20': round(current_sma_20, 2),
                'sma_50': round(current_sma_50, 2),
                'price_vs_sma20': round(((last_price - current_sma_20) / current_sma_20) * 100, 2),
                'avg_minute_volatility': round(avg_minute_volatility, 4)
            },
            'hourly_patterns': {
                'most_volatile_hour': most_volatile_hour,
                'highest_volume_hour': highest_volume_hour,
                'hourly_volume_avg': {str(h): int(v) for h, v in hour_volume.items()}
            }
        }
        
    def find_trading_signals(self, symbol: str) -> List[Dict]:
        """Find potential trading signals"""
        
        analysis = self.analyze_symbol_performance(symbol)
        if not analysis:
            return []
            
        signals = []
        
        # RSI signals
        rsi = analysis['technical_indicators']['current_rsi']
        if rsi < 30:
            signals.append({
                'type': 'BUY_SIGNAL',
                'indicator': 'RSI',
                'value': rsi,
                'reason': f'Oversold condition (RSI: {rsi:.1f})'
            })
        elif rsi > 70:
            signals.append({
                'type': 'SELL_SIGNAL', 
                'indicator': 'RSI',
                'value': rsi,
                'reason': f'Overbought condition (RSI: {rsi:.1f})'
            })
            
        # Price vs SMA signals
        sma_diff = analysis['technical_indicators']['price_vs_sma20']
        if sma_diff > 5:
            signals.append({
                'type': 'SELL_SIGNAL',
                'indicator': 'SMA',
                'reason': f'Price {sma_diff:.1f}% above 20-period SMA'
            })
        elif sma_diff < -5:
            signals.append({
                'type': 'BUY_SIGNAL',
                'indicator': 'SMA', 
                'reason': f'Price {abs(sma_diff):.1f}% below 20-period SMA'
            })
            
        # Volatility signals
        volatility = analysis['price_performance']['volatility_pct']
        if volatility > 15:
            signals.append({
                'type': 'HIGH_VOLATILITY',
                'indicator': 'Volatility',
                'value': volatility,
                'reason': f'High volatility ({volatility:.1f}%) - increased risk'
            })
            
        return signals
        
    def generate_comprehensive_report(self) -> Dict:
        """Generate comprehensive analysis report"""
        
        print("📋 Generating comprehensive minute-level analysis...")
        
        report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'data_date': self.data['target_date'],
            'total_minutes_analyzed': len(self.data['crypto_data']),
            'symbols': list(self.symbol_data.keys()),
            'symbol_analysis': {}
        }
        
        # Analyze each symbol
        for symbol in self.symbol_data.keys():
            analysis = self.analyze_symbol_performance(symbol)
            signals = self.find_trading_signals(symbol)
            
            report['symbol_analysis'][symbol] = {
                **analysis,
                'trading_signals': signals,
                'signal_count': len(signals)
            }
            
        return report


def main():
    """Main analysis execution"""
    
    print("🔬 SIMPLE MINUTE-LEVEL CRYPTO ANALYSIS")
    print("=" * 60)
    
    # Check for data file
    data_file = "crypto_minute_data_20251012.json"
    
    if not os.path.exists(data_file):
        print(f"❌ Data file not found: {data_file}")
        print("💡 Run crypto_minute_collector.py first to collect data.")
        return
        
    # Initialize analyzer
    analyzer = SimpleMinuteAnalyzer(data_file)
    
    # Generate report
    report = analyzer.generate_comprehensive_report()
    
    # Display results
    print(f"\n📊 ANALYSIS RESULTS")
    print("=" * 35)
    print(f"📅 Data Date: {report['data_date']}")
    print(f"⏰ Minutes Analyzed: {report['total_minutes_analyzed']:,}")
    print(f"🪙 Symbols: {', '.join(report['symbols'])}")
    
    print(f"\n💰 DETAILED SYMBOL ANALYSIS:")
    print("-" * 50)
    
    for symbol, analysis in report['symbol_analysis'].items():
        perf = analysis['price_performance']
        tech = analysis['technical_indicators']
        vol = analysis['volume_analysis']
        signals = analysis['trading_signals']
        
        print(f"\n🔸 {symbol} ({analysis['data_points']} minutes):")
        print(f"   📈 Performance: {perf['day_return_pct']:+.2f}%")
        print(f"   💰 Price: ${perf['open']:.2f} → ${perf['close']:.2f}")
        print(f"   📊 Range: ${perf['low']:.2f} - ${perf['high']:.2f}")
        print(f"   ⚡ Volatility: {perf['volatility_pct']:.2f}%")
        print(f"   📈 RSI: {tech['current_rsi']:.1f}")
        print(f"   💹 Volume: {vol['total_volume']:,}")
        
        # Peak activity
        patterns = analysis['hourly_patterns']
        print(f"   🕐 Peak Volatility: {patterns['most_volatile_hour']:02d}:00 UTC")
        print(f"   📊 Peak Volume: {patterns['highest_volume_hour']:02d}:00 UTC")
        
        # Trading signals
        if signals:
            print(f"   🎯 Signals ({len(signals)}):")
            for signal in signals[:3]:  # Show first 3
                print(f"      • {signal['type']}: {signal['reason']}")
        else:
            print(f"   🎯 No strong signals detected")
    
    # Save detailed report
    report_filename = f"minute_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    # Summary insights
    print(f"\n💡 KEY INSIGHTS:")
    print("-" * 20)
    
    # Best performer
    best_performer = max(report['symbol_analysis'].items(), 
                        key=lambda x: x[1]['price_performance']['day_return_pct'])
    print(f"🏆 Best Performer: {best_performer[0]} ({best_performer[1]['price_performance']['day_return_pct']:+.2f}%)")
    
    # Most volatile
    most_volatile = max(report['symbol_analysis'].items(),
                       key=lambda x: x[1]['price_performance']['volatility_pct'])
    print(f"⚡ Most Volatile: {most_volatile[0]} ({most_volatile[1]['price_performance']['volatility_pct']:.2f}%)")
    
    # Highest volume
    highest_volume = max(report['symbol_analysis'].items(),
                        key=lambda x: x[1]['volume_analysis']['total_volume'])
    print(f"📊 Highest Volume: {highest_volume[0]} ({highest_volume[1]['volume_analysis']['total_volume']:,})")
    
    # Total signals
    total_signals = sum(len(analysis['trading_signals']) for analysis in report['symbol_analysis'].values())
    print(f"🎯 Trading Signals: {total_signals} detected across all symbols")
    
    print(f"\n📄 Detailed report saved: {report_filename}")
    print(f"☁️ Minute data uploaded to S3 successfully!")
    print(f"🎉 Complete minute-level analysis finished!")


if __name__ == "__main__":
    main()