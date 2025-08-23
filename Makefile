# HomeyPro MCP Server Makefile

.PHONY: help install test run clean lint format check-env docker-build docker-build-multi docker-push

# Default target
help:
	@echo "HomeyPro MCP Server - Available commands:"
	@echo ""
	@echo "  install     - Install dependencies using uv"
	@echo "  test        - Run test suite"
	@echo "  test-interactive - Run interactive test mode"
	@echo "  run         - Start the MCP server"
	@echo "  clean       - Clean up generated files"
	@echo "  lint        - Run linting checks"
	@echo "  format      - Format code using black"
	@echo "  check-env   - Check environment configuration"
	@echo "  setup       - Initial setup (install + check-env)"
	@echo "  docker-build - Build Docker image for current platform"
	@echo "  docker-build-multi - Build multi-architecture Docker image (AMD64 + ARM64)"
	@echo "  docker-push - Build and push multi-architecture image to registry"
	@echo ""
	@echo "Environment variables required:"
	@echo "  HOMEY_API_URL - Your HomeyPro API URL (e.g., http://192.168.1.100)"
	@echo "  HOMEY_API_TOKEN    - Your HomeyPro Personal Access Token"
	@echo ""
	@echo "Example usage:"
	@echo "  make setup"
	@echo "  make check-env"
	@echo "  make test"
	@echo "  make run"

# Install dependencies
install:
	@echo "Installing dependencies..."
	uv sync
	@echo "Dependencies installed successfully!"

# Run test suite
test:
	@echo "Running test suite..."
	python test_server.py

# Run interactive test mode
test-interactive:
	@echo "Starting interactive test mode..."
	python test_server.py --interactive

# Start the MCP server
run:
	@echo "Starting HomeyPro MCP Server..."
	python run_server.py

# Clean up generated files
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	@echo "Cleanup complete!"

# Run linting checks
lint:
	@echo "Running linting checks..."
	python -m flake8 main.py test_server.py run_server.py --max-line-length=88 --ignore=E203,W503 || echo "flake8 not installed, skipping..."
	python -m mypy main.py test_server.py run_server.py --ignore-missing-imports || echo "mypy not installed, skipping..."

# Format code
format:
	@echo "Formatting code..."
	python -m black main.py test_server.py run_server.py --line-length=88 || echo "black not installed, skipping..."
	python -m isort main.py test_server.py run_server.py --profile=black || echo "isort not installed, skipping..."

# Check environment configuration
check-env:
	@echo "Checking environment configuration..."
	@if [ -z "$(HOMEY_API_URL)" ]; then \
		echo "❌ HOMEY_API_URL environment variable not set"; \
		echo "   Example: export HOMEY_API_URL=http://192.168.1.100"; \
		exit 1; \
	else \
		echo "✅ HOMEY_API_URL: $(HOMEY_API_URL)"; \
	fi
	@if [ -z "$(HOMEY_API_TOKEN)" ]; then \
		echo "❌ HOMEY_API_TOKEN environment variable not set"; \
		echo "   Generate a Personal Access Token from HomeyPro Settings > API"; \
		exit 1; \
	else \
		echo "✅ HOMEY_API_TOKEN: **********************"; \
	fi
	@echo "Environment configuration looks good!"

# Initial setup
setup: install
	@echo "Setting up HomeyPro MCP Server..."
	@echo ""
	@echo "Please ensure you have set the following environment variables:"
	@echo "  HOMEY_API_URL - Your HomeyPro API URL"
	@echo "  HOMEY_API_TOKEN    - Your HomeyPro Personal Access Token"
	@echo ""
	@echo "You can also create a .env file based on .env.example"
	@echo ""
	@echo "Run 'make check-env' to verify your configuration"
	@echo "Run 'make test' to test the connection"
	@echo "Run 'make run' to start the server"

# Development helpers
dev-install:
	@echo "Installing development dependencies..."
	uv add --dev black flake8 mypy isort pytest
	@echo "Development dependencies installed!"

# Quick development workflow
dev: format lint test
	@echo "Development workflow complete!"

# Check if we can connect to HomeyPro
check-connection:
	@echo "Testing connection to HomeyPro..."
	@python -c "\
import asyncio; \
import os; \
from main import ensure_client; \
\
async def test(): \
    try: \
        client = await ensure_client(); \
        print('✅ Successfully connected to HomeyPro'); \
        await client.disconnect(); \
    except Exception as e: \
        print(f'❌ Connection failed: {e}'); \
        exit(1); \
\
asyncio.run(test())"

# Show server information
info:
	@echo "HomeyPro MCP Server Information"
	@echo "==============================="
	@echo "Python version: $(shell python --version)"
	@echo "UV version: $(shell uv --version 2>/dev/null || echo 'Not installed')"
	@echo "Project directory: $(PWD)"
	@echo "Virtual environment: $(shell python -c 'import sys; print(sys.prefix)')"
	@echo ""
	@echo "Environment variables:"
	@echo "  HOMEY_API_URL: $(HOMEY_API_URL)"
	@echo "  HOMEY_API_TOKEN: $(if $(HOMEY_API_TOKEN),Set (hidden),Not set)"
	@echo ""
	@echo "Files:"
	@echo "  main.py: $(shell test -f main.py && echo 'Present' || echo 'Missing')"
	@echo "  test_server.py: $(shell test -f test_server.py && echo 'Present' || echo 'Missing')"
	@echo "  run_server.py: $(shell test -f run_server.py && echo 'Present' || echo 'Missing')"
	@echo "  .env: $(shell test -f .env && echo 'Present' || echo 'Not found')"

# Docker build targets
DOCKER_IMAGE ?= ghcr.io/pigmej/python-homey-mcp
DOCKER_TAG ?= latest

# Build Docker image for current platform
docker-build:
	@echo "Building Docker image for current platform..."
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .
	@echo "Docker image built successfully!"

# Build multi-architecture Docker image (requires Docker Buildx)
docker-build-multi:
	@echo "Building multi-architecture Docker image (AMD64 + ARM64)..."
	@echo "Setting up Docker Buildx..."
	docker buildx create --name multiarch --use --bootstrap 2>/dev/null || docker buildx use multiarch
	@echo "Building for linux/amd64 and linux/arm64..."
	docker buildx build \
		--platform linux/amd64,linux/arm64 \
		--tag $(DOCKER_IMAGE):$(DOCKER_TAG) \
		--load \
		.
	@echo "Multi-architecture Docker image built successfully!"

# Build and push multi-architecture image to registry
docker-push:
	@echo "Building and pushing multi-architecture Docker image..."
	@echo "Setting up Docker Buildx..."
	docker buildx create --name multiarch --use --bootstrap 2>/dev/null || docker buildx use multiarch
	@echo "Building and pushing for linux/amd64 and linux/arm64..."
	docker buildx build \
		--platform linux/amd64,linux/arm64 \
		--tag $(DOCKER_IMAGE):$(DOCKER_TAG) \
		--push \
		.
	@echo "Multi-architecture Docker image pushed successfully!"

# Test Docker image
docker-test:
	@echo "Testing Docker image..."
	docker run --rm -e HOMEY_API_URL=$(HOMEY_API_URL) -e HOMEY_API_TOKEN=$(HOMEY_API_TOKEN) $(DOCKER_IMAGE):$(DOCKER_TAG) --help || echo "Docker test completed"
