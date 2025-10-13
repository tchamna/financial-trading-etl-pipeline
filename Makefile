# 🏦 Financial Trading ETL Pipeline - Makefile
# ==============================================
# Professional project automation and management

.PHONY: help install install-dev test clean lint format docker-up docker-down docs

# Default target
help: ## Show this help message
	@echo "🏦 Financial Trading ETL Pipeline"
	@echo "=================================="
	@echo "Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ================================
# 🚀 ENVIRONMENT SETUP
# ================================
install: ## Install production dependencies
	@echo "📦 Installing production dependencies..."
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	@echo "📦 Installing development dependencies..."
	pip install -r requirements.txt -r requirements-dev.txt
	@echo "🔧 Setting up pre-commit hooks..."
	pre-commit install

setup: ## Complete project setup
	@echo "🏗️ Setting up Financial Trading ETL Pipeline..."
	cp .env.example .env
	@echo "✅ Created .env file - please update with your credentials"
	make install-dev
	@echo "✅ Setup complete! Edit .env and run 'make test' to verify"

# ================================
# 🧪 TESTING & VALIDATION
# ================================
test: ## Run all tests
	@echo "🧪 Running test suite..."
	pytest tests/ -v --cov=scripts --cov=spark --cov-report=html --cov-report=term

test-quick: ## Run quick tests only
	@echo "⚡ Running quick tests..."
	pytest tests/test_integration.py -v

test-pipeline: ## Test the full ETL pipeline
	@echo "🔄 Testing ETL pipeline..."
	python scripts/integration_test.py

# ================================
# 🔧 CODE QUALITY
# ================================
lint: ## Run code linting
	@echo "🔍 Checking code quality..."
	flake8 scripts/ spark/ dags/ --max-line-length=100
	mypy scripts/ spark/ --ignore-missing-imports

format: ## Format code
	@echo "✨ Formatting code..."
	black scripts/ spark/ dags/ tests/
	isort scripts/ spark/ dags/ tests/

quality: ## Run all quality checks
	make format
	make lint
	@echo "✅ Code quality checks complete"

# ================================
# 🐳 DOCKER OPERATIONS
# ================================
docker-up: ## Start Docker services
	@echo "🐳 Starting Docker services..."
	docker-compose up -d
	@echo "✅ Services started. Access:"
	@echo "   📊 Jupyter: http://localhost:8888"
	@echo "   🗄️ PostgreSQL: localhost:5433"
	@echo "   📈 Redis: localhost:6379"

docker-down: ## Stop Docker services
	@echo "🛑 Stopping Docker services..."
	docker-compose down

docker-clean: ## Clean Docker resources
	@echo "🧹 Cleaning Docker resources..."
	docker-compose down -v
	docker system prune -f

# ================================
# 📊 DATA OPERATIONS
# ================================
extract: ## Extract live financial data
	@echo "📥 Extracting live financial data..."
	python scripts/real_database_pipeline.py

validate-data: ## Validate database contents
	@echo "✅ Validating database..."
	python scripts/simple_db_check.py

backup-db: ## Create database backup
	@echo "💾 Creating database backup..."
	python scripts/create_database_dump.py

# ================================
# 🚀 AIRFLOW OPERATIONS
# ================================
airflow-init: ## Initialize Airflow
	@echo "🌪️ Initializing Airflow..."
	airflow db init
	airflow users create --role Admin --username admin --password admin --email admin@example.com --firstname Admin --lastname User

airflow-start: ## Start Airflow services
	@echo "🌪️ Starting Airflow..."
	airflow webserver --port 8080 &
	airflow scheduler &

airflow-stop: ## Stop Airflow services  
	@echo "🛑 Stopping Airflow..."
	pkill -f "airflow webserver"
	pkill -f "airflow scheduler"

# ================================
# 📝 DOCUMENTATION
# ================================
docs: ## Generate documentation
	@echo "📚 Generating documentation..."
	sphinx-build -b html docs/ docs/_build/

docs-serve: ## Serve documentation locally
	@echo "🌐 Serving docs at http://localhost:8000"
	python -m http.server 8000 -d docs/_build/

# ================================
# 🧹 CLEANUP
# ================================
clean: ## Clean temporary files
	@echo "🧹 Cleaning temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete
	find . -type f -name "*.tmp" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/

clean-data: ## Clean exported data files  
	@echo "🗑️ Cleaning data exports..."
	rm -rf csv_export_*/
	rm -f *.json
	rm -f *.sql
	rm -f *.csv

deep-clean: clean clean-data ## Complete cleanup
	@echo "🧹 Deep cleaning project..."
	rm -rf venv/
	rm -rf .venv/

# ================================
# 🔒 SECURITY
# ================================
security: ## Run security checks
	@echo "🔒 Running security checks..."
	bandit -r scripts/ spark/ -f json -o security-report.json
	@echo "✅ Security report generated: security-report.json"

check-env: ## Check environment configuration
	@echo "🔍 Checking environment..."
	@if [ ! -f .env ]; then echo "❌ .env file missing! Run 'make setup'"; exit 1; fi
	@echo "✅ Environment configuration found"

# ================================
# 📊 MONITORING & METRICS  
# ================================
health: ## Check system health
	@echo "💓 Checking system health..."
	python -c "import psutil; print(f'CPU: {psutil.cpu_percent()}%, Memory: {psutil.virtual_memory().percent}%')"
	@echo "✅ System status checked"

# ================================
# 🚀 DEPLOYMENT
# ================================
build: ## Build deployment artifacts
	@echo "🏗️ Building deployment artifacts..."
	make quality
	make test
	@echo "✅ Build complete - ready for deployment"

deploy-check: ## Pre-deployment checks
	make check-env
	make security
	make test
	@echo "✅ Deployment checks passed"

# ================================
# 📋 INFORMATION
# ================================
status: ## Show project status
	@echo "📊 Financial Trading ETL Pipeline Status"
	@echo "======================================="
	@echo "📁 Project: $(shell pwd)"
	@echo "🐍 Python: $(shell python --version)"
	@echo "📦 Packages: $(shell pip list | wc -l) installed"
	@echo "🧪 Tests: $(shell find tests/ -name "*.py" | wc -l) test files"
	@echo "📝 Scripts: $(shell find scripts/ -name "*.py" | wc -l) scripts"
	@if [ -f .env ]; then echo "✅ Environment configured"; else echo "❌ Environment not configured"; fi