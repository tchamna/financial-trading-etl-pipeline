#!/usr/bin/env python3
"""
Quick cryptocurrency support validator for users
Run this script to validate your cryptocurrency selection
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import CryptoMappingConfig
from user_config import get_user_config

def validate_crypto_selection():
    """Validate current cryptocurrency selection in user_config.py"""
    
    print("🔍 CRYPTOCURRENCY SUPPORT VALIDATOR")
    print("=" * 50)
    
    # Load configurations
    crypto_config = CryptoMappingConfig()
    user_config = get_user_config()
    
    # Get user's crypto symbols
    user_cryptos = user_config.get('crypto_symbols', [])
    
    if not user_cryptos:
        print("❌ No cryptocurrencies configured in user_config.py")
        print("💡 Edit CRYPTO_SYMBOLS in user_config.py to add cryptocurrencies")
        return
    
    print(f"📋 Your Current Selection: {user_cryptos}")
    print()
    
    # Validate each symbol
    valid_count = 0
    for crypto in user_cryptos:
        if crypto_config.is_supported(crypto):
            mapping = crypto_config.get_mapping(crypto)
            print(f"✅ {crypto} ({mapping['name']}) - SUPPORTED")
            valid_count += 1
        else:
            print(f"❌ {crypto} - NOT SUPPORTED")
    
    # Summary
    print()
    print("📊 VALIDATION SUMMARY:")
    print(f"   ✅ Supported: {valid_count}/{len(user_cryptos)} cryptocurrencies")
    
    if valid_count == len(user_cryptos):
        print("🎉 All your cryptocurrencies are supported! Ready to run the pipeline.")
    else:
        print(f"⚠️  Some cryptocurrencies are not supported.")
        print("💡 See USER_CONFIG_GUIDE.md for complete list of 41 supported cryptocurrencies")
        print("🚀 Or check CRYPTOCURRENCY_EXPANSION_SUMMARY.md for detailed categories")

if __name__ == "__main__":
    validate_crypto_selection()