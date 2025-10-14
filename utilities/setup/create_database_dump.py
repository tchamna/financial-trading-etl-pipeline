#!/usr/bin/env python3
"""
Database Dump Creator for Financial Trading ETL Pipeline
Creates various formats for data sharing with data scientists
"""

import os
import subprocess
import pandas as pd
import psycopg2
from datetime import datetime
import json

class DatabaseExporter:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'port': '5432',
            'database': 'financial_trading_db',
            'user': 'postgres',
            'password': 'deusiar'
        }
        
    def create_sql_dump(self):
        """Create a complete SQL dump of the database"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dump_file = f"financial_trading_db_dump_{timestamp}.sql"
        
        # Create the pg_dump command
        cmd = [
            'pg_dump',
            '-h', self.db_config['host'],
            '-p', self.db_config['port'],
            '-U', self.db_config['user'],
            '-d', self.db_config['database'],
            '--no-password',  # We'll set PGPASSWORD environment variable
            '-f', dump_file
        ]
        
        # Set password as environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = self.db_config['password']
        
        try:
            subprocess.run(cmd, env=env, check=True)
            print(f"✅ SQL dump created: {dump_file}")
            print(f"   Size: {os.path.getsize(dump_file) / 1024:.2f} KB")
            return dump_file
        except subprocess.CalledProcessError as e:
            print(f"❌ Error creating SQL dump: {e}")
            return None
    
    def export_to_csv(self):
        """Export all tables to CSV files"""
        try:
            conn = psycopg2.connect(**self.db_config)
            
            # Get all table names
            cursor = conn.cursor()
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_dir = f"csv_export_{timestamp}"
            os.makedirs(csv_dir, exist_ok=True)
            
            exported_files = []
            
            for table in tables:
                # Export each table to CSV
                df = pd.read_sql(f"SELECT * FROM {table}", conn)
                csv_file = os.path.join(csv_dir, f"{table}.csv")
                df.to_csv(csv_file, index=False)
                exported_files.append(csv_file)
                print(f"✅ Exported {table}: {len(df)} rows → {csv_file}")
            
            conn.close()
            print(f"\n📁 All CSV files in: {csv_dir}/")
            return csv_dir, exported_files
            
        except Exception as e:
            print(f"❌ Error exporting CSV: {e}")
            return None, []
    
    def export_to_json(self):
        """Export data to JSON format for APIs"""
        try:
            conn = psycopg2.connect(**self.db_config)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Export stock data
            stock_df = pd.read_sql("SELECT * FROM real_stock_data", conn)
            stock_json = f"stock_data_{timestamp}.json"
            stock_df.to_json(stock_json, orient='records', date_format='iso', indent=2)
            
            # Export crypto data
            crypto_df = pd.read_sql("SELECT * FROM real_crypto_data", conn)
            crypto_json = f"crypto_data_{timestamp}.json"
            crypto_df.to_json(crypto_json, orient='records', date_format='iso', indent=2)
            
            # Create combined summary
            summary = {
                "export_timestamp": datetime.now().isoformat(),
                "database_info": {
                    "name": "financial_trading_db",
                    "total_stocks": len(stock_df),
                    "total_cryptos": len(crypto_df),
                    "total_stock_market_cap": int(stock_df['market_cap'].sum()) if not stock_df.empty else 0,
                    "total_crypto_market_cap": int(crypto_df['market_cap'].sum()) if not crypto_df.empty else 0
                },
                "files": {
                    "stock_data": stock_json,
                    "crypto_data": crypto_json
                }
            }
            
            summary_json = f"data_summary_{timestamp}.json"
            with open(summary_json, 'w') as f:
                json.dump(summary, f, indent=2)
            
            conn.close()
            
            print(f"✅ JSON exports created:")
            print(f"   📊 Stock data: {stock_json}")
            print(f"   🚀 Crypto data: {crypto_json}")
            print(f"   📋 Summary: {summary_json}")
            
            return [stock_json, crypto_json, summary_json]
            
        except Exception as e:
            print(f"❌ Error exporting JSON: {e}")
            return []
    
    def create_connection_guide(self):
        """Create a guide for data scientists to connect"""
        guide_content = f"""# Financial Trading Database - Data Access Guide

## 🗄️ Database Information
- **Host:** {self.db_config['host']}
- **Port:** {self.db_config['port']}
- **Database:** {self.db_config['database']}
- **Username:** {self.db_config['user']}
- **Password:** {self.db_config['password']}

