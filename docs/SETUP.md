# 🚀 Quick Setup Guide

## 📋 **Prerequisites**
- Python 3.8+
- AWS Account (for S3 storage)
- Alpha Vantage API Key (free)

## ⚡ **5-Minute Setup**

### 1️⃣ **Clone & Install**
```bash
git clone https://github.com/tchamna/financial-trading-etl-pipeline.git
cd financial-trading-etl-pipeline
pip install -r requirements.txt
```

### 2️⃣ **Configure Your Credentials**

**Copy the example configuration:**
```bash
cp config.example.json config.json
```

**Edit `config.json` and replace these placeholders:**
- `YOUR_AWS_ACCESS_KEY_HERE` → Your AWS Access Key
- `YOUR_AWS_SECRET_KEY_HERE` → Your AWS Secret Key  
- `your-s3-bucket-name-here` → Your S3 bucket name
- `YOUR_ALPHA_VANTAGE_API_KEY_HERE` → Your Alpha Vantage API key
- `your_email@example.com` → Your email for alerts
- `your_database_password_here` → Your PostgreSQL password

### 3️⃣ **Customize Your Symbols**
Edit `user_config.py` to select your cryptocurrencies and stocks:

```python
# Choose from 41+ supported cryptocurrencies
CRYPTO_SYMBOLS = [
    "BTC", "ETH", "SOL", "MATIC", "UNI", "LINK"
]

# Add your favorite stocks  
STOCK_SYMBOLS = [
    "AAPL", "GOOGL", "TSLA", "NVDA"
]
```

### 4️⃣ **Validate Your Setup**
```bash
python utilities/validate_crypto_support.py
```

### 5️⃣ **Start Collecting Data**
```bash
# Test data collection
python scripts/crypto_minute_collector.py

# Start the full pipeline
docker-compose up -d
```

## 🔑 **Get Your API Keys**

### **Alpha Vantage (Free)**
1. Go to: https://www.alphavantage.co/support/#api-key
2. Sign up for free account
3. Copy your API key to `config.json`

### **AWS S3 (Free Tier Available)**
1. Create AWS account: https://aws.amazon.com/
2. Create IAM user with S3 permissions
3. Create S3 bucket for data storage
4. Copy credentials to `config.json`

## 🎯 **What You'll Get**
- ✅ **Real-time data** for 41+ cryptocurrencies
- ✅ **Historical analysis** with minute-level precision  
- ✅ **AWS S3 storage** for scalable data lake
- ✅ **Automated pipelines** with Apache Airflow
- ✅ **Ready-to-analyze data** in JSON & Parquet formats

## 🆘 **Need Help?**
- 📖 See `USER_CONFIG_GUIDE.md` for detailed configuration
- 🔧 Check `docs/CONFIG_GUIDE.md` for advanced setup  
- 🪙 Run `python utilities/validate_crypto_support.py` to test crypto symbols

**🎉 Ready to start collecting financial data!**