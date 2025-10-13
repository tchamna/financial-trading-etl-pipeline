#!/bin/bash
# Financial Trading ETL Pipeline - Quick Start Script
# This script helps you get started with the pipeline quickly

echo "🚀 Financial Trading ETL Pipeline - Quick Start"
echo "==============================================="

# Check if we're on Windows (PowerShell)
if command -v powershell &> /dev/null; then
    echo "🪟 Windows PowerShell detected"
    SHELL_TYPE="powershell"
else
    echo "🐧 Unix/Linux shell detected" 
    SHELL_TYPE="bash"
fi

# Function to run commands based on shell type
run_cmd() {
    if [ "$SHELL_TYPE" = "powershell" ]; then
        powershell -Command "$1"
    else
        eval "$1"
    fi
}

# Step 1: Check Python
echo ""
echo "📋 Step 1: Checking Python installation..."
python --version
if [ $? -ne 0 ]; then
    echo "❌ Python not found. Please install Python 3.9+ first."
    exit 1
fi

# Step 2: Create virtual environment
echo ""
echo "📋 Step 2: Setting up Python virtual environment..."
if [ "$SHELL_TYPE" = "powershell" ]; then
    python -m venv venv
    echo "Activating virtual environment..."
    echo "Please run: venv\\Scripts\\Activate.ps1"
    echo "Then re-run this script."
else
    python -m venv venv
    source venv/bin/activate
fi

# Step 3: Install dependencies
echo ""
echo "📋 Step 3: Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Step 4: Copy environment template
echo ""
echo "📋 Step 4: Setting up environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file from template"
    echo "⚠️  Please edit .env file with your actual credentials"
else
    echo "✅ .env file already exists"
fi

# Step 5: Check Docker
echo ""
echo "📋 Step 5: Checking Docker..."
docker --version
if [ $? -ne 0 ]; then
    echo "❌ Docker not found. Please install Docker Desktop first."
    echo "   Download from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

docker info > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Docker daemon not running. Please start Docker Desktop."
    exit 1
fi

# Step 6: Run quick tests
echo ""
echo "📋 Step 6: Running quick tests..."
python scripts/quick_test.py

# Step 7: Start services
echo ""
echo "📋 Step 7: Starting development services..."
echo "This will start Airflow, Prometheus, Grafana, and Jupyter Lab"
read -p "Start services now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose up -d
    
    echo ""
    echo "⏳ Waiting for services to start (this may take 2-3 minutes)..."
    sleep 30
    
    echo ""
    echo "🎉 Services started! Access them at:"
    echo "   🌐 Airflow UI:     http://localhost:8080 (admin/admin)"
    echo "   📊 Grafana:       http://localhost:3000 (admin/admin)"
    echo "   📈 Prometheus:    http://localhost:9090"
    echo "   📓 Jupyter Lab:   http://localhost:8888"
    echo ""
    echo "📝 Next steps:"
    echo "   1. Edit .env file with your API keys and credentials"
    echo "   2. Configure Airflow connections (see TESTING_DEPLOYMENT_GUIDE.md)"
    echo "   3. Test API connectivity: python scripts/test_api_connections.py"
    echo "   4. Trigger the DAG in Airflow UI"
fi

echo ""
echo "✅ Quick start complete!"
echo ""
echo "📚 For detailed information, see:"
echo "   - README.md - Project overview"
echo "   - PROJECT_DOCUMENTATION.md - Technical details"  
echo "   - TESTING_DEPLOYMENT_GUIDE.md - Testing and deployment"
echo "   - PROJECT_TRANSFORMATION.md - How this was transformed"