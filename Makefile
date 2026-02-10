# =============================================================================
# Makefile — Common development and deployment commands
# =============================================================================
.PHONY: help dev build test lint migrate deploy-staging deploy-prod \
        clean logs shell db-shell redis-shell format security-scan \
        docker-build docker-push

# Default target
.DEFAULT_GOAL := help

# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------
PROJECT_NAME     := selfpublisherforge
COMPOSE          := docker compose
COMPOSE_DEV      := $(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml
AWS_REGION       ?= us-east-1
AWS_ACCOUNT_ID   ?= $(shell aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "000000000000")
ECR_REGISTRY     := $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
VERSION          ?= $(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------
help: ## Show this help message
	@echo "============================================="
	@echo "  $(PROJECT_NAME) — Development Commands"
	@echo "============================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------
dev: ## Start all services in development mode with hot reload
	$(COMPOSE) up --build -d
	@echo ""
	@echo "Services running:"
	@echo "  Frontend: http://localhost:3000"
	@echo "  API:      http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo "  Flower:   http://localhost:5555"
	@echo ""

dev-down: ## Stop all development services
	$(COMPOSE) down

dev-restart: ## Restart all development services
	$(COMPOSE) down
	$(COMPOSE) up --build -d

logs: ## Tail logs for all services (or specify SERVICE=api)
	$(COMPOSE) logs -f $(SERVICE)

shell: ## Open a shell in the API container
	$(COMPOSE) exec backend bash

db-shell: ## Open a PostgreSQL shell
	$(COMPOSE) exec postgres psql -U postgres -d selfpublisherforge

redis-shell: ## Open a Redis CLI shell
	$(COMPOSE) exec redis redis-cli

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
build: ## Build all Docker images for production
	docker build -t $(PROJECT_NAME)-api:$(VERSION) ./backend
	docker build -t $(PROJECT_NAME)-frontend:$(VERSION) ./frontend
	@echo "Built images:"
	@echo "  $(PROJECT_NAME)-api:$(VERSION)"
	@echo "  $(PROJECT_NAME)-frontend:$(VERSION)"

docker-build: build ## Alias for build

docker-push: ## Push images to ECR (requires AWS auth)
	aws ecr get-login-password --region $(AWS_REGION) | \
		docker login --username AWS --password-stdin $(ECR_REGISTRY)
	docker tag $(PROJECT_NAME)-api:$(VERSION) $(ECR_REGISTRY)/$(PROJECT_NAME)-api:$(VERSION)
	docker tag $(PROJECT_NAME)-frontend:$(VERSION) $(ECR_REGISTRY)/$(PROJECT_NAME)-frontend:$(VERSION)
	docker push $(ECR_REGISTRY)/$(PROJECT_NAME)-api:$(VERSION)
	docker push $(ECR_REGISTRY)/$(PROJECT_NAME)-frontend:$(VERSION)

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------
test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend tests with coverage
	$(COMPOSE) exec backend pytest tests/ -v --cov=app --cov-report=term-missing -x

test-frontend: ## Run frontend tests with coverage
	$(COMPOSE) exec frontend npx jest --coverage --ci

test-e2e: ## Run end-to-end tests with Playwright
	cd frontend && npx playwright test

test-integration: ## Run integration tests
	$(COMPOSE) exec backend pytest tests/integration/ -v -x

# ---------------------------------------------------------------------------
# Linting & Formatting
# ---------------------------------------------------------------------------
lint: lint-backend lint-frontend ## Run all linters

lint-backend: ## Lint backend with ruff
	$(COMPOSE) exec backend ruff check .
	$(COMPOSE) exec backend ruff format --check .

lint-frontend: ## Lint frontend with ESLint and type-check with tsc
	$(COMPOSE) exec frontend npx next lint
	$(COMPOSE) exec frontend npx tsc --noEmit

format: ## Auto-format all code
	$(COMPOSE) exec backend ruff format .
	$(COMPOSE) exec backend ruff check --fix .

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
security-scan: ## Run security scans (pip-audit + npm audit)
	$(COMPOSE) exec backend pip-audit --strict --desc || true
	$(COMPOSE) exec frontend npm audit --audit-level=high || true

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
migrate: ## Run database migrations
	$(COMPOSE) exec backend alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="add users table")
	$(COMPOSE) exec backend alembic revision --autogenerate -m "$(MSG)"

migrate-rollback: ## Rollback one migration step
	$(COMPOSE) exec backend alembic downgrade -1

migrate-history: ## Show migration history
	$(COMPOSE) exec backend alembic history --verbose

# ---------------------------------------------------------------------------
# Deployment
# ---------------------------------------------------------------------------
deploy-staging: ## Deploy to staging environment
	bash infra/scripts/deploy.sh staging $(VERSION)

deploy-prod: ## Deploy to production environment (requires tag)
	@if [ -z "$(TAG)" ]; then \
		echo "ERROR: TAG is required. Usage: make deploy-prod TAG=v1.2.3"; \
		exit 1; \
	fi
	bash infra/scripts/deploy.sh production $(TAG)

rollback-staging: ## Rollback staging to previous version
	bash infra/scripts/deploy.sh rollback staging

rollback-prod: ## Rollback production to previous version
	bash infra/scripts/deploy.sh rollback production

# ---------------------------------------------------------------------------
# Terraform
# ---------------------------------------------------------------------------
tf-init: ## Initialize Terraform
	cd infra/terraform && terraform init

tf-plan: ## Plan Terraform changes (usage: make tf-plan ENV=staging)
	cd infra/terraform && terraform plan -var-file="environments/$(ENV).tfvars"

tf-apply: ## Apply Terraform changes (usage: make tf-apply ENV=staging)
	cd infra/terraform && terraform apply -var-file="environments/$(ENV).tfvars"

tf-destroy: ## Destroy Terraform resources (usage: make tf-destroy ENV=staging)
	cd infra/terraform && terraform destroy -var-file="environments/$(ENV).tfvars"

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------
clean: ## Remove all containers, volumes, and build artifacts
	$(COMPOSE) down -v --remove-orphans
	docker system prune -f
	rm -rf frontend/.next frontend/node_modules
	rm -rf backend/__pycache__ backend/.pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
