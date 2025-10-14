# 🎯 **USER GUIDE: How to Customize Your Financial Data Pipeline**

## 📝 **For Non-Technical Users - Simple Steps**

### **What You Can Customize (Without Programming!)**

This guide shows you exactly **where to change** the stocks and cryptocurrencies you want to track. You only need to edit **one file** - no coding required!

---

## 🔧 **STEP 1: Choose Your Stocks & Crypto**

### **📄 File to Edit**: `config.json`

**Location**: In your project folder, look for the file called `config.json`

### **What to Change**: 

**🏢 Stock Symbols** (Line 37):
```json
"stock_symbols": ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA", "META", "NFLX", "AMD", "CRM"]
```

**🪙 Cryptocurrency Symbols** (Line 38):
```json  
"crypto_symbols": ["bitcoin", "ethereum", "cardano", "polkadot", "chainlink", "solana", "avalanche-2"]
```

### **📚 Popular Options**:

**🏢 STOCK SYMBOLS** (Use the ticker symbol):
- **Apple**: `AAPL`
- **Microsoft**: `MSFT` 
- **Google/Alphabet**: `GOOGL`
- **Tesla**: `TSLA`
- **Amazon**: `AMZN`
- **Nvidia**: `NVDA`
- **Meta/Facebook**: `META`
- **Netflix**: `NFLX`
- **Disney**: `DIS`
- **Coca-Cola**: `KO`
- **Johnson & Johnson**: `JNJ`
- **Walmart**: `WMT`
- **JPMorgan Chase**: `JPM`
- **Visa**: `V`
- **Mastercard**: `MA`

**🪙 CRYPTOCURRENCY SYMBOLS** (Use the CoinGecko ID):
- **Bitcoin**: `bitcoin`
- **Ethereum**: `ethereum` 
- **Cardano**: `cardano`
- **Solana**: `solana`
- **Polkadot**: `polkadot`
- **Chainlink**: `chainlink`
- **Polygon**: `matic-network`
- **Avalanche**: `avalanche-2`
- **Dogecoin**: `dogecoin`
- **Shiba Inu**: `shiba-inu`
- **Litecoin**: `litecoin`
- **Ripple**: `ripple`

---

## ⚙️ **STEP 2: Required Settings You Must Change**

### **🔑 API Keys** (Lines 23-24):
```json
"alpha_vantage_api_key": "PUT_YOUR_FREE_API_KEY_HERE",
"coingecko_timeout": 30,
```

### **🗃️ Database Password** (Line 7):
```json
"password": "PUT_YOUR_DATABASE_PASSWORD_HERE",
```

### **☁️ AWS S3 Settings** (Lines 13-14) - **OPTIONAL**:
```json
"access_key_id": "PUT_YOUR_AWS_KEY_HERE",
"secret_access_key": "PUT_YOUR_AWS_SECRET_HERE",
```

**💡 TIP**: If you don't want to use AWS, change line 11 to:
```json
"enabled": false,
```

---

## 📋 **STEP 3: Easy Example - Personal Portfolio**

**Let's say you want to track**:
- **Stocks**: Apple, Tesla, Microsoft, Disney
- **Crypto**: Bitcoin, Ethereum, Dogecoin

**✏️ Change lines 37-38 to**:
```json
"stock_symbols": ["AAPL", "TSLA", "MSFT", "DIS"],
"crypto_symbols": ["bitcoin", "ethereum", "dogecoin"],
```

**That's it!** 🎉

---

## 🚀 **STEP 4: How to Run After Changes**

### **Windows Users**:
```powershell
# 1. Open PowerShell in your project folder
# 2. Run this command:
python scripts/real_database_pipeline.py
```

### **Mac/Linux Users**:
```bash
# 1. Open Terminal in your project folder  
# 2. Run this command:
python scripts/real_database_pipeline.py
```

---

## 🔍 **Advanced Settings (Optional)**

### **⏱️ How Often to Collect Data** (Line 39):
```json
"collection_interval_seconds": 300,
```
- **300** = Every 5 minutes
- **600** = Every 10 minutes  
- **1800** = Every 30 minutes

### **📧 Email Notifications** (Line 64):
```json
"email_list": ["your-email@gmail.com"],
```

---

## ❓ **Where to Find API Keys**

### **🔑 Alpha Vantage (Free - For Stocks)**:
1. Go to: https://www.alphavantage.co/support/#api-key
2. Click "Get your free API key today"
3. Fill out the form
4. Copy your API key
5. Paste it in `config.json` line 23

### **🪙 CoinGecko (Free - For Crypto)**:
- **No API key needed!** CoinGecko works without registration.

### **☁️ AWS S3 (Optional - For Cloud Storage)**:
1. Go to: https://aws.amazon.com/
2. Create free account
3. Go to IAM → Users → Create User
4. Copy Access Key ID and Secret Key
5. Paste them in `config.json` lines 13-14

---

## 🚨 **Common Mistakes to Avoid**

1. **❌ Wrong Format**: 
   - Stock symbols must be **UPPERCASE**: `"AAPL"` ✅ not `"aapl"` ❌
   - Crypto symbols must be **lowercase**: `"bitcoin"` ✅ not `"Bitcoin"` ❌

2. **❌ Missing Commas**: 
   - Always put commas between items: `["AAPL", "TSLA"]` ✅

3. **❌ Missing Quotes**:
   - Always use quotes: `"AAPL"` ✅ not `AAPL` ❌

4. **❌ Wrong Crypto Names**:
   - Use CoinGecko IDs: `"bitcoin"` ✅ not `"BTC"` ❌

---

## 🆘 **Need Help?**

### **📋 Test Your Settings**:
```powershell
python config.py validate
```

### **📊 See What You're Tracking**:
```powershell
python config.py summary  
```

### **🔧 Quick Test**:
```powershell
python scripts/quick_test.py
```

---

## 📈 **Example Configurations**

### **🏦 Conservative Investor**:
```json
"stock_symbols": ["JNJ", "KO", "WMT", "V", "MA"],
"crypto_symbols": ["bitcoin", "ethereum"],
```

### **🚀 Growth Investor**:
```json
"stock_symbols": ["TSLA", "NVDA", "AMD", "META", "NFLX"],
"crypto_symbols": ["ethereum", "solana", "cardano", "chainlink"],
```

### **🏢 Tech Focus**:
```json
"stock_symbols": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"],
"crypto_symbols": ["ethereum", "chainlink", "polkadot"],
```

---

**🎉 That's it! You're ready to track your custom portfolio!**