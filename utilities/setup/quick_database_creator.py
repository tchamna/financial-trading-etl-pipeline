#!/usr/bin/env python3
"""
Quick Database Creator
Creates the financial_trading_db database on your real PostgreSQL
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

def create_database():
    """Create the financial trading database"""
    load_dotenv()
    
    # Get credentials from .env
    host = os.getenv('DB_HOST', 'localhost')
    port = int(os.getenv('DB_PORT', 5432))
    user = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASSWORD')
    db_name = os.getenv('DB_DATABASE', 'financial_trading_db')
    
    print("🏗️  Creating Financial Trading Database")
    print("=" * 50)
    print(f"Host: {host}:{port}")
    print(f"User: {user}")
    print(f"Database to create: {db_name}")
    print()
    
    try:
        # Connect to default 'postgres' database first
        print("🔌 Connecting to PostgreSQL...")
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database='postgres'  # Connect to default database
        )
        
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        print(f"🔍 Checking if '{db_name}' database exists...")
        cursor.execute("""
            SELECT 1 FROM pg_database WHERE datname = %s;
        """, (db_name,))
        
        if cursor.fetchone():
            print(f"✅ Database '{db_name}' already exists!")
        else:
            # Create database
            print(f"🔨 Creating database '{db_name}'...")
            cursor.execute(f'CREATE DATABASE "{db_name}";')
            print(f"✅ Database '{db_name}' created successfully!")
        
        # Test connection to new database
        conn.close()
        
        print(f"🧪 Testing connection to '{db_name}'...")
        test_conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=db_name
        )
        
        test_cursor = test_conn.cursor()
        test_cursor.execute("SELECT current_database(), current_user;")
        db_info = test_cursor.fetchone()
        
        test_conn.close()
        
        print(f"✅ Successfully connected to database!")
        print(f"   📊 Database: {db_info[0]}")
        print(f"   👤 User: {db_info[1]}")
        
        print("\n🎯 READY FOR DATA PIPELINE!")
        print("Now you can run: python scripts/real_database_setup.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
        if "authentication failed" in str(e):
            print("\n💡 Authentication issue - check your password in .env file")
        elif "connection refused" in str(e):
            print("\n💡 PostgreSQL not running - start PostgreSQL service")
        else:
            print(f"\n💡 Error details: {e}")
        
        return False

if __name__ == "__main__":
    success = create_database()
    if success:
        print("\n🚀 Ready to run your pipeline with real PostgreSQL!")
    else:
        print("\n❌ Please fix the connection issue and try again.")