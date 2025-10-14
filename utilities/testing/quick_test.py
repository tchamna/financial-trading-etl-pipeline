#!/usr/bin/env python3
"""
Quick Test Script for Local Development
Run basic tests to verify the pipeline setup
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"🔍 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print(f"   ✅ {description} - OK")
            return True, result.stdout
        else:
            print(f"   ❌ {description} - FAILED")
            print(f"   Error: {result.stderr}")
            return False, result.stderr
    except subprocess.TimeoutExpired:
        print(f"   ⏰ {description} - TIMEOUT")
        return False, "Command timed out"
    except Exception as e:
        print(f"   💥 {description} - ERROR: {str(e)}")
        return False, str(e)

def check_python_dependencies():
    """Check if required Python packages are installed"""
    print("\n📦 Checking Python Dependencies")
    print("-" * 40)
    
    required_packages = [
        'pyspark', 'pandas', 'numpy', 'boto3', 'requests',
        'pytest', 'apache-airflow', 'snowflake-connector-python'
    ]
    
    all_good = True
    for package in required_packages:
        success, output = run_command(f"python -c \"import {package.replace('-', '_')}\"", f"Import {package}")
        if not success:
            all_good = False
    
    return all_good

def check_docker_status():
    """Check if Docker is running"""
    print("\n🐳 Checking Docker Status")
    print("-" * 40)
    
    success, output = run_command("docker --version", "Docker version check")
    if not success:
        return False
    
    success, output = run_command("docker info", "Docker daemon check")
    return success

def check_aws_credentials():
    """Check AWS credentials and connectivity"""
    print("\n☁️ Checking AWS Configuration")
    print("-" * 40)
    
    success, output = run_command("aws --version", "AWS CLI version")
    if not success:
        return False
    
    success, output = run_command("aws sts get-caller-identity", "AWS credentials check")
    if success:
        try:
            identity = json.loads(output)
            print(f"   👤 AWS User: {identity.get('Arn', 'Unknown')}")
        except:
            pass
    
    return success

def test_spark_local():
    """Test local Spark functionality"""
    print("\n⚡ Testing Local Spark")
    print("-" * 40)
    
    spark_test_code = '''
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("QuickTest").master("local[1]").getOrCreate()
data = [("Alice", 25), ("Bob", 30)]
df = spark.createDataFrame(data, ["name", "age"])
print(f"Spark test successful: {df.count()} records")
spark.stop()
'''
    
    # Write test code to temp file
    test_file = "temp_spark_test.py"
    with open(test_file, 'w') as f:
        f.write(spark_test_code)
    
    try:
        success, output = run_command(f"python {test_file}", "Spark local test")
        return success
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

def check_environment_variables():
    """Check required environment variables"""
    print("\n🔧 Checking Environment Variables")
    print("-" * 40)
    
    env_vars = {
        'ALPHA_VANTAGE_API_KEY': False,  # Optional
        'AWS_ACCESS_KEY_ID': False,      # Optional if using IAM roles
        'SNOWFLAKE_ACCOUNT': False,      # Optional for local testing
    }
    
    all_critical_set = True
    for var, required in env_vars.items():
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var} - Set")
        else:
            if required:
                print(f"   ❌ {var} - MISSING (Required)")
                all_critical_set = False
            else:
                print(f"   ⚠️  {var} - Not set (Optional for local testing)")
    
    return all_critical_set

def run_basic_tests():
    """Run basic pytest tests"""
    print("\n🧪 Running Basic Tests")
    print("-" * 40)
    
    # Check if test files exist
    test_files = [
        "tests/test_financial_transformation.py",
        "tests/test_integration.py"
    ]
    
    existing_tests = []
    for test_file in test_files:
        if os.path.exists(test_file):
            existing_tests.append(test_file)
            print(f"   📝 Found: {test_file}")
        else:
            print(f"   ⚠️  Missing: {test_file}")
    
    if existing_tests:
        # Run a simple test
        success, output = run_command("python -m pytest --version", "pytest version check")
        if success:
            # Run tests with limited scope for quick feedback
            success, output = run_command(
                "python -m pytest tests/ -v -x --tb=short -k 'not (integration or live_api)'", 
                "Running unit tests"
            )
            return success
    
    return len(existing_tests) > 0

def check_project_structure():
    """Check if project has the right structure"""
    print("\n📁 Checking Project Structure")
    print("-" * 40)
    
    required_files = [
        "airflow_financial_pipeline.py",
        "requirements.txt",
        "docker-compose.yml",
        "spark/financial_data_transformation.py",
        "sql/snowflake_financial_schema.sql"
    ]
    
    all_files_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ Missing: {file_path}")
            all_files_exist = False
    
    return all_files_exist

def main():
    """Main test runner"""
    print("🚀 Financial Trading ETL Pipeline - Quick Test")
    print("=" * 50)
    
    tests = [
        ("Project Structure", check_project_structure),
        ("Python Dependencies", check_python_dependencies),
        ("Environment Variables", check_environment_variables),
        ("Docker Status", check_docker_status),
        ("AWS Configuration", check_aws_credentials),
        ("Spark Local Test", test_spark_local),
        ("Basic Unit Tests", run_basic_tests),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"   💥 {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 QUICK TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    if passed == total:
        print("\n🎉 All quick tests passed! Ready for development.")
        print("\n📝 Next steps:")
        print("   1. Run 'docker-compose up -d' to start services")
        print("   2. Open http://localhost:8080 for Airflow UI")
        print("   3. Configure your API keys in .env file")
        print("   4. Run full integration tests")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please fix issues before proceeding.")
        print("\n🔧 Common fixes:")
        print("   - Install missing Python packages: pip install -r requirements.txt")
        print("   - Start Docker Desktop")
        print("   - Configure AWS credentials: aws configure")
        print("   - Set environment variables in .env file")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)