#!/usr/bin/env python3
"""
PostgreSQL Connection Helper
Finds the correct way to connect to your PostgreSQL installation
"""

import os
import psycopg2
import getpass
from dotenv import load_dotenv

def find_postgres_connection():
    """Try different connection methods to find the right one"""
    
    print("🔍 FINDING POSTGRESQL CONNECTION METHOD")
    print("=" * 50)
    
    # Get current Windows username
    windows_user = getpass.getuser()
    print(f"👤 Windows User: {windows_user}")
    
    # Different connection attempts
    connection_attempts = [
        {
            'desc': 'Default postgres user with empty password',
            'config': {'host': 'localhost', 'port': 5432, 'database': 'postgres', 'user': 'postgres', 'password': ''}
        },
        {
            'desc': 'Windows user authentication',
            'config': {'host': 'localhost', 'port': 5432, 'database': 'postgres', 'user': windows_user, 'password': ''}
        },
        {
            'desc': 'Default postgres user with common passwords',
            'config': {'host': 'localhost', 'port': 5432, 'database': 'postgres', 'user': 'postgres', 'password': 'postgres'}
        },
        {
            'desc': 'Trust authentication (no password)',
            'config': {'host': 'localhost', 'port': 5432, 'database': 'postgres', 'user': 'postgres'}
        }
    ]
    
    successful_config = None
    
    for i, attempt in enumerate(connection_attempts, 1):
        print(f"\n🔄 Attempt {i}: {attempt['desc']}")
        print("-" * 30)
        
        try:
            conn = psycopg2.connect(**attempt['config'])
            cursor = conn.cursor()
            
            # Get PostgreSQL info
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            cursor.execute("SELECT current_database(), current_user;")
            db_info = cursor.fetchone()
            
            cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
            databases = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            print(f"✅ SUCCESS!")
            print(f"   📊 Version: {version[:60]}...")
            print(f"   🗄️  Database: {db_info[0]}")
            print(f"   👤 Connected as: {db_info[1]}")
            print(f"   📋 Available databases: {', '.join(databases)}")
            
            successful_config = attempt['config']
            break
            
        except psycopg2.OperationalError as e:
            print(f"❌ Failed: {str(e)}")
            
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
    
    if successful_config:
        print(f"\n🎉 FOUND WORKING CONNECTION!")
        print("=" * 50)
        print("✅ Use these settings in your .env file:")
        print(f"DB_HOST={successful_config['host']}")
        print(f"DB_PORT={successful_config['port']}")
        print(f"DB_DATABASE=financial_trading_db")  # We'll create this
        print(f"DB_USER={successful_config['user']}")
        print(f"DB_PASSWORD={successful_config.get('password', '')}")
        
        return successful_config
    else:
        print(f"\n❌ NO WORKING CONNECTION FOUND")
        print("💡 Try these solutions:")
        print("1. Open pgAdmin and check connection settings")
        print("2. Reset postgres user password:")
        print("   - Open Command Prompt as Administrator")
        print("   - Run: psql -U postgres")
        print("   - If prompted, use the password you set during installation")
        print("3. Check PostgreSQL authentication in pg_hba.conf")
        
        return None

if __name__ == "__main__":
    find_postgres_connection()