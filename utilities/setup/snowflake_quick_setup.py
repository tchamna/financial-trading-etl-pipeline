"""
Quick Snowflake Setup Script
============================

This script helps you quickly configure and test Snowflake integration.

Usage:
    python utilities/setup/snowflake_quick_setup.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

def main():
    print("=" * 70)
    print("🏔️  SNOWFLAKE QUICK SETUP")
    print("=" * 70)
    
    print("\n📋 Step 1: Snowflake Account Information")
    print("-" * 70)
    print("You'll need the following information from your Snowflake account:")
    print("  • Account URL (e.g., xyz12345.snowflakecomputing.com)")
    print("  • Username")
    print("  • Password")
    print("  • Role (default: SYSADMIN)")
    print("")
    
    # Get user input
    account = input("Enter your Snowflake account URL: ").strip()
    username = input("Enter your Snowflake username: ").strip()
    password = input("Enter your Snowflake password: ").strip()
    role = input("Enter your Snowflake role [SYSADMIN]: ").strip() or "SYSADMIN"
    
    print("\n⚙️  Step 2: Configuration Settings")
    print("-" * 70)
    
    warehouse = input("Enter warehouse name [FINANCIAL_WH]: ").strip() or "FINANCIAL_WH"
    database = input("Enter database name [FINANCIAL_DB]: ").strip() or "FINANCIAL_DB"
    schema = input("Enter schema name [CORE]: ").strip() or "CORE"
    
    print("\n✅ Step 3: Saving Configuration")
    print("-" * 70)
    
    # Update config.json
    import json
    config_path = Path(__file__).parent.parent.parent / "config.json"
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        config['snowflake'] = {
            'account': account,
            'username': username,
            'password': password,
            'role': role,
            'warehouse': warehouse,
            'database': database,
            'schema': schema
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ config.json updated successfully!")
        
    except Exception as e:
        print(f"❌ Error updating config.json: {e}")
        return
    
    # Update user_config.py
    print("\n📝 Updating user_config.py...")
    user_config_path = Path(__file__).parent.parent.parent / "user_config.py"
    
    try:
        with open(user_config_path, 'r') as f:
            content = f.read()
        
        # Update settings
        content = content.replace(
            'ENABLE_SNOWFLAKE = False',
            'ENABLE_SNOWFLAKE = True'
        )
        content = content.replace(
            f'SNOWFLAKE_WAREHOUSE = "FINANCIAL_WH"',
            f'SNOWFLAKE_WAREHOUSE = "{warehouse}"'
        )
        content = content.replace(
            f'SNOWFLAKE_DATABASE = "FINANCIAL_DB"',
            f'SNOWFLAKE_DATABASE = "{database}"'
        )
        content = content.replace(
            f'SNOWFLAKE_SCHEMA = "CORE"',
            f'SNOWFLAKE_SCHEMA = "{schema}"'
        )
        
        with open(user_config_path, 'w') as f:
            f.write(content)
        
        print("✅ user_config.py updated successfully!")
        
    except Exception as e:
        print(f"❌ Error updating user_config.py: {e}")
        return
    
    print("\n🧪 Step 4: Testing Connection")
    print("-" * 70)
    
    try:
        import snowflake.connector
        
        print("Connecting to Snowflake...")
        conn = snowflake.connector.connect(
            account=account,
            user=username,
            password=password,
            role=role,
            warehouse=warehouse
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_VERSION()")
        version = cursor.fetchone()[0]
        
        print(f"✅ Connection successful!")
        print(f"   Snowflake version: {version}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 Troubleshooting:")
        print("   • Verify account URL format (no https://)")
        print("   • Check username and password")
        print("   • Ensure network access to Snowflake")
        return
    
    print("\n🎉 Setup Complete!")
    print("=" * 70)
    print("\n📚 Next Steps:")
    print("   1. Run the data loader:")
    print("      python scripts/snowflake_data_loader.py")
    print("")
    print("   2. Check the integration guide:")
    print("      docs/SNOWFLAKE_INTEGRATION_GUIDE.md")
    print("")
    print("   3. Query your data in Snowflake!")
    print("=" * 70)


if __name__ == "__main__":
    main()
