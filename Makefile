# SBEKMS Backend Makefile
# Web Development Knowledge Management System

.PHONY: help build up down restart logs shell test test-quick test-api test-core test-integration test-coverage clean install health status

# Default target
.DEFAULT_GOAL := help

# Variables
DOCKER_COMPOSE = docker-compose
API_CONTAINER = sbekms-api
GRAPHDB_CONTAINER = sbekms-graphdb

##@ Help
help: ## Display this help message
	@echo "SBEKMS Backend Management Commands"
	@echo "=================================="
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@echo "Docker Operations:"
	@echo "  build           Build Docker containers"
	@echo "  up              Start all services"
	@echo "  down            Stop all services"
	@echo "  restart         Restart all services"
	@echo "  rebuild         Rebuild and restart all services"
	@echo "  logs            Follow logs from API container"
	@echo "  logs-all        Follow logs from all containers"
	@echo ""
	@echo "Testing:"
	@echo "  test            Run all tests"
	@echo "  test-quick      Run tests with fail-fast"
	@echo "  test-api        Run API tests only"
	@echo "  test-core       Run core component tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-coverage   Run tests with coverage report"
	@echo ""
	@echo "Development:"
	@echo "  shell           Access API container shell"
	@echo "  shell-graphdb   Access GraphDB container shell"
	@echo "  install         Install/update Python dependencies"
	@echo ""
	@echo "Health & Status:"
	@echo "  health          Check health of all services"
	@echo "  status          Show container status"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean           Clean up containers, volumes, and images"
	@echo "  clean-all       Remove everything including images"
	@echo "  clean-uploads   Clean uploaded files"
	@echo ""
	@echo "Quick Actions:"
	@echo "  dev             Build and start development environment"
	@echo "  check           Quick health check and tests"
	@echo "  info            Show project information"

##@ Docker Operations
build: ## Build Docker containers
	@echo "🔨 Building Docker containers..."
	$(DOCKER_COMPOSE) build

up: ## Start all services
	@echo "🚀 Starting all services..."
	$(DOCKER_COMPOSE) up -d
	@echo "✅ Services started successfully!"
	@echo "📊 API: http://localhost:8000"
	@echo "📊 GraphDB: http://localhost:7200"
	@echo "📚 API Docs: http://localhost:8000/docs"

down: ## Stop all services
	@echo "🛑 Stopping all services..."
	$(DOCKER_COMPOSE) down
	@echo "✅ Services stopped successfully!"

restart: ## Restart all services
	@echo "🔄 Restarting all services..."
	$(DOCKER_COMPOSE) down
	$(DOCKER_COMPOSE) up -d
	@echo "✅ Services restarted successfully!"

rebuild: ## Rebuild and restart all services
	@echo "🔄 Rebuilding and restarting all services..."
	$(DOCKER_COMPOSE) down
	$(DOCKER_COMPOSE) build
	$(DOCKER_COMPOSE) up -d
	@echo "✅ Services rebuilt and restarted successfully!"

logs: ## Follow logs from API container
	@echo "📋 Following API logs (Ctrl+C to stop)..."
	$(DOCKER_COMPOSE) logs -f api

logs-all: ## Follow logs from all containers
	@echo "
	$(DOCKER_COMPOSE) logs -f

##@ Testing
test: ## Run all tests
	@echo "🧪 Running all tests..."
	@docker exec $(API_CONTAINER) python -m pytest app/tests/ -v

test-quick: ## Run tests with fail-fast
	@echo "⚡ Running quick tests (fail-fast)..."
	@docker exec $(API_CONTAINER) python -m pytest app/tests/ -x --tb=short

test-api: ## Run API tests only
	@echo "🔌 Running API tests..."
	@docker exec $(API_CONTAINER) python -m pytest app/tests/test_api/ -v

test-core: ## Run core component tests only
	@echo "🔧 Running core component tests..."
	@docker exec $(API_CONTAINER) python -m pytest app/tests/test_core/ -v

test-integration: ## Run integration tests only
	@echo "🔗 Running integration tests..."
	@docker exec $(API_CONTAINER) python -m pytest app/tests/test_integration.py -v

test-coverage: ## Run tests with coverage report
	@echo "📊 Running tests with coverage..."
	@docker exec $(API_CONTAINER) python -m pytest app/tests/ --cov=app --cov-report=html --cov-report=term

test-watch: ## Run tests in watch mode (requires pytest-watch)
	@echo "👀 Running tests in watch mode..."
	@docker exec $(API_CONTAINER) python -m pytest app/tests/ -f

##@ Development
shell: ## Access API container shell
	@echo "🐚 Accessing API container shell..."
	@docker exec -it $(API_CONTAINER) /bin/bash

shell-graphdb: ## Access GraphDB container shell
	@echo "🐚 Accessing GraphDB container shell..."
	@docker exec -it $(GRAPHDB_CONTAINER) /bin/bash

install: ## Install/update Python dependencies
	@echo "📦 Installing Python dependencies..."
	@docker exec $(API_CONTAINER) pip install -r requirements.txt

##@ Health & Status
health: ## Check health of all services
	@echo "🏥 Checking service health..."
	@echo "API Health:"
	@curl -s http://localhost:8000/api/system/health | python -m json.tool || echo "❌ API not responding"
	@echo "\nGraphDB Health:"
	@curl -s http://localhost:7200/rest/repositories | python -m json.tool || echo "❌ GraphDB not responding"

status: ## Show container status
	@echo "📊 Container Status:"
	@$(DOCKER_COMPOSE) ps

##@ Cleanup
clean: ## Clean up containers, volumes, and images
	@echo "🧹 Cleaning up Docker resources..."
	$(DOCKER_COMPOSE) down -v --remove-orphans
	@docker system prune -f
	@echo "✅ Cleanup completed!"

clean-all: ## Remove everything including images
	@echo "🗑️  WARNING: This will remove all containers, volumes, and images!"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	$(DOCKER_COMPOSE) down -v --remove-orphans --rmi all
	@docker system prune -a -f
	@echo "✅ Complete cleanup finished!"

clean-uploads: ## Clean uploaded files
	@echo "🗑️  Cleaning uploaded files..."
	@docker exec $(API_CONTAINER) find data/uploads -type f -name "*.py" -delete 2>/dev/null || true
	@docker exec $(API_CONTAINER) find data/uploads -type f -name "*.md" -delete 2>/dev/null || true
	@docker exec $(API_CONTAINER) find data/uploads -type f -name "*.json" -delete 2>/dev/null || true
	@echo "✅ Upload directory cleaned!"

##@ Quick Actions
dev: build up ## Build and start development environment
	@echo "🎯 Development environment ready!"

prod: ## Start production environment
	@echo "🚀 Starting production environment..."
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml up -d

check: health test-quick ## Quick health check and tests
	@echo "✅ Quick check completed!"

##@ Information
info: ## Show project information
	@echo "
	@echo "API URL: http://localhost:8000"
	@echo "GraphDB: http://localhost:7200"
	@echo "API Docs: http://localhost:8000/docs"
	@echo "Repository: sbekms"
	@echo "Ontology: Web Development Ontology (WDO)" 