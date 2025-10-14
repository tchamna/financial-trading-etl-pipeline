"""
Minute-Level Crypto Data Analyzer
=================================

Author: Shck Tchamna (tchamna@gmail.com)

Advanced analysis tools for minute-level cryptocurrency data including:
- Technical indicators (RSI, MACD, Bollinger Bands)
- Volatility analysis
- Volume patterns
- Price action analysis
- Trading signals
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Tuple
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config

class MinuteCryptoAnalyzer:
    """Analyzer for minute-level cryptocurrency data"""
    
    def __init__(self, data_file: str):
        """Initialize with minute data file"""
        self.data_file = data_file
        self.data = None
        self.df_dict = {}
        self.load_data()
        
    def load_data(self):
        """Load and prepare the minute data"""
        print("📊 Loading minute-level crypto data...")
        
        with open(self.data_file, 'r') as f:
            self.data = json.load(f)
        
        # Convert to DataFrames by symbol
        for symbol in set(record['symbol'] for record in self.data['crypto_data']):
            symbol_data = [r for r in self.data['crypto_data'] if r['symbol'] == symbol]
            
            df = pd.DataFrame(symbol_data)
            df['datetime'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('datetime').reset_index(drop=True)
            
            # Set datetime as index
            df.set_index('datetime', inplace=True)
            
            self.df_dict[symbol] = df
            
        print(f"✅ Loaded data for {len(self.df_dict)} symbols")
        
    def calculate_technical_indicators(self, symbol: str) -> pd.DataFrame:
        """Calculate technical indicators for a symbol"""
        
        if symbol not in self.df_dict:
            print(f"❌ No data for {symbol}")
            return None
            
        df = self.df_dict[symbol].copy()
        
        print(f"🔍 Calculating technical indicators for {symbol}...")
        
        # Price-based indicators
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_width'] = df['bb_upper'] - df['bb_lower']
        
        # Volatility indicators
        df['true_range'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift(1)),
                abs(df['low'] - df['close'].shift(1))
            )
        )
        df['atr'] = df['true_range'].rolling(window=14).mean()
        
        # Volume indicators
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # Price action
        df['price_change'] = df['close'].pct_change()
        df['price_change_abs'] = abs(df['price_change'])
        df['high_low_ratio'] = (df['high'] - df['low']) / df['close']
        
        return df
        
    def analyze_volatility_patterns(self, symbol: str) -> Dict:
        """Analyze volatility patterns throughout the day"""
        
        df = self.calculate_technical_indicators(symbol)
        if df is None:
            return {}
            
        print(f"⚡ Analyzing volatility patterns for {symbol}...")
        
        # Add hour for analysis
        df['hour'] = df.index.hour
        
        # Volatility by hour
        hourly_volatility = df.groupby('hour')['price_change_abs'].agg([
            'mean', 'std', 'count'
        ]).round(4)
        
        # Volume by hour
        hourly_volume = df.groupby('hour')['volume'].agg([
            'mean', 'std'
        ]).round(0)
        
        # ATR by hour
        hourly_atr = df.groupby('hour')['atr'].mean().round(2)
        
        return {
            'hourly_volatility': hourly_volatility,
            'hourly_volume': hourly_volume, 
            'hourly_atr': hourly_atr,
            'peak_volatility_hour': hourly_volatility['mean'].idxmax(),
            'lowest_volatility_hour': hourly_volatility['mean'].idxmin(),
            'peak_volume_hour': hourly_volume['mean'].idxmax()
        }
        
    def find_trading_signals(self, symbol: str) -> Dict:
        """Find potential trading signals based on technical indicators"""
        
        df = self.calculate_technical_indicators(symbol)
        if df is None:
            return {}
            
        print(f"🎯 Finding trading signals for {symbol}...")
        
        latest = df.iloc[-1]
        
        signals = {
            'symbol': symbol,
            'timestamp': str(latest.name),
            'current_price': latest['close'],
            'signals': []
        }
        
        # RSI signals
        if latest['rsi'] < 30:
            signals['signals'].append({
                'type': 'BUY',
                'indicator': 'RSI',
                'value': latest['rsi'],
                'reason': 'Oversold condition (RSI < 30)'
            })
        elif latest['rsi'] > 70:
            signals['signals'].append({
                'type': 'SELL',
                'indicator': 'RSI', 
                'value': latest['rsi'],
                'reason': 'Overbought condition (RSI > 70)'
            })
            
        # MACD signals
        if latest['macd'] > latest['macd_signal'] and df.iloc[-2]['macd'] <= df.iloc[-2]['macd_signal']:
            signals['signals'].append({
                'type': 'BUY',
                'indicator': 'MACD',
                'reason': 'MACD crossed above signal line'
            })
        elif latest['macd'] < latest['macd_signal'] and df.iloc[-2]['macd'] >= df.iloc[-2]['macd_signal']:
            signals['signals'].append({
                'type': 'SELL', 
                'indicator': 'MACD',
                'reason': 'MACD crossed below signal line'
            })
            
        # Bollinger Band signals
        if latest['close'] < latest['bb_lower']:
            signals['signals'].append({
                'type': 'BUY',
                'indicator': 'Bollinger Bands',
                'reason': 'Price below lower Bollinger Band'
            })
        elif latest['close'] > latest['bb_upper']:
            signals['signals'].append({
                'type': 'SELL',
                'indicator': 'Bollinger Bands', 
                'reason': 'Price above upper Bollinger Band'
            })
            
        # Volume signals
        if latest['volume_ratio'] > 2.0:
            signals['signals'].append({
                'type': 'ATTENTION',
                'indicator': 'Volume',
                'value': latest['volume_ratio'],
                'reason': 'Unusually high volume (2x average)'
            })
            
        return signals
        
    def generate_summary_report(self) -> Dict:
        """Generate comprehensive analysis summary"""
        
        print("📋 Generating comprehensive analysis report...")
        
        report = {
            'analysis_time': datetime.now().isoformat(),
            'data_date': self.data['target_date'],
            'symbols_analyzed': list(self.df_dict.keys()),
            'total_minutes': len(self.data['crypto_data']),
            'symbol_analysis': {}
        }
        
        for symbol in self.df_dict.keys():
            df = self.calculate_technical_indicators(symbol)
            volatility = self.analyze_volatility_patterns(symbol)
            signals = self.find_trading_signals(symbol)
            
            # Performance metrics
            first_price = df['close'].iloc[0]
            last_price = df['close'].iloc[-1]
            day_return = (last_price - first_price) / first_price * 100
            
            # Statistics
            price_stats = {
                'open': df['open'].iloc[0],
                'close': df['close'].iloc[-1],
                'high': df['high'].max(),
                'low': df['low'].min(),
                'day_return_pct': round(day_return, 2),
                'volatility_pct': round(df['price_change_abs'].mean() * 100, 4),
                'total_volume': int(df['volume'].sum()),
                'avg_volume_per_minute': int(df['volume'].mean())
            }
            
            # Technical levels
            latest = df.iloc[-1]
            technical_levels = {
                'current_rsi': round(latest['rsi'], 2),
                'macd': round(latest['macd'], 4),
                'macd_signal': round(latest['macd_signal'], 4),
                'bb_position': round((latest['close'] - latest['bb_lower']) / (latest['bb_upper'] - latest['bb_lower']), 2),
                'atr': round(latest['atr'], 2)
            }
            
            report['symbol_analysis'][symbol] = {
                'price_statistics': price_stats,
                'technical_indicators': technical_levels,
                'volatility_analysis': volatility,
                'trading_signals': signals,
                'data_points': len(df)
            }
            
        return report


def main():
    """Main analysis execution"""
    
    print("🔬 MINUTE-LEVEL CRYPTO DATA ANALYSIS")
    print("=" * 60)
    
    # Initialize analyzer
    data_file = "crypto_minute_data_20251012.json"
    
    if not os.path.exists(data_file):
        print(f"❌ Data file not found: {data_file}")
        print("Run crypto_minute_collector.py first to collect data.")
        return
        
    analyzer = MinuteCryptoAnalyzer(data_file)
    
    # Generate comprehensive report
    report = analyzer.generate_summary_report()
    
    # Save report
    report_file = f"minute_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    # Display summary
    print(f"\n📊 ANALYSIS SUMMARY")
    print("=" * 30)
    print(f"📅 Data Date: {report['data_date']}")
    print(f"🪙 Symbols: {', '.join(report['symbols_analyzed'])}")
    print(f"⏰ Total Minutes: {report['total_minutes']}")
    
    print(f"\n💰 SYMBOL PERFORMANCE:")
    for symbol, analysis in report['symbol_analysis'].items():
        stats = analysis['price_statistics']
        signals = analysis['trading_signals']
        
        print(f"\n🔸 {symbol}:")
        print(f"   📈 Day Return: {stats['day_return_pct']:+.2f}%")
        print(f"   💹 Range: ${stats['low']:.2f} - ${stats['high']:.2f}")
        print(f"   ⚡ Volatility: {stats['volatility_pct']:.2f}%")
        print(f"   📊 Volume: {stats['total_volume']:,}")
        print(f"   🎯 Signals: {len(signals['signals'])} detected")
        
        # Show signals
        for signal in signals['signals'][:3]:  # Show first 3 signals
            print(f"      • {signal['type']}: {signal['reason']}")
    
    print(f"\n📄 Detailed report saved: {report_file}")
    print(f"🎯 Use this data for trading strategies, risk management, and market analysis!")


if __name__ == "__main__":
    main()