# Financial Trading ETL Pipeline - Quick Start Script (PowerShell)
# This script helps you get started with the pipeline quickly on Windows

Write-Host "🚀 Financial Trading ETL Pipeline - Quick Start" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green

# Step 1: Check Python
Write-Host ""
Write-Host "📋 Step 1: Checking Python installation..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "❌ Python not found. Please install Python 3.9+ first." -ForegroundColor Red
    Write-Host "   Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Step 2: Create virtual environment
Write-Host ""
Write-Host "📋 Step 2: Setting up Python virtual environment..." -ForegroundColor Cyan
if (!(Test-Path "venv")) {
    python -m venv venv
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
}
else {
    Write-Host "✅ Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Step 3: Install dependencies
Write-Host ""
Write-Host "📋 Step 3: Installing Python dependencies..." -ForegroundColor Cyan
Write-Host "This may take a few minutes..." -ForegroundColor Yellow
python -m pip install --upgrade pip
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
}
else {
    Write-Host "❌ Failed to install some dependencies" -ForegroundColor Red
}

# Step 4: Copy environment template
Write-Host ""
Write-Host "📋 Step 4: Setting up environment configuration..." -ForegroundColor Cyan
if (!(Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "✅ Created .env file from template" -ForegroundColor Green
    Write-Host "⚠️  Please edit .env file with your actual credentials" -ForegroundColor Yellow
}
else {
    Write-Host "✅ .env file already exists" -ForegroundColor Green
}

# Step 5: Check Docker
Write-Host ""
Write-Host "📋 Step 5: Checking Docker..." -ForegroundColor Cyan
try {
    $dockerVersion = docker --version 2>&1
    Write-Host "✅ $dockerVersion" -ForegroundColor Green
    
    # Check if Docker is running
    docker info *> $null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker daemon is running" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Docker daemon not running. Please start Docker Desktop." -ForegroundColor Red
        Write-Host "   Make sure Docker Desktop is installed and running." -ForegroundColor Yellow
        exit 1
    }
}
catch {
    Write-Host "❌ Docker not found. Please install Docker Desktop first." -ForegroundColor Red
    Write-Host "   Download from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Step 6: Run quick tests
Write-Host ""
Write-Host "📋 Step 6: Running quick tests..." -ForegroundColor Cyan
python scripts/quick_test.py

# Step 7: Start services
Write-Host ""
Write-Host "📋 Step 7: Starting development services..." -ForegroundColor Cyan
Write-Host "This will start Airflow, Prometheus, Grafana, and Jupyter Lab" -ForegroundColor Yellow

$response = Read-Host "Start services now? (y/n)"
if ($response -eq "y" -or $response -eq "Y") {
    Write-Host "Starting Docker services..." -ForegroundColor Yellow
    docker-compose up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "⏳ Waiting for services to start (this may take 2-3 minutes)..." -ForegroundColor Yellow
        Start-Sleep -Seconds 30
        
        Write-Host ""
        Write-Host "🎉 Services started! Access them at:" -ForegroundColor Green
        Write-Host "   🌐 Airflow UI:     http://localhost:8080 (admin/admin)" -ForegroundColor Cyan
        Write-Host "   📊 Grafana:       http://localhost:3000 (admin/admin)" -ForegroundColor Cyan
        Write-Host "   📈 Prometheus:    http://localhost:9090" -ForegroundColor Cyan
        Write-Host "   📓 Jupyter Lab:   http://localhost:8888" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "📝 Next steps:" -ForegroundColor Yellow
        Write-Host "   1. Edit .env file with your API keys and credentials"
        Write-Host "   2. Configure Airflow connections (see TESTING_DEPLOYMENT_GUIDE.md)"
        Write-Host "   3. Test API connectivity: python scripts\test_api_connections.py"
        Write-Host "   4. Trigger the DAG in Airflow UI"
    }
    else {
        Write-Host "❌ Failed to start services. Check Docker logs." -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "✅ Quick start complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📚 For detailed information, see:" -ForegroundColor Cyan
Write-Host "   - README.md - Project overview"
Write-Host "   - PROJECT_DOCUMENTATION.md - Technical details"  
Write-Host "   - TESTING_DEPLOYMENT_GUIDE.md - Testing and deployment"
Write-Host "   - PROJECT_TRANSFORMATION.md - How this was transformed"

Write-Host ""
Write-Host "💡 Useful commands:" -ForegroundColor Yellow
Write-Host "   - Check service status: docker-compose ps"
Write-Host "   - View logs: docker-compose logs [service-name]"
Write-Host "   - Stop services: docker-compose down"
Write-Host "   - Run tests: python -m pytest tests/ -v"