# ellma Project Makefile
# Development and build automation

.PHONY: help install dev-install test lint format clean build publish docs serve-docs

# Default target
help: ## Show this help message
	@echo "ellma - Project Command Detector"
	@echo "================================="
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Installation targets
install: ## Install the package
	poetry install --no-root

install-dev: ## Install with development dependencies
	poetry install --with dev --extras "docs"
	poetry run pre-commit install

install-all: ## Install with all optional dependencies
	poetry install --with dev,web,audio,full,docs

# Testing targets
test: ## Run all tests
	@echo "Running all tests..."
	poetry run pytest

test-unit: ## Run unit tests only
	@echo "Running unit tests..."
	poetry run pytest -m "unit"

test-integration: ## Run integration tests only
	@echo "Running integration tests..."
	poetry run pytest -m "integration"

test-cov: ## Run tests with coverage report
	poetry run pytest --cov=ellma --cov-report=html --cov-report=term

test-verbose: ## Run tests with verbose output
	poetry run pytest -v

coverage: ## Generate test coverage report
	@echo "Generating test coverage report..."
	poetry run pytest --cov=ellma --cov-report=term-missing --cov-report=html

# Code quality targets
lint: ## Run all linting tools
	poetry run black --check ellma/ tests/
	poetry run flake8 ellma/ tests/
	poetry run mypy ellma/

format: ## Format code with black and isort
	poetry run black ellma/ tests/

format-check: ## Check if code is properly formatted
	poetry run black --check ellma/ tests/

mypy: ## Run type checking
	poetry run mypy ellma/

flake8: ## Run flake8 linter
	poetry run flake8 ellma/ tests/

# Build and publish targets
clean: ## Clean build artifacts
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	find . -path './.venv' -prune -o -type d -name '__pycache__' -exec rm -rf {} +
	find . -path './.venv' -prune -o -type f -name '*.pyc' -exec rm -f {} +
	find . -path './.venv' -prune -o -type f -name '*.pyo' -exec rm -f {} +

build: ## Build the package
	poetry version patch
	poetry build

publish-test: build ## Publish to test PyPI
	poetry config repositories.testpypi https://test.pypi.org/legacy/
	poetry publish -r testpypi

publish: build ## Publish to PyPI
	poetry publish

# Development targets
run: ## Run ellma on current directory
	poetry run ellma

run-dry: ## Run ellma in dry-run mode
	poetry run ellma --dry-run --verbose

run-example: ## Run ellma on example project
	poetry run ellma --path examples/ --verbose

# Quality assurance targets
qa: lint test ## Run quality assurance (lint + test)

ci: ## Run CI pipeline locally
	$(MAKE) format-check
	$(MAKE) lint
	$(MAKE) test-cov
	$(MAKE) build

pre-commit: ## Run pre-commit hooks on all files
	poetry run pre-commit run --all-files

# Utility targets
version: ## Show current version
	@poetry version

bump-patch: ## Bump patch version
	poetry version patch

bump-minor: ## Bump minor version
	poetry version minor

bump-major: ## Bump major version
	poetry version major

security: ## Run security checks
	poetry run bandit -r ellma/
	poetry run safety check

deps-update: ## Update dependencies
	poetry update

deps-show: ## Show dependency tree
	poetry show --tree

# Environment targets
env-info: ## Show environment information
	@echo "Python version:"
	@python --version
	@echo "Poetry version:"
	@poetry --version
	@echo "Project info:"
	@poetry show --no-dev

# Health check (dogfooding)
health-check: ## Run ellma on itself
	poetry run ellma --path . --verbose

health-check-dry: ## Preview ellma run on itself
	poetry run ellma --path . --dry-run --verbose

# Example and demo targets
create-examples: ## Create example projects for testing
	mkdir -p examples/javascript examples/python examples/docker
	echo '{"name": "test", "scripts": {"test": "echo test", "build": "echo build"}}' > examples/javascript/package.json
	echo 'test:\n\techo "Testing"' > examples/Makefile
	echo 'FROM python:3.9\nRUN echo "Docker test"' > examples/docker/Dockerfile

demo: create-examples ## Run demo on example projects
	@echo "Running ellma demo..."
	poetry run ellma --path examples/ --verbose

# Cleanup targets
clean-all: clean ## Clean everything
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf examples/

clean-cache: ## Clean Python cache files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

# Git targets
git-clean: ## Clean git repository
	git clean -fdx

tag: ## Create git tag with current version
	git tag v$(shell poetry version -s)
	git push origin v$(shell poetry version -s)

# Development workflow shortcuts
dev: install-dev format lint test ## Full development setup and check

quick-test: ## Quick test run (unit tests only)
	poetry run pytest tests/ -x -v --tb=short

# Release workflow
release-check: ## Check if ready for release
	@echo "Checking release readiness..."
	$(MAKE) clean
	$(MAKE) format-check
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) build
	@echo "✅ Ready for release!"

release-patch: ## Release patch version
	$(MAKE) release-check
	$(MAKE) bump-patch
	$(MAKE) tag
	$(MAKE) publish

release-minor: ## Release minor version
	$(MAKE) release-check
	$(MAKE) bump-minor
	$(MAKE) tag
	$(MAKE) publish

release-major: ## Release major version
	$(MAKE) release-check
	$(MAKE) bump-major
	$(MAKE) tag
	$(MAKE) publish