## 📊 Available Tables
1. **real_stock_data** - Live stock market data (AAPL, GOOGL, MSFT, TSLA, AMZN)
2. **real_crypto_data** - Cryptocurrency data (BTC, ETH, ADA, SOL, DOT)
3. **portfolio_positions** - Portfolio management data
4. **technical_analysis** - Technical indicators and analysis

## 🐍 Python Connection Example
```python
import psycopg2
import pandas as pd

# Database connection
conn = psycopg2.connect(
    host='{self.db_config['host']}',
    port='{self.db_config['port']}',
    database='{self.db_config['database']}',
    user='{self.db_config['user']}',
    password='{self.db_config['password']}'
)

# Load stock data
stock_df = pd.read_sql("SELECT * FROM real_stock_data", conn)
print(f"Stock records: {{len(stock_df)}}")

# Load crypto data  
crypto_df = pd.read_sql("SELECT * FROM real_crypto_data", conn)
print(f"Crypto records: {{len(crypto_df)}}")

conn.close()
```

## 🔗 Direct SQL Connection
```bash
psql -h {self.db_config['host']} -p {self.db_config['port']} -U {self.db_config['user']} -d {self.db_config['database']}
```

## 📈 Sample Queries for Data Scientists

### Stock Analysis
```sql
-- Top performing stocks by market cap
SELECT symbol, company_name, close_price, market_cap 
FROM real_stock_data 
ORDER BY market_cap DESC;

-- Stock price and volume analysis
SELECT symbol, close_price, volume, 
       (close_price * volume) as trading_value
FROM real_stock_data;
```

### Crypto Analysis
```sql
-- Crypto market rankings
SELECT name, symbol, current_price, market_cap_rank, 
       price_change_percentage_24h
FROM real_crypto_data 
ORDER BY market_cap_rank;

-- Top gainers/losers
SELECT name, symbol, price_change_percentage_24h
FROM real_crypto_data 
ORDER BY price_change_percentage_24h DESC;
```

## 🛠️ Tools & Integrations
- **Jupyter Notebooks:** Use psycopg2 + pandas for analysis
- **Power BI / Tableau:** Direct PostgreSQL connector
- **R:** RPostgreSQL package
- **DBeaver:** GUI database tool for exploration
- **pgAdmin:** Web-based PostgreSQL administration

## 📊 Data Formats Available
- **SQL Dump:** Complete database backup/restore
- **CSV Files:** Individual table exports for Excel/analysis
- **JSON:** API-friendly format for web applications
- **Parquet:** Coming soon for big data analytics

## 🔄 Data Update Schedule
- **Real-time:** Live API connections
- **Batch Updates:** Every 15 minutes via ETL pipeline
- **Historical Data:** Stored with timestamps for trend analysis

## 📧 Contact
For access requests or technical support, contact the ETL pipeline administrator.

---
Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        
        guide_file = "DATA_ACCESS_GUIDE.md"
        with open(guide_file, 'w') as f:
            f.write(guide_content)
        
        print(f"✅ Data access guide created: {guide_file}")
        return guide_file

def main():
    """Main execution function"""
    print("🚀 Financial Trading Database Export Tool")
    print("=" * 50)
    
    exporter = DatabaseExporter()
    
    # Create all export formats
    print("\n1️⃣ Creating SQL dump...")
    sql_dump = exporter.create_sql_dump()
    
    print("\n2️⃣ Exporting to CSV...")
    csv_dir, csv_files = exporter.export_to_csv()
    
    print("\n3️⃣ Exporting to JSON...")
    json_files = exporter.export_to_json()
    
    print("\n4️⃣ Creating data access guide...")
    guide_file = exporter.create_connection_guide()
    
    print("\n" + "=" * 50)
    print("✅ EXPORT COMPLETE!")
    print("\n📦 Files created:")
    if sql_dump:
        print(f"   🗄️  SQL Dump: {sql_dump}")
    if csv_dir:
        print(f"   📊 CSV Directory: {csv_dir}/")
    for json_file in json_files:
        print(f"   🔗 JSON: {json_file}")
    print(f"   📋 Guide: {guide_file}")
    
    print("\n🎯 Next Steps:")
    print("   • Share the SQL dump for complete database recreation")
    print("   • Provide CSV files for Excel/Pandas analysis")  
    print("   • Use JSON for API integrations")
    print("   • Send the access guide to data scientists")

if __name__ == "__main__":
    main()