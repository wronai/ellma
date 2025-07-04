# ELLMa Project Makefile
# Development and build automation

.PHONY: help install dev-install test lint format clean build publish docs serve-docs init shell run

# Default variables
PYTHON ?= python3
PIP ?= pip
POETRY ?= poetry
MODEL_URL ?= "https://huggingface.co/TheBloke/Mistral-7B-v0.1-GGUF/resolve/main/mistral-7b-v0.1.Q4_K_M.gguf"
MODEL_DIR = $(HOME)/.ellma/models
MODEL_FILE = $(MODEL_DIR)/mistral-7b.gguf

# Colors
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
WHITE  := $(shell tput -Txterm setaf 7)
RESET  := $(shell tput -Txterm sgr0)

##@ Help

# The help target prints out all targets with their descriptions
help:  ## Display this help
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*?##/ { printf "  ${YELLOW}%-20s${GREEN}%s${RESET}\n", $$1, $$2 } /^##@/ { printf "\n${WHITE}%s${RESET}\n", substr($$0, 5) } ' $(MAKEFILE_LIST) | column -ts:

##@ Development

init: ## Initialize development environment
	@echo "${GREEN}Initializing development environment...${RESET}"
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install poetry
	$(POETRY) install --with dev
	@echo "${GREEN}✓ Development environment ready${RESET}"

shell: ## Start interactive shell
	$(POETRY) run ellma shell

run: ## Run ellma with default command
	$(POETRY) run ellma $(ARGS)

download-model: ## Download the default model
	@echo "${GREEN}Downloading model...${RESET}"
	@mkdir -p $(MODEL_DIR)
	curl -L $(MODEL_URL) -o $(MODEL_FILE)
	@echo "${GREEN}✓ Model downloaded to $(MODEL_FILE)${RESET}"

##@ Documentation

docs: ## Generate documentation
	@echo "${GREEN}Generating documentation...${RESET}"
	$(POETRY) run mkdocs build

serve-docs: ## Serve documentation locally
	@echo "${GREEN}Starting documentation server...${RESET}"
	$(POETRY) run mkdocs serve --no-root

##@ Installation

install: ## Install the package
	$(POETRY) install --no-root

install-dev: ## Install with development dependencies
	$(POETRY) install --with dev --extras "docs"
	$(POETRY) run pre-commit install

install-all: ## Install with all optional dependencies
	$(POETRY) install --with dev,web,audio,full,docs

uninstall: ## Uninstall the package
	$(PIP) uninstall -y ellma
	@echo "${GREEN}✓ Package uninstalled${RESET}"

##@ Testing

test: test-core test-optional ## Run all tests (core + optional)

.PHONY: test-core
test-core: ## Run core tests only (without optional dependencies)
	@echo "${GREEN}Running core tests (without optional dependencies)...${RESET}"
	$(POETRY) run pytest tests/ -v -m "not requires_audio and not requires_audioop"

.PHONY: test-optional
test-optional: ## Run tests for optional features
	@echo "${GREEN}Running tests for optional features...${RESET}"
	$(POETRY) run pytest tests/ -v -m "requires_audio or requires_audioop"

.PHONY: test-coverage
test-coverage: ## Run tests with coverage report
	@echo "${GREEN}Running tests with coverage...${RESET}"
	$(POETRY) run coverage run -m pytest tests/
	$(POETRY) run coverage report -m

.PHONY: test-all
test-all: test test-optional test-coverage ## Run all tests including coverage
	@echo "${GREEN}Running all tests...${RESET}"
	$(POETRY) run pytest

unit: ## Run unit tests only
	@echo "${GREEN}Running unit tests...${RESET}"
	$(POETRY) run pytest -m "unit"

integration: ## Run integration tests only
	@echo "${GREEN}Running integration tests...${RESET}"
	$(POETRY) run pytest -m "integration"

coverage: ## Run tests with coverage report
	@echo "${GREEN}Generating test coverage report...${RESET}"
	$(POETRY) run pytest --cov=ellma --cov-report=term-missing --cov-report=html

coverage-html: ## Generate and open HTML coverage report
	$(POETRY) run pytest --cov=ellma --cov-report=html
	xdg-open htmlcov/index.html

test-verbose: ## Run tests with verbose output
	$(POETRY) run pytest -v -s

quick-test: ## Run quick test suite (faster, less verbose)
	$(POETRY) run pytest -xvs --tb=short tests/unit/

##@ Code Quality

lint: ## Run linters
	@echo "${GREEN}Running code formatters and linters...${RESET}"
	$(POETRY) run black --check .
	$(POETRY) run isort --check-only .
	$(POETRY) run flake8 .

format: ## Format code
	@echo "${GREEN}Formatting code...${RESET}"
	$(POETRY) run black .
	$(POETRY) run isort .ellma/ tests/
	$(POETRY) run mypy ellma/

format-check: ## Check code formatting without making changes
	@echo "${GREEN}Checking code formatting...${RESET}"
	$(POETRY) run black --check ellma/ tests/
	$(POETRY) run isort --check-only ellma/ tests/

typecheck: ## Run type checking with mypy
	@echo "${GREEN}Running type checking...${RESET}"
	$(POETRY) run mypy ellma/

check: lint typecheck test ## Run all checks (lint, typecheck, test)

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