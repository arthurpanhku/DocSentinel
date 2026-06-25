.PHONY: help install dev test lint format contracts contracts-check clean run-api frontend-install frontend-dev frontend-test frontend-check frontend-build run-console verify all

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pip install -e .

dev: install ## Install dev dependencies and pre-commit hooks
	pre-commit install

test: ## Run tests
	pytest

lint: ## Run linting (ruff)
	ruff check .

format: ## Format code (ruff)
	ruff format .
	ruff check --fix .

contracts: ## Generate OpenAPI, JSON Schema, and frontend API types
	python scripts/export_contracts.py
	npm run api:generate --prefix frontend

contracts-check: ## Verify committed generated contracts are current
	python scripts/export_contracts.py --check
	npm run api:generate --prefix frontend
	git diff --exit-code -- docs/openapi.json docs/schemas/assessment-report.json frontend/src/api/schema.d.ts

clean: ## Clean up build artifacts
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} +

run-api: ## Run the FastAPI backend
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend-install: ## Install React console dependencies
	npm install --prefix frontend

frontend-dev: ## Run the React console dev server
	npm run dev --prefix frontend

frontend-test: ## Run React console tests
	npm run test --prefix frontend

frontend-check: ## Run React console type checks and tests
	npm run check --prefix frontend
	npm audit --omit=dev --prefix frontend

frontend-build: ## Build the React console for FastAPI hosting
	npm run build --prefix frontend

run-console: frontend-build run-api ## Build the console and run FastAPI at /console

verify: lint test contracts-check frontend-check frontend-build ## Run all CI checks

all: format verify ## Format and run all verification
